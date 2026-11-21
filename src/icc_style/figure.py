"""Figure finalization (titles and source notes) and export."""

from __future__ import annotations

import os
import warnings
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Literal

import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.layout_engine import ConstrainedLayoutEngine

from icc_style.colors import DARK_GRAY

_GID = "icc-style-finalize"
# Titles are prose: "$" is never math here, so "R$ 10M to R$ 12M" renders as is.
_TEXT = {"gid": _GID, "parse_math": False}
_POINTS_PER_INCH = 72


def finalize_figure(
    fig: Figure,
    *,
    title: str | None = None,
    subtitle: str | None = None,
    source: str | None = None,
) -> Figure:
    """Add a figure-level title, subtitle and source note.

    The title and subtitle are left-aligned at the top of the figure and the
    source note at the bottom; the axes are laid out in the space between
    them. Use it for charts that leave the notebook (slides, reports, web):
    an action title states the conclusion, the subtitle the measure and
    units, and the source note where the data come from.

    The texts are drawn literally: ``$`` does not start mathtext, so amounts
    such as ``"R$ 10M to R$ 12M"`` need no escaping.

    Call it after plotting, as the last step before saving. Calling it again
    replaces the previous texts. The figure must use constrained layout (the
    ICC theme default) or no layout engine.

    Parameters
    ----------
    fig : Figure
        The figure to finalize.
    title : str, optional
        Main title, in bold. Use ``\\n`` for an explicit line break.
    subtitle : str, optional
        Secondary line below the title, typically the measure and units.
    source : str, optional
        Note at the bottom, e.g. ``"Source: IBGE. Note: values in 2024 R$."``

    Returns
    -------
    Figure
        The same figure, for chaining.
    """
    for text in [t for t in fig.texts if t.get_gid() == _GID]:
        text.remove()

    engine = fig.get_layout_engine()
    if engine is None:
        fig.set_layout_engine("constrained")
        engine = fig.get_layout_engine()
    if not isinstance(engine, ConstrainedLayoutEngine):
        raise ValueError(
            "finalize_figure() requires constrained layout, the ICC theme "
            "default; create the figure with layout='constrained'."
        )

    params = engine.get()
    height_in = fig.get_figheight()
    pad_x = params["w_pad"] / fig.get_figwidth()
    pad_y = params["h_pad"] / height_in
    # Gaps between stacked texts and between texts and the plotting area,
    # proportional to the base font size so that every context scales alike.
    font_in = mpl.rcParams["font.size"] / _POINTS_PER_INCH
    small_gap = 0.35 * font_in / height_in
    large_gap = 1.2 * font_in / height_in

    header = [
        (
            title,
            {
                "fontsize": mpl.rcParams["figure.titlesize"],
                "fontweight": mpl.rcParams["figure.titleweight"],
                "color": mpl.rcParams["text.color"],
            },
        ),
        (subtitle, {"fontsize": "medium", "color": DARK_GRAY}),
    ]
    y = 1.0 - pad_y
    header_bottom = None
    for content, style in header:
        if not content:
            continue
        text = fig.text(pad_x, y, content, ha="left", va="top", **_TEXT, **style)
        _warn_if_too_wide(fig, text, pad_x)
        header_bottom = y - _height(fig, text)
        y = header_bottom - small_gap

    footer_top = None
    if source:
        text = fig.text(
            pad_x,
            pad_y,
            source,
            **_TEXT,
            ha="left",
            va="bottom",
            fontsize="small",
            color=DARK_GRAY,
        )
        _warn_if_too_wide(fig, text, pad_x)
        footer_top = pad_y + _height(fig, text)

    # Constrained layout keeps a padding of h_pad inside the rectangle, so it
    # is subtracted here to make the visible gaps equal to large_gap.
    rect_top = 1.0 if header_bottom is None else header_bottom - large_gap + pad_y
    rect_bottom = 0.0 if footer_top is None else footer_top + large_gap - pad_y
    engine.set(rect=(0.0, rect_bottom, 1.0, rect_top - rect_bottom))
    return fig


def _height(fig: Figure, text) -> float:
    return text.get_window_extent().height / fig.bbox.height


def _warn_if_too_wide(fig: Figure, text, pad_x: float) -> None:
    width = text.get_window_extent().width / fig.bbox.width
    if width > 1.0 - 2 * pad_x:
        warnings.warn(
            f"Text {text.get_text()[:40]!r} is wider than the figure and will "
            f"be cut off; shorten it or add a line break ('\\n').",
            UserWarning,
            stacklevel=3,
        )


def save_figure(
    fig: Figure,
    path: str | os.PathLike[str],
    *,
    formats: Iterable[str] | None = None,
    dpi: float | None = None,
    transparent: bool = False,
    svg_text: Literal["path", "text"] = "path",
    bbox_inches: str | None = None,
    **savefig_kwargs: Any,
) -> list[Path]:
    """Save a figure in one or more formats with consistent export settings.

    Parameters
    ----------
    fig : Figure
        The figure to save.
    path : str or path-like
        Output file. With ``formats``, the extension is replaced by each
        format (``"figures/revenue"`` → ``figures/revenue.png``, ...). Missing
        parent directories are created.
    formats : iterable of str, optional
        For example ``("png", "svg", "pdf")``. Defaults to the extension of
        ``path``.
    dpi : float, optional
        Resolution of raster output (PNG). Defaults to ``savefig.dpi``, which
        the theme sets to 300. Vector formats are resolution independent.
    transparent : bool
        Save without background, e.g. for slides with colored backgrounds.
    svg_text : {"path", "text"}
        ``"path"`` (default) converts SVG text to outlines: the file looks the
        same everywhere but text is not editable or selectable. ``"text"``
        keeps real text, which is editable and smaller, but viewers without
        Poppins installed (or loaded by the web page) will substitute a font.
    bbox_inches : str, optional
        ``None`` keeps the exact figure size, which matters for slides and
        layouts. ``"tight"`` crops to the drawn content, changing the size.
    **savefig_kwargs
        Passed to `matplotlib.figure.Figure.savefig`.

    Returns
    -------
    list of Path
        The files written.

    Notes
    -----
    PDF output embeds the fonts as TrueType (editable in Illustrator,
    Inkscape and similar tools). PDF and SVG files omit the creation date and
    use fixed internal identifiers, so re-running the same script produces
    byte-identical files, which keeps figures under version control clean.
    """
    if svg_text not in ("path", "text"):
        raise ValueError(f"svg_text must be 'path' or 'text', not {svg_text!r}")
    path = Path(path)
    supported = fig.canvas.get_supported_filetypes()

    if formats is None:
        if not path.suffix:
            raise ValueError(
                "path has no file extension; add one (e.g. 'chart.png') or "
                "pass formats=('png', 'svg', 'pdf')"
            )
        targets = [path]
    else:
        formats = [fmt.lower().lstrip(".") for fmt in formats]
        if not formats:
            raise ValueError("formats must contain at least one format")
        stem = path.with_suffix("") if path.suffix.lstrip(".") in supported else path
        targets = [stem.with_name(f"{stem.name}.{fmt}") for fmt in formats]

    for target in targets:
        fmt = target.suffix.lstrip(".").lower()
        if fmt not in supported:
            raise ValueError(
                f"unsupported format {fmt!r}; supported: {', '.join(sorted(supported))}"
            )

    rc = {
        "svg.fonttype": "path" if svg_text == "path" else "none",
        "svg.hashsalt": "icc-style",
        "pdf.fonttype": 42,
    }
    written = []
    for target in targets:
        fmt = target.suffix.lstrip(".").lower()
        kwargs = dict(savefig_kwargs)
        if fmt == "pdf":
            kwargs.setdefault("metadata", {"CreationDate": None})
        elif fmt == "svg":
            kwargs.setdefault("metadata", {"Date": None})
        target.parent.mkdir(parents=True, exist_ok=True)
        with mpl.rc_context(rc):
            fig.savefig(
                target,
                format=fmt,
                dpi=dpi if dpi is not None else mpl.rcParams["savefig.dpi"],
                transparent=transparent,
                bbox_inches=bbox_inches,
                **kwargs,
            )
        written.append(target)
    return written
