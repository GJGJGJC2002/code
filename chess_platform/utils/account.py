import json
import os
import hashlib
from typing import Dict, Optional

ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "accounts.json")


def _load() -> Dict:
    if not os.path.exists(ACCOUNT_FILE):
        return {}
    with open(ACCOUNT_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}


def _save(data: Dict):
    with open(ACCOUNT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _hash(pwd: str) -> str:
    return hashlib.sha256(pwd.encode("utf-8")).hexdigest()


def register(username: str, password: str) -> bool:
    data = _load()
    if username in data:
        return False
    data[username] = {
        "pwd": _hash(password),
        "stats": {
            "games": 0,
            "win": 0,
            "draw": 0,
            "loss": 0
        }
    }
    _save(data)
    return True


def login(username: str, password: str) -> bool:
    data = _load()
    if username not in data:
        return False
    return data[username]["pwd"] == _hash(password)


def get_stats(username: str) -> Optional[Dict]:
    data = _load()
    return data.get(username, {}).get("stats")


def update_result(username: str, result: str):
    """
    result: 'win'/'loss'/'draw'
    """
    data = _load()
    if username not in data:
        return
    stats = data[username]["stats"]
    stats["games"] += 1
    if result in ["win", "loss", "draw"]:
        stats[result] += 1
    _save(data)


