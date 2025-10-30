"""
Snapshot Service.

This module provides functionality to periodically record portfolio balance
snapshots and OHLCV market data from exchange plugins.
"""

import asyncio
from datetime import datetime
from decimal import Decimal

from crypto_bot.application.dtos.order import BalanceDTO
from crypto_bot.infrastructure.database.engine import db_engine
from crypto_bot.infrastructure.database.models import (
    Asset,
    BalanceSnapshot,
    Exchange,
    MarketData,
)
from crypto_bot.infrastructure.database.repositories import (
    AssetRepository,
    BalanceSnapshotRepository,
    ExchangeRepository,
    MarketDataRepository,
    TradingPairRepository,
)
from crypto_bot.plugins.registry import exchange_registry
from crypto_bot.utils.logger import get_logger

logger = get_logger(__name__)


class SnapshotService:
    """
    Service for recording portfolio snapshots and market data.

    This service periodically fetches data from exchange plugins and persists
    it to the database, ensuring no duplicates are created.
    """

    def __init__(
        self,
        balance_snapshot_interval: float = 300.0,  # 5 minutes default
        market_data_interval: float = 60.0,  # 1 minute default
        enabled_exchanges: list[str] | None = None,
        enabled_symbols: list[str] | None = None,
        default_timeframe: str = "1m",
    ):
        """
        Initialize snapshot service.

        Args:
            balance_snapshot_interval: Interval in seconds between balance snapshots.
            market_data_interval: Interval in seconds between market data fetches.
            enabled_exchanges: List of exchange names to monitor (None = all).
            enabled_symbols: List of trading pair symbols to monitor (None = all).
            default_timeframe: Default timeframe for OHLCV data (e.g., "1m", "1h").
        """
        self._balance_snapshot_interval = balance_snapshot_interval
        self._market_data_interval = market_data_interval
        self._enabled_exchanges = enabled_exchanges
        self._enabled_symbols = enabled_symbols
        self._default_timeframe = default_timeframe

        self._running = False
        self._balance_task: asyncio.Task | None = None
        self._market_data_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start snapshot recording tasks."""
        if self._running:
            logger.warning("Snapshot service is already running")
            return

        self._running = True
        self._balance_task = asyncio.create_task(self._balance_snapshot_loop())
        self._market_data_task = asyncio.create_task(self._market_data_loop())
        logger.info(
            f"Snapshot service started (balance: {self._balance_snapshot_interval}s, "
            f"market_data: {self._market_data_interval}s)"
        )

    async def stop(self) -> None:
        """Stop snapshot recording tasks."""
        if not self._running:
            logger.warning("Snapshot service is not running")
            return

        self._running = False

        for task in [self._balance_task, self._market_data_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        logger.info("Snapshot service stopped")

    def is_running(self) -> bool:
        """Check if snapshot service is running."""
        return self._running

    async def _balance_snapshot_loop(self) -> None:
        """Main loop for recording balance snapshots."""
        logger.info(
            f"Starting balance snapshot loop with {self._balance_snapshot_interval}s interval"
        )

        try:
            while self._running:
                try:
                    await self._record_balance_snapshots()

                    await asyncio.sleep(self._balance_snapshot_interval)

                except asyncio.CancelledError:
                    logger.info("Balance snapshot loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in balance snapshot loop: {e}", exc_info=True)
                    await asyncio.sleep(self._balance_snapshot_interval)

        except Exception as e:
            logger.critical(f"Fatal error in balance snapshot loop: {e}", exc_info=True)
            self._running = False

    async def _market_data_loop(self) -> None:
        """Main loop for recording market data."""
        logger.info(
            f"Starting market data loop with {self._market_data_interval}s interval"
        )

        try:
            while self._running:
                try:
                    await self._record_market_data()

                    await asyncio.sleep(self._market_data_interval)

                except asyncio.CancelledError:
                    logger.info("Market data loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in market data loop: {e}", exc_info=True)
                    await asyncio.sleep(self._market_data_interval)

        except Exception as e:
            logger.critical(f"Fatal error in market data loop: {e}", exc_info=True)
            self._running = False

    async def _record_balance_snapshots(self) -> None:
        """Record balance snapshots for all enabled exchanges."""
        session_factory = db_engine.get_session_factory()
        async with session_factory() as session:
            try:
                exchange_repo = ExchangeRepository(session)
                asset_repo = AssetRepository(session)
                snapshot_repo = BalanceSnapshotRepository(session)

                # Get enabled exchanges
                exchanges = await self._get_enabled_exchanges(exchange_repo)

                snapshot_count = 0
                skipped_count = 0

                for exchange_model in exchanges:
                    try:
                        # Get exchange plugin instance
                        exchange_plugin = exchange_registry.get_exchange(
                            exchange_model.name
                        )
                        await exchange_plugin.initialize()

                        # Fetch balances
                        balances_data = await exchange_plugin.fetch_balance()
                        if not balances_data:
                            continue

                        # Normalize to dict if single balance returned
                        if isinstance(balances_data, BalanceDTO):
                            balances_dict = {balances_data.currency: balances_data}
                        else:
                            balances_dict = balances_data

                        snapshot_at = datetime.utcnow()

                        # Record snapshot for each currency
                        for currency, balance_dto in balances_dict.items():
                            if balance_dto.total == Decimal("0"):
                                continue  # Skip zero balances

                            # Get or create asset
                            asset_model = await asset_repo.get_by_symbol(currency)
                            if not asset_model:
                                asset_model = Asset(
                                    symbol=currency,
                                    name=currency,
                                    is_active=True,
                                )
                                asset_model = await asset_repo.create(asset_model)

                            # Check for duplicates and create snapshot
                            snapshot = BalanceSnapshot(
                                exchange_id=exchange_model.id,
                                asset_id=asset_model.id,
                                free_balance=float(balance_dto.free),
                                locked_balance=float(balance_dto.used),
                                total_balance=float(balance_dto.total),
                                value_in_usd=None,  # TODO: Calculate from price
                                snapshot_at=snapshot_at,
                            )

                            created = await snapshot_repo.create_if_not_exists(snapshot)
                            if created:
                                snapshot_count += 1
                            else:
                                skipped_count += 1

                    except Exception as e:
                        logger.error(
                            f"Failed to record balance snapshot for {exchange_model.name}: {e}",
                            exc_info=True,
                        )
                        continue

                if snapshot_count > 0 or skipped_count > 0:
                    logger.info(
                        f"Balance snapshots: {snapshot_count} created, "
                        f"{skipped_count} skipped (duplicates)"
                    )

                await session.commit()

            except Exception as e:
                logger.error(f"Error recording balance snapshots: {e}", exc_info=True)
                await session.rollback()

    async def _record_market_data(self) -> None:
        """Record market data for enabled trading pairs."""
        session_factory = db_engine.get_session_factory()
        async with session_factory() as session:
            try:
                exchange_repo = ExchangeRepository(session)
                trading_pair_repo = TradingPairRepository(session)
                market_data_repo = MarketDataRepository(session)

                # Get enabled exchanges
                exchanges = await self._get_enabled_exchanges(exchange_repo)

                record_count = 0
                skipped_count = 0

                for exchange_model in exchanges:
                    try:
                        # Get exchange plugin instance
                        exchange_plugin = exchange_registry.get_exchange(
                            exchange_model.name
                        )
                        await exchange_plugin.initialize()
                        await exchange_plugin.load_markets()

                        # Get trading pairs for this exchange
                        trading_pairs = await trading_pair_repo.get_by_exchange(
                            exchange_model.id
                        )

                        if self._enabled_symbols:
                            trading_pairs = [
                                tp
                                for tp in trading_pairs
                                if tp.symbol in self._enabled_symbols
                            ]

                        # Record market data for each trading pair
                        for trading_pair in trading_pairs:
                            try:
                                # Fetch OHLCV data (latest candle)
                                ohlcv_data = await exchange_plugin.fetch_ohlcv(
                                    trading_pair.symbol,
                                    timeframe=self._default_timeframe,
                                    limit=1,
                                )

                                if not ohlcv_data or len(ohlcv_data) == 0:
                                    continue

                                # OHLCV format: [timestamp, open, high, low, close, volume]
                                latest_candle = ohlcv_data[-1]
                                timestamp_ms = int(latest_candle[0])
                                timestamp = datetime.fromtimestamp(
                                    timestamp_ms / 1000.0
                                )

                                # Check for duplicates and create market data
                                market_data = MarketData(
                                    trading_pair_id=trading_pair.id,
                                    exchange_id=exchange_model.id,
                                    timeframe=self._default_timeframe,
                                    timestamp=timestamp,
                                    open=float(latest_candle[1]),
                                    high=float(latest_candle[2]),
                                    low=float(latest_candle[3]),
                                    close=float(latest_candle[4]),
                                    volume=float(latest_candle[5]),
                                )

                                created = await market_data_repo.create_if_not_exists(
                                    market_data
                                )
                                if created:
                                    record_count += 1
                                else:
                                    skipped_count += 1

                            except Exception as e:
                                logger.warning(
                                    f"Failed to record market data for "
                                    f"{trading_pair.symbol} on {exchange_model.name}: {e}"
                                )
                                continue

                    except Exception as e:
                        logger.error(
                            f"Failed to record market data for {exchange_model.name}: {e}",
                            exc_info=True,
                        )
                        continue

                if record_count > 0 or skipped_count > 0:
                    logger.info(
                        f"Market data: {record_count} created, "
                        f"{skipped_count} skipped (duplicates)"
                    )

                await session.commit()

            except Exception as e:
                logger.error(f"Error recording market data: {e}", exc_info=True)
                await session.rollback()

    async def _get_enabled_exchanges(
        self, exchange_repo: ExchangeRepository
    ) -> list[Exchange]:
        """
        Get list of enabled exchanges.

        Args:
            exchange_repo: Exchange repository.

        Returns:
            List of Exchange models.
        """
        all_exchanges = await exchange_repo.get_active_exchanges()

        if self._enabled_exchanges:
            return [ex for ex in all_exchanges if ex.name in self._enabled_exchanges]

        return all_exchanges

    async def record_balance_snapshot_now(self) -> int:
        """
        Manually trigger a balance snapshot recording (for testing or on-demand).

        Returns:
            Number of snapshots created.
        """
        count = 0
        session_factory = db_engine.get_session_factory()
        async with session_factory() as session:
            try:
                exchange_repo = ExchangeRepository(session)
                snapshot_repo = BalanceSnapshotRepository(session)
                exchanges = await self._get_enabled_exchanges(exchange_repo)

                # Record snapshots
                # (This duplicates logic from _record_balance_snapshots
                # but allows manual triggering)
                for exchange_model in exchanges:
                    exchange_plugin = exchange_registry.get_exchange(
                        exchange_model.name
                    )
                    await exchange_plugin.initialize()
                    balances_data = await exchange_plugin.fetch_balance()

                    if isinstance(balances_data, BalanceDTO):
                        balances_dict = {balances_data.currency: balances_data}
                    else:
                        balances_dict = balances_data

                    for currency, balance_dto in balances_dict.items():
                        asset_repo = AssetRepository(session)
                        asset_model = await asset_repo.get_by_symbol(currency)
                        if not asset_model:
                            asset_model = Asset(
                                symbol=currency,
                                name=currency,
                                is_active=True,
                            )
                            asset_model = await asset_repo.create(asset_model)

                        snapshot = BalanceSnapshot(
                            exchange_id=exchange_model.id,
                            asset_id=asset_model.id,
                            free_balance=float(balance_dto.free),
                            locked_balance=float(balance_dto.used),
                            total_balance=float(balance_dto.total),
                            value_in_usd=None,
                            snapshot_at=datetime.utcnow(),
                        )

                        created = await snapshot_repo.create_if_not_exists(snapshot)
                        if created:
                            count += 1

                await session.commit()

            except Exception as e:
                logger.error(f"Error in manual balance snapshot: {e}", exc_info=True)
                await session.rollback()

        return count

    async def record_market_data_now(self) -> int:
        """
        Manually trigger market data recording (for testing or on-demand).

        Returns:
            Number of market data records created.
        """
        count = 0
        session_factory = db_engine.get_session_factory()
        async with session_factory() as session:
            try:
                exchange_repo = ExchangeRepository(session)
                trading_pair_repo = TradingPairRepository(session)
                market_data_repo = MarketDataRepository(session)
                exchanges = await self._get_enabled_exchanges(exchange_repo)

                for exchange_model in exchanges:
                    exchange_plugin = exchange_registry.get_exchange(
                        exchange_model.name
                    )
                    await exchange_plugin.initialize()
                    await exchange_plugin.load_markets()

                    trading_pairs = await trading_pair_repo.get_by_exchange(
                        exchange_model.id
                    )

                    for trading_pair in trading_pairs:
                        ohlcv_data = await exchange_plugin.fetch_ohlcv(
                            trading_pair.symbol,
                            timeframe=self._default_timeframe,
                            limit=1,
                        )

                        if not ohlcv_data:
                            continue

                        latest_candle = ohlcv_data[-1]
                        timestamp_ms = int(latest_candle[0])
                        timestamp = datetime.fromtimestamp(timestamp_ms / 1000.0)

                        market_data = MarketData(
                            trading_pair_id=trading_pair.id,
                            exchange_id=exchange_model.id,
                            timeframe=self._default_timeframe,
                            timestamp=timestamp,
                            open=float(latest_candle[1]),
                            high=float(latest_candle[2]),
                            low=float(latest_candle[3]),
                            close=float(latest_candle[4]),
                            volume=float(latest_candle[5]),
                        )

                        created = await market_data_repo.create_if_not_exists(
                            market_data
                        )
                        if created:
                            count += 1

                await session.commit()

            except Exception as e:
                logger.error(
                    f"Error in manual market data recording: {e}", exc_info=True
                )
                await session.rollback()

        return count
