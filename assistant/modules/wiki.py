from assistant.utils.logger import setup_logger

logger = setup_logger()


def search(query: str, sentences: int = 4) -> str:
    """Return a Wikipedia summary for `query`."""
    try:
        import wikipedia
    except ImportError:
        return "wikipedia package not installed. Run: pip install wikipedia"

    try:
        summary = wikipedia.summary(query, sentences=sentences, auto_suggest=True)
        page = wikipedia.page(query, auto_suggest=True)
        return f"{summary}\n\nRead more: {page.url}"
    except wikipedia.DisambiguationError as e:
        options = e.options[:5]
        opts = "\n".join(f"  • {o}" for o in options)
        return f'"{query}" is ambiguous. Did you mean:\n{opts}\n\nTry again with a more specific term.'
    except wikipedia.PageError:
        return f'No Wikipedia page found for "{query}".'
    except Exception as e:
        logger.error(f"Wikipedia error: {e}")
        return f"Error fetching Wikipedia page: {e}"
