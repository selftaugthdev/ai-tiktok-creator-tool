#!/usr/bin/env bash
# Batch generate 90 MigraineCast infographic carousels for Pinterest
# 30 topics × 3 carousels each = 90 total (3/day for 30 days)
# Usage: bash batch_generate.sh
# Resumes from where it left off if interrupted (tracks progress in .batch_progress)

set -euo pipefail

PLATFORM="tiktok"
OUTPUT="output/grids/tiktok"
PROGRESS_FILE=".batch_progress"

TOPICS=(
  # WEEK 1: Emotional / relatable identity (Days 1-7)
  "what a migraine actually feels like (not just a headache)"
  "the invisible symptoms nobody talks about before a migraine hits"
  "why migraine sufferers cancel plans and feel guilty about it"
  "things only people with chronic migraines truly understand"
  "the emotional toll of living with unpredictable migraines"
  "why migraines make you feel like you are losing your mind"
  "the grief of missing out on life because of chronic migraines"

  # WEEK 2: Surprising science & brain mechanisms (Days 8-14)
  "the science of why barometric pressure drops trigger migraines"
  "how the trigeminovascular system causes migraine pain"
  "why your brain becomes hypersensitive during a migraine"
  "what actually happens in your brain during a migraine aura"
  "the gut-brain connection and why your diet affects migraines"
  "why some people get migraines and others never do"
  "what serotonin has to do with your migraine attacks"

  # WEEK 3: Myth-busting & counter-intuitive truths (Days 15-21)
  "migraine myths that doctors wish you would stop believing"
  "why painkillers can make your migraines worse over time"
  "the caffeine and migraine paradox most people get wrong"
  "why exercise can both trigger and prevent migraines"
  "why being told to just relax does nothing for your migraine"
  "the truth about whether chocolate actually causes migraines"
  "why bright lights hurt so much more during a migraine"

  # WEEK 4: Trigger deep-dives (Days 22-28)
  "hormonal migraine triggers across the monthly cycle"
  "screen time and blue light as underestimated migraine triggers"
  "neck tension and posture as daily migraine triggers"
  "why dehydration is the sneakiest migraine trigger"
  "smell and sensory overload triggers for migraines"
  "how skipping meals triggers migraines"
  "why changes in your daily routine spark migraine attacks"

  # WEEK 5: The 4 migraine phases explained (Days 29-35)
  "the prodrome phase: warning signs 24 hours before a migraine"
  "the migraine aura phase: visual and sensory disturbances explained"
  "the attack phase: what is happening in your body during peak migraine pain"
  "the postdrome phase: why you feel wiped out after a migraine"
  "how to use the 4 migraine phases to take action earlier"
  "why tracking each migraine phase changes how you manage them"
  "the migraine hangover that nobody warns you about"

  # WEEK 6: Practical prevention hacks (Days 36-42)
  "the best sleep habits to prevent migraine attacks"
  "how to build a migraine survival kit for bad days"
  "how tracking weather patterns can predict your next migraine"
  "daily habits that dramatically reduce migraine frequency"
  "how to create a migraine-proof morning routine"
  "the hydration plan that helps prevent migraines"
  "magnesium and migraines: what the research actually says"

  # WEEK 7: Food, drink & diet angles (Days 43-49)
  "hidden food triggers most migraine sufferers do not know about"
  "foods and drinks that actually help prevent migraines"
  "how the elimination diet works for migraine sufferers"
  "why alcohol triggers migraines and which types are worst"
  "the role of tyramine in food-triggered migraines"
  "why artificial sweeteners may be causing your migraines"
  "the anti-inflammatory diet approach to fewer migraines"

  # WEEK 8: Lifestyle & managing migraines in the real world (Days 50-56)
  "how to talk to coworkers and bosses about your migraines"
  "traveling with chronic migraines: what actually helps"
  "how to manage migraines as a parent"
  "how to reduce migraine guilt and reclaim your confidence"
  "why stress management is a medical necessity for migraine sufferers"
  "how to set boundaries when migraines control your schedule"
  "what to do when a migraine hits in a public place"

  # WEEK 9: Tracking, patterns & data-driven relief (Days 57-63)
  "how to keep a migraine diary that gives you real insights"
  "the 5 things you should track with every migraine"
  "how to identify your personal migraine trigger pattern"
  "why migraine frequency increases if you ignore your warning signs"
  "what your migraine data reveals about your lifestyle"
  "how to use weather forecasts to prepare for migraine risk days"
  "the power of predicting migraines before they start"

  # WEEK 10: Specific demographics & situations (Days 64-70)
  "migraines during pregnancy: what is safe and what is not"
  "why teenagers get migraines and what helps them"
  "how menopause changes your migraine pattern"
  "why men get migraines too but rarely talk about it"
  "migraines and the workplace: your rights and options"
  "how altitude and flying trigger migraines"
  "why migraines spike in summer heat and humidity"

  # WEEK 11: Treatment & relief strategies (Days 71-77)
  "the difference between abortive and preventive migraine treatment"
  "natural migraine relief methods that have scientific backing"
  "how cold therapy and ice packs reduce migraine pain"
  "the role of darkness and silence in migraine recovery"
  "breathing techniques that ease migraine pain fast"
  "pressure points that relieve migraine symptoms"
  "how to build a personal migraine response plan"

  # WEEK 12: App-adjacent and community (Days 78-84)
  "why knowing your migraine risk 24 hours ahead changes everything"
  "how pattern recognition is the key to fewer migraines"
  "the one migraine habit that makes the biggest difference"
  "why migraine sufferers need to stop blaming themselves"
  "how to explain your migraines to people who have never had one"
  "signs your migraine treatment plan needs to be updated"
  "what consistent migraine tracking reveals over 90 days"

  # WEEK 13 BONUS: Shareable & scroll-stopping (Days 85-90)
  "the migraine triggers hiding in your everyday environment"
  "10 things migraine warriors wish others understood"
  "why your migraines are worse in winter"
  "the biggest mistake migraine sufferers make on a good day"
  "the surprising link between migraines and your posture"
  "why you should never ignore your migraine prodrome symptoms"
)

# Read progress (index of last completed topic, 0-based)
START=0
if [[ -f "$PROGRESS_FILE" ]]; then
  START=$(cat "$PROGRESS_FILE")
  echo "Resuming from topic $((START + 1))/${#TOPICS[@]}..."
fi

TOTAL=${#TOPICS[@]}

for i in "${!TOPICS[@]}"; do
  if [[ $i -lt $START ]]; then
    continue
  fi

  TOPIC="${TOPICS[$i]}"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Topic $((i + 1))/${TOTAL}: ${TOPIC}"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  node bin/migrainecast-content.js grid \
    --topic "$TOPIC" \
    --output "$OUTPUT" \
    --platform $PLATFORM

  # Save progress after each completed topic
  echo $((i + 1)) > "$PROGRESS_FILE"
  echo "Progress saved: $((i + 1))/${TOTAL} topics done."
done

echo ""
echo "✓ All 90 grids generated!"
echo "  Output: output/grids/tiktok/to_upload/"
rm -f "$PROGRESS_FILE"
