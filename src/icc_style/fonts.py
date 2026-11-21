"""Registration of the bundled Poppins fonts with Matplotlib.

Fonts are added to Matplotlib's in-process font manager only. Nothing is
installed on the system and Matplotlib's on-disk font cache is not modified,
so registration has to happen once per Python session (``set_theme`` does it).
"""

from __future__ import annotations

import atexit
import contextlib
from importlib import resources
from pathlib import Path

import matplotlib
from matplotlib import font_manager

FAMILY = "Poppins"
FONT_FILES = ("Poppins-Regular.ttf", "Poppins-Bold.ttf")

_paths: dict[str, Path] = {}
# Keeps extracted resources alive when the package is imported from a zip file.
_resource_stack = contextlib.ExitStack()
atexit.register(_resource_stack.close)


class FontRegistrationError(RuntimeError):
    """Raised when the bundled Poppins fonts cannot be registered."""


def _font_path(filename: str) -> Path:
    resource = resources.files("icc_style").joinpath("fonts", filename)
    if not resource.is_file():
        raise FileNotFoundError(f"bundled font resource is missing: {filename}")
    # A real filesystem path is required: Matplotlib reopens the file whenever
    # it renders text, so a temporary extraction must outlive this call.
    # Resolving symlinks (e.g. a venv's lib64 -> lib) matches the canonical
    # paths that findfont() reports.
    return _resource_stack.enter_context(resources.as_file(resource)).resolve()


def register_fonts() -> tuple[Path, ...]:
    """Register the bundled Poppins Regular and Bold fonts with Matplotlib.

    Safe to call repeatedly: fonts already known to Matplotlib are not added
    again. Returns the paths of the registered font files.

    Raises
    ------
    FontRegistrationError
        If a font file is missing or cannot be read by Matplotlib.
    """
    # Checked against the live font list on every call, because Matplotlib can
    # rebuild its font manager during a session.
    known = {Path(entry.fname).resolve() for entry in font_manager.fontManager.ttflist}
    paths = []
    for filename in FONT_FILES:
        try:
            path = _paths.get(filename) or _font_path(filename)
            if path not in known:
                font_manager.fontManager.addfont(path)
        except Exception as exc:
            raise FontRegistrationError(
                f"Could not register the bundled font {filename!r} with "
                f"Matplotlib {matplotlib.__version__}: {exc}. Charts will fall "
                f"back to another font. Reinstalling icc-style usually fixes a "
                f"missing file; alternatively, install Poppins on the system."
            ) from exc
        _paths[filename] = path
        paths.append(path)
    return tuple(paths)


def check_fonts() -> dict[str, Path | None]:
    """Report which font files Matplotlib resolves for Poppins.

    Returns a mapping with the keys ``"regular"`` and ``"bold"``. Each value is
    the file Matplotlib would use for that weight of the Poppins family, or
    ``None`` if that weight is not available (Matplotlib would substitute a
    different font or weight).
    """
    result: dict[str, Path | None] = {}
    for key, weight in (("regular", 400), ("bold", 700)):
        prop = font_manager.FontProperties(family=FAMILY, weight=weight)
        try:
            found = Path(font_manager.findfont(prop, fallback_to_default=False))
        except ValueError:
            result[key] = None
            continue
        found = found.resolve()
        entry = next(
            (
                e
                for e in font_manager.fontManager.ttflist
                if Path(e.fname).resolve() == found
            ),
            None,
        )
        matches = entry is not None and entry.name == FAMILY and entry.weight == weight
        result[key] = found if matches else None
    return result
