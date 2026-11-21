# Contributing

Thanks for helping with ICC Style. This page covers how to propose a change and how a release is made.

## Setup

Install the development environment as described in the [Development section of the README](README.md#development).

## Before opening a pull request

Run the checks that CI runs:

```bash
ruff check . && ruff format --check .
python -m pytest
```

`python -m pytest -m "not slow"` skips the gallery notebook and is enough while iterating. If you change a chart in the gallery, regenerate the figures in `examples/figures/` by running the notebook, and review the images before committing them.

Changes go through a pull request, and CI has to pass before merging. If a change alters colors, sizes or fonts, say so in the description, because it changes the look of every user's charts.

## Commit messages

Start with a short subject in the imperative mood, up to about 50 characters, such as `Fix percent formatter rounding`. For anything that needs context, leave a blank line and explain what changed and why in a body wrapped at about 72 columns. A subject alone is enough for small changes.

## Versioning

Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html), in the form `MAJOR.MINOR.PATCH`.

- `PATCH`: bug fixes that do not change the public API.
- `MINOR`: new, backward-compatible features.
- `MAJOR`: changes that break the public API.

While the major version is 0, the API is not yet stable: a breaking change raises `MINOR`, and `PATCH` is reserved for fixes. Version 1.0.0 is planned for when the public API listed in the README is stable. Changes to colors, sizes or fonts count as notable even when the API is unchanged, so record them in the changelog.

## Changelog

Record every user-visible change in [CHANGELOG.md](CHANGELOG.md) under `Unreleased`, in the sections `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed` or `Security`.

## Releasing

The version lives in one place, `__version__` in `src/icc_style/__init__.py`, and `pyproject.toml` reads it from there.

1. In `CHANGELOG.md`, move the `Unreleased` entries under a new `[X.Y.Z] - YYYY-MM-DD` heading and update the links at the bottom of the file.
2. Set `__version__` to `X.Y.Z`.
3. Run `ruff check . && ruff format --check . && python -m pytest`.
4. Commit with the message `Release X.Y.Z`.
5. Create the tag `vX.Y.Z` on that commit and push it, then create a GitHub release from the tag, using the changelog entry as the description.

The package is distributed from GitHub and is not published on PyPI.
