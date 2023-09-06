from functools import partial
from pathlib import Path

import pytest


@pytest.fixture()
def project_path() -> Path:
    return Path(__file__).parent.parent.parent


@pytest.fixture()
def app_path(project_path) -> Path:
    return project_path / "difflume" / "tui" / "app.py"


@pytest.fixture(autouse=True)
def _set_home_dir_for_directory_tree(monkeypatch, project_path):
    monkeypatch.setenv(
        "DIFF_LUME_FILE_TREE_HOME", str(project_path / "tests" / "tui" / "fixtures")
    )


@pytest.fixture()
def snap_compare(snap_compare, app_path):
    return partial(snap_compare, app_path=str(app_path), terminal_size=(160, 40))


@pytest.fixture()
def document_url() -> str:
    return "/d"
