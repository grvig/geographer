import pytest

from geographer_pipeline import __version__
from geographer_pipeline.__main__ import main


def test_version_flag_prints_version(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_no_command_prints_help_and_fails(capsys):
    assert main([]) == 1
    assert "usage:" in capsys.readouterr().out


def test_index_rejects_unknown_country_before_any_request(capsys):
    assert main(["index", "IN", "ZZ"]) == 2
    assert "Unknown country code" in capsys.readouterr().out
