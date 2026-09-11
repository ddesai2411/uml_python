"""Commitment change order (CO) generation (business requirement #2, part 2).

When an invoice's billed total exceeds its commitment (typically because shipping
pushed it over the PO amount), e-Builder requires a commitment change order to
raise the commitment by the difference before the invoice can sit against it.
Today The User does this by hand. This module decides when a CO is needed and
builds the payload.

Two workflows The User described are both supported:

1. CO before the invoice: the invoice has not been imported yet. Raise the
   commitment by the delta, then the invoice imports at its full (corrected)
   amount -- see eb/ebInv/invoice_amount.py.
2. CO after the invoice: the invoice was already imported at the pre-shipping
   amount and Byways added shipping later. Raise the commitment AND add a second
   actual-cost line whose invoice number is ``<invoice>-1`` for the delta.

Decision/build functions are PURE (no I/O) and use Decimal, so every rule is
unit-testable without e-Builder or a test environment. ``post_commitment_co`` is
the only side-effecting function; it defaults to a dry run and isolates the
(unverified, no-sandbox) POST endpoint in one place.
"""

from decimal import Decimal

from eb.ebInv.invoice_amount import parse_money

_ZERO = Decimal("0")
DEFAULT_TOLERANCE = Decimal("0.01")


def _amt(value):
    """Coerce Decimal / str / float / None to Decimal (via parse_money)."""
    if isinstance(value, Decimal):
        return value
    return parse_money(value)


def commitment_delta(billed_total, commitment_amount):
    """billed - commitment. Positive means the commitment must be raised."""
    return _amt(billed_total) - _amt(commitment_amount)


def needs_change_order(billed_total, commitment_amount, tolerance=DEFAULT_TOLERANCE):
    """True when billed exceeds commitment beyond ``tolerance``.

    A commitment of zero/negative is treated as missing data (no CO) to avoid a
    false positive when the PO's current value is unavailable.
    """
    commitment = _amt(commitment_amount)
    if commitment <= _ZERO:
        return False
    return commitment_delta(billed_total, commitment) > _amt(tolerance)


def followup_cost_line_invoice_number(invoice_no):
    """The second actual-cost line reuses the invoice number with a ``-1`` suffix."""
    return f"{invoice_no}-1"


def build_commitment_co(po_no, po_info, delta, invoice_no, commitment_amount=None):
    """Build the CO payload that raises a commitment by ``delta``.

    ``po_info`` is an entry from ``ebAPI.get_activePOs`` (keys: FMP, Value,
    Vendor, PO_ID, CommitmentType, Description).
    """
    po_info = po_info or {}
    delta = _amt(delta)
    co = {
        "Commitment Number": po_no,
        "Commitment ID": po_info.get("PO_ID"),
        "FMP Number": po_info.get("FMP"),
        "Company Name": po_info.get("Vendor"),
        "Change Amount": str(delta),
        "Description": f"Shipping/discount adjustment for invoice {invoice_no}",
        "Source Invoice": invoice_no,
    }
    if commitment_amount is not None:
        co["New Commitment Amount"] = str(_amt(commitment_amount) + delta)
    return co


def build_followup_cost_line(po_no, po_info, delta, invoice_no):
    """Build the ``<invoice>-1`` actual-cost line for the CO-after-invoice flow."""
    po_info = po_info or {}
    return {
        "FMP Number": po_info.get("FMP"),
        "Invoice Number": followup_cost_line_invoice_number(invoice_no),
        "Commitment Number": po_no,
        "Invoice Item Amount": str(_amt(delta)),
        "Description": f"Shipping/discount for invoice {invoice_no}",
    }


def plan_commitment_change(billed_total, commitment_amount, po_no, po_info,
                           invoice_no, invoice_already_in_eb=False,
                           tolerance=DEFAULT_TOLERANCE):
    """Decide what (if anything) to do for one invoice/commitment.

    Returns a dict:
      ``needs_co``  bool
      ``delta``     Decimal (billed - commitment)
      ``co``        CO payload or None
      ``followup_line``  the ``<invoice>-1`` cost line, or None (only for the
                         CO-after-invoice workflow)
    """
    delta = commitment_delta(billed_total, commitment_amount)
    if not needs_change_order(billed_total, commitment_amount, tolerance):
        return {"needs_co": False, "delta": delta, "co": None, "followup_line": None}
    co = build_commitment_co(po_no, po_info, delta, invoice_no, commitment_amount)
    followup = (
        build_followup_cost_line(po_no, po_info, delta, invoice_no)
        if invoice_already_in_eb else None
    )
    return {"needs_co": True, "delta": delta, "co": co, "followup_line": followup}


def post_commitment_co(payload, dry_run=True):
    """Create the CO in e-Builder. Defaults to dry_run (logs, posts nothing).

    NOTE: no sandbox -- the endpoint/shape is built blind from the e-Builder docs
    and the noncostProcesses pattern in commitmentChangeOrders.py, and is
    unverified until The User's first live run. Keep the POST isolated here.
    """
    if dry_run:
        print("[DRY RUN] commitment change order:", payload)
        return {"dry_run": True, "posted": False, "payload": payload}

    import uml_lib.ebAPI_lib as ebAPI

    hostname = str(getattr(ebAPI.get_config(), "hostname", "")).rstrip("/")
    url = f"{hostname}/api/v2/noncostProcesses?processprefix=CO"  # unverified (no sandbox)
    response = ebAPI.postTOAPI(url, payload)
    return {"dry_run": False, "posted": True, "payload": payload, "response": response}


def post_followup_cost_line(payload, dry_run=True):
    """Post the ``<invoice>-1`` actual-cost line for the CO-after-invoice workflow.

    Defaults to dry_run (logs, posts nothing). Same no-sandbox caveat as
    ``post_commitment_co``: the endpoint is unverified and isolated here.
    """
    if dry_run:
        print("[DRY RUN] follow-up cost line:", payload)
        return {"dry_run": True, "posted": False, "payload": payload}

    import uml_lib.ebAPI_lib as ebAPI

    hostname = str(getattr(ebAPI.get_config(), "hostname", "")).rstrip("/")
    url = f"{hostname}/api/v2/invoices/cost"  # unverified (no sandbox)
    response = ebAPI.postTOAPI(url, payload)
    return {"dry_run": False, "posted": True, "payload": payload, "response": response}
