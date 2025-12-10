import logging
from src.models.chat_schema import ChatRequest, ChatResponse
from src.services.llm_service import llm_service
from src.core.exceptions import LLMGenerationException, VectorDBException

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    The High-Level Manager.
    It links the API Layer to the Service Layer.

    Responsibilities:
    1. Receive ChatRequest.
    2. Validate Input.
    3. Call LLMService (The Brain).
    4. Handle Errors Gracefully.
    """

    def handle_chat(self, request: ChatRequest) -> ChatResponse:
        """
        Main entry point for the /chat endpoint.
        """
        user_id = request.user_id
        query = request.query
        history = request.conversation_history

        logger.info(f"📨 Orchestrator received request: '{query}' (User: {user_id})")

        try:
            # 1. Validation (Fast Fail)
            if not query or not query.strip():
                return ChatResponse(
                    answer="Zəhmət olmasa, boş mesaj göndərməyin. Sizə necə kömək edə bilərəm?",
                    recommendations=[],
                )

            # 2. Delegate to the Brain (LLMService)
            # The LLMService handles Coach vs Expert logic, Web Search, and DB lookup internally.
            response = llm_service.get_response(
                query=query, conversation_history=history, user_id=user_id
            )

            logger.info("✅ Response generated successfully.")
            return response

        except LLMGenerationException as e:
            logger.error(f"❌ AI Generation Error: {e.message}")
            return ChatResponse(
                answer="Üzr istəyirəm, hal-hazırda beynimdə texniki problem var. (AI Error)"
            )

        except VectorDBException as e:
            logger.error(f"❌ Database Error: {e.message}")
            return ChatResponse(
                answer="Məlumat bazasına qoşula bilmədim, lakin ümumi biliklərimlə cavab verməyə çalışacağam."
            )

        except Exception as e:
            logger.critical(f"❌ Unhandled Orchestrator Error: {e}")
            return ChatResponse(
                answer="Sistemdə gözlənilməz xəta baş verdi. Texniki dəstək məlumatlandırıldı."
            )


# Singleton Instance
orchestrator = Orchestrator()
