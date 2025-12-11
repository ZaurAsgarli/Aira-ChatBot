"""
MynEra Aira - NEVER-FAIL Semantic Matching Engine
3-Tier Fallback: Vector → Keyword → Bestsellers (ALWAYS returns results)
"""

import logging
from typing import List, Tuple, Optional, Dict, Any

from src.config import settings
from src.services.vector_store import vector_store
from src.services.embedding_service import embedding_service
from src.models.chat_schema import Recommendation
from src.models.data_schemas import Course, Mentor

logger = logging.getLogger(__name__)


# ==============================================================================
# 📏 SCORING THRESHOLDS
# ==============================================================================
THRESHOLD_EXACT = 0.70
THRESHOLD_RELATED = 0.50
THRESHOLD_KEYWORD = 0.35  # Below this, use keyword matching


# ==============================================================================
# 🏆 BESTSELLER INVENTORY (Fallback + Keyword Matching)
# Each course has extensive tags for synonym matching
# ==============================================================================
BESTSELLER_COURSES = [
    {
        "id": "bs_python_backend",
        "title": "Python Backend İnkişafına Giriş",
        "type": "course",
        "description": "Django və FastAPI ilə REST API yaratmaq. Sıfırdan production-ready backend.",
        "category": "Backend Development",
        "tags": [
            "python", "django", "fastapi", "backend", "server", "api", "rest",
            "database", "sql", "proqramlaşdırma", "programming", "kod", "code",
            "server-side", "back-end", "flask", "postgresql", "mysql"
        ],
        "meta": {
            "difficulty": "Beginner",
            "duration": "22 saat",
            "rating": 4.8,
            "students": 214,
            "mentor": "Elçin Məmmədli"
        }
    },
    {
        "id": "bs_frontend_react",
        "title": "Frontend Roadmap: HTML-dən React-ə",
        "type": "course",
        "description": "Tam frontend yol xəritəsi: HTML, CSS, JavaScript, React. Veb developer ol.",
        "category": "Frontend Development",
        "tags": [
            "frontend", "html", "css", "javascript", "react", "vue", "angular",
            "web", "veb", "sayt", "site", "ui", "interface", "dizayn", "design",
            "front-end", "responsive", "tailwind", "bootstrap", "next.js"
        ],
        "meta": {
            "difficulty": "Beginner",
            "duration": "35 saat",
            "rating": 4.8,
            "students": 390,
            "mentor": "Nigar Qasımova"
        }
    },
    {
        "id": "bs_data_science",
        "title": "Data Analitikası üçün Python",
        "type": "course",
        "description": "Pandas, NumPy, Matplotlib ilə data analizi. Data Science-ə giriş.",
        "category": "Data Science",
        "tags": [
            "data", "analiz", "analytics", "science", "python", "pandas", "numpy",
            "matplotlib", "ml", "machine learning", "ai", "süni intellekt",
            "statistika", "visualization", "tableau", "power bi", "excel"
        ],
        "meta": {
            "difficulty": "Beginner",
            "duration": "20 saat",
            "rating": 4.8,
            "students": 310,
            "mentor": "Aysel Əhmədova"
        }
    },
    {
        "id": "bs_cybersecurity",
        "title": "Kiber Təhlükəsizlik Əsasları",
        "type": "course",
        "description": "Network security, penetration testing, ethical hacking əsasları.",
        "category": "Cybersecurity",
        "tags": [
            "security", "təhlükəsizlik", "hacking", "hack", "hacker", "pentesting",
            "penetration", "network", "şəbəkə", "cyber", "firewall", "virus",
            "malware", "ethical", "kali", "linux", "ctf"
        ],
        "meta": {
            "difficulty": "Intermediate",
            "duration": "25 saat",
            "rating": 4.7,
            "students": 156,
            "mentor": "Murad Əliyev"
        }
    },
    {
        "id": "bs_uiux_design",
        "title": "UI/UX Dizayn Masterclass",
        "type": "course",
        "description": "Figma ilə professional interfeys dizaynı. UX research metodları.",
        "category": "UI/UX Design",
        "tags": [
            "design", "dizayn", "figma", "ui", "ux", "interface", "user experience",
            "photoshop", "adobe", "illustrator", "sketch", "prototyping",
            "wireframe", "mockup", "graphic", "qrafik", "creative"
        ],
        "meta": {
            "difficulty": "Beginner",
            "duration": "18 saat",
            "rating": 4.9,
            "students": 245,
            "mentor": "Ləman Hüseynova"
        }
    },
    {
        "id": "bs_devops",
        "title": "DevOps və Cloud Engineering",
        "type": "course",
        "description": "Docker, Kubernetes, AWS, CI/CD. Infrastructure as Code.",
        "category": "DevOps",
        "tags": [
            "devops", "docker", "kubernetes", "k8s", "aws", "cloud", "azure",
            "gcp", "ci/cd", "jenkins", "gitlab", "linux", "terraform",
            "ansible", "infrastructure", "deployment", "automation"
        ],
        "meta": {
            "difficulty": "Intermediate",
            "duration": "30 saat",
            "rating": 4.7,
            "students": 128,
            "mentor": "Tural Məmmədov"
        }
    },
    {
        "id": "bs_mobile_flutter",
        "title": "Flutter ilə Mobil Tətbiq İnkişafı",
        "type": "course",
        "description": "Cross-platform mobil development. iOS və Android üçün bir kod.",
        "category": "Mobile Development",
        "tags": [
            "mobile", "mobil", "flutter", "dart", "android", "ios", "app",
            "tətbiq", "react native", "swift", "kotlin", "cross-platform",
            "telefon", "phone", "application"
        ],
        "meta": {
            "difficulty": "Beginner",
            "duration": "28 saat",
            "rating": 4.8,
            "students": 189,
            "mentor": "Orxan Rəhimli"
        }
    },
    {
        "id": "bs_sql_database",
        "title": "SQL və Database İdarəetmə",
        "type": "course",
        "description": "PostgreSQL, MySQL ilə database dizaynı və query optimization.",
        "category": "Database",
        "tags": [
            "sql", "database", "verilənlər bazası", "postgresql", "mysql",
            "mongodb", "nosql", "query", "data", "oracle", "sqlite",
            "normalization", "index", "optimization"
        ],
        "meta": {
            "difficulty": "Beginner",
            "duration": "15 saat",
            "rating": 4.6,
            "students": 276,
            "mentor": "Fərid Hüseynov"
        }
    }
]

# List-all triggers
LIST_ALL_TRIGGERS = [
    "all", "bütün", "hamısı", "siyahı", "list", "başqa", "other",
    "digər", "daha çox", "more", "nə var", "what else", "show all",
    "göstər", "kurslar", "courses", "bütün kurslar"
]


class MatchingEngine:
    """
    NEVER-FAIL Semantic Matching Engine.
    
    3-Tier Fallback Strategy:
    1. Vector Search (Qdrant)
    2. Keyword Matching (Bestseller tags)
    3. Popular Fallback (All Bestsellers)
    
    BUSINESS RULE: This function MUST ALWAYS return results!
    """

    def __init__(self):
        self.exact_threshold = THRESHOLD_EXACT
        self.related_threshold = THRESHOLD_RELATED
        self.keyword_threshold = THRESHOLD_KEYWORD

    def find_matches(self, query: str, limit: int = 5) -> Tuple[List[Recommendation], str]:
        """
        NEVER-FAIL search with 3-tier fallback.
        ✨ NEW: Intelligent price filtering and popularity sorting
        """
        recommendations = []
        context_text = ""
        q_lower = query.lower()
        
        # ===== DETECT BUDGET INTENT =====
        budget_keywords = ["ucuz", "cheap", "budget", "student", "tələbə", "ucuzdu", "sərfəli"]
        is_budget_query = any(kw in q_lower for kw in budget_keywords)
        price_filter = 50 if is_budget_query else None
        
        # ===== DETECT POPULARITY INTENT =====
        popularity_keywords = ["best", "popular", "ən yaxşı", "məşhur", "ən çox seçilən", "top"]
        is_popularity_query = any(kw in q_lower for kw in popularity_keywords)
        
        logger.info(f"🔍 Query analysis: budget_filter={price_filter}, popularity_sort={is_popularity_query}")
        
        # ===== CHECK FOR "LIST ALL" REQUEST =====
        is_list_all = any(trigger in q_lower for trigger in LIST_ALL_TRIGGERS)
        
        if is_list_all:
            logger.info("📋 List-all request. Returning full inventory.")
            return self._build_full_inventory()
        
        try:
            # ===== TIER 1: Vector Search =====
            logger.info(f"🔍 Tier 1: Vector search for: '{query}'")
            
            query_vector = embedding_service.get_embedding(query)
            
            course_hits = vector_store.search(
                settings.COLLECTION_COURSES, 
                query_vector, 
                limit=limit * 2,  # Get more to apply filters
                score_threshold=self.keyword_threshold
            )
            mentor_hits = vector_store.search(
                settings.COLLECTION_MENTORS, 
                query_vector, 
                limit=3,
                score_threshold=self.keyword_threshold
            )
            
            # ===== APPLY INTELLIGENT FILTERS =====
            if course_hits and price_filter:
                logger.info(f"💰 Applying budget filter: price <= {price_filter} AZN")
                course_hits = [
                    hit for hit in course_hits
                    if hit.get("payload", {}).get("price", 999) <= price_filter
                ]
            
            if course_hits and is_popularity_query:
                logger.info(f"🔥 Sorting by popularity (student_count)")
                course_hits.sort(
                    key=lambda h: h.get("payload", {}).get("student_count", 0),
                    reverse=True
                )
            
            logger.info(f"📊 Tier 1 results (after filters): {len(course_hits)} courses, {len(mentor_hits)} mentors")
            
            # Good vector results - use them
            if course_hits and any(h.get("score", 0) >= self.related_threshold for h in course_hits):
                context_text, recommendations = self._build_from_vector_hits(
                    query, course_hits[:limit], mentor_hits, price_filter, is_popularity_query
                )
                recommendations = self._deduplicate(recommendations)
                logger.info(f"✅ Tier 1 success: {len(recommendations)} results")
                return recommendations, context_text
            
            # ===== TIER 2: Keyword Matching =====
            logger.info(f"🔍 Tier 2: Keyword matching for: '{query}'")
            
            keyword_matches = self._keyword_match(query)
            
            if keyword_matches:
                context_text, recommendations = self._build_from_keywords(query, keyword_matches)
                logger.info(f"✅ Tier 2 success: {len(recommendations)} results")
                return recommendations, context_text
            
        except Exception as e:
            logger.error(f"❌ Search error: {e}", exc_info=True)
        
        # ===== TIER 3: Popular Fallback (NEVER FAIL) =====
        logger.info("🔍 Tier 3: Popular fallback")
        context_text, recommendations = self._build_popular_fallback(query)
        logger.info(f"✅ Tier 3 fallback: {len(recommendations)} popular courses")
        return recommendations, context_text

    def _keyword_match(self, query: str) -> List[Dict]:
        """Match query against bestseller tags."""
        q_lower = query.lower()
        matches = []
        
        for course in BESTSELLER_COURSES:
            # Check each tag
            match_count = 0
            for tag in course["tags"]:
                if tag in q_lower:
                    match_count += 1
            
            if match_count > 0:
                matches.append({
                    "course": course,
                    "match_count": match_count,
                    "match_type": "KEYWORD"
                })
        
        # Sort by match count
        matches.sort(key=lambda x: x["match_count"], reverse=True)
        return matches[:4]

    def _build_full_inventory(self) -> Tuple[List[Recommendation], str]:
        """Return ALL courses for 'list all' requests."""
        recommendations = []
        
        context = "\n📚 **[BÜTÜN KURSLARIMIZ]** - MynEra-da mövcud olan tam siyahı:\n\n"
        
        for course in BESTSELLER_COURSES:
            context += self._format_bestseller_context(course, "ALL") + "\n\n"
            recommendations.append(self._bestseller_to_rec(course, "ALL"))
        
        context += f"\n💡 **Cəmi {len(BESTSELLER_COURSES)} kurs mövcuddur.** Hansı sahə maraqlandırır?\n"
        
        return recommendations, context.strip()

    def _build_from_vector_hits(
        self, query: str, courses: List, mentors: List,
        price_filter: Optional[int] = None,
        is_popularity_query: bool = False
    ) -> Tuple[str, List[Recommendation]]:
        """Build context from vector search results."""
        recommendations = []
        
        # Categorize by score
        exact = [h for h in courses if h.get("score", 0) >= self.exact_threshold]
        related = [h for h in courses if self.related_threshold <= h.get("score", 0) < self.exact_threshold]
        
        # Build header with filters applied
        filter_note = ""
        if price_filter:
            filter_note += f" (💰 Budget-friendly: <{price_filter} AZN)"
        if is_popularity_query:
            filter_note += " (🔥 Sorted by popularity)"
        
        if exact:
            context = f"\n🎯 **[TAM UYĞUN]** - '{query}' üçün {len(exact)} dəqiq nəticə{filter_note}:\n\n"
            match_tag = "TAM_UYĞUN"
        elif related:
            context = f"\n📍 **[YAXIN]** - '{query}' ilə əlaqəli {len(related)} nəticə{filter_note}:\n\n"
            match_tag = "YAXIN"
        else:
            context = f"\n⚡ **[ƏLAQƏLİ]** - '{query}' üzrə tapılan variantlar{filter_note}:\n\n"
            match_tag = "ƏLAQƏLI"
        
        # Process courses
        all_hits = exact[:3] + related[:2] + courses[:2]
        for hit in all_hits[:5]:
            try:
                course = Course(**hit.get("payload", {}))
                score = hit.get("score", 0)
                context += self._format_course_context(course, score) + "\n\n"
                recommendations.append(self._course_to_rec(course, score, match_tag))
            except Exception as e:
                logger.warning(f"Course parse error: {e}")
        
        # Process mentors
        for hit in mentors[:2]:
            try:
                mentor = Mentor(**hit.get("payload", {}))
                score = hit.get("score", 0)
                context += self._format_mentor_context(mentor, score) + "\n\n"
                recommendations.append(self._mentor_to_rec(mentor, score, match_tag))
            except Exception as e:
                logger.warning(f"Mentor parse error: {e}")
        
        return context.strip(), recommendations

    def _build_from_keywords(
        self, query: str, matches: List[Dict]
    ) -> Tuple[str, List[Recommendation]]:
        """Build context from keyword matches."""
        recommendations = []
        
        context = f"\n🏷️ **[KEYWORD MATCH]** - '{query}' ilə əlaqəli kurslar:\n\n"
        
        for match in matches:
            course = match["course"]
            context += self._format_bestseller_context(course, "KEYWORD") + "\n\n"
            recommendations.append(self._bestseller_to_rec(course, "KEYWORD"))
        
        return context.strip(), recommendations

    def _build_popular_fallback(
        self, query: str
    ) -> Tuple[str, List[Recommendation]]:
        """Popular fallback - NEVER returns empty! Marks as ALTERNATIVE."""
        recommendations = []
        
        context = f"""
🏆 **[MATCH: ALTERNATIVE]** - '{query}' üçün tam uyğun kurs tapılmadı.

⚠️ Bu ALTERNATİV tövsiyələrdir. İstifadəçiyə izah et ki, dəqiq kurs yoxdur amma bu kurslar faydalı ola bilər:

"""
        
        for course in BESTSELLER_COURSES[:4]:
            context += self._format_bestseller_context(course, "ALTERNATIVE") + "\n\n"
            recommendations.append(self._bestseller_to_rec(course, "ALTERNATIVE"))
        
        context += "\n💡 **Qeyd:** Bu alternativ tövsiyələrdir. Dəqiq kurs üçün başqa mövzu sual et!\n"
        
        return context.strip(), recommendations

    def _format_course_context(self, course: Course, score: float) -> str:
        """Format course from vector DB."""
        match_pct = int(score * 100)
        
        # Get price and student_count from payload
        price = getattr(course, 'price', None)
        student_count = getattr(course, 'student_count', course.enrollment_count)
        
        # Build context with optional fields
        price_str = f" | 💰 {price:.0f} AZN" if price else ""
        popularity_str = f" | 🔥 {student_count} tələbə" if student_count > 0 else ""
        
        return f"""**📚 {course.title}** (Uyğunluq: {match_pct}%)
├─ Kateqoriya: {course.category}
├─ Səviyyə: {course.difficulty} | Müddət: {course.duration_hours} saat{price_str}{popularity_str}
├─ Reytinq: ⭐ {course.rating}
└─ Təsvir: {course.description[:120]}..."""

    def _format_mentor_context(self, mentor: Mentor, score: float) -> str:
        """Format mentor from vector DB."""
        match_pct = int(score * 100)
        return f"""**👨‍🏫 {mentor.ad}** (Uyğunluq: {match_pct}%)
├─ İxtisas: {mentor.ixtisas}
├─ Təcrübə: {mentor.umumi_tecrube_il} il
└─ Bacarıqlar: {', '.join(mentor.bacariqlar[:4])}"""

    def _format_bestseller_context(self, course: Dict, match_type: str) -> str:
        """Format bestseller course."""
        meta = course["meta"]
        return f"""**📚 {course['title']}** [{match_type}]
├─ Kateqoriya: {course['category']}
├─ Səviyyə: {meta['difficulty']} | Müddət: {meta['duration']}
├─ Reytinq: ⭐ {meta['rating']} ({meta['students']} tələbə)
├─ Mentor: {meta['mentor']}
└─ Təsvir: {course['description']}"""

    def _course_to_rec(self, course: Course, score: float, match_tag: str) -> Recommendation:
        """Convert Course to Recommendation."""
        return Recommendation(
            id=str(course.id),
            title=course.title,
            type="course",
            description=course.description[:150],
            meta={
                "category": course.category,
                "difficulty": course.difficulty,
                "duration": f"{course.duration_hours}h",
                "rating": float(course.rating),
                "score": round(score, 3),
                "match_quality": match_tag
            }
        )

    def _mentor_to_rec(self, mentor: Mentor, score: float, match_tag: str) -> Recommendation:
        """Convert Mentor to Recommendation."""
        return Recommendation(
            id=str(mentor.id),
            title=mentor.ad,
            type="mentor",
            description=mentor.ixtisas,
            meta={
                "specialty": mentor.ixtisas,
                "experience": f"{mentor.umumi_tecrube_il} il",
                "rating": float(mentor.rating),
                "score": round(score, 3),
                "match_quality": match_tag
            }
        )

    def _bestseller_to_rec(self, course: Dict, match_tag: str) -> Recommendation:
        """Convert bestseller dict to Recommendation."""
        return Recommendation(
            id=course["id"],
            title=course["title"],
            type="course",
            description=course["description"],
            meta={
                "category": course["category"],
                "difficulty": course["meta"]["difficulty"],
                "duration": course["meta"]["duration"],
                "rating": course["meta"]["rating"],
                "students": course["meta"]["students"],
                "mentor": course["meta"]["mentor"],
                "match_quality": match_tag
            }
        )

    def _deduplicate(self, recommendations: List[Recommendation]) -> List[Recommendation]:
        """Remove duplicate recommendations."""
        seen_ids = set()
        seen_titles = set()
        unique = []
        
        for rec in recommendations:
            if rec.id not in seen_ids and rec.title not in seen_titles:
                seen_ids.add(rec.id)
                seen_titles.add(rec.title)
                unique.append(rec)
        
        return unique


# Singleton instance
matching_engine = MatchingEngine()
