"""ICC Style: the Insper Consulting Club visual identity for Matplotlib and Seaborn.

>>> import icc_style as icc
>>> icc.set_theme()
"""

import contextlib

from icc_style.colors import (
    BLACK,
    BLUE,
    BRAND_COLORS,
    CATEGORICAL,
    DARK_GRAY,
    DARK_RED,
    DIVERGING_CMAP,
    GOLD,
    GRAY,
    LIGHT_GRAY,
    NEUTRALS,
    PALE_GRAY,
    PRIMARY_RED,
    SEQUENTIAL_CMAP,
    TEAL,
    VIOLET,
    WHITE,
)
from icc_style.figure import finalize_figure, save_figure
from icc_style.fonts import FontRegistrationError, check_fonts, register_fonts
from icc_style.formatting import (
    bps_formatter,
    brl_formatter,
    number_formatter,
    percent_formatter,
)
from icc_style.theme import CONTEXTS, rc_params, set_theme, theme_context

__version__ = "0.1.0"

__all__ = [
    "BLACK",
    "BLUE",
    "BRAND_COLORS",
    "CATEGORICAL",
    "CONTEXTS",
    "DARK_GRAY",
    "DARK_RED",
    "DIVERGING_CMAP",
    "GOLD",
    "GRAY",
    "LIGHT_GRAY",
    "NEUTRALS",
    "PALE_GRAY",
    "PRIMARY_RED",
    "SEQUENTIAL_CMAP",
    "TEAL",
    "VIOLET",
    "WHITE",
    "FontRegistrationError",
    "bps_formatter",
    "brl_formatter",
    "check_fonts",
    "finalize_figure",
    "number_formatter",
    "percent_formatter",
    "rc_params",
    "register_fonts",
    "save_figure",
    "set_theme",
    "theme_context",
]

# Registering the bundled fonts on import lets the plain style sheet
# (plt.style.use("icc_style.styles.icc")) find Poppins too. Failures are
# reported by set_theme() and check_fonts() rather than at import time.
with contextlib.suppress(FontRegistrationError):
    register_fonts()
