"""Telegram bot module for cafe notifications."""

__all__ = ["bot", "dp"]


def __getattr__(name):
    """Lazy import to avoid circular imports and module loading issues."""
    if name in ("bot", "dp"):
        from .bot import bot, dp
        return bot if name == "bot" else dp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
