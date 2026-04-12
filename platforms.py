"""Platform dimension and safe-zone configuration."""

from dataclasses import dataclass


@dataclass
class PlatformConfig:
    name: str
    width: int
    height: int
    safe_zone_top: int     # UI chrome at top (status bar + nav tabs)
    safe_zone_bottom: int  # UI chrome at bottom (captions, action bar)
    safe_zone_right: int   # UI chrome at right (engagement buttons)


TIKTOK = PlatformConfig(
    name="tiktok",
    width=1080,
    height=1920,
    safe_zone_top=200,    # status bar + For You/Following tabs
    safe_zone_bottom=480, # caption/description overlay
    safe_zone_right=160,  # like/comment/share button column
)

INSTAGRAM = PlatformConfig(
    name="instagram",
    width=1080,
    height=1350,          # 4:5 portrait (standard IG carousel format)
    safe_zone_top=160,    # status bar only (no tab row on carousels)
    safe_zone_bottom=200, # carousel dots + action bar
    safe_zone_right=80,   # no engagement button column on carousels
)

PLATFORMS = {"tiktok": TIKTOK, "instagram": INSTAGRAM}
