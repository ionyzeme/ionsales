# ionsales — D365 configuration & customization experiment

An experiment testing whether the "Claude writes, human reviews, iterate fast"
loop works for **Dynamics 365 Sales Enterprise + Project Operations**
configuration on a disposable sandbox. Full context, philosophy, and the
three-layer connection model live in **[`CLAUDE.md`](CLAUDE.md)** — read that first.

## Quick start

1. **Open in the devcontainer** (VS Code → _Reopen in Container_). It provisions
   the `pac` CLI, .NET 8 SDK, Node LTS, PowerShell, and the Power Platform Tools.
2. **Set your environment URL** — see [`docs/connection.md`](docs/connection.md) §0.
3. **Enable the Dataverse MCP + Claude Code client** for the env in the admin
   center (the #1 gotcha).
4. **Connect & smoke-test** the MCP and `pac auth` per `docs/connection.md`.
5. **Pick the thin slice** (`CLAUDE.md` → First thin slice) and run the loop.

## Layout

| Path | Purpose |
|------|---------|
| [`CLAUDE.md`](CLAUDE.md) | Single source of truth — reloaded each session |
| [`.devcontainer/`](.devcontainer/) | D365 toolchain (pac, .NET, Node, PowerShell) |
| [`.mcp.json`](.mcp.json) | Dataverse MCP server config (Layer 1) |
| [`docs/connection.md`](docs/connection.md) | Connection / auth setup for all 3 layers |
| [`docs/schema/`](docs/schema/) | Curated per-slice schema digests (Layer 3b) |
| [`docs/decisions.md`](docs/decisions.md) | Running log of what was tried + why |
| [`solutions/`](solutions/) | Unpacked solution YAML — the editable source (Layer 2) |
| [`src/plugins/`](src/plugins/) · [`src/pcf/`](src/pcf/) | Code-shaped artefacts |
| [`scripts/`](scripts/) | pac / Web API helpers, sample-data generators |
