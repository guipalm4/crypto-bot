"""Asset repository implementation."""

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_bot.domain.exceptions import RepositoryError
from crypto_bot.domain.repositories.asset_repository import IAssetRepository
from crypto_bot.infrastructure.database.models import Asset
from crypto_bot.infrastructure.database.repositories.base_repository import (
    BaseRepository,
)


class AssetRepository(BaseRepository[Asset], IAssetRepository):
    """Repository for Asset entities."""

    def __init__(self, session: AsyncSession):
        """
        Initialize asset repository.

        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session, Asset)

    async def get_by_symbol(self, symbol: str) -> Asset | None:
        """Get asset by symbol."""
        try:
            stmt = select(Asset).where(Asset.symbol == symbol)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get asset by symbol {symbol}: {str(e)}"
            ) from e

    async def get_active_assets(self, skip: int = 0, limit: int = 100) -> list[Asset]:
        """Get all active assets."""
        try:
            stmt = (
                select(Asset)
                .where(Asset.is_active == True)  # noqa: E712
                .offset(skip)
                .limit(limit)
                .order_by(Asset.symbol)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to get active assets: {str(e)}") from e

    async def search_by_name(
        self, name: str, skip: int = 0, limit: int = 100
    ) -> list[Asset]:
        """Search assets by name (partial match)."""
        try:
            stmt = (
                select(Asset)
                .where(Asset.name.ilike(f"%{name}%"))
                .offset(skip)
                .limit(limit)
                .order_by(Asset.symbol)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to search assets by name {name}: {str(e)}"
            ) from e
