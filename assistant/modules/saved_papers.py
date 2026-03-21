import json
import os
import re
from datetime import date
from assistant.utils.logger import setup_logger

logger = setup_logger()

SAVED_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'saved_papers.json')


def _load() -> list[dict]:
    if os.path.exists(SAVED_FILE):
        with open(SAVED_FILE) as f:
            return json.load(f)
    return []


def _save(papers: list[dict]):
    with open(SAVED_FILE, 'w') as f:
        json.dump(papers, f, indent=2)


def save_paper(paper: dict) -> str:
    """Save a paper dict (from get_paper_by_id). Returns status message."""
    arxiv_id = re.search(r'(\d{4}\.\d{4,5}(?:v\d+)?)', paper['link'])
    arxiv_id = arxiv_id.group(1) if arxiv_id else paper['link']

    papers = _load()
    if any(p['id'] == arxiv_id for p in papers):
        return f'Already saved: "{paper["title"]}"'

    papers.append({
        'id':       arxiv_id,
        'title':    paper['title'],
        'authors':  paper['authors'][:3],
        'link':     paper['link'],
        'saved_at': date.today().isoformat(),
    })
    _save(papers)
    return f'Saved: "{paper["title"]}"'


def list_papers() -> str:
    papers = _load()
    if not papers:
        return "No saved papers. Use /save <arxiv URL> to save one."
    lines = [f"Saved papers ({len(papers)}):\n"]
    for i, p in enumerate(papers, 1):
        authors = ', '.join(p['authors'])
        lines.append(f"{i}. {p['title']}\n   {authors}\n   {p['link']}\n   Saved: {p['saved_at']}")
    return '\n'.join(lines)


def remove_paper(index_or_id: str) -> str:
    """Remove by 1-based index or arXiv ID."""
    papers = _load()
    if not papers:
        return "No saved papers."

    # Try as 1-based index first
    if index_or_id.isdigit():
        idx = int(index_or_id) - 1
        if not (0 <= idx < len(papers)):
            return f"No paper at position {index_or_id}. You have {len(papers)} saved."
        removed = papers.pop(idx)
        _save(papers)
        return f'Removed: "{removed["title"]}"'

    # Try as arXiv ID
    before = len(papers)
    papers = [p for p in papers if p['id'] != index_or_id]
    if len(papers) == before:
        return f'No saved paper with ID "{index_or_id}".'
    _save(papers)
    return f'Removed paper {index_or_id}.'
