"""
Obsidian vault generator.

Takes a NoteCollection and produces a complete Obsidian vault:
  - One markdown file per note (YAML frontmatter + content + media + tags)
  - Index page linking all notes
  - Tag index grouped by frequency
  - .obsidian config directory
  - Media manifest for external download
"""

import json
import re
from datetime import datetime
from pathlib import Path

from .schema import Note, NoteCollection

__all__ = ["build_vault"]


def sanitize_filename(name: str, max_len: int = 80) -> str:
    """Clean a string for use as a filename."""
    name = re.sub(r'[<>:"/\\|?*\n\r\t]', "", name)
    name = name.strip(". ")
    if len(name) > max_len:
        name = name[:max_len].rstrip()
    return name or "untitled"


def _render_note(note: Note, media_refs: list[str]) -> str:
    """Render a single Note to Obsidian-compatible markdown."""

    # YAML frontmatter
    fm_fields = {
        "title": note.title,
        "source": note.source_url,
        "platform": note.source_platform,
        "author": note.author,
        "date": note.date,
        "type": note.note_type,
        "note_id": note.id,
    }
    # Add metadata fields
    fm_fields.update(note.metadata)

    lines = ["---"]
    for k, v in fm_fields.items():
        val = str(v).replace('"', '\\"') if v else ""
        lines.append(f'{k}: "{val}"')
    lines.extend(["---", ""])

    # Title
    lines.extend([f"# {note.title or 'Untitled'}", ""])

    # Content
    if note.content:
        lines.extend([note.content, ""])

    # Embedded media
    if media_refs:
        lines.extend(["## Media", ""])
        for ref in media_refs:
            lines.extend([f"![[{ref}]]", ""])

    # Tags
    if note.tags:
        tag_str = " ".join(f"#{t.replace(' ', '_')}" for t in note.tags)
        lines.extend(["## Tags", "", tag_str, ""])

    # Metadata footer
    lines.extend(["## Metadata", ""])
    if note.author:
        lines.append(f"- Author: {note.author}")
    if note.date:
        lines.append(f"- Date: {note.date}")
    for k, v in note.metadata.items():
        lines.append(f"- {k.replace('_', ' ').title()}: {v}")
    if note.source_url:
        lines.append(f"- [View original]({note.source_url})")
    lines.append("")

    return "\n".join(lines)


def build_vault(
    collection: NoteCollection,
    vault_dir: Path,
    skip_media_manifest: bool = False,
) -> dict:
    """
    Generate a complete Obsidian vault from a NoteCollection.

    Args:
        collection: Notes to include in the vault.
        vault_dir: Output directory for the vault.
        skip_media_manifest: If True, don't generate media manifest.

    Returns:
        dict with 'notes_count', 'tags_count', 'media_manifest' keys.
    """
    notes_dir = vault_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    # Create .obsidian config
    obsidian_dir = vault_dir / ".obsidian"
    obsidian_dir.mkdir(exist_ok=True)
    for cfg_file in ("app.json", "appearance.json"):
        cfg_path = obsidian_dir / cfg_file
        if not cfg_path.exists():
            cfg_path.write_text("{}")

    used_names: set[str] = set()
    media_manifest: list[dict] = []

    for note in collection.notes:
        media_refs = []

        # Queue images
        for idx, img_url in enumerate(note.images):
            ext = "webp"
            for check_ext in ("png", "jpg", "jpeg", "gif", "svg"):
                if f".{check_ext}" in img_url.lower():
                    ext = check_ext
                    break
            fn = f"{note.id}_{idx}.{ext}"
            media_refs.append(f"media/{note.id}/{fn}")
            media_manifest.append({"url": img_url, "path": f"media/{note.id}/{fn}"})

        # Queue videos
        for idx, vid_url in enumerate(note.videos):
            fn = f"{note.id}_video_{idx}.mp4" if idx > 0 else f"{note.id}_video.mp4"
            media_refs.append(f"media/{note.id}/{fn}")
            media_manifest.append({"url": vid_url, "path": f"media/{note.id}/{fn}"})

        # Write markdown
        md = _render_note(note, media_refs)
        safe_title = sanitize_filename(note.title or note.id)
        final_name = safe_title
        if final_name.lower() in used_names:
            final_name = f"{safe_title}_{note.id[:8]}"
        used_names.add(final_name.lower())

        (notes_dir / f"{final_name}.md").write_text(md, encoding="utf-8")

    # Generate index pages
    _generate_index(vault_dir, notes_dir, collection)
    tag_count = _generate_tag_index(vault_dir, collection)

    # Save media manifest
    if not skip_media_manifest and media_manifest:
        manifest_path = vault_dir / "media_manifest.json"
        manifest_path.write_text(json.dumps(media_manifest, indent=2, ensure_ascii=False))

    return {
        "notes_count": collection.count,
        "tags_count": tag_count,
        "media_manifest": media_manifest,
    }


def _generate_index(vault_dir: Path, notes_dir: Path, collection: NoteCollection):
    """Generate the main index.md."""
    note_files = sorted(notes_dir.glob("*.md"))
    source_label = collection.source or "various sources"

    lines = [
        "# Vault Index",
        "",
        f"> {len(note_files)} notes from {source_label}",
        f"> Built with [json2vault](https://github.com/jdh847/json2vault)"
        f" on {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## All Notes",
        "",
    ]
    for nf in note_files:
        lines.append(f"- [[notes/{nf.stem}]]")
    lines.append("")
    (vault_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")


def _generate_tag_index(vault_dir: Path, collection: NoteCollection) -> int:
    """Generate tags.md grouped by tag frequency."""
    tag_map: dict[str, list[str]] = {}
    for note in collection.notes:
        safe = sanitize_filename(note.title or note.id)
        for tag in note.tags:
            tag_map.setdefault(tag, []).append(safe)

    sorted_tags = sorted(tag_map.items(), key=lambda x: -len(x[1]))

    lines = [
        "# Tags Index",
        "",
        f"> {len(sorted_tags)} unique tags across {collection.count} notes",
        "",
    ]
    for tag, note_names in sorted_tags[:200]:
        lines.extend([f"## {tag} ({len(note_names)})", ""])
        for n in note_names[:30]:
            lines.append(f"- [[notes/{n}]]")
        if len(note_names) > 30:
            lines.append(f"- ...and {len(note_names) - 30} more")
        lines.append("")

    (vault_dir / "tags.md").write_text("\n".join(lines), encoding="utf-8")
    return len(sorted_tags)
