import logging
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from src.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """
    Manages interactions with Qdrant Cloud.
    Handles connection, collection creation, and vector uploading.
    """

    def __init__(self):
        # Initialize connection to Qdrant Cloud
        try:
            self.client = QdrantClient(
                url=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
            )
            # Test connection
            self.client.get_collections()
            logger.info(f"✅ Connected to Qdrant at {settings.QDRANT_HOST}")
        except Exception as e:
            logger.critical(f"❌ Failed to connect to Qdrant: {e}")
            raise e

    def ensure_collection_exists(self, collection_name: str, vector_size: int = 1536):
        """
        Checks if a collection exists. If not, creates it with the correct config.
        Default vector_size 1536 is for OpenAI text-embedding-3-small.
        """
        try:
            self.client.get_collection(collection_name)
            logger.info(f"Collection '{collection_name}' exists.")
        except (UnexpectedResponse, Exception):
            logger.warning(f"Collection '{collection_name}' not found. Creating...")

            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size, distance=models.Distance.COSINE
                ),
            )
            logger.info(f"✅ Collection '{collection_name}' created successfully.")

    def upload_vectors(self, collection_name: str, points: List[models.PointStruct]):
        """
        Uploads a batch of vectors (points) to Qdrant.
        """
        if not points:
            logger.warning("No points provided for upload.")
            return

        try:
            operation_info = self.client.upsert(
                collection_name=collection_name, wait=True, points=points
            )
            logger.info(
                f"Upserted {len(points)} points to '{collection_name}'. Status: {operation_info.status}"
            )
        except Exception as e:
            logger.error(f"Failed to upload vectors to {collection_name}: {e}")

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        Performs a semantic search in Qdrant.
        """
        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            )

            # Convert Qdrant objects to clean dictionaries
            return [
                {"id": hit.id, "score": hit.score, "payload": hit.payload}
                for hit in results
            ]
        except Exception as e:
            logger.error(f"Search failed in {collection_name}: {e}")
            return []


# Singleton instance
vector_store = VectorStoreService()
