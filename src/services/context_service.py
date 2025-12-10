import logging
from typing import Optional, Dict, Any
from qdrant_client.http import models  # Needed for exact filtering
from src.config import settings
from src.services.vector_store import vector_store

logger = logging.getLogger(__name__)


class ContextService:
    """
    Retrieves User Profile context from Qdrant.

    PRODUCTION CHANGE:
    Now uses 'Scroll' (Exact Filter) instead of 'Search' (Vector Similarity).
    This guarantees we retrieve the correct user profile by ID.
    """

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Searches for a user profile by 'user_id' in the Qdrant payload.
        """
        try:
            # 1. Create a Filter for exact match
            # This is like SQL: WHERE user_id = '...'
            id_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",  # Ensure your JSON payload has this field
                        match=models.MatchValue(value=user_id),
                    )
                ]
            )

            # 2. Use Scroll (Retrieve) instead of Vector Search
            # We access the raw client from vector_store to do this precise operation
            records, _ = vector_store.client.scroll(
                collection_name=settings.COLLECTION_LEARNERS,
                scroll_filter=id_filter,
                limit=1,
                with_payload=True,
                with_vectors=False,  # We don't need the vector, just the data
            )

            if records:
                profile = records[0].payload
                logger.info(
                    f"👤 Found profile for {user_id}: {profile.get('name', 'Unknown')}"
                )
                return profile

            logger.info(f"👤 No profile found for {user_id}. Treating as Guest.")
            return None

        except Exception as e:
            logger.error(f"❌ Failed to fetch user context: {e}")
            return None


context_service = ContextService()
