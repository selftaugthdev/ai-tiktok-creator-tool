"""Truth or Dare AI — script generator."""

import json
import os
import re

import anthropic

FORMATS = [
    "rate-these-dares",
    "bachelorette",
    "couples",
    "office-party",
    "unhinged-ai",
    "truth-or-dare-vs-basic",
]

SYSTEM_PROMPT = """You are a TikTok carousel scriptwriter for Truth or Dare AI, a mobile party game app that uses AI to generate custom dares and truths.

Your job is to generate carousel slide content that feels entertaining, shareable, and social — NOT like an ad. The tone is bold, playful, and slightly unhinged. Think group chat energy.

Always output a valid JSON object and nothing else. No preamble, no markdown fences.

Output schema:
{
  "hook": "text for slide 1 — the scroll-stopper",
  "slides": [
    { "label": "DARE" or "TRUTH", "text": "the dare or truth", "intensity": "mild" | "spicy" | "unhinged" },
    ...
  ],
  "cta": "text for the final slide — natural next step, not an ad"
}

Rules:
- hook: max 10 words, must create curiosity or social FOMO
- slides: 4 to 6 slides, mix of truths and dares unless the format is dare-only
- each slide text: max 2 lines, punchy, specific, not generic
- intensity: distribute realistically — not all unhinged, not all mild
- cta: feels like a friend's suggestion, not a sales pitch. Always refer to the app as "the Truth or Dare AI app". Always say "truths and dares" explicitly, never use vague pronouns like "ones" or "them". Never frame the app's content negatively (e.g. avoid "way worse", "more dangerous", "scarier") — frame it as more fun, more personal, more unhinged in a good way.
- no hashtags, no emojis in the JSON (emojis are added by the renderer)
- never use the word "challenge" — it sounds corporate
- no em dashes (— or –) anywhere. Use commas or periods instead."""

USER_PROMPT_TEMPLATE = """Generate a Truth or Dare AI TikTok carousel.

Format: {format}
Target audience: {audience}
Vibe: {vibe}"""


def generate_tod_carousel(fmt: str, audience: str, vibe: str) -> dict:
    """Call the Anthropic API and return the parsed carousel dict."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(format=fmt, audience=audience, vibe=vibe),
        }],
    )

    raw = message.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    data = json.loads(raw)

    if not isinstance(data, dict):
        raise ValueError("API response is not a JSON object.")
    if "hook" not in data or "slides" not in data or "cta" not in data:
        raise ValueError("Response missing required keys: hook, slides, cta.")
    if not (4 <= len(data["slides"]) <= 6):
        raise ValueError(f"Expected 4-6 slides, got {len(data['slides'])}.")

    return data
