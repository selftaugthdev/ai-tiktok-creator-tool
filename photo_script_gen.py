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

    photo_list = "\n".join(f"  - {p}" for p in photos)
    num_value = num_slides - 2

    prompt = f"""Create TikTok photo-overlay carousel content about "{topic}" for the app "{app_name}".

Available background photos:
{photo_list}

Return a JSON array of exactly {num_slides} slide objects.

Slide 1 (hook):
- "headline": single scroll-stopping statement (max 10 words, alarming or curiosity-driving, no question mark)
- "background_photo": the most dramatic or emotionally striking photo from the list

Slides 2 to {num_slides - 1} (value slides, {num_value} total):
- "headline": punchy point (max 7 words, ALL CAPS encouraged)
- "body": supporting detail (max 18 words, conversational)
- "background_photo": the most contextually relevant photo for this slide's content

Slide {num_slides} (CTA — no background_photo needed, handled automatically):
- "headline": short call-to-action (max 7 words)
- "body": must end with "Download {app_name} on iOS. Link in bio."

Rules:
- Every slide must have a different background_photo — no repeats
- Match photo mood to slide content (stormy sky for pressure/weather, lifestyle for personal struggle, props for triggers)
- Hook gets the most visually striking photo in the library
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
