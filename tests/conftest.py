import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest


@pytest.fixture(autouse=True)
def _isolate_rcparams():
    """Give every test Matplotlib's defaults and restore them afterwards."""
    with matplotlib.rc_context():
        matplotlib.style.use("default")
        yield
    plt.close("all")
