"""Theme activation: apply the ICC style sheets to Matplotlib."""

from __future__ import annotations

import contextlib
import functools
import warnings
from collections.abc import Iterator, Mapping
from importlib import resources
from typing import Any

import matplotlib as mpl
import matplotlib.style

from icc_style.colors import SEQUENTIAL_CMAP
from icc_style.fonts import FontRegistrationError, check_fonts, register_fonts

#: Available contexts. ``"default"`` is the base style sheet alone; the others
#: are applied on top of it.
CONTEXTS = ("default", "presentation", "publication")


@functools.cache
def _read_style(name: str) -> dict[str, Any]:
    resource = resources.files("icc_style.styles").joinpath(f"{name}.mplstyle")
    with resources.as_file(resource) as path:
        return dict(mpl.rc_params_from_file(path, use_default_template=False))


def rc_params(context: str = "default") -> dict[str, Any]:
    """Return the Matplotlib rcParams that make up the ICC theme.

    Useful where a theme must be passed explicitly instead of applied
    globally, e.g. ``seaborn.objects.Plot.theme(icc.rc_params())`` or
    ``matplotlib.rc_context(icc.rc_params("publication"))``. Fonts are not
    registered by this function; see `register_fonts`.
    """
    if context not in CONTEXTS:
        raise ValueError(
            f"unknown context {context!r}; choose one of {', '.join(CONTEXTS)}"
        )
    params = _read_style("icc").copy()
    if context != "default":
        params.update(_read_style(context))
    # The colormap is defined in Python, so it cannot live in the style sheet.
    params["image.cmap"] = SEQUENTIAL_CMAP.name
    return params


def set_theme(context: str = "default", *, rc: Mapping[str, Any] | None = None) -> None:
    """Apply the ICC theme to all subsequent Matplotlib and Seaborn figures.

    Parameters
    ----------
    context : {"default", "presentation", "publication"}
        ``"default"`` suits notebooks and general analysis, ``"presentation"``
        enlarges type and marks for slides, ``"publication"`` sizes figures for
        articles, reports and the web.
    rc : mapping, optional
        Extra rcParams applied after the theme, for local adjustments such as
        ``{"figure.figsize": (6, 6)}``.

    Notes
    -----
    Registers the bundled Poppins fonts and warns if Matplotlib still cannot
    resolve Poppins Regular and Bold. Calling Seaborn's ``set_theme``,
    ``set_style`` or ``set_context`` afterwards overrides parts of this theme,
    so call this function last. Restore Matplotlib's defaults with
    ``matplotlib.style.use("default")``.
    """
    params = rc_params(context)
    try:
        register_fonts()
    except FontRegistrationError as exc:
        warnings.warn(str(exc), UserWarning, stacklevel=2)
    matplotlib.style.use(params)
    if rc:
        matplotlib.style.use(dict(rc))
    _warn_if_fonts_missing()


@contextlib.contextmanager
def theme_context(
    context: str = "default", *, rc: Mapping[str, Any] | None = None
) -> Iterator[None]:
    """Apply the ICC theme temporarily, restoring previous settings on exit.

    Create *and save or display* figures inside the ``with`` block: some
    properties are only resolved when a figure is drawn.

    >>> with icc.theme_context("presentation"):
    ...     fig, ax = plt.subplots()
    ...     ax.plot([1, 2, 3])
    ...     icc.save_figure(fig, "slide-chart.png")
    """
    with mpl.rc_context():
        set_theme(context, rc=rc)
        yield


def _warn_if_fonts_missing() -> None:
    resolved = check_fonts()
    missing = [weight for weight, path in resolved.items() if path is None]
    if missing:
        warnings.warn(
            f"Matplotlib cannot find Poppins ({' and '.join(missing)}); text "
            f"will be drawn with a fallback font. Run icc_style.check_fonts() "
            f"for details.",
            UserWarning,
            stacklevel=3,
        )
