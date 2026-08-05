#!/usr/bin/env python3
"""
Minimal local web tool for SC Crypto Gateway Adapter v0.1.

This intentionally supports paper execution only. It does not place live orders,
hold secrets, sign transactions, or call exchange/wallet/DeFi APIs.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import secrets
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "intent-schema-v0.1.json"
REPORT_DIR = ROOT / "records" / "paper-executions"
JST = dt.timezone(dt.timedelta(hours=9), "JST")

SECRET_KEY_RE = re.compile(
    r"(seed|mnemonic|private[_-]?key|secret|api[_-]?secret|2fa|recovery)",
    re.IGNORECASE,
)

HARD_GUARDS = {
    "require_address_whitelist",
    "block_private_key_handling",
    "require_audit_log",
    "require_evidence",
    "require_dapp_calldata_review",
}

DEFAULT_INTENT = {
    "schema_version": "0.1",
    "intent_id": "INT-20260805-001",
    "created_at_jst": "2026-08-05 12:02 JST",
    "created_by": "web_ui",
    "source": {
        "chat_title": "SC Crypto Gateway Web Tool",
        "record_path": None,
        "related_plan_id": None,
        "related_url": None,
    },
    "intent_type": "trade",
    "execution_mode": "paper",
    "venue_type": "cex",
    "venue": "paper",
    "chain": "none",
    "network_id": None,
    "asset_flow": {
        "side": "BUY",
        "from_asset": "JPY",
        "to_asset": "BTC",
        "from_contract_address": None,
        "to_contract_address": None,
        "amount_type": "jpy_budget",
        "amount_jpy": 50000,
        "from_amount": None,
        "to_amount_min": None,
        "price_limit": None,
        "price_limit_currency": "JPY",
    },
    "risk": {
        "max_loss_jpy": 10000,
        "slippage_bps_max": 100,
        "gas_jpy_max": 0,
        "fee_jpy_max": 1000,
        "daily_limit_jpy_group": "default",
        "cash_reserve_ratio_min": 0.55,
        "requires_manual_confirm": True,
        "stop_loss_condition": "最大損失10,000円以内で撤退",
        "take_profit_condition": "Paper検証後に判断",
    },
    "safety": {
        "safety_profile": "strict",
        "toggles": {
            "require_manual_confirm": True,
            "enable_market_order": False,
            "enforce_max_order_jpy": True,
            "enforce_daily_limit_jpy": True,
            "enforce_max_loss_jpy": True,
            "enforce_slippage_bps": True,
            "enforce_gas_jpy_max": True,
            "enforce_cash_reserve_ratio": True,
            "require_asset_whitelist": True,
            "require_chain_whitelist": True,
            "require_venue_whitelist": True,
            "require_address_whitelist": True,
            "block_private_key_handling": True,
            "require_audit_log": True,
            "require_evidence": True,
            "require_dapp_calldata_review": True,
        },
    },
    "ledger": {
        "ledger_target": "paper_ledger",
        "evidence_required": True,
        "jpy_basis": "quote_time",
        "evidence_id": None,
        "check_status_default": "対象外",
    },
    "reason": "Gateway Adapterのpaper実行テスト。",
    "notes": None,
}


def now_jst() -> str:
    return dt.datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")


def load_schema() -> dict[str, Any]:
    if not SCHEMA_PATH.exists():
        return {}
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def walk_secret_like_keys(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            next_path = f"{path}.{key}"
            if str(key) not in HARD_GUARDS and SECRET_KEY_RE.search(str(key)):
                found.append(next_path)
            found.extend(walk_secret_like_keys(item, next_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(walk_secret_like_keys(item, f"{path}[{index}]"))
    return found


def validate_intent(intent: dict[str, Any]) -> dict[str, Any]:
    schema = load_schema()
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(intent, dict):
        return {"ok": False, "errors": ["Intent must be a JSON object."], "warnings": []}

    for field in schema.get("required", []):
        if field not in intent:
            errors.append(f"Missing required field: {field}")

    if intent.get("schema_version") != "0.1":
        errors.append("schema_version must be 0.1")

    intent_id = intent.get("intent_id")
    if not isinstance(intent_id, str) or not re.match(r"^INT-[0-9]{8}-[0-9]{3,6}$", intent_id):
        errors.append("intent_id must match INT-YYYYMMDD-001 format.")

    execution_mode = intent.get("execution_mode")
    if execution_mode not in {"paper", "shadow", "live_confirmed", "live_auto"}:
        errors.append("execution_mode is invalid.")

    if intent.get("venue_type") not in {"cex", "wallet", "defi", "dapp", "manual"}:
        errors.append("venue_type is invalid.")

    secret_paths = walk_secret_like_keys(intent)
    if secret_paths:
        errors.append("Intent contains secret-like keys: " + ", ".join(secret_paths))

    risk = intent.get("risk", {})
    if isinstance(risk, dict):
        max_loss = risk.get("max_loss_jpy")
        if isinstance(max_loss, (int, float)) and max_loss > 10000:
            errors.append("max_loss_jpy exceeds v0.1 upper limit of 10000.")
        amount_jpy = intent.get("asset_flow", {}).get("amount_jpy") if isinstance(intent.get("asset_flow"), dict) else None
        if isinstance(amount_jpy, (int, float)) and amount_jpy <= 0:
            errors.append("amount_jpy must be greater than 0 when provided.")
    else:
        errors.append("risk must be an object.")

    safety = intent.get("safety", {})
    toggles = safety.get("toggles", {}) if isinstance(safety, dict) else {}
    if not isinstance(toggles, dict):
        errors.append("safety.toggles must be an object.")
    else:
        for guard in HARD_GUARDS:
            if toggles.get(guard) is not True:
                errors.append(f"Hard Guard must remain true: safety.toggles.{guard}")

    if execution_mode != "paper":
        warnings.append("This v0.1 web tool can validate this Intent, but can only run paper execution.")

    if intent.get("venue_type") == "dapp":
        warnings.append("DApp adapter is disabled in v0.1; validation only.")

    ledger = intent.get("ledger", {})
    if isinstance(ledger, dict) and ledger.get("ledger_target") != "paper_ledger":
        warnings.append("Paper execution should normally use ledger.ledger_target=paper_ledger.")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def run_paper(intent: dict[str, Any]) -> dict[str, Any]:
    validation = validate_intent(intent)
    if not validation["ok"]:
        return {
            "status": "rejected",
            "created_at_jst": now_jst(),
            "validation": validation,
            "report": None,
        }

    if intent.get("execution_mode") != "paper":
        return {
            "status": "rejected",
            "created_at_jst": now_jst(),
            "validation": validation,
            "report": None,
            "reason": "This tool only runs execution_mode=paper.",
        }

    asset_flow = intent.get("asset_flow", {})
    risk = intent.get("risk", {})
    report_id = f"PER-{dt.datetime.now(JST).strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}"
    amount_jpy = asset_flow.get("amount_jpy")

    report = {
        "report_id": report_id,
        "schema_version": "0.1",
        "created_at_jst": now_jst(),
        "status": "paper_recorded",
        "intent_id": intent.get("intent_id"),
        "execution_mode": "paper",
        "venue_type": intent.get("venue_type"),
        "venue": intent.get("venue"),
        "intent_summary": {
            "intent_type": intent.get("intent_type"),
            "side": asset_flow.get("side"),
            "from_asset": asset_flow.get("from_asset"),
            "to_asset": asset_flow.get("to_asset"),
            "amount_jpy": amount_jpy,
            "reason": intent.get("reason"),
        },
        "risk_result": {
            "status": "passed",
            "max_loss_jpy": risk.get("max_loss_jpy"),
            "slippage_bps_max": risk.get("slippage_bps_max"),
            "gas_jpy_max": risk.get("gas_jpy_max"),
            "fee_jpy_max": risk.get("fee_jpy_max"),
            "cash_reserve_ratio_min": risk.get("cash_reserve_ratio_min"),
        },
        "paper_execution": {
            "executed_at_jst": now_jst(),
            "paper_amount_jpy": amount_jpy,
            "executed_price": None,
            "executed_price_currency": None,
            "fee_jpy_estimate": min(risk.get("fee_jpy_max", 0) or 0, amount_jpy * 0.01 if isinstance(amount_jpy, (int, float)) else 0),
            "gas_jpy_estimate": 0 if intent.get("venue_type") == "cex" else risk.get("gas_jpy_max"),
            "market_data_source": "not_connected_v0.1",
            "note": "v0.1 paper adapter does not fetch market quotes or place live orders.",
        },
        "ledger_export": {
            "target": "paper_ledger",
            "google_sheet_direct_write": False,
            "check_status": "対象外",
            "evidence_required": intent.get("ledger", {}).get("evidence_required"),
            "evidence_id": intent.get("ledger", {}).get("evidence_id"),
        },
        "events": [
            {"event": "intent_received", "at_jst": now_jst()},
            {"event": "schema_validated", "at_jst": now_jst()},
            {"event": "risk_passed", "at_jst": now_jst()},
            {"event": "paper_recorded", "at_jst": now_jst()},
        ],
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"{report_id}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["local_report_path"] = str(report_path)
    return {"status": "paper_recorded", "created_at_jst": now_jst(), "validation": validation, "report": report}


def json_response(handler: BaseHTTPRequestHandler, payload: dict[str, Any], status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json_body(handler: BaseHTTPRequestHandler) -> tuple[dict[str, Any] | None, str | None]:
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length).decode("utf-8")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON: {exc}"
    if not isinstance(value, dict):
        return None, "Request body must be a JSON object."
    return value, None


def page() -> str:
    default_json = html.escape(json.dumps(DEFAULT_INTENT, ensure_ascii=False, indent=2))
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SC Crypto Gateway Tool v0.1</title>
  <style>
    body {{ margin: 0; font-family: system-ui, -apple-system, sans-serif; background: #f7f7f4; color: #1f2933; }}
    header {{ padding: 16px; border-bottom: 1px solid #ddd8cc; background: #fff; position: sticky; top: 0; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 16px; display: grid; gap: 16px; grid-template-columns: 1fr; }}
    textarea {{ width: 100%; min-height: 440px; box-sizing: border-box; font: 13px/1.45 ui-monospace, SFMono-Regular, Menlo, monospace; padding: 12px; border: 1px solid #cfc8ba; border-radius: 8px; background: #fff; }}
    button {{ border: 0; border-radius: 8px; padding: 10px 14px; font-weight: 700; background: #174ea6; color: #fff; }}
    button.secondary {{ background: #5f6b7a; }}
    .bar {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
    .note {{ font-size: 13px; color: #59636e; }}
    pre {{ white-space: pre-wrap; overflow-wrap: anywhere; background: #111827; color: #e5e7eb; border-radius: 8px; padding: 12px; min-height: 240px; }}
    .status {{ font-weight: 700; }}
    @media (min-width: 900px) {{ main {{ grid-template-columns: 1fr 1fr; }} .full {{ grid-column: 1 / -1; }} }}
  </style>
</head>
<body>
  <header>
    <div class="status">SC Crypto Gateway Tool v0.1</div>
    <div class="note">paper実行専用。実発注、送金、署名、API Secretの扱いはしません。</div>
  </header>
  <main>
    <section>
      <div class="bar">
        <button onclick="validateIntent()">Validate</button>
        <button onclick="runPaper()">Run Paper</button>
        <button class="secondary" onclick="resetSample()">Reset Sample</button>
      </div>
      <p class="note">Intent JSONを貼り付けて検証し、paper adapterへ投げます。</p>
      <textarea id="intent">{default_json}</textarea>
    </section>
    <section>
      <div class="status">Result</div>
      <pre id="result">Ready.</pre>
    </section>
  </main>
  <script>
    const sample = document.getElementById('intent').value;
    function show(value) {{
      document.getElementById('result').textContent =
        typeof value === 'string' ? value : JSON.stringify(value, null, 2);
    }}
    function readIntent() {{
      return JSON.parse(document.getElementById('intent').value);
    }}
    function resetSample() {{
      document.getElementById('intent').value = sample;
      show('Sample restored.');
    }}
    async function post(path) {{
      let payload;
      try {{ payload = readIntent(); }} catch (err) {{ show('JSON parse error: ' + err.message); return; }}
      const res = await fetch(path, {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(payload)
      }});
      show(await res.json());
    }}
    function validateIntent() {{ post('/api/validate'); }}
    function runPaper() {{ post('/api/run-paper'); }}
  </script>
</body>
</html>"""


class GatewayHandler(BaseHTTPRequestHandler):
    server_version = "SCGatewayTool/0.1"

    def do_GET(self) -> None:
        if not self._authorized():
            return
        parsed = urlparse(self.path)
        if parsed.path == "/":
            body = page().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif parsed.path == "/api/health":
            json_response(self, {"ok": True, "now_jst": now_jst(), "mode": "paper_only"})
        else:
            json_response(self, {"ok": False, "error": "Not found"}, 404)

    def do_POST(self) -> None:
        if not self._authorized():
            return
        parsed = urlparse(self.path)
        payload, error = read_json_body(self)
        if error:
            json_response(self, {"ok": False, "error": error}, 400)
            return
        assert payload is not None
        if parsed.path == "/api/validate":
            json_response(self, validate_intent(payload))
        elif parsed.path == "/api/run-paper":
            result = run_paper(payload)
            json_response(self, result, 200 if result["status"] == "paper_recorded" else 400)
        else:
            json_response(self, {"ok": False, "error": "Not found"}, 404)

    def _authorized(self) -> bool:
        token = getattr(self.server, "gateway_token", None)
        if not token:
            return True
        parsed = urlparse(self.path)
        query_token = parse_qs(parsed.query).get("token", [None])[0]
        header_token = self.headers.get("X-Gateway-Token")
        if secrets.compare_digest(token, query_token or header_token or ""):
            return True
        json_response(self, {"ok": False, "error": "Unauthorized"}, 401)
        return False

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[%s] %s\n" % (now_jst(), fmt % args))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the SC Crypto Gateway paper web tool.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--token", default=os.environ.get("GATEWAY_UI_TOKEN"))
    parser.add_argument("--unsafe-no-token", action="store_true")
    parser.add_argument("--self-test", action="store_true", help="Validate and paper-run the built-in sample, then exit.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        result = run_paper(DEFAULT_INTENT)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") == "paper_recorded" else 1

    public_host = args.host not in {"127.0.0.1", "localhost", "::1"}
    if public_host and not args.token and not args.unsafe_no_token:
        print("Refusing to bind a non-local host without --token or GATEWAY_UI_TOKEN.", file=sys.stderr)
        return 2

    server = ThreadingHTTPServer((args.host, args.port), GatewayHandler)
    server.gateway_token = args.token
    print(f"SC Crypto Gateway Tool v0.1: http://{args.host}:{args.port}/")
    print("Mode: paper only. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
