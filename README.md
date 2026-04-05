# json2vault

Turn any JSON data into a structured Obsidian vault.

[中文文档](README_zh.md)

```
JSON (any source)  ──>  json2vault  ──>  Obsidian Vault
                                          ├── notes/
                                          ├── index.md
                                          ├── tags.md
                                          └── media_manifest.json
```

## Why

You probably have saved content scattered across many sources — social media exports, API dumps, browser bookmarks, RSS readers. They're all JSON, but in wildly different formats. json2vault converts them all into an Obsidian vault you can open immediately, complete with YAML frontmatter, tag indexes, and media references.

**Zero dependencies** — pure Python standard library. Just `pip install` and go.

## Quick Start

```bash
pip install json2vault
```

```bash
# Auto-detect format and build vault
json2vault build -i my_data.json -o ./my-vault

# Open in Obsidian → "Open folder as vault" → select my-vault/
```

That's it.

## Supported Formats

| Adapter | Source | Auto-detect |
|---------|--------|-------------|
| `xhs` | Xiaohongshu (小红书 / RedNote) favorites | Yes |
| `twitter` | Twitter/X data archive | Yes |
| `weibo` | Weibo (微博) posts/favorites | Yes |
| `pocket` | Pocket reading list | Yes |
| `generic` | Any JSON with title/content fields | Yes |
| `universal` | json2vault's own format | Yes |

json2vault auto-detects the JSON format and picks the right adapter. You can also specify one manually:

```bash
json2vault build -i data.json -o ./vault --adapter xhs
```

### Custom Formats

If your JSON has common field names like `title`, `content`, `date`, `tags`, `url`, the `generic` adapter handles it automatically. No code needed.

For completely custom field names, convert to json2vault's universal format first:

```json
{
  "json2vault_version": "1",
  "notes": [
    {
      "id": "1",
      "title": "My Note",
      "content": "Note content here",
      "tags": ["tag1", "tag2"],
      "date": "2024-01-15",
      "source_url": "https://example.com"
    }
  ]
}
```

## CLI Commands

```bash
# Build vault from JSON
json2vault build -i data.json -o ./vault

# Preview format detection (no files generated)
json2vault check -i data.json

# List all available adapters
json2vault adapters

# Scaffold a Karpathy-style knowledge base
json2vault init-kb -o ./my-knowledge-base
```

## Output Structure

```
my-vault/
├── .obsidian/       # Vault config (auto-created)
├── index.md         # Master index of all notes
├── tags.md          # Tag index (sorted by frequency)
├── notes/
│   ├── Note Title.md
│   └── ...
└── media_manifest.json  # URL → local path mapping for media download
```

Each markdown note includes YAML frontmatter (title, author, date, source, tags, custom metadata), full content, media references (`![[media/...]]`), and a metadata footer.

## Knowledge Base

json2vault can also scaffold a [Karpathy-style LLM knowledge base](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f):

```bash
json2vault init-kb -o ./my-kb
```

This creates:

```
my-kb/
├── raw/         # Immutable source materials
├── wiki/        # LLM-maintained knowledge wiki
│   ├── entities/
│   ├── concepts/
│   ├── comparisons/
│   └── synthesis/
├── schema/      # LLM behavior rules
└── logs/        # Operation audit trail
```

Workflow: convert JSON to vault with `json2vault build` → drop into `raw/` → have an LLM ingest (read sources, update wiki pages) → query the wiki → lint for health checks.

## Design Philosophy

- **Zero dependencies** — pure Python standard library, no third-party packages
- **Adapter pattern** — one adapter per data source, isolated and easy to extend
- **No network access** — json2vault only does local format conversion, never makes network requests
- **Media manifest** — generates `media_manifest.json` (URL → local path mapping), leaves downloading to the user

## Requirements

- Python 3.10+
- No third-party dependencies

## License

MIT
