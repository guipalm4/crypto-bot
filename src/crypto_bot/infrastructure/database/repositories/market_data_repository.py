"""Market Data repository implementation."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_bot.domain.exceptions import RepositoryError
from crypto_bot.infrastructure.database.models.market_data import MarketData
from crypto_bot.infrastructure.database.repositories.base_repository import (
    BaseRepository,
)


class MarketDataRepository(BaseRepository[MarketData]):
    """Repository for MarketData entities with deduplication support."""

    def __init__(self, session: AsyncSession):
        """
        Initialize market data repository.

        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session, MarketData)

    async def exists_at_timestamp(
        self,
        trading_pair_id: UUID,
        exchange_id: UUID,
        timeframe: str,
        timestamp: datetime,
    ) -> bool:
        """
        Check if market data already exists for the given parameters.

        Args:
            trading_pair_id: Trading pair identifier.
            exchange_id: Exchange identifier.
            timeframe: Timeframe string (e.g., "1m", "1h").
            timestamp: Data timestamp.

        Returns:
            True if market data exists, False otherwise.

        Raises:
            RepositoryError: If check fails.
        """
        try:
            stmt = select(MarketData).where(
                MarketData.trading_pair_id == trading_pair_id,
                MarketData.exchange_id == exchange_id,
                MarketData.timeframe == timeframe,
                MarketData.timestamp == timestamp,
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to check existence of market data: {str(e)}"
            ) from e

    async def create_if_not_exists(self, entity: MarketData) -> MarketData | None:
        """
        Create market data only if it doesn't already exist (deduplication).

        Args:
            entity: The market data entity to create.

        Returns:
            The created entity if it was created, None if it already existed.

        Raises:
            RepositoryError: If creation fails.
        """
        exists = await self.exists_at_timestamp(
            entity.trading_pair_id,
            entity.exchange_id,
            entity.timeframe,
            entity.timestamp,
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

    async def get_by_trading_pair_and_timeframe(
        self,
        trading_pair_id: UUID,
        exchange_id: UUID,
        timeframe: str,
        since: datetime | None = None,
        until: datetime | None = None,
        skip: int = 0,
        limit: int = 1000,
    ) -> list[MarketData]:
        """
        Get market data for a specific trading pair and timeframe.

        Args:
            trading_pair_id: Trading pair identifier.
            exchange_id: Exchange identifier.
            timeframe: Timeframe string (e.g., "1m", "1h").
            since: Optional start timestamp (inclusive).
            until: Optional end timestamp (inclusive).
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of market data records ordered by timestamp ascending.

        Raises:
            RepositoryError: If retrieval fails.
        """
        try:
            stmt = select(MarketData).where(
                MarketData.trading_pair_id == trading_pair_id,
                MarketData.exchange_id == exchange_id,
                MarketData.timeframe == timeframe,
            )

            if since:
                stmt = stmt.where(MarketData.timestamp >= since)
            if until:
                stmt = stmt.where(MarketData.timestamp <= until)

            stmt = stmt.order_by(MarketData.timestamp.asc()).offset(skip).limit(limit)

            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to get market data: {str(e)}") from e

    async def get_latest(
        self,
        trading_pair_id: UUID,
        exchange_id: UUID,
        timeframe: str,
    ) -> MarketData | None:
        """
        Get the most recent market data for a trading pair and timeframe.

        Args:
            trading_pair_id: Trading pair identifier.
            exchange_id: Exchange identifier.
            timeframe: Timeframe string (e.g., "1m", "1h").

        Returns:
            The latest market data record or None if none exists.

        Raises:
            RepositoryError: If retrieval fails.
        """
        try:
            stmt = (
                select(MarketData)
                .where(
                    MarketData.trading_pair_id == trading_pair_id,
                    MarketData.exchange_id == exchange_id,
                    MarketData.timeframe == timeframe,
                )
                .order_by(MarketData.timestamp.desc())
                .limit(1)
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to get latest market data: {str(e)}") from e
