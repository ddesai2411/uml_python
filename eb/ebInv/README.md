# Byways → e-Builder invoice automation (branch `invoice-paid-status`)

This branch automates two manual steps in the Byways → e-Builder invoice flow, plus
a supporting commitment change order. Everything is gated behind a **dry run** so
nothing reaches e-Builder until it has been reviewed.

## What it does

| # | Business requirement | Where |
| - | -------------------- | ----- |
| 1 | **Payable → Paid**: when Byways flips an already-imported invoice from Payable to Paid, update its e-Builder status to Paid | [`invoice_updates.py`](invoice_updates.py) |
| 2 | **Shipping/discount amount**: fold shipping, handling, tax, and discounts into the imported invoice amount (e-Builder has no shipping field) | [`invoice_amount.py`](invoice_amount.py), wired in [`write_Invoice_Cost_line.py`](write_Invoice_Cost_line.py) |
| 3 | **Commitment change order**: when an invoice's billed total exceeds its commitment (e.g. shipping pushed it over the PO), raise the commitment by the difference | [`../../CommitmentChangeOrders/co_builder.py`](../../CommitmentChangeOrders/co_builder.py) |

The entry point is `translate_Buyways_Invoices(theCSV, currStamp)` in
[`translate_BW_Invoices.py`](translate_BW_Invoices.py), called by `bw2eb/bw2eb.py`.

## Safety model (there is no test environment)

Because there is no sandbox, correctness is guarded two ways:

1. **Unit tests** cover every business rule (see the traceability matrix below). The
   decision/build logic is pure (no network/config), so it is fully testable.
2. **Dry run** is the default. The three posters (`post_invoice_update`,
   `post_commitment_co`, and the invoice cost import) log exactly what they *would*
   send to e-Builder and post nothing until `"dry_run": false` is set in
   `config.ebuilder.json`.

The e-Builder **write endpoints are built blind** from the API docs (no sandbox to
verify them). Each POST is isolated in a single `post_*` function so a wrong
endpoint/payload is a one-line fix. The user's first live run is the real integration
test — do it on a small, reviewed batch.

## Setup

The committed `env/` virtualenv is broken on some machines (it points at a Python
that may not exist). Create a fresh one with uv:

```bash
cd C:/git/UMASS/uml_python
uv venv .venv
uv pip install --python .venv/Scripts/python.exe pytest
```

## Configuration

`config.ebuilder.json` is **not committed** (it holds the API password). Copy the
template and fill it in:

```bash
cp config.ebuilder.example.json config.ebuilder.json
```

Keys: `hostname`, `username`, `password`, `data_cache_dir`, `daily_imports_dir`, and
`dry_run` (defaults to `true` when absent).

## Run the tests

```bash
.venv/Scripts/python.exe -m pytest -v
```

## Use it against a Byways export (dry run first)

1. Keep `"dry_run": true` in `config.ebuilder.json`.
2. Run the invoice flow over a Byways invoice CSV (via `bw2eb` or by calling
   `translate_Buyways_Invoices`). Review the `[DRY RUN] ...` lines: each Payable→Paid
   update, each corrected invoice amount, and each queued commitment change order.
3. Cross-check a few against known invoices (e.g. a shipping case where the voucher
   exceeds the PO).
4. Only then set `"dry_run": false` and run a small live batch, confirming in
   e-Builder that statuses flip to Paid and commitments are raised as expected.

## Requirement → test traceability

| Requirement | Tests |
| ----------- | ----- |
| #1 Payable→Paid detection, payload, dedup, dry-run | [`tests/test_paid_status.py`](../../tests/test_paid_status.py) |
| #2 Shipping/discount amount, money parsing, multi-line reconciliation | [`tests/test_invoice_amount.py`](../../tests/test_invoice_amount.py) |
| #3 Commitment change order delta/threshold, payloads, both workflows, dry-run | [`tests/test_commitment_co.py`](../../tests/test_commitment_co.py) |
| Config dry-run safety default | [`tests/test_config.py`](../../tests/test_config.py) |

## Known caveats

- **Amount reconciliation:** the per-line amount formula reconciled to Byways
  `Invoice Total` for 391 of 429 invoices in the sample export. The ~9% that don't are
  edge cases to catch in the dry-run review.
- **`Invoice Discount`** was zero across the sample export; the negative-discount path
  is coded to the stated convention but is unproven on real data.
- **CO-after-invoice follow-up line** (`<invoice>-1`) is built and tested but not yet
  wired into the already-in-EB branch; the CO-before-invoice path is wired.
- **Secret in history:** `config.ebuilder.json` was tracked previously, so its password
  is still in git history. It is now untracked and ignored — rotate the API key.
