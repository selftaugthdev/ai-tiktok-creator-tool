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

async function generateStatements(topic) {
  const client = new Anthropic();

  const message = await client.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 768,
    messages: [
      {
        role: 'user',
        content: `Generate exactly 7 emotional statements about "${topic}" for people with migraines.

Style: identity validation. Give words to feelings the reader already has but hasn't been able to express. Each statement should land like recognition, not advice.

Examples of the tone and length to aim for:
- "Brain fog so bad you forget what you were saying mid-sentence."
- "The fear of waking up with an attack and knowing the whole day is lost."
- "Feeling guilty for canceling again."
- "The loneliness of being in pain when no one understands how bad it really is."

Rules:
- No advice, no silver linings, no solutions. Just honest acknowledgment.
- Keep each statement to 1-2 lines when read — roughly 10-15 words max. Short, crisp, and direct.
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

function buildHtml(topic, statements) {
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
      width: 1080px;
      height: 1920px;
      overflow: hidden;
      background: ${COLORS.bg};
    }

    body {
      display: flex;
      flex-direction: column;
      padding: 100px 96px 80px;
      position: relative;
      font-family: 'Playfair Display', Georgia, serif;
      color: ${COLORS.text};
    }

    h1 {
      font-size: 86px;
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
      font-size: 47px;
      font-weight: 700;
      line-height: 1.35;
      text-align: left;
      color: ${COLORS.text};
    }

    .watermark {
      position: absolute;
      bottom: 32px;
      right: 96px;
      font-size: 32px;
      font-weight: 700;
      color: ${COLORS.watermark};
      letter-spacing: 0.5px;
    }
  </style>
</head>
<body>
  <h1>${escapeHtml(topic)}</h1>
  <div class="statements">
    ${statementItems}
  </div>
  <div class="watermark">MigraineCast</div>
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

async function renderSlide(html, outputPath) {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
    await page.setContent(html, { waitUntil: 'networkidle2' });
    await page.screenshot({ path: outputPath, type: 'png', clip: { x: 0, y: 0, width: 1080, height: 1920 } });
  } finally {
    await browser.close();
  }
}

async function runSlide({ topic, output }) {
  fs.mkdirSync(output, { recursive: true });
  const outputPath = path.join(output, 'slide.png');

  console.log(`\nGenerating statements for: "${topic}"`);
  const statements = await generateStatements(topic);
  console.log(`  ${statements.length} statements generated.`);

  console.log('Rendering slide...');
  const html = buildHtml(topic, statements);
  await renderSlide(html, outputPath);

  console.log(`\nDone. Saved to: ${outputPath}\n`);
}

module.exports = { runSlide };
