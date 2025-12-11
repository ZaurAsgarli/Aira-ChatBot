"""
MynEra Aira - Intelligent Web Research Service
Smart Google search via Serper with garbage filtering and official source boosting.
"""

import logging
import requests
import json
from typing import Tuple, List
from datetime import datetime

from src.config import settings
from src.models.chat_schema import Source

logger = logging.getLogger(__name__)


# ==============================================================================
# 🎯 SEARCH OPTIMIZATION SETTINGS
# ==============================================================================

# Filter out garbage sites that waste context
GARBAGE_FILTERS = [
    "-site:instagram.com",
    "-site:facebook.com",
    "-site:tiktok.com",
    "-site:twitter.com",
    "-site:youtube.com",
    "-site:pinterest.com",
]

# Keywords that trigger official .az domain boosting
OFFICIAL_TRIGGERS = [
    "bal", "qəbul", "keçid", "dim", "universitet", "university",
    "imtahan", "exam", "admission", "score", "magistr", "bakalavr",
    "plan yeri", "ixtisas", "fakültə"
]

# Keywords that need temporal context (current year appended)
TEMPORAL_TRIGGERS = [
    "maaş", "salary", "qiymət", "price", "hal-hazırda", "now",
    "trend", "statistic", "orta"
]


class WebSearchService:
    """
    Intelligent Web Research via Serper (Google).
    
    Features:
    - Garbage filtering (no social media)
    - Official source boosting (site:.az)
    - Temporal context injection
    - Dense information extraction
    - Max 10 results for richer context
    """

    def __init__(self):
        self.api_key = settings.SERPER_API_KEY
        self.base_url = "https://google.serper.dev/search"
        self.current_year = datetime.now().year
        
        if not self.api_key:
            logger.warning("⚠️ Serper API Key missing. Web search disabled.")

    def search(self, query: str) -> Tuple[str, List[Source]]:
        """
        Execute intelligent Google search.
        
        Args:
            query: User's search query
            
        Returns:
            Tuple of (formatted_context, list_of_sources)
        """
        if not self.api_key:
            return "⚠️ Web axtarışı deaktivdir.", []

        try:
            # Step 1: Optimize query
            optimized_query = self._optimize_query(query)
            logger.info(f"🔎 Searching: '{optimized_query}'")

            # Step 2: Execute Serper request
            payload = {
                "q": optimized_query,
                "gl": "az",  # Geolocation: Azerbaijan
                "hl": "az",  # Language: Azerbaijani
                "num": 10    # Fetch 10 results for richer context
            }
            headers = {
                'X-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }

            response = requests.post(
                self.base_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

            # Step 3: Process results
            organic_results = data.get("organic", [])
            
            if not organic_results:
                logger.warning("⚠️ No search results found")
                return self._no_results_context(query), []

            # Step 4: Build context and sources
            context, sources = self._build_context(query, organic_results)
            
            logger.info(f"✅ Returning {len(sources)} search results")
            return context, sources

        except requests.exceptions.Timeout:
            logger.error("❌ Search timeout")
            return "⚠️ Axtarış vaxtı bitdi. Yenidən cəhd edin.", []
        except Exception as e:
            logger.error(f"❌ Search error: {e}", exc_info=True)
            return f"⚠️ Axtarış xətası: {str(e)[:100]}", []

    def _optimize_query(self, query: str) -> str:
        """
        Optimize query for better results.
        - Add garbage filters
        - Boost official sources when relevant
        - Add temporal context when needed
        """
        optimized = query
        q_lower = query.lower()

        # Add garbage filters
        optimized += " " + " ".join(GARBAGE_FILTERS)

        # Boost official .az sources for education queries
        if any(trigger in q_lower for trigger in OFFICIAL_TRIGGERS):
            optimized += " site:.az"
            logger.info("🎯 Boosting official .az sources")

        # Add current year for temporal queries
        if any(trigger in q_lower for trigger in TEMPORAL_TRIGGERS):
            if str(self.current_year) not in query and str(self.current_year - 1) not in query:
                optimized += f" {self.current_year}"
                logger.info(f"📅 Added temporal context: {self.current_year}")

        return optimized.strip()

    def _build_context(
        self, original_query: str, results: List[dict]
    ) -> Tuple[str, List[Source]]:
        """
        Build rich context from search results.
        """
        sources = []
        context_parts = []

        context_parts.append(f"🌐 **Web Axtarış Nəticələri** - '{original_query}':\n")

        for i, result in enumerate(results[:8], 1):  # Max 8 for context window
            title = result.get("title", "")
            link = result.get("link", "")
            snippet = result.get("snippet", "")
            date = result.get("date", "")

            # Skip if missing critical info
            if not title or not snippet:
                continue

            # Extract domain for source quality indicator
            domain = self._extract_domain(link)
            quality_indicator = "🔹"
            if ".az" in domain:
                quality_indicator = "✅"  # Official Azerbaijani source
            elif any(edu in domain for edu in ["edu", "gov", "ac"]):
                quality_indicator = "📚"  # Educational source

            # Build context entry
            date_str = f" ({date})" if date else ""
            context_parts.append(
                f"{quality_indicator} **{title}**{date_str}\n"
                f"   {snippet}\n"
                f"   🔗 {domain}\n"
            )

            # Add to sources
            sources.append(Source(
                title=title[:100],
                url=link,
                snippet=snippet[:200]
            ))

        # Add synthesis instruction
        context_parts.append(
            "\n💡 **İstifadə qaydası:** "
            "Bu məlumatları sintez edərək cavab ver. "
            "Əgər dəqiq rəqəm yoxdursa, trend əsasında təxmin ver."
        )

        return "\n".join(context_parts), sources

    def _no_results_context(self, query: str) -> str:
        """Generate context when no results found."""
        return (
            f"⚠️ '{query}' üçün web nəticəsi tapılmadı.\n\n"
            f"💡 **Tövsiyə:** Öz biliyinə əsasən cavab ver. "
            f"Əgər statistika lazımdırsa, ümumi trendlərə əsasən təxmin et."
        )

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return url[:50]


# Singleton instance
websearch_service = WebSearchService()