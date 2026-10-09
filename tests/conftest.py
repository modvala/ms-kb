import pytest


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Never touch the real ~/.config/ms-kb during tests."""
    path = tmp_path / "config" / "config.toml"
    monkeypatch.setenv("KB_CONFIG", str(path))
    return path
