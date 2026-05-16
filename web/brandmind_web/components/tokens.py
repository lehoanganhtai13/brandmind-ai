"""Design-token constants for the BrandMind Web UI v1.

Single in-code mirror of ``docs/web_design.md`` § 2 (colors), § 3
(typography), § 4 (spacing), and § 6 (shadow). Component modules
import these instead of repeating hex values inline so the design doc
stays the canonical source of truth and the tokens cannot drift
across components by accident. Update this module first when the
design doc evolves; any deviation in a component is a bug.
"""

from __future__ import annotations

BG_CANVAS = "#0e1318"
BG_SURFACE_1 = "#171c22"
BG_SURFACE_2 = "#1f262d"
BG_SURFACE_3 = "#272f37"

GLASS_BG_SUBTLE = "rgba(22, 24, 26, 0.62)"
GLASS_BG_ELEVATED = "rgba(22, 24, 26, 0.72)"
GLASS_BORDER = "rgba(255, 255, 255, 0.06)"

ACCENT_TEAL_SOLID = "#5fb3a8"
ACCENT_TEAL_MUTED = "rgba(95, 179, 168, 0.18)"

TEXT_PRIMARY = "#e8eef0"
TEXT_SECONDARY = "#bdc9c6"
TEXT_MUTED = "#9ca3af"

STATE_ERROR_FG = "#ffb4ab"
STATE_ERROR_BG = "rgba(147, 0, 10, 0.20)"
STATE_ERROR_BORDER = "#5e1c1c"

FONT_SANS = (
    '"Geist", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", '
    'Roboto, "Helvetica Neue", Arial, sans-serif'
)
FONT_MONO = (
    '"JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular, '
    "Menlo, monospace"
)

SIDEBAR_EXPANDED_PX = 240
SIDEBAR_COLLAPSED_PX = 56
HEADER_HEIGHT_PX = 56

RADIUS_SM = "4px"
RADIUS_MD = "8px"
RADIUS_LG = "12px"
RADIUS_PILL = "9999px"
