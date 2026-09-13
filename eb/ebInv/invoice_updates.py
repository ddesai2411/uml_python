"""Payable -> Paid invoice status updates (business requirement #1).

Byways brings invoices into e-Builder while their status is "Payable" (imported
to e-Builder as "Approved"). When Byways later flips the SAME invoice to "Paid",
the existing translator skips it as already-in-EB, so today The User records the
payment by hand in the e-Builder UI. This module decides which already-imported
invoices now need to move to Paid and builds the update for each.

MECHANISM (confirmed live in the sandbox, 2026-09-13):
"Paid" in e-Builder is a recorded PAYMENT (the commitment item's actualsPaid goes
from 0 to the invoice amount, and the invoice's datePaid is set). The only thing
that produces that on an EXISTING invoice is the "Update Invoice Status" batch
process, exposed as POST /api/v2/Invoices/StatusUpdate. It UPDATES the invoice
(no create/collision, no workflow process). The process/import-create endpoints
cannot set Paid.

The API matches on the e-Builder NATIVE invoice number (the Buyways Invoice No
lives in the "Voucher ID" custom field), so the payload fields come from the EB
invoice record (see ebAPI.get_Invoices_for_paid_update) plus the Byways Paid Date.

Design:
- ``should_update_to_paid``, ``build_paid_update`` and ``collect_paid_updates``
  are PURE (no I/O), unit-testable without e-Builder or a network.
- ``post_status_update`` is the only side-effecting function; it defaults to a
  dry run (logs, posts nothing) and isolates the POST in one place.
"""

# e-Builder (EB) side statuses
EB_STATUS_APPROVED = "Approved"
EB_STATUS_PAID = "Paid"
# Byways (BW / CSV) side statuses
BW_STATUS_PAID = "Paid"


def should_update_to_paid(bw_row, eb_invoices):
    """Return True when this Byways row is an already-imported invoice whose
    e-Builder status is still ``Approved`` but whose Byways status is now
    ``Paid``.

    ``eb_invoices`` is the dict from ``ebAPI.get_Invoices_for_paid_update()``,
    keyed by Buyways Invoice No (= EB "Voucher ID"); each entry has "Status".
    """
    invoice_no = bw_row.get("Invoice No")
    if not invoice_no or invoice_no not in eb_invoices:
        return False
    eb_status = eb_invoices[invoice_no].get("Status")
    bw_status = bw_row.get("Invoice Status")
    return eb_status == EB_STATUS_APPROVED and bw_status == BW_STATUS_PAID


def build_paid_update(bw_row, eb_entry):
    """Build one /api/v2/Invoices/StatusUpdate ``data`` row.

    Values come from the e-Builder invoice record (``eb_entry`` from
    ``get_Invoices_for_paid_update``: native InvoiceNumber, CompanyNumber, Amount,
    ProjectName) plus the Byways ``Paid Date``. Required by the endpoint:
    projectIdentifier, invoiceNumber, amountPaid, companyNumber.
    """
    return {
        "projectIdentifier": eb_entry.get("ProjectName"),
        "invoiceNumber": eb_entry.get("InvoiceNumber"),   # EB native number
        "amountPaid": eb_entry.get("Amount"),             # paid in full
        "companyNumber": eb_entry.get("CompanyNumber"),
        "commitmentNumber": eb_entry.get("CommitmentNumber"),  # optional, if provided
        "datePaid": bw_row.get("Paid Date", ""),
        "status": EB_STATUS_PAID,
    }


def collect_paid_updates(rows, eb_invoices):
    """Scan Byways rows and return one StatusUpdate payload per invoice that
    transitioned Payable -> Paid. Multi-line invoices repeat across rows; each
    invoice yields at most one update.
    """
    updates = []
    seen = set()
    for r in rows:
        if not should_update_to_paid(r, eb_invoices):
            continue
        invoice_no = r.get("Invoice No")
        if invoice_no in seen:
            continue
        seen.add(invoice_no)
        updates.append(build_paid_update(r, eb_invoices[invoice_no]))
    return updates


def post_status_update(payload, dry_run=True):
    """Record the payment / set the invoice Paid via POST /api/v2/Invoices/StatusUpdate.

    Defaults to ``dry_run``: no network call, just returns the payload it *would*
    post. With ``dry_run=False`` it POSTs. ``options.projectIdentifier="ProjectName"``
    tells e-Builder the row's ``projectIdentifier`` is the project name.
    """
    if dry_run:
        print("[DRY RUN] invoice StatusUpdate:", payload)
        return {"dry_run": True, "posted": False, "payload": payload}

    # Lazy import so the pure functions above stay import-light for unit tests.
    import uml_lib.ebAPI_lib as ebAPI

    hostname = str(getattr(ebAPI.get_config(), "hostname", "")).rstrip("/")
    url = f"{hostname}/api/v2/Invoices/StatusUpdate"
    body = {"options": {"projectIdentifier": "ProjectName"}, "data": [payload]}
    response = ebAPI.postTOAPI(url, body)
    return {"dry_run": False, "posted": True, "payload": payload, "response": response}
