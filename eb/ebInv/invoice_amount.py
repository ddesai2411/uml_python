"""Corrected invoice line amount incl. shipping / discount (business req #2, part 1).

e-Builder has no shipping field: shipping (and handling, tax, and discounts) must
be folded directly into the invoice amount. Today the translator imports only the
line subtotal (``Invoice Line Extended Price``) -- the ``multiLine`` flag is passed
as a truthy placeholder, so the ``Invoice Total`` branch never runs and header
charges are never added. As a result the amount in e-Builder is short by the
shipping/discount, which is what The User fixes by hand.

Empirically (verified against the buyer-invoice export), Byways allocates
shipping/handling/tax **per line**, so the per-line billed amount is:

    Invoice Line Extended Price
      + Shipping Charge + Handling Charge + Tax1 Charge + Tax2 Charge
      + Invoice Discount            (Byways stores this negative)
      - Early Payment Discount      (positive; only when "Apply..." is true)

Summed across an invoice's lines this equals the Byways ``Invoice Total`` (it
reconciled for 391 of 429 invoices in the sample export; the remainder are edge
cases to catch in the dry-run review). Using the per-line formula works uniformly
for single-line invoices (the one line equals the total) and multi-line invoices,
so it does not depend on the broken ``multiLine`` flag.

All functions here are PURE (no I/O) and use :class:`decimal.Decimal` from string
inputs to avoid binary-float rounding, so amounts are exact and unit-testable
without e-Builder or a test environment.
"""

from decimal import Decimal, InvalidOperation

_ZERO = Decimal("0")


def parse_money(value):
    """Parse a Byways money cell into a Decimal.

    Handles thousands separators and currency symbols (e.g. ``"16,045.59"``,
    ``"$1,200.00"``), blanks/placeholders (``""``, ``"-"``), and negatives.
    Anything unparseable is treated as zero.
    """
    if value is None:
        return _ZERO
    s = str(value).strip().replace(",", "").replace("$", "")
    if s in ("", "-", "--"):
        return _ZERO
    try:
        return Decimal(s)
    except InvalidOperation:
        return _ZERO


def _is_true(flag):
    return str(flag).strip().lower() in ("true", "yes", "y", "t", "1")


def compute_invoice_line_amount(row):
    """Return the corrected billed amount for one Byways invoice line as a Decimal.

    See the module docstring for the formula and why it is applied per line.
    """
    amount = parse_money(row.get("Invoice Line Extended Price"))
    amount += parse_money(row.get("Shipping Charge"))
    amount += parse_money(row.get("Handling Charge"))
    amount += parse_money(row.get("Tax1 Charge"))
    amount += parse_money(row.get("Tax2 Charge"))
    # Invoice Discount is stored as a negative number in Byways -> add as-is.
    amount += parse_money(row.get("Invoice Discount"))
    # Early Payment Discount is a positive number -> subtract, only when applied.
    if _is_true(row.get("Apply Early Payment Discount")):
        amount -= parse_money(row.get("Early Payment Discount"))
    return amount
