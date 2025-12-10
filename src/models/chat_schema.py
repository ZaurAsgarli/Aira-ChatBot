from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

# --- Component Models ---


class Source(BaseModel):
    """Represents a citation (Link icon at bottom of chat)."""

    title: str = Field(..., description="Title of the webpage or document")
    url: Optional[str] = Field(None, description="URL if available")
    snippet: Optional[str] = Field(
        None, description="Short text snippet for hover effect"
    )
    source_type: Literal["web", "database", "internal_knowledge"] = "web"


class Recommendation(BaseModel):
    """Represents a suggested Mentor, Course, or University card."""

    id: str
    title: str = Field(..., description="Name of the course, mentor, or university")
    type: Literal["mentor", "course", "university", "career_path"]
    description: str = Field(..., description="Why is this recommended?")
    url: Optional[str] = Field(None, description="Link to profile or course page")
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extra data like price, rating, admission score, or salary data",
    )


# --- API Request/Response Models ---


class ChatRequest(BaseModel):
    """Data sent from Frontend to Backend."""

    query: str
    user_id: str = "guest_user"
    # This allows the Frontend to control context, making the API stateless
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Previous messages [{'role': 'user', 'content': '...'}]",
    )
    language: str = "az"  # Default to Azerbaijani


class ChatResponse(BaseModel):
    """Data sent from Backend to Frontend."""

    answer: str = Field(..., description="The main markdown text response")

    # Citations (Tavily Results)
    sources: List[Source] = Field(
        default_factory=list, description="List of citations/links"
    )

    # Cards (MynEra Courses/Mentors)
    recommendations: List[Recommendation] = Field(
        default_factory=list, description="Cards to show below the chat"
    )

    # Logic Flags
    needs_clarification: bool = Field(
        False, description="If True, Aira is asking a diagnostic question (Coach Mode)"
    )

    # ✨ NEW: Suggested Chips for UI (e.g. ["Backend", "Frontend", "Data"])
    follow_up_questions: List[str] = Field(
        default_factory=list,
        description="Suggested quick replies for the user to click",
    )
