#!/usr/bin/env python
"""
Sales Intelligence Brief — AI population layer.

Reads an account and its sales context (open opportunities, contacts) from
Dataverse, asks Claude to write a concise seller briefing and rate the account's
health, then writes the result back into the `ion_brief` and `ion_accounthealth`
columns. The AccountBriefGuard plug-in then auto-stamps `ion_briefupdatedon` and
enforces the At-Risk-needs-a-brief rule — so this script and the server-side
guard compose cleanly.

This is the "intelligence" layer of the slice: the columns + form (data model)
hold the brief; this turns a human-curated field into an AI-generated one.

Usage:
    python scripts/generate_brief.py --account "Northwind Traders"        # generate + print
    python scripts/generate_brief.py --account "Northwind Traders" --write # also save to Dataverse
    python scripts/generate_brief.py --account "Northwind Traders" --dry-run  # show context, no API call
    python scripts/generate_brief.py --account "Northwind Traders" --stub --write  # canned brief, exercises write path offline

Auth:
    Dataverse — reuses scripts/auth.py (DV CLI token cache).
    Claude    — ANTHROPIC_API_KEY from the environment or .env.
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auth import get_token, load_env

API_VERSION = "v9.2"
MODEL = "claude-opus-4-8"

# ion_accounthealth local option set (see docs/schema/sales-pilot.md).
HEALTH_TO_OPTION = {"Healthy": 100000000, "Watch": 100000001, "At Risk": 100000002}


class Health(str, Enum):
    healthy = "Healthy"
    watch = "Watch"
    at_risk = "At Risk"


def _env_base():
    load_env()
    return os.environ["DATAVERSE_URL"].rstrip("/") + f"/api/data/{API_VERSION}/"


def _headers(token, extra=None):
    h = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
    }
    if extra:
        h.update(extra)
    return h


def _get(base, token, path):
    req = urllib.request.Request(base + path, headers=_headers(token))
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def gather_context(base, token, account_name=None, account_id=None):
    """Pull the account plus its open opportunities and contacts."""
    if account_id is None:
        flt = "name eq '%s'" % account_name.replace("'", "''")
        rows = _get(base, token, "accounts?" + urllib.parse.urlencode({
            "$select": "accountid,name,revenue,numberofemployees,description,websiteurl,ion_accounthealth,ion_brief",
            "$filter": flt, "$top": "1"}))["value"]
        if not rows:
            raise SystemExit(f"No account found named {account_name!r}.")
        account = rows[0]
        account_id = account["accountid"]
    else:
        account = _get(base, token, "accounts(%s)?%s" % (account_id, urllib.parse.urlencode({
            "$select": "accountid,name,revenue,numberofemployees,description,websiteurl,ion_accounthealth,ion_brief"})))

    opps = _get(base, token, "opportunities?" + urllib.parse.urlencode({
        "$select": "name,estimatedvalue,estimatedclosedate,closeprobability,statecode,description",
        "$filter": "_parentaccountid_value eq %s" % account_id,
        "$orderby": "estimatedclosedate asc"}))["value"]

    contacts = _get(base, token, "contacts?" + urllib.parse.urlencode({
        "$select": "fullname,jobtitle,emailaddress1",
        "$filter": "_parentcustomerid_value eq %s" % account_id}))["value"]

    return account_id, account, opps, contacts


def build_context_doc(account, opps, contacts):
    """Render the gathered data as a compact briefing source document."""
    lines = ["# Account", f"Name: {account.get('name')}"]
    if account.get("revenue") is not None:
        lines.append(f"Annual revenue: {account['revenue']:,.0f}")
    if account.get("numberofemployees") is not None:
        lines.append(f"Employees: {account['numberofemployees']}")
    if account.get("description"):
        lines.append(f"Notes: {account['description']}")

    lines.append("\n# Open opportunities")
    if opps:
        for o in opps:
            val = o.get("estimatedvalue")
            lines.append(
                f"- {o.get('name')}: est. {val:,.0f} | close {o.get('estimatedclosedate','?')[:10]} "
                f"| {o.get('closeprobability','?')}% probability".replace("None", "?"))
    else:
        lines.append("- (none)")

    lines.append("\n# Key contacts")
    if contacts:
        for c in contacts:
            lines.append(f"- {c.get('fullname')} — {c.get('jobtitle') or 'role unknown'}")
    else:
        lines.append("- (none)")
    return "\n".join(lines)


SYSTEM_PROMPT = (
    "You are a sales intelligence analyst. From the structured account data you are given, "
    "write a tight pre-engagement brief a seller can read in 30 seconds, and rate the account's health.\n"
    "- brief: 4-7 sentences of markdown. Cover relationship state, pipeline momentum, the biggest "
    "open risk, and a concrete next best action. Be specific to the data; do not invent facts.\n"
    "- health: Healthy (momentum, low risk), Watch (mixed signals), or At Risk (stalled/declining/red flags).\n"
    "- rationale: one sentence justifying the health rating."
)


def generate_with_claude(context_doc):
    import anthropic  # local pydantic model below
    from pydantic import BaseModel

    class Brief(BaseModel):
        health: Health
        brief: str
        rationale: str

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    resp = client.messages.parse(
        model=MODEL,
        max_tokens=4000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": context_doc}],
        output_format=Brief,
    )
    return resp.parsed_output


def stub_brief(account, opps):
    """Deterministic brief for offline testing of the write path (no API call)."""
    total = sum(o.get("estimatedvalue") or 0 for o in opps)
    from pydantic import BaseModel

    class Brief(BaseModel):
        health: Health
        brief: str
        rationale: str

    return Brief(
        health=Health.watch,
        brief=(f"**{account.get('name')}** has {len(opps)} open opportunities worth ~{total:,.0f} in pipeline. "
               "Relationship is established but momentum is mixed. **Next best action:** confirm the renewal "
               "timeline with the VP Procurement before quarter close. _(stub brief — no AI call)_"),
        rationale="Stub: mixed pipeline signals.",
    )


def write_back(base, token, account_id, brief):
    body = {"ion_brief": brief.brief, "ion_accounthealth": HEALTH_TO_OPTION[brief.health.value]}
    req = urllib.request.Request(
        base + "accounts(%s)" % account_id, data=json.dumps(body).encode(),
        method="PATCH", headers=_headers(token, {"Content-Type": "application/json"}))
    urllib.request.urlopen(req)


def main():
    ap = argparse.ArgumentParser(description="Generate a sales intelligence brief for an account.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--account", help="Account name (exact match).")
    g.add_argument("--account-id", help="Account GUID.")
    ap.add_argument("--write", action="store_true", help="Save the brief back to Dataverse.")
    ap.add_argument("--dry-run", action="store_true", help="Gather + show the context document; no API call.")
    ap.add_argument("--stub", action="store_true", help="Use a canned brief instead of calling Claude.")
    args = ap.parse_args()

    base = _env_base()
    token = get_token()
    account_id, account, opps, contacts = gather_context(base, token, args.account, args.account_id)
    context_doc = build_context_doc(account, opps, contacts)

    print(f"=== Context for {account.get('name')} ({account_id}) ===\n{context_doc}\n")
    if args.dry_run:
        return

    brief = stub_brief(account, opps) if args.stub else generate_with_claude(context_doc)

    print(f"=== Generated brief ===\nHealth: {brief.health.value}\nRationale: {brief.rationale}\n\n{brief.brief}\n")

    if args.write:
        write_back(base, token, account_id, brief)
        check = _get(base, token, "accounts(%s)?%s" % (account_id, urllib.parse.urlencode({
            "$select": "ion_accounthealth,ion_briefupdatedon"})))
        print(f"Saved. ion_accounthealth={check.get('ion_accounthealth')} "
              f"ion_briefupdatedon={check.get('ion_briefupdatedon')} (auto-stamped by the plug-in)")


if __name__ == "__main__":
    main()
