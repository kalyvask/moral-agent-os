"""Adaptive review console for AI Safety OS.

A reviewer surface over the five dispositions: auto, confirm, present-options, escalate,
block. It loads the scenario bank, routes each action through the runtime, and lays the
results out as a triage queue with the assessment scores, the kaleidoscope interpretations
for plural cases, and a correction button that records a human decision into WorkspaceMemory
so the queue learns live (a confirmed action becomes auto next time).

Dependency-free: stdlib http.server, a static page, and a small JSON API. Runs offline with
the deterministic assessor.

    python web/app.py
    # open http://127.0.0.1:8000
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_safety_os import MoralAgentOS, WorkspaceMemory
from ai_safety_os.schema import Disposition, Scenario
from bench.run import load_scenarios

# One workspace memory for the server's lifetime, so corrections accumulate across requests
# and the queue visibly learns within a session.
MEMORY = WorkspaceMemory()
SCENARIOS = {s.id: s for s in load_scenarios()}

DISPOSITIONS = ["auto", "confirm", "present_options", "escalate", "block"]
DISPOSITION_LABEL = {
    "auto": "Auto",
    "confirm": "Confirm",
    "present_options": "Present options",
    "escalate": "Escalate",
    "block": "Block",
}


def _decision_payload(scenario_id: str) -> dict:
    scenario = SCENARIOS[scenario_id]
    runtime = MoralAgentOS(memory=MEMORY)
    decision = runtime.evaluate(scenario)
    a = decision.assessment
    return {
        "id": scenario.id,
        "action": scenario.action_text,
        "context": scenario.context,
        "role": scenario.agent_role,
        "family": scenario.action_family,
        "expected_label": scenario.expected_label.value,
        "disposition": decision.disposition.value,
        "rationale": decision.rationale,
        "scores": {
            "stakes": a.stakes,
            "reversibility": a.reversibility,
            "role_authority": a.role_authority,
            "norm_conflict": a.norm_conflict,
            "confidence": a.confidence,
            "universalizability": a.universalizability,
            "moral_patiency": a.moral_patiency,
            "affective_salience": a.affective_salience,
        },
        "flags": list(a.floor_violations) + list(a.reward_hacking_signals),
        "stakeholders": list(a.stakeholders),
        "options": [
            {
                "name": o.name,
                "interpretation": o.interpretation,
                "recommended_action": o.recommended_action,
            }
            for o in decision.options
        ],
    }


def build_queue() -> dict:
    items = [_decision_payload(sid) for sid in SCENARIOS]
    counts = {d: sum(1 for it in items if it["disposition"] == d) for d in DISPOSITIONS}
    standing = [
        {
            "stakeholder": rel.stakeholder,
            "trust": round(rel.trust, 2),
            "repair": round(rel.repair_obligation, 2),
        }
        for rel in MEMORY.all_relationships()
    ]
    return {
        "items": items,
        "counts": counts,
        "corrections": MEMORY.correction_count(),
        "standing": standing,
    }


def apply_review(memory: WorkspaceMemory, scenario: Scenario, *, approve: bool) -> None:
    """Record a reviewer's decision: a correction plus the interdependence update.

    Approving records the action as routine and credits cooperation with each stakeholder it
    touches; flagging records a stricter disposition and sanctions them, so the agent's
    standing tracks human review. The bank exposes stakeholder types (user, customer,
    investor); a live agent supplies named counterparties.
    """
    stakeholders = MoralAgentOS(memory=memory).evaluate(scenario).assessment.stakeholders
    if approve:
        memory.record_correction(scenario, Disposition.AUTO, note="reviewer console: approved")
        for name in stakeholders:
            memory.observe_cooperation(name)
    else:
        memory.record_correction(scenario, Disposition.ESCALATE, note="reviewer console: flagged")
        for name in stakeholders:
            memory.observe_sanction(name)


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>AI Safety OS - Review Console</title>
<style>
  :root {
    --auto:#6a8f4f; --confirm:#d9a441; --present_options:#7d6f9c;
    --escalate:#c1666b; --block:#8c3b3b; --ink:#222; --muted:#666; --line:#e4e2dd;
  }
  * { box-sizing: border-box; }
  body { margin:0; background:#f4f4f5; color:var(--ink);
         font-family: "Segoe UI", Helvetica, Arial, sans-serif; }
  header { padding:18px 24px; background:#fff; border-bottom:1px solid var(--line);
           display:flex; align-items:baseline; gap:16px; flex-wrap:wrap; }
  header h1 { font-size:18px; margin:0; }
  header .sub { color:var(--muted); font-size:13px; }
  .counts { margin-left:auto; display:flex; gap:8px; flex-wrap:wrap; }
  .pill { font-size:12px; padding:3px 9px; border-radius:999px; color:#fff; }
  main { padding:18px 24px; display:grid; gap:16px;
         grid-template-columns: repeat(auto-fill, minmax(330px, 1fr)); align-items:start; }
  .col h2 { font-size:13px; text-transform:uppercase; letter-spacing:.04em; margin:0 0 8px;
            padding-bottom:6px; border-bottom:2px solid var(--line); }
  .card { background:#fff; border:1px solid var(--line); border-left:4px solid #999;
          border-radius:6px; padding:12px 14px; margin-bottom:10px; }
  .card .action { font-weight:600; font-size:14px; }
  .card .meta { color:var(--muted); font-size:12px; margin:3px 0 8px; }
  .card .ctx { font-size:13px; margin-bottom:8px; }
  .chips { display:flex; flex-wrap:wrap; gap:5px; margin-bottom:8px; }
  .chip { font:11px ui-monospace, SFMono-Regular, Menlo, monospace; padding:2px 6px;
          border-radius:4px; background:#f0efea; color:#444; }
  .chip.hot { background:#f3dcdc; color:#7a2e2e; }
  .rationale { font-size:12px; color:#444; }
  .flags { font-size:12px; color:var(--escalate); margin-top:6px; }
  .opt { border-top:1px dashed var(--line); margin-top:8px; padding-top:8px; font-size:12px; }
  .opt b { color:var(--present_options); }
  .actions { margin-top:10px; display:flex; gap:8px; }
  button { font:13px inherit; padding:5px 10px; border:1px solid var(--line);
           background:#fafaf9; border-radius:5px; cursor:pointer; }
  button:hover { background:#f0efea; }
  .label { font-size:11px; color:var(--muted); }
  .mismatch { color:var(--escalate); }
  .standing { padding:8px 24px; background:#fff; border-bottom:1px solid var(--line);
              font-size:12px; display:flex; gap:6px; flex-wrap:wrap; align-items:center; }
</style>
</head>
<body>
<header>
  <h1>AI Safety OS</h1>
  <span class="sub">Adaptive review console - five dispositions over the workspace action bank</span>
  <span class="counts" id="counts"></span>
</header>
<div id="standing" class="standing"></div>
<main id="board"></main>
<script>
const DISPS = ["auto","confirm","present_options","escalate","block"];
const LABEL = {auto:"Auto",confirm:"Confirm",present_options:"Present options",escalate:"Escalate",block:"Block"};

function chip(name, val) {
  const hot = val >= 0.7 && (name==="stakes"||name==="norm_conflict"||name==="moral_patiency"||name==="affective_salience");
  const low = (name==="universalizability"||name==="role_authority"||name==="reversibility") && val <= 0.3;
  const cls = (hot||low) ? "chip hot" : "chip";
  const short = {stakes:"stk",reversibility:"rev",role_authority:"role",norm_conflict:"norm",
    confidence:"conf",universalizability:"univ",moral_patiency:"pati",affective_salience:"felt"}[name]||name;
  return `<span class="${cls}">${short} ${val.toFixed(2)}</span>`;
}

function card(it) {
  const mism = (it.disposition==="auto" && it.expected_label==="clear_inappropriate")
            || (it.disposition!=="auto" && it.expected_label==="clear_appropriate");
  const chips = Object.entries(it.scores).map(([k,v])=>chip(k,v)).join("");
  const flags = it.flags.length ? `<div class="flags">flag: ${it.flags.join("; ")}</div>` : "";
  const opts = it.options.map(o=>`<div class="opt"><b>${o.name}</b>: ${o.interpretation} <span class="label">-> ${o.recommended_action}</span></div>`).join("");
  const approve = it.disposition!=="auto"
    ? `<button onclick="review('${it.id}','approve')">Approve -> routine</button>` : "";
  const flag = it.disposition!=="block"
    ? `<button onclick="review('${it.id}','flag')">Flag -> inappropriate</button>` : "";
  const acts = (approve||flag) ? `<div class="actions">${approve}${flag}</div>` : "";
  const tag = mism ? ` <span class="mismatch label">(vs label: ${it.expected_label})</span>` : "";
  return `<div class="card" style="border-left-color:var(--${it.disposition})">
    <div class="action">${it.action}</div>
    <div class="meta">${it.role} - ${it.family}${tag}</div>
    <div class="ctx">${it.context}</div>
    <div class="chips">${chips}</div>
    <div class="rationale">${it.rationale}</div>${flags}${opts}${acts}</div>`;
}

async function load() {
  const data = await (await fetch("/api/queue")).json();
  document.getElementById("counts").innerHTML =
    DISPS.map(d=>`<span class="pill" style="background:var(--${d})">${LABEL[d]} ${data.counts[d]}</span>`).join("")
    + `<span class="pill" style="background:#555">corrections ${data.corrections}</span>`;
  const st = document.getElementById("standing");
  st.innerHTML = data.standing.length
    ? "<span class='label'>Standing by stakeholder:</span> " + data.standing.map(s=>
        `<span class="chip ${s.repair>0?'hot':''}">${s.stakeholder} · trust ${s.trust.toFixed(2)}${s.repair>0?` · owes ${s.repair.toFixed(2)}`:""}</span>`).join("")
    : "<span class='label'>Standing by stakeholder: approve or flag actions to build per-stakeholder trust.</span>";
  const board = document.getElementById("board");
  board.innerHTML = DISPS.map(d=>{
    const items = data.items.filter(it=>it.disposition===d);
    if (!items.length) return "";
    return `<div class="col"><h2 style="border-color:var(--${d})">${LABEL[d]} (${items.length})</h2>${items.map(card).join("")}</div>`;
  }).join("");
}
async function review(id, action) {
  await fetch("/api/correct", {method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({scenario_id:id, action:action})});
  load();
}
load();
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args) -> None:  # quiet server
        pass

    def _send(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - stdlib API
        if self.path.startswith("/api/queue"):
            self._send(json.dumps(build_queue()).encode("utf-8"), "application/json")
        elif self.path in ("/", "/index.html"):
            self._send(PAGE.encode("utf-8"), "text/html; charset=utf-8")
        else:
            self._send(b"not found", "text/plain", status=404)

    def do_POST(self) -> None:  # noqa: N802 - stdlib API
        if not self.path.startswith("/api/correct"):
            self._send(b"not found", "text/plain", status=404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        scenario = SCENARIOS.get(str(payload.get("scenario_id")))
        if scenario is not None:
            approve = str(payload.get("action", "approve")) != "flag"
            apply_review(MEMORY, scenario, approve=approve)
        self._send(json.dumps({"ok": scenario is not None}).encode("utf-8"), "application/json")


def main() -> None:
    server = HTTPServer(("127.0.0.1", 8000), Handler)
    print("AI Safety OS review console: http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
