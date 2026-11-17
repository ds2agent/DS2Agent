---
name: availability
description: Locate purchase links (LCSC, Mouser, and others) for a named chip and recommend parts for a described function, filtered by compliance standard and region. Standalone sourcing skill; not part of the datasheet-to-agent conversion pipeline.
---

# availability

Answers two query shapes, always with link-cited results and never a fabricated stock
count, price, or link.

1. **Lookup** — a named chip (MPN or family) plus optional standards and region →
   purchase links.
2. **Recommend** — a functional description → recommended parts plus links.

Hard rule: every link is a real distributor URL or an actual API response. Distinguish
`live` (fetched now), `constructed` (URL built from the MPN, not yet confirmed), and
`cached` (from an auditable, dated offer file). State stock/price only from a live
response or an explicit dated offer file.

## Entry points

### 1. Lookup (chip → links)

Inputs: `chip` (MPN / family / orderable part), optional `standards[]`, `region`,
`quantity`, `currency`.

Steps:

1. Normalize the chip to an exact MPN when possible (manufacturer + base part + package +
   grade + temperature range). A bare family ("AT24C256", "SHT31") must not silently
   become one orderable MPN — keep it a family and list its orderable variants.
2. Query the sources in [references/sources.md](references/sources.md). LCSC and Mouser are
   mandatory; add Digi-Key / TI / Arrow when region or standards call for it.
3. Filter by the requested standards and region using the mapping in
   [references/sources.md](references/sources.md). A compliance claim must come from the
   listing or datasheet, never inferred from the family.
4. Emit the output contract below.

### 2. Recommend (function → chip)

Inputs: a free-text requirement, e.g. "3.3 V I²C temperature+humidity sensor, DFN,
±2 %RH, RoHS, buy in China". Follow [references/recommend.md](references/recommend.md).

## Output contract

```json
{
  "kind": "lookup | recommend",
  "chip": "<normalized part or requirement summary>",
  "standards": ["RoHS", "REACH"],
  "region": "CN | US | EU | JP",
  "results": [
    {
      "mpn": "...",
      "manufacturer": "...",
      "distributor": "lcsc | mouser | digikey | ti | arrow | farnell",
      "link": "https://...",
      "price": {"amount": null, "currency": null},
      "stock": null,
      "lead_time": null,
      "standards": ["RoHS"],
      "evidence": "live | constructed | cached",
      "fetched_at": null
    }
  ],
  "limitations": ["..."]
}
```

`null` for price / stock / lead_time means "not obtained"; never guess.

## Verification

- Every `link` is a real URL for the named distributor.
- A lookup returns at least LCSC and Mouser; a recommend returns both per candidate where
  the part is carried, and a cited spec basis per candidate.
- A `live` result requires an actual fetch (API call or page read) at answer time.
- Re-query before quoting stock/price; do not carry a stale number.

## Hard rules

- No fabricated MPNs, stock, prices, links, or compliance flags.
- A standard/region filter that cannot be satisfied is reported as a limitation, not filled.
- "Recommended" parts are suggestions with a cited spec basis, not a datasheet-certified
  selection, and not a substitute for the engineer's review.
- Keep credentials (Mouser API key) out of any result, prompt, or file you emit.
