"""Logo and icon for the GitHub Profile Analyzer.

The logo is an original drawing (a code symbol inside fingerprint-like rings).
It is stored here as fixed SVG text so it can be placed inside the page header
and the sidebar without any extra file.
"""

from pathlib import Path

LOGO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" '
    'width="__SIZE__" height="__SIZE__" style="flex-shrink:0">'
    '<defs><linearGradient id="cpg" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#2F81F7"/><stop offset="1" stop-color="#A371F7"/>'
    "</linearGradient></defs>"
    '<rect width="64" height="64" rx="16" fill="url(#cpg)"/>'
    '<g fill="none" stroke="#FFFFFF" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="32" cy="32" r="27" stroke-width="2.2" stroke-opacity="0.35" '
    'stroke-dasharray="46 14 30 12 22 20" transform="rotate(-70 32 32)"/>'
    '<circle cx="32" cy="32" r="21" stroke-width="2.4" stroke-opacity="0.6" '
    'stroke-dasharray="38 10 26 9 20 16" transform="rotate(25 32 32)"/>'
    '<polyline points="25,25 18,32 25,39" stroke-width="3.6"/>'
    '<polyline points="39,25 46,32 39,39" stroke-width="3.6"/>'
    '<line x1="34.5" y1="24" x2="29.5" y2="40" stroke-width="3.6"/>'
    "</g></svg>"
)

ICON_PATH = Path(__file__).parent / "assets" / "logo.png"
FALLBACK_ICON = "\U0001F50E"   # magnifying glass emoji, used if the PNG is missing


def logo_html(size=56):
    """Return the logo as an inline SVG string of the given size in pixels."""
    return LOGO_SVG.replace("__SIZE__", str(int(size)))


def page_icon():
    """Return the browser tab icon: the logo PNG if it exists, else an emoji."""
    if ICON_PATH.exists():
        return str(ICON_PATH)
    return FALLBACK_ICON