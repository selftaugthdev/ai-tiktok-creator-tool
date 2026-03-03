#!/usr/bin/env python3
"""TikTok Carousel Generator — CLI entry point."""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from carousel_renderer import render_carousel
from script_gen import generate_carousel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate TikTok-style image carousels using AI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --app "MigraineCast" --topic "weather triggers for migraines" --count 3
  python main.py --app "FitTrack" --topic "morning routines" --count 1 --slides 5
  python main.py --app "MigraineCast" --topic "barometric pressure" --count 2 --illustration ./assets/brain_character.png
""",
    )
    parser.add_argument("--app", required=True, help="Name of the app being promoted.")
    parser.add_argument("--topic", required=True, help="Topic or theme for the carousels.")
    parser.add_argument("--count", required=True, type=int, help="Number of carousels to generate.")
    parser.add_argument(
        "--slides",
        type=int,
        default=7,
        help="Number of slides per carousel (default: 7; minimum: 3).",
    )
    parser.add_argument(
        "--illustration",
        default=None,
        help="Path to a PNG file to composite onto slides (overridden by chart_data when present).",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.count < 1:
        sys.exit("Error: --count must be at least 1.")
    if args.slides < 3:
        sys.exit("Error: --slides must be at least 3 (1 hook + 1 value + 1 CTA).")


def main() -> None:
    load_dotenv()

    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit(
            "Error: ANTHROPIC_API_KEY is not set.\n"
            "Create a .env file with ANTHROPIC_API_KEY=your-key-here."
        )

    args = parse_args()
    validate_args(args)

    app_slug = args.app.replace(" ", "_")
    output_base = Path("output") / "carousels" / app_slug

    # Find the next carousel number so existing ones are never overwritten
    existing = [
        int(p.name.split("_")[1])
        for p in output_base.glob("carousel_*")
        if p.is_dir() and p.name.split("_")[1].isdigit()
    ] if output_base.exists() else []
    next_num = max(existing, default=0) + 1

    print(f"\nGenerating {args.count} carousel(s) — {args.slides} slides each")
    print(f"App: {args.app!r}  |  Topic: {args.topic!r}\n")

    for i in range(args.count):
        carousel_num = next_num + i
        print(f"[{i + 1}/{args.count}] Fetching content from Claude...")

        try:
            slides = generate_carousel(args.app, args.topic, args.slides)
        except Exception as exc:
            print(f"  Error generating content: {exc}", file=sys.stderr)
            continue

        carousel_dir = output_base / f"carousel_{carousel_num}"
        print(f"[{i}/{args.count}] Rendering slides → {carousel_dir}/")

        try:
            illustration = Path(args.illustration) if args.illustration else None
            render_carousel(slides, carousel_dir, args.app, args.slides, illustration_path=illustration)
        except Exception as exc:
            print(f"  Error rendering slides: {exc}", file=sys.stderr)
            continue

    print(f"\nDone! Carousels saved to {output_base}/")


if __name__ == "__main__":
    main()
