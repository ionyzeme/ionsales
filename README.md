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

## Running on a remote mini PC (`ion`)

The devcontainer is host-agnostic and multi-arch — nothing in `.devcontainer/`
is tied to a particular machine, so it runs unchanged on a dedicated x86 mini PC
reached over Tailscale (MagicDNS host `ion`, user `iondocker`). The only work is
client-side wiring plus recreating the gitignored local files on the target box.

**Prereqs on `ion`:** Tailscale up, SSH enabled, **Docker Engine installed**, and
your laptop's SSH public key in `iondocker`'s `~/.ssh/authorized_keys`.

**1. SSH config** — add to `~/.ssh/config` on your laptop (not in this repo):

```ssh
Host ion
    HostName ion
    User iondocker
    # IdentityFile ~/.ssh/id_ed25519   # if you use a specific key
```

If the short name doesn't resolve, use the full MagicDNS name as `HostName`
(`ion.<your-tailnet>.ts.net` — see `tailscale status`).

**2. Verify** the path and that Docker is reachable:

```bash
tailscale ping ion
ssh ion 'docker version'
```

**3. Open the container on `ion`** (Remote-SSH path — recommended):

1. VS Code → **Remote-SSH: Connect to Host → `ion`**
2. Clone the repo on the mini PC: `git clone https://github.com/ionyzeme/ionsales.git`
3. Open the folder → **Dev Containers: Reopen in Container**

Files and the container both live on `ion`; the VS Code UI stays local.

> Alternative (keep editing in your local window, run only the container on `ion`):
> `docker context create iondev --docker "host=ssh://iondocker@ion"`, then set the
> VS Code `dev.containers.dockerHost` setting to `ssh://iondocker@ion` and use
> _Clone Repository in Container Volume_. Remote-SSH is less fiddly.

**4. First-run-on-`ion` checklist** — the gitignored local files don't travel with
the repo (they hold secrets), so recreate them inside the new container:

- `cp .devcontainer/devcontainer.env.example .devcontainer/devcontainer.env` — the
  build references it via `runArgs --env-file` and **won't start without it**. Fill in values.
- Recreate `.env`, or just re-run the `dataverse:dv-connect` flow.
- Re-do the two device-code sign-ins (DV CLI + `pac`) — the token caches are local
  to the container's home and don't carry over.

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
