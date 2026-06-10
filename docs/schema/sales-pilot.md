# Schema digest — Sales Pilot slice (Layer 3b)

> A hand/AI-curated map of *just our slice*, not the 2,000-table managed model.
> Claude reloads **this**, not `docs/metadata.xml`. See `CLAUDE.md` → Layer 3.
>
> **Source:** generated 2026-06-10 from the live env `org27cdc0fd.crm11.dynamics.com`
> (org ESP-PO) via the Web API metadata endpoints. Counts: opportunity 197 attrs,
> msdyn_project 195, msdyn_projectteam 82, quote 172 — only the **curated** columns
> are listed below. `C` = custom, `O` = out-of-box (OOB). Re-pull after schema changes.

Legend: **req** = RequiredLevel — `ApplicationRequired` (mandatory in UI),
`SystemRequired` (always), `Recommended`, `None`.

---

## `account` — Account  *(OOB, extended by our slice)*
The customer. Primary id `accountid`, name `name`. EntitySet `accounts`. **This is the
subject of the Sales Intelligence Brief slice** — we segment three `ion_` columns onto it
(solution `ion_SalesPilot`, publisher `ion`). Only our additions are listed; account has
~200 OOB columns referenced elsewhere as needed.

### Our columns (custom — `ion_`)
| Logical name | Type | Req | Label | Notes |
|---|---|---|---|---|
| `ion_brief` | Memo (4000) | None | Brief | The briefing a seller reads. Manual today; flow/AI-populated later. |
| `ion_accounthealth` | Choice (local) | None | Account Health | Headline signal. **100000000 Healthy · 100000001 Watch · 100000002 At Risk** |
| `ion_briefupdatedon` | DateTime (UserLocal) | None | Brief Updated On | Freshness — when the brief was last written. |

### Surfaced on
- **Account** main form (`8448b78f-8f42-454e-8e2a-f8196b0419af`) → new **"Sales Intelligence"** tab
  (Account Health, Brief Updated On, Brief). Published; form is in `ion_SalesPilot`.

### Enforcement (built — C# plug-in, no portal)
`Ion.SalesPilot.Plugins.AccountBriefGuard` (source: [src/plugins/](../../src/plugins/Ion.SalesPilot.Plugins/)),
registered sync **pre-operation** on account **Create + Update** (Update step filtered to
`ion_accounthealth,ion_brief`, with a `PreImage`):
- **Validation:** if effective `ion_accounthealth = At Risk` and `ion_brief` is empty → save is blocked.
- **Freshness:** when `ion_brief` is written/changed → `ion_briefupdatedon` auto-stamped (UTC).

### AI population layer (built — `scripts/generate_brief.py`)
Reads the account + its open opportunities + contacts, asks **Claude** (`claude-opus-4-8`,
structured output) to write the brief and rate health, then writes `ion_brief` +
`ion_accounthealth` back — which trips `AccountBriefGuard` to auto-stamp `ion_briefupdatedon`.
Run: `python scripts/generate_brief.py --account "Northwind Traders" --write`
(`--dry-run` to preview context, `--stub` to test offline). Needs `ANTHROPIC_API_KEY` in `.env`.

> Demo data seeded: account **Northwind Traders** + 2 contacts + 3 opportunities.

---

## `opportunity` — Opportunity  *(OOB, UserOwned)*
A potential revenue-generating deal. Primary id `opportunityid`, primary name `name`
(labelled "Topic"). EntitySet `opportunities`. **0 records** in env (fresh sandbox).
Project Operations stamps it with `msdyn_*` sales columns.

### Columns
| Kind | Logical name | Type | Req | Label |
|---|---|---|---|---|
| O | `name` | String | ApplicationRequired | Topic |
| O | `customerid` | Customer | ApplicationRequired | Potential Customer (→ account/contact) |
| O | `parentaccountid` | Lookup | None | Account |
| O | `parentcontactid` | Lookup | None | Contact |
| O | `estimatedvalue` | Money | None | Est. revenue |
| O | `estimatedclosedate` | DateTime | None | Est. close date |
| O | `actualvalue` | Money | None | Actual Revenue |
| O | `actualclosedate` | DateTime | None | Actual Close Date |
| O | `closeprobability` | Integer | None | Probability |
| O | `opportunityratingcode` | Picklist | None | Rating (Hot/Warm/Cold) |
| O | `budgetamount` | Money | None | Budget amount |
| O | `description` | Memo | None | Description |
| O | `statecode` | State | SystemRequired | Status |
| O | `statuscode` | Status | None | Status Reason |
| O | `transactioncurrencyid` | Lookup | ApplicationRequired | Currency |
| O | `ownerid` | Owner | SystemRequired | Owner |
| C | `msdyn_ordertype` | Picklist | Recommended | Type |
| C | `msdyn_accountmanagerid` | Lookup | Recommended | Account Manager (→ systemuser) |
| C | `msdyn_contractorganizationalunitid` | Lookup | Recommended | Contracting Unit |
| C | `msdyn_forecastcategory` | Picklist | None | Forecast category |
| C | `msdyn_opportunitykpiid` | Lookup | None | KPI |
| C | `msdyn_predictivescoreid` | Lookup | None | Predictive Score |
| C | `msdyn_segmentid` | Lookup | None | Segment Id |
| C | `msdyn_gdproptout` | Boolean | None | GDPR Optout |

_Deprecated custom cols present but skip: `msdyn_opportunitygrade`, `msdyn_opportunityscore(trend)`,
`msdyn_scorehistory`, `msdyn_scorereasons`, `msdyn_similaropportunities`._

### Choice sets
- `statecode`: 0 Open · 1 Won · 2 Lost
- `statuscode`: 1 In Progress · 2 On Hold · 3 Won · 4 Canceled · 5 Out-Sold
- `opportunityratingcode`: 1 Hot · 2 Warm · 3 Cold

### Key relationships
- **M2O (lookups):** `customerid`→account/contact · `parentaccountid`→account ·
  `parentcontactid`→contact · `transactioncurrencyid`→transactioncurrency ·
  `msdyn_accountmanagerid`→systemuser
- **O2M (children):** `quote.opportunityid` → opportunity (a quote belongs to an opportunity)

### Business process flows (active)
- **Project Service - Opportunity Sales Process** (primary entity opportunity)
- **Follow up with Opportunity** (primary entity opportunity)

---

## `quote` — Quote  *(OOB, UserOwned)*
A formal priced offer to a customer, optionally tied to an opportunity. Primary id
`quoteid`, name `name`. EntitySet `quotes`. Project Operations adds rollup/margin
columns (`msdyn_*`). The bridge from sales (opportunity) toward delivery (project).

### Columns
| Kind | Logical name | Type | Req | Label |
|---|---|---|---|---|
| O | `name` | String | ApplicationRequired | Name |
| O | `quotenumber` | String | — | Quote ID |
| O | `opportunityid` | Lookup | None | Opportunity (→ opportunity) |
| O | `customerid` | Customer | ApplicationRequired | Customer (→ account/contact) |
| O | `totalamount` | Money | — | Total Amount |
| O | `effectivefrom` / `effectiveto` | DateTime | None | Effective dates |
| O | `statecode` | State | SystemRequired | Status |
| O | `statuscode` | Status | None | Status Reason |
| O | `transactioncurrencyid` | Lookup | — | Currency |
| O | `ownerid` | Owner | SystemRequired | Owner |
| C | `msdyn_ordertype` | Picklist | Recommended | Type |
| C | `msdyn_contractorganizationalunitid` | Lookup | Recommended | Contracting Unit |
| C | `msdyn_accountmanagerid` | Lookup | Recommended | Account Manager (→ systemuser) |
| C | `msdyn_estimatedbudget` / `msdyn_customerbudgetrollup` | Picklist / Money | None | Budget |
| C | `msdyn_grossmargin` / `msdyn_adjustedgrossmargin` | Decimal | None | Gross Margin (%) |
| C | `msdyn_nottoexceedlimit` | Money | None | Not-to-exceed Limit |
| C | `msdyn_totalcost` | Money | None | Total Cost |
| C | `msdyn_profitability` / `msdyn_profitabilitymetric` | Picklist / Decimal | None | Profitability |

### Choice sets
- `statecode`: 0 Draft · 1 Active · 2 Won · 3 Closed
- `statuscode`: 1/2 In Progress · 3 Open · 4 Won · 5 Lost · 6 Canceled · 7 Revised

### Key relationships
- **M2O:** `opportunityid`→opportunity · `customerid`→account/contact ·
  `transactioncurrencyid`→transactioncurrency · `msdyn_accountmanagerid`→systemuser

---

## `msdyn_project` — Project  *(custom/managed by Project Operations, UserOwned)*
The delivery project. Primary id `msdyn_projectid`, **primary name `msdyn_subject`**
(labelled "Name"). EntitySet `msdyn_projects`. **1 record** in env. Linked to the
sales side via `msdyn_salesorderid` (the Contract). 99 custom cols — curated below.

### Columns
| Kind | Logical name | Type | Req | Label |
|---|---|---|---|---|
| C | `msdyn_subject` | String | ApplicationRequired | Name (primary) |
| C | `msdyn_customer` | Lookup | None | Customer (→ account) |
| C | `msdyn_salesorderid` | Lookup | None | Contract (→ salesorder) |
| C | `msdyn_projectmanager` | Lookup | ApplicationRequired | Project manager (→ systemuser) |
| C | `msdyn_scheduledstart` | DateTime | None | Start Date |
| C | `msdyn_progress` | Decimal | None | % Complete |
| C | `msdyn_totalplannedcost` / `msdyn_totalactualcost` | Money | None | Estimated / Actual Total Cost |
| C | `msdyn_totalplannedsales` / `msdyn_totalactualsales` | Money | None | Estimated / Actual Total Sales |
| C | `msdyn_teamsize` | Integer | None | Team Size |
| C | `msdyn_valuestatement` | Memo | None | Value statement |
| C | `msdyn_workhourtemplate` | Lookup | ApplicationRequired | Work hour template |
| O | `statecode` | State | SystemRequired | Project Status |
| O | `statuscode` | Status | None | Status Reason |
| O | `transactioncurrencyid` | Lookup | None | Currency |
| O | `ownerid` | Owner | SystemRequired | Owner |

### Choice sets
- `statecode`: 0 Active · 1 Inactive
- `statuscode`: 1 Active · 192350001 Project copying · 192350002 Project copy failed ·
  192350011 importing · 192350012 import failed · 192350021 converting · 192350022 convert failed

### Key relationships
- **M2O:** `msdyn_customer`→account · `msdyn_salesorderid`→salesorder (Contract) ·
  `msdyn_projectmanager`→systemuser · `transactioncurrencyid`→transactioncurrency
- **O2M (children):** `msdyn_projectteam.msdyn_project` → project (team members)

### Business process flows (active)
- **Project Service - Project Stages** (primary entity msdyn_project)

> ⚠️ **No direct opportunity↔project lookup.** The path is
> `opportunity → quote → (sales order / contract) → msdyn_project.msdyn_salesorderid`.
> A flow that "flags the project when an opportunity closes" must traverse the
> sales order, **or** the slice can add a direct `inz_` lookup if a shortcut is wanted.

---

## `msdyn_projectteam` — Project Team Member  *(custom/PO, UserOwned)*
A staffed/generic position on a project. Primary id `msdyn_projectteamid`, name
`msdyn_name` ("Position Name"). EntitySet `msdyn_projectteams`. 33 custom cols.

### Columns
| Kind | Logical name | Type | Req | Label |
|---|---|---|---|---|
| C | `msdyn_name` | String | None | Position Name |
| C | `msdyn_project` | Lookup | ApplicationRequired | Project (→ msdyn_project) |
| C | `msdyn_resourcecategory` | Lookup | ApplicationRequired | Role |
| C | `msdyn_bookableresourceid` | Lookup | None | Bookable Resource |
| C | `msdyn_organizationalunit` | Lookup | None | Resourcing Unit |
| C | `msdyn_start` / `msdyn_finish` | DateTime | ApplicationRequired | Start / Finish |
| C | `msdyn_effort` | Decimal | None | Total Effort (Hours) |
| C | `msdyn_effortcompleted` / `msdyn_effortremaining` | Decimal | None | Effort completed / remaining |
| C | `msdyn_hardbookedhours` / `msdyn_softbookedhours` | Decimal | None | Hard / Soft booked hours |
| C | `msdyn_workertype` | Picklist | None | Worker Type |
| C | `msdyn_billingtype` | Picklist | None | Billing Type |
| C | `msdyn_projectapprover` | Boolean | None | Project Approver |
| O | `statecode` | State | SystemRequired | Status |
| O | `statuscode` | Status | None | Status Reason |
| O | `ownerid` | Owner | SystemRequired | Owner |

### Key relationships
- **M2O:** `msdyn_project`→msdyn_project · `msdyn_resourcecategory`→role ·
  `msdyn_bookableresourceid`→bookableresource

---

## Slice map (how the tables connect)

```
account / contact
   ▲  ▲
   │  │ customerid
opportunity ──O2M──> quote.opportunityid
   │ (Project Service - Opportunity Sales Process BPF)
   │
   ▼ [quote → sales order / contract]   (no direct opp→project FK)
msdyn_project ──O2M──> msdyn_projectteam.msdyn_project
   (Project Service - Project Stages BPF)        │
   msdyn_salesorderid ──> salesorder (Contract)  ▼ msdyn_resourcecategory → role
```

The proposed first thin slice (engagement-risk on `opportunity`) lives entirely on
the `opportunity` table plus a flow reaching `msdyn_project` — note the indirect
opp→project path above when designing that flow.
