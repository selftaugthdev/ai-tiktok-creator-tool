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
        "cta_tagline": "See your next migraine before it sees you",
        "cta_follow_line": "Follow for daily migraine tips",
        "cta_download_line": "Download MigraineCast on iOS. Link in bio. www.migrainecast.app",
        "language_note": "Also Available In Dutch, German, French & Spanish",
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
        "homepage_slide_path": Path("assets") / "MigraineCast Showing Homepage.jpg",
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
        "cta_tagline": "Calm your panic attack in seconds",
        "cta_follow_line": "Follow for daily anxiety tips",
        "cta_download_line": "Download Calm SOS free on the App Store. Link in bio.",
        "caption_cta": "You don't have to white-knuckle it alone. Calm SOS is free to download on the App Store. Link in bio.",
        # Content
        "audience": "panic attack sufferer",
        "mechanism_examples": "the fight-or-flight response, adrenaline spikes, the amygdala hijack, hyperventilation cycles, nervous system dysregulation",
        # Hashtags
        "tiktok_hashtags": "#panicattack #anxietyattack #anxietyrelief #socialanxiety #mentalhealth",
        "instagram_hashtags": "#panicattack #anxietyattack #anxietyrelief #socialanxiety #mentalhealth #anxietytips #stress #anxietywarrior #panicattackhelp #calmdown #anxietysupport #mentalhealthmatters",
        # Reviews
        "reviews": [
            {
                "quote": "\u201cThis app got me through my worst panic attack. I don\u2019t go anywhere without it.\u201d",
                "author": "\u2014 App Store Review",
            },
            {
                "quote": "\u201cFinally something that actually works when anxiety hits. The breathing exercises alone are worth it.\u201d",
                "author": "\u2014 App Store Review",
            },
        ],
        # Screenshots
        "app_screenshot_path": Path("assets") / "Calm SOS HOME PAGE.jpg",
        "homepage_slide_path": Path("assets") / "Calm SOS HOME PAGE.jpg",
        "screenshot_options": [
            Path("assets") / "Calm SOS HOME PAGE.jpg",
            Path("assets") / "Calm SOS TOOLS.jpg",
            Path("assets") / "Calm SOS Breathing Programs.jpg",
            Path("assets") / "Calm SOS Personal Coach.jpg",
        ],
        # Colors (RGB tuples)  — Lavender Lounge palette
        "bg_color":                (206, 159, 252),   # #CE9FFC soft lavender
        "accent_color":            (75,  82,  126),   # #4B527E dusty indigo
        "text_headline_color":     (75,  82,  126),   # #4B527E dusty indigo
        "text_body_color":         (255, 248, 220),   # #FFF8DC cream
        "watermark_color":         (75,  82,  126),   # #4B527E dusty indigo
        "testimonial_bg_color":    (185, 135, 245),   # #B987F5 deeper lavender
        "infographic_circle_color":(230, 210, 255),   # #E6D2FF light lavender
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
