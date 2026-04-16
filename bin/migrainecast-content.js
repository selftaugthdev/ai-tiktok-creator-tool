#!/usr/bin/env node
'use strict';

require('dotenv').config();

const { Command } = require('commander');
const { runSlide } = require('../src/commands/slide');
const { runGrid } = require('../src/commands/grid');

const program = new Command();

program
  .name('migrainecast-content')
  .description('Generate MigraineCast TikTok content assets.')
  .version('1.0.0');

program
  .command('slide')
  .description('Generate a single photo post slide (1080x1920 TikTok or 1080x1350 Instagram PNG).')
  .requiredOption('--topic <topic>', 'Headline shown at the top of the slide.')
  .requiredOption('--output <dir>', 'Output directory — slide.png will be saved here.')
  .option('--platform <platform>', 'Target platform: tiktok (default) or instagram.', 'tiktok')
  .action(async (opts) => {
    if (!process.env.ANTHROPIC_API_KEY) {
      console.error('Error: ANTHROPIC_API_KEY is not set. Add it to your .env file.');
      process.exit(1);
    }
    if (!['tiktok', 'instagram'].includes(opts.platform)) {
      console.error('Error: --platform must be tiktok or instagram.');
      process.exit(1);
    }
    await runSlide(opts);
  });

program
  .command('grid')
  .description('Generate a "N Things About X" infographic (1080x1920 TikTok or 1080x1350 Instagram PNG).')
  .requiredOption('--topic <topic>', 'Topic for the infographic (e.g. "migraine trigger foods").')
  .requiredOption('--output <dir>', 'Output directory — infographic.png will be saved here.')
  .option('--platform <platform>', 'Target platform: tiktok (default) or instagram.', 'tiktok')
  .action(async (opts) => {
    if (!process.env.ANTHROPIC_API_KEY) {
      console.error('Error: ANTHROPIC_API_KEY is not set. Add it to your .env file.');
      process.exit(1);
    }
    if (!['tiktok', 'instagram'].includes(opts.platform)) {
      console.error('Error: --platform must be tiktok or instagram.');
      process.exit(1);
    }
    await runGrid(opts);
  });

program.parse(process.argv);
