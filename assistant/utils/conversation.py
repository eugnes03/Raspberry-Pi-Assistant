# In-memory map of Telegram chat_id -> OpenAI thread_id
# Cleared on bot restart; threads persist on OpenAI's side.

_threads: dict[int, str] = {}


def set_thread(chat_id: int, thread_id: str):
    _threads[chat_id] = thread_id


def get_thread(chat_id: int) -> str | None:
    return _threads.get(chat_id)


def clear_thread(chat_id: int):
    _threads.pop(chat_id, None)
