import json
import logging
from typing import List, Dict, Tuple, Optional

from openai import OpenAI
from src.config import settings
from src.models.chat_schema import ChatResponse, Source

# Import all the advanced prompts we just defined
from src.core.prompts import (
    SYSTEM_PROMPT,
    INTENT_CLASSIFIER_PROMPT,
    COACH_SYSTEM_PROMPT,
    EXPERT_SYSTEM_PROMPT,
    SEARCH_QUERY_ENHANCER
)

# Import internal services
from src.services.websearch_service import websearch_service
from src.services.matching_engine import matching_engine

logger = logging.getLogger(__name__)

class LLMService:
    """
    The Central Brain of Aira (Version 2.0).
    Orchestrates the decision between 'Coach Mode' (Profiling) and 'Expert Mode' (Knowledge).
    """

    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None
            logger.critical("❌ OpenAI API Key missing. Brain is offline.")

    def get_response(
        self, query: str, conversation_history: List[Dict[str, str]], user_id: str
    ) -> ChatResponse:
        """
        Main entry point.
        1. Analyzes Intent (Coach vs Expert).
        2. Routes to specific logic handler.
        3. Returns structured ChatResponse.
        """
        if not self.client:
            return ChatResponse(answer="⚠️ System Error: OpenAI Key missing.")

        # 1. Format History (Last 8 messages for context retention)
        # We perform a safe get to avoid key errors if history format varies
        history_str = "\n".join(
            [
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in conversation_history[-8:]
            ]
        )

        # 2. DETERMINE INTENT & MODE
        intent_data = self._classify_intent(query, history_str)
        mode = intent_data.get("mode", "expert")
        logger.info(f"🧠 Intent Analysis: {intent_data}")

        # 3. ROUTE TO HANDLER
        if mode == "coach":
            return self._handle_coach_mode(query, history_str)
        else:
            return self._handle_expert_mode(query, history_str, user_id)

    # ========================================================================
    # 🧠 INTENT CLASSIFICATION
    # ========================================================================
    def _classify_intent(self, query: str, history: str) -> Dict[str, str]:
        """
        Uses a small, fast LLM call to determine if we need Coach or Expert mode.
        """
        try:
            # Heuristic: If history is empty and query is short, default to Coach
            if not history and len(query.split()) < 4:
                return {"mode": "coach", "reason": "New user, short query"}

            prompt = INTENT_CLASSIFIER_PROMPT.format(
                user_message=query,
                history_summary=history[-500:] # Last 500 chars is enough for intent
            )

            response = self.client.chat.completions.create(
                model="gpt-4o-mini", # Fast model for routing
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Intent Classification Failed: {e}")
            return {"mode": "expert", "reason": "Fallback due to error"}

    # ========================================================================
    # 🅰️ COACH MODE HANDLER
    # ========================================================================
    def _handle_coach_mode(self, query: str, history: str) -> ChatResponse:
        """
        Handles the Career Profiling Logic.
        Output: JSON (Reply text + Buttons).
        """
        try:
            # SYSTEM NOTE INJECTION
            # If input is a number (e.g. "1"), tell GPT to look at history
            system_note = ""
            if query.strip().isdigit():
                system_note = "\n\n[SYSTEM NOTE]: The user replied with a number. Look at the 'follow_up_questions' (buttons) in the LAST ASSISTANT MESSAGE in history to interpret this choice."

            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL_MAIN,
                messages=[
                    {
                        "role": "system",
                        "content": COACH_SYSTEM_PROMPT.format(history=history) + system_note,
                    },
                    {"role": "user", "content": query},
                ],
                response_format={"type": "json_object"},
                temperature=0.7, # Creativity needed for psychological questions
            )
            
            data = json.loads(response.choices[0].message.content)

            return ChatResponse(
                answer=data.get("reply", "Gəl davam edək."),
                needs_clarification=True,
                follow_up_questions=data.get("follow_up_questions", []),
                recommendations=[],
                sources=[]
            )

        except Exception as e:
            logger.error(f"Coach Logic Error: {e}")
            return ChatResponse(
                answer="Üzr istəyirəm, fikrinizi tam tuta bilmədim. Gəl yenidən başlayaq: İT sahəsində hansı istiqamət sənə maraqlıdır?",
                follow_up_questions=["Texniki (Kod)", "Vizual (Dizayn)"]
            )

    # ========================================================================
    # 🅱️ EXPERT MODE HANDLER
    # ========================================================================
    def _handle_expert_mode(self, query: str, history: str, user_id: str) -> ChatResponse:
        """
        Handles Knowledge Delivery, Web Search, and Roadmap generation.
        Output: Markdown Text + Sources + Cards.
        """
        try:
            search_text = ""
            sources_list: List[Source] = []

            # 1. INTELLIGENT WEB SEARCH
            if settings.SEARCH_ENABLED:
                # Augment the query to get better results
                # e.g., "Maaşlar" -> "Backend developer salary Azerbaijan 2025"
                optimized_query = self._optimize_search_query(query, history)
                logger.info(f"🔍 Performing Search: {optimized_query}")
                
                search_text, sources_list = websearch_service.search(optimized_query)

            # 2. INTERNAL DATABASE MATCHING
            # Check if we have courses matching the query
            recommendations, db_context = matching_engine.find_matches(query)

            # 3. GENERATE ANSWER
            final_prompt = EXPERT_SYSTEM_PROMPT.format(
                search_results=search_text,
                db_context=db_context,
                history=history,
                query=query
            )

            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL_MAIN,
                messages=[
                    {"role": "system", "content": final_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.3, # Strictness for facts
            )

            markdown_answer = response.choices[0].message.content

            return ChatResponse(
                answer=markdown_answer,
                needs_clarification=False,
                recommendations=recommendations,
                sources=sources_list,
                follow_up_questions=[] # No chips in expert mode usually
            )

        except Exception as e:
            logger.error(f"Expert Logic Error: {e}")
            return ChatResponse(
                answer="Texniki xəta baş verdi. Zəhmət olmasa bir az sonra yenidən cəhd edin."
            )

    # ========================================================================
    # 🔍 UTILITIES
    # ========================================================================
    def _optimize_search_query(self, query: str, history: str) -> str:
        """
        Uses a tiny LLM call to rewrite the user's query for Tavily.
        Example: "Maaş?" -> "Data Science salary Azerbaijan 2025"
        """
        try:
            # Heuristic: If query is long enough, use it directly to save time
            if len(query.split()) > 5:
                return query + " Azerbaijan 2025"

            prompt = SEARCH_QUERY_ENHANCER.format(
                history_summary=history[-300:], # Short context
                query=query
            )

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            
            return response.choices[0].message.content.strip()
        except Exception:
            return query # Fallback

# Singleton Instance
llm_service = LLMService()