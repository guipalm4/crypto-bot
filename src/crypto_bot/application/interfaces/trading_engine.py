"""
Trading Engine Interface for Risk Management Integration.

This module defines the abstract interface between the risk management
system and the trading engine, ensuring all risk actions are atomic
and properly logged.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Optional

from crypto_bot.application.dtos.order import OrderDTO


class TradingEngineInterface(ABC):
    """
    Abstract interface for trading engine operations required by risk management.

    This interface ensures all risk-triggered actions are:
    - Atomic: Operations either complete fully or roll back
    - Logged: All actions are recorded with timestamps
    - Traceable: Actions can be audited through evaluation IDs
    """

    @abstractmethod
    async def close_position(
        self,
        symbol: str,
        reason: str,
        evaluation_id: Optional[str] = None,
    ) -> OrderDTO:
        """
        Close an open position immediately at market price.

        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")
            reason: Reason for closing (e.g., "stop_loss", "take_profit")
            evaluation_id: Optional risk evaluation ID for audit trail

        Returns:
            OrderDTO: The executed close order

        Raises:
            TradingEngineError: If position cannot be closed
        """
        pass

    @abstractmethod
    async def partial_close_position(
        self,
        symbol: str,
        percentage: Decimal,
        reason: str,
        evaluation_id: Optional[str] = None,
    ) -> OrderDTO:
        """
        Close a percentage of an open position at market price.

        Args:
            symbol: Trading pair symbol
            percentage: Percentage to close (0-100)
            reason: Reason for partial close
            evaluation_id: Optional risk evaluation ID for audit trail

        Returns:
            OrderDTO: The executed partial close order

        Raises:
            TradingEngineError: If position cannot be partially closed
        """
        pass

    @abstractmethod
    async def close_all_positions(
        self,
        reason: str,
        evaluation_id: Optional[str] = None,
    ) -> Dict[str, OrderDTO]:
        """
        Close all open positions immediately at market price.

        Args:
            reason: Reason for closing all positions (e.g., "emergency_exit")
            evaluation_id: Optional risk evaluation ID for audit trail

        Returns:
            Dict mapping symbol to executed close order

        Raises:
            TradingEngineError: If any position cannot be closed
        """
        pass

    @abstractmethod
    async def block_new_trades(
        self,
        duration_seconds: Optional[int] = None,
        reason: str = "",
        evaluation_id: Optional[str] = None,
    ) -> None:
        """
        Block all new trade creation for a specified duration.

        Args:
            duration_seconds: Block duration in seconds (None = indefinite)
            reason: Reason for blocking trades
            evaluation_id: Optional risk evaluation ID for audit trail

        Raises:
            TradingEngineError: If trades cannot be blocked
        """
        pass

    @abstractmethod
    async def is_trading_blocked(self) -> bool:
        """
        Check if new trades are currently blocked.

        Returns:
            True if trading is blocked, False otherwise
        """
        pass

    @abstractmethod
    async def resume_trading(
        self,
        reason: str = "",
        evaluation_id: Optional[str] = None,
    ) -> None:
        """
        Resume normal trading operations.

        Args:
            reason: Reason for resuming trading
            evaluation_id: Optional risk evaluation ID for audit trail

        Raises:
            TradingEngineError: If trading cannot be resumed
        """
        pass

    @abstractmethod
    async def get_position_size(self, symbol: str) -> Decimal:
        """
        Get current position size for a symbol.

        Args:
            symbol: Trading pair symbol

        Returns:
            Current position size (positive for long, negative for short)
        """
        pass

    @abstractmethod
    async def get_account_equity(self) -> Decimal:
        """
        Get current account equity (balance + unrealized PnL).

        Returns:
            Current account equity
        """
        pass
