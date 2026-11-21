import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest
from matplotlib.colors import to_hex

import icc_style as icc
from icc_style.theme import _read_style


def cycle_colors():
    return [
        to_hex(c).upper() for c in mpl.rcParams["axes.prop_cycle"].by_key()["color"]
    ]


def test_package_exposes_version_and_public_api():
    assert icc.__version__
    for name in icc.__all__:
        assert hasattr(icc, name), name


def test_set_theme_applies_identity():
    icc.set_theme()
    rc = mpl.rcParams
    assert rc["font.family"][0] == "Poppins"
    assert rc["axes.titleweight"] == "bold"
    assert rc["figure.titleweight"] == "bold"
    assert rc["font.weight"] == "normal"
    assert to_hex(rc["text.color"]).upper() == icc.BLACK
    assert to_hex(rc["axes.facecolor"]).upper() == icc.WHITE
    assert to_hex(rc["figure.facecolor"]).upper() == icc.WHITE
    assert cycle_colors() == list(icc.CATEGORICAL)
    assert not rc["axes.spines.top"]
    assert not rc["axes.spines.right"]
    assert rc["axes.grid"]
    assert rc["axes.grid.axis"] == "y"
    assert rc["image.cmap"] == "icc_reds"
    assert rc["pdf.fonttype"] == 42


@pytest.mark.parametrize("context", icc.CONTEXTS)
def test_every_context_applies(context):
    icc.set_theme(context)
    assert mpl.rcParams["font.family"][0] == "Poppins"
    assert cycle_colors()[0] == icc.PRIMARY_RED


def test_contexts_differ_in_scale():
    sizes = {}
    for context in icc.CONTEXTS:
        params = icc.rc_params(context)
        sizes[context] = (params["font.size"], params["lines.linewidth"])
    assert sizes["publication"] < sizes["default"] < sizes["presentation"]
    assert icc.rc_params("presentation")["figure.figsize"] == [10.0, 5.625]


def test_switching_contexts_fully_resets_scale():
    # Every parameter a context changes must also be set by the base sheet,
    # otherwise switching back to "default" would leave stale values behind.
    sheet_keys = _read_style("icc").keys()
    for context in ("presentation", "publication"):
        assert _read_style(context).keys() <= sheet_keys
    base = icc.rc_params("default")
    icc.set_theme("presentation")
    icc.set_theme("default")
    for key, value in base.items():
        assert mpl.rcParams[key] == value, key


def test_unknown_context_is_rejected():
    with pytest.raises(ValueError, match="unknown context"):
        icc.set_theme("poster")


def test_set_theme_is_idempotent():
    icc.set_theme()
    first = dict(mpl.rcParams)
    fonts_before = len(mpl.font_manager.fontManager.ttflist)
    icc.set_theme()
    assert dict(mpl.rcParams) == first
    assert len(mpl.font_manager.fontManager.ttflist) == fonts_before


def test_rc_overrides_are_applied_last():
    icc.set_theme(rc={"figure.figsize": (6, 6), "axes.grid": False})
    assert list(mpl.rcParams["figure.figsize"]) == [6, 6]
    assert not mpl.rcParams["axes.grid"]


def test_theme_context_restores_previous_settings():
    before = dict(mpl.rcParams)
    with icc.theme_context("presentation"):
        assert mpl.rcParams["font.size"] == 14
        _fig, ax = plt.subplots()
        assert ax.xaxis.label.get_fontsize() == 14
    assert dict(mpl.rcParams) == before


def test_rc_params_returns_a_fresh_copy():
    params = icc.rc_params()
    params["font.size"] = 99
    assert icc.rc_params()["font.size"] == 10


def test_style_sheet_is_usable_by_dotted_name():
    plt.style.use("icc_style.styles.icc")
    assert mpl.rcParams["font.family"][0] == "Poppins"
    assert cycle_colors() == list(icc.CATEGORICAL)
    plt.style.use("icc_style.styles.publication")
    assert mpl.rcParams["font.size"] == 9


def test_style_sheet_matches_theme_except_python_only_settings():
    plt.style.use("icc_style.styles.icc")
    from_sheet = dict(mpl.rcParams)
    mpl.style.use("default")
    icc.set_theme()
    from_theme = dict(mpl.rcParams)
    differences = {k for k in from_theme if from_theme[k] != from_sheet[k]}
    assert differences == {"image.cmap"}


def test_theme_renders_common_charts():
    icc.set_theme()
    fig, axes = plt.subplots(2, 2)
    axes[0, 0].plot([2022, 2023, 2024], [1, 2, 3])
    axes[0, 1].bar(["a", "b"], [3, -1])
    axes[1, 0].scatter([1, 2, 3], [3, 1, 2])
    axes[1, 1].imshow([[0, 1], [2, 3]])
    fig.canvas.draw()
    assert to_hex(axes[0, 0].lines[0].get_color()).upper() == icc.PRIMARY_RED
    assert axes[1, 1].images[0].get_cmap().name == "icc_reds"
