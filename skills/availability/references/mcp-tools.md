# Availability MCP tools — specification

How the `availability` scope-wide tools are integrated into the v0.2 delivered agent. The
reference implementation lives in
[`scripts/availability_tools.py`](../scripts/availability_tools.py); the generator copies it
into the delivered project as `availability/availability_tools.py` and registers its
`MCP_TOOLS` on the single public entry point.

## Namespace and routing

| Tool | Purpose |
|---|---|
| `availability__lookup` | named chip + standards + region → purchase links (LCSC, Mouser mandatory) |
| `availability__recommend` | functional description → recommended part families + links |

- Scope-wide, loaded once — like `board__*`, not a per-device model. It reads **no** device
  model and produces **no** device model.
- The `availability__` namespace is reserved; reject any device ID or tool that collides with
  it, exactly as `board__` is reserved.
- The root `agent_mcp.py` merges `availability_tools.MCP_TOOLS` into its combined
  `MCP_TOOLS`, alongside device `<device_id>__*` and `board__<board_id>__*` tools.
- Root `manifest.json` records the module path and the two final tool names.

## Module contract

`availability/availability_tools.py` is self-contained (stdlib only) and exposes:

- `lookup(mpn, standards=[], region=None, quantity=1, currency=None, api_key_env="MOUSER_API_KEY") -> dict`
- `recommend(requirement, standards=[], region=None, api_key_env="MOUSER_API_KEY") -> dict`
- `MCP_TOOLS` (list of `{name, model, scenarios, description, params, source, fn}`) and
  `get_tools()`.

## Evidence and fabrication rules

Every result entry carries `evidence` ∈ {`live`, `constructed`, `cached`}:

- `live` — an actual API/page fetch at answer time; only then may `price`/`stock`/`lead_time`
  be non-null.
- `constructed` — the link is a real distributor search URL built from the part number; it is
  **not** a confirmation of stock, price, or even that the part is carried.
- `cached` — from a dated, auditable offer file (the reference module never produces this
  on its own).

`null` price/stock/lead_time means "not obtained" and must never be guessed. Standards are
reported only from a listing/datasheet; otherwise `not_stated` and listed as a limitation.

## Credentials

`MOUSER_API_KEY` is read only from the process environment via `api_key_env`. It must never
appear in a tool argument, result, log, or any emitted file.

## Capability projection

`capabilities/availability.md` is the scope-wide projection: the two tool names, the
distributor/standards/region mapping (see
[`sources.md`](sources.md)), the evidence rules, and the explicit limitation that
recommendations are heuristic candidates, not a datasheet-certified selection. It owns no
device state.
