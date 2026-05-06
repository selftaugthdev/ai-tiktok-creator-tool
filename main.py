#!/usr/bin/env python3
"""TikTok Carousel Generator — CLI entry point."""

import argparse
import json
import os
import random
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

import carousel_renderer
import pexels as pexels_mod
from carousel_renderer import render_carousel
from photo_renderer import configure_platform as photo_configure_platform, render_sandra_carousel
from photo_script_gen import generate_sandra_carousel
from platforms import PLATFORMS
from script_gen import generate_caption, generate_carousel, generate_hook_variants


_HOOKS_FILE = Path("assets") / "migrainecast_50_hooks.md"
_HOOKS_USED_FILE = Path("assets") / "migrainecast_hooks_used.json"
_HOOKS_WARN_THRESHOLD = 10


def _parse_hooks() -> list:
    if not _HOOKS_FILE.exists():
        sys.exit(f"Error: hooks file not found at {_HOOKS_FILE}")
    text = _HOOKS_FILE.read_text(encoding="utf-8")
    hooks = []
    current_parts: list = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r'^\d+\.', stripped):
            if current_parts:
                hooks.append(" ".join(current_parts))
                current_parts = []
            hook_text = re.sub(r'^\d+\.\s*', '', stripped)
            if hook_text:
                current_parts = [hook_text]
        elif current_parts and stripped:
            if not stripped.startswith(('#', '---', '(')):
                current_parts.append(stripped)
        elif not stripped and current_parts:
            hooks.append(" ".join(current_parts))
            current_parts = []
    if current_parts:
        hooks.append(" ".join(current_parts))
    return hooks


def _load_used() -> set:
    if not _HOOKS_USED_FILE.exists():
        return set()
    data = json.loads(_HOOKS_USED_FILE.read_text(encoding="utf-8"))
    return set(data.get("used", []))


def _save_used(used: set) -> None:
    _HOOKS_USED_FILE.write_text(
        json.dumps({"used": sorted(used)}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_random_hook() -> str:
    hooks = _parse_hooks()
    if not hooks:
        sys.exit(f"Error: no hooks found in {_HOOKS_FILE}")

    used = _load_used()
    available = [h for h in hooks if h not in used]

    if not available:
        sys.exit(
            f"All {len(hooks)} hooks have been used.\n"
            f"Add new hooks to {_HOOKS_FILE} to continue."
        )

    chosen = random.choice(available)
    used.add(chosen)
    _save_used(used)

    remaining = len(available) - 1
    if remaining <= _HOOKS_WARN_THRESHOLD:
        print(
            f"WARNING: only {remaining} hook(s) left unused. "
            f"Add more hooks to {_HOOKS_FILE} soon.\n"
        )

    return chosen


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
    parser.add_argument("--topic", default=None, help="Topic or theme for the carousels.")
    parser.add_argument("--auto", action="store_true", help="Pick a random hook from assets/migrainecast_50_hooks.md.")
    parser.add_argument(
        "--variants",
        type=int,
        default=None,
        metavar="N",
        help="Number of carousel variants per hook (default: 3 with --auto, 1 with --topic).",
    )
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
        choices=["regular", "infographic", "hybrid", "sandra"],
        default="regular",
        help="Slide style: 'regular' (default), 'infographic' (emoji grid), 'hybrid', or 'sandra' (avatar + Pexels photos).",
    )
    parser.add_argument(
        "--platform",
        choices=["tiktok", "instagram"],
        default="tiktok",
        help="Target platform: 'tiktok' (1080×1920, default) or 'instagram' (1080×1350).",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.count < 1:
        sys.exit("Error: --count must be at least 1.")
    if args.style == "sandra":
        if args.slides < 4:
            sys.exit("Error: --slides must be at least 4 for sandra style (hook + 1 value + app showcase + CTA).")
    elif args.slides < 3:
        sys.exit("Error: --slides must be at least 3 (1 hook + 1 value + 1 CTA).")


def main() -> None:
    load_dotenv()

    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit(
            "Error: ANTHROPIC_API_KEY is not set.\n"
            "Create a .env file with ANTHROPIC_API_KEY=your-key-here."
        )

    args = parse_args()

    if not args.auto and args.topic is None:
        sys.exit("Error: --topic is required unless --auto is used.")

    # Resolve effective variant count: 3 by default with --auto, 1 with manual --topic
    n_variants = args.variants if args.variants is not None else (3 if args.auto else 1)
    if n_variants < 1:
        sys.exit("Error: --variants must be at least 1.")

    validate_args(args)

    platform_cfg = PLATFORMS[args.platform]

    from app_config import get_app_config
    app_cfg = get_app_config(args.app)

    if args.style == "sandra":
        photo_configure_platform(platform_cfg)
    else:
        carousel_renderer.configure_platform(platform_cfg)
    carousel_renderer.configure_app(app_cfg)

    app_slug = args.app.replace(" ", "_")
    style_folder = args.style
    if args.style == "infographic":
        output_base = Path("output") / "grids" / args.platform / "to_upload"
    else:
        output_base = Path("output") / "to-upload" / app_slug / args.platform / style_folder / "to_upload"

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

    total_carousels = args.count * n_variants
    variant_note = f" × {n_variants} variants = {total_carousels} carousels" if n_variants > 1 else ""
    print(f"\nGenerating {args.count} hook(s){variant_note} — {args.slides} slides each  [{args.style}] [{args.platform}]")
    print(f"App: {args.app!r}\n")

    carousel_counter = 0

    for i in range(args.count):
        # Pick hook for this iteration
        if args.auto:
            base_topic = load_random_hook()
            print(f"[hook {i + 1}/{args.count}] {base_topic!r}")
        else:
            base_topic = args.topic

        # Build slug from the base hook (shared across all its variants)
        _slug_words = re.sub(r'[^a-z0-9\s]', '', base_topic.lower()).split()[:6]
        base_slug = "-".join(_slug_words)

        # Generate variant hooks when needed
        if n_variants > 1:
            print(f"  Generating {n_variants - 1} variant hook(s) via Claude...")
            try:
                extra_hooks = generate_hook_variants(base_topic, n_variants - 1)
            except Exception as exc:
                print(f"  Warning: variant generation failed ({exc}), duplicating original.", file=sys.stderr)
                extra_hooks = [base_topic] * (n_variants - 1)
            all_hooks = [base_topic] + extra_hooks
            for v_idx, vh in enumerate(all_hooks, start=1):
                print(f"    v{v_idx}: {vh!r}")
            print()
        else:
            all_hooks = [base_topic]

        for v_idx, topic in enumerate(all_hooks, start=1):
            v_suffix = f"-v{v_idx}" if n_variants > 1 else ""
            carousel_num = next_num + carousel_counter
            carousel_counter += 1
            carousel_dir = output_base / f"carousel_{carousel_num}_{base_slug}{v_suffix}"

            label = f"[hook {i + 1}/{args.count}, v{v_idx}/{n_variants}]" if n_variants > 1 else f"[{i + 1}/{args.count}]"

            if args.style == "sandra":
                print(f"{label} Fetching Sandra content from Claude...")
                try:
                    items = generate_sandra_carousel(topic, args.slides)
                except Exception as exc:
                    print(f"  Error generating content: {exc}", file=sys.stderr)
                    continue

                print(f"  Fetching {len(items) - 1} Pexels photos for value slides...")
                for j, item in enumerate(items[1:], start=1):
                    query = item.get("pexels_query", "")
                    if not query:
                        continue
                    try:
                        sys.stdout.write(f"    [{j}/{len(items) - 1}] {query!r}...")
                        sys.stdout.flush()
                        rel_path = pexels_mod.fetch_photo(query)
                        item["background_photo"] = rel_path
                        print(" ✓")
                    except Exception as exc:
                        print(f" ✗ ({exc})", file=sys.stderr)
                        item["background_photo"] = ""

                print(f"{label} Rendering slides → {carousel_dir}/")
                try:
                    render_sandra_carousel(topic, items, carousel_dir, args.app)
                except Exception as exc:
                    print(f"  Error rendering slides: {exc}", file=sys.stderr)
                    continue

            else:
                print(f"{label} Fetching content from Claude...")
                try:
                    slides = generate_carousel(args.app, topic, args.slides, style=args.style)
                except Exception as exc:
                    print(f"  Error generating content: {exc}", file=sys.stderr)
                    continue

                _screenshot_options = [p for p in app_cfg.get("screenshot_options", []) if p.exists()]
                if not _screenshot_options:
                    _screenshot_options = [Path("assets") / "MigraineCast Showing Homepage.jpg"]
                screenshot_slides = [
                    {"screenshot_path": str(random.choice(_screenshot_options)), "mascot_expression": "default"},
                ]
                slides = slides[:-1] + screenshot_slides + slides[-1:]
                total_slides = len(slides)

                print(f"{label} Rendering slides → {carousel_dir}/")
                try:
                    illustration = Path(args.illustration) if args.illustration else None
                    render_carousel(slides, carousel_dir, args.app, total_slides, illustration_path=illustration)
                except Exception as exc:
                    print(f"  Error rendering slides: {exc}", file=sys.stderr)
                    continue

            print(f"{label} Generating caption...")
            try:
                caption = generate_caption(args.app, topic)
                caption_path = carousel_dir / "caption.txt"
                caption_path.write_text(caption, encoding="utf-8")
                print(f"    caption.txt → {caption_path}")
            except Exception as exc:
                print(f"  Warning: could not generate caption: {exc}", file=sys.stderr)

    print(f"\nDone! {carousel_counter} carousel(s) saved to {output_base}/")


if __name__ == "__main__":
    main()
