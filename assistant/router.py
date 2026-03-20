from assistant.modules import research
from assistant.utils.logger import setup_logger

logger = setup_logger()


def route(message: str) -> str:
    """Fallback router for plain-text (non-command) messages."""
    msg = message.lower().strip()
    logger.info(f"Routing plain message: {message}")

    try:
        if msg.startswith("search:"):
            query = message.split(":", 1)[1].strip()
            return research.handle(query, use_llm=False)

        if "paper" in msg or "research" in msg:
            return research.handle(message, use_llm=False)

        return "Use /help to see available commands."

    except Exception as e:
        logger.error(f"Router error: {e}")
        return f"Error: {e}"
