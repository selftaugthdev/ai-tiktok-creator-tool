"""Per-app configuration for all generators and renderers.

Add a new entry to CONFIGS to support a new app.
Keys are lowercase app name slugs for case-insensitive matching.
"""

from pathlib import Path


CONFIGS = {
    "migrainecast": {
        # Branding
        "logo_path": Path("assets") / "migraine_logo white.png",
        "watermark_text": "www.migrainecast.app",
        "has_mascot": True,
        # CTAs
        "cta_download_line": "Download MigraineCast on iOS. Link in bio. Or download at www.migrainecast.app",
        "caption_cta": "Stay ahead of your migraines with the MigraineCast app, link in Bio, free to download in the App store or at www.migrainecast.app",
        # Content
        "audience": "migraine sufferer",
        "mechanism_examples": "barometric pressure drops, the trigeminovascular system, the prodrome phase, pattern recognition across time",
        # Hashtags
        "tiktok_hashtags": "#migraine #migrainerelief #migraineawareness #migrainewarrior #chronicmigraine",
        "instagram_hashtags": "#migraine #migrainelife #migrainerelief #migrainetriggers #migraineawareness #MigraineCast #chronicmigraine #migrainewarrior #headacherelief #migrainetips #weathermigraine #migrainesupport",
        # Reviews
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
        # Screenshots
        "app_screenshot_path": Path("assets") / "Home Premium.png",
        "homepage_slide_path": Path("assets") / "MigraineCast Showing Home Page.jpg",
        "screenshot_options": [
            Path("assets") / "MigraineCast Showing Home Page.jpg",
            Path("assets") / "MigraineCast Showing Smart alert.jpg",
        ],
        # Colors (RGB tuples)
        "bg_color":                (250, 218, 221),   # #FADADD soft pink
        "accent_color":            (255, 107, 157),   # #FF6B9D hot pink
        "text_headline_color":     (45,  45,  45),    # #2D2D2D
        "text_body_color":         (85,  85,  85),    # #555555
        "watermark_color":         (255, 107, 157),   # #FF6B9D hot pink
        "testimonial_bg_color":    (255, 200, 215),   # deeper pink
        "infographic_circle_color":(255, 182, 210),   # lighter pink
    },
    "calm sos": {
        # Branding
        "logo_path": Path("assets") / "calm_sos_logo.png",
        "watermark_text": "Calm SOS",
        "has_mascot": False,
        # CTAs
        "cta_download_line": "Download Calm SOS free on the App Store. Link in bio.",
        "caption_cta": "You don't have to white-knuckle it alone. Calm SOS is free to download on the App Store. Link in bio.",
        # Content
        "audience": "panic attack sufferer",
        "mechanism_examples": "the fight-or-flight response, adrenaline spikes, the amygdala hijack, hyperventilation cycles, nervous system dysregulation",
        # Hashtags
        "tiktok_hashtags": "#panicattack #anxietyattack #anxietyrelief #socialanxiety #mentalhealth",
        "instagram_hashtags": "#panicattack #anxietyattack #anxietyrelief #socialanxiety #mentalhealth #anxietytips #stress #anxietywarrior #panicattackhelp #calmdown #anxietysupport #mentalhealthmatters",
        # Reviews
        "reviews": [],
        # Screenshots
        "app_screenshot_path": Path("assets") / "Calm SOS HOME PAGE.jpg",
        "homepage_slide_path": Path("assets") / "Calm SOS HOME PAGE.jpg",
        "screenshot_options": [
            Path("assets") / "Calm SOS HOME PAGE.jpg",
            Path("assets") / "Calm SOS TOOLS.jpg",
            Path("assets") / "Calm SOS Breathing Programs.jpg",
            Path("assets") / "Calm SOS Personal Coach.jpg",
        ],
        # Colors (RGB tuples)  — Deep Navy palette
        "bg_color":                (14,  45,  108),   # #0E2D6C deep navy
        "accent_color":            (255, 107, 157),   # #FF6B9D hot pink (same)
        "text_headline_color":     (240, 238, 246),   # near-white
        "text_body_color":         (201, 184, 232),   # #C9B8E8 soft lavender
        "watermark_color":         (160, 196, 255),   # #A0C4FF pastel blue
        "testimonial_bg_color":    (20,  55,  130),   # lighter navy
        "infographic_circle_color":(30,  65,  145),   # lighter navy for circles
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
