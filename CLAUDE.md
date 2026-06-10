# Dynamics 365 Configuration & Customization — Build Context (Experiment)

> This is the `CLAUDE.md` for a D365 experimentation project. Rename it to `CLAUDE.md`
> at the root of the new repo. It is the single source of truth Claude reloads each
> session — keep it current as the project's shape changes.

## What this is
An experiment to test whether the "Claude writes, human reviews, iterate fast" method
that works for greenfield code also works for **Dynamics 365 system configuration and
customization**. The target environment is a **plain, vanilla sandbox** with **Sales
Enterprise** and **Microsoft Project Operations** installed. There is **no production
risk** — the sandbox is disposable and can be reset at will. This phase is about
learning what's achievable, not shipping.

## The one structural difference from a code project (read this first)
In normal software, the source of truth is files Claude can read and edit. In D365, the
default authoring surface is a **point-and-click web portal** (make.powerapps.com), and
the application lives as **metadata inside Dataverse** — almost none of it is local.
Claude reasons over files. So the central discipline of this project is:

> **Move as much of the relevant app surface as possible into files Claude can read,
> without dragging the entire managed-solution iceberg onto disk.**

Sales + Project Operations are thousands of pre-built tables/forms/views you did not
author. Do NOT materialise all of that. Curate the *slice* that matters. See the
three-layer model below.

## Build philosophy (carried over from what works)
- **Thin slice first.** Prove ONE small Sales/PO extension end-to-end (table/column →
  form → business rule/flow → maybe a plugin → packaged solution) before adding breadth.
- **Build in dependency order**, not runtime order. Data model (Dataverse tables/columns/
  relationships) first; UI, automation, and code on top.
- **Git is the source of truth, not the environment.** The unpacked solution YAML in the
  repo is canonical. The sandbox is disposable scratch — if it drifts or is reset, rebuild
  from `pac solution pack` + import.
- **Curate context.** A tight, hand/AI-maintained schema digest beats a 4,000-table dump.
  This file + `docs/schema/` are Claude's standing context.
- **Experiment boldly.** It's a throwaway sandbox: use MCP writes freely, iterate, reset
  when messy. The only discipline tax worth paying now is the publisher + single-solution
  rule (below), because it keeps the managed-promotion path open for free.

---

## The three-layer connection model (how Claude sees the app)
The MCP server alone is a *keyhole*, not a *map*. Use three complementary layers:

### Layer 1 — Dataverse MCP server (live, interactive keyhole)
Microsoft's official Dataverse MCP server; Claude Code is a supported client.
- **Endpoint:** `https://{yourorg}.crm.dynamics.com/api/mcp`
- **Connect (Claude Code):**
  ```bash
  claude mcp add dataverse -t stdio -- npx -y @microsoft/dataverse mcp https://{yourorg}.crm.dynamics.com
  ```
  Restart Claude Code; sign in interactively. It runs **as you** — it can only see what
  your security roles allow.
- **Admin prerequisite:** the MCP server + the Claude client must be **enabled per-
  environment** in the Power Platform admin center. It silently won't connect otherwise —
  this is the #1 setup gotcha.
- **Key tools** (current names — the surface changed recently):
  - `search` — keyword search over table **schemas / apps / skills** (metadata discovery)
  - `describe` — details for a table / record / schema / app (replaced `describe_table`,
    `list_tables`, `fetch`)
  - `read_query` — Dataverse **SQL `SELECT`** (filters/joins/aggregates; read-only)
  - `search_data` — search actual records (only if Dataverse search is enabled)
  - `create_record` / `update_record` / `delete_record`, `create_table` / `update_table` /
    `delete_table` (writes; delete needs explicit approval)
- **Good at:** interactive exploration + live data ("describe the `msdyn_project` table",
  "how many open opportunities have no project").
- **Weak at:** FormXml, views, business process flows, business rules, ribbon, site map,
  security-role privilege sets — i.e. much of "what the app *looks like*". It's also
  ephemeral (not in git). That's why Layers 2 & 3 exist.
- **⚠️ Billing:** since **15 Dec 2025**, Dataverse MCP tools are metered when called by an
  AI agent **created outside Copilot Studio** (Claude Code counts as outside), UNLESS your
  user has a qualifying **Dynamics 365 Premium** or **M365 Copilot** license. Check before
  leaning on it heavily.

### Layer 2 — Unpacked solution source in git (the editable codebase)
Install the **Power Platform CLI** (`pac`), authenticate once, pull *your* solution as files.
```bash
pac auth create --environment https://{yourorg}.crm.dynamics.com
pac solution list                         # see all solutions (Sales, Project Operations, Default, yours…)
pac solution clone --name mark_SalesPilot # → YAML source tree (clean git diffs, modern flows/canvas)
# after portal changes:
pac solution sync                         # pull latest env state back into the same tree
```
- Use **`clone`/`sync`** → **YAML source-control format** (not the legacy verbose XML).
- **Pull your slice, not the iceberg.** Only unpack your own unmanaged dev solution. Do
  **NOT** unpack Sales / Project Operations (managed, enormous, read-only noise) — reference
  those via Layers 1 & 3.
- **The loop:** build/click in portal → `pac solution sync` → commit → Claude reviews the
  diff and edits FormXml / business rules / flow JSON / plugins (C#) / PCF (TS) → `pac
  solution pack` → `pac solution import` → verify.
- Honest boundary: a brand-new table/form is often fastest seeded with a few portal clicks,
  then `sync` and handed to Claude to refine/extend. Claude's leverage is highest on
  **editing, extending, reviewing, codifying**, and on genuinely code-shaped artefacts
  (plugins, PCF, Power Fx, complex flow logic).

### Layer 3 — `$metadata` + a curated schema digest (the map)
This is what most directly answers "how does Claude understand the app." Two artefacts,
both committed to git:
- **3a. Canonical schema dump.** Save the CSDL doc to the repo as a greppable reference:
  ```
  GET https://{yourorg}.api.crm.dynamics.com/api/data/v9.2/$metadata
  ```
  Describes every table/column/relationship/action/function. Large — don't paste wholesale;
  `grep` it for exact logical/schema names. For plugin work, also `pac modelbuilder build`
  for strongly-typed early-bound C# classes.
- **3b. The curated digest — the most important file you'll maintain.** A hand/AI-curated
  Markdown map of just your slice, in `docs/schema/`. Generate it via Layer 1, e.g.:
  > "Using the Dataverse MCP, `describe` the `opportunity`, `msdyn_project`,
  > `msdyn_projectteam`, and `quote` tables. For each, write into
  > `docs/schema/sales-pilot.md`: purpose, the columns I'll use (logical name, type,
  > required), key relationships, relevant choice sets, and any business process flows that
  > touch them. Mark out-of-box vs custom."

  Claude reloads *this*, not the 4,000-table managed model.

### How the layers work together (a typical task)
1. **Map (L3):** read `docs/schema/*.md` for the shape of the tables involved.
2. **Keyhole (L1):** `describe` / `read_query` anything the digest doesn't cover; sample live rows.
3. **Codebase (L2):** edit the unpacked source in `mark_SalesPilot`; `pack` + `import`; verify.
4. Update the digest to reflect the change. Loop closes.

---

## ALM model — unmanaged dev → managed distribution (keep the path open)
The sandbox is disposable, but a few rules keep clean managed promotion free:
- **Publisher + prefix on day one.** Create them before building anything; everything gets
  stamped (`mark_…`). This is what makes a clean managed export possible.
- **One unmanaged solution = unit of work AND unit of distribution.** Everything you build
  goes in `mark_SalesPilot`. **NEVER build in the Default solution** — leaked components
  can't be cleanly exported as managed. This is *the* trap.
- **Extend pre-built tables by segmentation.** When you customize a Sales/PO table, add only
  the **pieces you change** (the new column/form), not the whole managed table. Your managed
  export then layers cleanly on top of Sales + Project Operations downstream.
- **Managed is only ever an output.** Dev stays unmanaged forever:
  ```bash
  pac solution export --name mark_SalesPilot --managed       # from the dev source
  pac solution import --path mark_SalesPilot_managed.zip      # into a QA env (Sales+PO installed first)
  ```
  Never import managed back into dev. QA = Sales + Project Operations + your managed layer —
  a faithful rehearsal of production.
- **The dev→QA→prod pipeline is a LATER step.** Bolt it on once a slice proves out; don't
  build it speculatively during experimentation.

---

## Recommended repo layout
```
/                         (new repo root)
├── CLAUDE.md             (this file, renamed)
├── docs/
│   ├── schema/           (Layer 3b — curated per-slice schema digests)
│   │   └── sales-pilot.md
│   ├── metadata.xml      (Layer 3a — $metadata dump, greppable reference)
│   └── decisions.md      (running log of what was tried + why)
├── solutions/
│   └── mark_SalesPilot/  (Layer 2 — pac solution clone YAML tree; the editable source)
├── src/                  (optional code-shaped artefacts)
│   ├── plugins/          (C# plugins, early-bound classes from pac modelbuilder)
│   └── pcf/              (PCF controls, TypeScript)
└── scripts/              (pac/Web API helper scripts, sample-data generators)
```

## Gotchas to keep loaded
- **Managed vs unmanaged:** you can only edit your own *unmanaged* solution. Sales/PO
  components are managed (read-only) — extend, don't edit in place.
- **Don't materialise the iceberg:** never unpack the full Sales/PO solutions into git.
- **Security roles bound everything:** MCP and `pac` run as you. "Can't see a table" is
  usually a role/privilege issue, not a bug.
- **MCP writes are real writes** — fine here (disposable sandbox), but know it.
- **`read_query` is SELECT-only** (TDS) — analytics, not mutation. Mutations go through
  `create/update_record` or the solution pack/import path.
- **YAML format needs a current `pac`** (Microsoft.PowerApps.CLI ≥ 2.4.1). Run `pac install
  latest` if `clone`/`sync` output looks like legacy XML.

---

## Setup checklist (do in order)
1. **Admin:** enable Dataverse MCP server + Claude Code client for the sandbox env (admin
   center). Confirm MCP licensing/metering.
2. **Install `pac` CLI**; `pac auth create --environment <url>`.
3. **Create publisher + prefix** (`mark_`) and an **unmanaged solution** `mark_SalesPilot`
   in the portal.
4. **Connect MCP** in Claude Code; smoke-test ("show me the tables", "describe opportunity").
5. **`pac solution clone --name mark_SalesPilot`** into the repo; commit.
6. **Dump `$metadata`** → `docs/metadata.xml`; optional `pac modelbuilder build` for plugins.
7. **Generate `docs/schema/sales-pilot.md`** via the MCP.
8. **Pick the thin slice** and run the build loop.

## First thin slice (proposed — swap freely)
A small extension that exercises every layer: add a lightweight **"engagement risk"**
concept to `opportunity` (a choice column + a justification text column), surface it on the
Opportunity main form, drive a **business rule** (e.g. high risk requires justification),
and a **Power Automate flow** that flags the linked **Project Operations project** when an
opportunity closes as won at high risk. This touches: column/relationship metadata, FormXml,
a business rule, a flow, and the managed-export packaging — a complete spine on real
Sales+PO surface, small enough to finish.

## Definition of done (for the experiment)
- The thin slice works end-to-end in the sandbox.
- Its entire definition lives in git (`solutions/mark_SalesPilot`), rebuildable via
  `pac solution pack` + `import`.
- A managed export installs cleanly onto a second (QA) environment that has Sales + Project
  Operations — proving the distribution path.
- `docs/decisions.md` captures what worked, what didn't, and where Claude's leverage was
  high vs low — the actual output of the experiment.
