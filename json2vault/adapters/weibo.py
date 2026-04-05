"""Adapter for Weibo (微博) exports."""

from ..schema import Note, NoteCollection
from .registry import register


@register("weibo")
def adapt(data: dict) -> NoteCollection:
    """
    Convert Weibo export JSON to universal schema.

    Supports common Weibo scraper output formats.
    """
    raw = data.get("statuses") or data.get("posts") or data.get("notes") or data.get("data", [])
    if isinstance(data, list):
        raw = data

    notes = []
    for item in raw:
        weibo_id = str(item.get("id") or item.get("mid", ""))
        content = item.get("text") or item.get("content", "")

        # Strip HTML tags from Weibo content
        import re
        clean_content = re.sub(r"<[^>]+>", "", content)

        # Title: first line or first 80 chars
        title = item.get("title", "")
        if not title:
            title = clean_content.split("\n")[0][:80] if clean_content else "Untitled"

        # User info
        user = item.get("user", {})
        author = user.get("screen_name") or user.get("name", "")

        # Date
        date = item.get("created_at", "")

        # Images
        images = []
        pics = item.get("pics", [])
        for pic in pics:
            url = pic.get("large", {}).get("url") or pic.get("url", "")
            if url:
                images.append(url)
        if not images and item.get("original_pic"):
            images.append(item["original_pic"])
        if not images and item.get("thumbnail_pic"):
            images.append(item["thumbnail_pic"].replace("thumbnail", "large"))

        # Videos
        videos = []
        page_info = item.get("page_info", {})
        if page_info.get("type") == "video":
            media_info = page_info.get("media_info", {})
            video_url = (
                media_info.get("stream_url_hd")
                or media_info.get("stream_url")
                or ""
            )
            if video_url:
                videos.append(video_url)

        # Tags / topics
        tags = []
        for topic in item.get("topic_struct", []):
            if topic.get("topic_title"):
                tags.append(topic["topic_title"])
        # Also extract #hashtags# from content
        import re
        hashtags = re.findall(r"#(.+?)#", content)
        tags.extend(h for h in hashtags if h not in tags)

        metadata = {}
        if item.get("reposts_count"):
            metadata["reposts"] = str(item["reposts_count"])
        if item.get("comments_count"):
            metadata["comments"] = str(item["comments_count"])
        if item.get("attitudes_count"):
            metadata["likes"] = str(item["attitudes_count"])

        note_type = "video" if videos else ("image" if images else "text")

        notes.append(Note(
            id=weibo_id,
            title=title,
            content=clean_content,
            author=author,
            date=date,
            source_url=f"https://weibo.com/{user.get('id', '')}/{weibo_id}" if weibo_id else "",
            source_platform="weibo",
            note_type=note_type,
            tags=tags,
            images=images,
            videos=videos,
            metadata=metadata,
        ))

    return NoteCollection(
        notes=notes,
        source="weibo",
        exported_at=data.get("exported_at", "") if isinstance(data, dict) else "",
    )
