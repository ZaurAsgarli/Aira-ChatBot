"""
MynEra Aira - Production-Grade Data Schemas
Pydantic models for Courses and Mentors with helper methods for UI and LLM formatting.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ==============================================================================
# 🎓 COURSE MODEL
# ==============================================================================
class Course(BaseModel):
    """
    Course data model matching courses.json structure.
    Includes helper methods for UI cards and LLM context injection.
    """
    
    id: int
    title: str
    category: str
    sub_category: str
    tags: List[str] = Field(default_factory=list)
    difficulty: str
    duration_hours: int
    mentor_id: Optional[int] = None
    rating: float = 0.0
    enrollment_count: int = 0
    description: str = ""
    skills_covered: List[str] = Field(default_factory=list)
    learning_outcomes: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    content_outline: List[str] = Field(default_factory=list)
    group_available: bool = False
    course_creator_type: str = "mentor"
    languages: List[str] = Field(default_factory=lambda: ["Azərbaycan dili"])
    
    # 🆕 NEW FIELDS (Production-Grade Upgrade)
    price: Optional[float] = None  # Course price in AZN
    student_count: int = 0  # Actual student enrollments (from simulation)
    level: str = ""  # Alias for difficulty (for surgical embedding)
    
    def to_card_format(self) -> Dict[str, Any]:
        """
        Returns a dict optimized for chat UI cards.
        
        Returns:
            Dict with essential fields for frontend rendering
        """
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "sub_category": self.sub_category,
            "difficulty": self.difficulty,
            "duration": f"{self.duration_hours} saat",
            "rating": f"⭐ {self.rating}",
            "enrollment": f"{self.enrollment_count} tələbə",
            "description": self.description[:200] + "..." if len(self.description) > 200 else self.description,
            "tags": self.tags[:5],  # Limit to 5 tags for UI
            "group_available": "✓ Qrup kursu" if self.group_available else "Fərdi",
            "languages": ", ".join(self.languages),
        }
    
    def to_context_string(self, score: Optional[float] = None) -> str:
        """
        Returns formatted string for LLM context injection.
        
        Args:
            score: Optional semantic similarity score (0-1)
            
        Returns:
            Multi-line formatted string with match quality tag
        """
        match_tag = self._get_match_tag(score) if score is not None else ""
        
        context = f"""
{match_tag}🎓 **{self.title}**
├─ Kateqoriya: {self.category} > {self.sub_category}
├─ Səviyyə: {self.difficulty} | Müddət: {self.duration_hours} saat
├─ Reytinq: ⭐ {self.rating} ({self.enrollment_count} tələbə)
├─ Qrup: {'Bəli' if self.group_available else 'Xeyr'}
└─ Təsvir: {self.description[:150]}...

📚 Öyrəniləcək bacarıqlar: {', '.join(self.skills_covered[:5])}
🎯 Nəticələr: {', '.join(self.learning_outcomes[:3])}
⚠️ Tələblər: {', '.join(self.prerequisites) if self.prerequisites else 'Heç bir tələb yoxdur'}
"""
        return context.strip()
    
    def _get_match_tag(self, score: float) -> str:
        """Returns match quality tag based on score."""
        if score >= 0.85:
            return "[MATCH: EXACT ✓] "
        elif score >= 0.70:
            return "[MATCH: RELATED ≈] "
        else:
            return "[MATCH: WEAK ~] "
    
    def get_match_summary(self, score: float) -> Dict[str, Any]:
        """
        Returns match quality metadata.
        
        Args:
            score: Semantic similarity score
            
        Returns:
            Dict with match type, score, and explanation
        """
        if score >= 0.85:
            return {
                "type": "EXACT",
                "score": round(score * 100, 1),
                "explanation": "Sorğunuza tam uyğun kurs",
                "confidence": "high"
            }
        elif score >= 0.70:
            return {
                "type": "RELATED",
                "score": round(score * 100, 1),
                "explanation": "Yaxın alternativ kurs",
                "confidence": "medium"
            }
        else:
            return {
                "type": "WEAK",
                "score": round(score * 100, 1),
                "explanation": "Ümumi alternativ (birbaşa uyğun deyil)",
                "confidence": "low"
            }


# ==============================================================================
# 👨‍🏫 MENTOR MODEL
# ==============================================================================
class Mentor(BaseModel):
    """
    Mentor data model matching mentors.json structure.
    Includes helper methods for UI cards and LLM context injection.
    """
    
    id: int
    ad: str  # Name in Azerbaijani
    yas: int  # Age
    cins: str  # Gender
    tehsil: str  # Education
    umumi_tecrube_il: int  # Years of experience
    ixtisas: str  # Specialty
    bio: str = ""
    karyera_yolu: str = ""  # Career path
    keçmis_is_yerleri: List[str] = Field(default_factory=list)  # Past workplaces
    bacariqlar: List[str] = Field(default_factory=list)  # Skills
    diller: List[str] = Field(default_factory=list)  # Languages
    consultant_available: bool = False
    course_creator: bool = False
    rating: float = 0.0
    ai_hint: str = ""  # AI guidance for matching
    
    # 🆕 NEW FIELD (Production-Grade Upgrade)
    skill_score: int = 70  # Skill score (40-100 range) for pricing algorithm
    
    def to_card_format(self) -> Dict[str, Any]:
        """
        Returns a dict optimized for chat UI cards.
        
        Returns:
            Dict with essential fields for frontend rendering
        """
        return {
            "id": self.id,
            "name": self.ad,
            "age": self.yas,
            "specialty": self.ixtisas,
            "experience": f"{self.umumi_tecrube_il} il təcrübə",
            "rating": f"⭐ {self.rating}",
            "education": self.tehsil,
            "bio": self.bio[:150] + "..." if len(self.bio) > 150 else self.bio,
            "skills": self.bacariqlar[:6],  # Limit to 6 skills
            "languages": ", ".join(self.diller),
            "available_for": {
                "consultation": self.consultant_available,
                "courses": self.course_creator
            }
        }
    
    def to_context_string(self, score: Optional[float] = None) -> str:
        """
        Returns formatted string for LLM context injection.
        
        Args:
            score: Optional semantic similarity score (0-1)
            
        Returns:
            Multi-line formatted string with match quality tag
        """
        match_tag = self._get_match_tag(score) if score is not None else ""
        
        # Build availability string
        availability = []
        if self.consultant_available:
            availability.append("Məsləhət")
        if self.course_creator:
            availability.append("Kurs")
        avail_str = " + ".join(availability) if availability else "Müraciət edin"
        
        context = f"""
{match_tag}👨‍🏫 **{self.ad}** ({self.yas} yaş)
├─ İxtisas: {self.ixtisas}
├─ Təcrübə: {self.umumi_tecrube_il} il | Reytinq: ⭐ {self.rating}
├─ Təhsil: {self.tehsil}
├─ Əsas bacarıqlar: {', '.join(self.bacariqlar[:5])}
├─ Keçmiş iş yerləri: {', '.join(self.keçmis_is_yerleri[:3])}
├─ Mövcud: {avail_str}
└─ Bio: {self.bio[:120]}...

💼 Karyera yolu: {self.karyera_yolu}
"""
        return context.strip()
    
    def _get_match_tag(self, score: float) -> str:
        """Returns match quality tag based on score."""
        if score >= 0.85:
            return "[MATCH: EXACT ✓] "
        elif score >= 0.70:
            return "[MATCH: RELATED ≈] "
        else:
            return "[MATCH: WEAK ~] "
    
    def get_match_summary(self, score: float) -> Dict[str, Any]:
        """
        Returns match quality metadata.
        
        Args:
            score: Semantic similarity score
            
        Returns:
            Dict with match type, score, and explanation
        """
        if score >= 0.85:
            return {
                "type": "EXACT",
                "score": round(score * 100, 1),
                "explanation": "Sorğunuza tam uyğun mentor",
                "confidence": "high"
            }
        elif score >= 0.70:
            return {
                "type": "RELATED",
                "score": round(score * 100, 1),
                "explanation": "Yaxın ixtisasda mentor",
                "confidence": "medium"
            }
        else:
            return {
                "type": "WEAK",
                "score": round(score * 100, 1),
                "explanation": "Ümumi mentor (birbaşa uyğun deyil)",
                "confidence": "low"
            }


# ==============================================================================
# 🧪 HELPER FUNCTIONS
# ==============================================================================
def load_courses_from_json(data: List[Dict[str, Any]]) -> List[Course]:
    """
    Load and validate Course models from JSON data.
    
    Args:
        data: List of course dictionaries from JSON
        
    Returns:
        List of validated Course objects
    """
    courses = []
    for item in data:
        try:
            course = Course(**item)
            courses.append(course)
        except Exception as e:
            print(f"⚠️ Failed to parse course {item.get('id', 'unknown')}: {e}")
    return courses


def load_mentors_from_json(data: List[Dict[str, Any]]) -> List[Mentor]:
    """
    Load and validate Mentor models from JSON data.
    
    Args:
        data: List of mentor dictionaries from JSON
        
    Returns:
        List of validated Mentor objects
    """
    mentors = []
    for item in data:
        try:
            mentor = Mentor(**item)
            mentors.append(mentor)
        except Exception as e:
            print(f"⚠️ Failed to parse mentor {item.get('id', 'unknown')}: {e}")
    return mentors
