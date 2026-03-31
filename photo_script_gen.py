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
    value_photo_list = "\n".join(f"  - {p}" for p in value_photos)
    num_value = num_slides - 2

    prompt = f"""Create TikTok photo-overlay carousel content about "{topic}" for the app "{app_name}".

Hook photos (use ONLY these for slide 1):
{hook_photo_list}

Value/background photos (use for slides 2 onward):
{value_photo_list}

Return a JSON array of exactly {num_slides} slide objects.

Slide 1 (hook):
- "headline": a conversational, disbelief-style scroll-stopper in the style of one of these examples (make your own variation, do not copy verbatim):
  * "Will the weather trigger my migraine again today?"
  * "So you mean there is an app that helps forecast migraines?"
  * "That moment you find out there is actually an app that lets you log migraines and forecasts them accurately"
  * "So this app provides a detailed PDF report for all my migraine triggers to give to my doctor?"
  * "You're telling me there's an app that warns me for a migraine based on my personal triggers?"
  The hook must feel like a real person's reaction or a question they'd actually ask. Tie it directly to "{topic}".
- "background_photo": pick from hook photos only (the woman-with-phone / happy woman style fits this tone)

Slides 2 to {num_slides - 1} (value slides, {num_value} total):
- "headline": punchy point (max 7 words, ALL CAPS encouraged)
- "body": supporting detail (max 18 words, conversational)
- "background_photo": most contextually relevant photo from the value/background list

Slide {num_slides} (CTA — no background_photo needed, handled automatically):
- "headline": short call-to-action (max 7 words)
- "body": must end with "Download {app_name} on iOS. Link in bio."

Rules:
- Every slide must use a different background_photo — no repeats
- Match photo mood to slide content (stormy sky for weather slides, lifestyle for struggle, props for triggers)
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
    if len(slides) != num_slides:
        raise ValueError(f"Expected {num_slides} slides, got {len(slides)}.")

    return slides
