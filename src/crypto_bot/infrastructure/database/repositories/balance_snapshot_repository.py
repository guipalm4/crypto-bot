"""Balance Snapshot repository implementation."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_bot.domain.exceptions import RepositoryError
from crypto_bot.infrastructure.database.models.balance_snapshot import BalanceSnapshot
from crypto_bot.infrastructure.database.repositories.base_repository import (
    BaseRepository,
)


class BalanceSnapshotRepository(BaseRepository[BalanceSnapshot]):
    """Repository for BalanceSnapshot entities with deduplication support."""

    def __init__(self, session: AsyncSession):
        """
        Initialize balance snapshot repository.

        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session, BalanceSnapshot)

    async def exists_at_timestamp(
        self, exchange_id: UUID, asset_id: UUID, snapshot_at: datetime
    ) -> bool:
        """
        Check if a snapshot already exists for the given exchange, asset, and timestamp.

        Args:
            exchange_id: Exchange identifier.
            asset_id: Asset identifier.
            snapshot_at: Snapshot timestamp.

        Returns:
            True if snapshot exists, False otherwise.

        Raises:
            RepositoryError: If check fails.
        """
        try:
            stmt = select(BalanceSnapshot).where(
                BalanceSnapshot.exchange_id == exchange_id,
                BalanceSnapshot.asset_id == asset_id,
                BalanceSnapshot.snapshot_at == snapshot_at,
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to check existence of balance snapshot: {str(e)}"
            ) from e

    async def create_if_not_exists(
        self, entity: BalanceSnapshot
    ) -> BalanceSnapshot | None:
        """
        Create a snapshot only if it doesn't already exist (deduplication).

        Args:
            entity: The snapshot entity to create.

        Returns:
            The created entity if it was created, None if it already existed.

        Raises:
            RepositoryError: If creation fails.
        """
        exists = await self.exists_at_timestamp(
            entity.exchange_id, entity.asset_id, entity.snapshot_at
        )
        if exists:
            return None

        try:
            return await self.create(entity)
        except Exception as e:
            # Handle case where duplicate was inserted between check and create
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                return None
            raise

    async def get_by_exchange_and_asset(
        self,
        exchange_id: UUID,
        asset_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[BalanceSnapshot]:
        """
        Get snapshots for a specific exchange and asset.

        Args:
            exchange_id: Exchange identifier.
            asset_id: Asset identifier.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of balance snapshots ordered by snapshot_at descending.

        Raises:
            RepositoryError: If retrieval fails.
        """
        try:
            stmt = (
                select(BalanceSnapshot)
                .where(
                    BalanceSnapshot.exchange_id == exchange_id,
                    BalanceSnapshot.asset_id == asset_id,
                )
                .order_by(BalanceSnapshot.snapshot_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to get balance snapshots: {str(e)}") from e

    async def get_latest(
        self, exchange_id: UUID, asset_id: UUID
    ) -> BalanceSnapshot | None:
        """
        Get the most recent snapshot for an exchange and asset.

        Args:
            exchange_id: Exchange identifier.
            asset_id: Asset identifier.

        Returns:
            The latest balance snapshot or None if none exists.

        Raises:
            RepositoryError: If retrieval fails.
        """
        snapshots = await self.get_by_exchange_and_asset(exchange_id, asset_id, limit=1)
        return snapshots[0] if snapshots else None
