"""Business requirement #1: Payable -> Paid invoice status update.

These tests exercise the pure decision/build logic in
``eb.ebInv.invoice_updates`` against representative Byways rows and e-Builder
invoice state. They require no network, no config, and no e-Builder access.

The Paid transition is applied via POST /api/v2/Invoices/StatusUpdate (the
"Update Invoice Status" batch process); payload fields come from the EB invoice
record (native invoiceNumber, companyNumber, amount, project name) plus the
Byways Paid Date.

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


def eb_entry(status="Approved", **overrides):
    """One entry as ebAPI.get_Invoices_for_paid_update() returns it."""
    e = {
        "Status": status,
        "InvoiceNumber": "INV-100",     # EB native number
        "CompanyNumber": "KHK001",
        "Amount": 718.30,
        "ProjectName": "KH - Test Project",
    }
    e.update(overrides)
    return e


def eb_state(**invoices):
    """e-Builder lookup map: voucher_id -> entry. Pass status per voucher."""
    return {vid: eb_entry(status=status) for vid, status in invoices.items()}


# ---------------------------------------------------------------------------
# should_update_to_paid
# ---------------------------------------------------------------------------

def test_paid_transition_is_flagged():
    eb = eb_state(X3321427="Approved")
    assert invoice_updates.should_update_to_paid(bw_row(), eb) is True


def test_still_payable_is_not_flagged():
    eb = eb_state(X3321427="Approved")
    assert invoice_updates.should_update_to_paid(bw_row(**{"Invoice Status": "Payable"}), eb) is False


def test_already_paid_in_eb_is_not_flagged():
    eb = eb_state(X3321427="Paid")
    assert invoice_updates.should_update_to_paid(bw_row(), eb) is False


def test_not_in_eb_is_not_flagged():
    eb = eb_state(X9999999="Approved")
    assert invoice_updates.should_update_to_paid(bw_row(), eb) is False


def test_in_process_status_is_not_flagged():
    eb = eb_state(X3321427="Approved")
    assert invoice_updates.should_update_to_paid(bw_row(**{"Invoice Status": "In Process"}), eb) is False


def test_missing_invoice_number_is_not_flagged():
    eb = eb_state(X3321427="Approved")
    assert invoice_updates.should_update_to_paid(bw_row(**{"Invoice No": ""}), eb) is False


# ---------------------------------------------------------------------------
# build_paid_update -> StatusUpdate payload
# ---------------------------------------------------------------------------

def test_build_paid_update_maps_status_update_fields():
    payload = invoice_updates.build_paid_update(bw_row(), eb_entry())
    assert payload["projectIdentifier"] == "KH - Test Project"
    assert payload["invoiceNumber"] == "INV-100"      # EB native, not the Byways X-number
    assert payload["amountPaid"] == 718.30
    assert payload["companyNumber"] == "KHK001"
    assert payload["datePaid"] == "2026-09-01"        # from the Byways row
    assert payload["status"] == "Paid"


def test_build_paid_update_status_is_always_paid():
    payload = invoice_updates.build_paid_update(bw_row(**{"Invoice Status": "Paid"}), eb_entry())
    assert payload["status"] == "Paid"


# ---------------------------------------------------------------------------
# collect_paid_updates (iteration + dedup)
# ---------------------------------------------------------------------------

def test_collect_dedups_multiline_invoice():
    """A 2-line invoice appears twice in the CSV -> exactly one update."""
    rows = [bw_row(**{"PO Line No": "1"}), bw_row(**{"PO Line No": "2"})]
    eb = eb_state(X3321427="Approved")
    updates = invoice_updates.collect_paid_updates(rows, eb)
    assert len(updates) == 1
    assert updates[0]["invoiceNumber"] == "INV-100"


def test_collect_only_returns_paid_transitions():
    rows = [
        bw_row(**{"Invoice No": "X1", "Invoice Status": "Paid"}),      # transition
        bw_row(**{"Invoice No": "X2", "Invoice Status": "Payable"}),   # still payable
        bw_row(**{"Invoice No": "X3", "Invoice Status": "Paid"}),      # not in EB
    ]
    eb = eb_state(X1="Approved", X2="Approved")  # X3 absent
    updates = invoice_updates.collect_paid_updates(rows, eb)
    assert [u["projectIdentifier"] for u in updates] == ["KH - Test Project"]
    assert len(updates) == 1


# ---------------------------------------------------------------------------
# post_status_update dry-run safety
# ---------------------------------------------------------------------------

def test_post_dry_run_posts_nothing():
    payload = invoice_updates.build_paid_update(bw_row(), eb_entry())
    result = invoice_updates.post_status_update(payload, dry_run=True)
    assert result["posted"] is False
    assert result["dry_run"] is True
    assert result["payload"] == payload
