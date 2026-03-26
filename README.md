# UML Python

Internal Python utilities for UMass Lowell Facilities workflows around e-Builder and Buyways.

This repository contains:
- a `tkinter` dashboard for running common workflows
- e-Builder API helpers
- Buyways CSV/XML translation utilities
- reporting scripts for monthly status, FMP, and time allocation
- cache/export helpers for JSON, Excel, HTML, and database loading

## Current state

This project has been updated to use consistent repo-root imports and now includes Python dependency files:
- `pyproject.toml`
- `requirements.txt`

There are still environment-specific paths in parts of the codebase, especially `B:\...` and some older `/Users/...` paths. That means some features still expect the original network/shared-drive layout unless those paths are reconfigured.

## Main entry point

The primary UI entry point is:
- `ebDashboard.py`

Run it from the repository root:
- `C:\git\UMASS\uml_python`

## What the dashboard does

`ebDashboard.py` provides buttons for the most common workflows:

- **Run ebData**
  - Pulls e-Builder data from the API and saves local JSON cache files
- **Run bw2eb**
  - Converts a selected Buyways CSV into e-Builder import output
- **Run bwebJoined**
  - Processes zipped Buyways report batches
- **Run bweb XML**
  - Processes Buyways XML files into Excel/HTML output
- **Run timeAlloc**
  - Builds time allocation reports from a selected CSV
- **Run ebFMP**
  - Builds an HTML FMP report
- **Run for Monthly Status**
  - Generates the monthly status report

## Important project structure

- `ebDashboard.py`
  - main desktop dashboard
- `uml_lib/ebAPI_lib.py`
  - e-Builder API access and local cache helpers
- `uml_lib/dailyDataImport.py`
  - downloads JSON cache files from e-Builder
- `bw2eb/`
  - Buyways import workflows
- `eb/ebPO/`
  - PO XML/translation logic
- `eb/ebInv/`
  - invoice XML/translation logic
- `sampleData/`
  - sample CSV/XML inputs for testing
- `ebDataToSQL/`
  - scripts for loading cached data into SQL systems

## Python environment setup

It is best to run this project in its own virtual environment.

### PowerShell steps

From the repo root:

1. Create a virtual environment:
   - `python -m venv .venv`

2. Activate it in PowerShell:
   - `.\.venv\Scripts\Activate.ps1`

3. Upgrade `pip`:
   - `python -m pip install --upgrade pip`

4. Install dependencies:
   - `python -m pip install -r requirements.txt`

Optional:
- install the project metadata package too:
  - `python -m pip install .`

### If PowerShell blocks activation

If activation is blocked by execution policy, you can either:
- run PowerShell as allowed by your environment policy, or
- use a one-time process-scope policy change:
  - `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

Then activate again:
- `.\.venv\Scripts\Activate.ps1`

## Configuration

The e-Builder API config file is expected at:
- `config.ebuilder.json`

Place it in the repo root:
- `C:\git\UMASS\uml_python\config.ebuilder.json`

Example:

```json
{
  "hostname": "https://your-ebuilder-host",
  "username": "your-username",
  "password": "your-password",
  "data_cache_dir": "C:\\git\\UMASS\\uml_python\\data\\ebData",
  "daily_imports_dir": "C:\\git\\UMASS\\uml_python\\data\\dailyImports",
  "from_bw_dir": "C:\\git\\UMASS\\uml_python\\data\\fromBW",
  "fmp_output_file": "C:\\git\\UMASS\\uml_python\\output\\ebFMP.html"
}
```

An example config is included at:
- `config.ebuilder.example.json`

### `daily_imports_dir`

`daily_imports_dir` is the base folder for the files that older scripts used to write under:
- `B:\dailyImports`

Set it to any writable folder on your machine or shared drive, for example:
- `C:\git\UMASS\uml_python\data\dailyImports`

Current workflows use this directory for generated outputs such as:
- timestamped CSV import workbooks like `_CSV_<timestamp>_...`
- timestamped XML import workbooks like `_XML_<timestamp>_...`
- summary HTML files like `_PODataTotals.html` and `_InvoiceDataTotals.html`
- working subfolders such as `fromBuyways_reports`, `fromXML`, and `TEST`

Usage notes:
- keep the key name exactly as `daily_imports_dir` in `config.ebuilder.json`
- point it at the root `dailyImports` folder, not directly at one of its subfolders
- use a path that the current user can read and write
- code reads it through `uml_lib.ebAPI_lib.get_daily_imports_dir()` when building daily import output paths
- the nearby `B:\dailyImports...` comments left in older files are intentional breadcrumbs showing the legacy location that was replaced by this config value

## How to run

### Run the dashboard

From the repo root, with the virtual environment activated:
- `python ebDashboard.py`

## Buyways to E-Builder Import

### `Run bwebJoined`

`Run bwebJoined` is the dashboard action that processes a batch of zipped Buyways report exports without prompting for a file picker.

What it does:
1. Reads `daily_imports_dir` from `config.ebuilder.json`.
2. Looks in `daily_imports_dir\fromBuyways_reports\` for `.zip` files.
3. Extracts each zip file into that same `fromBuyways_reports` folder.
4. Scans the extracted files for:
   - `*po_search*.csv`
   - `*invoice_search*.csv`
5. Sends each CSV through the standard `bw2eb` translator:
   - PO CSVs go to the PO import workflow
   - invoice CSVs go to the invoice import workflow
6. Deletes each CSV after it is processed.
7. Collects the generated import workbooks and groups them into:
   - PO cost imports
   - PO process imports
   - invoice cost imports
   - invoice process imports
8. Joins each non-empty group into a single combined workbook.
9. Updates the rolling HTML summary files for PO and invoice totals.
10. Returns the list of joined workbook paths to the dashboard UI.

Paths used by `Run bwebJoined`:
- reads zip files from `daily_imports_dir\fromBuyways_reports\`
- reads extracted CSV files from `daily_imports_dir\fromBuyways_reports\`
- writes per-file import workbooks under `daily_imports_dir` with names like `_CSV_<timestamp>_POcostImport.xlsx`
- writes joined batch workbooks under `daily_imports_dir` with names like `_CSV-ZIP_<timestamp>_POCostImportJoinedData.xlsx`
- updates summary HTML files at:
  - `daily_imports_dir\_PODataTotals.html`
  - `daily_imports_dir\_InvoiceDataTotals.html`

Important notes:
- `daily_imports_dir\fromBuyways_reports\` must already exist before you run this workflow
- the script currently computes a `processed` subfolder path under `fromBuyways_reports`, but the zip-move step is commented out, so zip files are currently left in place after extraction
- the actual HTML summary output path comes from `daily_imports_dir`, even though there are a few leftover historical path variables in the older script
- this workflow depends on the same downstream PO and invoice translators used by the single-file `Run bw2eb` button

### Run a single script directly

Examples:
- `python moStat.py`
- `python ebTimeAlloc.py`
- `python ebFMP.py`

Note that many scripts depend on:
- a valid `config.ebuilder.json`
- local cache files
- network/shared-drive paths used by the original workflow

## Typical first-time workflow

1. Clone/open the repo at:
   - `C:\git\UMASS\uml_python`
2. Create and activate `.venv`
3. Install dependencies
4. Create `config.ebuilder.json`
5. Start with `Run ebData` in the dashboard to populate cached JSON files
6. Test one workflow at a time using sample files where possible

## Local cache behavior

Several workflows rely on cached e-Builder data stored as JSON files.

Today, some code still expects cache files under a hard-coded location such as:
- `B:\ebData\`

That means:
- if the cache directory does not exist, features that read cached JSON may fail
- if the shared drive is unavailable, some workflows will not run until path configuration is centralized

## Sample inputs

Example files are available in:
- `sampleData/`

These are useful for testing CSV/XML processing without needing fresh production exports first.

## Dependencies

Dependencies are tracked in both:
- `requirements.txt`
- `pyproject.toml`

Notable packages used by this repo include:
- `openpyxl`
- `pandas`
- `requests`
- `xmltodict`
- `lxml`
- `pyodbc`
- `mysql-connector-python`

## Troubleshooting

### `ModuleNotFoundError`
Run from the repo root:
- `C:\git\UMASS\uml_python`

And make sure the virtual environment is activated.

### `Config file not found`
Create:
- `config.ebuilder.json`

in the repo root.

### Missing JSON cache files
Run:
- `Run ebData`

from the dashboard, assuming your configured data path and API access are valid.

### Shared-drive path errors
Some workflows still reference paths like:
- `B:\...`

If those locations do not exist on your machine, those features will need path configuration updates before they can run locally.

## Development notes

Current repo conventions:
- use repo-root imports like `uml_lib...`, `eb...`, and `bw2eb...`
- avoid import-time API calls or file I/O
- keep `requirements.txt` and `pyproject.toml` in sync when changing dependencies
- run from the repository root

## Recommended next improvement

The next major improvement for portability is centralizing all hard-coded paths into configuration so the project can run outside the original environment without source edits.

## Change Request Protocol — how to use

This repository includes a conversational change-request protocol in `.github/copilot-instructions.md`. Follow it when you want the assistant to make code changes.

How to start a new change request (suggested phrasing):
- "I would like to start a new change request"

What happens next:
1. The assistant will generate a 6-digit acceptance code and present it to you.
2. You must reply with that exact code to confirm the request before any code is changed.
3. If you instead ask "Are you ready?", the assistant will present a compact TLDR plan of the proposed changes and generate a fresh code for acceptance.
4. If git actions are part of the workflow, changes should be staged only unless you explicitly request a commit.

Why this exists:
- The protocol prevents accidental or premature edits and ensures there is an explicit human approval step before code changes are applied.

How to modify the protocol text

Keep numbering stable so reviewers can reference specific steps. To insert a new instruction between two existing steps, add a decimal sub-step. For example:
- To insert a step between step `1` and `2`, add `1.1` with the new instruction. This preserves the original integer indexes for easy reference.

If you want to renumber the protocol to a new canonical order, do both of the following:
1. Edit `.github/copilot-instructions.md` and update the numbered list.
2. Update `README.md` with a short summary of the change and the new step numbers.

Rule of thumb: prefer adding a decimal sub-step (e.g., `3.1`) to keep references stable; only renumber the whole list if you are intentionally reorganizing the entire protocol.

Where to edit the protocol
- Primary source of truth: `.github/copilot-instructions.md` in the repo root.
- Make the same, short, corresponding note in `README.md` so humans who open the repo see the workflow quickly.

After protocol changes
- Follow the change-request protocol itself when making edits to the protocol file (generate code, get confirmation, then implement). This ensures edits to the protocol are made with the same governance as any other change.
