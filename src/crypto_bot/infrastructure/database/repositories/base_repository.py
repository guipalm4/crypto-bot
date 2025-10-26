"""
Base repository implementation using SQLAlchemy ORM.

Provides common CRUD operations for all repositories.
"""

from typing import Generic, Protocol, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_bot.domain.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    RepositoryError,
)
from crypto_bot.domain.repositories.base import IRepository
from crypto_bot.infrastructure.database.base import Base


class EntityWithId(Protocol):
    """Protocol for entities that have an ID field."""

    id: UUID


T = TypeVar("T", bound=Base, covariant=False)


class BaseRepository(IRepository[T], Generic[T]):
    """Base repository with common CRUD operations using SQLAlchemy."""

    def __init__(self, session: AsyncSession, model_class: type[T]):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy async session.
            model_class: The SQLAlchemy model class.
        """
        self._session = session
        self._model_class = model_class

    async def create(self, entity: T) -> T:
        """
        Create a new entity.

        Args:
            entity: The entity to create.

        Returns:
            The created entity with generated fields.

        Raises:
            DuplicateEntityError: If unique constraint is violated.
            RepositoryError: If creation fails for other reasons.
        """
        try:
            self._session.add(entity)
            await self._session.flush()
            await self._session.refresh(entity)
            return entity
        except IntegrityError as e:
            await self._session.rollback()
            # Extract field name from error if possible
            error_msg = str(e.orig)
            if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
                raise DuplicateEntityError(
                    entity_type=self._model_class.__name__,
                    field="unknown",
                    value="unknown",
                ) from e
            raise RepositoryError(
                f"Integrity error creating {self._model_class.__name__}: {error_msg}"
            ) from e
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise RepositoryError(
                f"Failed to create {self._model_class.__name__}: {str(e)}"
            ) from e

    async def get_by_id(self, entity_id: UUID) -> T | None:
        """
        Retrieve an entity by its ID.

        Args:
            entity_id: The unique identifier of the entity.

        Returns:
            The entity if found, None otherwise.

        Raises:
            RepositoryError: If retrieval fails.
        """
        try:
            result = await self._session.get(self._model_class, entity_id)
            return result
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get {self._model_class.__name__} by ID {entity_id}: {str(e)}"
            ) from e

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        """
        Retrieve all entities with pagination.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of entities.

        Raises:
            RepositoryError: If retrieval fails.
        """
        try:
            stmt = select(self._model_class).offset(skip).limit(limit)
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get all {self._model_class.__name__}: {str(e)}"
            ) from e

    async def update(self, entity: T) -> T:
        """
        Update an existing entity.

        Args:
            entity: The entity with updated fields. Must have an 'id' attribute.

        Returns:
            The updated entity.

        Raises:
            EntityNotFoundError: If entity not found.
            RepositoryError: If update fails.

        Note:
            This method expects entity to have an 'id' attribute.
            All SQLAlchemy models inheriting from Base should have this attribute.
        """
        try:
            # Type safety: Access ID directly since MyPy can't verify
            # that all Base subclasses have 'id' attribute at compile time
            entity_id = entity.id
            if not isinstance(entity_id, UUID):
                raise RepositoryError(
                    f"Entity {self._model_class.__name__} must have an 'id' attribute of type UUID"
                )
            existing = await self.get_by_id(entity_id)
            if not existing:
                raise EntityNotFoundError(
                    entity_type=self._model_class.__name__,
                    entity_id=str(entity_id),
                )

            # Merge changes
            merged = await self._session.merge(entity)
            await self._session.flush()
            await self._session.refresh(merged)
            return merged
        except EntityNotFoundError:
            raise
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise RepositoryError(
                f"Failed to update {self._model_class.__name__}: {str(e)}"
            ) from e

    async def delete(self, entity_id: UUID) -> bool:
        """
        Delete an entity by its ID.

        Args:
            entity_id: The unique identifier of the entity.

        Returns:
            True if deletion was successful, False if entity not found.

        Raises:
            RepositoryError: If deletion fails.
        """
        try:
            entity = await self.get_by_id(entity_id)
            if not entity:
                return False

            await self._session.delete(entity)
            await self._session.flush()
            return True
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise RepositoryError(
                f"Failed to delete {self._model_class.__name__} {entity_id}: {str(e)}"
            ) from e

    async def exists(self, entity_id: UUID) -> bool:
        """
        Check if an entity exists.

        Args:
            entity_id: The unique identifier of the entity.

        Returns:
            True if the entity exists, False otherwise.

        Raises:
            RepositoryError: If check fails.
        """
        try:
            entity = await self.get_by_id(entity_id)
            return entity is not None
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to check existence of {self._model_class.__name__} {entity_id}: {str(e)}"
            ) from e
