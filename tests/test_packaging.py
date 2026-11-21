from importlib import metadata, resources

import icc_style as icc


def test_package_resources_are_present():
    root = resources.files("icc_style")
    for name in ("Poppins-Regular.ttf", "Poppins-Bold.ttf", "OFL.txt"):
        assert root.joinpath("fonts", name).is_file(), name
    for name in ("icc", "presentation", "publication"):
        assert root.joinpath("styles", f"{name}.mplstyle").is_file(), name
    assert root.joinpath("py.typed").is_file()


def test_font_license_keeps_the_copyright_notice():
    text = resources.files("icc_style").joinpath("fonts", "OFL.txt").read_text()
    assert "Copyright 2020 The Poppins Project Authors" in text
    assert "SIL OPEN FONT LICENSE Version 1.1" in text


def test_installed_metadata_matches_the_package():
    assert metadata.version("icc-style") == icc.__version__
    meta = metadata.metadata("icc-style")
    assert meta["Name"] == "icc-style"
    assert "OFL-1.1" in (meta["License-Expression"] or "")
    requirements = metadata.requires("icc-style") or []
    runtime = [r for r in requirements if "extra ==" not in r]
    assert [r.split(">")[0].strip() for r in runtime] == ["matplotlib"]
