import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest
from matplotlib.colors import to_hex

import icc_style as icc

sns = pytest.importorskip("seaborn")


def test_seaborn_uses_the_icc_color_cycle():
    icc.set_theme()
    palette = [to_hex(c).upper() for c in sns.color_palette()]
    assert palette == list(icc.CATEGORICAL)


def test_seaborn_plots_render_with_the_theme():
    icc.set_theme()
    data = {"x": [1, 2, 3, 1, 2, 3], "y": [1, 3, 2, 2, 1, 3], "g": list("aaabbb")}
    fig, ax = plt.subplots()
    sns.lineplot(data=data, x="x", y="y", hue="g", ax=ax)
    fig.canvas.draw()
    colors = [to_hex(line.get_color()).upper() for line in ax.get_lines()[:2]]
    assert colors == [icc.PRIMARY_RED, icc.BLUE]
    assert ax.xaxis.label.get_fontfamily()[0] == "Poppins"


def test_seaborn_heatmap_accepts_icc_colormaps():
    icc.set_theme()
    _fig, ax = plt.subplots()
    sns.heatmap([[-1, 0], [0.5, 1]], cmap="icc_diverging", center=0, ax=ax)
    cmap = ax.collections[0].get_cmap()  # seaborn uses a copy of the colormap
    for x in (0.0, 0.5, 1.0):
        assert to_hex(cmap(x)) == to_hex(icc.DIVERGING_CMAP(x))


def test_seaborn_set_theme_overrides_and_icc_restores():
    icc.set_theme()
    sns.set_theme()
    assert mpl.rcParams["font.family"] == ["sans-serif"]
    icc.set_theme()
    assert mpl.rcParams["font.family"][0] == "Poppins"
    assert to_hex(mpl.rcParams["axes.facecolor"]).upper() == icc.WHITE


def test_seaborn_objects_accept_rc_params():
    so = pytest.importorskip("seaborn.objects")
    icc.register_fonts()
    fig = plt.figure()
    plot = so.Plot(x=[1, 2, 3], y=[3, 1, 2]).add(so.Line()).theme(icc.rc_params())
    plot.on(fig).plot()
    ax = fig.axes[0]
    assert to_hex(ax.get_facecolor()).upper() == icc.WHITE
    assert to_hex(ax.get_lines()[0].get_color()).upper() == icc.PRIMARY_RED
