import json
import os
import re
import arxiv
import requests
from bs4 import BeautifulSoup
from assistant.utils.logger import setup_logger

logger = setup_logger()

TOPICS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'topics.json')

# Regex to detect arxiv category codes like math.AG, cs.LG, cond-mat.supr-con, hep-th, quant-ph
_CATEGORY_RE = re.compile(r'^[a-zA-Z][a-zA-Z-]*(\.[a-zA-Z]{2,8})?$')


# ---------------------------------------------------------------------------
# Topic persistence
# ---------------------------------------------------------------------------

def load_topics() -> list[str]:
    if os.path.exists(TOPICS_FILE):
        with open(TOPICS_FILE) as f:
            return json.load(f)
    return []


def save_topics(topics: list[str]):
    with open(TOPICS_FILE, 'w') as f:
        json.dump(topics, f, indent=2)


# ---------------------------------------------------------------------------
# arXiv search
# ---------------------------------------------------------------------------

def is_category(query: str) -> bool:
    """Return True if the query looks like an arXiv category code (e.g. math.AG, cs.LG, hep-th)."""
    q = query.strip()
    # Must be a single token (no spaces) and match the category pattern
    return ' ' not in q and bool(_CATEGORY_RE.match(q))


def get_papers(query: str, max_results: int = 5) -> list[dict]:
    """Search arXiv. If query is a category code, list newest papers in that category."""
    if is_category(query):
        arxiv_query = f"cat:{query}"
    else:
        arxiv_query = query
    search = arxiv.Search(
        query=arxiv_query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )
    results = []
    for result in search.results():
        results.append({
            "title":    result.title,
            "authors":  [a.name for a in result.authors],
            "summary":  result.summary,
            "link":     result.entry_id,
            "arxiv_id": result.get_short_id(),
        })
    return results


def format_papers(papers: list[dict], use_llm: bool = False) -> str:
    if not papers:
        return "No papers found."

    response = ""
    for p in papers:
        response += f"• {p['title']}\n"
        response += f"  {', '.join(p['authors'][:3])}\n"

        if use_llm:
            try:
                from assistant.utils.openai_client import summarize
                summary = summarize(p["summary"])
                response += f"  Summary: {summary}\n"
            except Exception as e:
                logger.error(f"LLM error: {e}")

        response += f"  {p['link']}\n\n"

    return response.strip()


def get_paper_by_id(arxiv_url: str) -> dict | None:
    """Fetch a single paper from an arXiv URL or bare ID like 2301.12345."""
    match = re.search(r'(\d{4}\.\d{4,5}(?:v\d+)?)', arxiv_url)
    if not match:
        return None
    arxiv_id = match.group(1)
    try:
        client = arxiv.Client()
        search = arxiv.Search(id_list=[arxiv_id])
        result = next(client.results(search))
        return {
            "title":    result.title,
            "authors":  [a.name for a in result.authors],
            "summary":  result.summary,
            "link":     result.entry_id,
            "arxiv_id": arxiv_id,
        }
    except StopIteration:
        return None
    except Exception as e:
        logger.error(f"arXiv fetch error: {e}")
        return None


def fetch_paper_full_text(arxiv_id: str) -> str | None:
    """
    Try to fetch the full HTML version of a paper from arxiv.org/html/{id}.
    Returns extracted plain text (truncated to ~10 000 chars) or None if unavailable.
    """
    url = f"https://arxiv.org/html/{arxiv_id}"
    try:
        resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
        text = soup.get_text(separator=' ', strip=True)
        return text[:10000] if text else None
    except Exception as e:
        logger.error(f"HTML fetch error for {arxiv_id}: {e}")
        return None


def handle(message: str, use_llm: bool = False) -> str:
    logger.info(f"Research query: {message} | LLM: {use_llm}")
    papers = get_papers(message)
    return format_papers(papers, use_llm)


# ---------------------------------------------------------------------------
# /settopics command helper
# ---------------------------------------------------------------------------

def set_topics(args: str) -> str:
    topics = [t.strip() for t in args.split(',') if t.strip()]
    if not topics:
        return "Provide topics separated by commas.\nExample: /settopics machine learning, quantum computing"
    save_topics(topics)
    lines = ["Topics saved:"] + [f"  • {t}" for t in topics]
    return '\n'.join(lines)


def list_topics() -> str:
    topics = load_topics()
    if not topics:
        return "No topics set. Use /settopics to configure."
    lines = ["Current research topics:"] + [f"  • {t}" for t in topics]
    return '\n'.join(lines)
