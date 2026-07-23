# Category 1 — TMDL Syntax / Parsing Errors

These are the errors that stop the **parser** cold — the file doesn't even
load, and Power BI Desktop typically shows a generic error like "There is a
problem with the definition content in your Power BI project" with a nested
`TMDL Format Error`. Files live under `*.SemanticModel/definition/**/*.tmdl`.

## 1.1 Indentation is TAB-based, not space-based

- Each hierarchy level = **one literal TAB character**. Never spaces.
- Example (real structure):
  ```
  table Sales
  	lineageTag: 5ea63c0c-409e-475a-b654-9f7f0fd09f75

  	column id
  		dataType: int64
  		formatString: 0
  		lineageTag: 0d753156-573f-4879-8cd7-f2774f7be948
  		summarizeBy: sum
  		sourceColumn: id

  		annotation SummarizationSetBy = Automatic
  ```
  `table` sits at column 0. Direct children (`column`, `measure`, the table's
  own `lineageTag`): 1 tab. Properties of a column/measure (`dataType`,
  `lineageTag`, etc.) and its `annotation`: 2 tabs.
- **When editing with a text-edit tool**, copy the indentation of the
  neighboring line exactly instead of guessing tab counts. Don't trust how it
  *looks* rendered — some editors visually expand tabs to spaces; verify the
  raw bytes if unsure.
- A single space-indented line can fail the **entire file's** parse, not just
  that object — the error rarely points at the exact offending line in a way
  that's obvious, so re-check every line you touched, not just the one that
  changed conceptually.

## 1.2 Comments: `///` not `//`

- TMDL doc-comments use **triple slash** (`///`) at the start of a line. A bare
  `//` line-comment is only valid *inside* embedded M or DAX code blocks — as a
  standalone line before a `column`/`measure`/`table` declaration, it is
  **invalid TMDL** and fails to parse.
- Real failure signature:
  ```
  TMDL Format Error:
  	Parsing error type - InvalidLineType
  	Detailed error - Unexpected line type: Other!
  	Document - './tables/SomeTable'
  	Line Number - 894
  	Line - '	// Calculated column requested by the user: ...'
  ```
- This is a very common LLM mistake: when annotating *why* a change was made
  during a migration or refactor (e.g. "// added per user request"), the model
  reaches for `//` out of habit from general-purpose code, not realizing TMDL's
  comment syntax differs. **Always use `///`** for any explanatory comment
  placed directly in a `.tmdl` file, matching whatever convention is already
  used elsewhere in the same project.
- If you (or a prior edit) used `//` in bulk (e.g. across a whole migration),
  grep the entire `*.SemanticModel/definition/` tree for lines starting with
  `//` (not `///`) outside of any embedded M/DAX block — every one of them is
  a parse-breaking bug waiting to surface.

## 1.3 Encoding — BOM and non-UTF-8-without-BOM saves

- TMDL files are expected to be plain UTF-8 **without a byte-order mark (BOM)**.
- If a file gets rewritten via a shell command that defaults to BOM-prefixed
  UTF-8 — e.g. PowerShell 5.1's `Set-Content`/`Out-File -Encoding utf8` writes a
  BOM by default — the file can fail to parse or silently corrupt, even though
  the visible text content is unchanged.
- **Never use raw shell redirection or `Set-Content`/`Out-File` to bulk-edit
  `.tmdl` files.** Use a proper file-edit tool that preserves the original
  encoding, or if a script is unavoidable, force BOM-less UTF-8 explicitly
  (e.g. `-Encoding utf8NoBOM` in PowerShell 7+, or write bytes manually in
  PowerShell 5.1).
- After any bulk find/replace across multiple `.tmdl` files, verify none of
  them picked up a BOM — this is easy to miss because the file *looks* correct
  when viewed in most editors.

## 1.4 String interpolation corrupting embedded DAX

- If you generate or rewrite TMDL content via a scripting language's string
  interpolation (PowerShell `"$var"`, bash, etc.) instead of writing the literal
  text directly, watch for interpolation accidentally consuming or mangling
  DAX tokens that look like variables — e.g. a `VAR`/`RETURN`/`IF` structure can
  silently lose lines if the surrounding script treats parts of the DAX as
  something to substitute.
- Prefer direct file-edit tools (which pass content through literally) over
  generating TMDL/DAX text through a shell's string interpolation. If a script
  must be used, re-read the resulting file afterward and diff it conceptually
  against the intended change — don't assume the script executed as written.

## 1.5 Unique `lineageTag` (GUID) per object

- Every table, column, measure, relationship, and role has a `lineageTag` — a
  GUID (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`, lowercase, hyphenated).
- **Never reuse an existing `lineageTag`** on a new object, and never copy one
  from another object as a shortcut. A duplicate `lineageTag` anywhere in the
  model can cause it to fail loading, sometimes with an error that doesn't
  obviously point at "duplicate GUID."
- When creating a new object, generate a fresh, genuinely random GUID.

## 1.6 Measures — expression indentation and balance

- Syntax: `measure 'Measure Name' =` followed by the DAX expression, typically
  indented further than the `measure` line (commonly +2 tabs, but follow
  whatever pattern the rest of the file already uses).
- After the expression, indentation returns to the `measure`'s own level (1 tab)
  for trailing properties like `lineageTag` and `annotation PBI_FormatHint = {...}`.
- Quote the measure name with single quotes (`'...'`) if it contains a space or
  special character; leave unquoted only for simple identifiers.
- Check parentheses/brackets are balanced in the DAX expression — this is the
  single most common hand-edit mistake in measures.

## 1.7 Before declaring a file clean

- Re-read the whole file top to bottom (not just the edited lines), mentally
  tracking indentation depth.
- Grep for `//` (not `///`) outside embedded M/DAX blocks.
- If a column/measure was renamed or added, grep other `.tmdl` files and the
  report's `.json` files for the old/new name (see `model-update-errors.md` and
  `visual-report-errors.md`).
