#!/usr/bin/env node
'use strict';
/**
 * One-time helper — lists all connected Post Bridge social accounts.
 * Run once to find your Instagram and TikTok account IDs, then add them to .env:
 *   POSTBRIDGE_INSTAGRAM_ACCOUNT_ID=123
 *   POSTBRIDGE_TIKTOK_ACCOUNT_ID=456
 */

require('dotenv').config();

const API = 'https://api.post-bridge.com';

async function main() {
  const key = process.env.POSTBRIDGE_API_KEY;
  if (!key) { console.error('POSTBRIDGE_API_KEY not set in .env'); process.exit(1); }

  const res = await fetch(`${API}/v1/social-accounts?limit=50`, {
    headers: { Authorization: `Bearer ${key}` },
  });
  const json = await res.json();

  if (!res.ok) { console.error('API error:', json); process.exit(1); }

  console.log('\nConnected social accounts:\n');
  for (const a of json.data) {
    console.log(`  ID: ${a.id}  |  Platform: ${a.platform}  |  Username: ${a.username}`);
  }
  console.log('\nAdd the relevant IDs to your .env:');
  console.log('  POSTBRIDGE_INSTAGRAM_ACCOUNT_ID=<id>');
  console.log('  POSTBRIDGE_TIKTOK_ACCOUNT_ID=<id>\n');
}

main();
