---
name: pbip-doctor
description: >
  Use this skill whenever editing files inside a Power BI Project (.pbip) folder
  — TMDL files under a *.SemanticModel/definition/ folder, or JSON files under a
  *.Report/definition/ folder — regardless of which agent, skill, or MCP server
  (e.g. a semantic-model MCP, a report-authoring skill, or manual edits) produced
  the change. Also use whenever the user asks to review, validate, debug, or find
  errors in a .pbip project, or asks why a file won't open in Power BI Desktop.
  Use PROACTIVELY right after ANY tool finishes editing .tmdl or .json files
  inside a .pbip project, before reporting the edit as complete — to catch
  syntax, encoding, and reference errors before the user opens the file in Power
  BI Desktop and hits a load failure. Can also run standalone, unprompted by any
  edit, as a periodic health check on a project. Triggers include: "review this
  pbip", "why won't this open", "validate this tmdl", "check this model", "Power
  BI won't load", "find the error in this report", "suggest improvements to this
  model/dashboard".
---

# Skill: PBIP Doctor

A safety net and reviewer for **Power BI Project (.pbip)** files: the TMDL
definition of the semantic model, and the JSON definition of the report. LLMs
still routinely produce syntactically-plausible-but-invalid TMDL/JSON, or
updates that are locally correct but break a reference elsewhere in the
project. Power BI Desktop's error messages for these failures are often generic
("there's a problem with the definition content...") and don't point at the
actual root cause — this skill exists to catch the real cause before the user
ever opens the file.

**Tool-agnostic by design.** This skill doesn't care what produced the change —
a semantic-model MCP server, a report-authoring skill, an agentic coding tool,
or a human editing by hand. It watches the *files*, not the *tool*, so it slots
in after (or independently of) whatever else is doing the actual editing.

**What makes this different from a structural/schema validator**: rather than
just checking "is this valid TMDL/JSON," the checklists here are built from
concrete failure modes actually observed in production — the specific ways an
LLM or an automated migration silently breaks a working model (see
`references/error-signatures.md` for real Power BI Desktop error text mapped to
root cause). Use a schema-level validator (if one is available in your setup)
for structural completeness; use this skill for judgment-heavy checks a schema
validator can't do — cascading renames, orphaned variation tables, M function
argument-order bugs, encoding corruption from bulk edits, and so on.

Three modes:

1. **Automatic guardrail** — run right after any tool finishes editing a
   `.tmdl` or `.json` file inside a `.pbip` project, before reporting the task
   as done.
2. **On-demand review** — when the user asks to review, validate, debug, or
   improve an existing project, whether or not it was touched this session.
3. **Standalone health check** — run against a project with no specific trigger,
   e.g. "give this model a checkup" or as a periodic habit before a release/demo.

---

## 1. WORKFLOW

### Step 1 — Scope the review

- If this follows an edit: check which files changed (`git status`/diff if
  version-controlled, or just the files you just wrote). Review those files
  **plus** anything that references what changed — e.g. if you renamed a column,
  every measure, relationship, role, and visual that could reference it is in
  scope, not just the file you edited.
- If it's an on-demand review: ask (or infer from the request) whether the scope
  is the semantic model, the report, or the whole project.

### Step 2 — Pick the right checklist

This skill splits errors into three categories — read the reference file(s) that
match what you touched:

```
TMDL syntax/parsing errors (file won't parse at all)        → references/tmdl-syntax-errors.md
Data model update errors (parses fine, breaks on load/refresh) → references/model-update-errors.md
Report/visual JSON errors (report won't render or shows blank) → references/visual-report-errors.md
```

If unsure which category an error belongs to, check `references/error-signatures.md`
first — it maps literal Power BI Desktop error strings to root cause and category.

### Step 3 — Run the checklist

Go through the relevant checklist item by item against the file(s) in scope.
Don't narrate every item you checked — just report what you find.

### Step 4 — Report

- **Nothing found**: say so briefly and specifically (e.g. "Reviewed the TMDL for
  table X and the visual.json for page Y — no syntax or reference errors").
- **Issue(s) found**: list each with file + line + what's wrong + the fix. Fix
  directly (Edit) if it's an objective syntax/reference error. If it's a proposed
  improvement rather than a bug, present it as a suggestion and confirm before
  applying.
- **Never** claim "looks fine" without having actually read the files.

### Step 5 — Improvements (only when explicitly requested, or in review mode)

Beyond hard errors, flag:
- Duplicate or near-duplicate measures (candidates to consolidate)
- Columns with no apparent consumer (no measure, relationship, or visual uses them)
- `summarizeBy` that doesn't make sense for the column's semantic type (e.g. `sum`
  on an ID column)
- DAX that could be simpler or more efficient (e.g. nested `IF(ISBLANK(...))` vs `DIVIDE(..., 0)`)
- Visuals bound to fields that no longer exist in the model

These are suggestions, not auto-fixes — always confirm before applying anything
in this category (unlike objective error fixes, which you should just apply).

---

## 2. GENERAL RULES

- **Don't invent errors.** If you're not certain something breaks Power BI, flag
  it as "worth double-checking manually," not as a confirmed bug.
- **TMDL is TAB-indented, not space-indented.** Never use spaces to indent a
  `.tmdl` file. See `references/tmdl-syntax-errors.md`.
- **TMDL comments use `///` (triple slash), not `//`.** A bare `//` line comment
  outside of embedded M/DAX code is invalid TMDL and fails to parse. See
  `references/tmdl-syntax-errors.md` — this is one of the single most common
  mistakes an LLM makes when annotating a migration.
- **Watch file encoding after bulk text edits**, especially anything done via
  shell scripting (PowerShell, sed, etc.) rather than a proper file-edit tool —
  see `references/tmdl-syntax-errors.md` §BOM.
- **Report JSON is schema-versioned** (a `$schema` URL at the top of the file) —
  never remove or change that line, and never invent a property that doesn't
  exist in comparable files in the same project.
- Prefer the smallest possible diff when fixing — don't reformat an entire file
  over one localized error.
- After fixing, re-read the changed section to confirm the fix didn't introduce
  a new problem (unbalanced parens/braces, a comma left dangling).
- When a column, table, or measure is renamed or removed, always grep the whole
  project for the old name — TMDL, other TMDL files, and every `.json` file
  under the report — before considering the change done.

---

## 3. REFERENCE FILES

- `references/tmdl-syntax-errors.md` — semantic/syntax errors in `.tmdl` files:
  indentation, comments, quoting, encoding, GUID collisions.
- `references/model-update-errors.md` — errors from changing the data model:
  renamed/removed columns, orphaned relationships and variation tables, M query
  function misuse, cascading references across tables.
- `references/visual-report-errors.md` — errors in the report definition: broken
  visual bindings, JSON structure, page/bookmark ID sync, schema versioning.
- `references/error-signatures.md` — known Power BI Desktop error messages
  mapped to root cause, category, and fix. Check here first if you have an
  actual error message/log from the user.

---

## 4. EXAMPLE

Some other tool in the workflow — an MCP server, an agentic coding skill, or a
manual edit — just added a new measure to a measures file and changed a
column's `sourceColumn` in a table file. Before reporting "done," this skill:

1. Reads the measures file in full, checks tab indentation, DAX syntax, and that
   the new measure has a fresh (non-duplicate) `lineageTag`.
2. Reads the edited table file and confirms the new `sourceColumn` still matches
   a real column in the upstream query (M code in `expressions.tmdl` / the
   table's own partition).
3. Greps the whole project for the old measure/column name to confirm nothing
   else (other tables, roles, relationships, `visual.json` files) still points
   at it.
4. Reports "clean" or the list of fixes applied.
