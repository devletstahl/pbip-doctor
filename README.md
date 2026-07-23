<p align="center">
  <img src="assets/logo/header-badge.gif" width="320" alt="pbip-doctor">
</p>

<p align="center">
  A Claude Code skill that catches broken Power BI Project (.pbip) edits
</p>

<p align="center">
  <a href="#install">Install</a> ·
  <a href="#usage">Usage</a> ·
  <a href="#why">Why</a> ·
  <a href="#in-action">In action</a> ·
  <a href="#whats-inside">What's inside</a> ·
  <a href="#license">License</a>
</p>

---

## Why

This came out of a pattern I kept running into: Claude edits a `.pbip` file, it looks fine, then Power BI Desktop throws an error and I'm back debugging it with Claude anyway. Usually the same handful of mistakes: a `//` comment where TMDL wants `///`, a renamed column that breaks three other files, an M query argument in the wrong slot.

pbip-doctor is that recurring troubleshooting turned into a skill: a checklist built from the errors I actually kept hitting, plus a lookup table mapping real Power BI Desktop error messages to their root cause. It's not a generic schema validator, it's the specific ways an agentic edit silently breaks a working `.pbip` project.

## Install

Clone (or copy) this folder into your Claude Code skills directory:

```bash
git clone https://github.com/devletstahl/pbip-doctor.git ~/.claude/skills/pbip-doctor
```

Or drop it into a project's `.claude/skills/` folder to scope it to one repo instead of making it global. No dependencies, no API keys, no build step: it's a Markdown skill definition plus reference files Claude reads directly.

## Usage

The skill activates on its own in three situations:

- **Right after an edit**: any tool just changed a `.tmdl` or `.json` file inside a `.pbip` project, Claude reviews it before saying the task is done.
- **On demand**: ask directly, *"review this pbip"*, *"why won't this open"*, *"validate this tmdl"*.
- **Standalone health check**: *"give this model a checkup"*, with no prior edit at all.

Paste an actual Power BI Desktop error message and the skill checks it against `references/error-signatures.md` first, real error text mapped to root cause, faster than re-deriving the cause from scratch.

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
SomeTable.tmdl:894, TMDL doesn't accept a bare `//` line comment before
a column declaration (that's valid inside M/DAX code, not as a standalone
comment in the file itself). Whatever migrated this file used `//` in
~30 places to document the changes; I replaced all of them with `///`
(TMDL's actual doc-comment syntax), matching the convention already used
elsewhere in the model. Try opening the .pbip again.
```

That bug, and four others like it (BOM re-encoding after a PowerShell bulk edit, an orphaned auto-generated date table left behind after a column removal, an M function argument in the wrong position, a rename that broke three unrelated measures), is what `references/error-signatures.md` and the other checklists are built from. Each one cost real debugging time once; the point of this skill is that it only costs that time once.

## What's inside

```
pbip-doctor/
├── SKILL.md                          : entry point, workflow, scope, rules
└── references/
    ├── tmdl-syntax-errors.md         : parser-breaking errors (indentation, comments, encoding, GUIDs)
    ├── model-update-errors.md        : errors from changing the model (orphaned tables, M query bugs, cascading renames)
    ├── visual-report-errors.md       : report/visual JSON errors (broken bindings, schema versioning, ID sync)
    └── error-signatures.md           : known Power BI Desktop error text, mapped to root cause and fix
```

Each reference file is a checklist built from an actual failure, not a theoretical one, see each file's intro for the reasoning.

## License

[MIT](LICENSE): use it, fork it, adapt the checklists to your own project's conventions.

---
