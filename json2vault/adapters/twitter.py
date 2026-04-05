"""Adapter for Twitter / X data export archive."""

from ..schema import Note, NoteCollection
from .registry import register


@register("twitter")
def adapt(data: dict) -> NoteCollection:
    """
    Convert Twitter/X archive JSON to universal schema.

    Supports the official Twitter data export format (tweets.json from archive).
    """
    raw = data if isinstance(data, list) else data.get("tweets", data.get("data", []))

    notes = []
    for item in raw:
        tweet = item.get("tweet", item)
        tweet_id = tweet.get("id_str") or tweet.get("id", "")

        # Content
        content = tweet.get("full_text") or tweet.get("text", "")

        # First line or first 80 chars as title
        first_line = content.split("\n")[0][:80] if content else "Untitled"

        # Date
        date = tweet.get("created_at", "")

        # Media
        images = []
        videos = []
        media_list = tweet.get("extended_entities", {}).get("media", [])
        if not media_list:
            media_list = tweet.get("entities", {}).get("media", [])
        for m in media_list:
            if m.get("type") == "video":
                variants = m.get("video_info", {}).get("variants", [])
                mp4s = [v for v in variants if v.get("content_type") == "video/mp4"]
                if mp4s:
                    best = max(mp4s, key=lambda v: v.get("bitrate", 0))
                    videos.append(best["url"])
            else:
                images.append(m.get("media_url_https") or m.get("media_url", ""))

        # Hashtags
        tags = [h["text"] for h in tweet.get("entities", {}).get("hashtags", [])]

        # User
        user = tweet.get("user", {})
        author = user.get("screen_name") or user.get("name", "")

        metadata = {}
        if tweet.get("retweet_count"):
            metadata["retweets"] = str(tweet["retweet_count"])
        if tweet.get("favorite_count"):
            metadata["likes"] = str(tweet["favorite_count"])

        note_type = "video" if videos else ("image" if images else "text")

        notes.append(Note(
            id=tweet_id,
            title=first_line,
            content=content,
            author=author,
            date=date,
            source_url=f"https://x.com/{author}/status/{tweet_id}" if tweet_id and author else "",
            source_platform="twitter",
            note_type=note_type,
            tags=tags,
            images=images,
            videos=videos,
            metadata=metadata,
        ))

    return NoteCollection(
        notes=notes,
        source="twitter",
        exported_at=data.get("exported_at", "") if isinstance(data, dict) else "",
    )
