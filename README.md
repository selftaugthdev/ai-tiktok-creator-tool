# AI TikTok Creator Tool

Python CLI that generates TikTok-style image carousels (1080×1920 PNG) for iOS app marketing. Claude generates the slide copy; Pillow renders the images locally. Slides with stat-heavy content automatically get a Plotly bar chart composited in.

---

## Project structure

```
.
├── main.py               # CLI entry point
├── script_gen.py         # Anthropic API — slide content generation
├── carousel_renderer.py  # Pillow — image rendering + compositing
├── chart_generator.py    # Plotly — bar chart → PIL Image
├── requirements.txt
├── .env                  # your API key (create from .env.example)
└── output/
    └── carousels/
        └── MigraineCast/
            ├── carousel_1/
            │   ├── slide_01.png
            │   └── ...
            └── carousel_2/
                └── ...
```

---

## Setup

**1. Install dependencies**
```bash
python3 -m pip install -r requirements.txt
```

**2. Add your Anthropic API key**
```bash
cp .env.example .env
# then open .env and fill in your key
```

**3. (Optional) Custom fonts**

Drop `Bold.ttf` and `Regular.ttf` into a `fonts/` directory for crisper text. Falls back to system fonts (Arial/Helvetica) automatically.

---

## Usage

```bash
python3 main.py --app "AppName" --topic "your topic" --count <n> [--slides <n>] [--illustration path/to/image.png]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--app` | yes | — | App name shown in watermark and CTA |
| `--topic` | yes | — | Subject matter for the carousel |
| `--count` | yes | — | Number of carousels to generate |
| `--slides` | no | `7` | Slides per carousel (min 3) |
| `--illustration` | no | — | PNG to composite onto slides (chart_data overrides this) |

### Examples

```bash
# Generate 3 carousels about weather-triggered migraines
python3 main.py --app "MigraineCast" --topic "weather triggers for migraines" --count 3

# With illustration composited between headline and body
python3 main.py --app "MigraineCast" --topic "barometric pressure and migraines" --count 2 --illustration ./assets/brain_character.png

# Custom slide count
python3 main.py --app "Calm SOS" --topic "anxiety grounding techniques" --count 1 --slides 5
```

---

## Slide layout

Each carousel follows this structure:

| Slide | Type | Content |
|-------|------|---------|
| 1 | Hook | Bold, scroll-stopping statement |
| 2 – N-1 | Value | One actionable tip or insight per slide |
| N | CTA | "Download [app] on iOS. Link in bio." |

### Visual design

- **Canvas**: 1080 × 1920 px
- **Background**: soft pink `#FADADD`
- **Headline**: dark `#2D2D2D`, 88px bold, centered
- **Body**: medium gray `#555555`, 48px, centered
- **Accent**: hot pink `#FF6B9D` — pip above headline, slide counter, bottom bar
- **Watermark**: app name, bottom-right

### Chart slides

When Claude determines a slide is naturally suited to a bar chart (stats, rankings, percentages), it returns `chart_data` which is rendered via Plotly and composited onto the slide instead of the illustration.
