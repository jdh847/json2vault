"""Adapter for Xiaohongshu (小红书 / RedNote) favorites export."""

from ..schema import Note, NoteCollection
from .registry import register


@register("xhs")
def adapt(data: dict) -> NoteCollection:
    """
    Convert XHS favorites JSON to universal schema.

    Supports multiple export formats with varying field names.
    """
    raw_notes = data.get("notes", [])
    if isinstance(data, list):
        raw_notes = data

    notes = []
    for n in raw_notes:
        note_id = n.get("note_id") or n.get("noteId") or n.get("id", "")

        # Title: try common field names
        title = n.get("title") or n.get("display_title") or n.get("displayTitle") or ""
        content = n.get("desc") or n.get("content") or n.get("description") or ""

        # Author
        author = n.get("author") or n.get("author_nickname") or ""
        if not author and isinstance(n.get("user"), dict):
            author = n["user"].get("nickname", "")

        # Date
        date = n.get("timeStr") or n.get("date") or ""
        if not date and n.get("time"):
            try:
                from datetime import datetime
                date = datetime.fromtimestamp(n["time"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError, OSError):
                pass

        # Images
        images = n.get("images", [])
        if not images and n.get("image_urls"):
            images = n["image_urls"]
        if not images:
            for img in n.get("imageList", []):
                url = img.get("urlDefault") or img.get("url", "")
                if url:
                    if url.startswith("//"):
                        url = "https:" + url
                    images.append(url)

        # Video
        videos = []
        video_url = n.get("videoUrl") or n.get("video_url") or ""
        if video_url:
            videos.append(video_url)

        # Tags
        tags = n.get("tags", [])
        if not tags:
            tags = [t.get("name", "") for t in n.get("tagList", []) if t.get("name")]

        # Engagement stats
        interact = n.get("interactInfo", {})
        metadata = {}
        for key, sources in [
            ("likes", ["liked", "likedCount", "liked_count"]),
            ("collects", ["collected", "collectedCount", "collected_count"]),
            ("comments", ["comments", "commentCount", "comment_count"]),
        ]:
            for s in sources:
                val = interact.get(s) or n.get(s)
                if val:
                    metadata[key] = str(val)
                    break

        note_type = "video" if (n.get("type") == "video" or videos) else "text"

        notes.append(Note(
            id=note_id,
            title=title,
            content=content,
            author=author,
            date=date,
            source_url=f"https://www.xiaohongshu.com/explore/{note_id}" if note_id else "",
            source_platform="xiaohongshu",
            note_type=note_type,
            tags=tags,
            images=images,
            videos=videos,
            metadata=metadata,
        ))

    return NoteCollection(
        notes=notes,
        source=data.get("source", "xiaohongshu"),
        exported_at=data.get("exported_at", ""),
    )
