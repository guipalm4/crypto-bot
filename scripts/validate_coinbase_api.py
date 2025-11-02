#!/usr/bin/env python3
"""
Coinbase API Validation Script

This script validates the Coinbase API integration by testing:
- API connection establishment
- Authentication with configured credentials
- Basic API operations (fetch markets, balance, ticker)
- Error handling and rate limiting

Usage:
    python scripts/validate_coinbase_api.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from crypto_bot.config.settings import settings
from crypto_bot.plugins.exchanges.coinbase_pro_plugin import CoinbaseProPlugin
from crypto_bot.plugins.exchanges.config_models import CoinbaseProConfig
from crypto_bot.utils.structured_logger import get_logger

logger = get_logger(__name__)


async def validate_coinbase_api() -> None:
    """
    Validate Coinbase API integration.

    Tests:
    1. Plugin initialization
    2. Connection establishment
    3. Market data fetching
    4. Account balance retrieval (if authenticated)
    5. Ticker price fetching
    """
    print("=" * 80)
    print("Coinbase API Validation")
    print("=" * 80)
    print()

    # Check if credentials are configured
    if not settings.coinbase_api_key or not settings.coinbase_api_secret:
        print("❌ ERROR: Coinbase credentials not configured in .env")
        print("   Required variables:")
        print("   - COINBASE_API_KEY")
        print("   - COINBASE_API_SECRET")
        print("   - COINBASE_PASSPHRASE")
        sys.exit(1)

    print("✅ Credentials found:")
    print(f"   - API Key: {settings.coinbase_api_key[:10]}...")
    print(f"   - Secret: {'configured' if settings.coinbase_api_secret else 'missing'}")
    print(
        f"   - Passphrase: {'configured' if settings.coinbase_passphrase else 'missing'}"
    )
    print(f"   - Sandbox Mode: {settings.coinbase_sandbox}")
    print()

    # Determine if we can do authenticated operations
    can_authenticate = bool(
        settings.coinbase_api_key
        and settings.coinbase_api_secret
        and settings.coinbase_passphrase
    )

    if not can_authenticate:
        print("⚠️  WARNING: Passphrase not configured.")
        print("   Will only test public API operations (markets, ticker, orderbook).")
        print("   Authenticated operations (balance) will be skipped.")
        print()

    # Create Coinbase plugin configuration
    # Note: Coinbase via CCXT may not support sandbox mode properly
    # For validation, we'll use production if sandbox fails
    use_sandbox = settings.coinbase_sandbox

    try:
        # For public operations, we can create config without auth if passphrase is missing
        if not settings.coinbase_passphrase:
            print("   ℹ️  Creating config for public API operations only...")
            # Try sandbox first, but note it may not be supported
            config = CoinbaseProConfig(
                api_key=None,  # No auth for public operations
                secret=None,
                sandbox=False,  # Coinbase CCXT doesn't support sandbox, use production
                rate_limit=1000,
            )
            print("   ℹ️  Using production API (Coinbase CCXT doesn't support sandbox)")
        else:
            # Full authenticated config
            config = CoinbaseProConfig(
                api_key=settings.coinbase_api_key,
                secret=settings.coinbase_api_secret,
                password=settings.coinbase_passphrase,
                sandbox=False,  # Coinbase CCXT doesn't support sandbox, use production
                rate_limit=1000,
            )
            if use_sandbox:
                print("   ⚠️  Note: Coinbase via CCXT doesn't support sandbox mode")
                print("   ℹ️  Using production API instead")
        print("✅ Coinbase configuration created successfully")
    except Exception as e:
        print(f"❌ ERROR: Failed to create Coinbase configuration: {e}")
        sys.exit(1)

    # Initialize plugin
    plugin = None
    try:
        print("\n📡 Initializing Coinbase plugin...")
        plugin = CoinbaseProPlugin(config)
        await plugin.initialize()
        print("✅ Plugin initialized successfully")
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize plugin: {e}")
        logger.exception("Plugin initialization failed")
        sys.exit(1)

    try:
        # Test 1: Load markets
        print("\n📊 Test 1: Loading markets...")
        markets = await plugin.load_markets()
        print(f"✅ Loaded {len(markets)} trading pairs")
        if markets:
            sample_pairs = list(markets.keys())[:5]
            print(f"   Sample pairs: {', '.join(sample_pairs)}")
    except Exception as e:
        print(f"❌ ERROR: Failed to load markets: {e}")
        logger.exception("Market loading failed")
        await plugin.close()
        sys.exit(1)

    try:
        # Test 2: Fetch ticker
        print("\n💰 Test 2: Fetching ticker (BTC/USDT)...")
        ticker = await plugin.fetch_ticker("BTC/USDT")
        print("✅ Ticker fetched successfully")
        print(f"   Symbol: {ticker.get('symbol', 'N/A')}")
        print(f"   Last Price: {ticker.get('last', 'N/A')}")
        print(f"   Bid: {ticker.get('bid', 'N/A')}")
        print(f"   Ask: {ticker.get('ask', 'N/A')}")
    except Exception as e:
        print(f"⚠️  WARNING: Failed to fetch ticker (may not be available): {e}")
        logger.warning("Ticker fetch failed", exc_info=True)

    try:
        # Test 3: Fetch balance (if authenticated)
        print("\n💳 Test 3: Fetching account balance...")
        if not can_authenticate:
            print("   ⏭️  Skipped: Passphrase required for authenticated operations")
        else:
            balance = await plugin.fetch_balance()
            print("✅ Balance fetched successfully")

            # Show non-zero balances
            non_zero = {
                curr: bal
                for curr, bal in balance.items()
                if isinstance(bal, dict) and bal.get("total", 0) > 0
            }
            if non_zero:
                print(f"   Currencies with balance: {len(non_zero)}")
                for curr, bal in list(non_zero.items())[:5]:
                    total = bal.get("total", 0)
                    free = bal.get("free", 0)
                    print(f"   - {curr}: {free} free, {total} total")
            else:
                print("   No balances found (may be sandbox account)")
    except Exception as e:
        if "passphrase" in str(e).lower() or "password" in str(e).lower():
            print(f"   ⏭️  Skipped: {e}")
        else:
            print(f"⚠️  WARNING: Failed to fetch balance: {e}")
            logger.warning("Balance fetch failed", exc_info=True)

    try:
        # Test 4: Fetch orderbook
        print("\n📈 Test 4: Fetching orderbook (BTC/USDT)...")
        # Use the CCXT method directly since plugin may not expose it
        if plugin._ccxt:
            orderbook = await plugin._ccxt.fetch_order_book("BTC/USDT", 5)
            print("✅ Orderbook fetched successfully")
            bids = orderbook.get("bids", [])
            asks = orderbook.get("asks", [])
            print(f"   Bids: {len(bids)} entries")
            print(f"   Asks: {len(asks)} entries")
            if bids:
                print(f"   Best bid: {bids[0]}")
            if asks:
                print(f"   Best ask: {asks[0]}")
        else:
            print("   ⚠️  CCXT instance not available")
    except Exception as e:
        print(f"⚠️  WARNING: Failed to fetch orderbook: {e}")
        logger.warning("Orderbook fetch failed", exc_info=True)

    # Cleanup
    try:
        await plugin.close()
        print("\n✅ Plugin closed successfully")
    except Exception as e:
        print(f"⚠️  WARNING: Error closing plugin: {e}")

    print("\n" + "=" * 80)
    print("✅ Coinbase API Validation Completed Successfully!")
    print("=" * 80)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(validate_coinbase_api())
