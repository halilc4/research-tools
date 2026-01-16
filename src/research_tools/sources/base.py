"""Base classes for research sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Article:
    """Represents a fetched article."""

    id: int
    title: str
    url: str
    author: str
    reactions: int
    comments: int
    reading_time: int
    tags: list[str]
    published_at: datetime


@dataclass
class TagStats:
    """Aggregated statistics for a tag."""

    name: str
    article_count: int
    total_reactions: int
    total_comments: int
    avg_reactions: float
    avg_comments: float
    avg_reading_time: float


@dataclass
class AuthorStats:
    """Aggregated statistics for an author."""

    username: str
    article_count: int
    total_reactions: int
    total_comments: int
    avg_reactions: float
    articles: list[Article] = field(default_factory=list)


class ResearchSource(ABC):
    """Abstract base class for research data sources."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Source identifier (e.g., 'devto')."""
        pass

    @abstractmethod
    async def fetch_articles(
        self,
        tags: list[str] | None = None,
        period: int = 7,
        limit: int = 100,
    ) -> list[Article]:
        """
        Fetch articles from the source.

        Args:
            tags: Filter by tags (None = no filter)
            period: Trending period in days
            limit: Maximum articles to fetch

        Returns:
            List of Article objects
        """
        pass
