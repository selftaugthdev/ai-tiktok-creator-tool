#!/usr/bin/env node
'use strict';
/**
 * One-time script: schedule 16 V2 Sandra carousels to TikTok via PostBridge.
 *
 * Schedule:
 *   2026-05-26 (today):     1 post in ~15 min from launch
 *   2026-05-27 (Wed) – 2026-05-31 (Sun):  3/day
 *     Morning:   08–10 Brussels = 06–08 UTC
 *     Afternoon: 14–16 Brussels = 12–14 UTC
 *     Evening:   20–22 Brussels = 18–20 UTC
 *
 * Usage:
 *   node bin/bulk-schedule-sandra-v2.js
 *   node bin/bulk-schedule-sandra-v2.js --dry-run
 */

require('dotenv').config();

const fs   = require('fs');
const path = require('path');

const TO_UPLOAD_DIR    = 'output/to-upload/MigraineCast/tiktok/sandra/to_upload';
const API              = 'https://api.post-bridge.com';
const FORCED_HASHTAGS  = '#migraine #migrainerelief #migraineawareness #chronicpain #migrainewarrior';

// ── Schedule ──────────────────────────────────────────────────────────────────
// First slot is computed as now + 15 min. Rest are hardcoded UTC times.
function buildSchedule() {
  const firstAt = new Date(Date.now() + 15 * 60 * 1000);
  const firstUtc = `${String(firstAt.getUTCHours()).padStart(2, '0')}:${String(firstAt.getUTCMinutes()).padStart(2, '0')}`;

  return [
    // Today May 26 — one immediate post
    { date: '2026-05-26', timeUtc: firstUtc, slot: 'now+15min' },

    // Wednesday May 27
    { date: '2026-05-27', timeUtc: '06:15', slot: 'morning'   },
    { date: '2026-05-27', timeUtc: '12:20', slot: 'afternoon' },
    { date: '2026-05-27', timeUtc: '18:20', slot: 'evening'   },

    // Thursday May 28
    { date: '2026-05-28', timeUtc: '07:05', slot: 'morning'   },
    { date: '2026-05-28', timeUtc: '13:10', slot: 'afternoon' },
    { date: '2026-05-28', timeUtc: '19:05', slot: 'evening'   },

    // Friday May 29
    { date: '2026-05-29', timeUtc: '06:45', slot: 'morning'   },
    { date: '2026-05-29', timeUtc: '12:45', slot: 'afternoon' },
    { date: '2026-05-29', timeUtc: '18:45', slot: 'evening'   },

    // Saturday May 30
    { date: '2026-05-30', timeUtc: '07:30', slot: 'morning'   },
    { date: '2026-05-30', timeUtc: '13:35', slot: 'afternoon' },
    { date: '2026-05-30', timeUtc: '19:30', slot: 'evening'   },

    // Sunday May 31
    { date: '2026-05-31', timeUtc: '06:05', slot: 'morning'   },
    { date: '2026-05-31', timeUtc: '12:05', slot: 'afternoon' },
    { date: '2026-05-31', timeUtc: '18:05', slot: 'evening'   },
  ];
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function apiHeaders() {
  return {
    Authorization: `Bearer ${process.env.POSTBRIDGE_API_KEY}`,
    'Content-Type': 'application/json',
  };
}

function utcToBrussels(utcTime) {
  const [h, m] = utcTime.split(':').map(Number);
  return `${String((h + 2) % 24).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

/** Parse TITLE / DESCRIPTION sections from caption.txt; hashtags are forced. */
function parseCaption(text) {
  const titleMatch = text.match(/^TITLE:\s*\n([\s\S]*?)(?=\n(?:DESCRIPTION|HASHTAGS):|$)/m);
  const descMatch  = text.match(/^DESCRIPTION:\s*\n([\s\S]*?)(?=\n(?:TITLE|HASHTAGS):|$)/m);

  const title       = titleMatch ? titleMatch[1].trim() : '';
  const description = descMatch  ? descMatch[1].trim()  : text.trim();
  return { title, description, hashtags: FORCED_HASHTAGS };
}

/** Upload a single file, with up to 5 retries. */
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

function moveToScheduled(folderPath) {
  const abs  = path.resolve(folderPath);
  const dest = abs.replace(`${path.sep}to_upload${path.sep}`, `${path.sep}scheduled${path.sep}`);
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.renameSync(abs, dest);
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main() {
  const args   = process.argv.slice(2);
  const dryRun = args.includes('--dry-run');

  const key      = process.env.POSTBRIDGE_API_KEY;
  const tiktokId = parseInt(process.env.POSTBRIDGE_TIKTOK_ACCOUNT_ID, 10);

  if (!dryRun) {
    if (!key)            { console.error('POSTBRIDGE_API_KEY not set in .env');            process.exit(1); }
    if (isNaN(tiktokId)) { console.error('POSTBRIDGE_TIKTOK_ACCOUNT_ID not set in .env'); process.exit(1); }
  }

  const schedule = buildSchedule();

  // Collect all -v2 carousel folders sorted numerically
  const allFolders = fs.readdirSync(TO_UPLOAD_DIR)
    .filter(f => f.endsWith('-v2') && fs.statSync(path.join(TO_UPLOAD_DIR, f)).isDirectory())
    .sort((a, b) => {
      const numA = parseInt(a.match(/carousel_(\d+)/)?.[1] ?? '0', 10);
      const numB = parseInt(b.match(/carousel_(\d+)/)?.[1] ?? '0', 10);
      return numA - numB;
    })
    .slice(0, schedule.length);

  if (allFolders.length === 0) {
    console.error(`No V2 carousels found in ${TO_UPLOAD_DIR}`);
    process.exit(1);
  }

  const count = Math.min(allFolders.length, schedule.length);

  console.log(`\nV2 Sandra — TikTok draft scheduler`);
  console.log(`Found ${allFolders.length} V2 carousels, scheduling ${count}`);
  console.log(`Platform:    TikTok (drafts)`);
  console.log(`Windows:     08–10, 14–16, 20–22 Brussels (UTC+2)`);
  console.log(`Hashtags:    ${FORCED_HASHTAGS}`);
  if (dryRun) console.log('\n⚠️  DRY RUN — no API calls will be made\n');
  else        console.log('');

  let posted = 0;
  let errors = 0;

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

    const { title, description, hashtags } = parseCaption(fs.readFileSync(captionPath, 'utf8'));
    const caption = [description, hashtags].filter(Boolean).join('\n\n');

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

      moveToScheduled(folder);
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
