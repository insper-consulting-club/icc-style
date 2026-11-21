import re
import subprocess
import sys
import warnings

import matplotlib.pyplot as plt
import pytest
from matplotlib.image import imread

import icc_style as icc


@pytest.fixture
def chart():
    icc.set_theme()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([2022, 2023, 2024], [10, 12, 15])
    ax.set_ylabel("Revenue")
    return fig, ax


def finalize_texts(fig):
    return [t for t in fig.texts if t.get_gid() == "icc-style-finalize"]


def test_finalize_figure_places_texts_around_the_axes(chart):
    fig, ax = chart
    icc.finalize_figure(fig, title="Title", subtitle="Subtitle", source="Source")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    title, subtitle, source = (
        t.get_window_extent(renderer) for t in finalize_texts(fig)
    )
    axes_box = ax.get_tightbbox(renderer)

    assert title.y0 > subtitle.y1  # subtitle below title
    assert subtitle.y0 > axes_box.y1  # axes (incl. tick labels) below the header
    assert source.y1 < axes_box.y0  # source note below the axes
    assert source.y0 >= 0
    assert title.y1 <= fig.bbox.height
    # Title, subtitle and source share the left edge, aligned with tick labels.
    assert title.x0 == pytest.approx(subtitle.x0) == pytest.approx(source.x0)
    assert abs(title.x0 - axes_box.x0) < 0.05 * fig.bbox.width


def test_finalize_figure_styles_the_title_hierarchy(chart):
    fig, _ = chart
    icc.finalize_figure(fig, title="Title", subtitle="Subtitle", source="Source")
    title, subtitle, source = finalize_texts(fig)
    assert title.get_fontweight() == "bold"
    assert subtitle.get_fontweight() == "normal"
    assert title.get_fontsize() > subtitle.get_fontsize() > source.get_fontsize()


def test_finalize_figure_is_repeatable(chart):
    fig, _ = chart
    icc.finalize_figure(fig, title="First", source="Source")
    icc.finalize_figure(fig, title="Second")
    assert [t.get_text() for t in finalize_texts(fig)] == ["Second"]


def test_finalize_figure_keeps_currency_literal(chart):
    fig, _ = chart
    icc.finalize_figure(fig, title="From R$ 10M to R$ 12M")
    (title,) = finalize_texts(fig)
    fig.canvas.draw()
    assert not title.get_parse_math()


def test_finalize_figure_warns_about_overlong_text(chart):
    fig, _ = chart
    with pytest.warns(UserWarning, match="wider than the figure"):
        icc.finalize_figure(fig, title="A very long title " * 6)


def test_finalize_figure_without_texts_leaves_layout_untouched(chart):
    fig, _ = chart
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        icc.finalize_figure(fig)
    assert fig.get_layout_engine().get()["rect"] == (0, 0, 1, 1)


def test_finalize_figure_enables_constrained_layout_when_absent():
    fig, _ = plt.subplots(layout="none")
    icc.finalize_figure(fig, title="Title")
    assert fig.get_layout_engine().__class__.__name__ == "ConstrainedLayoutEngine"


def test_finalize_figure_rejects_other_layout_engines():
    fig, _ = plt.subplots(layout="tight")
    with pytest.raises(ValueError, match="constrained layout"):
        icc.finalize_figure(fig, title="Title")


def test_save_figure_writes_png_svg_and_pdf(chart, tmp_path):
    fig, _ = chart
    paths = icc.save_figure(
        fig, tmp_path / "out" / "chart", formats=("png", "svg", "pdf")
    )
    assert [p.name for p in paths] == ["chart.png", "chart.svg", "chart.pdf"]
    assert paths[0].read_bytes().startswith(b"\x89PNG")
    assert b"<svg" in paths[1].read_bytes()
    assert paths[2].read_bytes().startswith(b"%PDF")


def test_save_figure_uses_the_extension_by_default(chart, tmp_path):
    fig, _ = chart
    (path,) = icc.save_figure(fig, tmp_path / "chart.pdf")
    assert path == tmp_path / "chart.pdf"


def test_save_figure_replaces_a_known_extension_when_formats_are_given(chart, tmp_path):
    fig, _ = chart
    paths = icc.save_figure(fig, tmp_path / "chart.png", formats=["svg"])
    assert paths == [tmp_path / "chart.svg"]


def test_png_size_follows_dpi(chart, tmp_path):
    fig, _ = chart
    (path,) = icc.save_figure(fig, tmp_path / "chart.png", dpi=50)
    height, width, _ = imread(path).shape
    assert (width, height) == (300, 200)


def test_png_uses_theme_dpi_by_default(chart, tmp_path):
    fig, _ = chart
    (path,) = icc.save_figure(fig, tmp_path / "chart.png")
    assert imread(path).shape[:2] == (1200, 1800)


def test_transparent_png_has_no_background(chart, tmp_path):
    fig, _ = chart
    (opaque,) = icc.save_figure(fig, tmp_path / "opaque.png", dpi=20)
    (clear,) = icc.save_figure(fig, tmp_path / "clear.png", dpi=20, transparent=True)
    assert imread(opaque)[0, 0, 3] == 1.0
    assert imread(clear)[0, 0, 3] == 0.0


def test_svg_text_as_paths_or_as_editable_text(chart, tmp_path):
    fig, ax = chart
    ax.set_title("Editable")
    (outlined,) = icc.save_figure(fig, tmp_path / "paths.svg")
    (editable,) = icc.save_figure(fig, tmp_path / "text.svg", svg_text="text")
    assert "<text" not in outlined.read_text()
    content = editable.read_text()
    assert "Editable" in content
    assert re.search(r"font[^>]*Poppins", content)


def test_pdf_embeds_truetype_fonts(chart, tmp_path):
    fig, ax = chart
    ax.set_title("Title")
    (path,) = icc.save_figure(fig, tmp_path / "chart.pdf")
    data = path.read_bytes()
    assert b"/FontFile2" in data  # TrueType (type 42), not Type 3
    assert b"+Poppins-Bold" in data


REPRODUCIBILITY_SCRIPT = """
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import icc_style as icc
icc.set_theme()
fig, ax = plt.subplots()
ax.plot([2022, 2023, 2024], [10, 12, 15])
icc.finalize_figure(fig, title="Title", source="Source")
icc.save_figure(fig, sys.argv[1], formats=("pdf", "svg"))
"""


def test_rerunning_a_script_reproduces_vector_files(tmp_path):
    for run in ("first", "second"):
        subprocess.run(
            [sys.executable, "-c", REPRODUCIBILITY_SCRIPT, str(tmp_path / run)],
            check=True,
            timeout=300,
        )
    for fmt in ("pdf", "svg"):
        first = (tmp_path / f"first.{fmt}").read_bytes()
        assert first == (tmp_path / f"second.{fmt}").read_bytes(), fmt


def test_save_figure_rejects_bad_arguments(chart, tmp_path):
    fig, _ = chart
    with pytest.raises(ValueError, match="extension"):
        icc.save_figure(fig, tmp_path / "chart")
    with pytest.raises(ValueError, match="unsupported format"):
        icc.save_figure(fig, tmp_path / "chart", formats=["docx"])
    with pytest.raises(ValueError, match="svg_text"):
        icc.save_figure(fig, tmp_path / "chart.svg", svg_text="outline")
