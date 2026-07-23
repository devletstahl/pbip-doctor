<p align="center">
  <img src="assets/logo/final-ekg-circle-pbi-static.svg" width="96" height="96" alt="pbip-doctor logo" />
</p>

<h1 align="center">pbip-doctor</h1>

<p align="center">
  A Claude Code skill that catches broken Power BI Project (.pbip) edits<br>
  before you ever hit "won't load" in Power BI Desktop.
</p>

<p align="center">
  <a href="#install">Install</a> ·
  <a href="#usage">Usage</a> ·
  <a href="#why">Why this exists</a> ·
  <a href="#in-action">In action</a> ·
  <a href="#whats-inside">What's inside</a> ·
  <a href="#license">License</a>
</p>

---

## Why

Claude (and most LLMs) still routinely produce TMDL or report-JSON edits that
look correct but aren't — a bare `//` comment where TMDL requires `///`, a
column rename that leaves three other files pointing at the old name, an M
query argument in the wrong position. Power BI Desktop's error for all of
these is usually the same unhelpful dialog:

> "There's a problem with the definition content in your Power BI project."

**pbip-doctor** is a review pass built from real failures like these — not a
generic schema validator, but a checklist of the specific ways an agentic edit
silently breaks a working `.pbip` project, plus a lookup table mapping actual
Power BI Desktop error text back to root cause.

It's **tool-agnostic**: it doesn't care whether the edit came from a semantic-
model MCP server, a report-authoring skill, another agent, or a human typing
directly into a `.tmdl` file. It watches the *files*, not the tool.

## Install

Clone (or copy) this folder into your Claude Code skills directory:

```bash
git clone https://github.com/<your-username>/pbip-doctor.git ~/.claude/skills/pbip-doctor
```

Or drop the folder into a project's `.claude/skills/` directory to scope it to
one repo instead of making it global.

No dependencies, no API keys, no build step — it's a Markdown skill definition
plus reference files that Claude reads directly.

## Usage

The skill activates on its own in three situations:

- **Right after an edit** — any tool just changed a `.tmdl` or `.json` file
  inside a `.pbip` project; Claude reviews it before saying the task is done.
- **On demand** — ask directly: *"review this pbip"*, *"why won't this open"*,
  *"validate this tmdl"*, *"check this model"*.
- **Standalone health check** — *"give this model a checkup"*, with no prior
  edit at all.

If you paste an actual Power BI Desktop error message, the skill checks it
against `references/error-signatures.md` first, which maps real error text to
root cause — much faster than re-deriving the cause from scratch.

## In action

**Power BI Desktop, on open:**

```
There's a problem with the definition content in your Power BI project.

TMDL Format Error:
    Parsing error type - InvalidLineType
    Detailed error - Unexpected line type: Other!
    Document - './tables/SomeTable'
    Line Number - 894
    Line - '	// Calculated column requested by the user: shows the real ID'
```

**Claude, with pbip-doctor loaded:**

```
Found and fixed the error. The problem was invalid comment syntax in
SomeTable.tmdl:894 — TMDL doesn't accept a bare `//` line comment before
a column declaration (that's valid inside M/DAX code, but not as a
standalone comment in the file itself). Whatever migrated this file used
`//` in ~30 places to document the changes; I replaced all of them with
`///` (TMDL's actual doc-comment syntax), matching the convention already
used elsewhere in the same model. Try opening the .pbip again.
```

That specific bug — and four others like it (BOM re-encoding after a
PowerShell bulk edit, an orphaned auto-generated date table left behind after
a column removal, an M function argument passed in the wrong position, a
column rename that broke three unrelated measures) — is what
`references/error-signatures.md` and the other checklists are built from.
Each one cost real debugging time once; the point of this skill is that it
only has to cost that time once.

## What's inside

```
pbip-doctor/
├── SKILL.md                          — entry point: workflow, scope, rules
└── references/
    ├── tmdl-syntax-errors.md         — parser-breaking errors (indentation, comments, encoding, GUIDs)
    ├── model-update-errors.md        — errors from changing the model (orphaned tables, M query bugs, cascading renames)
    ├── visual-report-errors.md       — report/visual JSON errors (broken bindings, schema versioning, ID sync)
    └── error-signatures.md           — known Power BI Desktop error text → root cause → fix
```

Each reference file is a checklist derived from an actual failure, not a
theoretical one — see each file's intro for the reasoning.

## License

[MIT](LICENSE) — use it, fork it, adapt the checklists to your own project's
conventions.

---

<p align="center">
  <sub>Built for Claude Code · not affiliated with Microsoft or Power BI</sub>
</p>
