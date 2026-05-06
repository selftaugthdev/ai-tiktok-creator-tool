import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app_config import get_app_config
from chart_generator import generate_chart_image

# Canvas dimensions (TikTok portrait)
WIDTH = 1080
HEIGHT = 1920

# Colour palette
BG_COLOR = (250, 218, 221)      # #FADADD soft pink
ACCENT_COLOR = (255, 107, 157)  # #FF6B9D hot pink
COLOR_HEADLINE = (45, 45, 45)   # #2D2D2D
COLOR_BODY = (85, 85, 85)       # #555555
COLOR_WATERMARK = (255, 107, 157)  # #FF6B9D hot pink

# Layout constants
MARGIN_X = 80
ACCENT_BAR_HEIGHT = 12
PADDING_BOTTOM = 80
SLIDE_NUM_MARGIN = 60
ILLUS_MAX_W = 600
ILLUS_MAX_H = 600

# Platform safe zones (UI chrome that overlaps the image) — defaults are TikTok
SAFE_ZONE_TOP = 200     # status bar + nav tabs at top
SAFE_ZONE_RIGHT = 160   # engagement buttons on right (~15% of 1080)
SAFE_ZONE_BOTTOM = 480  # caption/description overlay (~25% of 1920)

# Mascot constants
MASCOT_DIR = Path("assets")
MASCOT_W = 280
MASCOT_PAD_X = 60
MASCOT_PAD_Y = 20
VALID_EXPRESSIONS = {"calm", "default", "sad", "smug", "stormy", "warning"}

# App logo (CTA slide) — resolved per app at render time via get_app_config()
MC_LOGO_W = 280
MC_LOGO_RADIUS = 52
MC_LOGO_GAP = 40   # gap between logo and headline

# Testimonial / review (CTA slide)
TESTIMONIAL_FONT_SIZE = 36
TESTIMONIAL_PAD_X = 40
TESTIMONIAL_PAD_Y = 22
TESTIMONIAL_BG = (255, 200, 215)   # slightly deeper pink
REVIEW_STAR_OUTER_R = 26   # outer radius of each star point (diameter = 52px)
REVIEW_STAR_INNER_R = 11   # inner radius (valley between points)
REVIEW_AUTHOR_SIZE = 30

# CTA slide primary/secondary calls to action
CTA_PRIMARY_FONT_SIZE = 52
CTA_PRIMARY_PILL_PY = 22   # vertical padding inside the pill
CTA_PRIMARY_PILL_GAP = 44  # gap between testimonial block and primary CTA pill
CTA_SECONDARY_FONT_SIZE = 38
CTA_SECONDARY_GAP = 20     # gap between primary pill and secondary CTA text
# Default reviews — used as fallback when app config has none
REVIEWS = [
    {
        "quote": "\u201cAll of my migraines were in line with high or medium risk days on the app.\u201d",
        "author": "\u2014 Selen_B_D, App Store",
    },
    {
        "quote": "\u201cI was sceptical at first, but the weather does have impact on my migraine, a lot more than I had ever thought possible. This app has become my daily go-to.\u201d",
        "author": "\u2014 Winter-flowers-in-summer, App Store",
    },
]

# Infographic constants
INFOGRAPHIC_CELL_W = 240
INFOGRAPHIC_COL_GAP = 40
INFOGRAPHIC_CIRCLE_D = 120
INFOGRAPHIC_EMOJI_SIZE = 52
INFOGRAPHIC_LABEL_SIZE = 36
INFOGRAPHIC_LABEL_GAP = 20
INFOGRAPHIC_ROW_GAP = 40
INFOGRAPHIC_SUBTITLE_PY = 18
INFOGRAPHIC_SUBTITLE_PX = 40
INFOGRAPHIC_GRID_TOP_GAP = 40
INFOGRAPHIC_HEADLINE_GAP = 50
INFOGRAPHIC_SUBTITLE_SIZE = 43
INFOGRAPHIC_CIRCLE_FILL = (255, 182, 210)  # lighter pink for icon circles


# ---------------------------------------------------------------------------
# Platform configuration
# ---------------------------------------------------------------------------

def configure_platform(cfg) -> None:
    """Update module-level layout constants for the target platform.
    Call this before rendering when using a non-default platform."""
    global WIDTH, HEIGHT, SAFE_ZONE_TOP, SAFE_ZONE_RIGHT, SAFE_ZONE_BOTTOM
    WIDTH = cfg.width
    HEIGHT = cfg.height
    SAFE_ZONE_TOP = cfg.safe_zone_top
    SAFE_ZONE_RIGHT = cfg.safe_zone_right
    SAFE_ZONE_BOTTOM = cfg.safe_zone_bottom


def configure_app(app_cfg: dict) -> None:
    """Update module-level color constants for the target app.
    Call this before rendering alongside configure_platform."""
    global BG_COLOR, ACCENT_COLOR, COLOR_HEADLINE, COLOR_BODY
    global COLOR_WATERMARK, TESTIMONIAL_BG, INFOGRAPHIC_CIRCLE_FILL
    BG_COLOR               = app_cfg["bg_color"]
    ACCENT_COLOR           = app_cfg["accent_color"]
    COLOR_HEADLINE         = app_cfg["text_headline_color"]
    COLOR_BODY             = app_cfg["text_body_color"]
    COLOR_WATERMARK        = app_cfg["watermark_color"]
    TESTIMONIAL_BG         = app_cfg["testimonial_bg_color"]
    INFOGRAPHIC_CIRCLE_FILL = app_cfg["infographic_circle_color"]


# ---------------------------------------------------------------------------
# Font loading
# ---------------------------------------------------------------------------

def _try_font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except (OSError, IOError):
        return None


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Try to load a decent font; fall back to PIL's built-in default."""

    # 1. Look for fonts bundled with the project
    local_name = "Bold.ttf" if bold else "Regular.ttf"
    local = _try_font(str(Path("fonts") / local_name), size)
    if local:
        return local

    # 2. Common macOS paths
    macos_bold = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    macos_regular = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]

    # 3. Common Linux paths
    linux_bold = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    linux_regular = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]

    # 4. Windows paths
    win_bold = ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/calibrib.ttf"]
    win_regular = ["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/calibri.ttf"]

    candidates = (
        (macos_bold if bold else macos_regular)
        + (linux_bold if bold else linux_regular)
        + (win_bold if bold else win_regular)
    )

    for path in candidates:
        font = _try_font(path, size)
        if font:
            return font

    # Last resort — PIL built-in (no size control)
    return ImageFont.load_default()


def _load_emoji_font(size: int) -> ImageFont.ImageFont:
    """Load a color emoji font, falling back to regular."""
    emoji_candidates = [
        "/System/Library/Fonts/Apple Color Emoji.ttc",
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        "/usr/share/fonts/truetype/noto/NotoEmoji-Regular.ttf",
    ]
    for path in emoji_candidates:
        f = _try_font(path, size)
        if f:
            return f
    return load_font(size, bold=False)


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list:
    """Break text into lines that fit within max_width pixels."""
    words = text.split()
    lines = []
    current = []

    for word in words:
        test = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] > max_width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)

    if current:
        lines.append(" ".join(current))
    return lines


def _text_block_height(draw: ImageDraw.ImageDraw, lines: list, font: ImageFont.ImageFont, line_gap: int) -> int:
    """Return total pixel height of a block of wrapped lines."""
    if not lines:
        return 0
    sample_bbox = draw.textbbox((0, 0), "Ag", font=font)
    line_h = sample_bbox[3] - sample_bbox[1]
    return line_h * len(lines) + line_gap * (len(lines) - 1)


def _draw_centered_lines(
    draw: ImageDraw.ImageDraw,
    lines: list,
    font: ImageFont.ImageFont,
    y_start: int,
    color: tuple,
    line_gap: int = 12,
) -> int:
    """Draw lines centred horizontally; return the y-coordinate after the block."""
    sample_bbox = draw.textbbox((0, 0), "Ag", font=font)
    line_h = sample_bbox[3] - sample_bbox[1]

    y = y_start
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (WIDTH - text_w) // 2
        draw.text((x, y), line, font=font, fill=color)
        y += line_h + line_gap

    return y


def _split_sentences(text: str) -> list:
    """Split text into individual sentences on . ! ? boundaries."""
    import re
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in parts if s.strip()]


def _draw_stars(
    draw: ImageDraw.ImageDraw,
    cx: int,
    y: int,
    count: int,
    outer_r: int,
    inner_r: int,
    color: tuple,
) -> None:
    """Draw `count` filled 5-pointed star polygons horizontally centered at cx."""
    star_diam = outer_r * 2
    gap = 12
    total_w = count * star_diam + (count - 1) * gap
    x_start = cx - total_w // 2

    for i in range(count):
        sx = x_start + i * (star_diam + gap) + outer_r
        sy = y + outer_r
        pts = []
        for j in range(5):
            a_out = math.radians(-90 + j * 72)
            pts.append((sx + outer_r * math.cos(a_out), sy + outer_r * math.sin(a_out)))
            a_in = math.radians(-90 + j * 72 + 36)
            pts.append((sx + inner_r * math.cos(a_in), sy + inner_r * math.sin(a_in)))
        draw.polygon(pts, fill=color)


def _infographic_grid_height(num_items: int, label_line_h: int = 42) -> int:
    """Estimate pixel height of the infographic emoji grid."""
    cols = 3
    rows = (num_items + cols - 1) // cols
    row_h = INFOGRAPHIC_CIRCLE_D + INFOGRAPHIC_LABEL_GAP + label_line_h * 2 + 8 + INFOGRAPHIC_ROW_GAP
    return rows * row_h - INFOGRAPHIC_ROW_GAP  # no trailing gap after last row


# ---------------------------------------------------------------------------
# Infographic layout
# ---------------------------------------------------------------------------

def _render_infographic_body(
    draw: ImageDraw.ImageDraw,
    img: Image.Image,
    items: list,
    subtitle: str,
    y_start: int,
    subtitle_font: ImageFont.ImageFont,
    label_font: ImageFont.ImageFont,
) -> None:
    """Draw subtitle pill + 3-column emoji icon grid."""
    emoji_font = _load_emoji_font(INFOGRAPHIC_EMOJI_SIZE)

    # ── Subtitle pill ────────────────────────────────────────────────────────
    sub_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    sub_w = sub_bbox[2] - sub_bbox[0]
    pill_w = sub_w + INFOGRAPHIC_SUBTITLE_PX * 2
    pill_h = sub_bbox[1] + sub_bbox[3] + INFOGRAPHIC_SUBTITLE_PY * 2
    pill_x = (WIDTH - pill_w) // 2
    pill_y = y_start

    draw.rounded_rectangle(
        [(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)],
        radius=pill_h // 2,
        fill=ACCENT_COLOR,
    )
    draw.text(
        (pill_x + INFOGRAPHIC_SUBTITLE_PX, pill_y + INFOGRAPHIC_SUBTITLE_PY),
        subtitle,
        font=subtitle_font,
        fill=(255, 255, 255),
    )

    y = pill_y + pill_h + INFOGRAPHIC_GRID_TOP_GAP

    # ── Emoji grid ───────────────────────────────────────────────────────────
    cols = 3
    total_grid_w = cols * INFOGRAPHIC_CELL_W + (cols - 1) * INFOGRAPHIC_COL_GAP
    # Center within the horizontal safe zone (left margin → safe right edge)
    safe_area_w = WIDTH - MARGIN_X - SAFE_ZONE_RIGHT  # 1080-80-160 = 840px
    grid_x_start = MARGIN_X + max(0, (safe_area_w - total_grid_w) // 2)

    sample_lb = draw.textbbox((0, 0), "Ag", font=label_font)
    label_line_h = sample_lb[3] - sample_lb[1]
    row_h = INFOGRAPHIC_CIRCLE_D + INFOGRAPHIC_LABEL_GAP + label_line_h * 2 + 8 + INFOGRAPHIC_ROW_GAP

    for idx, item in enumerate(items[:6]):
        col = idx % cols
        row = idx // cols
        cell_x = grid_x_start + col * (INFOGRAPHIC_CELL_W + INFOGRAPHIC_COL_GAP)
        cell_y = y + row * row_h
        cx = cell_x + INFOGRAPHIC_CELL_W // 2

        # Circle background
        r = INFOGRAPHIC_CIRCLE_D // 2
        draw.ellipse(
            [(cx - r, cell_y), (cx + r, cell_y + INFOGRAPHIC_CIRCLE_D)],
            fill=INFOGRAPHIC_CIRCLE_FILL,
        )

        # Emoji centered in circle
        emoji = item.get("emoji", "")
        if emoji:
            e_bbox = draw.textbbox((0, 0), emoji, font=emoji_font)
            e_w = e_bbox[2] - e_bbox[0]
            e_h = e_bbox[3] - e_bbox[1]
            e_x = cx - e_w // 2
            e_y = cell_y + (INFOGRAPHIC_CIRCLE_D - e_h) // 2
            try:
                draw.text((e_x, e_y), emoji, font=emoji_font, fill=(45, 45, 45), embedded_color=True)
            except TypeError:
                draw.text((e_x, e_y), emoji, font=emoji_font, fill=(45, 45, 45))

        # Label below circle
        label = item.get("label", "")
        if label:
            label_lines = _wrap_text(draw, label, label_font, INFOGRAPHIC_CELL_W)
            label_y = cell_y + INFOGRAPHIC_CIRCLE_D + INFOGRAPHIC_LABEL_GAP
            for line in label_lines:
                lb = draw.textbbox((0, 0), line, font=label_font)
                lw = lb[2] - lb[0]
                draw.text((cx - lw // 2, label_y), line, font=label_font, fill=COLOR_BODY)
                label_y += label_line_h + 8


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_slide(
    slide: dict,
    slide_index: int,
    total_slides: int,
    app_name: str,
    output_path: Path,
    illustration_path: Path = None,
    mascot_expression: str = "default",
) -> None:
    """Render a single slide and save it as a PNG."""
    app_cfg = get_app_config(app_name)

    img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    headline_font = load_font(88, bold=True)
    body_font = load_font(48, bold=False)
    counter_font = load_font(38, bold=False)
    watermark_font = load_font(34, bold=False)

    available_width = WIDTH - 2 * MARGIN_X

    # ── Slide counter (top-right, hot pink) ──────────────────────────────────
    counter_text = f"{slide_index} / {total_slides}"
    cb = draw.textbbox((0, 0), counter_text, font=counter_font)
    counter_w = cb[2] - cb[0]
    draw.text(
        (WIDTH - SLIDE_NUM_MARGIN - counter_w, SLIDE_NUM_MARGIN),
        counter_text,
        font=counter_font,
        fill=ACCENT_COLOR,
    )

    # ── Usable area (respects platform safe zones) ───────────────────────────
    usable_top = SAFE_ZONE_TOP
    usable_bottom = HEIGHT - SAFE_ZONE_BOTTOM

    if "screenshot_path" in slide:
        # ── Screenshot layout ─────────────────────────────────────────────────
        try:
            ss = Image.open(slide["screenshot_path"]).convert("RGBA")
            # Scale to fill full width; crop top/bottom if taller than canvas
            scale = WIDTH / ss.width
            new_h = int(ss.height * scale)
            ss = ss.resize((WIDTH, new_h), Image.LANCZOS)
            if new_h > HEIGHT:
                crop_y = (new_h - HEIGHT) // 2
                ss = ss.crop((0, crop_y, WIDTH, crop_y + HEIGHT))
                img.paste(ss, (0, 0), mask=ss.split()[3])
            else:
                y_offset = (HEIGHT - new_h) // 2
                img.paste(ss, (0, y_offset), mask=ss.split()[3])
        except Exception as exc:
            print(f"  Warning: could not load screenshot {slide['screenshot_path']}: {exc}")

    elif "items" in slide:
        # ── Infographic layout ────────────────────────────────────────────────
        headline_lines = _wrap_text(draw, slide["headline"], headline_font, available_width)
        headline_h = _text_block_height(draw, headline_lines, headline_font, 16)
        items = slide.get("items", [])
        subtitle = slide.get("subtitle", "")
        subtitle_font = load_font(INFOGRAPHIC_SUBTITLE_SIZE, bold=True)
        label_font = load_font(INFOGRAPHIC_LABEL_SIZE, bold=False)

        sub_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        pill_h = sub_bbox[1] + sub_bbox[3] + INFOGRAPHIC_SUBTITLE_PY * 2

        sample_lb = draw.textbbox((0, 0), "Ag", font=label_font)
        label_line_h = sample_lb[3] - sample_lb[1]
        grid_h = _infographic_grid_height(len(items), label_line_h)

        total_h = (
            headline_h
            + INFOGRAPHIC_HEADLINE_GAP
            + pill_h
            + INFOGRAPHIC_GRID_TOP_GAP
            + grid_h
        )
        block_top = max((usable_top + usable_bottom) // 2 - total_h // 2, usable_top)

        # Accent pip above headline
        pip_y = block_top - 36
        if pip_y >= usable_top - 10:
            draw.rectangle(
                [(WIDTH // 2 - 60, pip_y), (WIDTH // 2 + 60, pip_y + 6)],
                fill=ACCENT_COLOR,
            )

        # Headline
        y = block_top
        y = _draw_centered_lines(draw, headline_lines, headline_font, y, COLOR_HEADLINE, line_gap=16)
        y += INFOGRAPHIC_HEADLINE_GAP

        # Subtitle pill + emoji grid
        _render_infographic_body(draw, img, items, subtitle, y, subtitle_font, label_font)

    else:
        # ── Regular layout ────────────────────────────────────────────────────
        is_cta = slide_index == total_slides
        headline_lines = _wrap_text(draw, slide["headline"], headline_font, available_width)
        headline_h = _text_block_height(draw, headline_lines, headline_font, 16)

        # Non-CTA slides: measure body text
        body_lines = []
        body_h = 0
        if not is_cta:
            body_lines = _wrap_text(draw, slide.get("body", ""), body_font, available_width)
            body_h = _text_block_height(draw, body_lines, body_font, 14)

        # CTA slide: testimonial + two-CTA block
        review = None
        testimonial_lines = []
        testimonial_h = 0
        testimonial_font = None
        author_font = None
        primary_cta_font = None
        secondary_cta_font = None
        secondary_cta_lines = []
        primary_cta_pill_h = 0
        secondary_cta_h = 0
        if is_cta:
            available_reviews = app_cfg["reviews"] or REVIEWS
            review = random.choice(available_reviews)
            testimonial_font = load_font(TESTIMONIAL_FONT_SIZE, bold=False)
            author_font = load_font(REVIEW_AUTHOR_SIZE, bold=False)
            testimonial_lines = _wrap_text(
                draw, review["quote"], testimonial_font,
                available_width - TESTIMONIAL_PAD_X * 2,
            )
            author_bbox = draw.textbbox((0, 0), review["author"], font=author_font)
            star_h = REVIEW_STAR_OUTER_R * 2
            author_h = author_bbox[3] - author_bbox[1]
            quote_h = _text_block_height(draw, testimonial_lines, testimonial_font, 12)
            text_h = star_h + 12 + quote_h + 12 + author_h
            testimonial_h = text_h + TESTIMONIAL_PAD_Y * 2

            primary_cta_font = load_font(CTA_PRIMARY_FONT_SIZE, bold=True)
            pcta_bbox = draw.textbbox((0, 0), app_cfg["cta_follow_line"], font=primary_cta_font)
            pcta_line_h = pcta_bbox[3] - pcta_bbox[1]
            primary_cta_pill_h = pcta_line_h + CTA_PRIMARY_PILL_PY * 2

            secondary_cta_font = load_font(CTA_SECONDARY_FONT_SIZE, bold=False)
            secondary_cta_lines = _wrap_text(
                draw, app_cfg["cta_download_line"], secondary_cta_font, available_width,
            )
            secondary_cta_h = _text_block_height(draw, secondary_cta_lines, secondary_cta_font, 12)

        # Resolve visual element — chart takes priority over illustration (non-CTA only)
        visual_img = None
        if not is_cta:
            chart_data = slide.get("chart_data")
            if chart_data:
                visual_img = generate_chart_image(chart_data)
            elif illustration_path:
                visual_img = Image.open(illustration_path).convert("RGBA")
                visual_img.thumbnail((ILLUS_MAX_W, ILLUS_MAX_H), Image.LANCZOS)

        # Load logo for CTA slide
        mc_logo_img = None
        logo_path = app_cfg["logo_path"]
        if is_cta and logo_path.exists():
            mc_logo_img = Image.open(logo_path).convert("RGBA")
            mc_logo_img = mc_logo_img.resize((MC_LOGO_W, MC_LOGO_W), Image.LANCZOS)

        # Calculate total content block height
        block_gap = 60 if visual_img else 80
        testimonial_gap = 40
        logo_prefix_h = (MC_LOGO_W + MC_LOGO_GAP) if mc_logo_img else 0
        if visual_img:
            total_h = headline_h + block_gap + visual_img.height + block_gap + body_h
        elif is_cta:
            total_h = (
                logo_prefix_h
                + headline_h
                + testimonial_gap
                + testimonial_h
                + CTA_PRIMARY_PILL_GAP
                + primary_cta_pill_h
                + CTA_SECONDARY_GAP
                + secondary_cta_h
            )
        else:
            total_h = headline_h + block_gap + body_h

        block_top = max((usable_top + usable_bottom) // 2 - total_h // 2, usable_top)

        # Logo (CTA slide, above headline)
        y = block_top
        if mc_logo_img:
            mask = Image.new("L", (MC_LOGO_W, MC_LOGO_W), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle([(0, 0), (MC_LOGO_W, MC_LOGO_W)], radius=MC_LOGO_RADIUS, fill=255)
            logo_x = (WIDTH - MC_LOGO_W) // 2
            img.paste(mc_logo_img, (logo_x, y), mask=mask)
            y += MC_LOGO_W + MC_LOGO_GAP

        # Accent pip above headline
        pip_y = y - 36
        if pip_y >= usable_top - 10:
            draw.rectangle(
                [(WIDTH // 2 - 60, pip_y), (WIDTH // 2 + 60, pip_y + 6)],
                fill=ACCENT_COLOR,
            )

        # Headline
        y = _draw_centered_lines(draw, headline_lines, headline_font, y, COLOR_HEADLINE, line_gap=16)
        y += block_gap if not is_cta else testimonial_gap

        if is_cta:
            # ── Review block ─────────────────────────────────────────────────
            if review:
                rect_x = MARGIN_X
                draw.rounded_rectangle(
                    [(rect_x, y), (rect_x + available_width, y + testimonial_h)],
                    radius=20,
                    fill=TESTIMONIAL_BG,
                )
                inner_y = y + TESTIMONIAL_PAD_Y
                _draw_stars(draw, WIDTH // 2, inner_y, 5, REVIEW_STAR_OUTER_R, REVIEW_STAR_INNER_R, ACCENT_COLOR)
                inner_y += REVIEW_STAR_OUTER_R * 2 + 12
                inner_y = _draw_centered_lines(draw, testimonial_lines, testimonial_font, inner_y, COLOR_BODY, line_gap=12)
                inner_y += 12
                ab = draw.textbbox((0, 0), review["author"], font=author_font)
                draw.text(((WIDTH - (ab[2] - ab[0])) // 2, inner_y), review["author"], font=author_font, fill=COLOR_BODY)
                y += testimonial_h

            y += CTA_PRIMARY_PILL_GAP

            # ── Primary CTA pill ("Follow for daily migraine tips") ───────────
            pcta_bbox2 = draw.textbbox((0, 0), app_cfg["cta_follow_line"], font=primary_cta_font)
            pcta_line_h = pcta_bbox2[3] - pcta_bbox2[1]
            draw.rounded_rectangle(
                [(MARGIN_X, y), (MARGIN_X + available_width, y + primary_cta_pill_h)],
                radius=primary_cta_pill_h // 2,
                fill=ACCENT_COLOR,
            )
            pcta_w = pcta_bbox2[2] - pcta_bbox2[0]
            pcta_x = (WIDTH - pcta_w) // 2
            pcta_y = y + (primary_cta_pill_h - pcta_line_h) // 2
            draw.text((pcta_x, pcta_y), app_cfg["cta_follow_line"], font=primary_cta_font, fill=(255, 255, 255))
            y += primary_cta_pill_h + CTA_SECONDARY_GAP

            # ── Secondary CTA ("Download ... Link in bio. URL") ───────────────
            _draw_centered_lines(draw, secondary_cta_lines, secondary_cta_font, y, COLOR_BODY, line_gap=12)

        else:
            # Visual (chart or illustration)
            if visual_img:
                x_offset = (WIDTH - visual_img.width) // 2
                if visual_img.mode == "RGBA":
                    img.paste(visual_img, (x_offset, y), mask=visual_img.split()[3])
                else:
                    img.paste(visual_img, (x_offset, y))
                y += visual_img.height + block_gap

            # Body text
            _draw_centered_lines(draw, body_lines, body_font, y, COLOR_BODY, line_gap=14)

    # ── Bottom accent bar ─────────────────────────────────────────────────────
    bar_y = HEIGHT - ACCENT_BAR_HEIGHT
    draw.rectangle([(0, bar_y), (WIDTH, HEIGHT)], fill=ACCENT_COLOR)

    # ── App name watermark (top-left, same row as slide counter) ─────────────
    wm_text = app_cfg["watermark_text"]
    is_screenshot_slide = "screenshot_path" in slide
    wm_fill = (30, 30, 30) if is_screenshot_slide else COLOR_WATERMARK
    wm_x = max(SLIDE_NUM_MARGIN - 20, 20) if is_screenshot_slide else SLIDE_NUM_MARGIN
    draw.text(
        (wm_x, SLIDE_NUM_MARGIN),
        wm_text,
        font=watermark_font,
        fill=wm_fill,
    )

    # ── Mascot (lower-left, composited on top) ───────────────────────────────
    # Only on hook (slide 1) — skip CTA (logo is there now) and value slides
    # Skip on Instagram (shorter canvas — mascot overlaps text content)
    is_infographic_value = "items" in slide
    is_hook_or_cta = slide_index == 1
    expression = mascot_expression if mascot_expression in VALID_EXPRESSIONS else "default"
    mascot_path = MASCOT_DIR / f"mascot_{expression}.png"
    if not is_infographic_value and is_hook_or_cta and HEIGHT >= 1700 and mascot_path.exists() and app_cfg.get("has_mascot", True):
        mascot_img = Image.open(mascot_path).convert("RGBA")
        ratio = MASCOT_W / mascot_img.width
        mascot_h = int(mascot_img.height * ratio)
        mascot_img = mascot_img.resize((MASCOT_W, mascot_h), Image.LANCZOS)
        mascot_x = MASCOT_PAD_X
        mascot_y = (HEIGHT - SAFE_ZONE_BOTTOM) - MASCOT_PAD_Y - mascot_h
        img.paste(mascot_img, (mascot_x, mascot_y), mask=mascot_img.split()[3])

    img.save(output_path, "PNG")


def render_carousel(
    slides: list,
    output_dir: Path,
    app_name: str,
    total_slides: int,
    illustration_path: Path = None,
) -> None:
    """Render every slide in a carousel and save PNGs into output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, slide in enumerate(slides, start=1):
        filename = output_dir / f"slide_{i:02d}.png"
        mascot_expression = slide.get("mascot_expression", "default")
        render_slide(
            slide=slide,
            slide_index=i,
            total_slides=total_slides,
            app_name=app_name,
            output_path=filename,
            illustration_path=illustration_path,
            mascot_expression=mascot_expression,
        )
        print(f"    slide {i:02d}/{total_slides} → {filename.name}")
