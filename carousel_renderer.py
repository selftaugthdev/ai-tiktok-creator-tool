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

# TikTok safe zones (UI chrome that overlaps the image)
SAFE_ZONE_RIGHT = 160   # engagement buttons on right (~15% of 1080)
SAFE_ZONE_BOTTOM = 480  # caption/description overlay (~25% of 1920)

# Mascot constants
MASCOT_DIR = Path("assets")
MASCOT_W = 280
MASCOT_PAD_X = 60
MASCOT_PAD_Y = 20
VALID_EXPRESSIONS = {"calm", "default", "sad", "smug", "stormy", "warning"}

# Testimonial (CTA slide)
TESTIMONIAL_FONT_SIZE = 36
TESTIMONIAL_PAD_X = 40
TESTIMONIAL_PAD_Y = 22
TESTIMONIAL_BG = (255, 200, 215)   # slightly deeper pink

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

    # ── Usable area (respects TikTok bottom caption safe zone) ───────────────
    usable_top = SLIDE_NUM_MARGIN + 80
    usable_bottom = HEIGHT - SAFE_ZONE_BOTTOM

    # ── Headline (always present) ─────────────────────────────────────────────
    headline_lines = _wrap_text(draw, slide["headline"], headline_font, available_width)
    headline_h = _text_block_height(draw, headline_lines, headline_font, 16)

    if "items" in slide:
        # ── Infographic layout ────────────────────────────────────────────────
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
        body_lines = _wrap_text(draw, slide["body"], body_font, available_width)
        body_h = _text_block_height(draw, body_lines, body_font, 14)

        # Testimonial block (CTA / last slide only)
        is_cta = slide_index == total_slides
        testimonial_lines = []
        testimonial_h = 0
        testimonial_font = None
        if is_cta:
            testimonial_text = (
                f"\u201cThe {app_name} app (finally) helped me stop "
                f"being blindsided by my migraines\u201d"
            )
            testimonial_font = load_font(TESTIMONIAL_FONT_SIZE, bold=False)
            testimonial_lines = _wrap_text(
                draw, testimonial_text, testimonial_font,
                available_width - TESTIMONIAL_PAD_X * 2,
            )
            text_h = _text_block_height(draw, testimonial_lines, testimonial_font, 12)
            testimonial_h = text_h + TESTIMONIAL_PAD_Y * 2

        # Resolve visual element — chart takes priority over illustration
        visual_img = None
        chart_data = slide.get("chart_data")
        if chart_data:
            visual_img = generate_chart_image(chart_data)
        elif illustration_path:
            visual_img = Image.open(illustration_path).convert("RGBA")
            visual_img.thumbnail((ILLUS_MAX_W, ILLUS_MAX_H), Image.LANCZOS)

        # Calculate total content block height
        block_gap = 60 if visual_img else 80
        testimonial_gap = 40  # gap between headline and testimonial, and testimonial and body
        if visual_img:
            total_h = headline_h + block_gap + visual_img.height + block_gap + body_h
        elif is_cta:
            total_h = headline_h + testimonial_gap + testimonial_h + testimonial_gap + body_h
        else:
            total_h = headline_h + block_gap + body_h

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
        y += block_gap if not is_cta else testimonial_gap

        # Testimonial (CTA slide only)
        if is_cta and testimonial_lines:
            rect_x = MARGIN_X
            rect_h = testimonial_h
            draw.rounded_rectangle(
                [(rect_x, y), (rect_x + available_width, y + rect_h)],
                radius=20,
                fill=TESTIMONIAL_BG,
            )
            _draw_centered_lines(
                draw, testimonial_lines, testimonial_font,
                y + TESTIMONIAL_PAD_Y, COLOR_BODY, line_gap=12,
            )
            y += rect_h + testimonial_gap

        # Visual (chart or illustration)
        if visual_img:
            x_offset = (WIDTH - visual_img.width) // 2
            if visual_img.mode == "RGBA":
                img.paste(visual_img, (x_offset, y), mask=visual_img.split()[3])
            else:
                img.paste(visual_img, (x_offset, y))
            y += visual_img.height + block_gap

        # Body
        _draw_centered_lines(draw, body_lines, body_font, y, COLOR_BODY, line_gap=14)

    # ── Bottom accent bar ─────────────────────────────────────────────────────
    bar_y = HEIGHT - ACCENT_BAR_HEIGHT
    draw.rectangle([(0, bar_y), (WIDTH, HEIGHT)], fill=ACCENT_COLOR)

    # ── App name watermark (above accent bar, right-aligned) ──────────────────
    wm_text = "www.migrainecast.app" if "migrainecast" in app_name.lower() else app_name
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
    # Skip on infographic value slides — the emoji grid fills that space
    is_infographic_value = "items" in slide
    expression = mascot_expression if mascot_expression in VALID_EXPRESSIONS else "default"
    mascot_path = MASCOT_DIR / f"mascot_{expression}.png"
    if not is_infographic_value and mascot_path.exists():
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
