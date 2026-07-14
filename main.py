"""Entry point for the Hori Telegram moderation bot.

Run with: python main.py
"""

from __future__ import annotations

import asyncio

from core.startup import run_application


def main() -> None:
    """Run the bot's asyncio event loop until interrupted or terminated."""
    try:
        asyncio.run(run_application())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
