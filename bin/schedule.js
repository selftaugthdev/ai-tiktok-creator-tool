#!/usr/bin/env node
'use strict';
/**
 * Schedule a generated output folder to Post Bridge.
 *
 * Usage:
 *   node bin/schedule.js --folder output/slides/tiktok/types-of-migraine_1
 *   node bin/schedule.js --folder output/grids/instagram/ways-stress_1 --schedule "2026-04-19T09:00:00Z"
 *
 * Without --schedule, posts are auto-queued to the next available slot in Post Bridge.
 *
 * Required in .env:
 *   POSTBRIDGE_API_KEY
 *   POSTBRIDGE_INSTAGRAM_ACCOUNT_ID
 *   POSTBRIDGE_TIKTOK_ACCOUNT_ID
 */

require('dotenv').config();

const fs   = require('fs');
const path = require('path');
const { Command } = require('commander');

const API = 'https://api.post-bridge.com';

// ── TikTok fixed hashtags (always the same 5) ────────────────────────────────
const TIKTOK_HASHTAGS = '#migraine #migrainerelief #migraineawareness #migrainewarrior #chronicmigraine';

// ── Helpers ───────────────────────────────────────────────────────────────────

function apiHeaders() {
  return {
    Authorization: `Bearer ${process.env.POSTBRIDGE_API_KEY}`,
    'Content-Type': 'application/json',
  };
}

/** Parse caption.txt into { title, description, hashtags, cta } */
function parseCaption(text) {
  // Strip em-dashes just in case
  text = text.replace(/[—–]/g, ',');

  const titleMatch       = text.match(/TITLE:\n([\s\S]*?)\n\nDESCRIPTION:/);
  const descriptionMatch = text.match(/DESCRIPTION:\n([\s\S]*?)\n\nHASHTAGS:/);
  const hashtagsMatch    = text.match(/HASHTAGS:\n([\s\S]*?)(?:\n\n|$)/);

  // CTA is always the last non-empty paragraph
  const paragraphs = text.split(/\n\n+/).map(p => p.trim()).filter(Boolean);
  const cta = paragraphs[paragraphs.length - 1].startsWith('Stay ahead') ? paragraphs[paragraphs.length - 1] : '';

  return {
    title:       titleMatch       ? titleMatch[1].trim()       : '',
    description: descriptionMatch ? descriptionMatch[1].trim() : '',
    hashtags:    hashtagsMatch    ? hashtagsMatch[1].trim()    : '',
    cta,
  };
}

/** Find all PNG files in a folder (sorted so slide_01 comes before slide_02). */
function findPngs(folder) {
  return fs.readdirSync(folder)
    .filter(f => f.endsWith('.png'))
    .sort()
    .map(f => path.join(folder, f));
}

/** Two-step Post Bridge media upload. Returns media_id. */
async function uploadFile(filePath) {
  const stats    = fs.statSync(filePath);
  const fileName = path.basename(filePath);

  // Step 1: get signed upload URL
  const urlRes = await fetch(`${API}/v1/media/create-upload-url`, {
    method:  'POST',
    headers: apiHeaders(),
    body:    JSON.stringify({ name: fileName, mime_type: 'image/png', size_bytes: stats.size }),
  });
  if (!urlRes.ok) {
    const err = await urlRes.json().catch(() => ({}));
    throw new Error(`Failed to get upload URL for ${fileName}: ${JSON.stringify(err)}`);
  }
  const { media_id, upload_url } = await urlRes.json();

  // Step 2: PUT the file to the signed URL
  const fileBuffer = fs.readFileSync(filePath);
  const putRes = await fetch(upload_url, {
    method:  'PUT',
    headers: { 'Content-Type': 'image/png' },
    body:    fileBuffer,
  });
  if (!putRes.ok) throw new Error(`Failed to upload file ${fileName} to signed URL`);

  return media_id;
}

/** Create a post via Post Bridge API. */
async function createPost(payload) {
  const res = await fetch(`${API}/v1/posts`, {
    method:  'POST',
    headers: apiHeaders(),
    body:    JSON.stringify(payload),
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(`Failed to create post: ${JSON.stringify(json)}`);
  return json;
}

// ── Main ──────────────────────────────────────────────────────────────────────

const program = new Command();

program
  .name('schedule')
  .description('Schedule a generated output folder to Instagram and TikTok via Post Bridge.')
  .requiredOption('--folder <path>', 'Path to the generated output folder (must contain a caption.txt and PNG file(s)).')
  .option('--schedule <datetime>', 'ISO 8601 datetime to schedule (e.g. 2026-04-19T09:00:00Z). Omit to use Post Bridge auto-queue.')
  .option('--tiktok-only', 'Only post to TikTok.')
  .option('--instagram-only', 'Only post to Instagram.')
  .action(async (opts) => {
    const key = process.env.POSTBRIDGE_API_KEY;
    if (!key) { console.error('POSTBRIDGE_API_KEY not set in .env'); process.exit(1); }

    const igId     = parseInt(process.env.POSTBRIDGE_INSTAGRAM_ACCOUNT_ID, 10);
    const tiktokId = parseInt(process.env.POSTBRIDGE_TIKTOK_ACCOUNT_ID, 10);

    if (!opts.instagramOnly && isNaN(tiktokId)) {
      console.error('POSTBRIDGE_TIKTOK_ACCOUNT_ID not set in .env. Run: node bin/list-accounts.js');
      process.exit(1);
    }
    if (!opts.tiktokOnly && isNaN(igId)) {
      console.error('POSTBRIDGE_INSTAGRAM_ACCOUNT_ID not set in .env. Run: node bin/list-accounts.js');
      process.exit(1);
    }

    const folder = opts.folder;
    if (!fs.existsSync(folder)) { console.error(`Folder not found: ${folder}`); process.exit(1); }

    const captionPath = path.join(folder, 'caption.txt');
    if (!fs.existsSync(captionPath)) { console.error(`No caption.txt found in ${folder}`); process.exit(1); }

    const pngs = findPngs(folder);
    if (!pngs.length) { console.error(`No PNG files found in ${folder}`); process.exit(1); }

    console.log(`\nScheduling: ${folder}`);
    console.log(`Found ${pngs.length} PNG(s): ${pngs.map(p => path.basename(p)).join(', ')}`);

    // ── Parse caption ─────────────────────────────────────────────────────────
    const raw = fs.readFileSync(captionPath, 'utf8');
    const { title, description, hashtags, cta } = parseCaption(raw);

    if (!description) { console.error('Could not parse description from caption.txt'); process.exit(1); }

    // ── Upload media ─────────────────────────────────────────────────────────
    console.log('\nUploading media...');
    const mediaIds = [];
    for (const png of pngs) {
      process.stdout.write(`  Uploading ${path.basename(png)}...`);
      const id = await uploadFile(png);
      mediaIds.push(id);
      console.log(` ✓ (${id})`);
    }

    const scheduling = opts.schedule
      ? { scheduled_at: opts.schedule }
      : { use_queue: true };

    // ── TikTok post ───────────────────────────────────────────────────────────
    if (!opts.instagramOnly) {
      const tiktokCaption = [description, cta, TIKTOK_HASHTAGS].filter(Boolean).join('\n\n');

      const tiktokPayload = {
        caption:         tiktokCaption,
        social_accounts: [tiktokId],
        media:           mediaIds,
        platform_configurations: {
          tiktok: {
            title:   title || undefined,
            caption: tiktokCaption,
            draft:   true,   // send to TikTok inbox
          },
        },
        ...scheduling,
      };

      process.stdout.write('\nCreating TikTok post (→ inbox)...');
      const tiktokPost = await createPost(tiktokPayload);
      console.log(` ✓ (post id: ${tiktokPost.id})`);
    }

    // ── Instagram post ────────────────────────────────────────────────────────
    if (!opts.tiktokOnly) {
      const igCaption = [description, cta, hashtags].filter(Boolean).join('\n\n');

      const igPayload = {
        caption:         igCaption,
        social_accounts: [igId],
        media:           mediaIds,
        platform_configurations: {
          instagram: {
            caption: igCaption,
          },
        },
        ...scheduling,
      };

      process.stdout.write('\nCreating Instagram post...');
      const igPost = await createPost(igPayload);
      console.log(` ✓ (post id: ${igPost.id})`);
    }

    const when = opts.schedule || 'next queue slot';
    console.log(`\nDone! Scheduled for: ${when}\n`);
  });

program.parse(process.argv);
