# CLAUDE.md — AI TikTok Creator Tool

Read this file at the start of every session. It contains full project context, architecture decisions, and conventions.

---

## What This Project Is

Python CLI that generates TikTok-style image carousels (1080×1920 PNG slides) for iOS app marketing. Claude generates the slide copy, Pillow renders the images locally. Primary use case is promoting **MigraineCast** and **Calm SOS**.

---

## CLI Usage

```bash
python3 main.py --app "MigraineCast" --topic "weather triggers for migraines" --count 3
python3 main.py --app "Calm SOS" --topic "anxiety grounding techniques" --count 1 --slides 5
```

- `--app` — app name (used in watermark and CTA copy)
- `--topic` — content theme for the carousel
- `--count` — number of carousels to generate
- `--slides` — slides per carousel (default: 7, minimum: 3)

Use `python3`, not `python` — `python` is not on PATH on this machine.

---

## File Responsibilities

```
main.py               — argparse CLI, orchestrates generation + rendering
script_gen.py         — Anthropic API call, returns list[dict] with headline/body/chart_data/mascot_expression
carousel_renderer.py  — Pillow rendering (pink bg, fonts, illustration/chart compositing, mascot, accent bar)
chart_generator.py    — Plotly bar chart → PIL Image (used when slide has chart_data)
assets/               — mascot PNGs (mascot_calm/default/sad/smug/stormy/warning.png), all transparent
requirements.txt      — anthropic, pillow, plotly, kaleido, python-dotenv
.env                  — ANTHROPIC_API_KEY (gitignored)
.env.example          — committed placeholder
output/carousels/     — generated PNGs, gitignored
```

---

## Output Structure

```
output/carousels/
├── MigraineCast/
│   ├── carousel_1/
│   │   ├── slide_01.png
│   │   └── ...
└── Calm_SOS/
    ├── carousel_1/
    │   └── ...
```

App name spaces are replaced with underscores for the folder name.

---

## Design Spec (carousel_renderer.py)

- **Canvas:** 1080×1920 px
- **Background:** solid soft pink `#FADADD`
- **Accent color:** `#FF6B9D` (hot pink) — pip above headline, slide counter, bottom bar
- **Headline:** dark `#2D2D2D`, 88px bold, centered
- **Body:** medium gray `#555555`, 48px regular, centered
- **Slide counter:** top-right, 38px, hot pink
- **Watermark:** app name, bottom-right above accent bar, 34px, light gray
- **Accent bar:** hot pink, 12px, bottom edge
- **Content block** vertically centered in usable area
- **Mascot:** 280px wide, lower-left corner (60px from left, 20px above accent bar), composited on top of all content

### Layout with visual element
Headline → (illustration or chart) → body, stacked with 60px gaps.
Without visual: headline → body with 80px gap.

### Mascot
- Appears on every slide, lower-left, on top of any overlapping text (text is not constrained around it)
- Expression is chosen by Claude per slide via `mascot_expression` field
- Valid expressions: `calm`, `default`, `sad`, `smug`, `stormy`, `warning`
- CTA slide (last slide) is always locked to `smug`
- Falls back to `default` if field is missing or invalid
- Assets live in `assets/mascot_{expression}.png` (transparent PNGs)

### Font strategy
Checks `./fonts/Bold.ttf` and `./fonts/Regular.ttf` first, then falls back to system fonts (macOS Helvetica/Arial → Linux Liberation/DejaVu → Windows Arial), then PIL default.

---

## Prompt Rules (script_gen.py)

- Slide 1: hook (bold/alarming statement)
- Slides 2–N-1: value slides (distinct actionable tips)
- Last slide: CTA — body must end with `"Download {app_name} on iOS. Link in bio."`
- No em-dashes (— or –) anywhere — use commas or periods instead
- Headlines: max 8 words, punchy
- Body: max 25 words, conversational
- `chart_data` is optional — only included when content suits a bar chart (stats, rankings, percentages). Format: `{"labels": [...], "values": [...], "title": "..."}`
- `mascot_expression` — required on every slide. One of: `calm`, `default`, `sad`, `smug`, `stormy`, `warning`. CTA slide must always be `smug`.

---

## Environment

```
ANTHROPIC_API_KEY     required — set in .env
```

Model: `claude-sonnet-4-6`

---

## Known Gotchas

- **Python version:** runs on Python 3.9. Avoid `X | Y` union type hints (3.10+ syntax) — use plain return types or `Optional`.
- **pip not on PATH** — use `python3 -m pip install -r requirements.txt` to install deps.
- **Line breaks in CLI commands** — always run commands on a single line in the terminal; hitting Enter mid-command executes prematurely.
- **kaleido:** required for Plotly PNG export. Installed via requirements.txt. If chart rendering fails, check kaleido is installed (`python3 -m pip install kaleido`).
