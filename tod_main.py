#!/usr/bin/env python3
"""Truth or Dare AI — TikTok Carousel Generator CLI."""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from tod_renderer import render_tod_carousel
from tod_script_gen import FORMATS, generate_tod_carousel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Truth or Dare AI TikTok carousels.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 tod_main.py --format unhinged-ai --audience "college students" --vibe "chaotic friday night"
  python3 tod_main.py --format bachelorette --audience "bridesmaids" --vibe "classy but chaotic" --count 2
""",
    )
    parser.add_argument("--format", required=True, choices=FORMATS, help="Carousel format.")
    parser.add_argument("--audience", required=True, help="Target audience description.")
    parser.add_argument("--vibe", required=True, help="Vibe or energy of the carousel.")
    parser.add_argument("--count", type=int, default=1, help="Number of carousels to generate (default: 1).")
    return parser.parse_args()


def main() -> None:
    load_dotenv()

    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit(
            "Error: ANTHROPIC_API_KEY is not set.\n"
            "Create a .env file with ANTHROPIC_API_KEY=your-key-here."
        )

    args = parse_args()

    app_slug = "Truth_or_Dare_AI"
    output_base = Path("output") / "to-upload" / app_slug

    # Find the next carousel number so existing ones are never overwritten
    existing = []
    for search_base in [output_base, Path("output") / "uploaded" / app_slug]:
        if search_base.exists():
            for p in search_base.rglob("carousel_*"):
                if p.is_dir():
                    parts = p.name.split("_")
                    if len(parts) > 1 and parts[1].isdigit():
                        existing.append(int(parts[1]))
    next_num = max(existing, default=0) + 1

    format_slug = args.format

    print(f"\nGenerating {args.count} Truth or Dare AI carousel(s)")
    print(f"Format: {args.format}  |  Audience: {args.audience}  |  Vibe: {args.vibe}\n")

    for i in range(args.count):
        carousel_num = next_num + i
        print(f"[{i + 1}/{args.count}] Fetching content from Claude...")

        try:
            data = generate_tod_carousel(args.format, args.audience, args.vibe)
        except Exception as exc:
            print(f"  Error generating content: {exc}", file=sys.stderr)
            continue

        carousel_dir = output_base / f"carousel_{carousel_num}_{format_slug}"
        print(f"[{i + 1}/{args.count}] Rendering slides → {carousel_dir}/")

        try:
            render_tod_carousel(data, carousel_dir)
        except Exception as exc:
            print(f"  Error rendering slides: {exc}", file=sys.stderr)
            continue

    print(f"\nDone! Carousels saved to {output_base}/")


if __name__ == "__main__":
    main()
