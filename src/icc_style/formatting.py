"""Tick and label formatters for business and economic charts.

Each function returns a Matplotlib `~matplotlib.ticker.Formatter`, used either
on an axis or, because formatters are callable, on single values::

    ax.yaxis.set_major_formatter(icc.brl_formatter(compact=True))
    ax.bar_label(bars, fmt=icc.percent_formatter(decimals=1))
    icc.brl_formatter(compact=True)(2_500_000)  # 'R$ 2.5M'
"""

from __future__ import annotations

import math
from typing import Literal

import matplotlib as mpl
from matplotlib.ticker import Formatter

Locale = Literal["en", "pt-BR"]
Negative = Literal["minus", "parentheses"]

_SEPARATORS = {"en": (",", "."), "pt-BR": (".", ",")}
_COMPACT_UNITS = {
    "en": ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")),
    "pt-BR": ((1e12, " tri"), (1e9, " bi"), (1e6, " mi"), (1e3, " mil")),
}
_MAX_AUTO_DECIMALS = 2
_NBSP = " "


class _NumberFormatter(Formatter):
    """Shared implementation of the public formatter factories."""

    def __init__(
        self,
        decimals: int | None,
        *,
        compact: bool,
        prefix: str,
        suffix: str,
        scale: float,
        signed: bool,
        negative: Negative,
        locale: Locale,
    ) -> None:
        if locale not in _SEPARATORS:
            raise ValueError(f"locale must be 'en' or 'pt-BR', not {locale!r}")
        if negative not in ("minus", "parentheses"):
            raise ValueError(
                f"negative must be 'minus' or 'parentheses', not {negative!r}"
            )
        if decimals is not None and decimals < 0:
            raise ValueError("decimals must be a non-negative integer or None")
        self.decimals = decimals
        self.compact = compact
        self.prefix = prefix
        self.suffix = suffix
        self.scale = scale
        self.signed = signed
        self.negative = negative
        self.locale = locale
        self._axis_decimals: int | None = None

    def set_locs(self, locs) -> None:
        # With automatic precision, all ticks of an axis share the number of
        # decimals needed by the most precise one ("0.5, 1.0, 1.5", not
        # "0.5, 1, 1.5"). Compact labels keep per-value precision instead.
        super().set_locs(locs)
        self._axis_decimals = None
        if self.decimals is None and not self.compact and len(locs):
            self._axis_decimals = max(
                _needed_decimals(abs(loc) * self.scale) for loc in locs
            )

    def __call__(self, x: float, pos: int | None = None) -> str:
        value = float(x) * self.scale
        if math.isnan(value):
            return ""
        unit = ""
        if self.compact:
            for threshold, label in _COMPACT_UNITS[self.locale]:
                if abs(value) >= threshold:
                    value /= threshold
                    unit = label
                    break

        decimals = self.decimals
        if decimals is None:
            decimals = self._axis_decimals
        if decimals is None:
            decimals = _needed_decimals(abs(value))
        body = self._group(abs(value), decimals)
        is_negative = value < 0 and body.strip("0.,") != ""

        text = f"{self.prefix}{body}{unit}{self.suffix}"
        if is_negative:
            if self.negative == "parentheses":
                return f"({text})"
            minus = "−" if mpl.rcParams["axes.unicode_minus"] else "-"
            return minus + text
        if self.signed and body.strip("0.,") != "":
            return "+" + text
        return text

    def _group(self, value: float, decimals: int) -> str:
        thousands, decimal = _SEPARATORS[self.locale]
        text = f"{value:,.{decimals}f}"
        return text.translate(str.maketrans({",": thousands, ".": decimal}))


def _needed_decimals(value: float) -> int:
    """Smallest number of decimals (up to a cap) that represents *value*."""
    for decimals in range(_MAX_AUTO_DECIMALS + 1):
        if math.isclose(round(value, decimals), value, rel_tol=1e-9, abs_tol=1e-9):
            return decimals
    return _MAX_AUTO_DECIMALS


def number_formatter(
    decimals: int | None = None,
    *,
    compact: bool = False,
    prefix: str = "",
    suffix: str = "",
    scale: float = 1.0,
    signed: bool = False,
    negative: Negative = "minus",
    locale: Locale = "en",
) -> Formatter:
    """Format plain numbers with thousands separators.

    Parameters
    ----------
    decimals : int, optional
        Fixed number of decimals. By default, an axis shows as few decimals as
        needed to label every tick exactly (at most two), the same for all
        ticks. For data labels and annotations, set it explicitly (for
        example ``decimals=0``) to avoid spurious precision.
    compact : bool
        Abbreviate large values: ``1.5M`` / ``1,5 mi``, ``2B`` / ``2 bi``.
    prefix, suffix : str
        Text placed around the number, e.g. ``suffix=" t"``.
    scale : float
        Multiply values by this factor before formatting.
    signed : bool
        Prefix positive values with ``+``, useful for changes.
    negative : {"minus", "parentheses"}
        Show negatives as ``−5`` or, accounting style, as ``(5)``.
    locale : {"en", "pt-BR"}
        ``"en"`` writes ``1,234.5``; ``"pt-BR"`` writes ``1.234,5``.
    """
    return _NumberFormatter(
        decimals,
        compact=compact,
        prefix=prefix,
        suffix=suffix,
        scale=scale,
        signed=signed,
        negative=negative,
        locale=locale,
    )


def brl_formatter(
    decimals: int | None = None,
    *,
    compact: bool = False,
    scale: float = 1.0,
    signed: bool = False,
    negative: Negative = "minus",
    locale: Locale = "en",
) -> Formatter:
    """Format Brazilian real amounts: ``R$ 1,250`` or ``R$ 1.2M``.

    Use ``scale`` when the data are in other units, e.g. ``scale=1e6`` for
    values stored in millions together with ``compact=True``. See
    `number_formatter` for the other parameters.
    """
    return _NumberFormatter(
        decimals,
        compact=compact,
        prefix="R$" + _NBSP,
        suffix="",
        scale=scale,
        signed=signed,
        negative=negative,
        locale=locale,
    )


def percent_formatter(
    decimals: int | None = None,
    *,
    scale: float = 100.0,
    signed: bool = False,
    negative: Negative = "minus",
    locale: Locale = "en",
) -> Formatter:
    """Format fractions as percentages: ``0.125`` becomes ``12.5%``.

    If the data are already in percent (``12.5``), pass ``scale=1``. See
    `number_formatter` for the other parameters.
    """
    return _NumberFormatter(
        decimals,
        compact=False,
        prefix="",
        suffix="%",
        scale=scale,
        signed=signed,
        negative=negative,
        locale=locale,
    )


def bps_formatter(
    decimals: int | None = 0,
    *,
    scale: float = 10_000.0,
    signed: bool = False,
    unit: str = "bps",
    negative: Negative = "minus",
    locale: Locale = "en",
) -> Formatter:
    """Format fractions as basis points: ``0.0125`` becomes ``125 bps``.

    If the data are already in basis points, pass ``scale=1``. Portuguese
    texts often use ``unit="p.b."``. See `number_formatter` for the other
    parameters.
    """
    return _NumberFormatter(
        decimals,
        compact=False,
        prefix="",
        suffix=_NBSP + unit if unit else "",
        scale=scale,
        signed=signed,
        negative=negative,
        locale=locale,
    )
