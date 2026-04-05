"""
Universal note schema.

Every adapter converts source-specific JSON into this common format.
The vault builder only knows about this schema — it never sees raw source data.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Note:
    """A single note in the universal schema."""

    id: str
    title: str
    content: str = ""
    author: str = ""
    date: str = ""
    source_url: str = ""
    source_platform: str = ""
    note_type: str = "text"  # text, image, video, link
    tags: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    videos: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "author": self.author,
            "date": self.date,
            "source_url": self.source_url,
            "source_platform": self.source_platform,
            "note_type": self.note_type,
            "tags": self.tags,
            "images": self.images,
            "videos": self.videos,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Note":
        return cls(
            id=d.get("id", ""),
            title=d.get("title", ""),
            content=d.get("content", ""),
            author=d.get("author", ""),
            date=d.get("date", ""),
            source_url=d.get("source_url", ""),
            source_platform=d.get("source_platform", ""),
            note_type=d.get("note_type", "text"),
            tags=d.get("tags", []),
            images=d.get("images", []),
            videos=d.get("videos", []),
            metadata=d.get("metadata", {}),
        )


@dataclass
class NoteCollection:
    """A collection of notes ready for vault generation."""

    notes: list[Note] = field(default_factory=list)
    source: str = ""
    exported_at: str = ""

    @property
    def count(self) -> int:
        return len(self.notes)

    def all_tags(self) -> dict[str, int]:
        """Return tag → count mapping, sorted by frequency."""
        counts: dict[str, int] = {}
        for note in self.notes:
            for tag in note.tags:
                counts[tag] = counts.get(tag, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: -x[1]))
