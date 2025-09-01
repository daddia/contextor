#!/usr/bin/env python3
"""Standalone token counting script for .mdc files.

This script provides accurate token counting using tiktoken when available,
with fallback to word-based estimation.
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any


def count_tokens_tiktoken(text: str, encoding_name: str = "cl100k_base") -> int | None:
    """Count tokens using tiktoken (if available)."""
    try:
        import tiktoken

        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(text)
        return len(tokens)
    except ImportError:
        return None


def estimate_tokens_from_words(text: str) -> int:
    """Estimate token count from word count using the 4/3 ratio."""
    words = len(text.split())
    return int(words * 4 / 3)  # 1 token ≈ 3/4 words


def estimate_tokens_from_chars(text: str) -> int:
    """Estimate token count from character count using the 1/4 ratio."""
    return len(text) // 4  # 1 token ≈ 4 characters


def get_content_stats(text: str) -> dict[str, Any]:
    """Get comprehensive content statistics."""
    lines = text.splitlines()
    words = text.split()
    chars = len(text)
    chars_no_spaces = len(text.replace(" ", ""))

    # Count different types of content
    code_blocks = len(re.findall(r"```[\s\S]*?```", text))
    inline_code = len(re.findall(r"`[^`]+`", text))
    links = len(re.findall(r"\[([^\]]+)\]\([^\)]+\)", text))
    headings = len(re.findall(r"^#+\s", text, re.MULTILINE))

    # Try tiktoken first, fall back to estimation
    tokens_tiktoken = count_tokens_tiktoken(text)
    tokens_estimated_words = estimate_tokens_from_words(text)
    tokens_estimated_chars = estimate_tokens_from_chars(text)

    return {
        "lines": len(lines),
        "words": len(words),
        "characters": chars,
        "characters_no_spaces": chars_no_spaces,
        "tokens": tokens_tiktoken
        if tokens_tiktoken is not None
        else tokens_estimated_words,
        "tokens_tiktoken": tokens_tiktoken,
        "tokens_estimated_words": tokens_estimated_words,
        "tokens_estimated_chars": tokens_estimated_chars,
        "code_blocks": code_blocks,
        "inline_code": inline_code,
        "links": links,
        "headings": headings,
        "avg_words_per_line": len(words) / max(1, len(lines)),
        "avg_chars_per_word": chars / max(1, len(words)),
    }


def format_number(num: int) -> str:
    """Format large numbers with commas."""
    return f"{num:,}"


def format_size(size_bytes: int) -> str:
    """Format byte size in human-readable format."""
    size_float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size_float < 1024:
            return f"{size_float:.1f} {unit}"
        size_float /= 1024
    return f"{size_float:.1f} TB"


def main() -> int:
    parser = argparse.ArgumentParser(description="Count tokens in .mdc files")
    parser.add_argument("directory", help="Directory containing .mdc files")
    parser.add_argument("--detailed", action="store_true", help="Show per-file details")
    parser.add_argument("--output", help="Save results to JSON file")
    parser.add_argument(
        "--encoding", default="cl100k_base", help="Tiktoken encoding to use"
    )

    args = parser.parse_args()

    source_path = Path(args.directory)
    if not source_path.exists() or not source_path.is_dir():
        print(f"Error: {args.directory} is not a valid directory")
        return 1

    # Find all .mdc files
    mdc_files = list(source_path.rglob("*.mdc"))
    if not mdc_files:
        print(f"No .mdc files found in {args.directory}")
        return 1

    print(f"Analyzing {len(mdc_files)} .mdc files...")

    # Check if tiktoken is available
    tiktoken_available = count_tokens_tiktoken("test") is not None
    if tiktoken_available:
        print("✅ Using tiktoken for precise token counting")
    else:
        print("⚠️  tiktoken not available, using word-based estimation")
        print("   Install with: pip install tiktoken")

    total_stats = {
        "files": 0,
        "lines": 0,
        "words": 0,
        "characters": 0,
        "tokens": 0,
        "tokens_tiktoken": 0,
        "tokens_estimated_words": 0,
        "tokens_estimated_chars": 0,
        "code_blocks": 0,
        "inline_code": 0,
        "links": 0,
        "headings": 0,
        "size_bytes": 0,
    }

    file_stats = []

    for file_path in mdc_files:
        try:
            content = file_path.read_text(encoding="utf-8")
            stats = get_content_stats(content)

            # Add file info
            stats["file"] = str(file_path.relative_to(source_path))
            stats["size_bytes"] = file_path.stat().st_size

            # Accumulate totals
            total_stats["files"] += 1
            for key in [
                "lines",
                "words",
                "characters",
                "tokens",
                "tokens_estimated_words",
                "tokens_estimated_chars",
                "code_blocks",
                "inline_code",
                "links",
                "headings",
                "size_bytes",
            ]:
                if key in stats and stats[key] is not None:
                    total_stats[key] += stats[key]

            if stats.get("tokens_tiktoken") is not None:
                total_stats["tokens_tiktoken"] += stats["tokens_tiktoken"]

            if args.detailed:
                file_stats.append(stats)

        except Exception as e:
            print(f"Warning: Failed to analyze {file_path}: {e}")

    # Calculate averages
    if total_stats["files"] > 0:
        avg_stats = {
            "tokens_per_file": total_stats["tokens"] / total_stats["files"],
            "words_per_file": total_stats["words"] / total_stats["files"],
            "lines_per_file": total_stats["lines"] / total_stats["files"],
            "chars_per_file": total_stats["characters"] / total_stats["files"],
            "size_per_file": total_stats["size_bytes"] / total_stats["files"],
        }
    else:
        avg_stats = {}

    # Display results
    print("\n" + "=" * 60)
    print("TOKEN ANALYSIS SUMMARY")
    print("=" * 60)

    print(f"Files analyzed: {format_number(total_stats['files'])}")
    print(f"Total size: {format_size(total_stats['size_bytes'])}")
    print(f"Total lines: {format_number(total_stats['lines'])}")
    print(f"Total words: {format_number(total_stats['words'])}")
    print(f"Total characters: {format_number(total_stats['characters'])}")
    print()

    if tiktoken_available and total_stats["tokens_tiktoken"] > 0:
        print(
            f"🎯 TOTAL TOKENS (tiktoken): {format_number(total_stats['tokens_tiktoken'])}"
        )
        print(
            f"   Est. from words: {format_number(total_stats['tokens_estimated_words'])}"
        )
        print(
            f"   Est. from chars: {format_number(total_stats['tokens_estimated_chars'])}"
        )

        # Show accuracy comparison
        word_accuracy = (
            total_stats["tokens_estimated_words"] / total_stats["tokens_tiktoken"]
        ) * 100
        char_accuracy = (
            total_stats["tokens_estimated_chars"] / total_stats["tokens_tiktoken"]
        ) * 100
        print(f"   Word estimation accuracy: {word_accuracy:.1f}%")
        print(f"   Char estimation accuracy: {char_accuracy:.1f}%")
    else:
        print(f"🎯 TOTAL TOKENS (estimated): {format_number(total_stats['tokens'])}")
        print(
            f"   Est. from words: {format_number(total_stats['tokens_estimated_words'])}"
        )
        print(
            f"   Est. from chars: {format_number(total_stats['tokens_estimated_chars'])}"
        )

    print()
    print("Content breakdown:")
    print(f"  Code blocks: {format_number(total_stats['code_blocks'])}")
    print(f"  Inline code: {format_number(total_stats['inline_code'])}")
    print(f"  Links: {format_number(total_stats['links'])}")
    print(f"  Headings: {format_number(total_stats['headings'])}")

    if avg_stats:
        print()
        print("Averages per file:")
        print(f"  Tokens: {avg_stats['tokens_per_file']:.1f}")
        print(f"  Words: {avg_stats['words_per_file']:.1f}")
        print(f"  Lines: {avg_stats['lines_per_file']:.1f}")
        print(f"  Size: {format_size(int(avg_stats['size_per_file']))}")

    if args.detailed:
        print("\n" + "-" * 60)
        print("DETAILED FILE STATISTICS")
        print("-" * 60)

        # Sort by token count descending
        file_stats.sort(key=lambda x: x.get("tokens", 0) or 0, reverse=True)

        for stats in file_stats[:10]:  # Show top 10
            tokens = stats.get("tokens") or 0
            words = stats.get("words", 0)
            lines = stats.get("lines", 0)
            size_bytes = stats.get("size_bytes", 0)

            print(f"\n📄 {stats['file']}")
            print(
                f"   Tokens: {format_number(tokens)} | "
                f"Words: {format_number(words)} | "
                f"Lines: {format_number(lines)} | "
                f"Size: {format_size(size_bytes)}"
            )

        if len(file_stats) > 10:
            print(f"\n... and {len(file_stats) - 10} more files")

    # Save results if requested
    if args.output:
        results = {
            "summary": total_stats,
            "averages": avg_stats,
            "tiktoken_available": tiktoken_available,
            "encoding": args.encoding if tiktoken_available else None,
        }

        if args.detailed:
            results["files"] = file_stats

        output_path = Path(args.output)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to: {args.output}")
        except Exception as e:
            print(f"Error saving results: {e}")
            return 1

    return 0


if __name__ == "__main__":
    exit(main())
