# Changelog

All notable changes to this project are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). While the major version is 0, a change that breaks the public API raises the minor version.

## [Unreleased]

## [0.1.0] - 2026-11-21

### Added

- Matplotlib theme with three contexts (`default`, `presentation`, `publication`), applied with `set_theme()`, `theme_context()` or the native style sheets in `icc_style.styles`.
- Bundled Poppins Regular and Bold fonts, registered with Matplotlib on import, with `register_fonts()` and `check_fonts()` for diagnostics.
- Official brand colors, categorical and neutral extensions, and the `icc_reds` and `icc_diverging` colormaps.
- Number formatters for plain numbers, Brazilian reais, percentages and basis points, with English and Brazilian Portuguese separators.
- `finalize_figure()` for titles, subtitles and source notes, and `save_figure()` for PNG, SVG and PDF export.
- Seaborn support, including `seaborn.objects` through `rc_params()`.
- Example gallery notebook on synthetic data, test suite and CI on Linux, Windows and macOS.

[Unreleased]: https://github.com/insper-consulting-club/icc-style/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/insper-consulting-club/icc-style/releases/tag/v0.1.0
