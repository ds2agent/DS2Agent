# Availability — sources

Search endpoints, per-distributor attributes, and the standards/region mapping used by the
lookup path.

## Distributors

### LCSC (mandatory)

- Search (web): `https://www.lcsc.com/search?q=<url-encoded-query>`
- Part page: `https://www.lcsc.com/product-detail/<slug>.html` (slug comes from a search result)
- JSON endpoint (unofficial, may change without notice):
  `https://wmsc.lcsc.com/wmsc/search/global?keyword=<url-encoded-query>`
  returns `{"result": {"productList": [{...}]}}` with `productCode`, `productModel`,
  `productName`, `stockNumber`, `minOrderNum`, `productPrice`, `brandNameEn`.

Attributes per listing: stock (`stockNumber`), price (CNY), brand, and compliance flags
(RoHS/REACH) shown on the detail page. Strongest for CN and global prototyping.

### Mouser (mandatory)

- Search (web): `https://www.mouser.com/c/?q=<url-encoded-query>`
- Search API (requires `MOUSER_API_KEY`; a key is scoped to one region):
  - Part number: `POST https://api.mouser.com/api/v1/search/partnumber?apiKey=<key>`
    body `{"SearchByPartRequest":{"mouserPartNumber":"<mpn>","partSearchOptions":"Exact"}}`
  - Keyword: `POST https://api.mouser.com/api/v1/search/keyword?apiKey=<key>`
    body `{"SearchByKeywordRequest":{"keyword":"<query>","records":50,"startingRecord":0,"searchOptions":"None"}}`
  - Part number + manufacturer: `POST https://api.mouser.com/api/v1/search/partnumberandmanufacturer?apiKey=<key>`
    body `{"SearchByPartMfrRequest":{"mouserPartNumber":"<mpn>","manufacturer":"<mfr>"}}`

Typical part fields in the response (`SearchResults.Parts[]`): `Manufacturer`,
`ManufacturerPartNumber`, `MouserPartNumber`, `Availability` ("N In Stock"),
`PricingBreaks[]`, `LeadTime`, `ProductDetailUrl`, `LifecycleStatus`, and, where populated,
`RoHSStatus` and `REACHStatus`.

Region subdomains / keys: `mouser.com` (US), `mouser.cn` (CN), `mouser.co.uk`, `mouser.de`,
`mouser.fr`, `mouser.it`, `mouser.co.jp`, `mouser.kr`, `mouser.tw`, `mouser.com.tr`.

The v0.1 runtime already ships a strict Mouser normalizer:
`python -m ds2agent supply --mpn <mpn> --api-key-env MOUSER_API_KEY`.

### Optional (region / standards driven)

| Distributor | Search URL |
|---|---|
| Digi-Key | `https://www.digikey.com/en/products/result?keywords=<url-encoded>` (API needs OAuth) |
| TI store | `https://www.ti.com/store/ti/en/p/search/?searchTerm=<url-encoded>` |
| Arrow | `https://www.arrow.com/en/products/search?q=<url-encoded>` |
| Farnell / element14 (EU) | `https://www.newark.com/search?st=<url-encoded>` |
| TME (EU) | `https://www.tme.eu/en/katalog/?search=<url-encoded>` |

## Standards → filter

| Standard | Where it appears | Rule |
|---|---|---|
| RoHS | Mouser `RoHSStatus`, LCSC detail flag, datasheet | claim only from listing/datasheet |
| REACH / SVHC | Mouser `REACHStatus`, LCSC detail, datasheet | claim only from listing |
| AEC-Q100 / AEC-Q200 | datasheet / part attribute | automotive grade; cite the datasheet |
| UL | datasheet / listing | cite source |
| Temperature grade | datasheet operating range | commercial 0..+70 °C, industrial −40..+85 °C, automotive −40..+125 °C |

A standard the listing does not state is reported as `not_stated`, never implied.

## Region → distributor / currency

| Region | Primary distributors | Currency |
|---|---|---|
| CN | LCSC, Mouser.cn | CNY |
| US / NA | Mouser, Digi-Key, TI, Arrow | USD |
| EU | Mouser.eu, Farnell/element14, RS, TME | EUR / GBP |
| JP | Mouser, Digi-Key, CoreStaff | JPY |

Region changes local stock and lead time; prefer a distributor with local stock for the
target region and record which region each link targets.
