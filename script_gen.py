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
- "items": list of 4-6 objects, each with "label" (short phrase, max 4 words) and "emoji" (a single emoji character). Items must be specific, varied, and relevant to the subtitle.
- "mascot_expression": one of "calm", "default", "sad", "smug", "stormy", "warning". Choose based on emotional tone.

Slide {num_slides} (CTA) must have:
- "headline": call-to-action headline (max 8 words)
- "body": must end with "Download {app_name} on iOS. Link in bio. Or download at www.migrainecast.app"
- "mascot_expression": must be "smug"

Rules:
- STAY ON TOPIC. Every value slide must directly address the specific situation or scenario described in the topic. If the topic is about canceling plans, items must be about handling that moment — the guilt, the communication, the recovery — NOT general migraine science or biology.
- NEVER drift into tangentially related but off-topic content. Tips about heat/ice packs, body posture, or caffeine are off-topic if the subject is an emotional or social situation.
- Items must be specific and non-obvious. No generic entries like "take medication", "rest", or "drink water" — assume the audience already knows those.
- Each item should feel like something worth writing down.
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
1. Hook slide: A bold, surprising or alarming statement about {topic} that stops the scroll. Make it feel urgent and personal.
2-{num_slides - 1}. Value slides ({num_value_slides} slides): One specific, non-obvious tip or insight per slide. Each tip must be distinct.
{num_slides}. CTA slide: Encourage users to download {app_name} on iOS. The body must end with "Download {app_name} on iOS. Link in bio. Or download at www.migrainecast.app"

Copywriting rules for value slides — this is the most important part:
- STAY ON TOPIC. Every value slide must directly address the specific situation or scenario described in the topic. If the topic is about canceling plans, tips must be about handling that moment — the guilt, the communication, the recovery, the decision-making — NOT general migraine science or biology.
- NEVER drift into tangentially related but off-topic content. If someone asked for "tips for canceling plans", they do not want a lecture on caffeine or neck stiffness. They want tips for what to do RIGHT NOW in that situation.
- NEVER write obvious tips. Assume the audience already knows the basics. No "take your medication", "stay hydrated", "lie in a dark room", "track your triggers" — these are things everyone has heard.
- Every tip must feel like a revelation. Ask yourself: would a migraine sufferer stop scrolling and think "I didn't know that"? If not, pick a different angle.
- Lead with the surprising or counterintuitive angle — the emotional truth, the social strategy, or the body mechanism. Make it feel like insider knowledge, not a doctor's pamphlet.
- Use specific numbers, timeframes, or concrete actions where possible. Vague claims lose trust.
- Each slide should feel complete as a standalone post.

General rules:
- Headlines must be short and punchy — no filler words.
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
