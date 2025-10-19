"""Exchange repository implementation."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from crypto_bot.domain.repositories.exchange_repository import IExchangeRepository
from crypto_bot.domain.exceptions import RepositoryError
from crypto_bot.infrastructure.database.models import Exchange
from crypto_bot.infrastructure.database.repositories.base_repository import (
    BaseRepository,
)


class ExchangeRepository(BaseRepository[Exchange], IExchangeRepository):
    """Repository for Exchange entities."""

    def __init__(self, session: AsyncSession):
        """
        Initialize exchange repository.

        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session, Exchange)

    async def get_by_name(self, name: str) -> Optional[Exchange]:
        """Get exchange by name."""
        try:
            stmt = select(Exchange).where(Exchange.name == name)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get exchange by name {name}: {str(e)}"
            ) from e

    async def get_active_exchanges(
        self, skip: int = 0, limit: int = 100
    ) -> List[Exchange]:
        """Get all active exchanges."""
        try:
            stmt = (
                select(Exchange)
                .where(Exchange.is_active == True)  # noqa: E712
                .offset(skip)
                .limit(limit)
                .order_by(Exchange.name)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to get active exchanges: {str(e)}") from e

    async def get_testnet_exchanges(
        self, skip: int = 0, limit: int = 100
    ) -> List[Exchange]:
        """Get all testnet exchanges."""
        try:
            stmt = (
                select(Exchange)
                .where(Exchange.is_testnet == True)  # noqa: E712
                .offset(skip)
                .limit(limit)
                .order_by(Exchange.name)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to get testnet exchanges: {str(e)}") from e

