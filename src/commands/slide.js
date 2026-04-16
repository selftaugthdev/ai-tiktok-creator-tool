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
    paddingTop: 100,
    paddingBottom: 80,
    h1Size: 86,
    statementSize: 47,
    safeBottom: 1840,
  },
  instagram: {
    width: 1080,
    height: 1350,
    paddingTop: 70,
    paddingBottom: 60,
    h1Size: 76,
    statementSize: 42,
    safeBottom: 1290,
  },
};

async function generateStatements(topic) {
  const client = new Anthropic();

  const message = await client.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 768,
    messages: [
      {
        role: 'user',
        content: `Generate exactly 7 statements for a TikTok slide with the title: "${topic}"

First, read the title and decide which style fits:

A) IDENTITY VALIDATION — use this when the title is emotional, experiential, or describes what migraine life feels like. Give words to feelings the reader already has. Each statement lands like recognition, not advice.
   Examples: "The fear of waking up with an attack and knowing the whole day is lost." / "Feeling guilty for canceling again."

B) ACTIONABLE TIPS — use this when the title is a how-to, a guide, or asks for practical advice. Give specific, non-obvious tips the reader can actually use. Each statement is a concrete action or insight.
   Examples: "Switch overhead lights for warm bedside lamps — harsh ceiling light is one of the biggest hidden triggers." / "Keep unscented cleaning products in every room. Fragrance is a top trigger most people overlook."

Rules for both styles:
- Keep each statement to 1-2 lines — roughly 10-15 words max. Short and direct.
- No em-dashes. Use commas or periods instead.
- No hashtags, no emojis.
- Return ONLY a JSON array of exactly 7 strings. No markdown, no explanation.`,
      },
    ],
  });

  const raw = message.content[0].text.trim().replace(/^```(?:json)?\s*/, '').replace(/\s*```$/, '');
  const statements = JSON.parse(raw);

  if (!Array.isArray(statements)) throw new Error('Claude did not return a JSON array.');
  return statements;
}

function buildHtml(topic, statements, platform = 'tiktok') {
  const p = PLATFORMS[platform] || PLATFORMS.tiktok;
  const statementItems = statements
    .map((s) => `<p class="statement">${escapeHtml(s)}</p>`)
    .join('\n    ');

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

    html, body {
      width: ${p.width}px;
      height: ${p.height}px;
      overflow: hidden;
      background: ${COLORS.bg};
    }

    body {
      display: flex;
      flex-direction: column;
      padding: ${p.paddingTop}px 96px ${p.paddingBottom}px;
      position: relative;
      font-family: 'Playfair Display', Georgia, serif;
      color: ${COLORS.text};
    }

    h1 {
      font-size: ${p.h1Size}px;
      font-weight: 900;
      line-height: 1.1;
      text-align: center;
      margin-bottom: 80px;
      color: ${COLORS.text};
    }

    /* Statements fill remaining space, evenly distributed with explicit minimum gap */
    .statements {
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: space-evenly;
      gap: 32px;
    }

    .statement {
      font-size: ${p.statementSize}px;
      font-weight: 700;
      line-height: 1.35;
      text-align: left;
      color: ${COLORS.text};
    }

    .brand-top {
      position: absolute;
      top: 40px;
      left: 0;
      right: 0;
      text-align: center;
      font-size: 32px;
      font-weight: 700;
      color: ${COLORS.watermark};
      letter-spacing: 0.5px;
    }

    .watermark {
      position: absolute;
      bottom: 32px;
      right: 96px;
      font-size: 28px;
      font-weight: 400;
      color: ${COLORS.watermark};
    }
  </style>
</head>
<body>
  <h1>${escapeHtml(topic)}</h1>
  <div class="statements">
    ${statementItems}
  </div>
  <div class="brand-top">MigraineCast</div>
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

async function renderSlide(html, outputPath, platform = 'tiktok') {
  const p = PLATFORMS[platform] || PLATFORMS.tiktok;
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: p.width, height: p.height, deviceScaleFactor: 1 });
    await page.setContent(html, { waitUntil: 'networkidle2' });

    // Auto-scale fonts down until the last statement fits within the slide
    await page.evaluate((safeBottom, initH, initS) => {
      const headline = document.querySelector('h1');
      const items = document.querySelectorAll('.statement');

      let hSize = initH;
      let sSize = initS;

      for (let i = 0; i < 60; i++) {
        const last = document.querySelector('.statement:last-child');
        if (!last) break;
        if (last.getBoundingClientRect().bottom <= safeBottom) break;

        if (sSize > 28) {
          sSize -= 1;
          items.forEach(el => { el.style.fontSize = sSize + 'px'; });
        } else if (hSize > 48) {
          hSize -= 2;
          headline.style.fontSize = hSize + 'px';
        } else {
          break;
        }
      }
    }, p.safeBottom, p.h1Size, p.statementSize);

    await page.screenshot({ path: outputPath, type: 'png', clip: { x: 0, y: 0, width: p.width, height: p.height } });
  } finally {
    await browser.close();
  }
}

async function runSlide({ topic, output, platform = 'tiktok' }) {
  fs.mkdirSync(output, { recursive: true });
  const outputPath = path.join(output, 'slide.png');
  const captionPath = path.join(output, 'caption.txt');

  console.log(`\nGenerating statements for: "${topic}" [${platform}]`);
  const statements = await generateStatements(topic);
  console.log(`  ${statements.length} statements generated.`);

  console.log('Rendering slide...');
  const html = buildHtml(topic, statements, platform);
  await renderSlide(html, outputPath, platform);

  const caption = [topic, '', ...statements, '', 'Stay ahead of your migraines with the MigraineCast app, download for free in the appstore or at www.migrainecast.app'].join('\n');
  fs.writeFileSync(captionPath, caption, 'utf8');
  console.log(`    caption.txt → ${captionPath}`);

  console.log(`\nDone. Saved to: ${outputPath}\n`);
}

module.exports = { runSlide };
