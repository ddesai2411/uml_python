"""Config dry-run safety: a missing/false/true dry_run key is honored, and the
default is the safe one (dry run ON) so nothing posts to production by accident.

Pure test of eBuilderConfig.from_dict -- no file IO, no network.
Run: .venv/Scripts/python.exe -m pytest tests/test_config.py -v
"""

import pytest

from uml_lib.ebAPI_config import eBuilderConfig


def base(**overrides):
    data = {
        "hostname": "https://api2-us2.e-builder.net",
        "username": "you@example.com",
        "password": "secret",
    }
    data.update(overrides)
    return data


def test_dry_run_defaults_to_true_when_absent():
    cfg = eBuilderConfig.from_dict(base())
    assert cfg.dry_run is True


def test_dry_run_false_is_honored():
    cfg = eBuilderConfig.from_dict(base(dry_run=False))
    assert cfg.dry_run is False


def test_dry_run_true_is_honored():
    cfg = eBuilderConfig.from_dict(base(dry_run=True))
    assert cfg.dry_run is True


def test_dry_run_non_bool_rejected():
    with pytest.raises(TypeError):
        eBuilderConfig.from_dict(base(dry_run="false"))
