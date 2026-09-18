"""Commitment change order (CO) generation (business requirement #2, part 2).

When an invoice's billed total exceeds its commitment (typically because shipping
pushed it over the PO amount), the commitment must be raised before the invoice
can sit against it. Today The User does this by hand.

MECHANISM (confirmed live in the sandbox, 2026-09-13):
- Raise the commitment  -> POST /api/v2/CommitmentChanges/Import (the "Import
  Commitment Changes" batch process). Verified: a commitment went 55 -> 65.
- The <invoice>-1 follow-up cost line -> POST /api/v2/Invoices/Import (a cost
  invoice import; verified it books the amount as an actual).

Both match on the e-Builder NATIVE commitment number (not the Buyways PO No), so
the payload fields come from ebAPI.get_commitments_for_change() keyed by the
Buyways PO No.

Two workflows are supported:
1. CO before the invoice: raise the commitment by the delta; the invoice then
   imports at its full (corrected) amount (see eb/ebInv/invoice_amount.py).
2. CO after the invoice: the invoice was imported at the pre-shipping amount and
   Byways added shipping later. Raise the commitment AND add a <invoice>-1
   actual-cost line for the delta.

Decision/build functions are PURE (no I/O) and use Decimal. ``post_commitment_co``
and ``post_followup_cost_line`` are the only side-effecting functions; both
default to dry run.
"""

from datetime import date
from decimal import Decimal

from eb.ebInv.invoice_amount import parse_money

_ZERO = Decimal("0")
DEFAULT_TOLERANCE = Decimal("0.01")

# Commitment-change reason code fallback. Account-configured (Setup -> Cost ->
# Reason Codes -> Commitment Change). "Owner Directive" is a valid SANDBOX value.
# For production, set "co_reason_code" in config.ebuilder.json to UMass's valid value
# (this constant is only the fallback when the config key is absent).
CO_REASON_CODE = "Owner Directive"


def get_co_reason_code():
    """The commitment-change reason code: config.co_reason_code if set, else the
    CO_REASON_CODE fallback. Config is read lazily so the pure builders stay
    testable without a config file."""
    try:
        import uml_lib.ebAPI_lib as ebAPI
        cfg_val = getattr(ebAPI.get_config(), "co_reason_code", None)
        if cfg_val:
            return cfg_val
    except Exception:
        pass
    return CO_REASON_CODE


def _amt(value):
    """Coerce Decimal / str / float / None to Decimal (via parse_money)."""
    if isinstance(value, Decimal):
        return value
    return parse_money(value)


def _first_item(co_entry):
    """Commitment item number to hang the change/cost on (first item, else '001')."""
    items = (co_entry or {}).get("ItemNumbers") or []
    return items[0] if items else "001"


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


def build_commitment_co(co_entry, delta, invoice_no, change_date=None):
    """Build one /api/v2/CommitmentChanges/Import ``data`` row that raises the
    commitment by ``delta``.

    ``co_entry`` is an entry from ``ebAPI.get_commitments_for_change()``
    (CommitmentNumber (native), ProjectName, ItemNumbers, ...).
    """
    co_entry = co_entry or {}
    change_date = change_date or date.today().isoformat()
    return {
        "header": {
            "projectIdentifier": co_entry.get("ProjectName"),
            "commitmentNumber": co_entry.get("CommitmentNumber"),   # EB native number
            "commitmentChangeNumber": f"BW-{invoice_no}",           # unique per commitment
            "reasonCode": get_co_reason_code(),
            "dateofChange": change_date,
            "description": f"Shipping/discount adjustment for invoice {invoice_no}",
            "status": "Approved",
        },
        "items": [{
            "commitmentChangeItemNumber": "001",
            "commitmentItemNumber": _first_item(co_entry),
            "amount": float(_amt(delta)),
        }],
    }


def build_followup_cost_line(co_entry, delta, invoice_no):
    """Build the ``<invoice>-1`` actual-cost line (POST /api/v2/Invoices/Import)
    for the CO-after-invoice flow."""
    co_entry = co_entry or {}
    return {
        "header": {
            "projectIdentifier": co_entry.get("ProjectName"),
            "commitmentNumber": co_entry.get("CommitmentNumber"),
            "invoiceNumber": followup_cost_line_invoice_number(invoice_no),
            "description": f"Shipping/discount for invoice {invoice_no}",
        },
        "items": [{
            "commitmentItemNumber": _first_item(co_entry),
            "amount": float(_amt(delta)),
            "amountThisPeriod": float(_amt(delta)),
        }],
    }


def plan_commitment_change(billed_total, commitment_amount, co_entry, invoice_no,
                           invoice_already_in_eb=False, tolerance=DEFAULT_TOLERANCE):
    """Decide what (if anything) to do for one invoice/commitment.

    Returns a dict:
      ``needs_co``       bool
      ``delta``          Decimal (billed - commitment)
      ``co``             CommitmentChanges/Import payload or None
      ``followup_line``  the <invoice>-1 Invoices/Import payload, or None (only for
                         the CO-after-invoice workflow)
    """
    delta = commitment_delta(billed_total, commitment_amount)
    if not needs_change_order(billed_total, commitment_amount, tolerance):
        return {"needs_co": False, "delta": delta, "co": None, "followup_line": None}
    co = build_commitment_co(co_entry, delta, invoice_no)
    followup = (
        build_followup_cost_line(co_entry, delta, invoice_no)
        if invoice_already_in_eb else None
    )
    return {"needs_co": True, "delta": delta, "co": co, "followup_line": followup}


def post_commitment_co(payload, dry_run=True):
    """Raise the commitment via POST /api/v2/CommitmentChanges/Import.

    Defaults to ``dry_run`` (logs, posts nothing). ``payload`` is one data row
    (header + items) from :func:`build_commitment_co`.
    """
    if dry_run:
        print("[DRY RUN] commitment change order:", payload)
        return {"dry_run": True, "posted": False, "payload": payload}

    import uml_lib.ebAPI_lib as ebAPI

    hostname = str(getattr(ebAPI.get_config(), "hostname", "")).rstrip("/")
    url = f"{hostname}/api/v2/CommitmentChanges/Import"
    body = {"options": {"projectIdentifier": "ProjectName"}, "data": [payload]}
    response = ebAPI.postTOAPI(url, body)
    return {"dry_run": False, "posted": True, "payload": payload, "response": response}


def post_followup_cost_line(payload, dry_run=True):
    """Post the ``<invoice>-1`` actual-cost line via POST /api/v2/Invoices/Import.

    Defaults to ``dry_run`` (logs, posts nothing). ``payload`` is one data row
    (header + items) from :func:`build_followup_cost_line`.
    """
    if dry_run:
        print("[DRY RUN] follow-up cost line:", payload)
        return {"dry_run": True, "posted": False, "payload": payload}

    import uml_lib.ebAPI_lib as ebAPI

    hostname = str(getattr(ebAPI.get_config(), "hostname", "")).rstrip("/")
    url = f"{hostname}/api/v2/Invoices/Import"
    body = {"options": {"projectIdentifier": "ProjectName"}, "data": [payload]}
    response = ebAPI.postTOAPI(url, body)
    return {"dry_run": False, "posted": True, "payload": payload, "response": response}
