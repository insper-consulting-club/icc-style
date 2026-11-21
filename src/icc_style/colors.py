"""ICC brand colors and the analytical palettes built on them.

Only the four ``BRAND`` colors are official ICC identity colors. Everything else
in this module is a *visualization extension*: colors chosen so that charts can
show several categories, magnitudes or deviations while staying consistent
with the brand.
"""

from __future__ import annotations

import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap

# Official ICC brand colors ---------------------------------------------------

PRIMARY_RED = "#B20000"
DARK_RED = "#7B001E"
BLACK = "#1A1A1A"
WHITE = "#FFFFFF"

BRAND_COLORS = {
    "primary_red": PRIMARY_RED,
    "dark_red": DARK_RED,
    "black": BLACK,
    "white": WHITE,
}

# Analytical extensions: categorical hues ---------------------------------------
# Chosen to sit in the same lightness band as PRIMARY_RED (OKLCH L 0.48-0.60),
# with at least 3:1 contrast on white, and in an order whose neighbors remain
# distinguishable under protanopia and deuteranopia.

BLUE = "#1F66B5"
GOLD = "#A8770A"
TEAL = "#0E8A7A"
VIOLET = "#8350B8"

#: Default color cycle. Assign in this order; the first four are also mutually
#: distinguishable, which matters for scatterplots where any two can touch.
CATEGORICAL = (PRIMARY_RED, BLUE, GOLD, TEAL, VIOLET)

# Analytical extensions: neutrals -------------------------------------------------
# Grays for secondary text, context series, de-emphasized bars and fills.

DARK_GRAY = "#4D4D4D"
GRAY = "#8C8C8C"
LIGHT_GRAY = "#C8C8C8"
PALE_GRAY = "#E6E6E6"

NEUTRALS = (DARK_GRAY, GRAY, LIGHT_GRAY, PALE_GRAY)

# Analytical extensions: colormaps -------------------------------------------------
# Anchors were interpolated in OKLab and resampled at equal lightness steps, so
# perceived lightness changes evenly along each map.

_SEQUENTIAL_ANCHORS = (
    "#FBEFEE",
    "#F4D0CC",
    "#ECB1AA",
    "#E29288",
    "#D67367",
    "#C95245",
    "#BA2A20",
    "#A00010",
    DARK_RED,
)
_DIVERGING_ANCHORS = (
    "#123F75",
    "#2468B6",
    "#6C96CD",
    "#AEC4E2",
    "#F2F2F2",
    "#EBB2AB",
    "#D67367",
    "#BA2A20",
    DARK_RED,
)

#: Light-to-dark red ramp for magnitudes (heatmaps, choropleths).
SEQUENTIAL_CMAP = LinearSegmentedColormap.from_list("icc_reds", _SEQUENTIAL_ANCHORS)
#: Blue-gray-red map for deviations around a meaningful midpoint.
DIVERGING_CMAP = LinearSegmentedColormap.from_list("icc_diverging", _DIVERGING_ANCHORS)


def _register_colormaps() -> None:
    """Make the colormaps available by name (``cmap="icc_reds"``)."""
    for cmap in (SEQUENTIAL_CMAP, DIVERGING_CMAP):
        for variant in (cmap, cmap.reversed()):
            if variant.name not in mpl.colormaps:
                mpl.colormaps.register(variant)


_register_colormaps()
