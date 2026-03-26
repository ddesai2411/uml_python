# Copilot Instructions
## Change Request Protocol

Follow these steps for every change request in this project, in order:

1. **Generate a 6-digit code** before touching any code. The code must be derived using a Unix timestamp hash to ensure genuine randomness: take the current Unix epoch time in seconds, multiply by a prime (e.g. 2654435761), take modulo 900000, then add 100000 to guarantee a 6-digit result. The code must be unique to the change request and unique within the current chat session. Present it clearly to the user before doing anything else.
2. **Wait for confirmation.** The user must reply with that exact 6-digit code to proceed. Do not begin implementing until they do.
3. **If the code is not confirmed immediately**, treat it as a signal that the solution needs more discussion. Discard the code, do not reuse it, and re-engage to better understand the problem before proposing a new approach.
4. **If the user asks "Are you ready?"**, respond with a short TLDR — a tight bulleted list of exactly what will be changed. No code snippets, no prose padding, no fluff. Then generate a **new** 6-digit code for acceptance of that specific plan.
   - **Always use this exact format for the TLDR response:**

     > **Changes**
     > - \<what is being added, changed, or removed — one bullet per file or concern\>
     >
     > **`XXXXXX`** ← acceptance code
5. **If the "Are you ready?" code is not confirmed immediately**, discard it and return to step 2 — treat it as a signal that the plan needs more discussion before proceeding.
6. **Only after a code is confirmed** proceed with implementation.
   - **Always use this exact format for the implementation response:**

     > Confirmed. Implementing now.
     >
     > ---
     >
     > ### 1 — \<first change area\>
     > \<make the change — no commentary padding\>
     >
     > ### 2 — \<second change area\>
     > \<make the change\>
     >
     > _(continue numbered sections for each logical change)_
     >
     > ---
     >
     > _Summary table at the end:_
     >
     > | What | Detail |
     > |---|---|
     > | `FileName.cs` | one-line description of what changed and why |
7. **After implementation, update `README.md`** to reflect any changes that affect how the project is set up, run, or understood. Keep it current at all times.

---
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


---

## Dependencies
- Prefer existing libraries already declared in `pyproject.toml` and `requirements.txt`.
- When adding or removing Python dependencies, update both `pyproject.toml` and `requirements.txt`.
- Keep compatibility with the repo's declared Python version in `pyproject.toml`.

## Validation
- Validate Python changes with a compile or import check before finishing.
- Prefer focused fixes over broad refactors unless the task explicitly requests a larger cleanup.

## Git workflow
- Stage the files you changed.
- Do not create a git commit unless the user explicitly asks for one.

## Style
- Follow the existing code style and naming in the touched file.
- Avoid adding comments unless they help clarify non-obvious behavior.
