"""Truth or Dare AI — carousel renderer."""

from pathlib import Path

from PIL import Image, ImageDraw

from carousel_renderer import (
    _draw_centered_lines,
    _text_block_height,
    _wrap_text,
    load_font,
    ACCENT_BAR_HEIGHT,
    MARGIN_X,
    SAFE_ZONE_BOTTOM,
    SLIDE_NUM_MARGIN,
    WIDTH,
    HEIGHT,
)

# ── Backgrounds ───────────────────────────────────────────────────────────────
BG_DARK = (15, 23, 42)         # #0F172A — hook & CTA
BG_DARE = (239, 68, 68)        # #EF4444 — DARE slides
BG_TRUTH = (59, 130, 246)      # #3B82F6 — TRUTH slides

# ── Chrome colors (counter, watermark, accent bar) ────────────────────────────
ACCENT_PURPLE = (139, 92, 246)         # #8B5CF6
COLOR_COUNTER_DARK = (139, 92, 246)    # purple on dark bg
COLOR_COUNTER_LIGHT = (255, 255, 255)  # white on colored bg
COLOR_WATERMARK = (148, 163, 184)      # #94A3B8 slate

# ── Card ──────────────────────────────────────────────────────────────────────
CARD_COLOR = (255, 255, 255)
CARD_MARGIN_X = 80     # card left/right from canvas edge → card width = 920px
CARD_PAD_X = 60        # inner horizontal padding
CARD_PAD_Y = 64        # inner top/bottom padding
CARD_RADIUS = 36
CARD_ITEM_GAP = 48     # gap between badge / text / intensity inside card

# ── DARE/TRUTH badge (inside card) ────────────────────────────────────────────
BADGE_FONT_SIZE = 56
BADGE_COLOR = (26, 26, 26)   # near-black
BADGE_PAD_X = 52
BADGE_PAD_Y = 22

# ── Main card text ────────────────────────────────────────────────────────────
CARD_TEXT_FONT_SIZE = 58
CARD_TEXT_COLOR = (26, 26, 26)

# ── Intensity badge ───────────────────────────────────────────────────────────
INTENSITY_FONT_SIZE = 36
INTENSITY_PAD_X = 36
INTENSITY_PAD_Y = 16
INTENSITY_COLORS = {
    "mild": (34, 197, 94),     # #22C55E green
    "spicy": (249, 115, 22),   # #F97316 orange
    "unhinged": (239, 68, 68), # #EF4444 red
}

# ── Hook / CTA ────────────────────────────────────────────────────────────────
HOOK_FONT_SIZE = 88
CTA_FONT_SIZE = 56
CTA_DOWNLOAD_FONT_SIZE = 40
CTA_LOGO_W = 340          # logo width on CTA slide
CTA_LOGO_RADIUS = 60      # rounded corner clip for the logo
CTA_LOGO_GAP = 56         # gap between logo and tagline
CTA_TAGLINE_GAP = 36      # gap between tagline and download line
TOD_LOGO_PATH = Path("assets") / "Truth Or Dare Ai LOGO.png"
CTA_DOWNLOAD_TEXT = "Download on the App Store. Link in bio."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pill(draw: ImageDraw.ImageDraw, text: str, font, cx: int, y: int,
          bg: tuple, fg: tuple, pad_x: int, pad_y: int) -> int:
    """Draw a centered pill. Returns y-coordinate after the pill."""
    lb = draw.textbbox((0, 0), text, font=font)
    tw, th = lb[2] - lb[0], lb[3] - lb[1]
    bw = tw + pad_x * 2
    bh = th + pad_y * 2
    bx = cx - bw // 2
    draw.rounded_rectangle([(bx, y), (bx + bw, y + bh)], radius=bh // 2, fill=bg)
    # Compensate for textbbox origin offset so text is perfectly centered
    draw.text((bx + pad_x - lb[0], y + pad_y - lb[1]), text, font=font, fill=fg)
    return y + bh


def _pill_height(draw: ImageDraw.ImageDraw, text: str, font, pad_y: int) -> int:
    lb = draw.textbbox((0, 0), text, font=font)
    return (lb[3] - lb[1]) + pad_y * 2


# ---------------------------------------------------------------------------
# Slide renderers
# ---------------------------------------------------------------------------

def _render_chrome(
    draw: ImageDraw.ImageDraw,
    slide_index: int,
    total_slides: int,
    app_name: str,
    counter_color: tuple,
) -> None:
    """Slide counter (top-right) + watermark (top-left)."""
    counter_font = load_font(38, bold=False)
    watermark_font = load_font(34, bold=False)

    counter_text = f"{slide_index} / {total_slides}"
    cb = draw.textbbox((0, 0), counter_text, font=counter_font)
    draw.text(
        (WIDTH - SLIDE_NUM_MARGIN - (cb[2] - cb[0]), SLIDE_NUM_MARGIN),
        counter_text,
        font=counter_font,
        fill=counter_color,
    )
    draw.text((SLIDE_NUM_MARGIN, SLIDE_NUM_MARGIN), app_name, font=watermark_font, fill=COLOR_WATERMARK)


def _render_hook(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    slide_data: dict,
    slide_index: int,
    total_slides: int,
    app_name: str,
) -> None:
    font = load_font(HOOK_FONT_SIZE, bold=True)
    available_width = WIDTH - 2 * MARGIN_X
    usable_top = SLIDE_NUM_MARGIN + 80
    usable_bottom = HEIGHT - SAFE_ZONE_BOTTOM

    lines = _wrap_text(draw, slide_data["text"], font, available_width)
    total_h = _text_block_height(draw, lines, font, 16)
    block_top = max((usable_top + usable_bottom) // 2 - total_h // 2, usable_top)

    pip_y = block_top - 36
    if pip_y >= usable_top - 10:
        draw.rectangle([(WIDTH // 2 - 60, pip_y), (WIDTH // 2 + 60, pip_y + 6)], fill=ACCENT_PURPLE)

    _draw_centered_lines(draw, lines, font, block_top, (255, 255, 255), line_gap=16)
    _render_chrome(draw, slide_index, total_slides, app_name, counter_color=COLOR_COUNTER_DARK)


def _split_sentences(text: str) -> list:
    """Split text into individual sentences on . ! ? boundaries."""
    import re
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in parts if s.strip()]


def _render_cta(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    slide_data: dict,
    slide_index: int,
    total_slides: int,
    app_name: str,
) -> None:
    tagline_font = load_font(CTA_FONT_SIZE, bold=True)
    download_font = load_font(CTA_DOWNLOAD_FONT_SIZE, bold=False)
    available_width = WIDTH - 2 * MARGIN_X
    usable_top = SLIDE_NUM_MARGIN + 80
    usable_bottom = HEIGHT - SAFE_ZONE_BOTTOM

    # Split tagline into individual sentences for airy spacing
    sentences = _split_sentences(slide_data["text"])
    SENTENCE_GAP = 40  # extra gap between sentences

    sentence_blocks = [_wrap_text(draw, s, tagline_font, available_width) for s in sentences]
    sentence_heights = [_text_block_height(draw, b, tagline_font, 16) for b in sentence_blocks]
    tagline_h = sum(sentence_heights) + SENTENCE_GAP * (len(sentences) - 1)

    logo_h = CTA_LOGO_W
    dl_lines = _wrap_text(draw, CTA_DOWNLOAD_TEXT, download_font, available_width)
    dl_h = _text_block_height(draw, dl_lines, download_font, 12)

    total_h = logo_h + CTA_LOGO_GAP + tagline_h + CTA_TAGLINE_GAP + dl_h
    block_top = max((usable_top + usable_bottom) // 2 - total_h // 2, usable_top)

    y = block_top

    # Logo
    if TOD_LOGO_PATH.exists():
        logo = Image.open(TOD_LOGO_PATH).convert("RGBA")
        logo = logo.resize((CTA_LOGO_W, CTA_LOGO_W), Image.LANCZOS)
        # Clip to rounded square using a mask
        mask = Image.new("L", (CTA_LOGO_W, CTA_LOGO_W), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), (CTA_LOGO_W, CTA_LOGO_W)], radius=CTA_LOGO_RADIUS, fill=255)
        logo_x = (WIDTH - CTA_LOGO_W) // 2
        img.paste(logo, (logo_x, y), mask=mask)

    y += logo_h + CTA_LOGO_GAP

    # Tagline — each sentence drawn separately with breathing room
    for i, (block, block_h) in enumerate(zip(sentence_blocks, sentence_heights)):
        _draw_centered_lines(draw, block, tagline_font, y, (255, 255, 255), line_gap=16)
        y += block_h + (SENTENCE_GAP if i < len(sentence_blocks) - 1 else 0)
    y += CTA_TAGLINE_GAP

    # Download line (softer color)
    _draw_centered_lines(draw, dl_lines, download_font, y, (148, 163, 184), line_gap=12)

    _render_chrome(draw, slide_index, total_slides, app_name, counter_color=COLOR_COUNTER_DARK)


def _render_value(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    slide_data: dict,
    slide_index: int,
    total_slides: int,
    app_name: str,
) -> None:
    label = slide_data.get("label", "DARE").upper()
    text = slide_data.get("text", "")
    intensity = slide_data.get("intensity", "mild").lower()

    badge_font = load_font(BADGE_FONT_SIZE, bold=True)
    text_font = load_font(CARD_TEXT_FONT_SIZE, bold=True)
    intensity_font = load_font(INTENSITY_FONT_SIZE, bold=True)

    card_w = WIDTH - 2 * CARD_MARGIN_X          # 920px
    text_max_w = card_w - 2 * CARD_PAD_X        # 800px
    cx = WIDTH // 2                              # horizontal center

    # Measure all card contents
    badge_h = _pill_height(draw, label, badge_font, BADGE_PAD_Y)
    text_lines = _wrap_text(draw, text, text_font, text_max_w)
    text_h = _text_block_height(draw, text_lines, text_font, 16)
    intensity_h = _pill_height(draw, intensity.upper(), intensity_font, INTENSITY_PAD_Y)

    card_content_h = (
        CARD_PAD_Y
        + badge_h
        + CARD_ITEM_GAP
        + text_h
        + CARD_ITEM_GAP
        + intensity_h
        + CARD_PAD_Y
    )

    # Center card vertically in usable area
    usable_top = SLIDE_NUM_MARGIN + 80
    usable_bottom = HEIGHT - SAFE_ZONE_BOTTOM
    card_y = max((usable_top + usable_bottom) // 2 - card_content_h // 2, usable_top)

    # Draw card
    draw.rounded_rectangle(
        [(CARD_MARGIN_X, card_y), (CARD_MARGIN_X + card_w, card_y + card_content_h)],
        radius=CARD_RADIUS,
        fill=CARD_COLOR,
    )

    y = card_y + CARD_PAD_Y

    # DARE / TRUTH badge
    y = _pill(draw, label, badge_font, cx, y, BADGE_COLOR, (255, 255, 255), BADGE_PAD_X, BADGE_PAD_Y)
    y += CARD_ITEM_GAP

    # Main text
    _draw_centered_lines(draw, text_lines, text_font, y, CARD_TEXT_COLOR, line_gap=16)
    y += text_h + CARD_ITEM_GAP

    # Intensity badge
    _pill(
        draw, intensity.upper(), intensity_font, cx, y,
        INTENSITY_COLORS.get(intensity, INTENSITY_COLORS["mild"]),
        (255, 255, 255), INTENSITY_PAD_X, INTENSITY_PAD_Y,
    )

    _render_chrome(draw, slide_index, total_slides, app_name, counter_color=COLOR_COUNTER_LIGHT)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_tod_slide(
    slide_data: dict,
    slide_index: int,
    total_slides: int,
    app_name: str,
    output_path: Path,
) -> None:
    slide_type = slide_data.get("type")
    label = slide_data.get("label", "DARE").upper()

    if slide_type in ("hook", "cta"):
        bg = BG_DARK
    elif label == "TRUTH":
        bg = BG_TRUTH
    else:
        bg = BG_DARE

    img = Image.new("RGB", (WIDTH, HEIGHT), color=bg)
    draw = ImageDraw.Draw(img)

    if slide_type == "hook":
        _render_hook(img, draw, slide_data, slide_index, total_slides, app_name)
    elif slide_type == "cta":
        _render_cta(img, draw, slide_data, slide_index, total_slides, app_name)
    else:
        _render_value(img, draw, slide_data, slide_index, total_slides, app_name)

    # Accent bar
    draw.rectangle([(0, HEIGHT - ACCENT_BAR_HEIGHT), (WIDTH, HEIGHT)], fill=ACCENT_PURPLE)

    img.save(output_path, "PNG")


def render_tod_carousel(data: dict, output_dir: Path, app_name: str = "Truth or Dare AI") -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    slides = [{"type": "hook", "text": data["hook"]}]
    for s in data["slides"]:
        slides.append({"type": "value", **s})
    slides.append({"type": "cta", "text": data["cta"]})

    total = len(slides)
    for i, slide in enumerate(slides, start=1):
        filename = output_dir / f"slide_{i:02d}.png"
        render_tod_slide(slide, i, total, app_name, filename)
        print(f"    slide {i:02d}/{total} → {filename.name}")
