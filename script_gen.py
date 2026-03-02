import json
import os
import re

import anthropic


def generate_carousel(app_name: str, topic: str, num_slides: int = 7) -> list[dict]:
    """Call the Anthropic API to generate slide content for one carousel."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    num_value_slides = num_slides - 2

    prompt = f"""Create TikTok carousel slide content about "{topic}" for the app "{app_name}".

Return a JSON array of exactly {num_slides} slide objects. Each object must have:
- "headline": punchy, attention-grabbing text (max 8 words, ALL CAPS encouraged)
- "body": supporting text (1-2 sentences, max 25 words)

Slide structure:
1. Hook slide: A bold, surprising or alarming statement about {topic} that stops the scroll.
2-{num_slides - 1}. Value slides ({num_value_slides} slides): One specific, actionable tip or insight about {topic} per slide. Each tip must be distinct.
{num_slides}. CTA slide: Encourage users to download {app_name} to track or learn more about {topic}.

Rules:
- Headlines must be short and punchy — no filler words.
- Body text should feel conversational and credible.
- Make each value slide feel like a standalone revelation.
- Return ONLY a valid JSON array. No markdown fences, no explanation."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if the model wraps in them
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    slides = json.loads(raw)

    if not isinstance(slides, list):
        raise ValueError("API response is not a JSON array.")
    if len(slides) != num_slides:
        raise ValueError(f"Expected {num_slides} slides, got {len(slides)}.")

    for i, slide in enumerate(slides):
        if "headline" not in slide or "body" not in slide:
            raise ValueError(f"Slide {i + 1} is missing 'headline' or 'body' field.")

    return slides
