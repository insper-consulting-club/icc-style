import itertools
import re

import matplotlib as mpl
import pytest
from matplotlib.colors import to_rgb

import icc_style as icc

HEX = re.compile(r"^#[0-9A-F]{6}$")


def relative_luminance(color):
    def channel(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in to_rgb(color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((relative_luminance(a), relative_luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def oklab_lightness(color):
    def linear(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (linear(c) for c in to_rgb(color))
    lms = (
        0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b,
        0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b,
        0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b,
    )
    l_, m_, s_ = (v ** (1 / 3) for v in lms)
    return 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_


def test_official_brand_colors_are_exact():
    assert icc.PRIMARY_RED == "#B20000"
    assert icc.DARK_RED == "#7B001E"
    assert icc.BLACK == "#1A1A1A"
    assert icc.WHITE == "#FFFFFF"
    assert icc.BRAND_COLORS == {
        "primary_red": "#B20000",
        "dark_red": "#7B001E",
        "black": "#1A1A1A",
        "white": "#FFFFFF",
    }


def test_all_public_colors_are_uppercase_hex():
    colors = [*icc.BRAND_COLORS.values(), *icc.CATEGORICAL, *icc.NEUTRALS]
    assert all(HEX.match(c) for c in colors)


def test_categorical_palette_leads_with_primary_red_and_is_not_all_red():
    assert icc.CATEGORICAL[0] == icc.PRIMARY_RED
    assert len(set(icc.CATEGORICAL)) == len(icc.CATEGORICAL)
    assert icc.DARK_RED not in icc.CATEGORICAL
    hues = [mpl.colors.rgb_to_hsv(to_rgb(c))[0] for c in icc.CATEGORICAL]
    reddish = [h for h in hues if h < 0.05 or h > 0.95]
    assert len(reddish) == 1


@pytest.mark.parametrize("color", icc.CATEGORICAL)
def test_categorical_colors_have_mark_contrast_on_white(color):
    assert contrast(color, icc.WHITE) >= 3.0


def test_text_colors_meet_wcag_aa_on_white():
    assert contrast(icc.BLACK, icc.WHITE) >= 4.5
    assert contrast(icc.DARK_GRAY, icc.WHITE) >= 4.5


@pytest.mark.parametrize(
    "name", ["icc_reds", "icc_reds_r", "icc_diverging", "icc_diverging_r"]
)
def test_colormaps_are_registered(name):
    assert name in mpl.colormaps


def test_sequential_colormap_lightness_is_monotonic():
    values = [oklab_lightness(icc.SEQUENTIAL_CMAP(i / 50)) for i in range(51)]
    assert all(a > b for a, b in itertools.pairwise(values))
    assert mpl.colors.to_hex(icc.SEQUENTIAL_CMAP(1.0)).upper() == icc.DARK_RED


def test_diverging_colormap_is_symmetric_around_a_neutral_midpoint():
    mid = to_rgb(icc.DIVERGING_CMAP(0.5))
    assert max(mid) - min(mid) < 0.03  # gray, not a hue
    for i in range(26):
        low = oklab_lightness(icc.DIVERGING_CMAP(i / 50))
        high = oklab_lightness(icc.DIVERGING_CMAP(1 - i / 50))
        assert abs(low - high) < 0.02
