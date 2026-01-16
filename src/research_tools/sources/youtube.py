"""YouTube research source using Serper Videos API."""

from dataclasses import dataclass, field

from ..serper import SerperClient
from ..serper.client import VideoResult


@dataclass
class YouTubeSearchResult:
    """YouTube video search results."""

    query: str
    videos: list[VideoResult] = field(default_factory=list)


class YouTubeResearch:
    """Research source for YouTube videos via Serper Videos API."""

    name = "youtube"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def search(
        self,
        query: str,
        limit: int = 20,
        region: str = "us",
    ) -> YouTubeSearchResult:
        """
        Search for videos.

        Args:
            query: Search query
            limit: Max number of results
            region: Country code (us, gb, rs, etc.)

        Returns:
            YouTubeSearchResult with video list
        """
        async with SerperClient(self.api_key) as client:
            videos = await client.videos(query, num=limit, gl=region)
            return YouTubeSearchResult(query=query, videos=videos)

    async def channel_videos(
        self,
        channel: str,
        limit: int = 20,
        region: str = "us",
    ) -> YouTubeSearchResult:
        """
        Search for videos from a specific channel.

        Args:
            channel: Channel name
            limit: Max number of results
            region: Country code

        Returns:
            YouTubeSearchResult with videos from channel
        """
        query = f'"{channel}" site:youtube.com'
        async with SerperClient(self.api_key) as client:
            videos = await client.videos(query, num=limit, gl=region)
            # Filter to only include videos from matching channel
            filtered = [v for v in videos if channel.lower() in v.channel.lower()]
            return YouTubeSearchResult(query=channel, videos=filtered or videos)

    async def trending(
        self,
        category: str | None = None,
        region: str = "us",
        limit: int = 20,
    ) -> YouTubeSearchResult:
        """
        Get trending videos.

        Args:
            category: Optional category (music, gaming, tech, etc.)
            region: Country code
            limit: Max number of results

        Returns:
            YouTubeSearchResult with trending videos
        """
        if category:
            query = f"trending {category} videos {region}"
        else:
            query = f"trending videos {region}"

        async with SerperClient(self.api_key) as client:
            videos = await client.videos(query, num=limit, gl=region)
            return YouTubeSearchResult(query=query, videos=videos)
