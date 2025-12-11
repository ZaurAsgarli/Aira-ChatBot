"""
MynEra Aira - User Profiler Service
Extracts metadata from conversation history for personalized matching.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from openai import OpenAI

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """Extracted user metadata for personalized matching."""
    technical_level: str  # "beginner" | "intermediate" | "advanced"
    tone_preference: str  # "formal" | "casual"
    budget_sensitivity: str  # "low" | "high"
    interests: List[str]  # Detected topics
    raw_reasoning: str  # LLM's reasoning

    def to_filters(self) -> Dict:
        """Convert to Qdrant filter conditions."""
        filters = {}
        if self.technical_level == "beginner":
            filters["difficulty"] = ["Başlanğıc", "Başlanğıcdan İrəli"]
        elif self.technical_level == "advanced":
            filters["difficulty"] = ["İrəli", "Orta"]
        return filters


PROFILER_PROMPT = """Analyze the user's messages and extract a profile.

USER MESSAGES:
{messages}

Extract these attributes based on writing style and content:

1. TECHNICAL_LEVEL: 
   - "beginner" = Uses simple language, asks basic questions, mentions "starting out"
   - "intermediate" = Knows some terms, asks specific questions
   - "advanced" = Uses jargon, discusses architecture/optimization

2. TONE_PREFERENCE:
   - "formal" = Academic language, polite, structured
   - "casual" = Slang, emojis, startup/hacker vibe

3. BUDGET_SENSITIVITY:
   - "low" = Asks about prices, discounts, free options
   - "high" = Doesn't mention cost, focuses on quality

4. INTERESTS: List of detected topics (max 3)

Respond in this exact JSON format (no markdown):
{{"technical_level": "...", "tone_preference": "...", "budget_sensitivity": "...", "interests": [...], "reasoning": "..."}}
"""


class UserProfiler:
    """Lightweight LLM-based user profiler."""

    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None
            logger.warning("⚠️ OpenAI key missing for profiler")

    def profile(self, conversation_history: List[Dict[str, str]]) -> UserProfile:
        """Extract user profile from last 5 messages."""
        
        # Default profile
        default = UserProfile(
            technical_level="beginner",
            tone_preference="casual",
            budget_sensitivity="high",
            interests=[],
            raw_reasoning="Default profile (no history)"
        )

        if not self.client or not conversation_history:
            return default

        try:
            # Get last 5 user messages
            user_msgs = [m["content"] for m in conversation_history[-10:] if m.get("role") == "user"][-5:]
            
            if not user_msgs:
                return default

            messages_text = "\n".join([f"- {m}" for m in user_msgs])
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cheap
                messages=[
                    {"role": "system", "content": "You are a user behavior analyst. Output JSON only."},
                    {"role": "user", "content": PROFILER_PROMPT.format(messages=messages_text)}
                ],
                temperature=0.3,
                max_tokens=300
            )

            content = response.choices[0].message.content or "{}"
            
            # Parse JSON
            import json
            # Clean potential markdown
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            data = json.loads(content.strip())
            
            profile = UserProfile(
                technical_level=data.get("technical_level", "beginner"),
                tone_preference=data.get("tone_preference", "casual"),
                budget_sensitivity=data.get("budget_sensitivity", "high"),
                interests=data.get("interests", []),
                raw_reasoning=data.get("reasoning", "")
            )
            
            logger.info(f"👤 Profile: {profile.technical_level}/{profile.tone_preference}")
            return profile

        except Exception as e:
            logger.warning(f"⚠️ Profiler error: {e}")
            return default


user_profiler = UserProfiler()
