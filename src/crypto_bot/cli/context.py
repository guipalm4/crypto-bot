"""
CLI Context Management.

Manages initialization and lifecycle of services required by CLI commands.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from crypto_bot.application.interfaces.trading_service import ITradingService
from crypto_bot.application.services.risk_service import RiskService
from crypto_bot.application.services.strategy_orchestrator import StrategyOrchestrator
from crypto_bot.application.services.trading_service import TradingService
from crypto_bot.domain.repositories.strategy_repository import IStrategyRepository
from crypto_bot.infrastructure.database.engine import get_db_session
from crypto_bot.infrastructure.database.repositories.strategy_repository import (
    StrategyRepository,
)
from crypto_bot.utils.structured_logger import get_logger

logger = get_logger(__name__)


class CLIContext:
    """
    Context manager for CLI commands.

    Manages lifecycle of database sessions, repositories, and services
    needed by CLI commands.
    """

    def __init__(self) -> None:
        """Initialize CLI context."""
        self._orchestrator: Optional[StrategyOrchestrator] = None
        self._trading_service: Optional[ITradingService] = None
        self._risk_service: Optional[RiskService] = None
        self._session: Optional[AsyncSession] = None

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session context.

        Yields:
            AsyncSession: Database session
        """
        async for session in get_db_session():
            try:
                self._session = session
                yield session
            finally:
                self._session = None

    async def get_strategy_repository(self) -> IStrategyRepository:
        """
        Get strategy repository instance.

        Returns:
            IStrategyRepository: Strategy repository

        Raises:
            RuntimeError: If database session is not available
        """
        if self._session is None:
            raise RuntimeError(
                "Database session not initialized. Use get_session() context manager."
            )

        return StrategyRepository(self._session)

    async def get_trading_service(self) -> ITradingService:
        """
        Get trading service instance.

        Returns:
            ITradingService: Trading service
        """
        if self._trading_service is None:
            self._trading_service = TradingService()
        return self._trading_service

    async def get_risk_service(self) -> RiskService:
        """
        Get risk service instance.

        Returns:
            RiskService: Risk service
        """
        if self._risk_service is None:
            from crypto_bot.infrastructure.config.settings import get_settings

            settings = get_settings()
            self._risk_service = RiskService(settings.trading.risk)
        return self._risk_service

    async def get_orchestrator(self, dry_run: bool = False) -> StrategyOrchestrator:
        """
        Get strategy orchestrator instance.

        Args:
            dry_run: Whether to run in dry-run mode

        Returns:
            StrategyOrchestrator: Strategy orchestrator

        Raises:
            RuntimeError: If database session is not available
        """
        if self._orchestrator is None or self._orchestrator.dry_run != dry_run:
            strategy_repository = await self.get_strategy_repository()
            trading_service = await self.get_trading_service()
            risk_service = await self.get_risk_service()

            self._orchestrator = StrategyOrchestrator(
                strategy_repository=strategy_repository,
                trading_service=trading_service,
                risk_service=risk_service,
                dry_run=dry_run,
                max_concurrent_strategies=10,
            )

        return self._orchestrator

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._orchestrator and self._orchestrator._running:
            await self._orchestrator.stop()

        if self._trading_service and hasattr(self._trading_service, "close"):
            await self._trading_service.close()

        self._orchestrator = None
        self._trading_service = None
        self._risk_service = None
        self._session = None


# Global context instance
cli_context = CLIContext()


def run_async(coro: Any) -> Any:
    """
    Run async coroutine in event loop.

    Args:
        coro: Async coroutine to run
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)
