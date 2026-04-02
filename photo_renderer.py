"""Photo-overlay carousel renderer.

No slide counter, watermark, or accent bar — clean photo + text bubbles only.

Slide order:
  1. Hook (photo + hook bubble top + app logo/name bottom)
  2. Topic slide (app screenshot + "Topic →" bubble — always fixed)
  3–N-1. Value slides (photo + headline top + body bottom)
  N. CTA (app screenshot + dark overlay + logo + bubbles)
"""

from pathlib import Path

from PIL import Image, ImageDraw

from carousel_renderer import (
    _draw_centered_lines,
    _text_block_height,
    _wrap_text,
    load_font,
    MARGIN_X,
    WIDTH,
    HEIGHT,
)

PHOTOS_DIR = Path("photos")
CTA_BG_PATH = Path("assets") / "Home Premium.png"
HOMEPAGE_SLIDE_PATH = Path("assets") / "MigraineCast Showing Home Page.jpg"
MC_LOGO_PATH = Path("assets") / "Migraine Cast LOGO DARK MODE.png"

# ── Bubble ────────────────────────────────────────────────────────────────────
BUBBLE_COLOR = (255, 255, 255)
BUBBLE_TEXT_COLOR = (15, 15, 15)
BUBBLE_RADIUS = 20
BUBBLE_W = WIDTH - 2 * MARGIN_X    # 920px
BUBBLE_PAD_X = 44
BUBBLE_PAD_Y = 30
BUBBLE_LINE_GAP = 14

# ── Font sizes ────────────────────────────────────────────────────────────────
HOOK_FONT_SIZE = 80
VALUE_HEADLINE_SIZE = 68
VALUE_BODY_SIZE = 52
TOPIC_FONT_SIZE = 62
CTA_HEADLINE_SIZE = 62
CTA_BODY_SIZE = 46

# ── Hook positioning ──────────────────────────────────────────────────────────
HOOK_BUBBLE_Y = 140              # top of hook text bubble
HOOK_BRANDING_BOTTOM = HEIGHT - 500  # bottom edge of logo+name block
HOOK_LOGO_W = 130
HOOK_LOGO_RADIUS = 26
HOOK_LOGO_GAP = 14               # gap between logo and app name bubble
HOOK_NAME_FONT_SIZE = 36

# ── Value slide positioning ───────────────────────────────────────────────────
VALUE_TOP_BUBBLE_Y = 120
VALUE_BOTTOM_BUBBLE_BOTTOM = HEIGHT - 500   # bottom bubble bottom edge

# ── Topic slide ───────────────────────────────────────────────────────────────
TOPIC_OVERLAY_ALPHA = 140        # slightly lighter than CTA so app UI shows through

# ── CTA slide ─────────────────────────────────────────────────────────────────
CTA_OVERLAY_ALPHA = 155
CTA_LOGO_W = 280
CTA_LOGO_RADIUS = 52
CTA_LOGO_Y = 260
CTA_LOGO_GAP = 56


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_and_crop(photo_path: Path) -> Image.Image:
    """Load photo, scale to fill 1080×1920, center-crop."""
    img = Image.open(photo_path).convert("RGB")
    scale = max(WIDTH / img.width, HEIGHT / img.height)
    new_w, new_h = int(img.width * scale), int(img.height * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    x_off = (new_w - WIDTH) // 2
    y_off = (new_h - HEIGHT) // 2
    return img.crop((x_off, y_off, x_off + WIDTH, y_off + HEIGHT))


def _bubble_height(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    lines = _wrap_text(draw, text, font, BUBBLE_W - 2 * BUBBLE_PAD_X)
    return _text_block_height(draw, lines, font, BUBBLE_LINE_GAP) + 2 * BUBBLE_PAD_Y


def _draw_bubble(draw: ImageDraw.ImageDraw, text: str, font, y: int) -> int:
    """Draw white bubble at y. Returns y after the bubble."""
    text_max_w = BUBBLE_W - 2 * BUBBLE_PAD_X
    lines = _wrap_text(draw, text, font, text_max_w)
    text_h = _text_block_height(draw, lines, font, BUBBLE_LINE_GAP)
    bubble_h = text_h + 2 * BUBBLE_PAD_Y

    draw.rounded_rectangle(
        [(MARGIN_X, y), (MARGIN_X + BUBBLE_W, y + bubble_h)],
        radius=BUBBLE_RADIUS,
        fill=BUBBLE_COLOR,
    )
    _draw_centered_lines(draw, lines, font, y + BUBBLE_PAD_Y, BUBBLE_TEXT_COLOR, line_gap=BUBBLE_LINE_GAP)
    return y + bubble_h


def _paste_logo(img: Image.Image, logo_path: Path, logo_w: int, logo_radius: int, y: int) -> None:
    """Composite a rounded-square logo onto img at the given y, centered horizontally."""
    logo = Image.open(logo_path).convert("RGBA")
    logo = logo.resize((logo_w, logo_w), Image.LANCZOS)
    mask = Image.new("L", (logo_w, logo_w), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (logo_w, logo_w)], radius=logo_radius, fill=255)
    img.paste(logo, ((WIDTH - logo_w) // 2, y), mask=mask)


# ---------------------------------------------------------------------------
# Slide renderers
# ---------------------------------------------------------------------------

HOMEPAGE_CTA_HEADLINE = "STOP BEING BLINDSIDED BY MIGRAINES"
HOMEPAGE_CTA_BODY = "Download MigraineCast on iOS. Link in bio."


def _render_homepage_cta(output_path: Path) -> None:
    """Final slide: homepage photo + fixed headline + body bubbles."""
    if HOMEPAGE_SLIDE_PATH.exists():
        img = _load_and_crop(HOMEPAGE_SLIDE_PATH)
    else:
        img = Image.new("RGB", (WIDTH, HEIGHT), (20, 20, 20))

    draw = ImageDraw.Draw(img)
    headline_font = load_font(VALUE_HEADLINE_SIZE, bold=True)
    body_font = load_font(VALUE_BODY_SIZE, bold=False)

    _draw_bubble(draw, HOMEPAGE_CTA_HEADLINE, headline_font, VALUE_TOP_BUBBLE_Y)

    body_bh = _bubble_height(draw, HOMEPAGE_CTA_BODY, body_font)
    _draw_bubble(draw, HOMEPAGE_CTA_BODY, body_font, VALUE_BOTTOM_BUBBLE_BOTTOM - body_bh)

    img.save(output_path, "PNG")


def _render_hook(slide: dict, output_path: Path, app_name: str) -> None:
    bg_rel = slide.get("background_photo", "")
    bg_path = PHOTOS_DIR / bg_rel if bg_rel else None

    if bg_path and bg_path.exists():
        img = _load_and_crop(bg_path)
    else:
        img = Image.new("RGB", (WIDTH, HEIGHT), (20, 20, 20))

    draw = ImageDraw.Draw(img)
    hook_font = load_font(HOOK_FONT_SIZE, bold=True)
    name_font = load_font(HOOK_NAME_FONT_SIZE, bold=True)

    # Hook bubble anchored to top
    _draw_bubble(draw, slide["headline"], hook_font, HOOK_BUBBLE_Y)

    # Branding block anchored to bottom: logo above app name bubble
    name_bh = _bubble_height(draw, app_name, name_font)
    logo_y = HOOK_BRANDING_BOTTOM - name_bh - HOOK_LOGO_GAP - HOOK_LOGO_W

    if MC_LOGO_PATH.exists():
        _paste_logo(img, MC_LOGO_PATH, HOOK_LOGO_W, HOOK_LOGO_RADIUS, logo_y)

    # Re-acquire draw after paste
    draw = ImageDraw.Draw(img)
    name_y = logo_y + HOOK_LOGO_W + HOOK_LOGO_GAP
    _draw_bubble(draw, app_name, name_font, name_y)

    img.save(output_path, "PNG")


def _render_topic_slide(topic: str, output_path: Path) -> None:
    """Fixed slide 2: app screenshot + 'Topic →' bubble to prompt swiping."""
    if CTA_BG_PATH.exists():
        img = _load_and_crop(CTA_BG_PATH)
    else:
        img = Image.new("RGB", (WIDTH, HEIGHT), (15, 23, 42))

    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, TOPIC_OVERLAY_ALPHA))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    font = load_font(TOPIC_FONT_SIZE, bold=True)
    topic_text = f"{topic} \u2192"   # → arrow

    bh = _bubble_height(draw, topic_text, font)
    y = (HEIGHT // 2) - (bh // 2)
    _draw_bubble(draw, topic_text, font, y)

    img.save(output_path, "PNG")


def _render_value(slide: dict, output_path: Path) -> None:
    bg_rel = slide.get("background_photo", "")
    bg_path = PHOTOS_DIR / bg_rel if bg_rel else None

    if bg_path and bg_path.exists():
        img = _load_and_crop(bg_path)
    else:
        img = Image.new("RGB", (WIDTH, HEIGHT), (20, 20, 20))

    draw = ImageDraw.Draw(img)
    headline_font = load_font(VALUE_HEADLINE_SIZE, bold=True)
    body_font = load_font(VALUE_BODY_SIZE, bold=False)

    # Top bubble — headline
    _draw_bubble(draw, slide["headline"], headline_font, VALUE_TOP_BUBBLE_Y)

    # Bottom bubble — body, anchored so its bottom = VALUE_BOTTOM_BUBBLE_BOTTOM
    body_bh = _bubble_height(draw, slide["body"], body_font)
    _draw_bubble(draw, slide["body"], body_font, VALUE_BOTTOM_BUBBLE_BOTTOM - body_bh)

    img.save(output_path, "PNG")


def _render_cta(slide: dict, output_path: Path, app_name: str) -> None:
    if CTA_BG_PATH.exists():
        img = _load_and_crop(CTA_BG_PATH)
    else:
        img = Image.new("RGB", (WIDTH, HEIGHT), (15, 23, 42))

    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, CTA_OVERLAY_ALPHA))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    y = CTA_LOGO_Y
    if MC_LOGO_PATH.exists():
        _paste_logo(img, MC_LOGO_PATH, CTA_LOGO_W, CTA_LOGO_RADIUS, y)
        draw = ImageDraw.Draw(img)
        y += CTA_LOGO_W + CTA_LOGO_GAP

    y = _draw_bubble(draw, slide["headline"], load_font(CTA_HEADLINE_SIZE, bold=True), y)
    y += 32
    _draw_bubble(draw, slide["body"], load_font(CTA_BODY_SIZE, bold=False), y)

    img.save(output_path, "PNG")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_photo_carousel(slides: list, output_dir: Path, app_name: str, topic: str = "") -> None:
    """Render every slide. Injects topic slide after hook automatically."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build render queue: hook → value slides → homepage CTA (always fixed last)
    queue = [("ai", slide) for slide in slides] + [("homepage", None)]
    total = len(queue)

    for i, (kind, slide) in enumerate(queue, start=1):
        filename = output_dir / f"slide_{i:02d}.png"

        if kind == "homepage":
            _render_homepage_cta(filename)
        elif i == 1:
            _render_hook(slide, filename, app_name)
        else:
            _render_value(slide, filename)

        print(f"    slide {i:02d}/{total} → {filename.name}")
