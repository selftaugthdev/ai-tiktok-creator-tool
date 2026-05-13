"""Photo-overlay carousel renderer.

No slide counter, watermark, or accent bar — clean photo + text bubbles only.

Slide order:
  1. Hook (photo + hook bubble top + app logo/name bottom)
  2. Topic slide (app screenshot + "Topic →" bubble — always fixed)
  3–N-1. Value slides (photo + headline top + body bottom)
  N. CTA (app screenshot + dark overlay + logo + bubbles)
"""

import random
from pathlib import Path

from PIL import Image, ImageDraw

import carousel_renderer as _cr
from app_config import get_app_config
from carousel_renderer import (
    _draw_centered_lines,
    _draw_stars,
    _text_block_height,
    _wrap_text,
    load_font,
    MARGIN_X,
    WIDTH,
    HEIGHT,
    REVIEWS,
    ACCENT_COLOR,
)

PHOTOS_DIR = Path("photos")
# Fallback logo — used when app config logo is not found
_FALLBACK_LOGO_PATH = Path("assets") / "Migraine Cast LOGO DARK MODE.png"

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
HOOK_BUBBLE_Y = 230              # top of hook text bubble (below TikTok top chrome ~200px)
HOOK_BRANDING_BOTTOM = HEIGHT - 500  # bottom edge of logo+name block
HOOK_LOGO_W = 130
HOOK_LOGO_RADIUS = 26
HOOK_LOGO_GAP = 14               # gap between logo and app name bubble
HOOK_NAME_FONT_SIZE = 36

# ── Value slide positioning ───────────────────────────────────────────────────
VALUE_TOP_BUBBLE_Y = 230         # below TikTok top chrome ~200px
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
# Platform configuration
# ---------------------------------------------------------------------------

def configure_platform(cfg) -> None:
    """Update layout constants for the target platform. Call before rendering."""
    global HEIGHT, HOOK_BUBBLE_Y, VALUE_TOP_BUBBLE_Y
    global HOOK_BRANDING_BOTTOM, VALUE_BOTTOM_BUBBLE_BOTTOM, CTA_LOGO_Y
    _cr.configure_platform(cfg)
    HEIGHT = cfg.height
    # Top bubbles sit just below the platform's top chrome
    HOOK_BUBBLE_Y = cfg.safe_zone_top + 30
    VALUE_TOP_BUBBLE_Y = cfg.safe_zone_top + 30
    # Bottom-anchored elements sit just above the platform's bottom chrome
    HOOK_BRANDING_BOTTOM = cfg.height - cfg.safe_zone_bottom - 20
    VALUE_BOTTOM_BUBBLE_BOTTOM = cfg.height - cfg.safe_zone_bottom - 20
    # CTA logo sits below the top chrome with a small gap
    CTA_LOGO_Y = cfg.safe_zone_top + 60


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

_MIGRAINECAST_CTA_HEADLINE = "STOP BEING BLINDSIDED BY MIGRAINES"
_CALMSOS_CTA_HEADLINE = "YOU DON'T HAVE TO WHITE-KNUCKLE IT ALONE"

REVIEW_BUBBLE_QUOTE_SIZE = 40
REVIEW_BUBBLE_AUTHOR_SIZE = 32
REVIEW_BUBBLE_GAP = 16
REVIEW_BUBBLE_STAR_OUTER_R = 22
REVIEW_BUBBLE_STAR_INNER_R = 9


def _draw_review_bubble(draw: ImageDraw.ImageDraw, review: dict, y: int) -> int:
    """Draw a white review bubble with stars, quote, and author. Returns y after bubble."""
    text_max_w = BUBBLE_W - 2 * BUBBLE_PAD_X
    quote_font = load_font(REVIEW_BUBBLE_QUOTE_SIZE, bold=False)
    author_font = load_font(REVIEW_BUBBLE_AUTHOR_SIZE, bold=False)

    star_h = REVIEW_BUBBLE_STAR_OUTER_R * 2

    quote_lines = _wrap_text(draw, review["quote"], quote_font, text_max_w)
    quote_h = _text_block_height(draw, quote_lines, quote_font, BUBBLE_LINE_GAP)

    author_lines = _wrap_text(draw, review["author"], author_font, text_max_w)
    author_h = _text_block_height(draw, author_lines, author_font, BUBBLE_LINE_GAP)

    text_h = star_h + REVIEW_BUBBLE_GAP + quote_h + REVIEW_BUBBLE_GAP + author_h
    bubble_h = text_h + 2 * BUBBLE_PAD_Y

    draw.rounded_rectangle(
        [(MARGIN_X, y), (MARGIN_X + BUBBLE_W, y + bubble_h)],
        radius=BUBBLE_RADIUS,
        fill=BUBBLE_COLOR,
    )

    inner_y = y + BUBBLE_PAD_Y
    _draw_stars(draw, WIDTH // 2, inner_y, 5, REVIEW_BUBBLE_STAR_OUTER_R, REVIEW_BUBBLE_STAR_INNER_R, ACCENT_COLOR)
    inner_y += star_h + REVIEW_BUBBLE_GAP
    inner_y = _draw_centered_lines(draw, quote_lines, quote_font, inner_y, BUBBLE_TEXT_COLOR, line_gap=BUBBLE_LINE_GAP)
    inner_y += REVIEW_BUBBLE_GAP
    _draw_centered_lines(draw, author_lines, author_font, inner_y, (100, 100, 100), line_gap=BUBBLE_LINE_GAP)

    return y + bubble_h


def _render_homepage_cta(output_path: Path, app_name: str = "MigraineCast") -> None:
    """Final slide: homepage photo + headline bubble + review bubble + body bubble."""
    app_cfg = get_app_config(app_name)
    homepage_path = app_cfg["homepage_slide_path"]

    if homepage_path and homepage_path.exists():
        img = _load_and_crop(homepage_path)
    else:
        img = Image.new("RGB", (WIDTH, HEIGHT), (20, 20, 20))

    draw = ImageDraw.Draw(img)
    headline_font = load_font(VALUE_HEADLINE_SIZE, bold=True)
    body_font = load_font(VALUE_BODY_SIZE, bold=False)

    # Headline: app-specific
    if "calm" in app_name.lower():
        cta_headline = _CALMSOS_CTA_HEADLINE
    else:
        cta_headline = _MIGRAINECAST_CTA_HEADLINE

    y = _draw_bubble(draw, cta_headline, headline_font, VALUE_TOP_BUBBLE_Y)

    # Review bubble (skip if app has no reviews)
    available_reviews = app_cfg["reviews"] or REVIEWS
    if available_reviews:
        y += 50
        _draw_review_bubble(draw, random.choice(available_reviews), y)

    cta_body = app_cfg["cta_download_line"]
    body_bh = _bubble_height(draw, cta_body, body_font)
    _draw_bubble(draw, cta_body, body_font, VALUE_BOTTOM_BUBBLE_BOTTOM - body_bh)

    language_note = app_cfg.get("language_note", "")
    if language_note:
        note_font = load_font(32, bold=False)
        note_y = VALUE_BOTTOM_BUBBLE_BOTTOM + 24
        lines = _wrap_text(draw, language_note, note_font, BUBBLE_W)
        text_h = _text_block_height(draw, lines, note_font, 10)
        pad_y = 16
        box_h = text_h + 2 * pad_y
        box_overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(box_overlay).rounded_rectangle(
            [(MARGIN_X, note_y - pad_y), (MARGIN_X + BUBBLE_W, note_y - pad_y + box_h)],
            radius=14,
            fill=(20, 20, 20, 190),
        )
        img = Image.alpha_composite(img.convert("RGBA"), box_overlay).convert("RGB")
        draw = ImageDraw.Draw(img)
        _draw_centered_lines(draw, lines, note_font, note_y, (255, 255, 255), line_gap=10)

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

    app_cfg = get_app_config(app_name)
    logo_path = app_cfg["logo_path"] if app_cfg["logo_path"].exists() else _FALLBACK_LOGO_PATH
    if logo_path.exists():
        _paste_logo(img, logo_path, HOOK_LOGO_W, HOOK_LOGO_RADIUS, logo_y)

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
    app_cfg = get_app_config(app_name)
    cta_bg = app_cfg["app_screenshot_path"]

    if cta_bg and cta_bg.exists():
        img = _load_and_crop(cta_bg)
    else:
        img = Image.new("RGB", (WIDTH, HEIGHT), (15, 23, 42))

    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, CTA_OVERLAY_ALPHA))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    y = CTA_LOGO_Y
    logo_path = app_cfg["logo_path"] if app_cfg["logo_path"].exists() else _FALLBACK_LOGO_PATH
    if logo_path.exists():
        _paste_logo(img, logo_path, CTA_LOGO_W, CTA_LOGO_RADIUS, y)
        draw = ImageDraw.Draw(img)
        y += CTA_LOGO_W + CTA_LOGO_GAP

    y = _draw_bubble(draw, slide["headline"], load_font(CTA_HEADLINE_SIZE, bold=True), y)
    y += 32
    _draw_bubble(draw, slide["body"], load_font(CTA_BODY_SIZE, bold=False), y)

    img.save(output_path, "PNG")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

SANDRA_ASSETS_DIR = Path("assets")
# Hook bubble starts just below the vertical center so Sandra's face stays visible above.
_SANDRA_HOOK_Y_RATIO = 0.52

# ── App screenshot overlay slide ───────────────────────────────────────────────
_SCREENSHOT_LABEL_FONT_SIZE = 52
_SCREENSHOT_MAX_W = 700
_SCREENSHOT_CORNER_R = 20
_SCREENSHOT_LABEL_PAD_X = 44
_SCREENSHOT_LABEL_PAD_Y = 18


def _render_app_screenshot_slide(slide: dict, output_path: Path, app_name: str) -> None:
    """Pexels bg + accent label pill + white body bubble + app screenshot composited below."""
    from app_config import get_app_config
    app_cfg = get_app_config(app_name)
    accent = app_cfg.get("accent_color", (255, 107, 157))

    bg_rel = slide.get("background_photo", "")
    bg_path = PHOTOS_DIR / bg_rel if bg_rel else None
    if bg_path and bg_path.exists():
        img = _load_and_crop(bg_path)
    else:
        img = Image.new("RGB", (WIDTH, HEIGHT), (20, 20, 20))

    draw = ImageDraw.Draw(img)

    # Label pill (accent color bg, white text)
    label_font = load_font(_SCREENSHOT_LABEL_FONT_SIZE, bold=True)
    label_text = slide.get("label", "")
    bbox = draw.textbbox((0, 0), label_text, font=label_font)
    lw = bbox[2] - bbox[0]
    lh = bbox[3] - bbox[1]
    pill_w = lw + 2 * _SCREENSHOT_LABEL_PAD_X
    pill_h = lh + 2 * _SCREENSHOT_LABEL_PAD_Y
    pill_x = (WIDTH - pill_w) // 2
    pill_y = VALUE_TOP_BUBBLE_Y
    draw.rounded_rectangle(
        [(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)],
        radius=pill_h // 2,
        fill=accent,
    )
    draw.text(
        (WIDTH // 2, pill_y + _SCREENSHOT_LABEL_PAD_Y + lh // 2),
        label_text,
        font=label_font,
        fill=(255, 255, 255),
        anchor="mm",
    )
    y = pill_y + pill_h + 24

    # Body bubble
    body_font = load_font(VALUE_BODY_SIZE, bold=False)
    body_bh = _bubble_height(draw, slide["body"], body_font)
    _draw_bubble(draw, slide["body"], body_font, y)
    y += body_bh + 44

    # App screenshot composited below
    screenshot_path = SANDRA_ASSETS_DIR / slide["app_screenshot"]
    if screenshot_path.exists():
        ss = Image.open(screenshot_path).convert("RGBA")
        scale = _SCREENSHOT_MAX_W / ss.width
        new_w = _SCREENSHOT_MAX_W
        new_h = int(ss.height * scale)
        max_h = HEIGHT - y - 80
        if new_h > max_h:
            scale = max_h / ss.height
            new_w = int(ss.width * scale)
            new_h = max_h
        ss = ss.resize((new_w, new_h), Image.LANCZOS)
        mask = Image.new("L", (new_w, new_h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (new_w, new_h)], radius=_SCREENSHOT_CORNER_R, fill=255)
        x_off = (WIDTH - new_w) // 2
        img.paste(ss, (x_off, y), mask=mask)

    img.save(output_path, "PNG")


def _render_sandra_hook(hook_text: str, sandra_image: str, output_path: Path) -> None:
    """Slide 1: full-bleed Sandra photo with hook bubble in lower half."""
    img_path = SANDRA_ASSETS_DIR / sandra_image
    if img_path.exists():
        img = _load_and_crop(img_path)
    else:
        img = Image.new("RGB", (WIDTH, HEIGHT), (20, 20, 20))

    draw = ImageDraw.Draw(img)
    font = load_font(HOOK_FONT_SIZE, bold=True)
    bubble_y = int(HEIGHT * _SANDRA_HOOK_Y_RATIO)
    _draw_bubble(draw, hook_text, font, bubble_y)

    img.save(output_path, "PNG")


def _render_sandra_app_showcase(output_path: Path, app_name: str) -> None:
    """Second-to-last slide: clean app screenshot with tagline bubble at bottom."""
    from app_config import get_app_config
    app_cfg = get_app_config(app_name)
    homepage_path = app_cfg["homepage_slide_path"]

    if homepage_path and homepage_path.exists():
        img = _load_and_crop(homepage_path)
    else:
        img = Image.new("RGB", (WIDTH, HEIGHT), (20, 20, 20))

    # Light overlay keeps app UI visible
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 90))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(img)
    font = load_font(VALUE_HEADLINE_SIZE, bold=True)
    tagline = app_cfg.get("cta_tagline", "See your next migraine before it sees you.")
    bh = _bubble_height(draw, tagline, font)
    _draw_bubble(draw, tagline, font, VALUE_BOTTOM_BUBBLE_BOTTOM - bh)

    img.save(output_path, "PNG")


def render_sandra_carousel(hook: str, items: list, output_dir: Path, app_name: str) -> None:
    """Render a full Sandra-style carousel.

    items[0]   = {"sandra_image": "..."}                                   hook metadata
    items[1:-1] or items[1:] = value slides ({"headline", "body", "background_photo"})
    items[-1]  = {"app_screenshot": "...", "label": "...", "body": "...", "background_photo": "..."}
                 when an app screenshot slide is present (injected at mid-carousel position)

    Homepage CTA is always appended as the final slide.
    App showcase slide is replaced by the app screenshot slide when present.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    sandra_image = items[0].get("sandra_image", "Sandra Neutral look.jpg")
    remaining = items[1:]

    # Separate app screenshot slide from value slides
    screenshot_slide = None
    value_slides = []
    for item in remaining:
        if "app_screenshot" in item:
            screenshot_slide = item
        else:
            value_slides.append(item)

    # Inject screenshot as the last value slide (second-to-last before CTA)
    if screenshot_slide:
        value_slides.append(screenshot_slide)

    # If no screenshot slide, fall back to the app showcase
    use_showcase = screenshot_slide is None
    total = 1 + len(value_slides) + (1 if use_showcase else 0) + 1

    # Slide 1: hook
    path = output_dir / "slide_01.png"
    _render_sandra_hook(hook, sandra_image, path)
    print(f"    slide 01/{total:02d} → {path.name}  [{sandra_image}]")

    # Value slides (including screenshot slide if present)
    for idx, slide in enumerate(value_slides, start=2):
        path = output_dir / f"slide_{idx:02d}.png"
        if "app_screenshot" in slide:
            _render_app_screenshot_slide(slide, path, app_name)
            print(f"    slide {idx:02d}/{total:02d} → {path.name}  [app: {slide['app_screenshot']}]")
        else:
            _render_value(slide, path)
            print(f"    slide {idx:02d}/{total:02d} → {path.name}")

    # App showcase (only when no screenshot slide)
    if use_showcase:
        showcase_num = 1 + len(value_slides) + 1
        path = output_dir / f"slide_{showcase_num:02d}.png"
        _render_sandra_app_showcase(path, app_name)
        print(f"    slide {showcase_num:02d}/{total:02d} → {path.name}")

    # Homepage CTA (last)
    path = output_dir / f"slide_{total:02d}.png"
    _render_homepage_cta(path, app_name)
    print(f"    slide {total:02d}/{total:02d} → {path.name}")


def render_photo_carousel(slides: list, output_dir: Path, app_name: str, topic: str = "") -> None:
    """Render every slide. Injects topic slide after hook automatically."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build render queue: hook → value slides → homepage CTA (always fixed last)
    queue = [("ai", slide) for slide in slides] + [("homepage", None)]
    total = len(queue)

    for i, (kind, slide) in enumerate(queue, start=1):
        filename = output_dir / f"slide_{i:02d}.png"

        if kind == "homepage":
            _render_homepage_cta(filename, app_name)
        elif i == 1:
            _render_hook(slide, filename, app_name)
        else:
            _render_value(slide, filename)

        print(f"    slide {i:02d}/{total} → {filename.name}")
