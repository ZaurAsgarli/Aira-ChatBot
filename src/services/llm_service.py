import json
import logging
from typing import List, Dict

from openai import OpenAI
from src.config import settings
from src.core.prompts import (
    INTENT_SYSTEM_PROMPT,
    COACH_SYSTEM_PROMPT,
    EXPERT_SYSTEM_PROMPT,
)
from src.models.chat_schema import ChatResponse, Source
from src.services.websearch_service import websearch_service
from src.services.matching_engine import matching_engine

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None
            logger.critical("❌ OpenAI API Key missing.")

    def get_response(
        self, query: str, conversation_history: List[Dict[str, str]], user_id: str
    ) -> ChatResponse:
        if not self.client:
            return ChatResponse(answer="⚠️ System Error: OpenAI Key missing.")

        # 1. Format History
        # We include the last 8 messages to ensure the "Diagnosis Chain" isn't broken
        history_str = "\n".join(
            [
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in conversation_history[-8:]
            ]
        )

        # 2. DETERMINE INTENT
        mode = self._check_intent(query, history_str)
        logger.info(f"🧠 Intent Detected: {mode.upper()}")

        # --- COACH MODE ---
        if mode == "coach":
            try:
                # 🧠 INTELLIGENT CONTEXT INJECTION
                # If the user typed "1", tell GPT to look at the previous bot message's buttons.
                system_instruction = COACH_SYSTEM_PROMPT.format(history=history_str)

                if query.isdigit():
                    system_instruction += f"\n\n[SYSTEM NOTE]: The user answered '{query}'. Look at your previous message in history to map this number to the option text."

                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": query},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                )
                data = json.loads(response.choices[0].message.content)

                return ChatResponse(
                    answer=data.get("reply", "Gəl davam edək."),
                    needs_clarification=True,
                    follow_up_questions=data.get("follow_up_questions", []),
                    recommendations=[],
                    sources=[],
                )
            except Exception as e:
                logger.error(f"Coach Mode Error: {e}")
                return ChatResponse(
                    answer="Üzr istəyirəm, bir az qarışıqlıq oldu. Gəl yenidən başlayaq."
                )

        # --- EXPERT MODE ---

        search_text = ""
        sources_list: List[Source] = []

        if settings.SEARCH_ENABLED:
            augmented_query = query
            # If query is short (like "Roadmap" or "1"), grab context from history
            if len(query.split()) < 5 and conversation_history:
                last_bot_msg = conversation_history[-1].get("content", "")
                augmented_query = (
                    f"{query} context: {last_bot_msg[-150:]} salary roadmap"
                )

            logger.info(f"🔍 Searching: {augmented_query}")
            search_text, sources_list = websearch_service.search(augmented_query)

        recommendations, db_context = matching_engine.find_matches(query)

        final_prompt = EXPERT_SYSTEM_PROMPT.format(
            search_results=search_text,
            db_context=db_context,
            history=history_str,
            query=query,
        )

        try:
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL_MAIN,
                messages=[
                    {"role": "system", "content": final_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.3,
            )

            markdown_answer = response.choices[0].message.content

            return ChatResponse(
                answer=markdown_answer,
                needs_clarification=False,
                recommendations=recommendations,
                sources=sources_list,
                follow_up_questions=[],
            )

        except Exception as e:
            logger.error(f"Expert Mode Error: {e}")
            return ChatResponse(answer="Texniki xəta baş verdi.")

    def _check_intent(self, query: str, history: str) -> str:
        try:
            if not history and len(query.split()) < 3:
                return "coach"

            res = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                    {"role": "system", "content": f"HISTORY:\n{history}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            data = json.loads(res.choices[0].message.content)
            return data.get("mode", "expert")
        except Exception:
            return "expert"


llm_service = LLMService()
