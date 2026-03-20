import json
import os
import arxiv
from assistant.utils.logger import setup_logger

logger = setup_logger()

TOPICS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'topics.json')


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

def get_papers(query: str, max_results: int = 5) -> list[dict]:
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )
    results = []
    for result in search.results():
        results.append({
            "title":   result.title,
            "authors": [a.name for a in result.authors],
            "summary": result.summary,
            "link":    result.entry_id,
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
