"""dev.to research source implementation."""

import asyncio
from datetime import datetime

import httpx

from .base import ResearchSource, Article


class DevToResearch(ResearchSource):
    """dev.to API client for research data."""

    API_BASE = "https://dev.to/api"
    MAX_PER_PAGE = 100

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "devto"

    def _parse_article(self, data: dict) -> Article:
        """Parse API response into Article object."""
        published = data.get("published_at") or data.get("published_timestamp")
        if isinstance(published, str):
            # Handle ISO format with Z suffix
            published = published.replace("Z", "+00:00")
            published_dt = datetime.fromisoformat(published)
        else:
            published_dt = datetime.now()

        tags = data.get("tag_list", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]

        return Article(
            id=data.get("id", 0),
            title=data.get("title", ""),
            url=data.get("url", ""),
            author=data.get("user", {}).get("username", "unknown"),
            reactions=data.get("public_reactions_count", 0),
            comments=data.get("comments_count", 0),
            reading_time=data.get("reading_time_minutes", 0),
            tags=tags,
            published_at=published_dt,
        )

    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        tag: str | None,
        period: int,
        page: int,
        per_page: int,
    ) -> list[dict]:
        """Fetch a single page of articles."""
        params: dict = {
            "top": period,
            "page": page,
            "per_page": per_page,
        }
        if tag:
            params["tag"] = tag

        headers = {}
        if self.api_key:
            headers["api-key"] = self.api_key

        response = await client.get(
            f"{self.API_BASE}/articles",
            params=params,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    async def fetch_articles(
        self,
        tags: list[str] | None = None,
        period: int = 7,
        limit: int = 100,
    ) -> list[Article]:
        """
        Fetch trending articles from dev.to.

        If tags provided, fetches for each tag and deduplicates.
        Otherwise fetches general trending.
        """
        seen_ids: set[int] = set()
        articles: list[Article] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            if tags:
                # Fetch for each tag
                for tag in tags:
                    tag_articles = await self._fetch_for_tag(
                        client, tag, period, limit
                    )
                    for article in tag_articles:
                        if article.id not in seen_ids:
                            seen_ids.add(article.id)
                            articles.append(article)
                            if len(articles) >= limit:
                                break
                    if len(articles) >= limit:
                        break
                    # Small delay between tags to be nice to API
                    await asyncio.sleep(0.1)
            else:
                # Fetch general trending
                articles = await self._fetch_for_tag(client, None, period, limit)

        # Sort by reactions (most popular first)
        articles.sort(key=lambda a: a.reactions, reverse=True)
        return articles[:limit]

    async def _fetch_for_tag(
        self,
        client: httpx.AsyncClient,
        tag: str | None,
        period: int,
        limit: int,
    ) -> list[Article]:
        """Fetch articles for a specific tag with pagination."""
        articles: list[Article] = []
        page = 1
        per_page = min(limit, self.MAX_PER_PAGE)

        while len(articles) < limit:
            try:
                data = await self._fetch_page(client, tag, period, page, per_page)
            except httpx.HTTPStatusError:
                break

            if not data:
                break

            for item in data:
                articles.append(self._parse_article(item))
                if len(articles) >= limit:
                    break

            if len(data) < per_page:
                # No more pages
                break

            page += 1
            # Small delay between pages
            await asyncio.sleep(0.1)

        return articles
