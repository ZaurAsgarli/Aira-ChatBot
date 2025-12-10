import logging
from openai import OpenAI
from src.config import settings

logger = logging.getLogger(__name__)


class ClarificationService:
    """
    Analyzes queries to see if they are too vague (Ambiguity Check).
    """

    def __init__(self):
        # Initialize a dedicated client here to avoid importing LLMService (Circular Import)
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None
            logger.warning("⚠️ OpenAI API Key missing in ClarificationService.")

    def check_ambiguity(self, query: str) -> str | None:
        """
        Returns a clarifying question string if ambiguous,
        or None if the query is clear.
        """
        if not self.client:
            return None

        # Quick heuristic: Long queries are usually clear
        if len(query.split()) > 5:
            return None

        system_prompt = (
            "You are a helper AI for an IT Education platform. "
            "Determine if the user's query is too vague (e.g., just 'course', 'help', 'python'). "
            "If it is vague, return a polite clarifying question in Azerbaijani. "
            "If it is clear enough (e.g., 'python courses', 'backend roadmap'), return exactly 'CLEAR'."
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Use mini for speed/cost
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.0,
            )

            content = response.choices[0].message.content.strip()

            if "CLEAR" in content:
                return None

            return content

        except Exception as e:
            logger.error(f"Clarification check failed: {e}")
            return None


# Singleton instance
clarification_service = ClarificationService()
