import logging
import uuid
from typing import List, Any, Union
from qdrant_client.http import models

from src.config import settings
from src.services.data_loader import data_loader
from src.services.embedding_service import embedding_service
from src.services.vector_store import vector_store
from src.models.data_schemas import Course, Mentor
from src.models.db_schema import Learner

logger = logging.getLogger(__name__)


class SyncService:
    """
    Orchestrates the synchronization between JSON files and Qdrant Cloud.
    Uses 'Semantic Concentration' strategy - keywords are repeated to boost 
    their weight in vector search for better relevance.
    """

    # --- Text Optimization Methods (Semantic Concentration) ---
    
    def _optimize_mentor_text(self, mentor: Mentor) -> str:
        """
        Creates a 'Concentrated Signal' string for mentors.
        Repeats key fields (name, skill, tags) to boost vector weight.
        """
        name = mentor.ad
        skill = mentor.ixtisas
        tags = " ".join(mentor.bacariqlar)
        bio = mentor.bio
        # Repeat important keywords for better search relevance
        return f"{name} {skill} {tags} {skill} {bio}"
    
    def _optimize_course_text(self, course: Course) -> str:
        """
        Creates a 'Concentrated Signal' string for courses.
        Repeats title and tags to outweigh description noise.
        """
        title = course.title
        tags = " ".join(course.tags)
        desc = course.description
        # Strategy: "Python Python Backend Backend Django API"
        return f"{title} {tags} {title} {tags} {desc}"
    
    def _optimize_learner_text(self, learner: Learner) -> str:
        """
        Creates a 'Concentrated Signal' string for learners.
        Focuses on interests and history for matching.
        """
        history_text = " ".join([h.query for h in learner.history])
        interests = " ".join(learner.tech_interests)
        role = learner.current_role
        # Repeat interests and role for better matching
        return f"{role} {interests} {role} {interests} {history_text}"

    # --- Sync Methods ---

    def sync_all(self):
        """Runs the full sync pipeline for all categories (incremental upsert)."""
        logger.info("🚀 Starting full database sync...")
        self.sync_mentors()
        self.sync_courses()
        self.sync_learners()
        logger.info("✨ Full sync completed successfully.")
    
    def reindex_all(self):
        """
        Performs a FULL re-index: recreates all collections from scratch.
        Use this when data structure changes or to ensure clean state.
        """
        logger.info("♻️ Starting FULL re-index (recreating collections)...")
        self.reindex_mentors()
        self.reindex_courses()
        self.reindex_learners()
        logger.info("✨ Full re-index completed successfully.")
    
    def reindex_mentors(self):
        """Recreates mentor collection and re-uploads all data."""
        collection = settings.COLLECTION_MENTORS
        vector_store.recreate_collection(collection)
        self._sync_mentors_internal()
    
    def reindex_courses(self):
        """Recreates courses collection and re-uploads all data."""
        collection = settings.COLLECTION_COURSES
        vector_store.recreate_collection(collection)
        self._sync_courses_internal()
    
    def reindex_learners(self):
        """Recreates learners collection and re-uploads all data."""
        collection = settings.COLLECTION_LEARNERS
        vector_store.recreate_collection(collection)
        self._sync_learners_internal()

    def _generate_uuid(self, prefix: str, id_value: Any) -> str:
        """Helper to create consistent UUIDs based on ID."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{prefix}_{id_value}"))

    def sync_mentors(self):
        """Process Mentors JSON -> Qdrant (ensures collection exists first)."""
        collection = settings.COLLECTION_MENTORS
        vector_store.ensure_collection_exists(collection)
        self._sync_mentors_internal()

    def sync_courses(self):
        """Process Courses JSON -> Qdrant (ensures collection exists first)."""
        collection = settings.COLLECTION_COURSES
        vector_store.ensure_collection_exists(collection)
        self._sync_courses_internal()

    def sync_learners(self):
        """Process Learners JSON -> Qdrant (ensures collection exists first)."""
        collection = settings.COLLECTION_LEARNERS
        vector_store.ensure_collection_exists(collection)
        self._sync_learners_internal()

    # --- Internal Sync Methods (Semantic Concentration Strategy) ---

    def _sync_mentors_internal(self):
        """Internal: Upload mentors using semantic concentration."""
        collection = settings.COLLECTION_MENTORS
        mentors = data_loader.load_mentors()
        if not mentors:
            return

        logger.info(f"Processing {len(mentors)} mentors...")
        
        # Use optimized text for better search relevance
        texts_to_embed = [self._optimize_mentor_text(m) for m in mentors]
        vectors = embedding_service.get_embeddings_batch(texts_to_embed)

        points = []
        for i, mentor in enumerate(mentors):
            point_id = self._generate_uuid("mentor", mentor.id)
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vectors[i],
                    payload=mentor.model_dump(),  # Full data for display
                )
            )

        vector_store.upload_vectors(collection, points)
        logger.info(f"✅ Uploaded {len(points)} mentors.")

    def _sync_courses_internal(self):
        """Internal: Upload courses using semantic concentration."""
        collection = settings.COLLECTION_COURSES
        courses = data_loader.load_courses()
        if not courses:
            return

        logger.info(f"Processing {len(courses)} courses...")
        
        # Use optimized text for better search relevance
        texts_to_embed = [self._optimize_course_text(c) for c in courses]
        vectors = embedding_service.get_embeddings_batch(texts_to_embed)

        points = []
        for i, course in enumerate(courses):
            point_id = self._generate_uuid("course", course.id)
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vectors[i],
                    payload=course.model_dump(),  # Full data for display
                )
            )

        vector_store.upload_vectors(collection, points)
        logger.info(f"✅ Uploaded {len(points)} courses.")

    def _sync_learners_internal(self):
        """Internal: Upload learners using semantic concentration."""
        collection = settings.COLLECTION_LEARNERS
        learners = data_loader.load_learners()
        if not learners:
            return

        logger.info(f"Processing {len(learners)} learners...")
        
        # Use optimized text for better search relevance
        texts_to_embed = [self._optimize_learner_text(l) for l in learners]
        vectors = embedding_service.get_embeddings_batch(texts_to_embed)

        points = []
        for i, learner in enumerate(learners):
            point_id = self._generate_uuid("learner", learner.id)
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vectors[i],
                    payload=learner.model_dump(),  # Full data for display
                )
            )

        vector_store.upload_vectors(collection, points)
        logger.info(f"✅ Uploaded {len(points)} learners.")


# Singleton
sync_service = SyncService()
