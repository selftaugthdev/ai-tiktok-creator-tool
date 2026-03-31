#!/usr/bin/env python3
"""MigraineCast Photo-Overlay Carousel Generator."""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from photo_renderer import render_photo_carousel
from photo_script_gen import generate_photo_carousel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate photo-overlay TikTok carousels for MigraineCast.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 photo_main.py --app "MigraineCast" --topic "weather triggers for migraines" --slides 5
  python3 photo_main.py --app "MigraineCast" --topic "migraine phases" --count 2 --slides 6
""",
    )
    parser.add_argument("--app", required=True, help="App name.")
    parser.add_argument("--topic", required=True, help="Content topic.")
    parser.add_argument("--count", type=int, default=1, help="Number of carousels (default: 1).")
    parser.add_argument("--slides", type=int, default=5, help="Slides per carousel (default: 5, min: 3).")
    return parser.parse_args()


def main() -> None:
    load_dotenv()

    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit(
            "Error: ANTHROPIC_API_KEY is not set.\n"
            "Create a .env file with ANTHROPIC_API_KEY=your-key-here."
        )

    args = parse_args()

    if args.slides < 3:
        sys.exit("Error: --slides must be at least 3 (1 hook + 1 value + 1 CTA).")

    app_slug = args.app.replace(" ", "_")
    topic_slug = args.topic.lower().replace(" ", "-")
    output_base = Path("output") / "to-upload" / app_slug / "photo"

    # Find next carousel number (never overwrite existing)
    existing = []
    for search_base in [output_base, Path("output") / "uploaded" / app_slug]:
        if search_base.exists():
            for p in search_base.rglob("carousel_*"):
                if p.is_dir():
                    parts = p.name.split("_")
                    if len(parts) > 1 and parts[1].isdigit():
                        existing.append(int(parts[1]))
    next_num = max(existing, default=0) + 1

    print(f"\nGenerating {args.count} photo carousel(s) — {args.slides} slides each")
    print(f"App: {args.app!r}  |  Topic: {args.topic!r}\n")

    for i in range(args.count):
        carousel_num = next_num + i
        print(f"[{i + 1}/{args.count}] Fetching content + photo selections from Claude...")

        try:
            slides = generate_photo_carousel(args.app, args.topic, args.slides)
        except Exception as exc:
            print(f"  Error generating content: {exc}", file=sys.stderr)
            continue

        carousel_dir = output_base / f"carousel_{carousel_num}_{topic_slug}"
        print(f"[{i + 1}/{args.count}] Rendering slides → {carousel_dir}/")

        try:
            render_photo_carousel(slides, carousel_dir, args.app, topic=args.topic)
        except Exception as exc:
            print(f"  Error rendering slides: {exc}", file=sys.stderr)
            continue

    print(f"\nDone! Carousels saved to {output_base}/")


if __name__ == "__main__":
    main()
