"""Cache entry model for API response caching."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class CacheEntry(SQLModel, table=True):
    """Cached API response with TTL."""

    __tablename__ = "cache_entries"

    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    data: str  # JSON serialized
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.utcnow() > self.expires_at
