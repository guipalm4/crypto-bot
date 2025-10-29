#!/usr/bin/env python3
"""
Crypto Trading Bot - Main Entry Point

This module serves as the main entry point for the Crypto Trading Bot application.
It can be run directly with `python -m crypto_bot` or through the CLI.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from crypto_bot.cli.main import main
from crypto_bot.utils.system_events import log_critical_error, log_shutdown, log_startup

if __name__ == "__main__":
    try:
        # Log startup
        log_startup(
            app_name="Crypto Trading Bot",
            version="0.1.0",
            environment=sys.argv[-1] if len(sys.argv) > 1 else "development",
        )

        main()
        log_shutdown(reason="normal_exit", exit_code=0)
        sys.exit(0)
    except KeyboardInterrupt:
        log_shutdown(reason="user_interrupt", exit_code=130)
        print("\n👋 Crypto Trading Bot stopped by user")
        sys.exit(130)
    except Exception as e:
        log_critical_error(e, context={"module": "__main__"})
        print(f"❌ Error: {e}")
        sys.exit(1)
