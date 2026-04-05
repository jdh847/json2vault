"""Adapter for json2vault's own universal format."""

from ..schema import Note, NoteCollection
from .registry import register


@register("universal")
def adapt(data: dict) -> NoteCollection:
    """
    Load data already in json2vault universal format.

    Expected structure:
    {
      "json2vault_version": "1",
      "source": "...",
      "exported_at": "...",
      "notes": [ { ...Note fields... } ]
    }
    """
    notes = [Note.from_dict(n) for n in data.get("notes", [])]
    return NoteCollection(
        notes=notes,
        source=data.get("source", ""),
        exported_at=data.get("exported_at", ""),
    )
