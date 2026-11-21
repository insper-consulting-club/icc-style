import hashlib
import io
import json
import os
import subprocess
import sys
import textwrap
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import pytest
from matplotlib import font_manager
from matplotlib.text import Text

import icc_style as icc
from icc_style import fonts

PACKAGE_DIR = Path(icc.__file__).parent

# SHA-256 of the files in google/fonts ofl/poppins; the fonts must stay unmodified.
UPSTREAM_SHA256 = {
    "Poppins-Regular.ttf": "7e65201e9b79159e2300267cc885e16c8dcef2424cdfa09a29bfb0980a94a7ba",  # noqa: E501
    "Poppins-Bold.ttf": "983676516167748b74de6f4771fb384c664fd913acb8b471122ecacf5da5ea6c",  # noqa: E501
}


def font_entry(path):
    target = Path(path).resolve()
    entries = font_manager.fontManager.ttflist
    return next(e for e in entries if Path(e.fname).resolve() == target)


def text_by_content(fig, content):
    return next(t for t in fig.findobj(Text) if t.get_text() == content)


def resolved_file(text):
    return Path(font_manager.findfont(text.get_fontproperties()))


def test_bundled_fonts_are_unmodified_upstream_files():
    for name, digest in UPSTREAM_SHA256.items():
        data = (PACKAGE_DIR / "fonts" / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest


def test_register_fonts_registers_both_weights():
    paths = icc.register_fonts()
    assert [p.name for p in paths] == ["Poppins-Regular.ttf", "Poppins-Bold.ttf"]
    assert all(p.is_file() for p in paths)
    assert [(font_entry(p).name, font_entry(p).weight) for p in paths] == [
        ("Poppins", 400),
        ("Poppins", 700),
    ]


def test_register_fonts_is_idempotent():
    icc.register_fonts()
    count = len(font_manager.fontManager.ttflist)
    for _ in range(3):
        icc.register_fonts()
    assert len(font_manager.fontManager.ttflist) == count


def test_check_fonts_finds_regular_and_bold():
    icc.register_fonts()
    result = icc.check_fonts()
    assert result["regular"] is not None
    assert result["bold"] is not None
    assert font_entry(result["regular"]).weight == 400
    assert font_entry(result["bold"]).weight == 700


def test_titles_render_bold_and_labels_regular():
    icc.set_theme()
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [3, 1, 2], label="Series")
    ax.set_title("Axes title")
    ax.set_xlabel("X label")
    ax.legend()
    ax.annotate("Note", (2, 1))
    icc.finalize_figure(fig, title="Figure title", subtitle="Subtitle", source="Source")
    fig.canvas.draw()

    bold = ["Axes title", "Figure title"]
    regular = ["X label", "Series", "Note", "Subtitle", "Source"]
    regular.append(ax.get_yticklabels()[0].get_text())
    for content in bold:
        path = resolved_file(text_by_content(fig, content))
        assert (font_entry(path).name, font_entry(path).weight) == ("Poppins", 700), (
            content
        )
    for content in regular:
        path = resolved_file(text_by_content(fig, content))
        assert (font_entry(path).name, font_entry(path).weight) == ("Poppins", 400), (
            content
        )


def test_rendered_pdf_embeds_poppins_regular_and_bold():
    icc.set_theme()
    fig, ax = plt.subplots()
    ax.set_title("Bold title")
    ax.set_xlabel("Regular label")
    buffer = io.BytesIO()
    fig.savefig(buffer, format="pdf")
    pdf = buffer.getvalue()
    assert b"+Poppins-Bold" in pdf
    assert b"+Poppins-Regular" in pdf
    assert b"DejaVu" not in pdf


def test_registration_failure_raises_a_diagnostic_error(monkeypatch):
    monkeypatch.setattr(fonts, "FONT_FILES", ("Poppins-Missing.ttf",))
    with pytest.raises(icc.FontRegistrationError, match=r"Poppins-Missing\.ttf"):
        icc.register_fonts()


def test_set_theme_warns_when_registration_fails(monkeypatch):
    def fail():
        raise icc.FontRegistrationError("broken")

    monkeypatch.setattr("icc_style.theme.register_fonts", fail)
    with pytest.warns(UserWarning, match="broken"):
        icc.set_theme()


def test_set_theme_warns_when_poppins_cannot_be_resolved(monkeypatch):
    monkeypatch.setattr(
        "icc_style.theme.check_fonts", lambda: {"regular": None, "bold": None}
    )
    with pytest.warns(UserWarning, match="cannot find Poppins"):
        icc.set_theme()


def test_set_theme_is_silent_when_fonts_resolve():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        icc.set_theme()


ISOLATED_SCRIPT = textwrap.dedent(
    """
    import io, json, warnings
    from pathlib import Path
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    warnings.simplefilter("error", UserWarning)  # e.g. "cannot find Poppins"
    import icc_style as icc

    icc.set_theme()
    fig, ax = plt.subplots()
    ax.set_title("Title")
    ax.set_xlabel("Label")
    buffer = io.BytesIO()
    fig.savefig(buffer, format="pdf")
    pdf = buffer.getvalue()
    print(json.dumps({
        "package": str(Path(icc.__file__).parent),
        "fonts": {k: str(v) for k, v in icc.check_fonts().items()},
        "bold_embedded": b"+Poppins-Bold" in pdf,
        "regular_embedded": b"+Poppins-Regular" in pdf,
    }))
    """
)


def test_bundled_fonts_work_without_any_system_installation(tmp_path):
    """Simulate a fresh machine (e.g. Colab): empty home, font and Matplotlib caches."""
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("XDG_", "MPL", "FONTCONFIG"))
    }
    env.update(
        HOME=str(tmp_path),
        XDG_DATA_HOME=str(tmp_path / "share"),
        XDG_CACHE_HOME=str(tmp_path / "cache"),
        XDG_CONFIG_HOME=str(tmp_path / "config"),
        MPLCONFIGDIR=str(tmp_path / "mpl"),
    )
    completed = subprocess.run(
        [sys.executable, "-c", ISOLATED_SCRIPT],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout.strip().splitlines()[-1])
    package = Path(result["package"]).resolve()
    if package not in Path(result["fonts"]["regular"]).parents:
        pytest.skip("a system-wide Poppins installation takes precedence here")
    assert Path(result["fonts"]["regular"]) == package / "fonts" / "Poppins-Regular.ttf"
    assert Path(result["fonts"]["bold"]) == package / "fonts" / "Poppins-Bold.ttf"
    assert result["bold_embedded"]
    assert result["regular_embedded"]
