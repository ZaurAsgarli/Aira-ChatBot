import logging
from typing import Tuple, List, Any

# Tools & Config
from langchain_community.tools.tavily_search import TavilySearchResults
from src.config import settings

# Models & Utils
from src.models.chat_schema import Source
from src.utils.citation_utils import parse_tavily_results, format_sources_for_llm

logger = logging.getLogger(__name__)


class WebSearchService:
    """
    Wrapper around Tavily API.
    Returns both a text summary for the LLM and structured citations for the UI.
    """

    def __init__(self):
        self.tool = None
        api_key = settings.TAVILY_API_KEY

        # 1. Validation
        if not settings.SEARCH_ENABLED or not api_key or not api_key.startswith("tvly"):
            logger.warning("⚠️ Tavily API Key missing or invalid. Search is disabled.")
            return

        # 2. Initialization
        try:
            # max_results=5 gives us enough sources to filter the best ones
            self.tool = TavilySearchResults(tavily_api_key=api_key, max_results=5)
            logger.info("✅ Tavily Search Service activated.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Tavily: {e}")
            self.tool = None

    def search(self, query: str) -> Tuple[str, List[Source]]:
        """
        Executes web search.

        Returns:
            Tuple[str, List[Source]]:
            - str: Formatted text for the AI context (e.g. "1. Python is... (Source: url)")
            - List[Source]: Structured objects for the Frontend UI citations.
        """
        # Default empty return
        if not self.tool:
            return "", []

        try:
            logger.info(f"🔎 Searching Web: {query}")

            # Execute Search
            raw_results = self.tool.invoke({"query": query})

            # 1. Parse into Structured Data (for UI)
            sources = parse_tavily_results(raw_results)

            # 2. Format into Text (for LLM Context)
            formatted_text = format_sources_for_llm(sources)

            return formatted_text, sources

        except Exception as e:
            logger.error(f"❌ Search operation failed: {e}")
            return "", []


# Singleton instance
websearch_service = WebSearchService()
