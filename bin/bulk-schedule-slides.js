#!/usr/bin/env node
'use strict';
/**
 * Bulk-schedule all slides in output/slides/tiktok/to_upload/ to Pinterest only.
 *
 * Schedule: 1 slide/day, staggered times between 15:00–01:59 CEST (13:00–23:59 UTC).
 *
 * Usage:
 *   node bin/bulk-schedule-slides.js
 *   node bin/bulk-schedule-slides.js --start 2026-05-05   # override start date
 *   node bin/bulk-schedule-slides.js --dry-run            # preview schedule, no API calls
 */

require('dotenv').config();

const fs   = require('fs');
const path = require('path');

const TO_UPLOAD_DIR = 'output/slides/tiktok/to_upload';
const API           = 'https://api.post-bridge.com';

// 30 varied post times (UTC) — 15:00–01:59 CEST window
const POST_TIMES_UTC = [
  '13:15', '14:00', '15:30', '16:45', '17:20',
  '18:05', '19:00', '20:30', '21:15', '22:00',
  '23:30', '13:45', '15:00', '16:15', '17:50',
  '18:30', '19:45', '21:00', '22:15', '23:00',
  '14:30', '15:45', '17:00', '18:00', '19:15',
  '20:45', '21:30', '22:45', '23:15', '13:30',
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function apiHeaders() {
  return {
    Authorization: `Bearer ${process.env.POSTBRIDGE_API_KEY}`,
    'Content-Type': 'application/json',
  };
}

function addDays(dateStr, n) {
  const d = new Date(`${dateStr}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

function tomorrow() {
  return addDays(new Date().toISOString().slice(0, 10), 1);
}

/** Parse caption.txt — first line = title, middle = description, last paragraph = CTA. */
function parseCaption(text) {
  const paragraphs = text.trim().split(/\n\n+/).map(p => p.trim()).filter(Boolean);
  const cta = paragraphs[paragraphs.length - 1].startsWith('Stay ahead')
    ? paragraphs[paragraphs.length - 1]
    : '';
  const contentParagraphs = cta ? paragraphs.slice(0, -1) : paragraphs;
  const title       = contentParagraphs[0] || '';
  const description = contentParagraphs.slice(1).join('\n\n');
  return { title, description, cta };
}

async function uploadFile(filePath, attempt = 1) {
  const stats    = fs.statSync(filePath);
  const fileName = path.basename(filePath);

  const urlRes = await fetch(`${API}/v1/media/create-upload-url`, {
    method:  'POST',
    headers: apiHeaders(),
    body:    JSON.stringify({ name: fileName, mime_type: 'image/png', size_bytes: stats.size }),
  });
  if (!urlRes.ok) {
    const err = await urlRes.json().catch(() => ({}));
    if (attempt < 4) {
      await new Promise(r => setTimeout(r, attempt * 2000));
      return uploadFile(filePath, attempt + 1);
    }
    throw new Error(`Upload URL failed for ${fileName}: ${JSON.stringify(err)}`);
  }
  const { media_id, upload_url } = await urlRes.json();

  const putRes = await fetch(upload_url, {
    method:  'PUT',
    headers: { 'Content-Type': 'image/png' },
    body:    fs.readFileSync(filePath),
  });
  if (!putRes.ok) {
    if (attempt < 4) {
      await new Promise(r => setTimeout(r, attempt * 2000));
      return uploadFile(filePath, attempt + 1);
    }
    throw new Error(`PUT failed for ${fileName}`);
  }
  return media_id;
}

async function createPost(payload) {
  const res  = await fetch(`${API}/v1/posts`, {
    method:  'POST',
    headers: apiHeaders(),
    body:    JSON.stringify(payload),
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(`Create post failed: ${JSON.stringify(json)}`);
  return json;
}

function moveToScheduled(folderPath) {
  const abs  = path.resolve(folderPath);
  const dest = abs.replace(`${path.sep}to_upload${path.sep}`, `${path.sep}scheduled${path.sep}`);
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.renameSync(abs, dest);
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main() {
  const args      = process.argv.slice(2);
  const dryRun    = args.includes('--dry-run');
  const startIdx  = args.indexOf('--start');
  const startDate = startIdx !== -1 ? args[startIdx + 1] : tomorrow();

  const key         = process.env.POSTBRIDGE_API_KEY;
  const pinterestId = parseInt(process.env.POSTBRIDGE_PINTEREST_ACCOUNT_ID, 10);

  if (!dryRun) {
    if (!key)               { console.error('POSTBRIDGE_API_KEY not set in .env');               process.exit(1); }
    if (isNaN(pinterestId)) { console.error('POSTBRIDGE_PINTEREST_ACCOUNT_ID not set in .env'); process.exit(1); }
  }

  const allFolders = fs.readdirSync(TO_UPLOAD_DIR)
    .filter(f => fs.statSync(path.join(TO_UPLOAD_DIR, f)).isDirectory())
    .sort();

  console.log(`\nFound ${allFolders.length} slide folders`);
  console.log(`Start date:  ${startDate}`);
  console.log(`End date:    ${addDays(startDate, allFolders.length - 1)}`);
  console.log(`Platform:    Pinterest only`);
  console.log(`Posting:     1/day at varied times between 15:00–01:59 CEST`);
  if (dryRun) console.log('\n⚠️  DRY RUN — no API calls will be made\n');

  let posted = 0;
  let errors = 0;

  for (let i = 0; i < allFolders.length; i++) {
    const folder      = path.join(TO_UPLOAD_DIR, allFolders[i]);
    const captionPath = path.join(folder, 'caption.txt');
    const pngPath     = path.join(folder, 'slide.png');
    const dateStr     = addDays(startDate, i);
    const timeUtc     = POST_TIMES_UTC[i % POST_TIMES_UTC.length];
    const scheduledAt = `${dateStr}T${timeUtc}:00Z`;

    if (!fs.existsSync(captionPath) || !fs.existsSync(pngPath)) {
      console.log(`  ⚠️  Skipping ${allFolders[i]} — missing caption.txt or slide.png`);
      errors++;
      continue;
    }

    const { title, description, cta } = parseCaption(fs.readFileSync(captionPath, 'utf8'));
    const caption = [description, cta].filter(Boolean).join('\n\n');

    console.log(`\n[${i + 1}/${allFolders.length}] ${allFolders[i]}`);
    const [utcH, utcM] = timeUtc.split(':').map(Number);
    const cestH = String((utcH + 2) % 24).padStart(2, '0');
    console.log(`  Scheduled: ${dateStr} ${timeUtc} UTC (${cestH}:${String(utcM).padStart(2, '0')} CEST)`);
    console.log(`  Title: ${title}`);

    if (dryRun) { posted++; continue; }

    try {
      process.stdout.write('  Uploading slide.png...');
      const mediaId = await uploadFile(pngPath);
      console.log(' ✓');

      process.stdout.write('  Creating Pinterest post...');
      const post = await createPost({
        caption,
        social_accounts: [pinterestId],
        media:           [mediaId],
        scheduled_at:    scheduledAt,
        platform_configurations: {
          pinterest: { title, caption },
        },
      });
      console.log(` ✓ (id: ${post.id})`);

      moveToScheduled(folder);
      posted++;
    } catch (err) {
      console.error(`\n  ✗ Error: ${err.message}`);
      errors++;
    }

    await new Promise(r => setTimeout(r, 500));
  }

  console.log(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  console.log(`Done! ${posted} scheduled to Pinterest, ${errors} errors.`);
  console.log(`Spread across ${posted} days starting ${startDate}`);
  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`);
}

main().catch(err => { console.error(err); process.exit(1); });
