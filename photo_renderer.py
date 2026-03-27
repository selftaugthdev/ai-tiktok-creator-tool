"""Photo-overlay carousel renderer.

No slide counter, watermark, or accent bar — clean photo + text bubbles only.
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
CTA_HEADLINE_SIZE = 62
CTA_BODY_SIZE = 46

# ── Positioning ───────────────────────────────────────────────────────────────
# Hook: bubble centered vertically
# Value: top bubble anchored high, bottom bubble anchored low — photo breathes in middle
VALUE_TOP_BUBBLE_Y = 120       # top bubble top edge
VALUE_BOTTOM_BUBBLE_BOTTOM = HEIGHT - 500  # bottom bubble bottom edge (above TikTok caption zone)

# CTA
CTA_OVERLAY_ALPHA = 155        # 0-255 darkness of overlay over app screenshot
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
    """Return the pixel height a bubble would be for this text + font."""
    lines = _wrap_text(draw, text, font, BUBBLE_W - 2 * BUBBLE_PAD_X)
    return _text_block_height(draw, lines, font, BUBBLE_LINE_GAP) + 2 * BUBBLE_PAD_Y


def _draw_bubble(draw: ImageDraw.ImageDraw, text: str, font, y: int) -> int:
    """Draw white bubble at y. Returns y-coordinate after the bubble."""
    bx = MARGIN_X
    text_max_w = BUBBLE_W - 2 * BUBBLE_PAD_X
    lines = _wrap_text(draw, text, font, text_max_w)
    text_h = _text_block_height(draw, lines, font, BUBBLE_LINE_GAP)
    bubble_h = text_h + 2 * BUBBLE_PAD_Y

    draw.rounded_rectangle(
        [(bx, y), (bx + BUBBLE_W, y + bubble_h)],
        radius=BUBBLE_RADIUS,
        fill=BUBBLE_COLOR,
    )
    _draw_centered_lines(draw, lines, font, y + BUBBLE_PAD_Y, BUBBLE_TEXT_COLOR, line_gap=BUBBLE_LINE_GAP)
    return y + bubble_h


# ---------------------------------------------------------------------------
# Slide renderers
# ---------------------------------------------------------------------------

def _render_hook(slide: dict, output_path: Path) -> None:
    bg_rel = slide.get("background_photo", "")
    bg_path = PHOTOS_DIR / bg_rel if bg_rel else None

    if bg_path and bg_path.exists():
        img = _load_and_crop(bg_path)
    else:
        img = Image.new("RGB", (WIDTH, HEIGHT), (20, 20, 20))

    draw = ImageDraw.Draw(img)
    font = load_font(HOOK_FONT_SIZE, bold=True)

    # Center bubble vertically
    bh = _bubble_height(draw, slide["headline"], font)
    y = (HEIGHT // 2) - (bh // 2)
    _draw_bubble(draw, slide["headline"], font, y)

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

    # Top bubble — headline, anchored high
    _draw_bubble(draw, slide["headline"], headline_font, VALUE_TOP_BUBBLE_Y)

    # Bottom bubble — body, anchored low so photo breathes in the middle
    body_bh = _bubble_height(draw, slide["body"], body_font)
    body_y = VALUE_BOTTOM_BUBBLE_BOTTOM - body_bh
    _draw_bubble(draw, slide["body"], body_font, body_y)

    img.save(output_path, "PNG")


def _render_cta(slide: dict, output_path: Path, app_name: str) -> None:
    # Background: app screenshot with dark overlay
    if CTA_BG_PATH.exists():
        img = _load_and_crop(CTA_BG_PATH)
    else:
        img = Image.new("RGB", (WIDTH, HEIGHT), (15, 23, 42))

    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, CTA_OVERLAY_ALPHA))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Logo
    y = CTA_LOGO_Y
    if MC_LOGO_PATH.exists():
        logo = Image.open(MC_LOGO_PATH).convert("RGBA")
        logo = logo.resize((CTA_LOGO_W, CTA_LOGO_W), Image.LANCZOS)
        mask = Image.new("L", (CTA_LOGO_W, CTA_LOGO_W), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), (CTA_LOGO_W, CTA_LOGO_W)], radius=CTA_LOGO_RADIUS, fill=255)
        img.paste(logo, ((WIDTH - CTA_LOGO_W) // 2, y), mask=mask)
        y += CTA_LOGO_W + CTA_LOGO_GAP

    headline_font = load_font(CTA_HEADLINE_SIZE, bold=True)
    body_font = load_font(CTA_BODY_SIZE, bold=False)

    y = _draw_bubble(draw, slide["headline"], headline_font, y)
    y += 32
    _draw_bubble(draw, slide["body"], body_font, y)

    img.save(output_path, "PNG")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_photo_carousel(slides: list, output_dir: Path, app_name: str) -> None:
    """Render every slide and save PNGs into output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    total = len(slides)

    for i, slide in enumerate(slides, start=1):
        filename = output_dir / f"slide_{i:02d}.png"

        if i == 1:
            _render_hook(slide, filename)
        elif i == total:
            _render_cta(slide, filename, app_name)
        else:
            _render_value(slide, filename)

        print(f"    slide {i:02d}/{total} → {filename.name}")
