import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
CHAT_IDS_FILE = os.path.join(DATA_DIR, 'chat_ids.json')

_paused = False
_pause_reason = ""
_chat_ids: set = set()


def load_chat_ids():
    global _chat_ids
    if os.path.exists(CHAT_IDS_FILE):
        with open(CHAT_IDS_FILE) as f:
            _chat_ids = set(json.load(f))


def _save_chat_ids():
    with open(CHAT_IDS_FILE, 'w') as f:
        json.dump(list(_chat_ids), f)


def register_chat(chat_id: int):
    _chat_ids.add(chat_id)
    _save_chat_ids()


def get_chat_ids() -> list[int]:
    return list(_chat_ids)


def is_paused() -> bool:
    return _paused


def pause(reason: str = ""):
    global _paused, _pause_reason
    _paused = True
    _pause_reason = reason


def resume():
    global _paused, _pause_reason
    _paused = False
    _pause_reason = ""


def get_pause_reason() -> str:
    return _pause_reason
