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

## How to run

### Run the dashboard

From the repo root, with the virtual environment activated:
- `python ebDashboard.py`

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
