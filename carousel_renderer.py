from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from chart_generator import generate_chart_image

# Canvas dimensions (TikTok portrait)
WIDTH = 1080
HEIGHT = 1920

# Colour palette
BG_COLOR = (250, 218, 221)      # #FADADD soft pink
ACCENT_COLOR = (255, 107, 157)  # #FF6B9D hot pink
COLOR_HEADLINE = (45, 45, 45)   # #2D2D2D
COLOR_BODY = (85, 85, 85)       # #555555
COLOR_WATERMARK = (170, 170, 170)

# Layout constants
MARGIN_X = 80
ACCENT_BAR_HEIGHT = 12
PADDING_BOTTOM = 80
SLIDE_NUM_MARGIN = 60
ILLUS_MAX_W = 600
ILLUS_MAX_H = 600

# Mascot constants
MASCOT_DIR = Path("assets")
MASCOT_W = 280
MASCOT_PAD_X = 60
MASCOT_PAD_Y = 20
VALID_EXPRESSIONS = {"calm", "default", "sad", "smug", "stormy", "warning"}


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

    # ── Measure text blocks ───────────────────────────────────────────────────
    headline_lines = _wrap_text(draw, slide["headline"], headline_font, available_width)
    body_lines = _wrap_text(draw, slide["body"], body_font, available_width)
    headline_h = _text_block_height(draw, headline_lines, headline_font, 16)
    body_h = _text_block_height(draw, body_lines, body_font, 14)

    # ── Resolve visual element — chart takes priority over illustration ───────
    visual_img = None
    chart_data = slide.get("chart_data")
    if chart_data:
        visual_img = generate_chart_image(chart_data)
    elif illustration_path:
        visual_img = Image.open(illustration_path).convert("RGBA")
        visual_img.thumbnail((ILLUS_MAX_W, ILLUS_MAX_H), Image.LANCZOS)

    # ── Calculate total content block height ─────────────────────────────────
    block_gap = 60 if visual_img else 80
    if visual_img:
        total_h = headline_h + block_gap + visual_img.height + block_gap + body_h
    else:
        total_h = headline_h + block_gap + body_h

    # ── Centre block in usable vertical space ────────────────────────────────
    usable_top = SLIDE_NUM_MARGIN + 80
    usable_bottom = HEIGHT - ACCENT_BAR_HEIGHT - PADDING_BOTTOM
    block_top = max((usable_top + usable_bottom) // 2 - total_h // 2, usable_top)

    # ── Accent pip above headline ─────────────────────────────────────────────
    pip_y = block_top - 36
    if pip_y >= usable_top - 10:
        draw.rectangle(
            [(WIDTH // 2 - 60, pip_y), (WIDTH // 2 + 60, pip_y + 6)],
            fill=ACCENT_COLOR,
        )

    # ── Headline ──────────────────────────────────────────────────────────────
    y = block_top
    y = _draw_centered_lines(draw, headline_lines, headline_font, y, COLOR_HEADLINE, line_gap=16)
    y += block_gap

    # ── Visual (chart or illustration) ───────────────────────────────────────
    if visual_img:
        x_offset = (WIDTH - visual_img.width) // 2
        if visual_img.mode == "RGBA":
            img.paste(visual_img, (x_offset, y), mask=visual_img.split()[3])
        else:
            img.paste(visual_img, (x_offset, y))
        y += visual_img.height + block_gap

    # ── Body ──────────────────────────────────────────────────────────────────
    _draw_centered_lines(draw, body_lines, body_font, y, COLOR_BODY, line_gap=14)

    # ── Bottom accent bar ─────────────────────────────────────────────────────
    bar_y = HEIGHT - ACCENT_BAR_HEIGHT
    draw.rectangle([(0, bar_y), (WIDTH, HEIGHT)], fill=ACCENT_COLOR)

    # ── App name watermark (above accent bar, right-aligned) ──────────────────
    wm_text = app_name
    wb = draw.textbbox((0, 0), wm_text, font=watermark_font)
    wm_w = wb[2] - wb[0]
    wm_h = wb[3] - wb[1]
    wm_y = bar_y - PADDING_BOTTOM // 2 - wm_h
    draw.text(
        (WIDTH - MARGIN_X - wm_w, wm_y),
        wm_text,
        font=watermark_font,
        fill=COLOR_WATERMARK,
    )

    # ── Mascot (lower-left, composited on top) ───────────────────────────────
    expression = mascot_expression if mascot_expression in VALID_EXPRESSIONS else "default"
    mascot_path = MASCOT_DIR / f"mascot_{expression}.png"
    if mascot_path.exists():
        mascot_img = Image.open(mascot_path).convert("RGBA")
        ratio = MASCOT_W / mascot_img.width
        mascot_h = int(mascot_img.height * ratio)
        mascot_img = mascot_img.resize((MASCOT_W, mascot_h), Image.LANCZOS)
        mascot_x = MASCOT_PAD_X
        mascot_y = bar_y - MASCOT_PAD_Y - mascot_h
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
