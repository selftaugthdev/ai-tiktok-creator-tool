#!/usr/bin/env node
'use strict';
/**
 * Schedule Sandra carousels (carousel_197+) to TikTok via PostBridge.
 *
 * 1 post today (now + 15 min), then 2/day for 11 days:
 *   Morning: 08–10 Brussels (06–08 UTC)
 *   Evening: 19–21 Brussels (17–19 UTC)
 * Brussels is CEST (UTC+2) in June.
 *
 * The forced CTA + hashtag block is appended to every description, replacing
 * whatever caption.txt contains for hashtags/CTA.
 *
 * Usage:
 *   node bin/bulk-schedule-sandra-2x.js
 *   node bin/bulk-schedule-sandra-2x.js --start 2026-06-11
 *   node bin/bulk-schedule-sandra-2x.js --dry-run
 */

require('dotenv').config();

const fs   = require('fs');
const path = require('path');

const TO_UPLOAD_DIR = 'output/to-upload/MigraineCast/tiktok/sandra/to_upload';
const API           = 'https://api.post-bridge.com';

// Only schedule carousels with numbers >= this
const MIN_CAROUSEL_NUM = 197;

const FORCED_BLOCK =
  'Stay ahead of your migraines with the MigraineCast app, link in Bio, download for free in the App store or at www.migrainecast.app\n\n' +
  '#migraine #migrainerelief #migraineawareness #migrainerelieftok #migrainewarrior';

// Staggered times within each UTC window, cycling across days
const MORNING_TIMES_UTC = [
  '06:15', '07:05', '06:45', '07:30', '06:05', '07:15', '06:35',
];
const EVENING_TIMES_UTC = [
  '17:20', '18:05', '17:45', '18:30', '17:05', '18:15', '17:35',
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

function utcToBrussels(utcTime) {
  const [h, m] = utcTime.split(':').map(Number);
  return `${String((h + 2) % 24).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

/** Build the 23-slot schedule: 1 post today (now+15min), then 2/day for 11 days. */
function buildSchedule(today) {
  const firstAt   = new Date(Date.now() + 15 * 60 * 1000);
  const firstUtc  = `${String(firstAt.getUTCHours()).padStart(2, '0')}:${String(firstAt.getUTCMinutes()).padStart(2, '0')}`;

  const schedule = [{ date: today, timeUtc: firstUtc, slot: 'now+15min' }];

  for (let day = 1; day <= 11; day++) {
    const dateStr = addDays(today, day);
    schedule.push({ date: dateStr, timeUtc: MORNING_TIMES_UTC[(day - 1) % MORNING_TIMES_UTC.length], slot: 'morning' });
    schedule.push({ date: dateStr, timeUtc: EVENING_TIMES_UTC[(day - 1) % EVENING_TIMES_UTC.length], slot: 'evening' });
  }

  return schedule;
}

/** Extract TITLE and DESCRIPTION from caption.txt, then append the forced CTA/hashtag block. */
function parseCaption(text) {
  const titleMatch = text.match(/^TITLE:\s*\n([\s\S]*?)(?=\n(?:DESCRIPTION|HASHTAGS):|$)/m);
  const descMatch  = text.match(/^DESCRIPTION:\s*\n([\s\S]*?)(?=\n(?:TITLE|HASHTAGS):|$)/m);

  const title = titleMatch ? titleMatch[1].trim() : '';
  let description = descMatch ? descMatch[1].trim() : text.trim();

  // Strip any embedded CTA line the generator already added — we replace it with FORCED_BLOCK.
  description = description.replace(/\n*Stay ahead of your migraines[^\n]*www\.migrainecast\.app\.?/gi, '').trim();

  const caption = `${description}\n\n${FORCED_BLOCK}`;
  return { title, caption };
}

/** Upload a single file, with up to 5 retries (catches both HTTP errors and socket errors). */
async function uploadFile(filePath, attempt = 1) {
  const stats    = fs.statSync(filePath);
  const fileName = path.basename(filePath);

  try {
    const urlRes = await fetch(`${API}/v1/media/create-upload-url`, {
      method:  'POST',
      headers: apiHeaders(),
      body:    JSON.stringify({ name: fileName, mime_type: 'image/png', size_bytes: stats.size }),
    });
    if (!urlRes.ok) {
      const err = await urlRes.json().catch(() => ({}));
      throw new Error(`Upload URL failed for ${fileName}: ${JSON.stringify(err)}`);
    }
    const { media_id, upload_url } = await urlRes.json();

    const putRes = await fetch(upload_url, {
      method:  'PUT',
      headers: { 'Content-Type': 'image/png' },
      body:    fs.readFileSync(filePath),
    });
    if (!putRes.ok) throw new Error(`PUT failed for ${fileName}`);

    return media_id;
  } catch (err) {
    if (attempt < 6) {
      const delay = attempt * 3000;
      process.stdout.write(` (retry ${attempt}, waiting ${delay / 1000}s...)`);
      await new Promise(r => setTimeout(r, delay));
      return uploadFile(filePath, attempt + 1);
    }
    throw err;
  }
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

function moveToUploaded(folderPath) {
  const abs  = path.resolve(folderPath);
  const dest = abs
    .replace(`${path.sep}to-upload${path.sep}`, `${path.sep}uploaded${path.sep}`)
    .replace(`${path.sep}to_upload${path.sep}`, `${path.sep}uploaded${path.sep}`);
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.renameSync(abs, dest);
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main() {
  const args      = process.argv.slice(2);
  const dryRun    = args.includes('--dry-run');
  const startIdx  = args.indexOf('--start');
  const today     = startIdx !== -1 ? args[startIdx + 1] : new Date().toISOString().slice(0, 10);

  const key      = process.env.POSTBRIDGE_API_KEY;
  const tiktokId = parseInt(process.env.POSTBRIDGE_TIKTOK_ACCOUNT_ID, 10);

  if (!dryRun) {
    if (!key)            { console.error('POSTBRIDGE_API_KEY not set in .env');            process.exit(1); }
    if (isNaN(tiktokId)) { console.error('POSTBRIDGE_TIKTOK_ACCOUNT_ID not set in .env'); process.exit(1); }
  }

  const schedule = buildSchedule(today);

  // Collect qualifying folders: carousel number >= MIN_CAROUSEL_NUM, no -vN suffix
  const allFolders = fs.readdirSync(TO_UPLOAD_DIR)
    .filter(f => {
      if (!fs.statSync(path.join(TO_UPLOAD_DIR, f)).isDirectory()) return false;
      if (/-v\d+$/.test(f)) return false;
      const num = parseInt(f.match(/carousel_(\d+)/)?.[1] ?? '0', 10);
      return num >= MIN_CAROUSEL_NUM;
    })
    .sort((a, b) => {
      const numA = parseInt(a.match(/carousel_(\d+)/)?.[1] ?? '0', 10);
      const numB = parseInt(b.match(/carousel_(\d+)/)?.[1] ?? '0', 10);
      return numA - numB;
    })
    .slice(0, schedule.length);

  if (allFolders.length === 0) {
    console.error(`No eligible carousels found in ${TO_UPLOAD_DIR}`);
    process.exit(1);
  }

  console.log(`\nFound ${allFolders.length} carousels, scheduling ${Math.min(allFolders.length, schedule.length)}`);
  console.log(`Platform:    TikTok (drafts)`);
  console.log(`Schedule:    1 today (now+15min), then 2/day — morning 08–10, evening 19–21 Brussels (UTC+2)`);
  if (dryRun) console.log('\n⚠️  DRY RUN — no API calls will be made\n');
  else        console.log('');

  let posted = 0;
  let errors = 0;
  const count = Math.min(allFolders.length, schedule.length);

  for (let i = 0; i < count; i++) {
    const { date, timeUtc, slot } = schedule[i];
    const scheduledAt = `${date}T${timeUtc}:00Z`;

    const folder      = path.join(TO_UPLOAD_DIR, allFolders[i]);
    const captionPath = path.join(folder, 'caption.txt');

    const slides = fs.readdirSync(folder)
      .filter(f => /^slide_\d+\.png$/.test(f))
      .sort();

    if (!fs.existsSync(captionPath) || slides.length === 0) {
      console.log(`  ⚠️  Skipping ${allFolders[i]} — missing caption.txt or slides`);
      errors++;
      continue;
    }

    const { title, caption } = parseCaption(fs.readFileSync(captionPath, 'utf8'));

    console.log(`\n[${i + 1}/${count}] ${allFolders[i]}`);
    console.log(`  ${date}  ${timeUtc} UTC (${utcToBrussels(timeUtc)} Brussels)  [${slot}]`);
    console.log(`  Title: ${title}`);
    console.log(`  Slides: ${slides.length}`);

    if (dryRun) { posted++; continue; }

    try {
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

      moveToUploaded(folder);
      posted++;
    } catch (err) {
      console.error(`\n  ✗ Error: ${err.message}`);
      errors++;
    }

    await new Promise(r => setTimeout(r, 500));
  }

  console.log(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  console.log(`Done! ${posted} scheduled to TikTok as drafts, ${errors} errors.`);
  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`);
}

main().catch(err => { console.error(err); process.exit(1); });
