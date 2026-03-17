# Copilot Instructions

## Workspace and imports
- Treat `C:\git\UMASS\uml_python` as the workspace root.
- Run and import code from the repo root.
- Use root-relative imports only, such as:
  - `import uml_lib.ebAPI_lib as eb`
  - `import eb.ebPO.translate_BW_POs as tPO`
  - `import bw2eb.bw2eb as bw2eb`
  - `import moStat`
- Do not introduce legacy import styles such as:
  - `uml_python...`
  - `uml.uml_lib...`
  - bare local imports like `import ebAPI_lib`

## Runtime behavior
- Do not add API calls, file I/O, report generation, or other side effects at import time.
- Put executable script logic behind `if __name__ == "__main__":`.
- Keep changes minimal and preserve existing report formats, output field names, and workflow behavior unless the task explicitly asks for changes.

## Configuration and paths
- Assume e-Builder credentials and environment-specific settings come from `config.ebuilder.json`.
- Do not add new hard-coded machine-specific paths such as `B:\...` or `/Users/...`. New path settings should be added as config variables in `config.ebuilder.json` and documented in these instructions.
- When a path needs to be configurable, add a named variable to `config.ebuilder.json` instead of hard-coding it in source.
- For new path handling, prefer `pathlib.Path` and centralize path resolution in `config/helpers` rather than scattering string literals.

## Dependencies
- Prefer existing libraries already declared in `pyproject.toml` and `requirements.txt`.
- When adding or removing Python dependencies, update both `pyproject.toml` and `requirements.txt`.
- Keep compatibility with the repo's declared Python version in `pyproject.toml`.

## Validation
- Validate Python changes with a compile or import check before finishing.
- Prefer focused fixes over broad refactors unless the task explicitly requests a larger cleanup.

## Style
- Follow the existing code style and naming in the touched file.
- Avoid adding comments unless they help clarify non-obvious behavior.
