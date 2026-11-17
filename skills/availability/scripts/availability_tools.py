"""Scope-wide availability tools for the v0.2 delivered agent.

Two namespaced tools, no device model required:

* ``availability__lookup``    — named chip + standards + region -> purchase links
                                (LCSC and Mouser are mandatory).
* ``availability__recommend`` — functional description -> recommended part families
                                plus purchase links.

Evidence-first and fabrication-free: ``price``/``stock``/``lead_time`` are ``None``
unless a live response supplies them. Every link is a real distributor URL and carries an
``evidence`` tag — ``live`` (fetched now), ``constructed`` (built from the part number,
not yet confirmed), or ``cached`` (from a dated offer file; not produced here).

API keys
--------

Mouser is the only keyed distributor here. ``MOUSER_API_KEY`` is read **only** from the
process environment (never from a tool argument, result, or log). One Mouser key is scoped
to one regional site, so the key itself determines the region and currency of the live
result; ``region`` still selects the fallback distributor set. With a key present, ``lookup``
and ``recommend`` return live stock/price/lead-time and RoHS/REACH flags; without it they
return ``constructed`` search links and ``null`` values.

LCSC has no official public API key; it is queried through the unofficial JSON endpoint and
falls back to a constructed search link on any failure.

Self-contained (stdlib only). Import and merge ``MCP_TOOLS`` into the root ``agent_mcp.py``.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

MOUSER_PARTNUMBER_ENDPOINT = "https://api.mouser.com/api/v1/search/partnumber"
MOUSER_KEYWORD_ENDPOINT = "https://api.mouser.com/api/v1/search/keyword"
LCSC_JSON_ENDPOINT = "https://wmsc.lcsc.com/wmsc/search/global"

_DEFAULT_TIMEOUT = 20.0


def _q(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def _search_url(distributor: str, query: str) -> str:
    if distributor == "lcsc":
        return f"https://www.lcsc.com/search?q={_q(query)}"
    if distributor == "mouser":
        return f"https://www.mouser.com/c/?q={_q(query)}"
    if distributor == "digikey":
        return f"https://www.digikey.com/en/products/result?keywords={_q(query)}"
    if distributor == "ti":
        return f"https://www.ti.com/store/ti/en/p/search/?searchTerm={_q(query)}"
    if distributor == "arrow":
        return f"https://www.arrow.com/en/products/search?q={_q(query)}"
    raise ValueError(f"unknown distributor: {distributor}")


_REGION_DISTRIBUTORS = {
    "CN": ["lcsc", "mouser"],
    "US": ["mouser", "digikey", "ti", "arrow"],
    "EU": ["mouser", "digikey", "arrow"],
    "JP": ["mouser", "digikey"],
}


def _region_list(region: str | None) -> list[str]:
    if region is None:
        return ["lcsc", "mouser"]  # mandatory minimum
    key = region.upper()
    return _REGION_DISTRIBUTORS.get(key, ["lcsc", "mouser"])


def _http_json(url: str, timeout: float, body: dict | None = None) -> dict:
    data = None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers=headers, method="POST" if data else "GET"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _lcsc_live(mpn: str, timeout: float) -> list[dict]:
    """Live LCSC lookup via the unofficial JSON endpoint. Empty on any failure."""
    url = f"{LCSC_JSON_ENDPOINT}?keyword={_q(mpn)}"
    try:
        payload = _http_json(url, timeout)
    except (urllib.error.URLError, OSError, ValueError, KeyError, json.JSONDecodeError):
        return []
    result = payload.get("result") if isinstance(payload, dict) else None
    products = result.get("productList") if isinstance(result, dict) else None
    if not isinstance(products, list):
        return []
    out = []
    for p in products:
        if not isinstance(p, dict):
            continue
        code = p.get("productCode")
        model = p.get("productModel")
        if not code or not model:
            continue
        out.append({
            "mpn": model,
            "manufacturer": p.get("brandNameEn"),
            "distributor": "lcsc",
            "link": f"https://www.lcsc.com/product-detail/{code}.html",
            "price": {"amount": _str_or_none(p.get("productPrice")), "currency": "CNY"},
            "stock": _int_or_none(p.get("stockNumber")),
            "lead_time": None,
            "standards": [],
            "evidence": "live",
            "fetched_at": None,
        })
    return out


def _normalize_mouser_parts(payload: Any, quantity: int, currency: str | None) -> list[dict]:
    if not isinstance(payload, dict) or payload.get("Errors"):
        return []
    search = payload.get("SearchResults")
    parts = search.get("Parts") if isinstance(search, dict) else None
    if not isinstance(parts, list):
        return []
    out = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        standards = []
        if part.get("RoHSStatus"):
            standards.append("RoHS")
        if part.get("REACHStatus"):
            standards.append("REACH")
        out.append({
            "mpn": part.get("ManufacturerPartNumber"),
            "manufacturer": part.get("Manufacturer"),
            "distributor": "mouser",
            "link": part.get("ProductDetailUrl"),
            "price": _select_price(part.get("PricingBreaks"), quantity, currency),
            "stock": _stock_number(part.get("Availability")),
            "lead_time": part.get("LeadTime"),
            "standards": standards,
            "evidence": "live",
            "fetched_at": None,
        })
    return out


def _mouser_live(mpn: str, api_key: str, quantity: int, currency: str | None,
                 timeout: float) -> list[dict]:
    url = f"{MOUSER_PARTNUMBER_ENDPOINT}?apiKey={_q(api_key)}"
    body = {"SearchByPartRequest": {"mouserPartNumber": mpn, "partSearchOptions": "Exact"}}
    try:
        payload = _http_json(url, timeout, body)
    except (urllib.error.URLError, OSError, ValueError, KeyError, json.JSONDecodeError):
        return []
    return _normalize_mouser_parts(payload, quantity, currency)


def _mouser_keyword_live(keyword: str, api_key: str, quantity: int, currency: str | None,
                         timeout: float, records: int = 20) -> list[dict]:
    url = f"{MOUSER_KEYWORD_ENDPOINT}?apiKey={_q(api_key)}"
    body = {"SearchByKeywordRequest": {
        "keyword": keyword, "records": records, "startingRecord": 0,
        "searchOptions": "None",
    }}
    try:
        payload = _http_json(url, timeout, body)
    except (urllib.error.URLError, OSError, ValueError, KeyError, json.JSONDecodeError):
        return []
    return _normalize_mouser_parts(payload, quantity, currency)


def _constructed(distributor: str, query: str) -> dict:
    return {
        "mpn": query,
        "manufacturer": None,
        "distributor": distributor,
        "link": _search_url(distributor, query),
        "price": {"amount": None, "currency": None},
        "stock": None,
        "lead_time": None,
        "standards": [],
        "evidence": "constructed",
        "fetched_at": None,
    }


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


_STOCK_RE = re.compile(r"^\s*(\d{1,3}(?:,\d{3})+|\d+)\s+In\s+Stock\b", re.IGNORECASE)


def _stock_number(text: Any) -> int | None:
    if not isinstance(text, str):
        return None
    match = _STOCK_RE.match(text)
    return int(match.group(1).replace(",", "")) if match else None


def _select_price(breaks: Any, quantity: int, currency: str | None) -> dict | None:
    if not isinstance(breaks, list) or not breaks:
        return None
    selected = None
    for entry in breaks:
        if not isinstance(entry, dict):
            continue
        qty = _int_or_none(entry.get("Quantity"))
        amount = _str_or_none(entry.get("Price"))
        cur = _str_or_none(entry.get("Currency"))
        if amount is None:
            continue
        if selected is None:
            selected = {"amount": amount, "currency": cur}
        if qty is not None and qty <= quantity:
            selected = {"amount": amount, "currency": cur}
    return selected


def _lookup_mouser(mpn: str, api_key: str | None, quantity: int, currency: str | None,
                   timeout: float) -> list[dict]:
    if not api_key:
        return [_constructed("mouser", mpn)]
    live = _mouser_live(mpn, api_key, quantity, currency, timeout)
    if not live:
        # Exact search missed (family / non-exact MPN): retry as a keyword search.
        live = _mouser_keyword_live(mpn, api_key, quantity, currency, timeout)
    return live or [_constructed("mouser", mpn)]


def lookup(mpn: str, standards: list[str] | None = None, region: str | None = None,
           quantity: int = 1, currency: str | None = None,
           api_key_env: str = "MOUSER_API_KEY", timeout: float = _DEFAULT_TIMEOUT) -> dict:
    """availability__lookup — purchase links for a named chip."""
    if not isinstance(mpn, str) or not mpn.strip():
        return {"error": "mpn must be a non-empty string"}
    if type(quantity) is not int or quantity <= 0:
        return {"error": "quantity must be a positive integer"}
    standards = [s for s in (standards or []) if isinstance(s, str) and s.strip()]
    region = region.upper() if isinstance(region, str) and region.strip() else None
    api_key = os.environ.get(api_key_env) if isinstance(api_key_env, str) else None

    results: list[dict] = []
    results.extend(_lcsc_live(mpn, timeout) or [_constructed("lcsc", mpn)])
    results.extend(_lookup_mouser(mpn, api_key, quantity, currency, timeout))

    region_note = (f"unknown region '{region}'; defaulted to LCSC + Mouser"
                   if region is not None and region not in _REGION_DISTRIBUTORS else None)
    return {
        "kind": "lookup",
        "chip": mpn,
        "standards": standards,
        "region": region,
        "results": results,
        "limitations": _limitations(standards, results, region_note),
    }


def recommend(requirement: str, standards: list[str] | None = None,
              region: str | None = None, api_key_env: str = "MOUSER_API_KEY",
              timeout: float = _DEFAULT_TIMEOUT) -> dict:
    """availability__recommend — part families for a described function."""
    if not isinstance(requirement, str) or not requirement.strip():
        return {"error": "requirement must be a non-empty string"}
    standards = [s for s in (standards or []) if isinstance(s, str) and s.strip()]
    region = region.upper() if isinstance(region, str) and region.strip() else None
    api_key = os.environ.get(api_key_env) if isinstance(api_key_env, str) else None

    results: list[dict] = []

    # With a key: discover real parts matching the whole requirement (live).
    if api_key:
        for part in _mouser_keyword_live(requirement, api_key, 1, None, timeout):
            part["basis"] = "Mouser keyword search on the requirement"
            results.append(part)

    # Built-in family candidates with LCSC + Mouser (and other region distributors).
    for family in _match_families(requirement):
        for distributor in _region_list(region):
            if distributor == "lcsc":
                live = _lcsc_live(family["mpn"], timeout)
                entries = live or [_constructed("lcsc", family["mpn"])]
            elif distributor == "mouser" and api_key:
                live = _mouser_live(family["mpn"], api_key, 1, None, timeout)
                entries = live or [_constructed("mouser", family["mpn"])]
            else:
                entries = [_constructed(distributor, family["mpn"])]
            for e in entries:
                e["basis"] = family["basis"]
                results.append(e)

    return {
        "kind": "recommend",
        "chip": requirement,
        "standards": standards,
        "region": region,
        "results": results,
        "limitations": _recommend_limitations(standards, api_key is not None),
    }


def _recommend_limitations(standards: list[str], live: bool) -> list[str]:
    notes = ["Recommendations are heuristic candidates; verify spec match on the listing "
             "before ordering."]
    if not live:
        notes.append("No Mouser API key; stock/price are not fetched (constructed links).")
    if standards:
        notes.append(f"Standards {', '.join(standards)} must be confirmed per listing.")
    return notes


_FAMILIES = [
    {"kw": ("temperature", "humidity"), "mpn": "SHT31-DIS-B", "manufacturer": "Sensirion",
     "basis": "environmental sensor, I2C"},
    {"kw": ("pressure", "barometric"), "mpn": "BMP280", "manufacturer": "Bosch",
     "basis": "barometric pressure sensor, I2C/SPI"},
    {"kw": ("accelerometer", "accel", "imu", "gyro"), "mpn": "ADXL345", "manufacturer": "ADI",
     "basis": "3-axis accelerometer, I2C/SPI"},
    {"kw": ("current", "power monitor", "power meter"), "mpn": "INA219", "manufacturer": "TI",
     "basis": "bidirectional current/power monitor, I2C"},
    {"kw": ("load cell", "weigh", "bridge", "strain"), "mpn": "HX711", "manufacturer": "AVIA",
     "basis": "24-bit weigh-scale ADC"},
    {"kw": ("eeprom", "memory", "storage"), "mpn": "AT24C256C", "manufacturer": "Microchip",
     "basis": "256-Kbit I2C EEPROM"},
    {"kw": ("gpio", "io expander", "i/o expander"), "mpn": "PCF8574T", "manufacturer": "NXP",
     "basis": "8-bit I2C I/O expander"},
    {"kw": ("dac", "digital to analog"), "mpn": "MCP4725", "manufacturer": "Microchip",
     "basis": "12-bit DAC with EEPROM, I2C"},
    {"kw": ("mux", "multiplexer", "switch", "i2c switch"), "mpn": "PCA9548A", "manufacturer": "TI",
     "basis": "8-channel I2C switch"},
    {"kw": ("rtc", "real time clock", "clock"), "mpn": "DS3231", "manufacturer": "Maxim/ADI",
     "basis": "I2C RTC/TCXO"},
    {"kw": ("nfc", "rfid", "near field"), "mpn": "PN532", "manufacturer": "NXP",
     "basis": "NFC controller"},
    {"kw": ("magnetometer", "magnetic", "compass"), "mpn": "QMC5883L", "manufacturer": "QST",
     "basis": "3-axis magnetometer, I2C"},
]


def _match_families(requirement: str) -> list[dict]:
    text = requirement.casefold()
    matched = [f for f in _FAMILIES if any(k in text for k in f["kw"])]
    return matched if matched else _FAMILIES[:3]


def _limitations(standards: list[str], results: list[dict], extra: str | None) -> list[str]:
    notes: list[str] = []
    if standards:
        live = [r for r in results if r.get("evidence") == "live"]
        if not live:
            notes.append(
                f"Standards {', '.join(standards)} require live confirmation; no live "
                "listing was fetched, so they are reported not_stated.")
    if extra:
        notes.append(extra)
    return notes


def _tool(name: str, description: str, params: dict, fn) -> dict:
    return {
        "name": name,
        "model": "availability",
        "scenarios": ["mcp-interface"],
        "description": description,
        "params": params,
        "source": "availability/SKILL.md",
        "fn": fn,
    }


_LOOKUP_PARAMS = {
    "type": "object",
    "properties": {
        "mpn": {"type": "string", "description": "Part number / orderable part / family."},
        "standards": {"type": "array", "items": {"type": "string"},
                      "description": "Compliance standards, e.g. RoHS, REACH, AEC-Q100."},
        "region": {"type": "string", "enum": ["CN", "US", "EU", "JP"],
                   "description": "Target region; drives distributor and currency."},
        "quantity": {"type": "integer", "minimum": 1, "default": 1},
        "currency": {"type": "string", "description": "ISO currency code, e.g. USD."},
        "api_key_env": {"type": "string", "default": "MOUSER_API_KEY",
                        "description": "Env var holding the Mouser API key (never the key itself)."},
    },
    "required": ["mpn"],
}

_RECOMMEND_PARAMS = {
    "type": "object",
    "properties": {
        "requirement": {"type": "string", "description": "Free-text functional requirement."},
        "standards": {"type": "array", "items": {"type": "string"}},
        "region": {"type": "string", "enum": ["CN", "US", "EU", "JP"]},
        "api_key_env": {"type": "string", "default": "MOUSER_API_KEY",
                        "description": "Env var holding the Mouser API key (never the key itself)."},
    },
    "required": ["requirement"],
}

MCP_TOOLS = [
    _tool("availability__lookup",
          "Purchase links (LCSC, Mouser, ...) for a named chip, filtered by standards and region.",
          _LOOKUP_PARAMS, lookup),
    _tool("availability__recommend",
          "Recommend part families for a described function, with LCSC/Mouser links.",
          _RECOMMEND_PARAMS, recommend),
]


def get_tools() -> list[dict]:
    return MCP_TOOLS
