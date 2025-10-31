"""
Strategy Orchestration Service.

Orchestrates the execution of trading strategies by scheduling runs,
fetching market data, computing indicators, generating signals, and
executing trades via the trading engine.
"""

import asyncio
import time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set

import pandas as pd

from crypto_bot.application.dtos.order import (
    CreateOrderRequest,
    OrderDTO,
    OrderSide,
    OrderType,
    RetryPolicy,
)
from crypto_bot.application.interfaces.trading_service import ITradingService
from crypto_bot.application.services.risk_service import RiskService
from crypto_bot.domain.repositories.strategy_repository import IStrategyRepository
from crypto_bot.infrastructure.exchanges.base import ExchangeBase
from crypto_bot.plugins.indicators.cache import get_cache
from crypto_bot.plugins.indicators.loader import IndicatorPluginRegistry
from crypto_bot.plugins.registry import ExchangePluginRegistry
from crypto_bot.plugins.strategies.base import Strategy, StrategySignal
from crypto_bot.plugins.strategies.loader import discover_strategies
from crypto_bot.utils.structured_logger import get_logger

logger = get_logger(__name__)


# Timeframe to seconds mapping
TIMEFRAME_SECONDS: Dict[str, int] = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
}


class StrategyExecutionContext:
    """
    Execution context for a single strategy run.

    Contains all the data and state needed for a strategy execution cycle.
    """

    def __init__(
        self,
        strategy_db_model: Any,  # Strategy DB model
        strategy_class: type[Strategy],
        exchange_plugin: ExchangeBase,
        symbol: str,
        timeframe: str,
        dry_run: bool = False,
    ):
        """
        Initialize strategy execution context.

        Args:
            strategy_db_model: Database model for the strategy
            strategy_class: Strategy plugin class
            exchange_plugin: Exchange plugin instance
            symbol: Trading pair symbol
            timeframe: Timeframe for data fetching
            dry_run: Whether to run in dry-run mode
        """
        self.strategy_db_model = strategy_db_model
        self.strategy_class = strategy_class
        self.strategy_instance: Optional[Strategy] = None
        self.exchange_plugin = exchange_plugin
        self.symbol = symbol
        self.timeframe = timeframe
        self.dry_run = dry_run
        self.ohlcv_data: Optional[List[List[float]]] = None
        self.market_data_df: Optional[pd.DataFrame] = None
        self.indicators: Dict[str, Any] = {}
        self.signal: Optional[StrategySignal] = None
        self.order: Optional[OrderDTO] = None
        self.error: Optional[Exception] = None


class StrategyOrchestrator:
    """
    Orchestrates the execution of multiple trading strategies.

    Manages scheduling, data fetching, indicator computation, signal generation,
    and trade execution for active strategies.
    """

    def __init__(
        self,
        strategy_repository: IStrategyRepository,
        trading_service: ITradingService,
        risk_service: RiskService,
        exchange_registry: Optional[ExchangePluginRegistry] = None,
        indicator_registry: Optional[IndicatorPluginRegistry] = None,
        dry_run: bool = False,
        max_concurrent_strategies: int = 10,
    ):
        """
        Initialize the strategy orchestrator.

        Args:
            strategy_repository: Repository for accessing strategy configurations
            trading_service: Service for executing trades
            risk_service: Service for risk management checks
            exchange_registry: Registry for exchange plugins (auto-initialized if None)
            indicator_loader: Loader for indicator plugins (auto-initialized if None)
            dry_run: Whether to run in dry-run mode (no real trades)
            max_concurrent_strategies: Maximum number of strategies to run concurrently
        """
        self.strategy_repository = strategy_repository
        self.trading_service = trading_service
        self.risk_service = risk_service
        self.exchange_registry = exchange_registry or ExchangePluginRegistry()
        self.indicator_registry = indicator_registry or IndicatorPluginRegistry()
        self.dry_run = dry_run
        self.max_concurrent_strategies = max_concurrent_strategies

        # Execution state
        self._running = False
        self._tasks: Set[asyncio.Task] = set()
        self._scheduler_task: Optional[asyncio.Task] = None
        self._locks: Dict[str, asyncio.Lock] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent_strategies)
        # Track last execution time per strategy to avoid duplicate runs
        self._last_execution: Dict[str, float] = {}
        # Track error counts per strategy for circuit breaker pattern
        self._error_counts: Dict[str, int] = {}
        self._max_consecutive_errors = 5  # Circuit breaker threshold

        # Discovered strategies
        self._strategy_classes = discover_strategies()

        logger.info(
            "strategy_orchestrator:initialized",
            dry_run=dry_run,
            max_concurrent=max_concurrent_strategies,
            discovered_strategies=list(self._strategy_classes.keys()),
        )

    async def start(self) -> None:
        """
        Start the orchestrator and begin scheduling strategy executions.

        Raises:
            RuntimeError: If orchestrator is already running
        """
        if self._running:
            raise RuntimeError("Orchestrator is already running")

        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("strategy_orchestrator:started")

    async def stop(self) -> None:
        """
        Stop the orchestrator and cancel all running tasks.

        Waits for current strategy executions to complete gracefully.
        """
        if not self._running:
            return

        self._running = False

        # Cancel scheduler
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

        # Wait for running strategy tasks to complete
        if self._tasks:
            logger.info(
                "strategy_orchestrator:waiting_for_tasks",
                count=len(self._tasks),
            )
            await asyncio.gather(*self._tasks, return_exceptions=True)
            self._tasks.clear()

        logger.info("strategy_orchestrator:stopped")

    async def _scheduler_loop(self) -> None:
        """
        Main scheduler loop that triggers strategy executions.

        Runs continuously, scheduling strategy executions based on their
        configured timeframes and pairs. Uses intelligent scheduling to
        avoid redundant executions and respect timeframe boundaries.
        """
        while self._running:
            try:
                current_time = time.time()

                # Get active strategies from database
                active_strategies = (
                    await self.strategy_repository.get_active_strategies()
                )

                if not active_strategies:
                    logger.debug("strategy_orchestrator:no_active_strategies")
                    await asyncio.sleep(60)  # Check again in 1 minute
                    continue

                # Create execution contexts for each strategy
                execution_contexts = await self._create_execution_contexts(
                    active_strategies
                )

                # Filter contexts that are ready for execution based on timeframe
                ready_contexts = []
                for ctx in execution_contexts:
                    strategy_key = (
                        f"{ctx.strategy_db_model.id}:{ctx.symbol}:{ctx.timeframe}"
                    )
                    timeframe_seconds = TIMEFRAME_SECONDS.get(ctx.timeframe, 60)
                    last_exec = self._last_execution.get(strategy_key, 0)

                    # Execute if enough time has passed since last execution
                    time_since_last = current_time - last_exec
                    if time_since_last >= timeframe_seconds:
                        ready_contexts.append(ctx)
                    else:
                        logger.debug(
                            "strategy_orchestrator:strategy_not_ready",
                            strategy_id=str(ctx.strategy_db_model.id),
                            timeframe=ctx.timeframe,
                            seconds_remaining=timeframe_seconds - time_since_last,
                        )

                # Execute ready strategies concurrently (limited by semaphore)
                if ready_contexts:
                    tasks = [
                        self._run_strategy_with_tracking(ctx, current_time)
                        for ctx in ready_contexts
                    ]
                    await asyncio.gather(*tasks, return_exceptions=True)

                # Determine next execution time (shortest remaining timeframe)
                if execution_contexts:
                    next_check_times = []
                    for ctx in execution_contexts:
                        strategy_key = (
                            f"{ctx.strategy_db_model.id}:{ctx.symbol}:{ctx.timeframe}"
                        )
                        timeframe_seconds = TIMEFRAME_SECONDS.get(ctx.timeframe, 60)
                        last_exec = self._last_execution.get(strategy_key, 0)
                        next_exec = last_exec + timeframe_seconds
                        time_until_next = max(0, next_exec - current_time)
                        next_check_times.append(time_until_next)

                    # Sleep until the next strategy is ready (with minimum check interval)
                    min_wait = min(next_check_times) if next_check_times else 60
                    sleep_time = max(
                        1, min(min_wait, 60)
                    )  # Check at least every minute
                    logger.debug(
                        "strategy_orchestrator:scheduler_sleep",
                        sleep_seconds=sleep_time,
                        strategies_count=len(execution_contexts),
                    )
                    await asyncio.sleep(sleep_time)
                else:
                    await asyncio.sleep(60)

            except asyncio.CancelledError:
                logger.info("strategy_orchestrator:scheduler_cancelled")
                raise
            except Exception as e:
                logger.error(
                    "strategy_orchestrator:scheduler_error",
                    exc_type=type(e).__name__,
                    exc_msg=str(e),
                )
                await asyncio.sleep(10)  # Brief pause before retry

    async def _create_execution_contexts(
        self, strategies: List[Any]
    ) -> List[StrategyExecutionContext]:
        """
        Create execution contexts for active strategies.

        Args:
            strategies: List of strategy database models

        Returns:
            List of execution contexts ready for execution
        """
        contexts = []

        for strategy_db in strategies:
            try:
                # Get strategy class from plugin registry
                strategy_class = self._strategy_classes.get(strategy_db.plugin_name)
                if not strategy_class:
                    logger.warning(
                        "strategy_orchestrator:strategy_not_found",
                        plugin_name=strategy_db.plugin_name,
                        strategy_id=str(strategy_db.id),
                    )
                    continue

                # Extract configuration (assuming it includes exchange, symbol, timeframe)
                params = strategy_db.parameters_json
                exchange_name = params.get("exchange")
                symbol = params.get("symbol")
                timeframe = params.get("timeframe", "1h")

                if not exchange_name or not symbol:
                    logger.warning(
                        "strategy_orchestrator:missing_config",
                        strategy_id=str(strategy_db.id),
                    )
                    continue

                # Get exchange plugin
                try:
                    exchange_plugin = self.exchange_registry.get_exchange(exchange_name)
                    await exchange_plugin.initialize()
                except Exception as e:
                    logger.error(
                        "strategy_orchestrator:exchange_init_failed",
                        exchange=exchange_name,
                        exc_type=type(e).__name__,
                        exc_msg=str(e),
                    )
                    continue

                # Create execution context
                context = StrategyExecutionContext(
                    strategy_db_model=strategy_db,
                    strategy_class=strategy_class,
                    exchange_plugin=exchange_plugin,
                    symbol=symbol,
                    timeframe=timeframe,
                    dry_run=self.dry_run,
                )

                contexts.append(context)

            except Exception as e:
                logger.error(
                    "strategy_orchestrator:context_creation_failed",
                    strategy_id=(
                        str(strategy_db.id) if hasattr(strategy_db, "id") else "unknown"
                    ),
                    exc_type=type(e).__name__,
                    exc_msg=str(e),
                )

        return contexts

    async def _run_strategy_with_semaphore(
        self, context: StrategyExecutionContext
    ) -> None:
        """
        Run a strategy execution with semaphore concurrency control.

        Args:
            context: Strategy execution context
        """
        async with self._semaphore:
            task = asyncio.create_task(self._run_strategy(context))
            self._tasks.add(task)
            try:
                await task
            finally:
                self._tasks.discard(task)

    async def _run_strategy_with_tracking(
        self, context: StrategyExecutionContext, execution_time: float
    ) -> None:
        """
        Run a strategy execution and track execution time.

        Args:
            context: Strategy execution context
            execution_time: Timestamp when execution started
        """
        strategy_key = (
            f"{context.strategy_db_model.id}:{context.symbol}:{context.timeframe}"
        )
        await self._run_strategy_with_semaphore(context)
        # Update last execution time and reset error count after successful run
        if context.error is None:
            self._last_execution[strategy_key] = execution_time
            self._reset_error_count(strategy_key)

    async def _run_strategy(self, context: StrategyExecutionContext) -> None:
        """
        Execute a single strategy run.

        Performs the full cycle:
        1. Fetch OHLCV data
        2. Compute indicators
        3. Generate strategy signal
        4. Execute trade (if signal indicates)

        Args:
            context: Strategy execution context
        """
        strategy_id = str(context.strategy_db_model.id)
        strategy_name = context.strategy_db_model.name

        logger.info(
            "strategy_orchestrator:strategy_run_start",
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            symbol=context.symbol,
            timeframe=context.timeframe,
            dry_run=context.dry_run,
        )

        try:
            # Initialize strategy instance if needed
            if context.strategy_instance is None:
                context.strategy_instance = context.strategy_class()
                context.strategy_instance.validate_parameters(
                    context.strategy_db_model.parameters_json
                )

            # Fetch OHLCV data
            await self._fetch_market_data(context)

            # Compute indicators
            await self._compute_indicators(context)

            # Generate signal
            await self._generate_signal(context)

            # Execute trade if signal indicates
            if context.signal and context.signal.action in ("buy", "sell"):
                await self._execute_trade(context)

            logger.info(
                "strategy_orchestrator:strategy_run_complete",
                strategy_id=strategy_id,
                strategy_name=strategy_name,
                signal_action=context.signal.action if context.signal else None,
                order_created=context.order is not None,
            )

        except Exception as e:
            context.error = e
            strategy_key = self._get_strategy_key(context)
            error_count = self._increment_error_count(strategy_key)

            logger.error(
                "strategy_orchestrator:strategy_run_error",
                strategy_id=strategy_id,
                strategy_name=strategy_name,
                symbol=context.symbol,
                timeframe=context.timeframe,
                exc_type=type(e).__name__,
                exc_msg=str(e),
                consecutive_errors=error_count,
                max_allowed=self._max_consecutive_errors,
            )

            # Circuit breaker: Skip strategy if too many consecutive errors
            if error_count >= self._max_consecutive_errors:
                logger.warning(
                    "strategy_orchestrator:circuit_breaker_activated",
                    strategy_id=strategy_id,
                    strategy_name=strategy_name,
                    error_count=error_count,
                )

    async def _fetch_market_data(
        self, context: StrategyExecutionContext, max_retries: int = 3
    ) -> None:
        """
        Fetch OHLCV market data for the strategy's symbol and timeframe.

        Implements retry logic with exponential backoff for transient failures.

        Args:
            context: Strategy execution context
            max_retries: Maximum number of retry attempts

        Raises:
            Exception: If all retry attempts fail
        """
        strategy_key = self._get_strategy_key(context)
        retry_count = 0
        last_exception: Optional[Exception] = None

        while retry_count <= max_retries:
            try:
                # Fetch OHLCV data (last 100 candles for indicator calculations)
                ohlcv = await context.exchange_plugin.fetch_ohlcv(
                    symbol=context.symbol,
                    timeframe=context.timeframe,
                    limit=100,
                )

                if not ohlcv:
                    raise ValueError(f"No OHLCV data returned for {context.symbol}")

                context.ohlcv_data = ohlcv

                # Convert to DataFrame for easier manipulation
                df = pd.DataFrame(
                    ohlcv,
                    columns=["timestamp", "open", "high", "low", "close", "volume"],
                )
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                df.set_index("timestamp", inplace=True)
                context.market_data_df = df

                # Reset error count on success
                self._error_counts[strategy_key] = 0

                logger.debug(
                    "strategy_orchestrator:data_fetched",
                    symbol=context.symbol,
                    timeframe=context.timeframe,
                    candles=len(ohlcv),
                    retry_count=retry_count,
                )
                return

            except (ValueError, RuntimeError) as e:
                # Non-retriable errors
                last_exception = e
                self._increment_error_count(strategy_key)
                logger.error(
                    "strategy_orchestrator:data_fetch_error_fatal",
                    symbol=context.symbol,
                    timeframe=context.timeframe,
                    exc_type=type(e).__name__,
                    exc_msg=str(e),
                    retry_count=retry_count,
                )
                raise

            except Exception as e:
                # Retriable errors
                last_exception = e
                retry_count += 1

                if retry_count <= max_retries:
                    backoff_time = min(
                        2**retry_count, 30
                    )  # Exponential backoff, max 30s
                    logger.warning(
                        "strategy_orchestrator:data_fetch_error_retry",
                        symbol=context.symbol,
                        timeframe=context.timeframe,
                        exc_type=type(e).__name__,
                        exc_msg=str(e),
                        retry_count=retry_count,
                        max_retries=max_retries,
                        backoff_seconds=backoff_time,
                    )
                    await asyncio.sleep(backoff_time)
                else:
                    self._increment_error_count(strategy_key)
                    logger.error(
                        "strategy_orchestrator:data_fetch_error_max_retries",
                        symbol=context.symbol,
                        timeframe=context.timeframe,
                        exc_type=type(e).__name__,
                        exc_msg=str(e),
                        total_retries=retry_count,
                    )

        # All retries exhausted
        if last_exception:
            raise last_exception

    def _get_strategy_key(self, context: StrategyExecutionContext) -> str:
        """
        Get unique key for strategy tracking.

        Args:
            context: Strategy execution context

        Returns:
            Unique strategy key
        """
        return f"{context.strategy_db_model.id}:{context.symbol}:{context.timeframe}"

    def _increment_error_count(self, strategy_key: str) -> int:
        """
        Increment error count for a strategy (circuit breaker pattern).

        Args:
            strategy_key: Unique strategy key

        Returns:
            Current error count after increment
        """
        self._error_counts[strategy_key] = self._error_counts.get(strategy_key, 0) + 1
        return self._error_counts[strategy_key]

    def _reset_error_count(self, strategy_key: str) -> None:
        """
        Reset error count for a strategy after successful execution.

        Args:
            strategy_key: Unique strategy key
        """
        self._error_counts[strategy_key] = 0

    async def _compute_indicators(self, context: StrategyExecutionContext) -> None:
        """
        Compute technical indicators required by the strategy.

        Args:
            context: Strategy execution context
        """
        if context.market_data_df is None:
            raise ValueError("Market data must be fetched before computing indicators")

        try:
            # Get indicator cache
            cache = get_cache()

            # Strategy parameters may specify which indicators to compute
            params = context.strategy_db_model.parameters_json
            indicator_configs = params.get("indicators", {})

            computed_indicators = {}

            for indicator_name, indicator_params in indicator_configs.items():
                try:
                    # Try cache first
                    cached = cache.get(
                        indicator_name, context.market_data_df, indicator_params
                    )

                    if cached is not None:
                        computed_indicators[indicator_name] = cached
                        logger.debug(
                            "strategy_orchestrator:indicator_cached",
                            indicator=indicator_name,
                        )
                    else:
                        # Load and create indicator instance
                        indicator = self.indicator_registry.create_indicator_instance(
                            indicator_name
                        )

                        # Validate parameters
                        indicator.validate_parameters(indicator_params)

                        # Compute indicator
                        result = indicator.calculate(
                            context.market_data_df, indicator_params
                        )

                        # Cache result
                        cache.set(
                            indicator_name,
                            context.market_data_df,
                            indicator_params,
                            result,
                        )

                        computed_indicators[indicator_name] = result

                        logger.debug(
                            "strategy_orchestrator:indicator_computed",
                            indicator=indicator_name,
                        )

                except Exception as e:
                    logger.warning(
                        "strategy_orchestrator:indicator_error",
                        indicator=indicator_name,
                        exc_type=type(e).__name__,
                        exc_msg=str(e),
                    )
                    # Continue with other indicators

            context.indicators = computed_indicators

        except Exception as e:
            logger.error(
                "strategy_orchestrator:indicator_computation_error",
                strategy_name=context.strategy_db_model.name,
                symbol=context.symbol,
                indicators_count=len(context.indicators),
                exc_type=type(e).__name__,
                exc_msg=str(e),
            )
            raise

    async def _generate_signal(self, context: StrategyExecutionContext) -> None:
        """
        Generate trading signal from strategy.

        Args:
            context: Strategy execution context
        """
        if context.market_data_df is None:
            raise ValueError("Market data must be available to generate signals")

        try:
            # Prepare market data for strategy (combine OHLCV and indicators)
            market_data = {
                "ohlcv": context.market_data_df,
                "indicators": context.indicators,
            }

            # Generate signal
            if context.strategy_instance is None:
                raise RuntimeError(
                    "Strategy instance must be initialized before generating signals"
                )
            signal = context.strategy_instance.generate_signal(
                market_data, context.strategy_db_model.parameters_json
            )

            context.signal = signal

            logger.info(
                "strategy_orchestrator:signal_generated",
                strategy_name=context.strategy_db_model.name,
                signal_action=signal.action,
                signal_strength=signal.strength,
            )

        except Exception as e:
            logger.error(
                "strategy_orchestrator:signal_generation_error",
                strategy_name=context.strategy_db_model.name,
                symbol=context.symbol,
                timeframe=context.timeframe,
                exc_type=type(e).__name__,
                exc_msg=str(e),
            )
            raise

    async def _execute_trade(self, context: StrategyExecutionContext) -> None:
        """
        Execute a trade based on strategy signal.

        Args:
            context: Strategy execution context
        """
        if context.signal is None:
            return

        if context.dry_run:
            # Log simulated trade
            logger.info(
                "strategy_orchestrator:dry_run_trade",
                strategy_name=context.strategy_db_model.name,
                action=context.signal.action,
                symbol=context.symbol,
                signal_strength=context.signal.strength,
            )
            return

        try:
            # Determine order side and type from signal
            side = OrderSide.BUY if context.signal.action == "buy" else OrderSide.SELL
            order_type = OrderType.MARKET  # Default to market orders

            # Get order parameters from signal metadata or strategy config
            params = context.strategy_db_model.parameters_json
            quantity = Decimal(str(context.signal.metadata.get("quantity", "0.001")))
            price = None  # Market order

            if order_type == OrderType.LIMIT:
                price = Decimal(str(context.signal.metadata.get("price", "0")))

            # Risk check before execution
            # (This would integrate with RiskService for validation)
            # For now, proceed with execution

            # Get exchange name from context
            exchange_name = params.get("exchange")

            # Create order request
            order_request = CreateOrderRequest(
                exchange=exchange_name,
                symbol=context.symbol,
                side=side,
                type=order_type,
                quantity=quantity,
                price=price,
                timeout=30.0,
                retry_policy=RetryPolicy(),
            )

            # Execute order via trading service
            order = await self.trading_service.create_order(order_request)
            context.order = order

            logger.info(
                "strategy_orchestrator:trade_executed",
                strategy_name=context.strategy_db_model.name,
                order_id=order.id,
                symbol=context.symbol,
                side=side.value,
                quantity=quantity,
            )

        except Exception as e:
            strategy_key = self._get_strategy_key(context)
            error_count = self._increment_error_count(strategy_key)

            logger.error(
                "strategy_orchestrator:trade_execution_error",
                strategy_name=context.strategy_db_model.name,
                symbol=context.symbol,
                signal_action=context.signal.action if context.signal else None,
                exc_type=type(e).__name__,
                exc_msg=str(e),
                consecutive_errors=error_count,
            )
            # Don't raise - allow strategy to continue, just log the error
            # The strategy will be marked with error in context
