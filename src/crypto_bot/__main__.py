#!/usr/bin/env python3
"""
Crypto Trading Bot - Main Entry Point

This module serves as the main entry point for the Crypto Trading Bot application.
It can be run directly with `python -m crypto_bot` or through the CLI.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from crypto_bot.cli.main import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Crypto Trading Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
