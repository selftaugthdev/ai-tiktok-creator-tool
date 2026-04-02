"""Photo-overlay carousel — script generator."""

import json
import os
import re
from pathlib import Path

import anthropic

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

    hook_photo_list = "\n".join(f"  - {p}" for p in hook_photos) if hook_photos else "  (none yet — pick from value photos)"
    all_value_photos = value_photos + hook_photos  # hook photos also available for value slides
    value_photo_list = "\n".join(f"  - {p}" for p in all_value_photos)

    # Claude generates hook + value slides only — CTA is always the fixed homepage slide
    claude_slides = num_slides - 1
    num_value = claude_slides - 1

    prompt = f"""Create TikTok photo-overlay carousel content about "{topic}" for the app "{app_name}".

Hook photos (preferred for slide 1 — woman with phone, happy/surprised reactions):
{hook_photo_list}

All available photos (use for any slide):
{value_photo_list}

Return a JSON array of exactly {claude_slides} slide objects.

Slide 1 (hook):
- "headline": a conversational, disbelief-style scroll-stopper in the style of one of these examples (make your own variation, do not copy verbatim):
  * "Will the weather trigger my migraine again today?"
  * "So you mean there is an app that helps forecast migraines?"
  * "That moment you find out there is actually an app that lets you log migraines and forecasts them accurately"
  * "So this app provides a detailed PDF report for all my migraine triggers to give to my doctor?"
  * "You're telling me there's an app that warns me for a migraine based on my personal triggers?"
  The hook must feel like a real person's reaction or a question they'd actually ask. Tie it directly to "{topic}".
- "background_photo": prefer hook photos for slide 1, but use any photo if it's a stronger contextual match

Slides 2 to {claude_slides} (value slides, {num_value} total):
- "headline": punchy point (max 7 words, ALL CAPS encouraged)
- "body": supporting detail (max 18 words, conversational)
- "background_photo": pick the single most contextually relevant photo for this slide's specific content

Rules:
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
