"""Business requirement #2 (part 2): commitment change order generation.

Exercises the pure decision/build logic in ``CommitmentChangeOrders.co_builder``.
No network/config. The CO is applied via POST /api/v2/CommitmentChanges/Import and
the <invoice>-1 follow-up line via POST /api/v2/Invoices/Import; payload fields come
from the EB commitment record (native commitmentNumber, project, item numbers).

Run: .venv/Scripts/python.exe -m pytest tests/test_commitment_co.py -v
"""

from decimal import Decimal

from CommitmentChangeOrders import co_builder


# An entry as ebAPI.get_commitments_for_change() returns it.
CO_ENTRY = {
    "CommitmentNumber": "KHT09494",       # EB native number
    "ProjectName": "KH - Test Project",
    "ItemNumbers": ["001"],
    "Value": "8439.60",
    "CommitmentID": "PO-12345",
}


# ---------------------------------------------------------------------------
# commitment_delta / needs_change_order
# ---------------------------------------------------------------------------

def test_delta_is_billed_minus_commitment():
    assert co_builder.commitment_delta("8606.48", "8439.60") == Decimal("166.88")


def test_needs_co_when_billed_exceeds_commitment():
    assert co_builder.needs_change_order("8606.48", "8439.60") is True


def test_no_co_when_billed_equals_commitment():
    assert co_builder.needs_change_order("8439.60", "8439.60") is False


def test_no_co_when_billed_below_commitment():
    assert co_builder.needs_change_order("5000.00", "8439.60") is False


def test_no_co_within_tolerance():
    assert co_builder.needs_change_order("8439.61", "8439.60") is False


def test_co_just_over_tolerance():
    assert co_builder.needs_change_order("8439.62", "8439.60") is True


def test_no_co_when_commitment_missing_or_zero():
    assert co_builder.needs_change_order("100.00", "0") is False
    assert co_builder.needs_change_order("100.00", "") is False
    assert co_builder.needs_change_order("100.00", None) is False


def test_thousands_formatted_amounts():
    assert co_builder.needs_change_order("16,145.59", "16,045.59") is True
    assert co_builder.commitment_delta("16,145.59", "16,045.59") == Decimal("100.00")


# ---------------------------------------------------------------------------
# build_commitment_co -> CommitmentChanges/Import row
# ---------------------------------------------------------------------------

def test_build_co_payload_fields():
    co = co_builder.build_commitment_co(CO_ENTRY, Decimal("166.88"), "X3321427")
    hdr = co["header"]
    assert hdr["projectIdentifier"] == "KH - Test Project"
    assert hdr["commitmentNumber"] == "KHT09494"        # EB native, not the Buyways PO No
    assert hdr["commitmentChangeNumber"] == "BW-X3321427"
    assert hdr["reasonCode"] == co_builder.get_co_reason_code()
    assert hdr["dateofChange"]                          # a date was set
    assert "X3321427" in hdr["description"]
    item = co["items"][0]
    assert item["commitmentItemNumber"] == "001"
    assert item["amount"] == 166.88


def test_build_co_item_defaults_to_001_when_no_items():
    co = co_builder.build_commitment_co({"CommitmentNumber": "L1", "ItemNumbers": []},
                                        Decimal("50.00"), "X1")
    assert co["items"][0]["commitmentItemNumber"] == "001"
    assert co["items"][0]["amount"] == 50.0


# ---------------------------------------------------------------------------
# follow-up cost line (CO-after-invoice workflow) -> Invoices/Import row
# ---------------------------------------------------------------------------

def test_followup_invoice_number_suffix():
    assert co_builder.followup_cost_line_invoice_number("X3321427") == "X3321427-1"


def test_build_followup_cost_line():
    line = co_builder.build_followup_cost_line(CO_ENTRY, Decimal("166.88"), "X3321427")
    assert line["header"]["invoiceNumber"] == "X3321427-1"
    assert line["header"]["commitmentNumber"] == "KHT09494"
    assert line["items"][0]["amount"] == 166.88
    assert line["items"][0]["amountThisPeriod"] == 166.88


# ---------------------------------------------------------------------------
# plan_commitment_change (both workflows)
# ---------------------------------------------------------------------------

def test_plan_no_co_needed():
    plan = co_builder.plan_commitment_change("8000.00", "8439.60", CO_ENTRY, "X1")
    assert plan["needs_co"] is False
    assert plan["co"] is None
    assert plan["followup_line"] is None


def test_plan_co_before_invoice_has_no_followup_line():
    plan = co_builder.plan_commitment_change(
        "8606.48", "8439.60", CO_ENTRY, "X3321427", invoice_already_in_eb=False)
    assert plan["needs_co"] is True
    assert plan["delta"] == Decimal("166.88")
    assert plan["co"]["items"][0]["amount"] == 166.88
    assert plan["followup_line"] is None


def test_plan_co_after_invoice_includes_followup_line():
    plan = co_builder.plan_commitment_change(
        "8606.48", "8439.60", CO_ENTRY, "X3321427", invoice_already_in_eb=True)
    assert plan["needs_co"] is True
    assert plan["followup_line"]["header"]["invoiceNumber"] == "X3321427-1"
    assert plan["followup_line"]["items"][0]["amount"] == 166.88


# ---------------------------------------------------------------------------
# dry-run safety
# ---------------------------------------------------------------------------

def test_post_dry_run_posts_nothing():
    co = co_builder.build_commitment_co(CO_ENTRY, Decimal("10.00"), "X1")
    result = co_builder.post_commitment_co(co, dry_run=True)
    assert result["posted"] is False
    assert result["dry_run"] is True
    assert result["payload"] == co


def test_post_followup_cost_line_dry_run_posts_nothing():
    line = co_builder.build_followup_cost_line(CO_ENTRY, Decimal("10.00"), "X1")
    result = co_builder.post_followup_cost_line(line, dry_run=True)
    assert result["posted"] is False
    assert result["dry_run"] is True
    assert result["payload"] == line
