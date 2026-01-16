"""Serper.dev research source for SERP data."""

from dataclasses import dataclass, field

from ..serper import SerperClient
from ..serper.client import SearchResult, OrganicResult, PeopleAlsoAsk


@dataclass
class KeywordSuggestions:
    """Keyword autocomplete results."""

    query: str
    suggestions: list[str] = field(default_factory=list)


@dataclass
class SerpAnalysis:
    """SERP analysis for a query."""

    query: str
    results: list[OrganicResult] = field(default_factory=list)
    people_also_ask: list[PeopleAlsoAsk] = field(default_factory=list)
    related_searches: list[str] = field(default_factory=list)


class SerperResearch:
    """Research source using Serper.dev for Google SERP data."""

    name = "serper"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def get_keywords(self, query: str) -> KeywordSuggestions:
        """
        Get keyword suggestions (autocomplete).

        Args:
            query: Seed keyword

        Returns:
            KeywordSuggestions with suggestions list
        """
        async with SerperClient(self.api_key) as client:
            suggestions = await client.autocomplete(query)
            return KeywordSuggestions(query=query, suggestions=suggestions)

    async def get_serp(
        self,
        query: str,
        num: int = 10,
        gl: str = "us",
    ) -> SerpAnalysis:
        """
        Get SERP analysis (who ranks for a query).

        Args:
            query: Search query
            num: Number of results
            gl: Country code

        Returns:
            SerpAnalysis with organic results, PAA, and related searches
        """
        async with SerperClient(self.api_key) as client:
            result = await client.search(query, num=num, gl=gl)
            return SerpAnalysis(
                query=query,
                results=result.organic,
                people_also_ask=result.people_also_ask,
                related_searches=result.related_searches,
            )

    async def get_paa(self, query: str, gl: str = "us") -> list[PeopleAlsoAsk]:
        """
        Get People Also Ask questions.

        Args:
            query: Search query
            gl: Country code

        Returns:
            List of PAA items
        """
        async with SerperClient(self.api_key) as client:
            result = await client.search(query, num=10, gl=gl)
            return result.people_also_ask

    async def get_related(self, query: str, gl: str = "us") -> list[str]:
        """
        Get related searches.

        Args:
            query: Search query
            gl: Country code

        Returns:
            List of related search queries
        """
        async with SerperClient(self.api_key) as client:
            result = await client.search(query, num=10, gl=gl)
            return result.related_searches
