import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

import icc_style as icc

MINUS = "−"
NBSP = " "


@pytest.mark.parametrize(
    ("formatter", "value", "expected"),
    [
        (icc.number_formatter(), 1234567, "1,234,567"),
        (icc.number_formatter(locale="pt-BR"), 1234567, "1.234.567"),
        (icc.number_formatter(decimals=2), 1234.5, "1,234.50"),
        (icc.number_formatter(decimals=1, locale="pt-BR"), 1234.56, "1.234,6"),
        (icc.number_formatter(), 2.5, "2.5"),
        (icc.number_formatter(), 0.1 + 0.2, "0.3"),
        (icc.number_formatter(), -42, f"{MINUS}42"),
        (icc.number_formatter(negative="parentheses"), -1234.5, "(1,234.5)"),
        (icc.number_formatter(signed=True), 5, "+5"),
        (icc.number_formatter(signed=True), 0, "0"),
        (icc.number_formatter(decimals=0), -0.2, "0"),
        (icc.number_formatter(compact=True), 1_500_000, "1.5M"),
        (icc.number_formatter(compact=True), 2_000_000_000, "2B"),
        (icc.number_formatter(compact=True), 3_100_000_000_000, "3.1T"),
        (icc.number_formatter(compact=True), 950, "950"),
        (icc.number_formatter(compact=True, locale="pt-BR"), 1_500_000, "1,5 mi"),
        (icc.number_formatter(compact=True, locale="pt-BR"), 2_000, "2 mil"),
        (icc.number_formatter(suffix=" t"), 12, "12 t"),
        (icc.brl_formatter(), 1250, f"R${NBSP}1,250"),
        (icc.brl_formatter(locale="pt-BR", decimals=2), 1250.5, f"R${NBSP}1.250,50"),
        (icc.brl_formatter(compact=True), 2_500_000, f"R${NBSP}2.5M"),
        (icc.brl_formatter(compact=True, scale=1e6), 150, f"R${NBSP}150M"),
        (
            icc.brl_formatter(compact=True, locale="pt-BR"),
            3_200_000_000,
            f"R${NBSP}3,2 bi",
        ),
        (icc.brl_formatter(compact=True), -1_500_000, f"{MINUS}R${NBSP}1.5M"),
        (icc.brl_formatter(negative="parentheses"), -300, f"(R${NBSP}300)"),
        (icc.brl_formatter(signed=True, compact=True, scale=1e6), 18, f"+R${NBSP}18M"),
        (icc.percent_formatter(), 0.125, "12.5%"),
        (icc.percent_formatter(decimals=0), 0.125, "12%"),
        (icc.percent_formatter(decimals=1, locale="pt-BR"), 0.125, "12,5%"),
        (icc.percent_formatter(scale=1), 12.5, "12.5%"),
        (icc.percent_formatter(signed=True, decimals=0), -0.05, f"{MINUS}5%"),
        (icc.percent_formatter(signed=True, decimals=0), 0.05, "+5%"),
        (icc.bps_formatter(), 0.0125, f"125{NBSP}bps"),
        (icc.bps_formatter(scale=1), 40, f"40{NBSP}bps"),
        (icc.bps_formatter(signed=True), -0.0025, f"{MINUS}25{NBSP}bps"),
        (
            icc.bps_formatter(unit="p.b.", locale="pt-BR", scale=1),
            1500,
            f"1.500{NBSP}p.b.",
        ),
    ],
)
def test_formatters(formatter, value, expected):
    assert formatter(value) == expected


def test_plain_minus_when_unicode_minus_is_disabled():
    mpl.rcParams["axes.unicode_minus"] = False
    assert icc.number_formatter()(-3) == "-3"


def test_nan_is_formatted_as_empty_string():
    assert icc.percent_formatter()(float("nan")) == ""


def test_axis_ticks_share_decimals():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 0.015])
    ax.set_yticks([0, 0.005, 0.01, 0.015])
    ax.yaxis.set_major_formatter(icc.percent_formatter())
    fig.canvas.draw()
    labels = [label.get_text() for label in ax.get_yticklabels()]
    assert labels == ["0.0%", "0.5%", "1.0%", "1.5%"]


def test_compact_axis_ticks_avoid_duplicate_labels():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 2_000_000])
    ax.set_yticks([0, 500_000, 1_000_000, 1_500_000, 2_000_000])
    ax.yaxis.set_major_formatter(icc.brl_formatter(compact=True))
    fig.canvas.draw()
    labels = [label.get_text() for label in ax.get_yticklabels()]
    assert labels == [f"R${NBSP}{v}" for v in ("0", "500K", "1M", "1.5M", "2M")]


def test_formatter_works_with_bar_label():
    _fig, ax = plt.subplots()
    bars = ax.bar(["a", "b"], [0.25, 0.5])
    texts = ax.bar_label(bars, fmt=icc.percent_formatter(decimals=0))
    assert [t.get_text() for t in texts] == ["25%", "50%"]


@pytest.mark.parametrize(
    "kwargs",
    [{"locale": "fr"}, {"negative": "red"}, {"decimals": -1}],
)
def test_invalid_arguments_are_rejected(kwargs):
    with pytest.raises(ValueError, match="must be"):
        icc.number_formatter(**kwargs)
