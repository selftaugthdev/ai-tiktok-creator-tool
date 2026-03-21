'use strict';

const fs = require('fs');
const path = require('path');
const Anthropic = require('@anthropic-ai/sdk');
const puppeteer = require('puppeteer');

// Brand colors — matches carousel_renderer.py exactly
const COLORS = {
  bg: '#FADADD',
  accent: '#FF6B9D',
  headline: '#2D2D2D',
  body: '#555555',
  watermark: '#AAAAAA',
  circleFill: '#FFB6D2',
};

async function generateStatements(topic) {
  const client = new Anthropic();

  const message = await client.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 512,
    messages: [
      {
        role: 'user',
        content: `Generate 6-8 short emotional statements about "${topic}" for people with migraines.

Style: identity validation. Write as if giving words to feelings the reader already has but hasn't been able to express. Each statement should land like recognition, not advice.

Examples:
- "The fear of waking up and knowing the whole day is lost."
- "Canceling so often that people stop inviting you."
- "Feeling guilty for something your body did without your permission."

Rules:
- No advice, no silver linings, no solutions. Just honest acknowledgment.
- Start with "The" or "When you" or a similar grounded phrase.
- Max 12 words each. Short, punchy, emotionally resonant.
- No em-dashes. Use commas or periods instead.
- No hashtags, no emojis.
- Return ONLY a JSON array of strings. No markdown, no explanation.`,
      },
    ],
  });

  const raw = message.content[0].text.trim().replace(/^```(?:json)?\s*/,'').replace(/\s*```$/,'');
  const statements = JSON.parse(raw);

  if (!Array.isArray(statements)) throw new Error('Claude did not return a JSON array.');
  return statements;
}

function buildHtml(topic, statements) {
  const statementItems = statements
    .map((s) => `<div class="statement">${escapeHtml(s)}</div>`)
    .join('\n    ');

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Inter:wght@400&display=swap" rel="stylesheet" />
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
      padding: 90px 100px 104px; /* bottom padding clears accent bar (12px) + watermark row */
      position: relative;
      font-family: 'Playfair Display', Georgia, serif;
    }

    /* Hot pink accent bar, pinned to bottom */
    .accent-bar {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 12px;
      background: ${COLORS.accent};
    }

    /* Small pip above headline, matches carousel style */
    .pip {
      width: 120px;
      height: 6px;
      background: ${COLORS.accent};
      border-radius: 3px;
      margin-bottom: 44px;
    }

    .headline {
      color: ${COLORS.headline};
      font-size: 80px;
      font-weight: 900;
      line-height: 1.12;
      letter-spacing: -0.5px;
      margin-bottom: 64px;
    }

    /* Statements fill the remaining vertical space, centered */
    .statements {
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 44px;
    }

    .statement {
      color: ${COLORS.body};
      font-size: 54px;
      font-weight: 700;
      line-height: 1.25;
      letter-spacing: -0.2px;
    }

    /* App name watermark, bottom-right, above accent bar */
    .watermark {
      position: absolute;
      bottom: 28px;
      right: 100px;
      color: ${COLORS.watermark};
      font-family: 'Inter', Arial, sans-serif;
      font-size: 34px;
      font-weight: 400;
    }
  </style>
</head>
<body>
  <div class="pip"></div>
  <div class="headline">${escapeHtml(topic)}</div>
  <div class="statements">
    ${statementItems}
  </div>
  <div class="watermark">MigraineCast</div>
  <div class="accent-bar"></div>
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
