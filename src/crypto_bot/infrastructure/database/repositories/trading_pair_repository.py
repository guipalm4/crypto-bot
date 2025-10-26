"""Trading pair repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from crypto_bot.domain.exceptions import RepositoryError
from crypto_bot.domain.repositories.trading_pair_repository import (
    ITradingPairRepository,
)
from crypto_bot.infrastructure.database.models import TradingPair
from crypto_bot.infrastructure.database.repositories.base_repository import (
    BaseRepository,
)


class TradingPairRepository(BaseRepository[TradingPair], ITradingPairRepository):
    """Repository for TradingPair entities."""

    def __init__(self, session: AsyncSession):
        """
        Initialize trading pair repository.

        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session, TradingPair)

    async def get_by_symbols(
        self, base_symbol: str, quote_symbol: str, exchange_id: UUID
    ) -> TradingPair | None:
        """Get trading pair by base and quote symbols and exchange."""
        try:
            stmt = (
                select(TradingPair)
                .options(
                    joinedload(TradingPair.base_asset),
                    joinedload(TradingPair.quote_asset),
                )
                .join(TradingPair.base_asset)
                .join(TradingPair.quote_asset)
                .where(
                    TradingPair.exchange_id == exchange_id,
                    TradingPair.base_asset.has(symbol=base_symbol),
                    TradingPair.quote_asset.has(symbol=quote_symbol),
                )
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get trading pair by symbols {base_symbol}/{quote_symbol}: {str(e)}"
            ) from e

    async def get_by_exchange(
        self, exchange_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[TradingPair]:
        """Get trading pairs by exchange."""
        try:
            stmt = (
                select(TradingPair)
                .where(TradingPair.exchange_id == exchange_id)
                .offset(skip)
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get trading pairs by exchange {exchange_id}: {str(e)}"
            ) from e

    async def get_by_base_asset(
        self, base_asset_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[TradingPair]:
        """Get trading pairs by base asset."""
        try:
            stmt = (
                select(TradingPair)
                .where(TradingPair.base_asset_id == base_asset_id)
                .offset(skip)
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get trading pairs by base_asset {base_asset_id}: {str(e)}"
            ) from e

    async def get_by_quote_asset(
        self, quote_asset_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[TradingPair]:
        """Get trading pairs by quote asset."""
        try:
            stmt = (
                select(TradingPair)
                .where(TradingPair.quote_asset_id == quote_asset_id)
                .offset(skip)
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get trading pairs by quote_asset {quote_asset_id}: {str(e)}"
            ) from e

    async def get_active_pairs(
        self, exchange_id: UUID | None = None, skip: int = 0, limit: int = 100
    ) -> list[TradingPair]:
        """Get all active trading pairs."""
        try:
            stmt = select(TradingPair).where(
                TradingPair.is_active == True  # noqa: E712
            )

            if exchange_id:
                stmt = stmt.where(TradingPair.exchange_id == exchange_id)

            stmt = stmt.offset(skip).limit(limit)
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to get active trading pairs: {str(e)}"
            ) from e
