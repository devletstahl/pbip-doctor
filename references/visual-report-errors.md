# Category 3 — Report / Visual JSON Semantic Errors

Files under `*.Report/definition/**/*.json`: `report.json`, `pages/pages.json`,
`pages/<id>/page.json`, `pages/<id>/visuals/<id>/visual.json`,
`bookmarks/*.json`. Plain JSON, but with Fabric/Power BI-specific structural
rules and a versioned schema. Errors here typically don't stop the file from
opening — they show up as a blank/broken visual, a missing page, or a bookmark
that silently does nothing.

## 3.1 `$schema` — don't touch it

- Every relevant file starts with a `"$schema"` URL pointing at a specific
  Fabric schema **version**, e.g.
  `.../report/definition/visualContainer/2.10.0/schema.json`.
- **Never remove this line.** Never bump the version "just in case" — if the
  installed Power BI Desktop is older than the referenced schema version, the
  file can fail to open. If a file already had a version, keep it unchanged
  when editing.
- Different file types have different schemas (`visualContainer` for
  `visual.json`, `page` for `page.json`, etc.) — never copy a `$schema` line
  from one file type into another.

## 3.2 Broken field bindings after a model rename

- A `visual.json` binds to model fields (measures/columns) through nested
  expression structures, e.g.:
  ```json
  "expr": { "Literal": { "Value": "'Some Measure Name'" } }
  ```
  or a `Column`/`Measure`/`Aggregation` reference with an `Entity` (table name)
  and `Property` (column/measure name).
- If a measure or column referenced here was renamed or removed in the model
  (see `model-update-errors.md` §2.3), the visual breaks — typically showing
  "Can't display this visual" or a blank tile, with no build-time error at all.
- **This is the single easiest error to miss** because nothing fails when you
  edit the TMDL — it only surfaces when the report is opened and the visual
  tries to bind. Always grep every `visual.json` for the old name whenever a
  measure/column is renamed in the model, even if the report wasn't the thing
  you were editing.

## 3.3 JSON structural basics (still worth checking)

- Trailing commas: the last property in an object/array must never have a
  trailing comma. When inserting a new property at the end of an existing
  block, add the comma to the line that used to be last, not a new trailing one.
- Balanced braces/brackets — `visual.json` files are commonly 5-8 levels deep;
  when editing a nested block, confirm every `{`/`[` you touched still closes
  in the right place.
- Quoting: some string values are themselves DAX/M literals and legitimately
  contain single quotes inside a JSON double-quoted string (e.g. `"Value":
  "'Some Value'"`) — don't "fix" these into something that breaks the outer
  JSON string.

## 3.4 ID synchronization across index files

- `pages.json` lists page IDs in display order. Adding/removing a page folder
  under `pages/<id>/` is not enough — `pages.json` must be updated too, or the
  page won't show up (or a removed page ID lingers and errors).
- `page.json` lists the visuals belonging to that page — keep this in sync with
  the `visuals/<id>/` subfolders.
- `bookmarks/bookmarks.json` lists bookmark IDs the same way.
- Each `*.bookmark.json` snapshots filter/visual state. If a visual it
  references is later removed or renamed, the bookmark **doesn't error on file
  open** — it silently fails (or does nothing) only when the user applies it.
  Whenever removing/renaming a visual, grep the bookmarks folder too.

## 3.5 Cross-file reference checklist (run after any report or model edit)

1. Measure/column renamed in TMDL → grep every `visual.json` for the old name.
2. Page/visual ID changed → check the corresponding `pages.json`/`page.json`.
3. Visual removed → check every `*.bookmark.json` for a reference to its ID.
4. `$schema` line unchanged unless there was a deliberate, confirmed reason to
   change it.

## 3.6 Before declaring a report file clean

- Confirm the JSON parses (mentally, or with a JSON validator if available) —
  don't rely on visual inspection alone for deeply nested files.
- Confirm every field binding still resolves to something that exists in the
  current model.
- Confirm ID lists (`pages.json`, `page.json`, `bookmarks.json`) match the
  folders/files that actually exist on disk.
