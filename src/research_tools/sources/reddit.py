"""Reddit research source - subreddit monitoring for content ideas."""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx


@dataclass
class RedditPost:
    """Reddit post data for research."""

    id: str
    title: str
    url: str
    permalink: str
    author: str
    subreddit: str
    score: int
    upvote_ratio: float
    comments: int
    created_at: datetime
    flair: str | None = None


class RedditResearch:
    """Reddit subreddit research - hot/new/rising/top posts."""

    USER_AGENT = "blog-tools/1.0 (research)"
    BASE_URL = "https://www.reddit.com"

    @property
    def name(self) -> str:
        return "reddit"

    def _parse_post(self, data: dict) -> RedditPost:
        """Parse Reddit API response into RedditPost."""
        post = data.get("data", {})
        created_utc = datetime.fromtimestamp(
            post.get("created_utc", 0), tz=timezone.utc
        )

        return RedditPost(
            id=post.get("id", ""),
            title=post.get("title", ""),
            url=post.get("url", ""),
            permalink=f"https://reddit.com{post.get('permalink', '')}",
            author=post.get("author", "[deleted]"),
            subreddit=post.get("subreddit", ""),
            score=post.get("score", 0),
            upvote_ratio=post.get("upvote_ratio", 0),
            comments=post.get("num_comments", 0),
            created_at=created_utc,
            flair=post.get("link_flair_text"),
        )

    async def _fetch_subreddit(
        self,
        client: httpx.AsyncClient,
        subreddit: str,
        sort: str,
        period: str,
        limit: int,
    ) -> list[RedditPost]:
        """Fetch posts from a single subreddit."""
        url = f"{self.BASE_URL}/r/{subreddit}/{sort}.json"
        params: dict = {"limit": min(limit, 100)}

        # 't' param only applies to 'top' and 'controversial' sorts
        if sort in ("top", "controversial"):
            params["t"] = period

        try:
            response = await client.get(
                url,
                params=params,
                headers={"User-Agent": self.USER_AGENT},
                follow_redirects=True,
            )
            response.raise_for_status()
            data = response.json()

            children = data.get("data", {}).get("children", [])
            return [self._parse_post(child) for child in children]

        except httpx.HTTPStatusError:
            return []
        except Exception:
            return []

    async def fetch_posts(
        self,
        subreddits: list[str],
        sort: str = "hot",
        period: str = "week",
        limit: int = 25,
    ) -> list[RedditPost]:
        """
        Fetch posts from multiple subreddits.

        Args:
            subreddits: List of subreddit names (without r/)
            sort: hot, new, rising, top, controversial
            period: hour, day, week, month, year, all (for top/controversial)
            limit: Max posts per subreddit

        Returns:
            List of RedditPost objects sorted by score
        """
        posts: list[RedditPost] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for subreddit in subreddits:
                sub_posts = await self._fetch_subreddit(
                    client, subreddit, sort, period, limit
                )
                posts.extend(sub_posts)
                # Small delay between subreddits
                if len(subreddits) > 1:
                    await asyncio.sleep(0.2)

        # Sort by score (highest first)
        posts.sort(key=lambda p: p.score, reverse=True)
        return posts
