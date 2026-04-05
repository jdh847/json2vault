"""
Generic adapter — handles any JSON with recognizable fields.

This is the fallback adapter. It looks for common field names
(title, content, text, body, description, url, date, tags, etc.)
and maps them to the universal schema with best-effort matching.
"""

from ..schema import Note, NoteCollection
from .registry import register

# Common field name mappings (source field → schema field)
_TITLE_FIELDS = ["title", "name", "subject", "heading", "headline"]
_CONTENT_FIELDS = ["content", "text", "body", "description", "desc", "summary", "excerpt"]
_AUTHOR_FIELDS = ["author", "creator", "user", "username", "by", "writer"]
_DATE_FIELDS = ["date", "created_at", "timestamp", "time", "published", "created", "updated_at"]
_URL_FIELDS = ["url", "link", "source_url", "href", "source", "permalink"]
_TAG_FIELDS = ["tags", "labels", "categories", "keywords", "topics"]
_ID_FIELDS = ["id", "uid", "note_id", "item_id", "post_id", "entry_id"]


def _find_field(item: dict, candidates: list[str]) -> str:
    """Find the first matching field from a list of candidates."""
    for key in candidates:
        val = item.get(key)
        if val and isinstance(val, str):
            return val
    return ""


def _find_list_field(item: dict, candidates: list[str]) -> list[str]:
    """Find the first matching list field."""
    for key in candidates:
        val = item.get(key)
        if isinstance(val, list):
            return [str(v) for v in val if v]
        if isinstance(val, str) and "," in val:
            return [t.strip() for t in val.split(",") if t.strip()]
    return []


@register("generic")
def adapt(data: dict) -> NoteCollection:
    """
    Convert any JSON with common field names to universal schema.

    Accepts:
    - {"notes": [...]}  or  {"items": [...]}  or  {"data": [...]}
    - bare list [...]
    """
    # Find the list of items
    raw = data
    source = ""
    exported_at = ""

    if isinstance(data, dict):
        source = data.get("source", "")
        exported_at = data.get("exported_at", "")
        for key in ("notes", "items", "data", "entries", "posts", "records", "results"):
            if isinstance(data.get(key), list):
                raw = data[key]
                break

    if isinstance(raw, dict):
        raw = [raw]

    if not isinstance(raw, list):
        return NoteCollection(source=source, exported_at=exported_at)

    notes = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            continue

        note_id = _find_field(item, _ID_FIELDS) or str(i)
        title = _find_field(item, _TITLE_FIELDS)
        content = _find_field(item, _CONTENT_FIELDS)

        # If no title, use first line of content
        if not title and content:
            title = content.split("\n")[0][:80]
        if not title:
            title = f"Note {i + 1}"

        # Author — might be a string or a nested dict
        author = _find_field(item, _AUTHOR_FIELDS)
        if not author:
            for key in _AUTHOR_FIELDS:
                val = item.get(key)
                if isinstance(val, dict):
                    author = val.get("name") or val.get("nickname") or val.get("username", "")
                    break

        tags = _find_list_field(item, _TAG_FIELDS)

        # Collect any remaining fields as metadata
        known_keys = set()
        for field_list in [_TITLE_FIELDS, _CONTENT_FIELDS, _AUTHOR_FIELDS,
                           _DATE_FIELDS, _URL_FIELDS, _TAG_FIELDS, _ID_FIELDS]:
            known_keys.update(field_list)

        metadata = {}
        for k, v in item.items():
            if k not in known_keys and isinstance(v, (str, int, float, bool)):
                metadata[k] = str(v)

        notes.append(Note(
            id=note_id,
            title=title,
            content=content,
            author=author,
            date=_find_field(item, _DATE_FIELDS),
            source_url=_find_field(item, _URL_FIELDS),
            source_platform=source or "unknown",
            tags=tags,
            metadata=metadata,
        ))

    return NoteCollection(notes=notes, source=source, exported_at=exported_at)
