"""Integration test for the CO-after-invoice workflow wiring.

Drives translate_Buyways_Invoices over a tiny in-memory CSV with the e-Builder
reference-data calls monkeypatched, and asserts that an already-imported invoice
whose now-billed total exceeds its commitment produces (1) a commitment change
order and (2) a <invoice>-1 follow-up cost line -- while an invoice under its
commitment produces neither. No network, no config, no e-Builder.

Run: .venv/Scripts/python.exe -m pytest tests/test_translate_wiring.py -v
"""

from eb.ebInv import translate_BW_Invoices as tr


CSV_TEXT = (
    "Invoice No,PO No,Invoice Status,Invoice Total\n"
    "X100,L100,Payable,8606.48\n"   # already in EB; billed 8606.48 > commitment 8439.60 -> CO + -1 line
    "X200,L200,Payable,5000.00\n"   # already in EB; billed under commitment -> nothing
)

ACTIVE_POS = {
    "L100": {"FMP": "301105", "Value": "8439.60", "Vendor": "Acme",
             "PO_ID": "PO-1", "CommitmentType": "1", "Description": "gen parts"},
    "L200": {"FMP": "301106", "Value": "8439.60", "Vendor": "Beta",
             "PO_ID": "PO-2", "CommitmentType": "1", "Description": "widgets"},
}


def _patch_reference_data(monkeypatch, tmp_path):
    # e-Builder reference-data reads -> deterministic stubs
    monkeypatch.setattr(tr.ebCost, "getBudgetTasks", lambda: {})
    monkeypatch.setattr(tr.ebAPI, "get_FundingRules", lambda: {})
    monkeypatch.setattr(tr.ebAPI, "get_active_Projects", lambda: {})
    monkeypatch.setattr(tr.ebAPI, "get_activePOs", lambda ebProjs: ACTIVE_POS)
    monkeypatch.setattr(tr.ebAPI, "get_Invoices", lambda: ["X100", "X200"])
    monkeypatch.setattr(tr.ebAPI, "get_Invoices_dict",
                        lambda: {"X100": {"Status": "Approved"}, "X200": {"Status": "Approved"}})
    monkeypatch.setattr(tr.ebAPI, "get_daily_imports_dir", lambda create=False: tmp_path)
    monkeypatch.setattr(tr.ebAPI, "get_dry_run", lambda: True)


def test_co_after_invoice_wiring(monkeypatch, tmp_path):
    _patch_reference_data(monkeypatch, tmp_path)

    # Capture what the posters would send, instead of posting.
    posted_cos, posted_lines = [], []
    monkeypatch.setattr(tr.co_builder, "post_commitment_co",
                        lambda payload, dry_run=True: posted_cos.append(payload))
    monkeypatch.setattr(tr.co_builder, "post_followup_cost_line",
                        lambda payload, dry_run=True: posted_lines.append(payload))

    csv_path = tmp_path / "invoices.csv"
    csv_path.write_text(CSV_TEXT, encoding="utf-8")
    monkeypatch.chdir(tmp_path)  # ebInvoiceLog.txt is written to cwd

    result = tr.translate_Buyways_Invoices(str(csv_path), "20260911")
    counts = result["Stats"]

    # Exactly one CO and one follow-up line, from the over-commitment invoice only.
    assert counts["ChangeOrder"] == 1
    assert counts["FollowupLine"] == 1
    assert counts["AlreadyInEB"] == 2  # both invoices are already-in-EB, no paid update

    assert len(posted_cos) == 1
    assert len(posted_lines) == 1

    co = posted_cos[0]
    assert co["Commitment Number"] == "L100"
    assert co["Change Amount"] == "166.88"
    assert co["New Commitment Amount"] == "8606.48"

    line = posted_lines[0]
    assert line["Invoice Number"] == "X100-1"       # the <invoice>-1 second line
    assert line["Invoice Item Amount"] == "166.88"  # the shipping delta
    assert line["Commitment Number"] == "L100"


def test_no_co_when_all_invoices_under_commitment(monkeypatch, tmp_path):
    _patch_reference_data(monkeypatch, tmp_path)
    monkeypatch.setattr(tr.co_builder, "post_commitment_co", lambda payload, dry_run=True: None)
    monkeypatch.setattr(tr.co_builder, "post_followup_cost_line", lambda payload, dry_run=True: None)

    # Both invoices billed under their commitment.
    csv_path = tmp_path / "invoices.csv"
    csv_path.write_text(
        "Invoice No,PO No,Invoice Status,Invoice Total\n"
        "X100,L100,Payable,1000.00\n"
        "X200,L200,Payable,2000.00\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    result = tr.translate_Buyways_Invoices(str(csv_path), "20260911")
    counts = result["Stats"]
    assert counts["ChangeOrder"] == 0
    assert counts["FollowupLine"] == 0
