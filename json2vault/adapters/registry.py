"""
Adapter registry — maps format names to adapter functions.

Each adapter takes a raw dict (parsed JSON) and returns a NoteCollection.
"""

from typing import Callable, Optional

from ..schema import NoteCollection

# Type alias for adapter functions
AdapterFn = Callable[[dict], NoteCollection]

# Registry of built-in adapters
_ADAPTERS: dict[str, AdapterFn] = {}


def register(name: str):
    """Decorator to register an adapter."""
    def decorator(fn: AdapterFn) -> AdapterFn:
        _ADAPTERS[name] = fn
        return fn
    return decorator


def get_adapter(name: str) -> AdapterFn:
    """Get adapter by name."""
    if name not in _ADAPTERS:
        available = ", ".join(sorted(_ADAPTERS.keys()))
        raise ValueError(f"Unknown adapter '{name}'. Available: {available}")
    return _ADAPTERS[name]


def list_adapters() -> list[str]:
    """List all registered adapter names."""
    return sorted(_ADAPTERS.keys())


def detect_adapter(data: dict) -> Optional[str]:
    """Try to auto-detect the right adapter for the given JSON data."""
    # json2vault universal format
    if data.get("json2vault_version"):
        return "universal"

    # XHS / RedNote
    if data.get("source") == "xiaohongshu_favorites":
        return "xhs"
    if isinstance(data.get("notes"), list) and any(
        "note_id" in n or "display_title" in n for n in data["notes"][:5]
    ):
        return "xhs"

    # Twitter / X archive
    if isinstance(data, list) and any("tweet" in item for item in data[:5]):
        return "twitter"

    # Pocket export
    if isinstance(data, list) and any("resolved_title" in item for item in data[:5]):
        return "pocket"

    # Weibo
    if data.get("source") in ("weibo", "weibo_favorites"):
        return "weibo"

    # Generic fallback: list of objects with title/content
    items = data.get("notes") or data.get("items") or data.get("data")
    if isinstance(items, list) and items:
        sample = items[0]
        if isinstance(sample, dict) and ("title" in sample or "content" in sample):
            return "generic"

    # Bare list
    if isinstance(data, list) and data and isinstance(data[0], dict):
        if "title" in data[0] or "content" in data[0]:
            return "generic"

    return None


# Import built-in adapters to trigger registration
from . import universal, xhs, twitter, pocket, weibo, generic  # noqa: E402, F401
