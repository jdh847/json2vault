"""
Adapters convert source-specific JSON into the universal Note schema.

Each adapter is a function: (raw_json: dict) -> NoteCollection

Built-in adapters:
  - auto:       Tries to detect format automatically
  - universal:  JSON already in json2vault's own schema
  - xhs:        Xiaohongshu / RedNote favorites export
  - weibo:      Weibo favorites/posts export
  - twitter:    Twitter/X data export (archive)
  - pocket:     Pocket export
  - generic:    Flat list of objects with 'title' and 'content' fields
"""

from .registry import get_adapter, list_adapters, detect_adapter

__all__ = ["get_adapter", "list_adapters", "detect_adapter"]
