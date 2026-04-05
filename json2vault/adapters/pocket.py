"""Adapter for Pocket export data."""

from ..schema import Note, NoteCollection
from .registry import register


@register("pocket")
def adapt(data: dict) -> NoteCollection:
    """
    Convert Pocket export JSON to universal schema.

    Supports the Pocket API export format (list of saved items).
    """
    raw = data if isinstance(data, list) else data.get("list", data.get("items", []))

    # Pocket API sometimes returns a dict keyed by item_id
    if isinstance(raw, dict):
        raw = list(raw.values())

    notes = []
    for item in raw:
        item_id = str(item.get("item_id") or item.get("resolved_id", ""))
        title = item.get("resolved_title") or item.get("given_title") or ""
        content = item.get("excerpt", "")
        url = item.get("resolved_url") or item.get("given_url", "")

        # Date
        date = ""
        if item.get("time_added"):
            try:
                from datetime import datetime
                date = datetime.fromtimestamp(int(item["time_added"])).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            except (ValueError, TypeError, OSError):
                pass

        # Tags
        tags = []
        if isinstance(item.get("tags"), dict):
            tags = list(item["tags"].keys())

        # Images
        images = []
        if item.get("top_image_url"):
            images.append(item["top_image_url"])
        if isinstance(item.get("images"), dict):
            for img in item["images"].values():
                if img.get("src"):
                    images.append(img["src"])

        metadata = {}
        if item.get("word_count"):
            metadata["word_count"] = str(item["word_count"])
        if item.get("lang"):
            metadata["language"] = item["lang"]

        notes.append(Note(
            id=item_id,
            title=title,
            content=content,
            author=item.get("authors", {}).get("1", {}).get("name", ""),
            date=date,
            source_url=url,
            source_platform="pocket",
            note_type="link",
            tags=tags,
            images=images,
            metadata=metadata,
        ))

    return NoteCollection(notes=notes, source="pocket")
