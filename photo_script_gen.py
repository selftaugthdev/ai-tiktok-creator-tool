"""Photo-overlay carousel — script generator."""

import json
import os
import random
import re
from pathlib import Path

import anthropic

from app_config import get_app_config

PHOTOS_DIR = Path("photos")


def get_available_photos() -> list:
    """Scan photos/ recursively and return relative paths (folder/name.ext)."""
    if not PHOTOS_DIR.exists():
        return []
    photos = []
    for p in sorted(PHOTOS_DIR.rglob("*")):
        if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp") and p.is_file():
            photos.append(str(p.relative_to(PHOTOS_DIR)))
    return photos


def generate_photo_carousel(app_name: str, topic: str, num_slides: int) -> list:
    """Call Claude to generate slide copy + pick a background photo per slide."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    photos = get_available_photos()
    if not photos:
        raise ValueError("No photos found in photos/ directory.")

    hook_photos = [p for p in photos if p.startswith("hook/")]
    value_photos = [p for p in photos if not p.startswith("hook/")]

    # Randomly pre-select the hook photo so Claude doesn't always pick the same one
    chosen_hook_photo = random.choice(hook_photos) if hook_photos else None

    all_value_photos = value_photos + hook_photos  # hook photos also available for value slides
    value_photo_list = "\n".join(f"  - {p}" for p in all_value_photos)

    # Claude generates hook + value slides only — CTA is always the fixed homepage slide
    claude_slides = num_slides - 1
    num_value = claude_slides - 1

    hook_photo_instruction = (
        f'- "background_photo": use exactly "{chosen_hook_photo}" (already selected for you)'
        if chosen_hook_photo
        else '- "background_photo": pick any contextually relevant photo'
    )

    prompt = f"""Create TikTok photo-overlay carousel content about "{topic}" for the app "{app_name}".

All available photos (use for value slides):
{value_photo_list}

Return a JSON array of exactly {claude_slides} slide objects.

Slide 1 (hook):
- "headline": a conversational scroll-stopper that makes a migraine sufferer think "that's exactly what happens to me." Sounds like a real person's spoken reaction — not an ad. Choose ONE of these formats and write a fresh variation for "{topic}" — do NOT copy verbatim:
  * Personal discovery: "I tracked 6 months of migraines and [specific pattern from topic] showed up every single time"
  * Pattern recognition: "This is why you get a migraine every time [specific scenario tied to topic]"
  * Disbelief/social proof: "Wait, you're telling me there's an app that actually predicted my migraine 6 hours before it hit?"
  * POV moment: "POV: You check MigraineCast the morning of [specific scenario from topic] and it already warned you"
  * Pain validation: "Nobody talks about [specific uncomfortable truth tied to topic] and it's ruining migraine sufferers' lives"
  * Recognition: "If [very specific type of migraine situation tied to topic] keeps happening to you, this is why"
  Must be specific to "{topic}" — never a generic app pitch. The more specific and recognizable, the better.
{hook_photo_instruction}

Slides 2 to {claude_slides} (value slides, {num_value} total):
- "headline": specific, pattern-recognition point (max 7 words, ALL CAPS). Must make a migraine sufferer think "that's exactly what happens to me" — not a generic fact.
- "body": 1 sentence in first or second person that names the exact experience ("You've probably noticed...", "Most people don't realize..."). Max 18 words. Specific details beat vague claims.
- "background_photo": pick the single most contextually relevant photo for this slide's specific content

Rules:
- THE GOAL IS RECOGNITION, NOT EDUCATION. Urgency comes from specificity. Name exact scenarios, timeframes, and patterns — not general migraine science.
- PHOTO MATCHING IS CRITICAL. Read every filename carefully. If a filename directly matches the slide content, always use it — it beats any generic mood match. Examples:
  * A slide about doctor reports → use "hook/MigraineCast_Report.png" or "hook/Handing_report_on_phone_to_doctor.jpg" or "hook/woman_showing_phone_with_pdf_report.jpg"
  * A slide about caffeine → use "props/coffee_cup.jpg"
  * A slide about alcohol triggers → use "props/glass_of_wine.jpg"
  * A slide about sleep → use "lifestyle/person_in_bed_not_sleeping.jpg" or "lifestyle/woman_waking_up_groggy.jpg"
  * A slide about light sensitivity → use "lifestyle/woman_wearing_sunglasses_indoor.jpg"
  * A slide about barometric pressure → use "weather/barometric_pressure_change.jpg" or "weather/barometer.jpg"
- Every slide must use a different background_photo — no repeats
- No em-dashes (— or –). Use commas or periods instead
- Return ONLY a valid JSON array. No markdown fences, no explanation."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    slides = json.loads(raw)

    if not isinstance(slides, list):
        raise ValueError("API response is not a JSON array.")
    if len(slides) != claude_slides:
        raise ValueError(f"Expected {claude_slides} slides, got {len(slides)}.")

    return slides


def generate_photo_carousel_pexels(app_name: str, topic: str, num_slides: int) -> list:
    """Like generate_photo_carousel, but asks Claude for a Pexels search query
    per slide instead of picking from local filenames.

    Each returned slide dict has a 'pexels_query' key instead of 'background_photo'.
    photo_main.py resolves these to actual file paths after calling this function.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Claude generates hook + value slides — CTA is always the fixed homepage slide
    claude_slides = num_slides - 1
    num_value = claude_slides - 1

    prompt = f"""Create TikTok photo-overlay carousel content about "{topic}" for the app "{app_name}".

Return a JSON array of exactly {claude_slides} slide objects.

Slide 1 (hook):
- "headline": a conversational scroll-stopper that makes a migraine sufferer think "that's exactly what happens to me." Sounds like a real person's spoken reaction, not an ad. Choose ONE of these formats:
  * Personal discovery: "I tracked 6 months of migraines and [specific pattern from topic] showed up every single time"
  * Pattern recognition: "This is why you get a migraine every time [specific scenario tied to topic]"
  * POV moment: "POV: You check MigraineCast the morning of [specific scenario from topic] and it already warned you"
  * Pain validation: "Nobody talks about [specific uncomfortable truth tied to topic] and it's ruining migraine sufferers' lives"
  * Recognition: "If [very specific type of migraine situation tied to topic] keeps happening to you, this is why"
  Must be specific to "{topic}" — never a generic app pitch.
- "pexels_query": a vivid, specific 4-8 word search query describing the ideal background photo for this hook. Think cinematic and emotional — e.g. "woman lying in dark room with headache", "person canceling plans on phone looking sad". No brand names.

Slides 2 to {claude_slides} (value slides, {num_value} total):
- "headline": specific, pattern-recognition point (max 7 words, ALL CAPS). Must make a migraine sufferer think "that's exactly what happens to me."
- "body": 1 sentence in first or second person. Max 18 words. Specific details beat vague claims.
- "pexels_query": a vivid, specific 4-8 word search query for the ideal background photo. Match the slide's exact content — e.g. "feet soaking hot water tub", "peppermint essential oil bottle", "stormy weather dark clouds outside window", "person squinting at bright computer screen". No brand names.

Rules:
- THE GOAL IS RECOGNITION, NOT EDUCATION. Name exact scenarios, timeframes, and patterns.
- Every slide must have a different pexels_query — no repeats.
- Pexels queries should be highly visual and specific. Avoid abstract queries like "migraine pain" — instead describe a concrete scene or object.
- No em-dashes (— or –). Use commas or periods instead.
- Return ONLY a valid JSON array. No markdown fences, no explanation."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    slides = json.loads(raw)

    if not isinstance(slides, list):
        raise ValueError("API response is not a JSON array.")
    if len(slides) != claude_slides:
        raise ValueError(f"Expected {claude_slides} slides, got {len(slides)}.")

    return slides


def generate_sandra_carousel(
    hook: str,
    num_slides: int,
    app_name: str = "MigraineCast",
    avatar_override: str = None,
) -> list:
    """Generate avatar-style carousel content built around a given hook.

    Returns a list of (num_slides - 2) dicts:
      [0]  {"sandra_image": "<filename>"}         — avatar (pre-mapped or Claude-selected)
      [1+] {"headline": "...", "body": "...", "pexels_query": "..."}  — value slides

    When avatar_override is provided the avatar is pre-mapped and Claude only generates
    the value slides. Otherwise Claude picks the avatar from app_config avatar_images.

    The caller appends the two fixed end slides (app showcase + CTA) during rendering.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    app_cfg = get_app_config(app_name)
    audience = app_cfg.get("audience", "user")
    carousel_screenshots = app_cfg.get("app_carousel_screenshots", [])
    has_screenshots = bool(carousel_screenshots)

    # Showcase slide is replaced by app screenshot slide when screenshots are configured,
    # so num_value stays the same either way (screenshot takes showcase's slot).
    num_value = num_slides - 3          # subtract hook slide, showcase/screenshot, CTA

    screenshot_section = ""
    if has_screenshots:
        screenshot_options = "\n".join(
            f"  - {f}" for f in carousel_screenshots
        )
        screenshot_section = f"""

Final object (app screenshot slide — comes AFTER the value slides in the array):
Pick the screenshot whose content most directly relates to the hook topic.
Available screenshots:
{screenshot_options}

Return:
- "app_screenshot": the chosen filename (exact, from the list above)
- "label": 2-4 words, Title Case, describes what the screenshot shows (e.g. "3-Day Forecast", "Trigger Guide")
- "body": 1-2 sentences, first or second person, max 20 words. Make the reader want to use this feature.
- "pexels_query": 4-8 word vivid background photo description for this slide"""

    if avatar_override:
        # Avatar is pre-mapped — Claude only generates value slides (+ optional screenshot)
        total_items = num_value + (1 if has_screenshots else 0)
        prompt = f"""Create TikTok carousel slides built around this exact hook:
"{hook}"

Return a JSON array of exactly {total_items} objects.

Objects 1 to {num_value} (value slides):
Each delivers one specific insight that validates and expands the hook.
- "headline": max 7 words, ALL CAPS. Pattern-recognition statement — {audience}s should think "that's exactly what happens to me."
- "body": 1 sentence, first or second person, max 18 words. Specific details beat vague claims.
- "pexels_query": 4-8 word vivid scene description for the background photo (no brand names).
{screenshot_section}
Rules:
- Value slides must logically continue the hook: explain the WHY, the HOW, or what to do about it.
- Every pexels_query must be unique.
- NEVER use em-dashes (— – ‒ ―). This is a hard rule. Use commas or periods instead.
- Return ONLY a valid JSON array. No markdown fences, no explanation."""

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        items = json.loads(raw.strip())

        if not isinstance(items, list):
            raise ValueError("API response is not a JSON array.")
        if len(items) != total_items:
            raise ValueError(f"Expected {total_items} items, got {len(items)}.")

        return [{"sandra_image": avatar_override}] + items

    # No pre-mapped avatar — Claude picks avatar + generates value slides (+ optional screenshot)
    avatar_images = app_cfg.get("avatar_images", [])
    avatar_image_guide = app_cfg.get("avatar_image_guide", "")

    if not avatar_images:
        raise ValueError(
            f"No avatar images configured for {app_name!r}. "
            "Add image filenames to 'avatar_images' in app_config.py."
        )

    total_items = num_value + 1 + (1 if has_screenshots else 0)  # avatar + values + screenshot
    image_list = "\n".join(f"  - {img}" for img in avatar_images)

    prompt = f"""Create TikTok avatar-style carousel content built around this exact hook:
"{hook}"

Available avatar images:
{image_list}

Return a JSON array of exactly {total_items} objects.

Object 1 (hook avatar selection):
- "sandra_image": match the image to the LITERAL CONTENT of the hook — not its tone. All hooks sound bold; choose based on what the hook is actually about:
{avatar_image_guide}

Objects 2 to {num_value + 1} (value slides, {num_value} total):
Each delivers one specific insight that validates and expands the hook.
- "headline": max 7 words, ALL CAPS. Pattern-recognition statement — {audience}s should think "that's exactly what happens to me."
- "body": 1 sentence, first or second person, max 18 words. Specific details beat vague claims.
- "pexels_query": 4-8 word vivid scene description for the background photo (no brand names).
{screenshot_section}
Rules:
- Value slides must logically continue the hook: explain the WHY, the HOW, or what to do about it.
- Every pexels_query must be unique.
- NEVER use em-dashes (— – ‒ ―). This is a hard rule. Use commas or periods instead.
- Return ONLY a valid JSON array. No markdown fences, no explanation."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    items = json.loads(raw)

    if not isinstance(items, list):
        raise ValueError("API response is not a JSON array.")
    if len(items) != total_items:
        raise ValueError(f"Expected {total_items} items, got {len(items)}.")

    return items
