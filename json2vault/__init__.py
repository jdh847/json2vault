"""
json2vault: Turn any JSON data into a structured Obsidian vault.

Feed it JSON from any source — social media exports, API dumps,
data archives, bookmarks — and get a fully indexed Obsidian vault
with YAML frontmatter, embedded media references, and tag indexes.

Library usage::

    from json2vault import convert

    # One-liner: JSON file → Obsidian vault
    result = convert("data.json", "./my-vault")

    # With explicit adapter
    result = convert("favorites.json", "./vault", adapter="xhs")

    # Granular: load → adapt → build
    from json2vault import load_json, adapt, build_vault

    data = load_json("data.json")
    collection = adapt(data)                     # auto-detect
    collection = adapt(data, adapter="twitter")  # explicit
    result = build_vault(collection, "./vault")
"""

__version__ = "0.1.0"

import json
from pathlib import Path
from typing import Optional, Union

from .schema import Note, NoteCollection
from .adapters import get_adapter, list_adapters, detect_adapter
from .vault import build_vault


def load_json(path: Union[str, Path]) -> dict:
    """Load and parse a JSON file.

    Args:
        path: Path to a JSON file.

    Returns:
        Parsed JSON data as a dict or list.
    """
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def adapt(data: dict, adapter: Optional[str] = None) -> NoteCollection:
    """Convert raw JSON data to a NoteCollection using an adapter.

    Args:
        data: Parsed JSON data.
        adapter: Adapter name (e.g. "xhs", "twitter", "pocket", "weibo",
                 "generic", "universal"). If None, auto-detects the format.

    Returns:
        NoteCollection ready for vault generation.

    Raises:
        ValueError: If adapter is unknown or auto-detection fails.
    """
    if adapter is None:
        detected = detect_adapter(data)
        if not detected:
            raise ValueError(
                f"Could not auto-detect format. "
                f"Available adapters: {', '.join(list_adapters())}"
            )
        adapter = detected

    adapter_fn = get_adapter(adapter)
    return adapter_fn(data)


def convert(
    input_path: Union[str, Path],
    output_dir: Union[str, Path] = "./vault",
    adapter: Optional[str] = None,
    skip_media_manifest: bool = False,
) -> dict:
    """Convert a JSON file into an Obsidian vault. One-liner API.

    Args:
        input_path: Path to a JSON file.
        output_dir: Output vault directory.
        adapter: Adapter name, or None for auto-detection.
        skip_media_manifest: If True, skip generating media_manifest.json.

    Returns:
        dict with 'notes_count', 'tags_count', 'media_manifest' keys.
    """
    data = load_json(input_path)
    collection = adapt(data, adapter=adapter)
    return build_vault(collection, Path(output_dir), skip_media_manifest=skip_media_manifest)


__all__ = [
    "convert",
    "load_json",
    "adapt",
    "build_vault",
    "Note",
    "NoteCollection",
    "get_adapter",
    "list_adapters",
    "detect_adapter",
]
