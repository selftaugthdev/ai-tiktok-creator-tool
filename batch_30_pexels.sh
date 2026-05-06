#!/bin/bash
# Batch: 30 MigraineCast photo carousels (TikTok, Pexels backgrounds)
# Run from repo root: bash batch_30_pexels.sh

set -e
cd "$(dirname "$0")"

APP="MigraineCast"
PLATFORM="tiktok"
SLIDES=5

run() {
  local topic="$1"
  echo ""
  echo "======================================================"
  echo "TOPIC: $topic"
  echo "======================================================"
  python3 photo_main.py --app "$APP" --topic "$topic" --slides $SLIDES --platform $PLATFORM --pexels
}

# --- Symptom Awareness ---
run "early warning signs of a migraine attack"
run "migraine aura explained"
run "types of migraines most people don't know"
run "migraine vs headache what is the difference"
run "what is a silent migraine"
run "the four stages of a migraine attack"
run "what migraine postdrome feels like the migraine hangover"
run "lesser known migraine symptoms beyond head pain"
run "why sound sensitivity spikes during a migraine"
run "why cognitive fog hits during a migraine"

# --- Emotional / Educational ---
run "Everyone else feels fine. You feel the storm before it arrives"
run "You have been tracking your migraines wrong and it is not your fault"
run "The thing about migraines no one tells you: they follow a pattern"
run "The invisible illness that responds to weather forecasts"
run "Nobody sees it coming. Except the barometer and now you"
run "You are not broken. You are barometrically sensitive"
run "What if your next migraine was predictable 24 hours in advance"
run "You feel it before the rain. That is not anxiety that is a real physiological response"
run "The day I stopped dreading migraines and started forecasting them"
run "Every migraine I have had this year had one thing in common"

# --- Emotional / Community ---
run "things migraine sufferers wish people understood"
run "the emotional toll of cancelling plans due to migraines"
run "migraine guilt why sufferers feel bad for being in pain"
run "what migraine loneliness feels like"
run "the grief of losing days to migraine attacks"

# --- Tips & Relief ---
run "how to build a migraine emergency kit"
run "pressure point techniques for migraine relief"
run "the best magnesium supplements for migraine prevention"
run "rescue medication tips for migraine attacks"
run "how to reduce stress-related migraine triggers"

echo ""
echo "======================================================"
echo "All 30 carousels done!"
echo "======================================================"
