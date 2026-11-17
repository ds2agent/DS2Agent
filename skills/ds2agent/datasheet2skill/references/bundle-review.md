# Bundle review (schema and workbook rules)

`prepare` writes `inventory.json` (source snapshot) and `bundle.json` (editable routing). Edit
`bundle.json` before `extract`; the coordinator owns it.

## inventory.json

```json
{
  "name": "bmp280",
  "title": "BMP280 Digital Pressure Sensor",
  "main": "main.pdf",
  "sources": [
    {"id": "main", "path": "sources/0__main.pdf", "sha256": "<hex>", "role": "main",
     "pages": 49, "title": "BMP280 Data sheet"}
  ]
}
```

`sha256` is the content digest of the snapshotted source, computed over the bytes in source
order. `role` is one of `main`, `supplement`, `register-map`, `pin-table`.

## bundle.json

```json
{
  "name": "bmp280",
  "title": "BMP280 Digital Pressure Sensor",
  "main": "main",
  "sources": [
    {"id": "main", "role": "main", "title": "BMP280 Data sheet",
     "asset": "datasheet", "register_map": true, "pin_table": true}
  ]
}
```

Every supplied source must appear with a role, title, and asset routing. `register_map: true`
routes a source's register table into `references/register_map.md`; `pin_table: true` routes
its pin-out/connection tables into `references/pin_table.md`.

## Workbook (spreadsheet) rules

Workbook CSVs retain raw cell values, internal blanks, hidden rows and sheets, and cached
formula values. Verification re-reads each workbook snapshot and compares every exported
cell. Formula caches are never recalculated.

## Reuse

If the same source bytes were reviewed before, reuse those decisions after extraction; reuse
is allowed only for matching SHA-256 source snapshots and records provenance.
