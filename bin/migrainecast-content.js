#!/usr/bin/env node
'use strict';

require('dotenv').config();

const { Command } = require('commander');
const { runSlide } = require('../src/commands/slide');

const program = new Command();

program
  .name('migrainecast-content')
  .description('Generate MigraineCast TikTok content assets.')
  .version('1.0.0');

program
  .command('slide')
  .description('Generate a single TikTok photo post slide (1080x1920 PNG) with emotional statements.')
  .requiredOption('--topic <topic>', 'Headline shown at the top of the slide.')
  .requiredOption('--output <dir>', 'Output directory — slide.png will be saved here.')
  .action(async (opts) => {
    if (!process.env.ANTHROPIC_API_KEY) {
      console.error('Error: ANTHROPIC_API_KEY is not set. Add it to your .env file.');
      process.exit(1);
    }
    await runSlide(opts);
  });

program.parse(process.argv);
