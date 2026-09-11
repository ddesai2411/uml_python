"""Smoke test to confirm the pytest suite is wired up correctly.

Run from the project root (C:\\git\\UMASS\\uml_python) with:
    python -m pytest
This file has no dependencies on e-Builder, Buyways, the API, or SQL. It only
proves that pytest discovers and runs tests in the ``tests/`` folder. Real
business-requirement tests (Payable->Paid, invoice amount, commitment change
orders) will be added alongside it.
"""


def test_hello_world():
    assert "hello" + " " + "world" == "hello world"


def test_math_sanity():
    assert 2 + 2 == 4
