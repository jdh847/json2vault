"""
json2vault: Turn any JSON data into a structured Obsidian vault.

Feed it JSON from any source — social media exports, API dumps,
scraped data, bookmarks — and get a fully indexed Obsidian vault
with YAML frontmatter, embedded media references, and tag indexes.

Pipeline:
  1. Load JSON data
  2. Adapt to universal schema (via built-in or custom adapters)
  3. Generate Obsidian-compatible markdown vault
  4. Optionally scaffold a Karpathy-style knowledge base
"""

__version__ = "0.1.0"
