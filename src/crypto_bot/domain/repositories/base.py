"""
Base repository interface.

Defines the core CRUD operations that all repositories must implement.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """Base repository interface defining common CRUD operations."""

    @abstractmethod
    async def create(self, entity: T) -> T:
        """
        Create a new entity.

        Args:
            entity: The entity to create.

        Returns:
            The created entity with generated fields (e.g., ID, timestamps).

        Raises:
            RepositoryError: If creation fails.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """
        Update an existing entity.

        Args:
            entity: The entity with updated fields.

        Returns:
            The updated entity.

        Raises:
            RepositoryError: If update fails or entity not found.
        """
        pass

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """
        Delete an entity by its ID.

        Args:
            entity_id: The unique identifier of the entity.

        Returns:
            True if deletion was successful, False otherwise.

        Raises:
            RepositoryError: If deletion fails.
        """
        pass

    @abstractmethod
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
        pass
