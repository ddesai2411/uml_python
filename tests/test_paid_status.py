"""Business requirement #1: Payable -> Paid invoice status update.

These tests exercise the pure decision/build logic in
``eb.ebInv.invoice_updates`` against representative Byways rows and e-Builder
invoice state. They require no network, no config, and no e-Builder access --
this is how the requirement is validated without a test environment.

Run: .venv/Scripts/python.exe -m pytest tests/test_paid_status.py -v
"""

from eb.ebInv import invoice_updates


def bw_row(**overrides):
    """A minimal Byways invoice CSV row; override any field per test."""
    row = {
        "Invoice No": "X3321427",
        "Invoice Status": "Paid",
        "PO No": "L001939576",
        "PO Line No": "1",
        "Supplier Name": "Acme Supply",
        "Supplier Number": "0001234",
        "Paid Date": "2026-09-01",
        "FMP Number": "",
    }
    row.update(overrides)
    return row


def eb_state(**invoices):
    """e-Builder invoice status map, as get_Invoices_dict() returns it."""
    return {vid: {"Status": status, "Source": "BW"} for vid, status in invoices.items()}


# ---------------------------------------------------------------------------
# should_update_to_paid
# ---------------------------------------------------------------------------

def test_paid_transition_is_flagged():
    """Already in EB as Approved, Byways now Paid -> update needed."""
    eb = eb_state(X3321427="Approved")
    assert invoice_updates.should_update_to_paid(bw_row(), eb) is True


def test_still_payable_is_not_flagged():
    """Byways still Payable -> nothing to update."""
    eb = eb_state(X3321427="Approved")
    assert invoice_updates.should_update_to_paid(bw_row(**{"Invoice Status": "Payable"}), eb) is False


def test_already_paid_in_eb_is_not_flagged():
    """EB already shows Paid -> no duplicate update."""
    eb = eb_state(X3321427="Paid")
    assert invoice_updates.should_update_to_paid(bw_row(), eb) is False


def test_not_in_eb_is_not_flagged():
    """Invoice not in EB -> not an update (it's a normal new import)."""
    eb = eb_state(X9999999="Approved")
    assert invoice_updates.should_update_to_paid(bw_row(), eb) is False


def test_in_process_status_is_not_flagged():
    eb = eb_state(X3321427="Approved")
    assert invoice_updates.should_update_to_paid(bw_row(**{"Invoice Status": "In Process"}), eb) is False


def test_missing_invoice_number_is_not_flagged():
    eb = eb_state(X3321427="Approved")
    assert invoice_updates.should_update_to_paid(bw_row(**{"Invoice No": ""}), eb) is False


# ---------------------------------------------------------------------------
# build_paid_update
# ---------------------------------------------------------------------------

def test_build_paid_update_maps_all_fields():
    payload = invoice_updates.build_paid_update(bw_row(), fmp="301105")
    assert payload == {
        "FMP Number": "301105",
        "Status": "Paid",
        "Invoice Number": "X3321427",
        "Company Name": "Acme Supply",
        "Company Number": "0001234",
        "Date Paid": "2026-09-01",
    }


def test_build_paid_update_status_is_always_paid():
    payload = invoice_updates.build_paid_update(bw_row(**{"Invoice Status": "Paid"}), fmp="1")
    assert payload["Status"] == "Paid"


# ---------------------------------------------------------------------------
# collect_paid_updates (iteration + dedup + fmp lookup)
# ---------------------------------------------------------------------------

def test_collect_dedups_multiline_invoice():
    """A 2-line invoice appears twice in the CSV -> exactly one update."""
    rows = [
        bw_row(**{"PO Line No": "1"}),
        bw_row(**{"PO Line No": "2"}),
    ]
    eb = eb_state(X3321427="Approved")
    updates = invoice_updates.collect_paid_updates(rows, eb, fmp_lookup={"L001939576": "301105"})
    assert len(updates) == 1
    assert updates[0]["FMP Number"] == "301105"
    assert updates[0]["Invoice Number"] == "X3321427"


def test_collect_only_returns_paid_transitions():
    rows = [
        bw_row(**{"Invoice No": "X1", "Invoice Status": "Paid"}),      # transition
        bw_row(**{"Invoice No": "X2", "Invoice Status": "Payable"}),   # still payable
        bw_row(**{"Invoice No": "X3", "Invoice Status": "Paid"}),      # not in EB
    ]
    eb = eb_state(X1="Approved", X2="Approved")  # X3 absent
    updates = invoice_updates.collect_paid_updates(rows, eb)
    assert [u["Invoice Number"] for u in updates] == ["X1"]


def test_collect_fmp_falls_back_to_row_when_po_absent():
    rows = [bw_row(**{"PO No": "L-UNKNOWN", "FMP Number": "999999"})]
    eb = eb_state(X3321427="Approved")
    updates = invoice_updates.collect_paid_updates(rows, eb, fmp_lookup={"L001939576": "301105"})
    assert updates[0]["FMP Number"] == "999999"


# ---------------------------------------------------------------------------
# post_invoice_update dry-run safety
# ---------------------------------------------------------------------------

def test_post_dry_run_posts_nothing():
    payload = invoice_updates.build_paid_update(bw_row(), fmp="1")
    result = invoice_updates.post_invoice_update(payload, dry_run=True)
    assert result["posted"] is False
    assert result["dry_run"] is True
    assert result["payload"] == payload
