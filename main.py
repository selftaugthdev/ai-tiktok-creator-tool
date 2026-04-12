#!/usr/bin/env python3
"""TikTok Carousel Generator — CLI entry point."""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from carousel_renderer import render_carousel
from script_gen import generate_caption, generate_carousel


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
    parser.add_argument(
        "--style",
        choices=["regular", "infographic"],
        default="regular",
        help="Slide style: 'regular' (default) or 'infographic' (emoji grid for value slides).",
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
    topic_slug = args.topic.lower().replace(" ", "-")
    style_folder = "infographic" if args.style == "infographic" else "regular"
    output_base = Path("output") / "to-upload" / app_slug / style_folder

    # Find the next carousel number so existing ones are never overwritten.
    # Search all style subfolders under to-upload and uploaded to avoid collisions.
    def _existing_nums(app_folder: Path):
        if not app_folder.exists():
            return []
        nums = []
        for p in app_folder.rglob("carousel_*"):
            if p.is_dir():
                parts = p.name.split("_")
                if len(parts) > 1 and parts[1].isdigit():
                    nums.append(int(parts[1]))
        return nums

    uploaded_base = Path("output") / "uploaded" / app_slug
    existing = _existing_nums(Path("output") / "to-upload" / app_slug) + _existing_nums(uploaded_base)
    next_num = max(existing, default=0) + 1

    print(f"\nGenerating {args.count} carousel(s) — {args.slides} slides each  [{args.style}]")
    print(f"App: {args.app!r}  |  Topic: {args.topic!r}\n")

    for i in range(args.count):
        carousel_num = next_num + i
        print(f"[{i + 1}/{args.count}] Fetching content from Claude...")

        try:
            slides = generate_carousel(args.app, args.topic, args.slides, style=args.style)
        except Exception as exc:
            print(f"  Error generating content: {exc}", file=sys.stderr)
            continue

        # Inject app screenshot slides before the CTA (last slide)
        screenshot_slides = [
            {"screenshot_path": str(Path("assets") / "MigraineCast Showing Home Page.jpg"), "mascot_expression": "default"},
        ]
        slides = slides[:-1] + screenshot_slides + slides[-1:]
        total_slides = len(slides)

        carousel_dir = output_base / f"carousel_{carousel_num}_{topic_slug}"
        print(f"[{i}/{args.count}] Rendering slides → {carousel_dir}/")

        try:
            illustration = Path(args.illustration) if args.illustration else None
            render_carousel(slides, carousel_dir, args.app, total_slides, illustration_path=illustration)
        except Exception as exc:
            print(f"  Error rendering slides: {exc}", file=sys.stderr)
            continue

        print(f"[{i + 1}/{args.count}] Generating caption...")
        try:
            caption = generate_caption(args.app, args.topic)
            caption_path = carousel_dir / "caption.txt"
            caption_path.write_text(caption, encoding="utf-8")
            print(f"    caption.txt → {caption_path}")
        except Exception as exc:
            print(f"  Warning: could not generate caption: {exc}", file=sys.stderr)

    print(f"\nDone! Carousels saved to {output_base}/")


if __name__ == "__main__":
    main()
