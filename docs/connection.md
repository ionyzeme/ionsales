# Connection details & first-run setup

How this repo connects to the D365 sandbox across the three layers in `CLAUDE.md`.
**Fill in your environment URL first** (one place: `.devcontainer/devcontainer.env`).

## 0. One value to fill in

```bash
cp .devcontainer/devcontainer.env.example .devcontainer/devcontainer.env
# edit it: set DATAVERSE_URL to your sandbox org URL, e.g.
#   DATAVERSE_URL=https://org12345.crm.dynamics.com
```

Find the URL in the [Power Platform admin center](https://admin.powerplatform.microsoft.com)
→ your environment → **Details**, or in make.powerapps.com → **Settings →
Developer resources**. Then **Rebuild Container** in VS Code. `DATAVERSE_URL`
is now visible to both the Dataverse MCP (`.mcp.json`) and `pac` scripts.

## Admin prerequisite (do this before anything connects)

In the Power Platform admin center, **enable the Dataverse MCP server _and_ the
Claude Code client for this environment**. Without it the MCP silently fails to
connect — the #1 setup gotcha (`CLAUDE.md` → Layer 1). Also confirm MCP
metering/licensing (Dataverse MCP is metered for non-Copilot agents since
15 Dec 2025 unless you hold D365 Premium / M365 Copilot).

## Layer 1 — Dataverse MCP (live keyhole)

Configured in [`.mcp.json`](../.mcp.json) — Claude Code auto-discovers it on
session start. It expands `${DATAVERSE_URL}`; if unset it falls back to a
`YOURORG` placeholder (edit `.mcp.json` directly if you prefer).

On first use Claude Code prompts you to sign in interactively (browser/device
code). The server runs **as you** — it only sees what your security roles allow.
Smoke test: _"search the Dataverse for the opportunity table"_, then
_"describe the opportunity table"_.

## Layer 2 — Power Platform CLI (`pac`) — editable source

`pac` is installed in the devcontainer. Authenticate once (device-code flow,
works headless in the container):

```bash
pac auth create --environment "$DATAVERSE_URL"
pac auth list
pac solution list                          # find your unmanaged solution
pac solution clone --name inz_SalesPilot   # → solutions/inz_SalesPilot (YAML)
# after portal edits:
pac solution sync                           # pull env changes back into the tree
```

Run `clone`/`sync` from `solutions/`. Unpack **only your own unmanaged
solution** — never Sales / Project Operations (managed iceberg).

## Layer 3 — `$metadata` dump + curated digest

```bash
# 3a — greppable schema reference (requires a valid pac auth / bearer token)
curl -s -H "Authorization: Bearer $(pac auth token 2>/dev/null)" \
  "$DATAVERSE_API_URL/api/data/v9.2/\$metadata" -o docs/metadata.xml
```

- **3b** — maintain [`docs/schema/sales-pilot.md`](schema/sales-pilot.md) by hand
  + MCP. This is Claude's standing map.

## Auth model summary

| Layer | Tool | Auth | Runs as |
|-------|------|------|---------|
| 1 | Dataverse MCP | Interactive sign-in on first call | You |
| 2 | `pac` CLI | `pac auth create` (device code) | You |
| 3a | Web API `$metadata` | Bearer token from `pac auth token` | You |

All three are bounded by your security roles. "Can't see a table" is almost
always a role/privilege issue, not a bug.
