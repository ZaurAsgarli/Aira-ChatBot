"""
MynEra Aira - Agentic LLM Orchestration Service
Handles EMPTY_DB gracefully + Forces tool usage for factual data
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any

from openai import OpenAI
from src.config import settings
from src.models.chat_schema import ChatResponse, Source, Recommendation
from src.services.websearch_service import websearch_service
from src.services.matching_engine import matching_engine
from src.core.prompts import (
    MASTER_SYSTEM_PROMPT,
    TOOL_DEFINITIONS,
    HARD_BLOCK_KEYWORDS,
    SOFT_PIVOT_KEYWORDS,
    IT_CONTEXT_KEYWORDS,
    is_vague_query,
    is_it_context,
    detect_auto_search_triggers,
)

logger = logging.getLogger(__name__)


class LLMService:
    """
    Agentic LLM Orchestration with Dynamic Data Retrieval.
    
    Features:
    - Forces tool usage for factual questions
    - Handles EMPTY_DB gracefully (triggers web search)
    - Loop prevention (max 2 searches per type)
    - Forced synthesis after research phase
    """

    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("✅ OpenAI initialized")
        else:
            self.client = None
            logger.critical("❌ OpenAI Key missing")

        # Anti-loop settings
        self.max_iterations = 5
        self.max_web_searches = 2
        self.max_db_searches = 2

    def get_response(
        self, 
        query: str, 
        conversation_history: List[Dict[str, str]], 
        user_id: str
    ) -> ChatResponse:
        """
        Main entry point for generating responses.
        """
        if not self.client:
            return ChatResponse(answer="⚠️ Sistem xətası: OpenAI əlçatan deyil.")

        try:
            # ===== STEP 1: Safety Check =====
            is_safe, block_type = self._check_safety(query)
            if not is_safe:
                return self._blocked_response(block_type)
            
            if block_type == "SOFT":
                return self._soft_pivot_response()

            # ===== STEP 2: Prepare System Prompt =====
            current_date = self._get_azerbaijani_date()
            system_prompt = MASTER_SYSTEM_PROMPT.format(current_date=current_date)
            
            # ===== STEP 3: Build Messages =====
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (last 10 messages for better context)
            for msg in conversation_history[-10:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ["user", "assistant"] and content:
                    messages.append({"role": role, "content": content})
            
            messages.append({"role": "user", "content": query})

            # ===== STEP 4: Detect Auto-Search Triggers =====
            auto_triggers = detect_auto_search_triggers(query)
            if auto_triggers:
                logger.info(f"🎯 Auto-search triggers detected: {auto_triggers}")

            # ===== STEP 5: Agentic Loop =====
            all_sources: List[Source] = []
            all_recommendations: List[Recommendation] = []
            web_search_count = 0
            db_search_count = 0
            db_was_empty = False
            
            for iteration in range(self.max_iterations):
                logger.info(f"🔄 Iteration {iteration + 1}/{self.max_iterations}")
                
                # Determine available tools
                available_tools = self._get_available_tools(
                    web_search_count, db_search_count
                )
                
                # Call OpenAI
                response = self.client.chat.completions.create(
                    model=settings.LLM_MODEL_MAIN,
                    messages=messages,
                    tools=available_tools if available_tools else None,
                    tool_choice="auto" if available_tools else None,
                    temperature=0.7,
                    max_tokens=2500
                )
                
                choice = response.choices[0]
                message = choice.message
                
                # Check if done (no tool calls)
                if not message.tool_calls:
                    logger.info("✅ Response complete (no tool calls)")
                    return self._build_final_response(
                        message.content or "",
                        all_sources,
                        all_recommendations
                    )
                
                # Process tool calls
                messages.append(message)
                
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"🔧 Tool call: {tool_name}({tool_args})")
                    
                    if tool_name == "search_web":
                        web_search_count += 1
                        result, sources = self._execute_web_search(tool_args)
                        all_sources.extend(sources)
                        
                    elif tool_name == "query_vector_db":
                        db_search_count += 1
                        result, recommendations = self._execute_db_search(tool_args)
                        
                        # Check if DB was empty
                        if "[STATUS: EMPTY_DB]" in result:
                            db_was_empty = True
                            logger.warning("⚠️ Vector DB returned EMPTY_DB status")
                            # Add guidance for LLM
                            result += "\n\n💡 Tövsiyə: search_web ilə xarici resurslar tap."
                        else:
                            all_recommendations.extend(recommendations)
                        
                    else:
                        result = f"Unknown tool: {tool_name}"
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
                
                # If DB was empty and we haven't searched web yet, encourage web search
                if db_was_empty and web_search_count == 0 and iteration < self.max_iterations - 1:
                    messages.append({
                        "role": "user",
                        "content": (
                            "Bazada nəticə tapılmadı. Zəhmət olmasa search_web istifadə edib "
                            "bu mövzuda xarici resurslar və ya pulsuz öyrənmə materialları tap."
                        )
                    })
            
            # Max iterations reached - force synthesis
            logger.warning("⚠️ Max iterations reached. Forcing synthesis.")
            return self._force_synthesis(messages, all_sources, all_recommendations)

        except Exception as e:
            logger.error(f"❌ LLM error: {e}", exc_info=True)
            return ChatResponse(answer=f"⚠️ Xəta baş verdi. Yenidən cəhd edin.")

    def _get_available_tools(
        self, web_count: int, db_count: int
    ) -> List[Dict]:
        """Get available tools based on usage counts."""
        available = []
        
        if web_count < self.max_web_searches:
            available.append(TOOL_DEFINITIONS[0])  # search_web
        else:
            logger.info("🚫 Web search disabled (limit reached)")
            
        if db_count < self.max_db_searches:
            available.append(TOOL_DEFINITIONS[1])  # query_vector_db
        else:
            logger.info("🚫 DB search disabled (limit reached)")
        
        return available

    def _execute_web_search(self, args: Dict) -> tuple[str, List[Source]]:
        """Execute web search tool."""
        query = args.get("query", "")
        if not query:
            return "Error: No query provided", []
        
        context, sources = websearch_service.search(query)
        return context, sources

    def _execute_db_search(self, args: Dict) -> tuple[str, List[Recommendation]]:
        """Execute database search tool."""
        topic = args.get("topic", "")
        if not topic:
            return "Error: No topic provided", []
        
        recommendations, context = matching_engine.find_matches(topic)
        return context, recommendations

    def _force_synthesis(
        self,
        messages: List[Dict],
        sources: List[Source],
        recommendations: List[Recommendation]
    ) -> ChatResponse:
        """Force LLM to synthesize answer without more tool calls."""
        
        messages.append({
            "role": "user",
            "content": (
                "⚠️ Axtarış limiti doldu. İndi əldə etdiyin məlumatlarla cavab ver. "
                "Əgər kifayət qədər data var, onu istifadə et. "
                "Əgər data azdırsa, əldə olanı ümumiləşdir və tövsiyə ver."
            )
        })
        
        try:
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL_MAIN,
                messages=messages,
                tools=None,
                temperature=0.7,
                max_tokens=2500
            )
            
            content = response.choices[0].message.content or ""
            return self._build_final_response(content, sources, recommendations)
            
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return ChatResponse(
                answer="Məlumatları emal edərkən xəta baş verdi.",
                sources=sources,
                recommendations=recommendations
            )

    def _build_final_response(
        self,
        content: str,
        sources: List[Source],
        recommendations: List[Recommendation]
    ) -> ChatResponse:
        """Build final ChatResponse object."""
        
        # Deduplicate sources
        seen_urls = set()
        unique_sources = []
        for src in sources:
            if src.url not in seen_urls:
                seen_urls.add(src.url)
                unique_sources.append(src)
        
        # Deduplicate recommendations
        seen_ids = set()
        unique_recs = []
        for rec in recommendations:
            if rec.id not in seen_ids:
                seen_ids.add(rec.id)
                unique_recs.append(rec)
        
        return ChatResponse(
            answer=content,
            sources=unique_sources[:5],
            recommendations=unique_recs[:6],
            needs_clarification=False,
            follow_up_questions=[]
        )

    def _check_safety(self, query: str) -> tuple[bool, str]:
        """Check query safety with contextual awareness."""
        q_lower = query.lower()
        
        # Hard block
        for keyword in HARD_BLOCK_KEYWORDS:
            if keyword in q_lower:
                logger.warning(f"🛡️ HARD BLOCK: '{keyword}'")
                return False, "HARD"
        
        # Soft pivot - allow if in IT context
        for keyword in SOFT_PIVOT_KEYWORDS:
            if keyword in q_lower:
                if is_it_context(query):
                    logger.info(f"✅ '{keyword}' allowed (IT context detected)")
                    return True, "SAFE"
                else:
                    logger.info(f"🔄 SOFT PIVOT: '{keyword}' (no IT context)")
                    return True, "SOFT"
        
        return True, "SAFE"

    def _blocked_response(self, block_type: str) -> ChatResponse:
        """Return blocked response."""
        return ChatResponse(
            answer=(
                "Bu mövzu mənim sahəmə aid deyil. "
                "Mən İT karyera və təhsil məsləhətçisiyəm. "
                "İT, proqramlaşdırma, kurslar və ya karyera haqqında sual verə bilərsiniz."
            ),
            needs_clarification=False,
            sources=[],
            recommendations=[]
        )

    def _soft_pivot_response(self) -> ChatResponse:
        """Return soft pivot response."""
        return ChatResponse(
            answer=(
                "Bu maraqlı mövzudur, amma mənim ixtisasım İT və karyera məsləhətidir. 😊\n\n"
                "Sizə necə kömək edə bilərəm:\n"
                "- İT sahəsinə başlamaq\n"
                "- Proqramlaşdırma kursları\n"
                "- Universitet qəbulu\n"
                "- Karyera məsləhəti\n\n"
                "Bu mövzulardan hansı sizi maraqlandırır?"
            ),
            needs_clarification=True,
            sources=[],
            recommendations=[]
        )

    def _get_azerbaijani_date(self) -> str:
        """Get current date in Azerbaijani format."""
        months = {
            1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel",
            5: "May", 6: "İyun", 7: "İyul", 8: "Avqust",
            9: "Sentyabr", 10: "Oktyabr", 11: "Noyabr", 12: "Dekabr"
        }
        now = datetime.now()
        return f"{now.day} {months[now.month]} {now.year}"


# Singleton instance
llm_service = LLMService()