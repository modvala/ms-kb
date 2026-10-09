import pytest

from ms_kb import __version__
from ms_kb.cli import main


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"kb {__version__}"


def test_no_args_prints_help(capsys):
    assert main([]) == 0
    assert "usage: kb" in capsys.readouterr().out
