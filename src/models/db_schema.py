# src/models/db_schema.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# --- 1. COURSE MODEL (Based on your "Python Backend" example) ---
class Course(BaseModel):
    id: int
    title: str
    category: str
    sub_category: str
    tags: List[str]
    difficulty: str
    duration_hours: int
    mentor_id: int
    rating: float
    enrollment_count: int
    description: str
    skills_covered: List[str]
    learning_outcomes: List[str]
    prerequisites: List[str]
    content_outline: List[str]
    group_available: bool
    course_creator_type: str
    languages: List[str]


# --- 2. MENTOR MODEL (Based on your "Aysu Məmmədzadə" example) ---
# Note: We keep your Azerbaijani keys to match the JSON file directly.
class Mentor(BaseModel):
    id: int
    ad: str
    yas: int
    cins: str
    tehsil: str
    umumi_tecrube_il: int
    ixtisas: str
    bio: str
    karyera_yolu: str
    kecmis_is_yerleri: List[str] = Field(
        alias="keçmis_is_yerleri"
    )  # Handling special characters if needed
    bacariqlar: List[str]
    diller: List[str]
    consultant_available: bool
    course_creator: bool
    rating: float
    ai_hint: str


# --- 3. LEARNER MODEL (Based on your "Lətafət Kərimli" example) ---
class HistoryItem(BaseModel):
    query: str
    timestamp: str


class Learner(BaseModel):
    id: int
    name: str
    age: int
    general_interests: List[str]
    tech_interests: List[str]
    education_level: str
    current_role: str
    work_experience_years: int
    current_it_knowledge: str
    history: List[HistoryItem]
