"""Self-contained DRY-RUN demo for the Byways -> e-Builder automation.

Runs THREE separate dry runs, one per task, each from its own CSV under
eb/ebInv/samples/. It needs NO e-Builder config, data cache, or network: the
reference-data reads are stubbed and dry-run is forced ON, so the real posters
print exactly what they WOULD send to e-Builder ([DRY RUN] lines) and post
nothing.

    Task 1  Payable -> Paid status update          demo_task1_payable_to_paid.csv
    Task 2  Shipping/discount folded into amount    demo_task2_shipping_discount.csv
    Task 3  Commitment change order (both flows)    demo_task3_change_orders.csv

Usage:
    .venv\\Scripts\\python.exe eb\\ebInv\\demo_dry_run.py
"""

import csv
import io
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

# Allow running directly (python eb\ebInv\demo_dry_run.py) by putting the project
# root on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eb.ebInv import translate_BW_Invoices as tr
from eb.ebInv import invoice_amount

SAMPLES = Path(__file__).resolve().parent / "samples"


def banner(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


@contextmanager
def stubbed(active_pos, in_eb, eb_status):
    """Temporarily replace e-Builder reference-data reads with stubs and force
    dry-run ON, then restore the originals."""
    stubs = {
        (tr.ebCost, "getBudgetTasks"): lambda: {},
        (tr.ebAPI, "get_FundingRules"): lambda: {},
        (tr.ebAPI, "get_active_Projects"): lambda: {},
        (tr.ebAPI, "get_activePOs"): lambda ebProjs: active_pos,
        (tr.ebAPI, "get_Invoices"): lambda: list(in_eb),
        (tr.ebAPI, "get_Invoices_dict"): lambda: eb_status,
        (tr.ebAPI, "get_daily_imports_dir"): lambda create=False: Path(tempfile.mkdtemp()),
        (tr.ebAPI, "get_dry_run"): lambda: True,
    }
    originals = {key: getattr(*key) for key in stubs}
    for (mod, name), fn in stubs.items():
        setattr(mod, name, fn)
    try:
        yield
    finally:
        for (mod, name), fn in originals.items():
            setattr(mod, name, fn)


def run_translator(csv_name, active_pos, in_eb, eb_status):
    """Run the real translator over a demo CSV in dry-run, and surface only the
    [DRY RUN] poster lines plus the run summary (internal debug noise hidden)."""
    csv_path = SAMPLES / csv_name
    tmpdir = tempfile.mkdtemp()
    cwd = os.getcwd()
    buf = io.StringIO()
    real_stdout = sys.stdout
    with stubbed(active_pos, in_eb, eb_status):
        os.chdir(tmpdir)  # ebInvoiceLog.txt is written to cwd
        try:
            sys.stdout = buf
            result = tr.translate_Buyways_Invoices(str(csv_path), "DEMO")
        finally:
            sys.stdout = real_stdout
            os.chdir(cwd)

    for line in buf.getvalue().splitlines():
        if line.startswith("[DRY RUN]"):
            print("   " + line)
    counts = result["Stats"]
    shown = [(k, counts[k]) for k in ("PaidUpdate", "ChangeOrder", "FollowupLine") if counts.get(k)]
    print("   ---")
    print("   Summary:", ", ".join(f"{k}={v}" for k, v in shown) or "no actions")


def demo_task1():
    banner("TASK 1 DRY RUN  -  Payable -> Paid status update")
    print("CSV: samples/demo_task1_payable_to_paid.csv  (real rows from your InvoiceData export)")
    print("Two invoices already in e-Builder (Approved) that Byways now shows as Paid.")
    print("Expect: one paid-update posted per invoice.\n")
    # Real PO numbers + real commitment totals (from your POData export). FMP/PO_ID
    # are e-Builder-internal lookups (not in the Byways export) so they're placeholders.
    active_pos = {
        "L001943891": {"FMP": "<from e-Builder PO>", "Value": "42.28", "Vendor": "AT&T CORPORATION",
                       "PO_ID": "EB-PO", "CommitmentType": "1", "Description": "phone"},
        "L001943736": {"FMP": "<from e-Builder PO>", "Value": "388.84", "Vendor": "FEDERAL EXPRESS CORPORATION",
                       "PO_ID": "EB-PO", "CommitmentType": "1", "Description": "shipping"},
    }
    run_translator(
        "demo_task1_payable_to_paid.csv",
        active_pos,
        in_eb=["X3320038", "X3319928"],
        eb_status={"X3320038": {"Status": "Approved"}, "X3319928": {"Status": "Approved"}},
    )


def demo_task2():
    banner("TASK 2 DRY RUN  -  Shipping/discount folded into the invoice amount")
    print("CSV: samples/demo_task2_shipping_discount.csv  (real rows from your InvoiceData export)")
    print("Old behavior imported the subtotal only. Now shipping/handling/tax/discount")
    print("are folded in. Below: subtotal -> corrected billed amount for each row.\n")
    with (SAMPLES / "demo_task2_shipping_discount.csv").open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            subtotal = invoice_amount.parse_money(r["Invoice Line Extended Price"])
            corrected = invoice_amount.compute_invoice_line_amount(r)
            note = []
            if invoice_amount.parse_money(r["Shipping Charge"]):
                note.append(f"ship {r['Shipping Charge']}")
            if invoice_amount.parse_money(r["Handling Charge"]):
                note.append(f"handling {r['Handling Charge']}")
            if invoice_amount.parse_money(r["Early Payment Discount"]) and r["Apply Early Payment Discount"].lower() == "true":
                note.append(f"-early {r['Early Payment Discount']}")
            if invoice_amount.parse_money(r["Invoice Discount"]):
                note.append(f"discount {r['Invoice Discount']}")
            print(f"   {r['Invoice No']}:  subtotal {subtotal:>9}  ->  corrected {corrected:>9}   ({', '.join(note)})")


def demo_task3():
    banner("TASK 3 DRY RUN  -  Commitment change order (both workflows)")
    print("CSV: samples/demo_task3_change_orders.csv  (real over-commitment rows from your exports)")
    print("X3321241: NEW invoice, billed 501.39 > PO commit 476.85  -> CO before the invoice.")
    print("X3320667: already in e-Builder, billed 139.40 > commit 113.24 -> CO after + <invoice>-1.")
    print("Expect: a CO for each, and an X3320667-1 follow-up cost line.\n")
    # Real PO numbers + real commitment totals (sum of PO Extended Price) from POData.
    active_pos = {
        "L001944466": {"FMP": "<from e-Builder PO>", "Value": "476.85", "Vendor": "SIGMA-ALDRICH INC",
                       "PO_ID": "EB-PO", "CommitmentType": "1", "Description": "hydrazine"},
        "L001942565": {"FMP": "<from e-Builder PO>", "Value": "113.24", "Vendor": "AIRGAS USA LLC",
                       "PO_ID": "EB-PO", "CommitmentType": "1", "Description": "nitrogen"},
    }
    run_translator(
        "demo_task3_change_orders.csv",
        active_pos,
        in_eb=["X3320667"],  # X3321241 is new; X3320667 already imported
        eb_status={"X3320667": {"Status": "Approved"}},
    )


if __name__ == "__main__":
    # Optional arg: 1, 2, or 3 to run a single task (for pacing the demo);
    # no arg runs all three.
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("DRY-RUN DEMO  -  nothing is posted to e-Builder; every action is logged only.")
    print("Invoice #, PO #, amounts, suppliers and dates are REAL rows from the exports.")
    print("FMP Number shows '<from e-Builder PO>' because FMP is looked up from the")
    print("e-Builder facilities PO in production, not carried in the Byways export.\n")
    if which in ("1", "all"):
        demo_task1()
    if which in ("2", "all"):
        demo_task2()
    if which in ("3", "all"):
        demo_task3()
    print("\nDry run complete. Nothing was posted.")
    print('To go live: set "dry_run": false in config.ebuilder.json and run a small batch first.')
