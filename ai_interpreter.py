"""LLM-backed intent interpretation with a safe deterministic fallback.

The model only returns an allowed intent and optional month parameters. It never
writes SQL. Every calculation is performed by predefined, read-only functions.
"""
import json
import os
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
ALLOWED_INTENTS = {
    "total_revenue", "highest_revenue_product", "monthly_revenue",
    "highest_sales_region", "compare_months", "category_revenue",
    "channel_revenue", "unsupported"
}
MONTHS = {
    "january": "01", "jan": "01", "february": "02", "feb": "02",
    "march": "03", "mar": "03", "april": "04", "apr": "04",
    "may": "05", "june": "06", "jun": "06", "july": "07", "jul": "07",
    "august": "08", "aug": "08", "september": "09", "sep": "09",
    "october": "10", "oct": "10", "november": "11", "nov": "11",
    "december": "12", "dec": "12"
}


def _month_values(question: str):
    q = question.lower()
    matches = []
    for name, number in MONTHS.items():
        for match in re.finditer(rf"\b{name}\s+(20\d{{2}})\b", q):
            matches.append((match.start(), f"{match.group(1)}-{number}"))
    for match in re.finditer(r"\b(20\d{2})-(0[1-9]|1[0-2])\b", q):
        matches.append((match.start(), f"{match.group(1)}-{match.group(2)}"))
    found = []
    for _, item in sorted(matches):
        if item not in found:
            found.append(item)
    return found[:2]


def rule_based_interpret(question: str):
    q = question.lower().strip()
    months = _month_values(q)
    if any(x in q for x in ["compare", "change between", "difference between", "compared with", "versus", " vs "]) and len(months) >= 2:
        return {"intent": "compare_months", "month_a": months[0], "month_b": months[1], "method": "rules"}
    if ("total" in q and ("revenue" in q or "sales" in q or "earned" in q)) or "overall revenue" in q:
        return {"intent": "total_revenue", "method": "rules"}
    if ("product" in q or "item" in q) and any(x in q for x in ["highest", "most", "top", "generated", "earned", "best"]):
        return {"intent": "highest_revenue_product", "method": "rules"}
    if "region" in q and any(x in q for x in ["highest", "most", "best", "sales", "revenue", "top"]):
        return {"intent": "highest_sales_region", "method": "rules"}
    if any(x in q for x in ["monthly", "month-wise", "per month", "each month", "month by month", "trend"]):
        return {"intent": "monthly_revenue", "method": "rules"}
    if "categor" in q and any(x in q for x in ["revenue", "sales", "highest", "breakdown", "performance"]):
        return {"intent": "category_revenue", "method": "rules"}
    if any(x in q for x in ["channel", "online vs retail", "online and retail"]):
        return {"intent": "channel_revenue", "method": "rules"}
    if len(months) >= 2 and any(x in q for x in ["revenue", "sales", "month"]):
        return {"intent": "compare_months", "month_a": months[0], "month_b": months[1], "method": "rules"}
    return {"intent": "unsupported", "method": "rules"}


def interpret_question(question: str):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return rule_based_interpret(question)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        schema = {
            "type": "object",
            "properties": {
                "intent": {"type": "string", "enum": sorted(ALLOWED_INTENTS)},
                "month_a": {"type": ["string", "null"]},
                "month_b": {"type": ["string", "null"]}
            },
            "required": ["intent", "month_a", "month_b"],
            "additionalProperties": False
        }
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=[
                {"role": "system", "content": (
                    "Classify a sales analytics question into exactly one allowed intent. "
                    "Do not answer the question and do not generate SQL. Allowed intents: "
                    "total_revenue, highest_revenue_product, monthly_revenue, "
                    "highest_sales_region, compare_months, category_revenue, "
                    "channel_revenue, unsupported. For compare_months, return month_a and "
                    "month_b as YYYY-MM when identifiable. Only the supplied sales dataset "
                    "is available. If unsupported or unclear, use unsupported."
                )},
                {"role": "user", "content": question}
            ],
            response_format={"type": "json_schema", "json_schema": {"name": "sales_question_intent", "strict": True, "schema": schema}},
            temperature=0
        )
        result = json.loads(response.choices[0].message.content)
        if result.get("intent") not in ALLOWED_INTENTS:
            return rule_based_interpret(question)
        result["method"] = "openai"
        return result
    except Exception:
        # Keep the app usable if the key is absent, the network is unavailable,
        # or the model request fails. The UI reports which interpretation was used.
        result = rule_based_interpret(question)
        result["method"] = "rules_fallback"
        return result
