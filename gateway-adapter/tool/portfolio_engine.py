from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import secrets
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "portfolios.v0.1.json"
STATE_PATH = ROOT / "state" / "portfolio-state.v0.1.json"
REPORT_DIR = ROOT / "records" / "paper-executions"
DASHBOARD_DATA_PATH = ROOT.parent / "dashboard" / "crypto-pdca" / "data.json"
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

MODE_RANK = {"paper": 0, "shadow": 1, "live_confirmed": 2, "live_auto": 3}
APPROVAL_RANK = {"manual": 0, "auto": 1}


def now_jst() -> str:
    return dt.datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    return load_json(path)


def load_state(path: Path = STATE_PATH) -> dict[str, Any]:
    return load_json(path)


def save_state(state: dict[str, Any], path: Path = STATE_PATH) -> None:
    state["updated_at_jst"] = now_jst()
    write_json(path, state)


def portfolios_by_id(config: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    config = config or load_config()
    return {item["portfolio_id"]: item for item in config.get("portfolios", [])}


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


def portfolio_totals(portfolio_state: dict[str, Any]) -> dict[str, float]:
    positions = portfolio_state.get("positions", {})
    investment_cost = 0.0
    investment_value = 0.0
    unrealized = 0.0
    for position in positions.values():
        if position.get("position_status") == "Closed":
            continue
        cost = float(position.get("cost_basis_jpy") or 0)
        value = float(position.get("current_valuation_jpy") or 0)
        investment_cost += cost
        investment_value += value
        unrealized += value - cost
    cash = float(portfolio_state.get("cash_jpy") or 0)
    realized = float(portfolio_state.get("realized_pnl_jpy") or 0)
    total_asset = cash + investment_value
    return {
        "cash_jpy": cash,
        "investment_cost_jpy": investment_cost,
        "investment_value_jpy": investment_value,
        "realized_pnl_jpy": realized,
        "unrealized_pnl_jpy": unrealized,
        "total_asset_jpy": total_asset,
    }


def validate_intent(intent: dict[str, Any], config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(intent, dict):
        return {"ok": False, "errors": ["Intent must be a JSON object."], "warnings": []}

    required = [
        "schema_version",
        "intent_id",
        "idempotency_key",
        "portfolio_id",
        "created_at_jst",
        "created_by",
        "intent_type",
        "execution_mode",
        "venue_type",
        "venue",
        "asset_flow",
        "risk",
        "safety",
        "ledger",
        "reason",
    ]
    for field in required:
        if field not in intent:
            errors.append(f"Missing required field: {field}")

    if intent.get("schema_version") != "0.1":
        errors.append("schema_version must be 0.1")

    intent_id = intent.get("intent_id")
    if not isinstance(intent_id, str) or not re.match(r"^INT-[0-9]{8}-[0-9]{3,6}$", intent_id):
        errors.append("intent_id must match INT-YYYYMMDD-001 format.")

    idempotency_key = intent.get("idempotency_key")
    if not isinstance(idempotency_key, str) or not re.match(r"^[a-zA-Z0-9._:-]{8,120}$", idempotency_key):
        errors.append("idempotency_key must be an 8-120 character stable key.")

    config = load_config(config_path)
    portfolio_map = portfolios_by_id(config)
    portfolio_id = intent.get("portfolio_id")
    portfolio_config = portfolio_map.get(portfolio_id)
    if not portfolio_config:
        errors.append(f"Unknown portfolio_id: {portfolio_id}")

    execution_mode = intent.get("execution_mode")
    if execution_mode not in MODE_RANK:
        errors.append("execution_mode is invalid.")

    if intent.get("venue_type") not in {"cex", "wallet", "defi", "dapp", "manual"}:
        errors.append("venue_type is invalid.")

    secret_paths = walk_secret_like_keys(intent)
    if secret_paths:
        errors.append("Intent contains secret-like keys: " + ", ".join(secret_paths))

    asset_flow = intent.get("asset_flow", {})
    risk = intent.get("risk", {})
    if not isinstance(asset_flow, dict):
        errors.append("asset_flow must be an object.")
        asset_flow = {}
    if not isinstance(risk, dict):
        errors.append("risk must be an object.")
        risk = {}

    if portfolio_config:
        limits = portfolio_config.get("risk_limits", {})
        configured_mode = portfolio_config.get("execution_mode")
        if MODE_RANK.get(execution_mode, 99) > MODE_RANK.get(configured_mode, -1):
            errors.append(
                f"Intent execution_mode={execution_mode} exceeds portfolio execution_mode={configured_mode}."
            )
        if execution_mode not in limits.get("allowed_execution_modes", []):
            errors.append(f"execution_mode is not allowed by portfolio: {execution_mode}")
        if intent.get("venue_type") not in limits.get("allowed_venue_types", []):
            errors.append(f"venue_type is not allowed by portfolio: {intent.get('venue_type')}")
        if intent.get("venue") not in limits.get("allowed_venues", []):
            errors.append(f"venue is not allowed by portfolio: {intent.get('venue')}")

        requested_approval = intent.get("approval_policy")
        if requested_approval:
            configured_approval = portfolio_config.get("approval_policy")
            if APPROVAL_RANK.get(requested_approval, 99) > APPROVAL_RANK.get(configured_approval, -1):
                errors.append(
                    f"Intent approval_policy={requested_approval} exceeds portfolio approval_policy={configured_approval}."
                )

        for field in ("max_loss_jpy", "slippage_bps_max", "gas_jpy_max", "fee_jpy_max"):
            value = risk.get(field)
            limit = limits.get(field)
            if isinstance(value, (int, float)) and isinstance(limit, (int, float)) and value > limit:
                errors.append(f"risk.{field} exceeds portfolio limit {limit}.")

        reserve = risk.get("cash_reserve_ratio_min")
        configured_reserve = portfolio_config.get("cash_reserve_ratio")
        if isinstance(reserve, (int, float)) and reserve < configured_reserve:
            errors.append("Intent cash_reserve_ratio_min may not be lower than portfolio config.")

        asset_candidates = {asset_flow.get("from_asset"), asset_flow.get("to_asset")}
        allowed_assets = set(limits.get("allowed_assets", []))
        for asset in asset_candidates:
            if asset and asset not in allowed_assets:
                errors.append(f"asset is not allowed by portfolio: {asset}")

        amount_jpy = asset_flow.get("amount_jpy")
        if isinstance(amount_jpy, (int, float)) and amount_jpy > limits.get("max_order_jpy", amount_jpy):
            errors.append("asset_flow.amount_jpy exceeds portfolio max_order_jpy.")
        if isinstance(amount_jpy, (int, float)) and amount_jpy <= 0:
            errors.append("asset_flow.amount_jpy must be greater than 0 when provided.")

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

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "portfolio_id": portfolio_id,
        "effective_policy": policy_snapshot(portfolio_config) if portfolio_config else None,
    }


def policy_snapshot(portfolio_config: dict[str, Any]) -> dict[str, Any]:
    return {
        "portfolio_id": portfolio_config.get("portfolio_id"),
        "execution_mode": portfolio_config.get("execution_mode"),
        "approval_policy": portfolio_config.get("approval_policy"),
        "cash_reserve_ratio": portfolio_config.get("cash_reserve_ratio"),
        "investment_ratio": portfolio_config.get("investment_ratio"),
        "entry_matrix_profile": portfolio_config.get("entry_matrix_profile"),
        "risk_limits": portfolio_config.get("risk_limits", {}),
    }


def execution_price_jpy(intent: dict[str, Any], portfolio_state: dict[str, Any], symbol: str) -> float | None:
    asset_flow = intent.get("asset_flow", {})
    price = asset_flow.get("price_limit")
    currency = asset_flow.get("price_limit_currency")
    if isinstance(price, (int, float)) and currency == "JPY" and price > 0:
        return float(price)
    existing = portfolio_state.get("positions", {}).get(symbol, {})
    existing_price = existing.get("current_price_jpy")
    if isinstance(existing_price, (int, float)) and existing_price > 0:
        return float(existing_price)
    return None


def effective_approval_policy(intent: dict[str, Any], portfolio_config: dict[str, Any]) -> str:
    if portfolio_config.get("approval_policy") == "manual":
        return "manual"
    if intent.get("approval_policy") == "manual":
        return "manual"
    risk = intent.get("risk", {}) if isinstance(intent.get("risk"), dict) else {}
    safety = intent.get("safety", {}) if isinstance(intent.get("safety"), dict) else {}
    toggles = safety.get("toggles", {}) if isinstance(safety.get("toggles"), dict) else {}
    if risk.get("requires_manual_confirm") is True or toggles.get("require_manual_confirm") is True:
        return "manual"
    return "auto"


def event_notional_jpy(event: dict[str, Any]) -> float:
    for key in ("notional_jpy", "amount_jpy", "gross_jpy"):
        value = event.get(key)
        if isinstance(value, (int, float)):
            return abs(float(value))
    return 0.0


def daily_executed_notional_jpy(portfolio_state: dict[str, Any], jst_date: str) -> float:
    total = 0.0
    for event in portfolio_state.get("executed_intents", []):
        executed_at = str(event.get("executed_at_jst") or "")
        if executed_at[:10] != jst_date:
            continue
        if str(event.get("status", "")).startswith("paper_"):
            total += event_notional_jpy(event)
    return total


def effective_min_cash_jpy(portfolio_config: dict[str, Any]) -> float:
    limits = portfolio_config.get("risk_limits", {})
    configured_min = float(limits.get("min_cash_jpy") or 0)
    initial = float(portfolio_config.get("initial_capital_jpy") or 0)
    reserve = float(portfolio_config.get("cash_reserve_ratio") or 0)
    return max(configured_min, initial * reserve)


def enforce_risk_limits(
    intent: dict[str, Any],
    portfolio_config: dict[str, Any],
    portfolio_state: dict[str, Any],
    *,
    side: str,
    symbol: str,
    notional_jpy: float,
    fee_jpy: float,
) -> dict[str, Any]:
    limits = portfolio_config.get("risk_limits", {})
    totals_before = portfolio_totals(portfolio_state)
    jst_date = now_jst()[:10]

    max_order = limits.get("max_order_jpy")
    if isinstance(max_order, (int, float)) and notional_jpy > float(max_order):
        return {"ok": False, "reason": "Order would exceed portfolio max_order_jpy."}

    daily_limit = limits.get("daily_order_limit_jpy")
    daily_before = daily_executed_notional_jpy(portfolio_state, jst_date)
    if isinstance(daily_limit, (int, float)) and daily_before + notional_jpy > float(daily_limit):
        return {
            "ok": False,
            "reason": "Order would exceed portfolio daily_order_limit_jpy.",
            "details": {"jst_date": jst_date, "daily_before_jpy": daily_before, "order_notional_jpy": notional_jpy},
        }

    if side == "BUY":
        projected_cash = totals_before["cash_jpy"] - notional_jpy - fee_jpy
        min_cash = effective_min_cash_jpy(portfolio_config)
        if projected_cash < min_cash:
            return {
                "ok": False,
                "reason": "BUY would break portfolio cash reserve / min_cash_jpy.",
                "details": {"projected_cash_jpy": projected_cash, "min_cash_jpy": min_cash},
            }

        existing = portfolio_state.get("positions", {}).get(symbol, {})
        existing_cost = 0.0
        if existing and existing.get("position_status") != "Closed":
            existing_cost = float(existing.get("cost_basis_jpy") or 0)
        projected_position_cost = existing_cost + notional_jpy
        max_position = limits.get("max_position_cost_jpy")
        if isinstance(max_position, (int, float)) and projected_position_cost > float(max_position):
            return {
                "ok": False,
                "reason": "BUY would exceed portfolio max_position_cost_jpy.",
                "details": {
                    "symbol": symbol,
                    "projected_position_cost_jpy": projected_position_cost,
                    "max_position_cost_jpy": float(max_position),
                },
            }

        projected_total_investment = totals_before["investment_cost_jpy"] + notional_jpy
        max_total = limits.get("max_total_investment_jpy")
        if isinstance(max_total, (int, float)) and projected_total_investment > float(max_total):
            return {
                "ok": False,
                "reason": "BUY would exceed portfolio max_total_investment_jpy.",
                "details": {
                    "projected_total_investment_jpy": projected_total_investment,
                    "max_total_investment_jpy": float(max_total),
                },
            }

    return {"ok": True}


def state_fingerprint(state: dict[str, Any]) -> str:
    encoded = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_paper(
    intent: dict[str, Any],
    *,
    config_path: Path = CONFIG_PATH,
    state_path: Path = STATE_PATH,
    report_dir: Path = REPORT_DIR,
    write_report: bool = True,
) -> dict[str, Any]:
    validation = validate_intent(intent, config_path=config_path)
    if not validation["ok"]:
        return {"status": "rejected", "created_at_jst": now_jst(), "validation": validation, "report": None}
    if intent.get("execution_mode") != "paper":
        return {
            "status": "rejected",
            "created_at_jst": now_jst(),
            "validation": validation,
            "report": None,
            "reason": "This tool only runs execution_mode=paper.",
        }

    state = load_state(state_path)
    config = load_config(config_path)
    portfolio_map = portfolios_by_id(config)
    portfolio_id = intent["portfolio_id"]
    portfolio_config = portfolio_map[portfolio_id]
    portfolio_state = state["portfolios"][portfolio_id]
    idempotency_key = intent["idempotency_key"]

    prior_intent = portfolio_state.setdefault("idempotency_keys", {}).get(idempotency_key)
    if prior_intent:
        return {
            "status": "duplicate_intent",
            "created_at_jst": now_jst(),
            "validation": validation,
            "report": {
                "portfolio_id": portfolio_id,
                "intent_id": intent.get("intent_id"),
                "idempotency_key": idempotency_key,
                "prior_intent_id": prior_intent,
                "note": "No state mutation was performed.",
            },
        }

    effective_approval = effective_approval_policy(intent, portfolio_config)
    if portfolio_config.get("execution_mode") != "paper" or effective_approval != "auto":
        return {
            "status": "pending_approval",
            "created_at_jst": now_jst(),
            "validation": validation,
            "report": {
                "portfolio_id": portfolio_id,
                "intent_id": intent.get("intent_id"),
                "idempotency_key": idempotency_key,
                "effective_approval_policy": effective_approval,
                "portfolio_execution_mode": portfolio_config.get("execution_mode"),
                "note": "No state mutation was performed.",
            },
        }

    result = execute_state_transition(intent, portfolio_config, portfolio_state)
    if not result["ok"]:
        return {
            "status": "rejected",
            "created_at_jst": now_jst(),
            "validation": validation,
            "report": None,
            "reason": result["reason"],
        }

    report_id = f"PER-{dt.datetime.now(JST).strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}"
    event = result["event"]
    portfolio_state.setdefault("executed_intents", []).append(event)
    portfolio_state.setdefault("idempotency_keys", {})[idempotency_key] = intent["intent_id"]
    state["portfolios"][portfolio_id] = portfolio_state
    save_state(state, state_path)

    report = {
        "report_id": report_id,
        "schema_version": "0.1",
        "created_at_jst": now_jst(),
        "status": "paper_recorded",
        "intent_id": intent.get("intent_id"),
        "idempotency_key": idempotency_key,
        "portfolio_id": portfolio_id,
        "execution_mode": "paper",
        "venue_type": intent.get("venue_type"),
        "venue": intent.get("venue"),
        "effective_policy": policy_snapshot(portfolio_config) | {"effective_approval_policy": effective_approval},
        "paper_execution": event,
        "portfolio_totals_after": portfolio_totals(portfolio_state),
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
            {"event": "portfolio_policy_applied", "at_jst": now_jst()},
            {"event": "paper_recorded", "at_jst": now_jst()},
        ],
    }

    if write_report:
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"{report_id}.json"
        write_json(report_path, report)
        report["local_report_path"] = str(report_path)
    return {"status": "paper_recorded", "created_at_jst": now_jst(), "validation": validation, "report": report}


def execute_state_transition(
    intent: dict[str, Any],
    portfolio_config: dict[str, Any],
    portfolio_state: dict[str, Any],
) -> dict[str, Any]:
    asset_flow = intent.get("asset_flow", {})
    side = asset_flow.get("side")
    symbol = asset_flow.get("to_asset") if side == "BUY" else asset_flow.get("from_asset")
    if not symbol or symbol == "JPY":
        return {"ok": False, "reason": "Paper trade requires a non-JPY asset symbol."}
    symbol = str(symbol).upper()
    price_jpy = execution_price_jpy(intent, portfolio_state, symbol)
    if not price_jpy:
        return {"ok": False, "reason": "Paper execution requires price_limit in JPY or an existing current_price_jpy."}

    fee_limit = portfolio_config.get("risk_limits", {}).get("fee_jpy_max", 0)
    fee_jpy = min(float(fee_limit or 0), max(0.0, float(asset_flow.get("amount_jpy") or 0) * 0.001))
    positions = portfolio_state.setdefault("positions", {})
    executed_at = now_jst()

    if side == "BUY":
        amount_jpy = asset_flow.get("amount_jpy")
        if not isinstance(amount_jpy, (int, float)) or amount_jpy <= 0:
            return {"ok": False, "reason": "BUY requires asset_flow.amount_jpy."}
        notional_jpy = float(amount_jpy)
        total_debit = float(amount_jpy) + fee_jpy
        totals_before = portfolio_totals(portfolio_state)
        projected_cash = totals_before["cash_jpy"] - total_debit
        risk_check = enforce_risk_limits(
            intent,
            portfolio_config,
            portfolio_state,
            side="BUY",
            symbol=symbol,
            notional_jpy=notional_jpy,
            fee_jpy=fee_jpy,
        )
        if not risk_check["ok"]:
            return risk_check

        qty = float(amount_jpy) / price_jpy
        existing = positions.get(symbol)
        if existing and existing.get("position_status") != "Closed":
            old_qty = float(existing.get("quantity") or 0)
            old_cost = float(existing.get("cost_basis_jpy") or 0)
            new_qty = old_qty + qty
            new_cost = old_cost + float(amount_jpy)
            existing["quantity"] = new_qty
            existing["cost_basis_jpy"] = new_cost
            existing["average_entry_jpy"] = new_cost / new_qty if new_qty else price_jpy
            position = existing
        else:
            position = {
                "symbol": symbol,
                "coingecko_id": asset_flow.get("coingecko_id") or symbol.lower(),
                "quantity": qty,
                "average_entry_jpy": price_jpy,
                "average_entry_usd": None,
                "cost_basis_jpy": float(amount_jpy),
                "decision": "Paper executed",
                "position_status": "Open",
            }
        position["current_price_jpy"] = price_jpy
        position["current_price_usd"] = None
        position["current_valuation_jpy"] = position["quantity"] * price_jpy
        position["unrealized_pnl_jpy"] = position["current_valuation_jpy"] - position["cost_basis_jpy"]
        positions[symbol] = position
        portfolio_state["cash_jpy"] = projected_cash
        event = {
            "intent_id": intent["intent_id"],
            "idempotency_key": intent["idempotency_key"],
            "executed_at_jst": executed_at,
            "status": "paper_buy_recorded",
            "side": "BUY",
            "symbol": symbol,
            "amount_jpy": float(amount_jpy),
            "notional_jpy": notional_jpy,
            "quantity_delta": qty,
            "executed_price_jpy": price_jpy,
            "fee_jpy_estimate": fee_jpy,
            "cash_after_jpy": projected_cash,
        }
        return {"ok": True, "event": event}

    if side == "SELL":
        existing = positions.get(symbol)
        if not existing or existing.get("position_status") == "Closed":
            return {"ok": False, "reason": f"No open paper position for SELL: {symbol}"}
        current_qty = float(existing.get("quantity") or 0)
        amount_type = asset_flow.get("amount_type")
        if amount_type == "full_balance":
            qty = current_qty
        elif asset_flow.get("from_amount") is not None:
            qty = float(asset_flow.get("from_amount"))
        elif isinstance(asset_flow.get("amount_jpy"), (int, float)):
            qty = float(asset_flow["amount_jpy"]) / price_jpy
        else:
            return {"ok": False, "reason": "SELL requires full_balance, from_amount, or amount_jpy."}
        if qty <= 0 or qty > current_qty:
            return {"ok": False, "reason": "SELL quantity exceeds open paper position."}

        avg = float(existing.get("average_entry_jpy") or price_jpy)
        cost_reduction = avg * qty
        gross = price_jpy * qty
        risk_check = enforce_risk_limits(
            intent,
            portfolio_config,
            portfolio_state,
            side="SELL",
            symbol=symbol,
            notional_jpy=gross,
            fee_jpy=fee_jpy,
        )
        if not risk_check["ok"]:
            return risk_check
        proceeds = gross - fee_jpy
        realized = proceeds - cost_reduction
        remaining_qty = current_qty - qty
        existing["quantity"] = remaining_qty
        existing["cost_basis_jpy"] = max(0.0, float(existing.get("cost_basis_jpy") or 0) - cost_reduction)
        existing["current_price_jpy"] = price_jpy
        existing["current_valuation_jpy"] = remaining_qty * price_jpy
        existing["unrealized_pnl_jpy"] = existing["current_valuation_jpy"] - existing["cost_basis_jpy"]
        if remaining_qty <= 0.0000000001:
            existing["quantity"] = 0
            existing["position_status"] = "Closed"
            existing["closed_at_jst"] = executed_at
        positions[symbol] = existing
        portfolio_state["cash_jpy"] = float(portfolio_state.get("cash_jpy") or 0) + proceeds
        portfolio_state["realized_pnl_jpy"] = float(portfolio_state.get("realized_pnl_jpy") or 0) + realized
        event = {
            "intent_id": intent["intent_id"],
            "idempotency_key": intent["idempotency_key"],
            "executed_at_jst": executed_at,
            "status": "paper_sell_recorded",
            "side": "SELL",
            "symbol": symbol,
            "quantity_delta": -qty,
            "executed_price_jpy": price_jpy,
            "gross_jpy": gross,
            "notional_jpy": gross,
            "fee_jpy_estimate": fee_jpy,
            "realized_pnl_jpy": realized,
            "cash_after_jpy": portfolio_state["cash_jpy"],
        }
        return {"ok": True, "event": event}

    return {"ok": False, "reason": "Stateful paper executor supports BUY and SELL only in v0.1."}


def normalize_price_snapshot(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_prices = snapshot.get("prices", snapshot)
    normalized: dict[str, dict[str, Any]] = {}
    if isinstance(raw_prices, dict):
        items = raw_prices.items()
    elif isinstance(raw_prices, list):
        items = [(item.get("symbol") or item.get("coingecko_id"), item) for item in raw_prices if isinstance(item, dict)]
    else:
        items = []

    for key, value in items:
        if not key or not isinstance(value, dict):
            continue
        price_jpy = value.get("price_jpy", value.get("jpy"))
        price_usd = value.get("price_usd", value.get("usd"))
        if not isinstance(price_jpy, (int, float)) or price_jpy <= 0:
            continue
        record = {
            "current_price_jpy": float(price_jpy),
            "current_price_usd": float(price_usd) if isinstance(price_usd, (int, float)) else None,
            "source": value.get("source"),
        }
        normalized[str(key).upper()] = record
        coingecko_id = value.get("coingecko_id") or value.get("id")
        if coingecko_id:
            normalized[str(coingecko_id).upper()] = record
        symbol = value.get("symbol")
        if symbol:
            normalized[str(symbol).upper()] = record
    return normalized


def refresh_portfolio_metrics(
    portfolio_state: dict[str, Any],
    portfolio_config: dict[str, Any],
    *,
    at_jst: str | None = None,
) -> dict[str, Any]:
    totals = portfolio_totals(portfolio_state)
    initial = float(portfolio_config.get("initial_capital_jpy") or 0)
    total_pnl = totals["total_asset_jpy"] - initial
    portfolio_state["current_valuation_jpy"] = totals["investment_value_jpy"]
    portfolio_state["unrealized_pnl_jpy"] = totals["unrealized_pnl_jpy"]
    portfolio_state["total_asset_jpy"] = totals["total_asset_jpy"]
    portfolio_state["total_pnl_jpy"] = total_pnl
    portfolio_state["total_pnl_pct"] = (total_pnl / initial * 100) if initial else 0
    if at_jst:
        portfolio_state["last_mark_to_market_at_jst"] = at_jst
    return totals


def mark_to_market(
    snapshot: dict[str, Any],
    *,
    config_path: Path = CONFIG_PATH,
    state_path: Path = STATE_PATH,
    write_state: bool = True,
) -> dict[str, Any]:
    config = load_config(config_path)
    state = load_state(state_path)
    portfolio_map = portfolios_by_id(config)
    prices = normalize_price_snapshot(snapshot)
    at_jst = snapshot.get("created_at_jst") if isinstance(snapshot.get("created_at_jst"), str) else now_jst()
    portfolio_filter = snapshot.get("portfolio_id")
    updates: list[dict[str, Any]] = []

    before_cash = {
        portfolio_id: portfolio_state.get("cash_jpy")
        for portfolio_id, portfolio_state in state.get("portfolios", {}).items()
    }
    before_quantities = {
        portfolio_id: {
            symbol: position.get("quantity")
            for symbol, position in portfolio_state.get("positions", {}).items()
        }
        for portfolio_id, portfolio_state in state.get("portfolios", {}).items()
    }

    for portfolio_id, portfolio_state in state.get("portfolios", {}).items():
        if portfolio_filter and portfolio_filter != portfolio_id:
            continue
        portfolio_config = portfolio_map[portfolio_id]
        for symbol, position in portfolio_state.get("positions", {}).items():
            if position.get("position_status") == "Closed":
                continue
            lookup_keys = [
                str(symbol).upper(),
                str(position.get("coingecko_id") or "").upper(),
            ]
            price = next((prices[key] for key in lookup_keys if key in prices), None)
            if not price:
                continue
            old_price = position.get("current_price_jpy")
            current_price_jpy = price["current_price_jpy"]
            quantity = float(position.get("quantity") or 0)
            cost = float(position.get("cost_basis_jpy") or 0)
            position["current_price_jpy"] = current_price_jpy
            position["current_price_usd"] = price.get("current_price_usd")
            position["current_valuation_jpy"] = quantity * current_price_jpy
            position["unrealized_pnl_jpy"] = position["current_valuation_jpy"] - cost
            position["last_price_source"] = price.get("source")
            position["last_mark_to_market_at_jst"] = at_jst
            updates.append(
                {
                    "portfolio_id": portfolio_id,
                    "symbol": symbol,
                    "old_price_jpy": old_price,
                    "current_price_jpy": current_price_jpy,
                    "current_valuation_jpy": position["current_valuation_jpy"],
                    "unrealized_pnl_jpy": position["unrealized_pnl_jpy"],
                }
            )
        refresh_portfolio_metrics(portfolio_state, portfolio_config, at_jst=at_jst)

    after_cash = {
        portfolio_id: portfolio_state.get("cash_jpy")
        for portfolio_id, portfolio_state in state.get("portfolios", {}).items()
    }
    after_quantities = {
        portfolio_id: {
            symbol: position.get("quantity")
            for symbol, position in portfolio_state.get("positions", {}).items()
        }
        for portfolio_id, portfolio_state in state.get("portfolios", {}).items()
    }
    if before_cash != after_cash or before_quantities != after_quantities:
        raise RuntimeError("mark_to_market attempted to mutate cash or quantity")

    if write_state:
        save_state(state, state_path)
    return {
        "status": "mark_to_market_recorded",
        "created_at_jst": now_jst(),
        "snapshot_at_jst": at_jst,
        "updates_count": len(updates),
        "updates": updates,
        "state": state,
    }


def project_dashboard_data() -> dict[str, Any]:
    base = load_json(DASHBOARD_DATA_PATH) if DASHBOARD_DATA_PATH.exists() else {}
    config = load_config()
    state = load_state()
    portfolio_map = portfolios_by_id(config)
    projected_portfolios: list[dict[str, Any]] = []
    positions: list[dict[str, Any]] = []
    scenario_summary: dict[str, Any] = {}

    scenario_keys = {
        "core45_cash55": "core45Cash55",
        "speculative_meme_parallel": "memeParallel",
    }
    scenario_labels = {
        "core45_cash55": "Core",
        "speculative_meme_parallel": "Meme",
    }

    for portfolio_id, portfolio_state in state.get("portfolios", {}).items():
        portfolio_config = portfolio_map[portfolio_id]
        totals = portfolio_totals(portfolio_state)
        initial = float(portfolio_config.get("initial_capital_jpy") or 0)
        pnl = totals["total_asset_jpy"] - initial
        pnl_pct = (pnl / initial * 100) if initial else 0
        open_positions = []
        for symbol, position in portfolio_state.get("positions", {}).items():
            if position.get("position_status") == "Closed":
                continue
            current_value = float(position.get("current_valuation_jpy") or 0)
            cost = float(position.get("cost_basis_jpy") or 0)
            row = {
                "portfolio_id": portfolio_id,
                "portfolio_name": portfolio_config.get("name"),
                "scenario": scenario_labels.get(portfolio_id, portfolio_id),
                "symbol": symbol,
                "id": position.get("coingecko_id") or symbol.lower(),
                "quantity": position.get("quantity"),
                "amountJpy": round(cost),
                "entryJpy": position.get("average_entry_jpy"),
                "entryUsd": position.get("average_entry_usd"),
                "currentJpy": position.get("current_price_jpy"),
                "currentUsd": position.get("current_price_usd"),
                "valueJpy": round(current_value),
                "pnlJpy": round(current_value - cost),
                "pnlPct": round(((current_value / cost - 1) * 100) if cost else 0, 2),
                "decision": position.get("decision") or "Hold",
                "positionStatus": position.get("position_status") or "Open",
            }
            open_positions.append(row)
            positions.append(row)

        projected = {
            "portfolio_id": portfolio_id,
            "name": portfolio_config.get("name"),
            "initial_capital_jpy": portfolio_config.get("initial_capital_jpy"),
            "cash_reserve_ratio": portfolio_config.get("cash_reserve_ratio"),
            "investment_ratio": portfolio_config.get("investment_ratio"),
            "entry_matrix_profile": portfolio_config.get("entry_matrix_profile"),
            "execution_mode": portfolio_config.get("execution_mode"),
            "approval_policy": portfolio_config.get("approval_policy"),
            "risk_limits": portfolio_config.get("risk_limits"),
            "cash_jpy": round(totals["cash_jpy"]),
            "investment_cost_jpy": round(totals["investment_cost_jpy"]),
            "investment_value_jpy": round(totals["investment_value_jpy"]),
            "realized_pnl_jpy": round(totals["realized_pnl_jpy"]),
            "unrealized_pnl_jpy": round(totals["unrealized_pnl_jpy"]),
            "total_asset_jpy": round(totals["total_asset_jpy"]),
            "total_pnl_jpy": round(pnl),
            "total_pnl_pct": round(pnl_pct, 2),
            "positions": open_positions,
            "executed_intents_count": len(portfolio_state.get("executed_intents", [])),
        }
        projected_portfolios.append(projected)
        key = scenario_keys.get(portfolio_id, portfolio_id)
        scenario_summary[key] = {
            "totalCapitalJpy": round(initial),
            "fixedCashJpy": round(totals["cash_jpy"]),
            "investmentFrameJpy": round(initial * float(portfolio_config.get("investment_ratio") or 0)),
            "paperPurchaseJpy": round(totals["investment_cost_jpy"]),
            "activePaperCostJpy": round(totals["investment_cost_jpy"]),
            "activeInvestmentValueJpy": round(totals["investment_value_jpy"]),
            "investmentValueJpy": round(totals["investment_value_jpy"]),
            "realizedPnlJpy": round(totals["realized_pnl_jpy"]),
            "totalValueInclCashJpy": round(totals["total_asset_jpy"]),
            "investmentPnlPct": round(
                ((totals["investment_value_jpy"] + totals["realized_pnl_jpy"]) / totals["investment_cost_jpy"] - 1) * 100
                if totals["investment_cost_jpy"]
                else 0,
                2,
            ),
            "totalAssetPnlPct": round(pnl_pct, 2),
            "decision": current_portfolio_decision(open_positions),
        }

    data = deepcopy(base)
    data["schemaVersion"] = "2026.08.08.dashboard.portfolio-state.v1"
    data["updatedAtJst"] = now_jst()
    data.setdefault("source", {})["portfolioConfig"] = "gateway-adapter/config/portfolios.v0.1.json"
    data.setdefault("source", {})["portfolioState"] = "gateway-adapter/state/portfolio-state.v0.1.json"
    data.setdefault("source", {})["dashboardProjector"] = "gateway-adapter/tool/portfolio_engine.py"
    data["portfolioConfig"] = config
    data["portfolios"] = projected_portfolios
    data["positions"] = positions
    data["scenarioSummary"] = scenario_summary
    return data


def current_portfolio_decision(open_positions: list[dict[str, Any]]) -> str:
    if not open_positions:
        return "No open positions"
    stops = [item["symbol"] for item in open_positions if "Stop" in str(item.get("decision"))]
    reduce_watch = [item["symbol"] for item in open_positions if "Reduce" in str(item.get("decision"))]
    if stops:
        return "Stop watch: " + " / ".join(stops)
    if reduce_watch:
        return "Reduce watch: " + " / ".join(reduce_watch)
    return "Hold / no add"


def write_dashboard_data() -> dict[str, Any]:
    data = project_dashboard_data()
    write_json(DASHBOARD_DATA_PATH, data)
    return data


def test_intent(
    *,
    intent_id: str,
    idempotency_key: str,
    portfolio_id: str = "speculative_meme_parallel",
    symbol: str = "HYPE",
    coingecko_id: str = "hyperliquid",
    amount_jpy: float = 10000,
    price_jpy: float = 8573.7125,
    requires_manual_confirm: bool = False,
    approval_policy: str | None = None,
) -> dict[str, Any]:
    intent: dict[str, Any] = {
        "schema_version": "0.1",
        "intent_id": intent_id,
        "idempotency_key": idempotency_key,
        "portfolio_id": portfolio_id,
        "created_at_jst": "2026-08-08 15:05 JST",
        "created_by": "system",
        "source": {
            "chat_title": "SC Crypto Gateway self-test",
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
            "to_asset": symbol,
            "coingecko_id": coingecko_id,
            "from_contract_address": None,
            "to_contract_address": None,
            "amount_type": "jpy_budget",
            "amount_jpy": amount_jpy,
            "from_amount": None,
            "to_amount_min": None,
            "price_limit": price_jpy,
            "price_limit_currency": "JPY",
        },
        "risk": {
            "max_loss_jpy": 10000,
            "slippage_bps_max": 100,
            "gas_jpy_max": 0,
            "fee_jpy_max": 1000,
            "daily_limit_jpy_group": "default",
            "cash_reserve_ratio_min": 0.55,
            "requires_manual_confirm": requires_manual_confirm,
            "stop_loss_condition": "self-test",
            "take_profit_condition": "self-test",
        },
        "safety": {
            "safety_profile": "strict",
            "toggles": {
                "require_manual_confirm": requires_manual_confirm,
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
        "reason": "Stateful paper executor self-test.",
        "notes": None,
    }
    if approval_policy:
        intent["approval_policy"] = approval_policy
    return intent


def copy_fixture_paths(tmp: Path) -> tuple[Path, Path, Path]:
    config_path = tmp / "config" / "portfolios.v0.1.json"
    state_path = tmp / "state" / "portfolio-state.v0.1.json"
    report_dir = tmp / "records" / "paper-executions"
    write_json(config_path, load_config())
    write_json(state_path, load_state())
    report_dir.mkdir(parents=True, exist_ok=True)
    return config_path, state_path, report_dir


def record_test(name: str, passed: bool, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "passed": passed, "details": details or {}}


def run_self_tests() -> dict[str, Any]:
    production_before = state_fingerprint(load_state())
    results: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="sc-crypto-gateway-self-test-") as tmp_name:
        tmp = Path(tmp_name)

        config_path, state_path, report_dir = copy_fixture_paths(tmp)
        intent = test_intent(intent_id="INT-20260808-9001", idempotency_key="selftest:auto:9001")
        result = run_paper(intent, config_path=config_path, state_path=state_path, report_dir=report_dir, write_report=False)
        state_after = load_state(state_path)
        results.append(
            record_test(
                "auto paper -> paper_recorded",
                result.get("status") == "paper_recorded"
                and "selftest:auto:9001" in state_after["portfolios"]["speculative_meme_parallel"]["idempotency_keys"],
                {"status": result.get("status")},
            )
        )

        config_path, state_path, report_dir = copy_fixture_paths(tmp / "manual")
        before = state_fingerprint(load_state(state_path))
        config = load_config(config_path)
        config["portfolios"][1]["approval_policy"] = "manual"
        write_json(config_path, config)
        intent = test_intent(intent_id="INT-20260808-9002", idempotency_key="selftest:manual:9002")
        result = run_paper(intent, config_path=config_path, state_path=state_path, report_dir=report_dir, write_report=False)
        after = state_fingerprint(load_state(state_path))
        results.append(
            record_test(
                "manual paper -> pending_approval and state unchanged",
                result.get("status") == "pending_approval" and before == after,
                {"status": result.get("status")},
            )
        )

        config_path, state_path, report_dir = copy_fixture_paths(tmp / "intent-manual")
        before = state_fingerprint(load_state(state_path))
        intent = test_intent(
            intent_id="INT-20260808-9003",
            idempotency_key="selftest:intent-manual:9003",
            requires_manual_confirm=True,
        )
        result = run_paper(intent, config_path=config_path, state_path=state_path, report_dir=report_dir, write_report=False)
        after = state_fingerprint(load_state(state_path))
        results.append(
            record_test(
                "auto portfolio + manual intent -> pending_approval and state unchanged",
                result.get("status") == "pending_approval" and before == after,
                {"status": result.get("status")},
            )
        )

        config_path, state_path, report_dir = copy_fixture_paths(tmp / "duplicate")
        intent = test_intent(intent_id="INT-20260808-9004", idempotency_key="selftest:duplicate:9004")
        first = run_paper(intent, config_path=config_path, state_path=state_path, report_dir=report_dir, write_report=False)
        before_second = state_fingerprint(load_state(state_path))
        second = run_paper(intent, config_path=config_path, state_path=state_path, report_dir=report_dir, write_report=False)
        after_second = state_fingerprint(load_state(state_path))
        results.append(
            record_test(
                "duplicate idempotency -> state unchanged",
                first.get("status") == "paper_recorded"
                and second.get("status") == "duplicate_intent"
                and before_second == after_second,
                {"first": first.get("status"), "second": second.get("status")},
            )
        )

        config_path, state_path, report_dir = copy_fixture_paths(tmp / "cash")
        before = state_fingerprint(load_state(state_path))
        intent = test_intent(
            intent_id="INT-20260808-9005",
            idempotency_key="selftest:cash:9005",
            portfolio_id="core45_cash55",
            symbol="ETH",
            coingecko_id="ethereum",
            amount_jpy=10000,
            price_jpy=500000,
        )
        result = run_paper(intent, config_path=config_path, state_path=state_path, report_dir=report_dir, write_report=False)
        after = state_fingerprint(load_state(state_path))
        results.append(
            record_test(
                "cash 55% constraint exceeded -> rejected",
                result.get("status") == "rejected"
                and "cash reserve" in str(result.get("reason", ""))
                and before == after,
                {"status": result.get("status"), "reason": result.get("reason")},
            )
        )

        config_path, state_path, report_dir = copy_fixture_paths(tmp / "max-total")
        config = load_config(config_path)
        config["portfolios"][0]["risk_limits"]["min_cash_jpy"] = 0
        config["portfolios"][0]["cash_reserve_ratio"] = 0
        write_json(config_path, config)
        before = state_fingerprint(load_state(state_path))
        intent = test_intent(
            intent_id="INT-20260808-9006",
            idempotency_key="selftest:max-total:9006",
            portfolio_id="core45_cash55",
            symbol="ETH",
            coingecko_id="ethereum",
            amount_jpy=10000,
            price_jpy=500000,
        )
        result = run_paper(intent, config_path=config_path, state_path=state_path, report_dir=report_dir, write_report=False)
        after = state_fingerprint(load_state(state_path))
        results.append(
            record_test(
                "max total investment exceeded -> rejected",
                result.get("status") == "rejected"
                and "max_total_investment" in str(result.get("reason", ""))
                and before == after,
                {"status": result.get("status"), "reason": result.get("reason")},
            )
        )

        config_path, state_path, report_dir = copy_fixture_paths(tmp / "daily")
        state = load_state(state_path)
        state["portfolios"]["speculative_meme_parallel"]["executed_intents"].append(
            {
                "intent_id": "INT-20260808-DAILY-SEED",
                "idempotency_key": "selftest:daily-seed",
                "executed_at_jst": now_jst(),
                "status": "paper_buy_recorded",
                "symbol": "HYPE",
                "notional_jpy": 145000,
            }
        )
        write_json(state_path, state)
        before = state_fingerprint(load_state(state_path))
        intent = test_intent(intent_id="INT-20260808-9007", idempotency_key="selftest:daily:9007")
        result = run_paper(intent, config_path=config_path, state_path=state_path, report_dir=report_dir, write_report=False)
        after = state_fingerprint(load_state(state_path))
        results.append(
            record_test(
                "daily limit exceeded -> rejected",
                result.get("status") == "rejected"
                and "daily_order_limit" in str(result.get("reason", ""))
                and before == after,
                {"status": result.get("status"), "reason": result.get("reason")},
            )
        )

        config_path, state_path, report_dir = copy_fixture_paths(tmp / "mtm")
        before_state = load_state(state_path)
        before_cash = before_state["portfolios"]["speculative_meme_parallel"]["cash_jpy"]
        before_qty = before_state["portfolios"]["speculative_meme_parallel"]["positions"]["PUMP"]["quantity"]
        before_value = before_state["portfolios"]["speculative_meme_parallel"]["positions"]["PUMP"]["current_valuation_jpy"]
        snapshot = {
            "created_at_jst": "2026-08-08 16:00 JST",
            "prices": {
                "PUMP": {"price_jpy": 0.4, "price_usd": 0.002536, "source": "self-test"},
                "aave": {"price_jpy": 15000, "price_usd": 95.09, "source": "self-test"},
            },
        }
        result = mark_to_market(snapshot, config_path=config_path, state_path=state_path, write_state=True)
        after_state = load_state(state_path)
        after_cash = after_state["portfolios"]["speculative_meme_parallel"]["cash_jpy"]
        after_qty = after_state["portfolios"]["speculative_meme_parallel"]["positions"]["PUMP"]["quantity"]
        after_value = after_state["portfolios"]["speculative_meme_parallel"]["positions"]["PUMP"]["current_valuation_jpy"]
        results.append(
            record_test(
                "mark-to-market -> valuation only",
                result.get("status") == "mark_to_market_recorded"
                and before_cash == after_cash
                and before_qty == after_qty
                and before_value != after_value,
                {
                    "status": result.get("status"),
                    "updates_count": result.get("updates_count"),
                    "cash_unchanged": before_cash == after_cash,
                    "quantity_unchanged": before_qty == after_qty,
                },
            )
        )

    production_after = state_fingerprint(load_state())
    results.append(
        record_test(
            "self-test -> production state unchanged",
            production_before == production_after,
            {"production_state_fingerprint": production_after},
        )
    )

    return {
        "ok": all(item["passed"] for item in results),
        "created_at_jst": now_jst(),
        "results": results,
    }
