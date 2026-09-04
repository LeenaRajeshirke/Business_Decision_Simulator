"""
Parses a natural-language decision into a structured decision_type + params.

If AI_PROVIDER is configured and AI_API_KEY is set, this can call an LLM to do
the extraction (see ai_service.py for the provider-agnostic call). If not,
it falls back to transparent rule-based keyword matching so the app still
works with zero external dependencies.

Either way, the EXTRACTED PARAMETERS ARE ALWAYS SHOWN TO THE USER FOR REVIEW
AND EDITING before a simulation runs (see the /simulations router and the
frontend NewSimulation page) — the AI/rules layer never silently drives the
simulation engine.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..config import settings
from .ai_service import call_ai


@dataclass
class ParsedDecision:
    decision_type: str
    decision_params: dict
    parsed_by: str
    note: str | None = None


_PCT_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*%")


def _extract_pct(text: str) -> float | None:
    m = _PCT_RE.search(text)
    if not m:
        return None
    return float(m.group(1)) / 100.0


def _rule_based_parse(decision_text: str) -> ParsedDecision:
    text = decision_text.lower()
    pct = _extract_pct(text) or 0.10  # default assumption if no % found, clearly surfaced to user

    is_decrease = any(w in text for w in ["decrease", "reduce", "lower", "cut", "drop"])
    signed_pct = -abs(pct) if is_decrease else abs(pct)

    if "price" in text:
        return ParsedDecision(
            decision_type="pricing",
            decision_params={"price_change_pct": signed_pct},
            parsed_by="fallback_rules",
            note="Parsed using rule-based keyword matching (no AI provider configured).",
        )
    if "marketing" in text or "ad spend" in text or "advertising" in text:
        return ParsedDecision(
            decision_type="marketing",
            decision_params={"marketing_change_pct": signed_pct},
            parsed_by="fallback_rules",
            note="Parsed using rule-based keyword matching (no AI provider configured).",
        )
    if "hire" in text or "employee" in text or "staff" in text:
        return ParsedDecision(
            decision_type="hiring",
            decision_params={"monthly_salary_cost": 0.0, "expected_customer_lift_pct": 0.03},
            parsed_by="fallback_rules",
            note="Salary cost and expected lift are placeholders — please edit before running.",
        )
    if "branch" in text or "location" in text or "open another" in text or "expand" in text:
        return ParsedDecision(
            decision_type="expansion",
            decision_params={"new_location_fixed_cost": 0.0, "expected_customer_lift_pct": 0.15},
            parsed_by="fallback_rules",
            note="Fixed cost and expected lift are placeholders — please edit before running.",
        )
    if "launch" in text or "new product" in text:
        return ParsedDecision(
            decision_type="product_launch",
            decision_params={"launch_marketing_spend": 0.0, "expected_customer_lift_pct": 0.10},
            parsed_by="fallback_rules",
            note="Launch spend and expected lift are placeholders — please edit before running.",
        )
    if "customers" in text or "demand" in text:
        return ParsedDecision(
            decision_type="pricing",
            decision_params={"price_change_pct": 0.0, "elasticity_band": "medium"},
            parsed_by="fallback_rules",
            note="Could not confidently classify this decision — defaulted to a neutral pricing scenario. Please edit the parameters.",
        )

    return ParsedDecision(
        decision_type="other",
        decision_params={},
        parsed_by="fallback_rules",
        note="Could not classify this decision automatically. Please choose a decision type and enter parameters manually.",
    )


def parse_decision(decision_text: str) -> ParsedDecision:
    if settings.AI_PROVIDER != "none" and settings.AI_API_KEY:
        ai_result = call_ai(
            system_prompt=(
                "You extract structured business-decision parameters from natural language. "
                "Respond ONLY with JSON: "
                '{"decision_type": one of [pricing, marketing, hiring, expansion, product_launch, cost_reduction, other], '
                '"decision_params": {...numbers only...}}'
            ),
            user_prompt=decision_text,
        )
        if ai_result is not None:
            return ParsedDecision(
                decision_type=ai_result.get("decision_type", "other"),
                decision_params=ai_result.get("decision_params", {}),
                parsed_by="ai",
                note="Parsed by AI — please review and edit before running the simulation.",
            )
        # AI call failed/misconfigured — fall through to rules rather than erroring out.

    return _rule_based_parse(decision_text)
