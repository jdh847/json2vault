"""
CLI entry point for json2vault.

Usage:
    # Auto-detect format and build vault
    json2vault build -i data.json -o ./my-vault

    # Specify adapter explicitly
    json2vault build -i favorites.json -o ./vault --adapter xhs

    # List available adapters
    json2vault adapters

    # Validate JSON without building
    json2vault check -i data.json

    # Scaffold a Karpathy-style knowledge base
    json2vault init-kb -o ./my-knowledge-base
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from . import __version__
from .adapters import get_adapter, list_adapters, detect_adapter
from .vault import build_vault

logger = logging.getLogger("json2vault")


def main():
    parser = argparse.ArgumentParser(
        prog="json2vault",
        description="Turn any JSON data into a structured Obsidian vault.",
    )
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")

    subparsers = parser.add_subparsers(dest="command")

    # === build ===
    p_build = subparsers.add_parser("build", help="Build Obsidian vault from JSON")
    p_build.add_argument("-i", "--input", required=True, help="Input JSON file")
    p_build.add_argument("-o", "--output", default="./vault", help="Output vault directory")
    p_build.add_argument(
        "-a", "--adapter", default="auto",
        help="Adapter name (auto, xhs, twitter, pocket, weibo, generic, universal)",
    )
    p_build.add_argument("--skip-media", action="store_true", help="Skip media manifest")

    # === check ===
    p_check = subparsers.add_parser("check", help="Validate JSON and show detected format")
    p_check.add_argument("-i", "--input", required=True, help="Input JSON file")
    p_check.add_argument("-a", "--adapter", default="auto", help="Adapter to test")

    # === adapters ===
    subparsers.add_parser("adapters", help="List available adapters")

    # === init-kb ===
    p_kb = subparsers.add_parser("init-kb", help="Scaffold a Karpathy-style knowledge base")
    p_kb.add_argument("-o", "--output", default="./knowledge-base", help="Output directory")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "build":
        _cmd_build(args)
    elif args.command == "check":
        _cmd_check(args)
    elif args.command == "adapters":
        _cmd_adapters()
    elif args.command == "init-kb":
        _cmd_init_kb(args)


def _load_json(path: Path) -> dict:
    """Load and parse a JSON file."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {path}: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File not found: {path}")
        sys.exit(1)


def _resolve_adapter(data: dict, adapter_name: str):
    """Resolve adapter — auto-detect if needed."""
    if adapter_name == "auto":
        detected = detect_adapter(data)
        if not detected:
            print("Could not auto-detect format. Use --adapter to specify.")
            print(f"Available adapters: {', '.join(list_adapters())}")
            sys.exit(1)
        print(f"  Detected format: {detected}")
        return get_adapter(detected), detected
    return get_adapter(adapter_name), adapter_name


def _cmd_build(args):
    """Build vault from JSON."""
    input_path = Path(args.input)
    vault_dir = Path(args.output)

    print(f"Loading {input_path}...")
    data = _load_json(input_path)

    adapter_fn, adapter_name = _resolve_adapter(data, args.adapter)

    print(f"Adapting with '{adapter_name}' adapter...")
    collection = adapter_fn(data)
    print(f"  {collection.count} notes loaded")

    if collection.count == 0:
        print("No notes found. Check your JSON format or try a different --adapter.")
        sys.exit(1)

    # Show tag summary
    tags = collection.all_tags()
    if tags:
        top_tags = list(tags.items())[:5]
        tag_str = ", ".join(f"{t} ({c})" for t, c in top_tags)
        print(f"  Top tags: {tag_str}")

    print(f"\nBuilding vault at {vault_dir}...")
    result = build_vault(collection, vault_dir, skip_media_manifest=args.skip_media)

    print(f"\nDone!")
    print(f"  Notes: {result['notes_count']}")
    print(f"  Tags: {result['tags_count']}")
    if result["media_manifest"]:
        print(f"  Media files queued: {len(result['media_manifest'])}")
        print(f"  Media manifest: {vault_dir / 'media_manifest.json'}")
    print(f"\nOpen '{vault_dir}' as a vault in Obsidian.")


def _cmd_check(args):
    """Validate JSON and preview what would be generated."""
    input_path = Path(args.input)

    print(f"Checking {input_path}...")
    data = _load_json(input_path)

    adapter_fn, adapter_name = _resolve_adapter(data, args.adapter)

    print(f"\nParsing with '{adapter_name}' adapter...")
    collection = adapter_fn(data)

    print(f"\nResult:")
    print(f"  Notes: {collection.count}")
    print(f"  Source: {collection.source or '(unknown)'}")

    if collection.count > 0:
        # Show sample
        sample = collection.notes[0]
        print(f"\nFirst note preview:")
        print(f"  Title: {sample.title}")
        print(f"  Author: {sample.author or '(none)'}")
        print(f"  Date: {sample.date or '(none)'}")
        print(f"  Content: {sample.content[:100]}..." if len(sample.content) > 100 else f"  Content: {sample.content}")
        print(f"  Tags: {', '.join(sample.tags) if sample.tags else '(none)'}")
        print(f"  Images: {len(sample.images)}")
        print(f"  Videos: {len(sample.videos)}")

    # Tags summary
    tags = collection.all_tags()
    if tags:
        print(f"\nTop 10 tags:")
        for tag, count in list(tags.items())[:10]:
            print(f"  {tag}: {count}")

    print(f"\nLooks good! Run 'json2vault build -i {input_path}' to generate the vault.")


def _cmd_adapters():
    """List all available adapters."""
    print("Available adapters:\n")
    descriptions = {
        "generic": "Any JSON with title/content fields (fallback)",
        "pocket": "Pocket reading list export",
        "twitter": "Twitter/X data archive (tweets.json)",
        "universal": "json2vault's own format",
        "weibo": "Weibo (微博) posts/favorites export",
        "xhs": "Xiaohongshu (小红书/RedNote) favorites",
    }
    for name in list_adapters():
        desc = descriptions.get(name, "")
        print(f"  {name:12s}  {desc}")
    print(f"\nUse --adapter <name> with 'build' or 'check' commands.")
    print(f"Use --adapter auto (default) to auto-detect format.")


def _cmd_init_kb(args):
    """Scaffold a Karpathy-style knowledge base."""
    kb_dir = Path(args.output)

    if kb_dir.exists() and any(kb_dir.iterdir()):
        print(f"Directory {kb_dir} already exists and is not empty.")
        print("Use an empty directory or a new path.")
        sys.exit(1)

    print(f"Creating knowledge base at {kb_dir}...")

    # Create directory structure
    for subdir in [
        "raw",
        "wiki/entities",
        "wiki/concepts",
        "wiki/comparisons",
        "wiki/synthesis",
        "schema",
        "logs",
    ]:
        (kb_dir / subdir).mkdir(parents=True, exist_ok=True)

    # README
    (kb_dir / "README.md").write_text(
        "# Knowledge Base\n\n"
        "A personal knowledge management system based on "
        "[Karpathy's LLM Knowledge Base pattern]"
        "(https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).\n\n"
        "## Structure\n\n"
        "- `raw/` — Immutable source materials. Drop JSON, articles, PDFs here.\n"
        "- `wiki/` — LLM-maintained knowledge wiki (entities, concepts, comparisons, synthesis)\n"
        "- `schema/` — Configuration and rules for the LLM\n"
        "- `logs/` — Operation audit trail\n\n"
        "## Workflow\n\n"
        "1. Drop source data into `raw/`\n"
        "2. Ask an LLM to **ingest** — it reads sources and updates 10-15 wiki pages\n"
        "3. Ask the LLM to **query** — it searches the wiki and synthesizes answers\n"
        "4. Periodically ask the LLM to **lint** — it finds contradictions and gaps\n\n"
        "Built with [json2vault](https://github.com/jdh847/json2vault).\n",
        encoding="utf-8",
    )

    # Schema
    (kb_dir / "schema" / "CLAUDE.md").write_text(
        "# Wiki Schema\n\n"
        "## Rules\n\n"
        "- raw/ is **immutable** — read but never modify source materials\n"
        "- wiki/ is **LLM-owned** — the agent handles all creation and updates\n"
        "- Every wiki page must have `## Sources` and `## Related` sections\n"
        "- Separate facts from inferences (use `> [!NOTE]` callouts for inferences)\n"
        "- Use lowercase kebab-case filenames: `topic-name.md`\n"
        "- Prefix comparisons with `vs-`, synthesis with `syn-`\n\n"
        "## Operations\n\n"
        "### Ingest\n"
        "Read new source from raw/, update 10-15 wiki pages, add cross-references, "
        "update wiki/index.md, log in logs/log.md.\n\n"
        "### Query\n"
        "Search wiki pages, synthesize answer with citations. "
        "Optionally create new wiki page for substantial analyses.\n\n"
        "### Lint\n"
        "Find contradictions, orphaned pages, missing cross-references, "
        "data gaps, stale claims.\n",
        encoding="utf-8",
    )

    # Wiki index
    (kb_dir / "wiki" / "index.md").write_text(
        "# Wiki Index\n\n"
        "> Updated on every ingest operation.\n\n"
        "## Entities\n\n_No entity pages yet._\n\n"
        "## Concepts\n\n_No concept pages yet._\n\n"
        "## Comparisons\n\n_No comparison pages yet._\n\n"
        "## Synthesis\n\n_No synthesis pages yet._\n",
        encoding="utf-8",
    )

    # Log
    (kb_dir / "logs" / "log.md").write_text(
        "# Operation Log\n\n"
        f"> Knowledge base created on {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        encoding="utf-8",
    )

    # Raw readme
    (kb_dir / "raw" / "README.md").write_text(
        "# Raw Sources\n\n"
        "Drop your source materials here (JSON, markdown, text files, etc.).\n"
        "These files are **immutable** — the LLM reads but never modifies them.\n\n"
        "Tip: Use `json2vault build` to convert JSON exports into an Obsidian vault,\n"
        "then copy the vault into this knowledge base for ingestion.\n",
        encoding="utf-8",
    )

    print(f"\nDone! Knowledge base scaffolded at {kb_dir}")
    print(f"\nNext steps:")
    print(f"  1. Drop source data into {kb_dir}/raw/")
    print(f"  2. Use an LLM to ingest: 'read raw/ and update wiki pages'")
    print(f"  3. Query: ask questions and the LLM searches wiki/ for answers")


if __name__ == "__main__":
    main()
