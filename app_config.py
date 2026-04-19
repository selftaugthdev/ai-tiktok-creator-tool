"""Per-app configuration for all generators and renderers.

Add a new entry to CONFIGS to support a new app.
Keys are lowercase app name slugs for case-insensitive matching.
"""

from pathlib import Path


CONFIGS = {
    "migrainecast": {
        "logo_path": Path("assets") / "migraine_logo white.png",
        "watermark_text": "www.migrainecast.app",
        "cta_download_line": "Download MigraineCast on iOS. Link in bio. Or download at www.migrainecast.app",
        "caption_cta": "Stay ahead of your migraines with the MigraineCast app, link in Bio, free to download in the App store or at www.migrainecast.app",
        "audience": "migraine sufferer",
        "mechanism_examples": "barometric pressure drops, the trigeminovascular system, the prodrome phase, pattern recognition across time",
        "tiktok_hashtags": "#migraine #migrainerelief #migraineawareness #migrainewarrior #chronicmigraine",
        "instagram_hashtags": "#migraine #migrainelife #migrainerelief #migrainetriggers #migraineawareness #MigraineCast #chronicmigraine #migrainewarrior #headacherelief #migrainetips #weathermigraine #migrainesupport",
        "reviews": [
            {
                "quote": "\u201cAll of my migraines were in line with high or medium risk days on the app.\u201d",
                "author": "\u2014 Selen_B_D, App Store",
            },
            {
                "quote": "\u201cI was sceptical at first, but the weather does have impact on my migraine, a lot more than I had ever thought possible. This app has become my daily go-to.\u201d",
                "author": "\u2014 Winter-flowers-in-summer, App Store",
            },
        ],
        "app_screenshot_path": Path("assets") / "Home Premium.png",
        "homepage_slide_path": Path("assets") / "MigraineCast Showing Home Page.jpg",
    },
    "calm sos": {
        "logo_path": Path("assets") / "calm_sos_logo.png",
        "watermark_text": "Calm SOS",
        "cta_download_line": "Download Calm SOS free on the App Store. Link in bio.",
        "caption_cta": "You don't have to white-knuckle it alone. Calm SOS is free to download on the App Store. Link in bio.",
        "audience": "panic attack sufferer",
        "mechanism_examples": "the fight-or-flight response, adrenaline spikes, the amygdala hijack, hyperventilation cycles, nervous system dysregulation",
        "tiktok_hashtags": "#panicattack #anxietyattack #anxietyrelief #socialanxiety #mentalhealth",
        "instagram_hashtags": "#panicattack #anxietyattack #anxietyrelief #socialanxiety #mentalhealth #anxietytips #stress #anxietywarrior #panicattackhelp #calmdown #anxietysupport #mentalhealthmatters",
        "reviews": [],
        "app_screenshot_path": None,
        "homepage_slide_path": None,
    },
}


def get_app_config(app_name: str) -> dict:
    """Return config for the given app name (case-insensitive, fuzzy match).
    Falls back to MigraineCast if no match found.
    """
    key = app_name.lower().strip()
    if key in CONFIGS:
        return CONFIGS[key]
    for cfg_key, cfg in CONFIGS.items():
        if cfg_key in key or key in cfg_key:
            return cfg
    return CONFIGS["migrainecast"]
