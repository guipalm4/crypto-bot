"""Trade repository implementation."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from crypto_bot.domain.repositories.trade_repository import ITradeRepository
from crypto_bot.domain.exceptions import RepositoryError
from crypto_bot.infrastructure.database.models import Trade
from crypto_bot.infrastructure.database.repositories.base_repository import (
    BaseRepository,
)


class TradeRepository(BaseRepository[Trade], ITradeRepository):
    """Repository for Trade entities."""

    def __init__(self, session: AsyncSession):
        """
        Initialize trade repository.

        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session, Trade)

    async def get_by_order(
        self, order_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Trade]:
        """Get trades by order."""
        try:
            stmt = (
                select(Trade)
                .where(Trade.order_id == order_id)
                .offset(skip)
                .limit(limit)
                .order_by(Trade.executed_at.desc())
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get trades by order {order_id}: {str(e)}"
            ) from e

    async def get_by_exchange_trade_id(
        self, exchange_trade_id: str
    ) -> Optional[Trade]:
        """Get trade by exchange trade ID."""
        try:
            stmt = select(Trade).where(Trade.exchange_trade_id == exchange_trade_id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get trade by exchange_trade_id {exchange_trade_id}: {str(e)}"
            ) from e

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Trade]:
        """Get trades within a date range."""
        try:
            stmt = (
                select(Trade)
                .where(
                    Trade.executed_at >= start_date, Trade.executed_at <= end_date
                )
                .offset(skip)
                .limit(limit)
                .order_by(Trade.executed_at.desc())
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get trades by date range: {str(e)}"
            ) from e

