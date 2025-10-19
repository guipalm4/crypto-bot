"""Strategy repository implementation."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from crypto_bot.domain.repositories.strategy_repository import IStrategyRepository
from crypto_bot.domain.exceptions import RepositoryError
from crypto_bot.infrastructure.database.models import Strategy
from crypto_bot.infrastructure.database.repositories.base_repository import (
    BaseRepository,
)


class StrategyRepository(BaseRepository[Strategy], IStrategyRepository):
    """Repository for Strategy entities."""

    def __init__(self, session: AsyncSession):
        """
        Initialize strategy repository.

        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session, Strategy)

    async def get_by_name(self, name: str) -> Optional[Strategy]:
        """Get strategy by name."""
        try:
            stmt = select(Strategy).where(Strategy.name == name)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get strategy by name {name}: {str(e)}"
            ) from e

    async def get_by_plugin_name(
        self, plugin_name: str, skip: int = 0, limit: int = 100
    ) -> List[Strategy]:
        """Get strategies by plugin name."""
        try:
            stmt = (
                select(Strategy)
                .where(Strategy.plugin_name == plugin_name)
                .offset(skip)
                .limit(limit)
                .order_by(Strategy.name)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get strategies by plugin_name {plugin_name}: {str(e)}"
            ) from e

    async def get_active_strategies(
        self, skip: int = 0, limit: int = 100
    ) -> List[Strategy]:
        """Get all active strategies."""
        try:
            stmt = (
                select(Strategy)
                .where(Strategy.is_active == True)  # noqa: E712
                .offset(skip)
                .limit(limit)
                .order_by(Strategy.name)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to get active strategies: {str(e)}") from e

