"""Business requirement #2 (part 1): shipping/discount folded into invoice amount.

Exercises the pure amount logic in ``eb.ebInv.invoice_amount``. Several cases use
real values from the buyer-invoice export so the arithmetic is anchored to
production data (see the reconciliation done during design). No network/config.

Run: .venv/Scripts/python.exe -m pytest tests/test_invoice_amount.py -v
"""

from decimal import Decimal

from eb.ebInv import invoice_amount
from eb.ebInv.invoice_amount import parse_money, compute_invoice_line_amount


def line(**overrides):
    """A minimal invoice line with all charge fields zeroed; override per test."""
    row = {
        "Invoice Line Extended Price": "0",
        "Shipping Charge": "0",
        "Handling Charge": "0",
        "Tax1 Charge": "0",
        "Tax2 Charge": "0",
        "Invoice Discount": "0",
        "Early Payment Discount": "0",
        "Apply Early Payment Discount": "false",
    }
    row.update(overrides)
    return row


# ---------------------------------------------------------------------------
# parse_money
# ---------------------------------------------------------------------------

def test_parse_plain_number():
    assert parse_money("284.36") == Decimal("284.36")


def test_parse_thousands_separator():
    assert parse_money("16,045.59") == Decimal("16045.59")


def test_parse_currency_symbol_and_thousands():
    assert parse_money("$1,200.00") == Decimal("1200.00")


def test_parse_negative():
    assert parse_money("-12.50") == Decimal("-12.50")


def test_parse_blank_dash_none_are_zero():
    assert parse_money("") == Decimal("0")
    assert parse_money("-") == Decimal("0")
    assert parse_money(None) == Decimal("0")


def test_parse_garbage_is_zero():
    assert parse_money("N/A") == Decimal("0")


# ---------------------------------------------------------------------------
# compute_invoice_line_amount
# ---------------------------------------------------------------------------

def test_no_charges_is_just_subtotal():
    assert compute_invoice_line_amount(line(**{"Invoice Line Extended Price": "100.00"})) == Decimal("100.00")


def test_shipping_only_real_row_X3321395():
    # ext 269.97 + ship 14.39 = 284.36 (Invoice Total in the export)
    row = line(**{"Invoice Line Extended Price": "269.97", "Shipping Charge": "14.39"})
    assert compute_invoice_line_amount(row) == Decimal("284.36")


def test_shipping_plus_handling_real_row_X3321426():
    # ext 562.00 + ship 15.00 + handling 11.24 = 588.24
    row = line(**{"Invoice Line Extended Price": "562.00", "Shipping Charge": "15.00", "Handling Charge": "11.24"})
    assert compute_invoice_line_amount(row) == Decimal("588.24")


def test_early_payment_discount_applied_real_row_X3320541():
    # ext 77.48 + ship 10.83 - earlyDiscount 1.55 = 86.76
    row = line(**{
        "Invoice Line Extended Price": "77.48",
        "Shipping Charge": "10.83",
        "Early Payment Discount": "1.55",
        "Apply Early Payment Discount": "true",
    })
    assert compute_invoice_line_amount(row) == Decimal("86.76")


def test_early_payment_discount_not_applied_is_ignored():
    row = line(**{
        "Invoice Line Extended Price": "77.48",
        "Shipping Charge": "10.83",
        "Early Payment Discount": "1.55",
        "Apply Early Payment Discount": "false",
    })
    assert compute_invoice_line_amount(row) == Decimal("88.31")


def test_negative_invoice_discount_reduces_amount():
    # Byways stores Invoice Discount negative; adding it reduces the total.
    row = line(**{"Invoice Line Extended Price": "100.00", "Invoice Discount": "-10.00"})
    assert compute_invoice_line_amount(row) == Decimal("90.00")


def test_taxes_are_added():
    row = line(**{"Invoice Line Extended Price": "100.00", "Tax1 Charge": "5.00", "Tax2 Charge": "2.50"})
    assert compute_invoice_line_amount(row) == Decimal("107.50")


def test_multiline_lines_sum_to_invoice_total_X3321423():
    # Real 2-line invoice; per-line shipping differs. Sum must equal Invoice Total 213.69.
    l1 = line(**{"Invoice Line Extended Price": "94.00", "Shipping Charge": "20.30"})
    l2 = line(**{"Invoice Line Extended Price": "81.74", "Shipping Charge": "17.65"})
    total = compute_invoice_line_amount(l1) + compute_invoice_line_amount(l2)
    assert total == Decimal("213.69")


def test_thousands_formatted_subtotal():
    row = line(**{"Invoice Line Extended Price": "16,045.59", "Shipping Charge": "100.00"})
    assert compute_invoice_line_amount(row) == Decimal("16145.59")
