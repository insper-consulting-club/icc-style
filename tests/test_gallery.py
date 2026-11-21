import shutil
from pathlib import Path

import pytest

NOTEBOOK = Path(__file__).parents[1] / "examples" / "gallery.ipynb"


@pytest.mark.slow
def test_gallery_runs_from_start_to_finish(tmp_path):
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    pytest.importorskip("seaborn")
    pytest.importorskip("pandas")
    if not NOTEBOOK.exists():
        pytest.skip("gallery notebook is not part of this distribution")

    copy = tmp_path / NOTEBOOK.name
    shutil.copy(NOTEBOOK, copy)
    notebook = nbformat.read(copy, as_version=4)
    client = nbclient.NotebookClient(
        notebook, timeout=600, resources={"metadata": {"path": str(tmp_path)}}
    )
    client.execute()

    figures = {p.name for p in (tmp_path / "figures").iterdir()}
    assert {"01_ranking.png", "13_slide.pdf", "14_article.svg"} <= figures
