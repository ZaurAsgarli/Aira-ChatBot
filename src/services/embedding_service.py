import logging
from typing import List
from langchain_openai import OpenAIEmbeddings
from src.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Wrapper around OpenAI's Embedding Model (text-embedding-3-small).
    Converts text into vectors for Qdrant.
    """

    def __init__(self):
        self.model = None

        if not settings.OPENAI_API_KEY:
            logger.critical("❌ OpenAI API Key missing. Embeddings will not work.")
            return

        try:
            # LangChain handles batching and retries automatically
            self.model = OpenAIEmbeddings(
                model=settings.LLM_MODEL_EMBEDDING,
                openai_api_key=settings.OPENAI_API_KEY,
                dimensions=1536,  # Standard for text-embedding-3-small
            )
            logger.info(
                f"✅ Embedding Service initialized ({settings.LLM_MODEL_EMBEDDING})"
            )
        except Exception as e:
            logger.critical(f"❌ Failed to initialize Embeddings: {e}")

    def get_embedding(self, text: str) -> List[float]:
        """
        Embeds a single string (e.g., User Query).
        """
        if not self.model:
            return []

        try:
            # embed_query is optimized for search queries
            return self.model.embed_query(text)
        except Exception as e:
            logger.error(f"Embedding error (single): {e}")
            return []

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of texts (e.g., Course Descriptions for DB upload).
        """
        if not self.model or not texts:
            return []

        try:
            return self.model.embed_documents(texts)
        except Exception as e:
            logger.error(f"Embedding error (batch): {e}")
            return []


# Singleton instance
embedding_service = EmbeddingService()
