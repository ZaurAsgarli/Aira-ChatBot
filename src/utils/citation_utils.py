from typing import List, Dict, Any
from src.models.chat_schema import Source


def parse_tavily_results(results: Any) -> List[Source]:
    """
    Converts raw Tavily API response (List[Dict]) into proper Pydantic Source objects.
    This is essential for populating the 'sources' field in the ChatResponse.
    """
    sources_list = []

    if not isinstance(results, list):
        return []

    for res in results:
        # Safety check for missing keys
        title = res.get("title", res.get("content", "")[:30] + "...")
        url = res.get("url")
        content = res.get("content", "")

        # Only add valid sources with URLs
        if url:
            sources_list.append(
                Source(
                    title=title,
                    url=url,
                    snippet=content[:150] + "...",  # Keep snippet short for UI
                    source_type="web",
                )
            )

    return sources_list


def format_sources_for_llm(sources: List[Source]) -> str:
    """
    Turns the list of Source objects into a text block for GPT to read.
    """
    if not sources:
        return "No external sources found."

    text_block = ""
    for idx, src in enumerate(sources, 1):
        text_block += f"{idx}. {src.snippet} (Source: {src.url})\n"

    return text_block
