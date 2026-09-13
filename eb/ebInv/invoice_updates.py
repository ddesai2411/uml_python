"""Payable -> Paid invoice status updates (business requirement #1).

Byways brings invoices into e-Builder while their status is "Payable" (imported
to e-Builder as "Approved"). When Byways later flips the SAME invoice to "Paid",
the existing translator skips it as already-in-EB, so today The User changes the
e-Builder status by hand. This module decides which already-imported invoices now
need to move to Paid and builds the update payload for each.

Design for a no-test-environment world:
- ``should_update_to_paid``, ``build_paid_update`` and ``collect_paid_updates``
  are PURE (no I/O), so every business rule is unit-testable without e-Builder,
  a network, or a sandbox.
- ``post_invoice_update`` is the only side-effecting function. It defaults to a
  dry run (logs the payload, posts nothing) so nothing reaches production without
  an explicit opt-in. Because there is no sandbox to validate against, the real
  POST endpoint is isolated in this one function -- a wrong URL/shape is a
  one-line fix, not a rework.
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

    ``eb_invoices`` is the dict from ``ebAPI.get_Invoices_dict()``:
    ``{voucher_id: {"Status": <eb status>, ...}}``.
    """
    invoice_no = bw_row.get("Invoice No")
    if not invoice_no or invoice_no not in eb_invoices:
        return False
    eb_status = eb_invoices[invoice_no].get("Status")
    bw_status = bw_row.get("Invoice Status")
    return eb_status == EB_STATUS_APPROVED and bw_status == BW_STATUS_PAID


def build_paid_update(bw_row, fmp):
    """Build the Paid-update payload for one invoice.

    Keys mirror ``uml_lib.ebCostLib.updateInvoiceHeaders`` so the payload lines
    up with the e-Builder invoice-update contract. ``fmp`` is supplied by the
    caller (looked up from the PO, same as the cost-import path does), keeping
    this function pure.
    """
    # get_active_Projects stores the FMP as utf-8 bytes; decode so the payload is
    # JSON-serializable (json.dumps cannot serialize bytes) for the live POST.
    if isinstance(fmp, bytes):
        fmp = fmp.decode("utf-8", "replace")
    return {
        "FMP Number": fmp,
        "Status": EB_STATUS_PAID,
        "Invoice Number": bw_row.get("Invoice No"),
        "Company Name": bw_row.get("Supplier Name", ""),
        "Company Number": bw_row.get("Supplier Number", ""),
        "Date Paid": bw_row.get("Paid Date", ""),
    }


def collect_paid_updates(rows, eb_invoices, fmp_lookup=None):
    """Scan Byways rows and return one Paid-update payload per invoice that
    transitioned Payable -> Paid.

    Multi-line invoices repeat across rows; each invoice yields at most one
    update. ``fmp_lookup`` maps ``PO No`` -> FMP number; when a row's PO is not
    present, the row's own ``FMP Number`` column is used as a fallback.
    """
    fmp_lookup = fmp_lookup or {}
    updates = []
    seen = set()
    for r in rows:
        if not should_update_to_paid(r, eb_invoices):
            continue
        invoice_no = r.get("Invoice No")
        if invoice_no in seen:
            continue
        seen.add(invoice_no)
        fmp = fmp_lookup.get(r.get("PO No"), r.get("FMP Number", ""))
        updates.append(build_paid_update(r, fmp))
    return updates


def post_invoice_update(payload, dry_run=True):
    """Send one Paid update to e-Builder.

    Defaults to ``dry_run``: no network call, just returns the payload it *would*
    post. With ``dry_run=False`` it POSTs to the e-Builder API.

    NOTE: there is no sandbox, so the endpoint/shape below is built blind from
    the e-Builder docs and is unverified until The User's first live run. Keep
    the POST isolated here.
    """
    if dry_run:
        print("[DRY RUN] invoice paid-update:", payload)
        return {"dry_run": True, "posted": False, "payload": payload}

    # Lazy import so the pure functions above stay import-light and hermetic
    # for unit tests (no network/config dependency).
    import uml_lib.ebAPI_lib as ebAPI

    hostname = str(getattr(ebAPI.get_config(), "hostname", "")).rstrip("/")
    url = f"{hostname}/api/v2/invoices/update"  # unverified endpoint (no sandbox)
    response = ebAPI.postTOAPI(url, payload)
    return {"dry_run": False, "posted": True, "payload": payload, "response": response}
