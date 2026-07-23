# Known Power BI Desktop Error Signatures

When the user pastes an actual error message or a Frown/feedback log from Power
BI Desktop, check it against this list first — it's much faster than reading
every file from scratch. Each entry: what you'll see → what it actually means →
which category/reference file to open.

---

### `TMDL Format Error: Parsing error type - InvalidLineType` / `Unexpected line type: Other!`

- **Points at**: a specific document + line number + the offending line text.
- **Most common cause**: a bare `// comment` line in a `.tmdl` file outside any
  embedded M/DAX block (TMDL doc-comments require `///`), or a line indented
  with spaces instead of tabs.
- **Go to**: `tmdl-syntax-errors.md` §1.1 and §1.2.
- **Fix approach**: open the exact file/line named in the error, fix that one
  line — then grep the *whole project* for the same pattern (bare `//` lines,
  or space-indentation), because this kind of error is almost always
  introduced in bulk (e.g. by an automated migration adding "helpful" comments
  everywhere), not as an isolated typo.

### Generic "There's a problem with the definition content in your Power BI project" with no further detail, or the file *looks* correct on inspection

- **Most common cause**: file encoding — a BOM was introduced by a shell
  command that rewrote the file (e.g. PowerShell's default UTF-8 encoding).
- **Go to**: `tmdl-syntax-errors.md` §1.3.
- **Fix approach**: check every recently-touched `.tmdl` file for a BOM;
  rewrite without one.

### `DataModelLoadFailed` (as an inner error code) combined with a table that has `ShowAsVariationsOnly`

- **Most common cause**: an auto-generated local date table lost its variation
  source column (removed/renamed) but the table itself and its reference in
  `model.tmdl` weren't removed — an orphaned variation target.
- **Go to**: `model-update-errors.md` §2.1.
- **Fix approach**: remove the orphaned date table's `.tmdl` file and its
  listing in `model.tmdl`.

### `We cannot convert the value <N> to type Function` (or similar) during refresh, referencing an M step like `Table.TransformColumns`

- **Most common cause**: an optional positional argument was passed in the
  wrong slot — an enum value (e.g. `MissingField.Ignore`) landed in the
  argument position that expects a function (`defaultTransformation`).
- **Go to**: `model-update-errors.md` §2.2.
- **Fix approach**: check the real function signature; either reorder the
  arguments correctly or drop the unneeded one entirely.

### A specific measure/column M query step fails referencing a column name that "should" exist

- **Most common cause**: an upstream source (view/table) stopped exposing a
  column under its old friendly name after a migration, and a
  `Table.SelectColumns`/`Table.RenameColumns` step still references the old
  name literally.
- **Go to**: `model-update-errors.md` §2.3.
- **Fix approach**: if other measures still legitimately need the old name,
  add a `Table.DuplicateColumn` step to recreate it as a copy rather than
  renaming the original.

### Visual shows "Can't display this visual" / blank tile, but the file opened fine and no build error occurred

- **Most common cause**: the visual is bound to a measure/column that was
  renamed or removed in the model, and nothing re-checked `visual.json` files
  after the model change.
- **Go to**: `visual-report-errors.md` §3.2.
- **Fix approach**: grep every `visual.json` for the old field name; update the
  binding to the new name.

### A bookmark does nothing when applied (no error, just no effect)

- **Most common cause**: the bookmark references a visual ID that was later
  removed or changed.
- **Go to**: `visual-report-errors.md` §3.4.

### Page or visual missing from the report despite its folder/file existing on disk

- **Most common cause**: `pages.json` or `page.json` wasn't updated to include
  the new ID, or still lists a removed one.
- **Go to**: `visual-report-errors.md` §3.4.

---

## How to use this file

1. Take the user's error text (or the relevant part of a Frown/feedback log).
2. Match it against the signatures above by the distinctive substring (error
   type name, inner exception code, or the shape of the failure).
3. Jump straight to the referenced section instead of re-deriving the cause
   from scratch.
4. If nothing matches, fall back to the full checklists in the three category
   files, starting with whichever file type (`.tmdl` vs `.json`) the error log
   points at.
