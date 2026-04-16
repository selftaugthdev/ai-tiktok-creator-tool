'use strict';

const fs = require('fs');
const path = require('path');
const Anthropic = require('@anthropic-ai/sdk');
const puppeteer = require('puppeteer');

// Brand colors — matches carousel_renderer.py
const COLORS = {
  bg: '#FADADD',
  accent: '#FF6B9D',
  text: '#2D2D2D',
  watermark: '#AAAAAA',
};

const PLATFORMS = {
  tiktok: {
    width: 1080,
    height: 1920,
    paddingTop: 72,
    paddingBottom: 80,
    bigNumberSize: 320,
    headerGap: 60,
  },
  instagram: {
    width: 1080,
    height: 1350,
    paddingTop: 50,
    paddingBottom: 60,
    bigNumberSize: 220,
    headerGap: 40,
  },
};

async function generateGridData(topic) {
  const client = new Anthropic();

  const message = await client.messages.create({
    model: 'claude-sonnet-4-6',
    max_tokens: 1024,
    messages: [
      {
        role: 'user',
        content: `Generate content for a "N Things About X" TikTok infographic about: "${topic}"

Return a single JSON object with this exact shape:
{
  "number": <integer, either 6 or 9 — pick whichever fits better>,
  "title": "<short uppercase title, max 4 words, e.g. MIGRAINE TRIGGER FOODS>",
  "items": [
    { "emoji": "<single emoji>", "label": "<short label, max 4 words, lowercase>" },
    ...
  ]
}

The number of items must exactly match the "number" field (either 6 or 9).

Rules:
- Title must be SHORT — max 4 words, ALL CAPS. This is the big heading.
- Labels must be concise — 2-4 words, all lowercase.
- Pick 6 if the content suits 2 rows of 3, pick 9 if it suits 3 rows of 3.
- Emojis must be specific and visually distinct from each other.
- Items must be specific and non-obvious. No generic filler.
- No em-dashes anywhere.
- Return ONLY valid JSON. No markdown, no explanation.`,
      },
    ],
  });

  const raw = message.content[0].text.trim().replace(/^```(?:json)?\s*/, '').replace(/\s*```$/, '');
  const data = JSON.parse(raw);

  if (!data.number || !data.title || !Array.isArray(data.items)) {
    throw new Error('Claude returned unexpected JSON shape.');
  }
  if (data.items.length !== data.number) {
    throw new Error(`Expected ${data.number} items, got ${data.items.length}.`);
  }

  return data;
}

function buildHtml(data, platform = 'tiktok') {
  const { number, title, items } = data;
  const p = PLATFORMS[platform] || PLATFORMS.tiktok;

  const gridItems = items
    .map(
      ({ emoji, label }) => `
    <div class="cell">
      <div class="emoji">${emoji}</div>
      <div class="label">${escapeHtml(label)}</div>
    </div>`
    )
    .join('');

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

    html, body {
      width: ${p.width}px;
      height: ${p.height}px;
      overflow: hidden;
      background: ${COLORS.bg};
      font-family: 'Inter', Arial, sans-serif;
      color: ${COLORS.text};
    }

    body {
      display: flex;
      flex-direction: column;
      padding: ${p.paddingTop}px 80px ${p.paddingBottom}px;
      position: relative;
    }

    /* ── Header row: big number left, title right ── */
    .header {
      display: flex;
      align-items: flex-start;
      gap: 32px;
      margin-bottom: ${p.headerGap}px;
    }

    .big-number {
      font-size: ${p.bigNumberSize}px;
      font-weight: 900;
      line-height: 0.88;
      color: ${COLORS.accent};
      flex-shrink: 0;
      letter-spacing: -12px;
    }

    .title-block {
      flex: 1;
      display: flex;
      flex-direction: column;
      padding-top: 24px;
    }

    .title-text {
      font-size: 88px;
      font-weight: 900;
      line-height: 1.0;
      text-transform: uppercase;
      color: ${COLORS.text};
      word-break: break-word;
    }

    .brand-line {
      margin-top: 16px;
      font-size: 28px;
      font-weight: 400;
      color: ${COLORS.watermark};
    }

    /* ── 3-column emoji grid ── */
    .grid {
      flex: 1;
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px 24px;
      align-content: space-evenly;
    }

    .cell {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 18px;
      padding: 12px 8px;
    }

    .emoji {
      font-size: 120px;
      line-height: 1;
      text-align: center;
    }

    .label {
      font-size: 36px;
      font-weight: 700;
      text-align: center;
      color: ${COLORS.text};
      line-height: 1.2;
    }

    /* www.migrainecast.app — bottom right */
    .watermark {
      position: absolute;
      bottom: 32px;
      right: 80px;
      font-size: 26px;
      font-weight: 400;
      color: ${COLORS.watermark};
    }
  </style>
</head>
<body>
  <div class="header">
    <div class="big-number">${number}</div>
    <div class="title-block">
      <div class="title-text">${escapeHtml(title)}</div>
      <div class="brand-line">presented by MigraineCast</div>
    </div>
  </div>

  <div class="grid">
    ${gridItems}
  </div>

  <div class="watermark">www.migrainecast.app</div>
</body>
</html>`;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

async function renderGrid(html, outputPath, platform = 'tiktok') {
  const { width, height } = PLATFORMS[platform] || PLATFORMS.tiktok;
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width, height, deviceScaleFactor: 1 });
    await page.setContent(html, { waitUntil: 'networkidle2' });
    await page.screenshot({ path: outputPath, type: 'png', clip: { x: 0, y: 0, width, height } });
  } finally {
    await browser.close();
  }
}

function nextOutputDir(baseDir, prefix) {
  fs.mkdirSync(baseDir, { recursive: true });
  const existing = fs.readdirSync(baseDir)
    .filter(n => n.startsWith(prefix + '_'))
    .map(n => parseInt(n.split('_')[1], 10))
    .filter(n => !isNaN(n));
  const next = existing.length ? Math.max(...existing) + 1 : 1;
  const slug = prefix.replace(/\s+/g, '-').toLowerCase();
  return path.join(baseDir, `${slug}_${next}`);
}

async function runGrid({ topic, output, platform = 'tiktok' }) {
  const topicSlug = topic.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
  const runDir = nextOutputDir(output, topicSlug);
  fs.mkdirSync(runDir, { recursive: true });
  const outputPath = path.join(runDir, 'infographic.png');
  const captionPath = path.join(runDir, 'caption.txt');

  console.log(`\nGenerating grid data for: "${topic}" [${platform}]`);
  const data = await generateGridData(topic);
  console.log(`  ${data.number} items — "${data.title}"`);

  console.log('Rendering infographic...');
  const html = buildHtml(data, platform);
  await renderGrid(html, outputPath, platform);

  const itemLines = data.items.map(({ emoji, label }) => `${emoji} ${label}`);
  const caption = [
    `${data.number} ${data.title}`,
    '',
    ...itemLines,
    '',
    'Stay ahead of your migraines with the MigraineCast app, download for free in the appstore or at www.migrainecast.app',
  ].join('\n');
  fs.writeFileSync(captionPath, caption, 'utf8');
  console.log(`    caption.txt → ${captionPath}`);

  console.log(`\nDone. Saved to: ${runDir}\n`);
}

module.exports = { runGrid };
