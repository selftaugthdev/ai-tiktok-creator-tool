#!/bin/bash
# Batch: 30 MigraineCast slides (JSX tool, Playfair Display, 7 statements each)
# Run from repo root: bash batch_30_slides.sh

set -e
cd "$(dirname "$0")"

PLATFORM="tiktok"
OUTPUT="output/slides/tiktok"

run() {
  local topic="$1"
  echo ""
  echo "======================================================"
  echo "TOPIC: $topic"
  echo "======================================================"
  node bin/migrainecast-content.js slide --topic "$topic" --output "$OUTPUT" --platform $PLATFORM
}

# --- Education / Science ---
run "how barometric pressure triggers migraines"
run "weather patterns that cause headaches"
run "why temperature changes trigger migraines"
run "humidity and migraine connection"
run "what happens in your brain during a migraine"
run "why some people are more weather sensitive than others"
run "the role of serotonin in migraine attacks"
run "what is cortical spreading depression in migraines"
run "why migraines are more common in spring and fall"
run "how altitude and air pressure affect migraines"

# --- Symptom Awareness ---
run "what ocular migraines look like and what causes them"
run "why migraines cause nausea and vomiting"
run "how to tell if your dizziness is migraine related"
run "migraine fatigue, why you feel wiped out after an attack"
run "what a vestibular migraine feels like"

# --- Tips & Relief ---
run "how to prepare for high-risk weather days"
run "foods that trigger migraines"
run "migraine relief techniques that actually work"
run "how to track your migraine patterns"
run "morning routines for migraine sufferers"

# --- Emotional / Community ---
run "the anxiety of never knowing when the next migraine hits"
run "why migraine sufferers are often misunderstood at work"
run "how migraines affect mental health long-term"
run "what migraine acceptance looks like"
run "finding community as a chronic migraine sufferer"

# --- Emotional / Educational ---
run "Lying in a dark room again. This time I knew it was coming"
run "I used to cancel plans and apologize. Now I cancel plans and explain why"
run "You have had this migraine 3 times this month. They were not random"
run "I stopped being surprised by my migraines when I started watching the sky"
run "Your body is not betraying you. It is reacting to something real"

echo ""
echo "======================================================"
echo "All 30 slides done!"
echo "======================================================"
