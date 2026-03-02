from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Canvas dimensions (TikTok portrait)
WIDTH = 1080
HEIGHT = 1920

# Colour palette
BG_TOP = (26, 26, 46)        # #1a1a2e
BG_BOTTOM = (22, 33, 62)     # #16213e
ACCENT_COLOR = (124, 58, 237)  # #7c3aed
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (180, 180, 200)
COLOR_WATERMARK = (120, 120, 150)

# Layout constants
MARGIN_X = 80
ACCENT_BAR_HEIGHT = 14
PADDING_BOTTOM = 80          # space above accent bar
SLIDE_NUM_MARGIN = 60        # inset from edges for slide counter
CONTENT_CENTER_Y = 860       # vertical midpoint for headline block


# ---------------------------------------------------------------------------
# Font loading
# ---------------------------------------------------------------------------

def _try_font(path: str, size: int) -> ImageFont.FreeTypeFont | None:
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

    candidates = (macos_bold if bold else macos_regular) + \
                 (linux_bold if bold else linux_regular) + \
                 (win_bold if bold else win_regular)

    for path in candidates:
        font = _try_font(path, size)
        if font:
            return font

    # Last resort — PIL built-in (no size control)
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def _gradient_background() -> Image.Image:
    """Create a top-to-bottom gradient background image."""
    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (WIDTH - 1, y)], fill=(r, g, b))
    return img


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    """Break text into lines that fit within max_width pixels."""
    words = text.split()
    lines: list[str] = []
    current: list[str] = []

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


def _text_block_height(draw: ImageDraw.ImageDraw, lines: list[str], font: ImageFont.ImageFont, line_gap: int) -> int:
    """Return total pixel height of a block of wrapped lines."""
    if not lines:
        return 0
    sample_bbox = draw.textbbox((0, 0), "Ag", font=font)
    line_h = sample_bbox[3] - sample_bbox[1]
    return line_h * len(lines) + line_gap * (len(lines) - 1)


def _draw_centered_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
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
) -> None:
    """Render a single slide and save it as a PNG."""
    img = _gradient_background()
    draw = ImageDraw.Draw(img)

    headline_font = load_font(88, bold=True)
    body_font = load_font(48, bold=False)
    counter_font = load_font(38, bold=False)
    watermark_font = load_font(34, bold=False)

    available_width = WIDTH - 2 * MARGIN_X

    # ── Slide counter (top-right) ────────────────────────────────────────────
    counter_text = f"{slide_index} / {total_slides}"
    cb = draw.textbbox((0, 0), counter_text, font=counter_font)
    counter_w = cb[2] - cb[0]
    draw.text(
        (WIDTH - SLIDE_NUM_MARGIN - counter_w, SLIDE_NUM_MARGIN),
        counter_text,
        font=counter_font,
        fill=COLOR_GRAY,
    )

    # ── Headline ─────────────────────────────────────────────────────────────
    headline_lines = _wrap_text(draw, slide["headline"], headline_font, available_width)
    headline_h = _text_block_height(draw, headline_lines, headline_font, 16)

    # ── Body ─────────────────────────────────────────────────────────────────
    body_lines = _wrap_text(draw, slide["body"], body_font, available_width)
    body_h = _text_block_height(draw, body_lines, body_font, 14)

    gap_between = 52  # pixels between headline block and body block

    # Centre the combined content block around CONTENT_CENTER_Y
    total_h = headline_h + gap_between + body_h
    block_top = CONTENT_CENTER_Y - total_h // 2

    # Draw a small accent bar above the headline
    accent_pip_y = block_top - 36
    draw.rectangle(
        [(WIDTH // 2 - 60, accent_pip_y), (WIDTH // 2 + 60, accent_pip_y + 6)],
        fill=ACCENT_COLOR,
    )

    # Draw headline
    y_after_headline = _draw_centered_lines(
        draw, headline_lines, headline_font, block_top, COLOR_WHITE, line_gap=16
    )

    # Draw body
    _draw_centered_lines(
        draw, body_lines, body_font, y_after_headline + gap_between, COLOR_GRAY, line_gap=14
    )

    # ── Bottom accent bar ─────────────────────────────────────────────────────
    bar_y = HEIGHT - ACCENT_BAR_HEIGHT
    draw.rectangle([(0, bar_y), (WIDTH, HEIGHT)], fill=ACCENT_COLOR)

    # ── App name watermark (above accent bar, right-aligned) ─────────────────
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

    img.save(output_path, "PNG")


def render_carousel(
    slides: list[dict],
    output_dir: Path,
    app_name: str,
    total_slides: int,
) -> None:
    """Render every slide in a carousel and save PNGs into output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, slide in enumerate(slides, start=1):
        filename = output_dir / f"slide_{i:02d}.png"
        render_slide(
            slide=slide,
            slide_index=i,
            total_slides=total_slides,
            app_name=app_name,
            output_path=filename,
        )
        print(f"    slide {i:02d}/{total_slides} → {filename.name}")
