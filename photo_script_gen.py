"""Photo-overlay carousel — script generator."""

import json
import os
import random
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
