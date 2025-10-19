"""Position repository implementation."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from crypto_bot.domain.repositories.position_repository import IPositionRepository
from crypto_bot.domain.exceptions import RepositoryError
from crypto_bot.infrastructure.database.models import Position, PositionStatus
from crypto_bot.infrastructure.database.repositories.base_repository import (
    BaseRepository,
)


class PositionRepository(BaseRepository[Position], IPositionRepository):
    """Repository for Position entities."""

    def __init__(self, session: AsyncSession):
        """
        Initialize position repository.

        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session, Position)

    async def get_by_status(
        self, status: PositionStatus, skip: int = 0, limit: int = 100
    ) -> List[Position]:
        """Get positions by status."""
        try:
            stmt = (
                select(Position)
                .where(Position.status == status)
                .offset(skip)
                .limit(limit)
                .order_by(Position.opened_at.desc())
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get positions by status {status}: {str(e)}"
            ) from e

    async def get_by_trading_pair(
        self, trading_pair_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Position]:
        """Get positions by trading pair."""
        try:
            stmt = (
                select(Position)
                .where(Position.trading_pair_id == trading_pair_id)
                .offset(skip)
                .limit(limit)
                .order_by(Position.opened_at.desc())
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get positions by trading_pair {trading_pair_id}: {str(e)}"
            ) from e

    async def get_by_strategy(
        self, strategy_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Position]:
        """Get positions by strategy."""
        try:
            stmt = (
                select(Position)
                .where(Position.strategy_id == strategy_id)
                .offset(skip)
                .limit(limit)
                .order_by(Position.opened_at.desc())
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get positions by strategy {strategy_id}: {str(e)}"
            ) from e

    async def get_open_positions(
        self,
        exchange_id: Optional[UUID] = None,
        trading_pair_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Position]:
        """Get all open positions."""
        try:
            stmt = select(Position).where(Position.status == PositionStatus.OPEN)

            if exchange_id:
                stmt = stmt.where(Position.exchange_id == exchange_id)
            if trading_pair_id:
                stmt = stmt.where(Position.trading_pair_id == trading_pair_id)

            stmt = stmt.offset(skip).limit(limit).order_by(Position.opened_at.desc())
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to get open positions: {str(e)}") from e

    async def get_by_entry_order(self, entry_order_id: UUID) -> Optional[Position]:
        """Get position by entry order."""
        try:
            stmt = select(Position).where(Position.entry_order_id == entry_order_id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get position by entry_order {entry_order_id}: {str(e)}"
            ) from e

