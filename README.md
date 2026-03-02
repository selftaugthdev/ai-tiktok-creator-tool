# TikTok Carousel Generator

A Python CLI tool that uses Claude (Anthropic) to generate TikTok-style image carousels and renders them as 1080×1920 PNG slides with Pillow.

---

## Project structure

```
.
├── main.py               # CLI entry point
├── script_gen.py         # Anthropic API — slide content generation
├── carousel_renderer.py  # Pillow — image rendering
├── requirements.txt
├── .env                  # your API key (create from .env.example)
└── output/
    └── carousels/
        ├── carousel_1/
        │   ├── slide_01.png
        │   └── ...
        └── carousel_2/
            └── ...
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure your API key

```bash
cp .env.example .env
# then edit .env and paste your Anthropic API key
```

Get a key at <https://console.anthropic.com/>.

### 3. (Optional) Better fonts

By default the tool uses the best system font it can find (Arial, Helvetica, Liberation Sans). For crisper results, drop a TrueType font into a `fonts/` directory:

```bash
mkdir fonts
# place Bold.ttf and Regular.ttf inside fonts/
# e.g. download Inter from https://fonts.google.com/specimen/Inter
```

---

## Usage

```bash
python main.py --app "AppName" --topic "your topic" --count <n> [--slides <n>]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--app` | yes | — | App name shown on every slide |
| `--topic` | yes | — | Subject matter for the carousel |
| `--count` | yes | — | Number of carousels to generate |
| `--slides` | no | `7` | Slides per carousel (min 3) |

### Examples

```bash
# Generate 3 carousels about weather-triggered migraines for MigraineCast
python main.py --app "MigraineCast" --topic "weather triggers for migraines" --count 3

# Generate 1 carousel with 5 slides about morning routines for FitTrack
python main.py --app "FitTrack" --topic "morning routines" --count 1 --slides 5
```

---

## Slide layout

Each carousel follows this structure:

| Slide | Type | Content |
|-------|------|---------|
| 1 | Hook | Bold, scroll-stopping statement |
| 2 – N-1 | Value | One actionable tip or insight per slide |
| N | CTA | Download prompt for the app |

### Visual design

- **Canvas**: 1080 × 1920 px (TikTok portrait)
- **Background**: dark gradient (`#1a1a2e` → `#16213e`)
- **Headline**: large bold white text, centred
- **Body**: smaller light-gray text below headline
- **Accent bar**: purple (`#7c3aed`) at the bottom
- **Watermark**: app name in the bottom-right corner
- **Slide counter**: `1 / 7` indicator in the top-right corner
