"""Order repository implementation."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from crypto_bot.domain.repositories.order_repository import IOrderRepository
from crypto_bot.domain.exceptions import RepositoryError
from crypto_bot.infrastructure.database.models import Order, OrderStatus
from crypto_bot.infrastructure.database.repositories.base_repository import (
    BaseRepository,
)


class OrderRepository(BaseRepository[Order], IOrderRepository):
    """Repository for Order entities."""

    def __init__(self, session: AsyncSession):
        """
        Initialize order repository.

        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session, Order)

    async def get_by_exchange_order_id(
        self, exchange_order_id: str, exchange_id: UUID
    ) -> Optional[Order]:
        """Get order by exchange order ID."""
        try:
            stmt = select(Order).where(
                Order.exchange_order_id == exchange_order_id,
                Order.exchange_id == exchange_id,
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get order by exchange_order_id {exchange_order_id}: {str(e)}"
            ) from e

    async def get_by_status(
        self, status: OrderStatus, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get orders by status."""
        try:
            stmt = (
                select(Order)
                .where(Order.status == status)
                .offset(skip)
                .limit(limit)
                .order_by(Order.created_at.desc())
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get orders by status {status}: {str(e)}"
            ) from e

    async def get_by_trading_pair(
        self, trading_pair_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get orders by trading pair."""
        try:
            stmt = (
                select(Order)
                .where(Order.trading_pair_id == trading_pair_id)
                .offset(skip)
                .limit(limit)
                .order_by(Order.created_at.desc())
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get orders by trading_pair {trading_pair_id}: {str(e)}"
            ) from e

    async def get_by_strategy(
        self, strategy_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get orders by strategy."""
        try:
            stmt = (
                select(Order)
                .where(Order.strategy_id == strategy_id)
                .offset(skip)
                .limit(limit)
                .order_by(Order.created_at.desc())
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get orders by strategy {strategy_id}: {str(e)}"
            ) from e

    async def get_open_orders(
        self, exchange_id: Optional[UUID] = None, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get all open orders."""
        try:
            stmt = select(Order).where(
                Order.status.in_(
                    [OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]
                )
            )
            if exchange_id:
                stmt = stmt.where(Order.exchange_id == exchange_id)

            stmt = stmt.offset(skip).limit(limit).order_by(Order.created_at.desc())
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to get open orders: {str(e)}") from e

