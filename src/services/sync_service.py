import logging
import uuid
from typing import List, Any
from qdrant_client.http import models

from src.config import settings
from src.services.data_loader import data_loader
from src.services.embedding_service import embedding_service
from src.services.vector_store import vector_store

logger = logging.getLogger(__name__)


class SyncService:
    """
    Orchestrates the synchronization between JSON files and Qdrant Cloud.
    It prepares the data, embeds it, and uploads it.
    """

    def sync_all(self):
        """Runs the full sync pipeline for all categories."""
        logger.info("🚀 Starting full database sync...")
        self.sync_mentors()
        self.sync_courses()
        self.sync_learners()
        logger.info("✨ Full sync completed successfully.")

    def _generate_uuid(self, prefix: str, id_value: Any) -> str:
        """Helper to create consistent UUIDs based on ID."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{prefix}_{id_value}"))

    def sync_mentors(self):
        """Process Mentors JSON -> Qdrant"""
        collection = settings.COLLECTION_MENTORS

        # 1. Ensure Collection Exists
        vector_store.ensure_collection_exists(collection)

        # 2. Load Data
        mentors = data_loader.load_mentors()
        if not mentors:
            return

        points = []
        texts_to_embed = []

        logger.info(f"Processing {len(mentors)} mentors...")

        for mentor in mentors:
            # 3. Create Searchable Text (Rich Context)
            # We combine important fields so the AI can find this mentor easily.
            search_text = (
                f"Mentor Name: {mentor.ad}. "
                f"Expertise: {mentor.ixtisas}. "
                f"Skills: {', '.join(mentor.bacariqlar)}. "
                f"Bio: {mentor.bio}. "
                f"Career Path: {mentor.karyera_yolu}."
            )
            texts_to_embed.append(search_text)

        # 4. Generate Embeddings in Batch (Faster/Cheaper)
        vectors = embedding_service.get_embeddings_batch(texts_to_embed)

        # 5. Prepare Qdrant Points
        for i, mentor in enumerate(mentors):
            # Qdrant requires a UUID for the point ID (or integer)
            # We map the integer ID from JSON to a UUID to be safe
            point_id = self._generate_uuid("mentor", mentor.id)

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vectors[i],
                    payload=mentor.model_dump(),  # Stores the full JSON data
                )
            )

        # 6. Upload
        vector_store.upload_vectors(collection, points)

    def sync_courses(self):
        """Process Courses JSON -> Qdrant"""
        collection = settings.COLLECTION_COURSES
        vector_store.ensure_collection_exists(collection)

        courses = data_loader.load_courses()
        if not courses:
            return

        points = []
        texts_to_embed = []

        logger.info(f"Processing {len(courses)} courses...")

        for course in courses:
            # Create rich context for course search
            search_text = (
                f"Course Title: {course.title}. "
                f"Category: {course.category} - {course.sub_category}. "
                f"Difficulty: {course.difficulty}. "
                f"Description: {course.description}. "
                f"Skills: {', '.join(course.skills_covered)}. "
                f"Tags: {', '.join(course.tags)}."
            )
            texts_to_embed.append(search_text)

        vectors = embedding_service.get_embeddings_batch(texts_to_embed)

        for i, course in enumerate(courses):
            point_id = self._generate_uuid("course", course.id)
            points.append(
                models.PointStruct(
                    id=point_id, vector=vectors[i], payload=course.model_dump()
                )
            )

        vector_store.upload_vectors(collection, points)

    def sync_learners(self):
        """
        Process Learners JSON -> Qdrant.
        This is for finding 'look-alike' users or users with similar history.
        """
        collection = settings.COLLECTION_LEARNERS
        vector_store.ensure_collection_exists(collection)

        learners = data_loader.load_learners()
        if not learners:
            return

        points = []
        texts_to_embed = []

        logger.info(f"Processing {len(learners)} learners...")

        for learner in learners:
            # Combine interests and history for matching
            history_text = " ".join([h.query for h in learner.history])
            search_text = (
                f"Learner: {learner.name}. "
                f"Role: {learner.current_role}. "
                f"Interests: {', '.join(learner.tech_interests)}. "
                f"History: {history_text}"
            )
            texts_to_embed.append(search_text)

        vectors = embedding_service.get_embeddings_batch(texts_to_embed)

        for i, learner in enumerate(learners):
            point_id = self._generate_uuid("learner", learner.id)
            points.append(
                models.PointStruct(
                    id=point_id, vector=vectors[i], payload=learner.model_dump()
                )
            )

        vector_store.upload_vectors(collection, points)


# Singleton
sync_service = SyncService()
