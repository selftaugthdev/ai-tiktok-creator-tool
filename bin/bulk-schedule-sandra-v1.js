#!/usr/bin/env node
'use strict';
/**
 * Schedule all -v1 Sandra carousels to TikTok via PostBridge.
 *
 * Schedule: 2 per day — one morning (08–10 CEST), one evening (19–21 CEST).
 * Brussels is CEST (UTC+2) in May/June, so windows in UTC:
 *   Morning: 06:00–08:00 UTC
 *   Evening: 17:00–19:00 UTC
 *
 * Usage:
 *   node bin/bulk-schedule-sandra-v1.js
 *   node bin/bulk-schedule-sandra-v1.js --start 2026-05-07   # override start date
 *   node bin/bulk-schedule-sandra-v1.js --dry-run            # preview, no API calls
 */

require('dotenv').config();

const fs   = require('fs');
const path = require('path');

const TO_UPLOAD_DIR = 'output/to-upload/MigraineCast/tiktok/sandra/to_upload';
const API           = 'https://api.post-bridge.com';

// Staggered times within each window (UTC) so posts don't all land at the same minute
const MORNING_TIMES_UTC = [
  '06:15', '07:05', '06:45', '07:30', '06:05',
  '07:15', '06:35', '07:45', '06:20', '07:00',
  '06:50', '07:20',
];
const EVENING_TIMES_UTC = [
  '17:20', '18:05', '17:45', '18:30', '17:05',
  '18:15', '17:35', '18:50', '17:15', '18:00',
  '17:50', '18:25',
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

function utcToCest(utcTime) {
  const [h, m] = utcTime.split(':').map(Number);
  return `${String((h + 2) % 24).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

/** Parse caption.txt with labeled sections: TITLE: / DESCRIPTION: / HASHTAGS: */
function parseCaption(text) {
  const titleMatch  = text.match(/^TITLE:\s*\n([\s\S]*?)(?=\n(?:DESCRIPTION|HASHTAGS):|$)/m);
  const descMatch   = text.match(/^DESCRIPTION:\s*\n([\s\S]*?)(?=\n(?:TITLE|HASHTAGS):|$)/m);
  const tagsMatch   = text.match(/^HASHTAGS:\s*\n([\s\S]*?)(?=\n(?:TITLE|DESCRIPTION):|$)/m);

  const title       = titleMatch  ? titleMatch[1].trim()  : '';
  const description = descMatch   ? descMatch[1].trim()   : '';
  const hashtags    = tagsMatch   ? tagsMatch[1].trim()   : '';
  return { title, description, hashtags };
}

/** Upload a single file, with up to 3 retries. */
async function uploadFile(filePath, attempt = 1) {
  const stats    = fs.statSync(filePath);
  const fileName = path.basename(filePath);

  const urlRes = await fetch(`${API}/v1/media/create-upload-url`, {
    method:  'POST',
    headers: apiHeaders(),
    body:    JSON.stringify({ name: fileName, mime_type: 'image/png', size_bytes: stats.size }),
  });
  if (!urlRes.ok) {
    if (attempt < 4) {
      await new Promise(r => setTimeout(r, attempt * 2000));
      return uploadFile(filePath, attempt + 1);
    }
    const err = await urlRes.json().catch(() => ({}));
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

  const key      = process.env.POSTBRIDGE_API_KEY;
  const tiktokId = parseInt(process.env.POSTBRIDGE_TIKTOK_ACCOUNT_ID, 10);

  if (!dryRun) {
    if (!key)            { console.error('POSTBRIDGE_API_KEY not set in .env');        process.exit(1); }
    if (isNaN(tiktokId)) { console.error('POSTBRIDGE_TIKTOK_ACCOUNT_ID not set in .env'); process.exit(1); }
  }

  // Collect all -v1 carousel folders, sorted numerically by carousel number
  const allFolders = fs.readdirSync(TO_UPLOAD_DIR)
    .filter(f => f.endsWith('-v1') && fs.statSync(path.join(TO_UPLOAD_DIR, f)).isDirectory())
    .sort((a, b) => {
      const numA = parseInt(a.match(/carousel_(\d+)/)?.[1] ?? '0', 10);
      const numB = parseInt(b.match(/carousel_(\d+)/)?.[1] ?? '0', 10);
      return numA - numB;
    });

  const totalDays = Math.ceil(allFolders.length / 2);
  const endDate   = addDays(startDate, totalDays - 1);

  console.log(`\nFound ${allFolders.length} v1 carousels`);
  console.log(`Start date:  ${startDate}`);
  console.log(`End date:    ${endDate}  (${totalDays} days)`);
  console.log(`Platform:    TikTok`);
  console.log(`Schedule:    2/day — morning 08–10 CEST, evening 19–21 CEST`);
  if (dryRun) console.log('\n⚠️  DRY RUN — no API calls will be made\n');

  let posted = 0;
  let errors  = 0;

  for (let i = 0; i < allFolders.length; i++) {
    const dayIndex   = Math.floor(i / 2);
    const isMorning  = i % 2 === 0;
    const timesArray = isMorning ? MORNING_TIMES_UTC : EVENING_TIMES_UTC;
    const timeUtc    = timesArray[dayIndex % timesArray.length];
    const dateStr    = addDays(startDate, dayIndex);
    const scheduledAt = `${dateStr}T${timeUtc}:00Z`;

    const folder      = path.join(TO_UPLOAD_DIR, allFolders[i]);
    const captionPath = path.join(folder, 'caption.txt');

    // Collect slides in order
    const slides = fs.readdirSync(folder)
      .filter(f => /^slide_\d+\.png$/.test(f))
      .sort();

    if (!fs.existsSync(captionPath) || slides.length === 0) {
      console.log(`  ⚠️  Skipping ${allFolders[i]} — missing caption.txt or slides`);
      errors++;
      continue;
    }

    const { title, description, hashtags } = parseCaption(fs.readFileSync(captionPath, 'utf8'));
    const caption = [description, hashtags].filter(Boolean).join('\n\n');
    const slot    = isMorning ? 'morning' : 'evening';

    console.log(`\n[${i + 1}/${allFolders.length}] ${allFolders[i]}`);
    console.log(`  ${dateStr}  ${timeUtc} UTC (${utcToCest(timeUtc)} CEST)  [${slot}]`);
    console.log(`  Title: ${title}`);
    console.log(`  Slides: ${slides.length}`);

    if (dryRun) { posted++; continue; }

    try {
      // Upload all slides sequentially
      const mediaIds = [];
      for (const slide of slides) {
        process.stdout.write(`  Uploading ${slide}...`);
        const mediaId = await uploadFile(path.join(folder, slide));
        mediaIds.push(mediaId);
        console.log(' ✓');
        await new Promise(r => setTimeout(r, 300));
      }

      process.stdout.write('  Creating TikTok post...');
      const post = await createPost({
        caption,
        social_accounts: [tiktokId],
        media:           mediaIds,
        scheduled_at:    scheduledAt,
        platform_configurations: {
          tiktok: { title, caption, draft: true },
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
  console.log(`Done! ${posted} scheduled to TikTok, ${errors} errors.`);
  console.log(`Spread across ${totalDays} days (${startDate} → ${endDate})`);
  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`);
}

main().catch(err => { console.error(err); process.exit(1); });
