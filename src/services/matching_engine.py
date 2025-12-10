import logging
from typing import List, Tuple
from src.config import settings
from src.services.vector_store import vector_store
from src.services.embedding_service import embedding_service
from src.models.chat_schema import Recommendation

logger = logging.getLogger(__name__)


class MatchingEngine:
    """
    Dedicated engine for finding the best Mentors and Courses.
    Separates the 'Search' logic from the 'Chat' logic.
    """

    def find_matches(self, query: str) -> Tuple[List[Recommendation], str]:
        """
        Returns a tuple: (List of Recommendation Objects, Context String for LLM)
        """
        query_vector = embedding_service.get_embedding(query)
        context_text = ""
        recommendations = []

        # 1. Search Mentors
        mentor_hits = vector_store.search(
            settings.COLLECTION_MENTORS, query_vector, limit=2
        )
        for hit in mentor_hits:
            p = hit["payload"]
            # Add to text context for LLM to read
            context_text += (
                f"\n[MENTOR]: {p['ad']} | Skill: {p['ixtisas']} | Bio: {p['bio']}\n"
            )

            # Add structured recommendation card
            recommendations.append(
                Recommendation(
                    id=str(p["id"]),
                    title=p["ad"],
                    type="mentor",
                    description=f"{p['ixtisas']} - {p['bio'][:60]}...",
                    meta={"rating": p.get("rating"), "match_score": hit["score"]},
                )
            )

        # 2. Search Courses
        course_hits = vector_store.search(
            settings.COLLECTION_COURSES, query_vector, limit=2
        )
        for hit in course_hits:
            p = hit["payload"]
            context_text += f"\n[COURSE]: {p['title']} | Level: {p['difficulty']} | Skills: {p['skills_covered']}\n"

            recommendations.append(
                Recommendation(
                    id=str(p["id"]),
                    title=p["title"],
                    type="course",
                    description=p["description"][:60] + "...",
                    meta={"price": p.get("price"), "match_score": hit["score"]},
                )
            )

        return recommendations, context_text


matching_engine = MatchingEngine()
