"""Business requirement #2 (part 2): commitment change order generation.

Exercises the pure decision/build logic in ``CommitmentChangeOrders.co_builder``.
No network/config -- this is how the CO rules are validated without a test
environment.

Run: .venv/Scripts/python.exe -m pytest tests/test_commitment_co.py -v
"""

from decimal import Decimal

from CommitmentChangeOrders import co_builder


PO_INFO = {
    "FMP": "301105",
    "Value": "8439.60",
    "Vendor": "Acme Supply",
    "PO_ID": "PO-12345",
    "CommitmentType": "1",
    "Description": "Generator parts",
}


# ---------------------------------------------------------------------------
# commitment_delta / needs_change_order
# ---------------------------------------------------------------------------

def test_delta_is_billed_minus_commitment():
    # transcript example: PO 8439.60, billed exceeds it by shipping
    assert co_builder.commitment_delta("8606.48", "8439.60") == Decimal("166.88")


def test_needs_co_when_billed_exceeds_commitment():
    assert co_builder.needs_change_order("8606.48", "8439.60") is True


def test_no_co_when_billed_equals_commitment():
    assert co_builder.needs_change_order("8439.60", "8439.60") is False


def test_no_co_when_billed_below_commitment():
    # partial invoice / discount below commitment -> no CO
    assert co_builder.needs_change_order("5000.00", "8439.60") is False


def test_no_co_within_tolerance():
    # a penny over is treated as rounding, not a real change
    assert co_builder.needs_change_order("8439.61", "8439.60") is False


def test_co_just_over_tolerance():
    assert co_builder.needs_change_order("8439.62", "8439.60") is True


def test_no_co_when_commitment_missing_or_zero():
    # zero/blank commitment is treated as missing data, not "everything exceeds it"
    assert co_builder.needs_change_order("100.00", "0") is False
    assert co_builder.needs_change_order("100.00", "") is False
    assert co_builder.needs_change_order("100.00", None) is False


def test_thousands_formatted_amounts():
    assert co_builder.needs_change_order("16,145.59", "16,045.59") is True
    assert co_builder.commitment_delta("16,145.59", "16,045.59") == Decimal("100.00")


# ---------------------------------------------------------------------------
# build_commitment_co
# ---------------------------------------------------------------------------

def test_build_co_payload_fields():
    co = co_builder.build_commitment_co(
        "L001939576", PO_INFO, Decimal("166.88"), "X3321427", commitment_amount="8439.60"
    )
    assert co["Commitment Number"] == "L001939576"
    assert co["Commitment ID"] == "PO-12345"
    assert co["FMP Number"] == "301105"
    assert co["Company Name"] == "Acme Supply"
    assert co["Change Amount"] == "166.88"
    assert co["New Commitment Amount"] == "8606.48"
    assert co["Source Invoice"] == "X3321427"
    assert "X3321427" in co["Description"]


def test_build_co_without_commitment_amount_omits_new_total():
    co = co_builder.build_commitment_co("L1", PO_INFO, Decimal("50.00"), "X1")
    assert "New Commitment Amount" not in co
    assert co["Change Amount"] == "50.00"


# ---------------------------------------------------------------------------
# follow-up cost line (CO-after-invoice workflow)
# ---------------------------------------------------------------------------

def test_followup_invoice_number_suffix():
    assert co_builder.followup_cost_line_invoice_number("X3321427") == "X3321427-1"


def test_build_followup_cost_line():
    line = co_builder.build_followup_cost_line("L001939576", PO_INFO, Decimal("166.88"), "X3321427")
    assert line["Invoice Number"] == "X3321427-1"
    assert line["Commitment Number"] == "L001939576"
    assert line["Invoice Item Amount"] == "166.88"
    assert line["FMP Number"] == "301105"


# ---------------------------------------------------------------------------
# plan_commitment_change (ties it together, both workflows)
# ---------------------------------------------------------------------------

def test_plan_no_co_needed():
    plan = co_builder.plan_commitment_change("8000.00", "8439.60", "L1", PO_INFO, "X1")
    assert plan["needs_co"] is False
    assert plan["co"] is None
    assert plan["followup_line"] is None


def test_plan_co_before_invoice_has_no_followup_line():
    plan = co_builder.plan_commitment_change(
        "8606.48", "8439.60", "L001939576", PO_INFO, "X3321427",
        invoice_already_in_eb=False,
    )
    assert plan["needs_co"] is True
    assert plan["delta"] == Decimal("166.88")
    assert plan["co"]["Change Amount"] == "166.88"
    assert plan["followup_line"] is None


def test_plan_co_after_invoice_includes_followup_line():
    plan = co_builder.plan_commitment_change(
        "8606.48", "8439.60", "L001939576", PO_INFO, "X3321427",
        invoice_already_in_eb=True,
    )
    assert plan["needs_co"] is True
    assert plan["followup_line"]["Invoice Number"] == "X3321427-1"
    assert plan["followup_line"]["Invoice Item Amount"] == "166.88"


# ---------------------------------------------------------------------------
# post_commitment_co dry-run safety
# ---------------------------------------------------------------------------

def test_post_dry_run_posts_nothing():
    co = co_builder.build_commitment_co("L1", PO_INFO, Decimal("10.00"), "X1")
    result = co_builder.post_commitment_co(co, dry_run=True)
    assert result["posted"] is False
    assert result["dry_run"] is True
    assert result["payload"] == co


def test_post_followup_cost_line_dry_run_posts_nothing():
    line = co_builder.build_followup_cost_line("L1", PO_INFO, Decimal("10.00"), "X1")
    result = co_builder.post_followup_cost_line(line, dry_run=True)
    assert result["posted"] is False
    assert result["dry_run"] is True
    assert result["payload"] == line
