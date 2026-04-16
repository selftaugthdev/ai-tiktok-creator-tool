import json
import os
import re

import anthropic


def generate_carousel(app_name: str, topic: str, num_slides: int = 7, style: str = "regular") -> list:
    """Call the Anthropic API to generate slide content for one carousel."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    num_value_slides = num_slides - 2

    if style == "hybrid":
        num_middle = num_slides - 2
        num_reframe = max(1, round(num_middle * 0.6))
        num_payoff = num_middle - num_reframe
        reframe_range = f"Slides 2-{1 + num_reframe}" if num_reframe > 1 else "Slide 2"
        payoff_range = f"Slides {2 + num_reframe}-{num_slides - 1}" if num_payoff > 1 else f"Slide {2 + num_reframe}"

        prompt = f"""Create a TikTok carousel in the HYBRID format about "{topic}" for the app "{app_name}".

This format has a specific emotional arc: start with pure human pain, teach the science behind it, then arrive at the solution. Never lead with the app. Never sound like an ad.

Return a JSON array of exactly {num_slides} slide objects. Each object must have:
- "headline": punchy, ALL CAPS, max 8 words
- "body": 1-2 sentences, max 25 words
- "mascot_expression": one of "calm", "default", "sad", "smug", "stormy", "warning"

---

SLIDE 1 — EMOTIONAL HOOK
Goal: Make a migraine sufferer feel immediately, deeply seen. This is the moment they stop scrolling because it feels like you read their mind.
- No app mention. No data. No science yet.
- Pure identity and pain. Speak directly to the invisible burden: cancelled plans, not being believed, dreading the unknown, losing control of their own life.
- Use second person ("you", "your"). Write as if you have migraines too.
- Headline: a raw, specific emotional truth — not a question, not a generic hook. Something they have felt but never seen written down.
- Body: double down on the feeling. Make them feel understood, not informed.
- mascot_expression: "sad" or "stormy" (empathy, not alarm)

---

{reframe_range} — REFRAME ({num_reframe} slide{"s" if num_reframe > 1 else ""})
Goal: Transition from emotional to educational. Explain the science or pattern that causes what they just felt on slide 1. The tone shifts from empathetic to empowering — the reader goes from "I feel this" to "now I understand why."
- Introduce the mechanism: barometric pressure drops, the trigeminovascular system, the prodrome phase, pattern recognition across time.
- Tie every scientific point directly back to the lived experience described on slide 1. Never explain in the abstract.
- Each slide: one clear mechanism or insight. Use specific numbers and timeframes where possible ("pressure can drop 10 hPa in under 3 hours", "your brain detects changes 24-48 hours before the headache hits").
- Language: plain, conversational. Write like a fellow sufferer who has done their homework, not a medical pamphlet.
- mascot_expression: "default" or "calm" (curious, thoughtful tone)

---

{payoff_range} — PAYOFF ({num_payoff} slide{"s" if num_payoff > 1 else ""})
Goal: Connect the insight to taking back control. This is where {app_name} earns its place — as the logical next step, not a sales pitch.
- Frame it as: "now that you understand why this happens, here is how you can stop being blindsided."
- {app_name} should feel like the tool that makes the science from the reframe slides actionable. Never describe features — describe the change in the reader's life.
- Tone: empowering, forward-looking. The reader should feel capable, not sold to.
- The app name may appear here, but only in service of the reader's outcome.
- mascot_expression: "smug" or "calm" (confident, reassuring)

---

SLIDE {num_slides} — CTA
- Headline: a confident, outcome-focused call to action (max 8 words)
- Body: must end with "Download {app_name} on iOS. Link in bio. Or download at www.migrainecast.app"
- mascot_expression: must be "smug"

---

TONE RULES — read these carefully:
- 40% emotional, 40% educational, 20% solution. This ratio must be felt across the carousel as a whole.
- Never open with the app. Never use clinical or corporate language. No "game-changer", "empower", "unlock", "journey", "dive into".
- Write every slide as if spoken by someone who has migraines and has done the research themselves.
- Value slides should feel like something a reader would screenshot and send to someone who doesn't understand their condition.
- Do NOT use em-dashes (— or –) anywhere. Use commas or periods instead.
- Only include facts that are well-established in published research. Do not speculate.
- Return ONLY a valid JSON array. No markdown fences, no explanation."""
        max_tokens = 1024

    elif style == "infographic":
        prompt = f"""Create TikTok carousel slide content about "{topic}" for the app "{app_name}".

Return a JSON array of exactly {num_slides} slide objects.

Slide 1 (hook) must have:
- "headline": scroll-stopping hook (max 8 words, ALL CAPS). The goal is to make a migraine sufferer think "that's exactly what happens to me." Choose ONE of these formulas and write a fresh variation for "{topic}" — do NOT copy verbatim:
  * "I TRACKED [X] MONTHS OF MIGRAINES AND FOUND THIS" (personal discovery)
  * "THIS IS WHY YOU GET A MIGRAINE EVERY TIME [specific scenario from topic]" (pattern recognition)
  * "NOBODY WARNS YOU [uncomfortable specific truth about topic]" (pain validation)
  * "STOP [doing common thing] IF YOU GET MIGRAINES" (pattern interrupt)
  * "THIS IS WHY [topic-related situation] KEEPS HAPPENING TO YOU" (self-recognition)
  * "I DIDN'T BELIEVE MIGRAINES COULD BE PREDICTED UNTIL THIS" (social proof / discovery)
  Avoid: "DID YOU KNOW", "HERE'S WHAT", "THE TRUTH ABOUT". Must be specific to "{topic}", not generic migraine content.
- "body": 1 sentence that makes the reader feel seen — like you lived this too (max 25 words, conversational, first or second person, NOT a definition or list)
- "mascot_expression": one of "calm", "default", "sad", "smug", "stormy", "warning". Choose based on emotional tone.

Slides 2 through {num_slides - 1} (value slides, {num_value_slides} slides) must have:
- "headline": category or theme name (max 8 words, ALL CAPS)
- "subtitle": short descriptor phrase for the grid below (max 6 words, title case)
- "items": list of 4-6 objects, each with "label" (short phrase, max 4 words) and "emoji" (a single emoji character). Items must be specific, concrete, and instantly recognizable to a migraine sufferer — not clinical labels.
- "mascot_expression": one of "calm", "default", "sad", "smug", "stormy", "warning". Choose based on emotional tone.

Slide {num_slides} (CTA) must have:
- "headline": call-to-action headline (max 8 words)
- "body": must end with "Download {app_name} on iOS. Link in bio. Or download at www.migrainecast.app"
- "mascot_expression": must be "smug"

Rules:
- THE GOAL IS RECOGNITION, NOT EDUCATION. Every slide must make a migraine sufferer think "that's exactly what happens to me — I need this." Urgency comes from specificity, not from general facts.
- STAY ON TOPIC. Every value slide must directly address the exact situation in "{topic}". If the topic is about canceling plans, items cover the guilt, communication, and recovery — NOT general migraine science.
- Items must be specific and non-obvious. No generic entries like "take medication", "rest", or "drink water."
- Each item should feel like something a migraine sufferer would screenshot to show someone who doesn't understand them.
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
1. Hook slide (ALL CAPS headline, max 8 words): The goal is to make a migraine sufferer think "that's exactly what happens to me." Choose ONE of these formulas and write a fresh variation for "{topic}" — do NOT copy verbatim:
   * "I TRACKED [X] MONTHS OF MIGRAINES AND FOUND THIS" (personal discovery)
   * "THIS IS WHY YOU GET A MIGRAINE EVERY TIME [specific scenario from topic]" (pattern recognition)
   * "NOBODY WARNS YOU [uncomfortable specific truth about topic]" (pain validation)
   * "STOP [doing common thing] IF YOU GET MIGRAINES" (pattern interrupt)
   * "THIS IS WHY [topic-related situation] KEEPS HAPPENING TO YOU" (self-recognition)
   * "I DIDN'T BELIEVE MIGRAINES COULD BE PREDICTED UNTIL THIS" (social proof / discovery)
   Avoid: "DID YOU KNOW", "HERE'S WHAT", "THE TRUTH ABOUT". Body (max 25 words) must make the reader feel seen — like you lived this — not a definition or list.
2-{num_slides - 1}. Value slides ({num_value_slides} slides): One specific, instantly recognizable insight per slide. Each must be distinct and make the reader think "that's me."
{num_slides}. CTA slide: Encourage users to download {app_name} on iOS. The body must end with "Download {app_name} on iOS. Link in bio. Or download at www.migrainecast.app"

Copywriting rules for value slides — this is the most important part:
- THE GOAL IS RECOGNITION, NOT EDUCATION. Every slide must make a migraine sufferer think "that's exactly what happens to me — I need this." That sense of being understood is what converts, not general facts.
- STAY ON TOPIC. Every value slide must directly address the exact situation in the topic. If the topic is about canceling plans, tips cover the guilt, the decision, the communication — NOT caffeine or sleep science.
- NEVER drift off-topic. If someone asked about canceling plans, they do not want a lecture on neck stiffness.
- NEVER write obvious tips. No "take your medication", "stay hydrated", "lie in a dark room", "track your triggers."
- Use first or second person ("You've probably noticed...", "Most people with migraines don't realize..."). Make it feel personal, not clinical.
- Use specific details: timeframes, numbers, named scenarios. "3-4 hours before a storm, pressure drops and your neck stiffens" beats "weather affects migraines."
- Each slide should feel like something a reader would screenshot and send to someone who doesn't understand their migraines.

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


def generate_caption(app_name: str, topic: str) -> str:
    """Generate a TikTok caption (title + description + hashtags) for a carousel."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""Write a TikTok caption for a carousel about "{topic}" promoting the app "{app_name}".

Return plain text in this exact format (no markdown, no extra commentary):

TITLE:
[one line, the exact topic rephrased as a scroll-stopping TikTok title, max 60 characters]

DESCRIPTION:
[2-3 short sentences, conversational and direct, written like a real person talking to their audience. No corporate language, no buzzwords.]

HASHTAGS:
[8-12 relevant hashtags as a single line]

Rules:
- No em-dashes (— or –). Use commas or periods instead.
- No AI-sounding phrases like "game-changer", "dive into", "unlock", "journey", "empower".
- Write like someone who has migraines talking to others who do.
- The description should make people want to save the post."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    caption = message.content[0].text.strip()
    cta = "Stay ahead of your migraines with the MigraineCast app, link in Bio, free to download in the App store or at www.migrainecast.app"
    return f"{caption}\n\n{cta}"
