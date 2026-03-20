import urllib.request
import xml.etree.ElementTree as ET
from assistant.utils.logger import setup_logger

logger = setup_logger()

RSS_FEEDS = {
    'world':    'https://feeds.bbci.co.uk/news/world/rss.xml',
    'tech':     'https://feeds.bbci.co.uk/news/technology/rss.xml',
    'science':  'https://feeds.bbci.co.uk/news/science_and_environment/rss.xml',
    'us':       'https://feeds.bbci.co.uk/news/us_and_canada/rss.xml',
    'business': 'https://feeds.bbci.co.uk/news/business/rss.xml',
    'general':  'https://feeds.bbci.co.uk/news/rss.xml',
}


def fetch_headlines(category: str = 'general', count: int = 5) -> list[dict]:
    url = RSS_FEEDS.get(category.lower(), RSS_FEEDS['general'])
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            root = ET.fromstring(response.read())
        items = root.findall('.//item')[:count]
        return [
            {
                'title': item.findtext('title', '').strip(),
                'link':  item.findtext('link', '').strip(),
            }
            for item in items
        ]
    except Exception as e:
        logger.error(f"News fetch error ({category}): {e}")
        return []


def format_headlines(category: str = 'general', count: int = 5) -> str:
    category = category.strip().lower() or 'general'
    if category not in RSS_FEEDS:
        cats = ', '.join(RSS_FEEDS.keys())
        return f"Unknown category '{category}'. Available: {cats}"

    items = fetch_headlines(category, count)
    if not items:
        return "Couldn't fetch news right now."

    lines = [f"Top {category} news:\n"]
    for i, item in enumerate(items, 1):
        lines.append(f"{i}. {item['title']}\n   {item['link']}")
    return '\n'.join(lines)


def digest_section(categories: list[str] | None = None, count: int = 5) -> str:
    """Fetch multiple categories for the daily digest."""
    cats = categories or ['world', 'tech', 'science']
    sections = []
    for cat in cats:
        items = fetch_headlines(cat, count)
        if items:
            block = f"[{cat.upper()} NEWS]\n"
            for i, item in enumerate(items, 1):
                block += f"{i}. {item['title']}\n"
            sections.append(block)
    return '\n'.join(sections)
