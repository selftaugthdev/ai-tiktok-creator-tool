#!/usr/bin/env node
'use strict';
/**
 * Bulk-schedule all grids in output/grids/tiktok/to_upload/ to Pinterest + TikTok.
 *
 * Schedule:
 *   - Pinterest: all 90 grids, 3/day at 06:00 / 11:00 / 17:00 UTC
 *   - TikTok:    1st post of each day only (06:00 UTC), sent as draft to inbox
 *
 * Usage:
 *   node bin/bulk-schedule-grids.js
 *   node bin/bulk-schedule-grids.js --start 2026-05-01   # override start date
 *   node bin/bulk-schedule-grids.js --dry-run            # preview schedule, no API calls
 */

require('dotenv').config();

const fs   = require('fs');
const path = require('path');

const TO_UPLOAD_DIR = 'output/grids/tiktok/to_upload';
const API           = 'https://api.post-bridge.com';

// Post times (UTC) — 08:00, 13:00, 19:00 CEST
const DAILY_TIMES_UTC = ['06:00', '11:00', '17:00'];

// ── Helpers ───────────────────────────────────────────────────────────────────

function apiHeaders() {
  return {
    Authorization: `Bearer ${process.env.POSTBRIDGE_API_KEY}`,
    'Content-Type': 'application/json',
  };
}

function isoDateTime(dateStr, timeUtc) {
  return `${dateStr}T${timeUtc}:00Z`;
}

/** Add N days to a YYYY-MM-DD string. */
function addDays(dateStr, n) {
  const d = new Date(`${dateStr}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

/** Tomorrow as YYYY-MM-DD. */
function tomorrow() {
  return addDays(new Date().toISOString().slice(0, 10), 1);
}

/** Parse caption.txt — first line = title, emoji lines = description, last paragraph = CTA. */
function parseCaption(text) {
  const lines      = text.trim().split('\n');
  const title      = lines[0].trim();
  const ctaLine    = lines[lines.length - 1].startsWith('Stay ahead') ? lines[lines.length - 1].trim() : '';
  const bodyLines  = lines.slice(1, ctaLine ? lines.length - 1 : undefined).filter(l => l.trim());
  const description = bodyLines.join('\n').trim();
  return { title, description, cta: ctaLine };
}

/** Deduplicate folders: keep only the first (lowest _N) per base slug. */
function deduplicateFolders(folders) {
  const seen = new Set();
  const result = [];
  for (const f of folders.sort()) {
    const base = f.replace(/_\d+$/, '');
    if (!seen.has(base)) {
      seen.add(base);
      result.push(f);
    }
  }
  return result;
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
  const args    = process.argv.slice(2);
  const dryRun  = args.includes('--dry-run');
  const startIdx = args.indexOf('--start');
  const startDate = startIdx !== -1 ? args[startIdx + 1] : tomorrow();

  const key          = process.env.POSTBRIDGE_API_KEY;
  const pinterestId  = parseInt(process.env.POSTBRIDGE_PINTEREST_ACCOUNT_ID, 10);
  const tiktokId     = parseInt(process.env.POSTBRIDGE_TIKTOK_ACCOUNT_ID, 10);

  if (!dryRun) {
    if (!key)              { console.error('POSTBRIDGE_API_KEY not set in .env');           process.exit(1); }
    if (isNaN(pinterestId)){ console.error('POSTBRIDGE_PINTEREST_ACCOUNT_ID not set in .env'); process.exit(1); }
    if (isNaN(tiktokId))   { console.error('POSTBRIDGE_TIKTOK_ACCOUNT_ID not set in .env');    process.exit(1); }
  }

  // ── Load & deduplicate folders ────────────────────────────────────────────
  const allFolders = fs.readdirSync(TO_UPLOAD_DIR)
    .filter(f => fs.statSync(path.join(TO_UPLOAD_DIR, f)).isDirectory());

  const folders = deduplicateFolders(allFolders).slice(0, 90);

  console.log(`\nFound ${allFolders.length} folders → ${folders.length} unique grids after dedup`);
  console.log(`Start date: ${startDate}`);
  console.log(`Schedule: 3/day Pinterest | 1/day TikTok (first slot)`);
  console.log(`End date:  ${addDays(startDate, Math.ceil(folders.length / 3) - 1)}`);
  if (dryRun) console.log('\n⚠️  DRY RUN — no API calls will be made\n');

  let dayIndex  = 0;
  let slotIndex = 0;
  let posted    = 0;
  let errors    = 0;

  for (let i = 0; i < folders.length; i++) {
    dayIndex  = Math.floor(i / 3);
    slotIndex = i % 3;

    const folder      = path.join(TO_UPLOAD_DIR, folders[i]);
    const captionPath = path.join(folder, 'caption.txt');
    const pngPath     = path.join(folder, 'infographic.png');
    const dateStr     = addDays(startDate, dayIndex);
    const timeUtc     = DAILY_TIMES_UTC[slotIndex];
    const scheduledAt = isoDateTime(dateStr, timeUtc);
    const isFirstSlot = slotIndex === 0;

    if (!fs.existsSync(captionPath) || !fs.existsSync(pngPath)) {
      console.log(`  ⚠️  Skipping ${folders[i]} — missing caption.txt or infographic.png`);
      errors++;
      continue;
    }

    const { title, description, cta } = parseCaption(fs.readFileSync(captionPath, 'utf8'));
    const pinterestCaption = [description, cta].filter(Boolean).join('\n\n');
    const tiktokCaption    = [description, cta, '#migraine #migrainerelief #migraineawareness #migrainewarrior #chronicmigraine'].filter(Boolean).join('\n\n');

    console.log(`\n[${i + 1}/${folders.length}] ${folders[i]}`);
    console.log(`  Date: ${dateStr} ${timeUtc} UTC${isFirstSlot ? '  ← TikTok too' : ''}`);
    console.log(`  Title: ${title}`);

    if (dryRun) { posted++; continue; }

    try {
      // Upload image
      process.stdout.write('  Uploading image...');
      const mediaId = await uploadFile(pngPath);
      console.log(` ✓`);

      // Pinterest
      process.stdout.write('  Pinterest...');
      const pinPost = await createPost({
        caption:         pinterestCaption,
        social_accounts: [pinterestId],
        media:           [mediaId],
        scheduled_at:    scheduledAt,
        platform_configurations: {
          pinterest: { title, caption: pinterestCaption },
        },
      });
      console.log(` ✓ (id: ${pinPost.id})`);

      // TikTok — first slot of each day only
      if (isFirstSlot) {
        process.stdout.write('  TikTok (draft)...');
        const ttPost = await createPost({
          caption:         tiktokCaption,
          social_accounts: [tiktokId],
          media:           [mediaId],
          scheduled_at:    scheduledAt,
          platform_configurations: {
            tiktok: { title, caption: tiktokCaption, draft: true },
          },
        });
        console.log(` ✓ (id: ${ttPost.id})`);
      }

      moveToScheduled(folder);
      posted++;
    } catch (err) {
      console.error(`\n  ✗ Error: ${err.message}`);
      errors++;
    }

    // Small delay between API calls to avoid rate limiting
    await new Promise(r => setTimeout(r, 500));
  }

  console.log(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  console.log(`Done! ${posted} scheduled, ${errors} errors.`);
  console.log(`Pinterest: ${posted} posts over ${Math.ceil(posted / 3)} days`);
  console.log(`TikTok:    ${Math.ceil(posted / 3)} posts (1/day, drafts in inbox)`);
  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`);
}

main().catch(err => { console.error(err); process.exit(1); });
