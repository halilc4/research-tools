"""Base repository with common CRUD operations."""

from typing import Generic, TypeVar

from sqlmodel import Session, SQLModel, select

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    """Base repository providing common CRUD operations."""

    def __init__(self, session: Session, model: type[T]):
        self.session = session
        self.model = model

    def get_by_id(self, id: int) -> T | None:
        """Get a record by ID."""
        return self.session.get(self.model, id)

    def get_all(self) -> list[T]:
        """Get all records."""
        return list(self.session.exec(select(self.model)).all())

    def create(self, obj: T) -> T:
        """Create a new record."""
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def delete(self, id: int) -> bool:
        """Delete a record by ID."""
        obj = self.get_by_id(id)
        if obj:
            self.session.delete(obj)
            self.session.commit()
            return True
        return False
