# Category 2 — Data Model Update Errors

These files parse fine (valid TMDL syntax) but break Power BI on **load** or
**refresh**, because a change left the model internally inconsistent. These are
harder to catch than syntax errors — they require reasoning about the model as
a graph, not just reading one file in isolation. Most commonly triggered by
column/table renames, removals, or migrations (e.g. swapping a data source).

## 2.1 Orphaned auto-generated date/variation tables

- Power BI auto-creates a hidden local date table for any date/datetime column
  used in a hierarchy or slicer, tied to that column via a **variation**
  (`ShowAsVariationsOnly` on the source column, plus a `variation` block
  pointing at the generated table).
- **Failure mode**: you remove or rename the source datetime column (e.g. during
  a data source migration), and you update/remove the `relationships.tmdl`
  entry — but you leave the auto-generated date table's own `.tmdl` file and its
  reference in `model.tmdl`'s table list untouched. Power BI requires every
  table with `ShowAsVariationsOnly` to be the *active target* of a variation;
  an orphaned one (variation source gone, target still declared) breaks the
  load.
- **Fix**: when removing/renaming a datetime column that had auto-generated
  date table behavior, also remove that table's `.tmdl` file entirely and its
  reference in `model.tmdl`, not just the relationship.
- **How to detect**: grep `model.tmdl` for date-table-like table names
  (commonly prefixed `LocalDateTable_` or `DateTableTemplate_`) and confirm each
  one's source column (check `variation`/`ShowAsVariationsOnly` in the relevant
  column) still exists.

## 2.2 M query function argument mistakes (positional args)

- When editing embedded Power Query (M) inside `expressions.tmdl` or a table's
  partition, a very easy mistake is passing an optional argument in the wrong
  **position** — M functions often take several optional positional arguments,
  and getting the position wrong doesn't fail to parse, it fails at **refresh
  time** with a cryptic runtime error.
- Real example: `Table.TransformColumns(table, {...}, MissingField.Ignore)` —
  here the 3rd positional argument is `defaultTransformation` (expects a
  *function*), not `missingField` (which is actually the 4th argument). Passing
  `MissingField.Ignore` (an enum value, `1`) in the 3rd slot produces an error
  along the lines of *"We cannot convert the value 1 to type Function"* — which
  gives no hint that the real issue is argument position.
- **Fix**: when passing more than the first 2 arguments to any M function,
  check the actual documented signature and argument order — don't assume
  argument names map to position by convention alone. If an optional argument
  isn't actually needed (e.g. columns already match after a prior rename), it's
  often simplest to drop it entirely rather than guess its correct slot.
- **How to detect**: after any M query edit, mentally verify each positional
  argument against the function's real signature, especially for functions with
  4+ possible arguments (`Table.TransformColumns`, `Table.RenameColumns`,
  `Table.SelectColumns`, `Table.AddColumn`, etc.).

## 2.3 Cascading column renames — the "who else uses this" check

- Renaming or removing a column at the source (e.g. a database view changes)
  requires updating **every** place in the model that references it:
  - The column's own `sourceColumn` in its table `.tmdl`
  - Any `Table.SelectColumns` / `Table.RenameColumns` step in the M query that
    lists the old name literally
  - Every measure that references `'Table'[Column]`
  - Every relationship's `fromColumn`/`toColumn`
  - Every RLS role's filter expression
  - Every `visual.json` binding (see `visual-report-errors.md`)
- **Failure mode observed**: an upstream view was migrated and stopped exposing
  two derived/aliased columns by their old friendly names — but those old names
  were still referenced by a `Table.SelectColumns` step (which fails outright
  if the named column doesn't exist), *and* separately still needed by other
  measures that legitimately depended on the raw underlying columns (so a
  simple rename wasn't safe — it would've broken those other measures).
- **Fix pattern**: when a column is renamed at the source but old-name
  consumers still need it under the old name, add a `Table.DuplicateColumn`
  step in the M query to recreate the old-named column as a copy, rather than
  renaming the original (which would break whatever else already legitimately
  depends on the original name/column).
- **How to detect / verify**: after any rename or removal, run one grep pass
  across the *whole project* — every `.tmdl` file — for the old column name in
  the pattern `TableName[old_name]` or `TableName.old_name`, plus a second pass
  across every `visual.json`. Confirm zero remaining hits, or that each
  remaining hit is intentional (duplicated column, not a stale reference).

## 2.4 `sourceColumn` drift

- A column's declared name (`column FriendlyName`) and its `sourceColumn:
  actual_db_field` can silently diverge if one is edited without the other —
  this doesn't break parsing, but breaks refresh (column not found in the
  source) or silently maps to the wrong underlying field.
- Always edit `sourceColumn` and the M query's column list together; never
  assume renaming one is enough.

## 2.5 Verification pass (run this after any model-structure edit)

1. List every table/column/measure that was renamed or removed this session.
2. Grep the whole `*.SemanticModel/definition/` tree for each old name.
3. Grep the whole `*.Report/definition/` tree for each old name.
4. For every hit, confirm it's either (a) intentionally still valid (e.g. a
   duplicated column keeping the old name alive on purpose) or (b) needs fixing.
5. Only report the task as complete once this pass returns zero unexplained hits.
