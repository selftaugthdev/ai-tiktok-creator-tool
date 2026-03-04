import json
import os
import re

import anthropic


def generate_carousel(app_name: str, topic: str, num_slides: int = 7, style: str = "regular") -> list:
    """Call the Anthropic API to generate slide content for one carousel."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    num_value_slides = num_slides - 2

    if style == "infographic":
        prompt = f"""Create TikTok carousel slide content about "{topic}" for the app "{app_name}".

Return a JSON array of exactly {num_slides} slide objects.

Slide 1 (hook) must have:
- "headline": bold, alarming hook statement (max 8 words, ALL CAPS encouraged)
- "body": supporting text (max 25 words, conversational)
- "mascot_expression": one of "calm", "default", "sad", "smug", "stormy", "warning". Choose based on emotional tone.

Slides 2 through {num_slides - 1} (value slides, {num_value_slides} slides) must have:
- "headline": category or theme name (max 8 words, ALL CAPS)
- "subtitle": short descriptor phrase for the grid below (max 6 words, title case)
- "items": list of 4-8 objects, each with "label" (short phrase, max 4 words) and "emoji" (a single emoji character). Items must be specific, varied, and relevant to the subtitle.
- "mascot_expression": one of "calm", "default", "sad", "smug", "stormy", "warning". Choose based on emotional tone.

Slide {num_slides} (CTA) must have:
- "headline": call-to-action headline (max 8 words)
- "body": must end with "Download {app_name} on iOS. Link in bio."
- "mascot_expression": must be "smug"

Rules:
- Do NOT use em-dashes (— or –) anywhere. Use commas or periods instead.
- Only include information that is well-established in published research. Do not speculate or extrapolate.
- Return ONLY a valid JSON array. No markdown fences, no explanation."""
        max_tokens = 2048
    else:
        prompt = f"""Create TikTok carousel slide content about "{topic}" for the app "{app_name}".

Return a JSON array of exactly {num_slides} slide objects. Each object must have:
- "headline": punchy, attention-grabbing text (max 8 words, ALL CAPS encouraged)
- "body": supporting text (1-2 sentences, max 25 words)
- "chart_data": (optional) only include when the slide content is naturally suited to a simple bar chart (e.g. statistics, rankings, percentages). Format as {{"labels": [...], "values": [...], "title": "..."}}. Omit this field entirely if not applicable. Do not force a chart onto slides where it does not add value.
- "mascot_expression": one of "calm", "default", "sad", "smug", "stormy", "warning". Choose based on the slide's emotional tone. The last slide (CTA) must always use "smug".

Slide structure:
1. Hook slide: A bold, surprising or alarming statement about {topic} that stops the scroll.
2-{num_slides - 1}. Value slides ({num_value_slides} slides): One specific, actionable tip or insight about {topic} per slide. Each tip must be distinct.
{num_slides}. CTA slide: Encourage users to download {app_name} on iOS. The body must end with "Download {app_name} on iOS. Link in bio."

Rules:
- Headlines must be short and punchy — no filler words.
- Body text should feel conversational and credible.
- Make each value slide feel like a standalone revelation.
- Do NOT use em-dashes (— or –) anywhere in the text. Use commas or periods instead.
- Only include information that is well-established in published research. Do not speculate or extrapolate. If a fact is uncertain, omit it rather than guess.
- Return ONLY a valid JSON array. No markdown fences, no explanation."""
        max_tokens = 1024

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
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
        if "headline" not in slide:
            raise ValueError(f"Slide {i + 1} is missing 'headline' field.")
        is_infographic_value = style == "infographic" and 0 < i < num_slides - 1
        if is_infographic_value:
            if "items" not in slide or "subtitle" not in slide:
                raise ValueError(f"Slide {i + 1} is missing 'items' or 'subtitle' field.")
        else:
            if "body" not in slide:
                raise ValueError(f"Slide {i + 1} is missing 'body' field.")

    return slides
