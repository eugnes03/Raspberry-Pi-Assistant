import time
from openai import OpenAI
from assistant.utils.config import OPENAI_API_KEY
from assistant.utils.logger import setup_logger

logger = setup_logger()

client = OpenAI(api_key=OPENAI_API_KEY)

_SYSTEM_PROMPT = (
    "You are a research paper assistant for a math student with a strong interest in geometric deep learning. "
    "When summarizing, be brief (3-5 sentences). "
    "When explaining theorems, proofs, or lemmas, be mathematically rigorous — state assumptions, quantifiers, and conclusions precisely — "
    "but also build intuition: explain what the result is really saying, why it should be true, and what it rules out. "
    "If the paper's content (e.g. symmetry, group actions, manifolds, graphs, equivariance, topology, differential geometry, representation theory) "
    "connects to geometric deep learning, briefly note how — for example, how a result might inform or constrain GDL architectures, "
    "or how a concept appears in message passing, equivariant networks, or graph neural networks. "
    "Only make GDL connections when they are genuinely relevant; do not force them."
)

_assistant_id: str | None = None


def _get_assistant() -> str:
    """Lazily create (or reuse) a single persistent assistant."""
    global _assistant_id
    if _assistant_id:
        return _assistant_id
    assistant = client.beta.assistants.create(
        name="Research Paper Assistant",
        instructions=_SYSTEM_PROMPT,
        model="gpt-4o-mini",
    )
    _assistant_id = assistant.id
    logger.info(f"Created OpenAI assistant: {_assistant_id}")
    return _assistant_id


def _run_and_wait(thread_id: str) -> str:
    """Create a run and poll until complete, then return the assistant's reply."""
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=_get_assistant(),
    )
    while run.status in ("queued", "in_progress"):
        time.sleep(0.8)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

    if run.status != "completed":
        error_detail = ""
        if run.last_error:
            error_detail = f" — {run.last_error.code}: {run.last_error.message}"
        raise RuntimeError(f"Run ended with status: {run.status}{error_detail}")

    messages = client.beta.threads.messages.list(thread_id=thread_id, order="desc", limit=1)
    return messages.data[0].content[0].text.value


def start_paper_thread(text: str, is_full_text: bool = False) -> tuple[str, str]:
    """
    Create a new thread seeded with the paper content.
    Pass is_full_text=True when text is the full article body (not just the abstract).
    Returns (thread_id, summary_text).
    """
    label = "full text" if is_full_text else "abstract"
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"Here is the {label} of the paper I want to discuss:\n\n{text}\n\nGive me a concise summary.",
    )
    summary = _run_and_wait(thread.id)
    return thread.id, summary


def ask_thread(thread_id: str, question: str) -> str:
    """Send a follow-up question to an existing thread."""
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=question,
    )
    return _run_and_wait(thread_id)


# Legacy helper kept for any other callers
def summarize(text: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        max_tokens=150,
    )
    return response.choices[0].message.content.strip()
