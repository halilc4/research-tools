"""Cache repository for API response caching with TTL."""

import json
from datetime import datetime, timedelta
from typing import Any

from sqlmodel import Session, select

from ..models import CacheEntry
from .base import BaseRepository


class CacheRepository(BaseRepository[CacheEntry]):
    """Repository for cache operations with TTL support."""

    def __init__(self, session: Session):
        super().__init__(session, CacheEntry)

    def get(self, key: str) -> Any | None:
        """Get cached data if exists and not expired."""
        stmt = select(CacheEntry).where(CacheEntry.key == key)
        entry = self.session.exec(stmt).first()

        if entry is None:
            return None

        if entry.is_expired():
            self.session.delete(entry)
            self.session.commit()
            return None

        return json.loads(entry.data)

    def set(self, key: str, data: Any, ttl_hours: int = 24) -> CacheEntry:
        """Set cache data with TTL."""
        stmt = select(CacheEntry).where(CacheEntry.key == key)
        existing = self.session.exec(stmt).first()

        now = datetime.utcnow()
        expires_at = now + timedelta(hours=ttl_hours)

        if existing:
            existing.data = json.dumps(data)
            existing.created_at = now
            existing.expires_at = expires_at
            self.session.commit()
            self.session.refresh(existing)
            return existing

        entry = CacheEntry(
            key=key,
            data=json.dumps(data),
            created_at=now,
            expires_at=expires_at,
        )
        return self.create(entry)

    def invalidate(self, key: str) -> bool:
        """Remove a specific cache entry."""
        stmt = select(CacheEntry).where(CacheEntry.key == key)
        entry = self.session.exec(stmt).first()

        if entry:
            self.session.delete(entry)
            self.session.commit()
            return True
        return False

    def cleanup(self) -> int:
        """Remove all expired cache entries. Returns count of deleted."""
        now = datetime.utcnow()
        stmt = select(CacheEntry).where(CacheEntry.expires_at < now)
        expired = list(self.session.exec(stmt).all())

        for entry in expired:
            self.session.delete(entry)

        self.session.commit()
        return len(expired)

    def clear_all(self) -> int:
        """Clear entire cache. Returns count of deleted."""
        all_entries = self.get_all()
        for entry in all_entries:
            self.session.delete(entry)
        self.session.commit()
        return len(all_entries)

    def stats(self) -> dict:
        """Get cache statistics."""
        all_entries = self.get_all()
        now = datetime.utcnow()

        valid = [e for e in all_entries if not e.is_expired()]
        expired = [e for e in all_entries if e.is_expired()]

        return {
            "total": len(all_entries),
            "valid": len(valid),
            "expired": len(expired),
        }
