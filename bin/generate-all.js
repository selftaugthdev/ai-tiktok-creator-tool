#!/usr/bin/env node
'use strict';

require('dotenv').config();

const { Command } = require('commander');
const { runSlide } = require('../src/commands/slide');
const { runGrid } = require('../src/commands/grid');

const program = new Command();

program
  .name('generate-all')
  .description('Generate all 4 assets for a topic: slide + grid for both TikTok and Instagram.')
  .requiredOption('--topic <topic>', 'Topic for all assets.')
  .action(async (opts) => {
    if (!process.env.ANTHROPIC_API_KEY) {
      console.error('Error: ANTHROPIC_API_KEY is not set. Add it to your .env file.');
      process.exit(1);
    }

    const { topic } = opts;

    const jobs = [
      { fn: runSlide, label: 'Slide   — TikTok',    args: { topic, output: 'output/slides/tiktok',    platform: 'tiktok'   } },
      { fn: runSlide, label: 'Slide   — Instagram', args: { topic, output: 'output/slides/instagram', platform: 'instagram' } },
      { fn: runGrid,  label: 'Grid    — TikTok',    args: { topic, output: 'output/grids/tiktok',     platform: 'tiktok'   } },
      { fn: runGrid,  label: 'Grid    — Instagram', args: { topic, output: 'output/grids/instagram',  platform: 'instagram' } },
    ];

    console.log(`\nGenerating all assets for: "${topic}"\n`);

    for (const { fn, label, args } of jobs) {
      console.log(`── ${label}`);
      await fn(args);
    }

    console.log('All done!\n');
  });

program.parse(process.argv);
