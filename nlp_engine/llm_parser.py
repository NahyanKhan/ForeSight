"""
ForeSight — LLM Cash Message Parser
Parses informal Telegram cash messages into structured JSON
using Ollama/Llama 3 (JSON mode) with a regex fallback.

Example: "Paid 5k cash to Raju for transport"
→ {"action": "expense", "amount": 5000, "vendor": "Raju", "category": "transport"}
"""

import re
import json
import requests
from datetime import datetime

# ─── Ollama Configuration ────────────────────────────────
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3:8b-instruct-q4_0"
OLLAMA_TIMEOUT = 15  # seconds

# ─── System Prompt (forces JSON output) ──────────────────
SYSTEM_PROMPT = """You are a cash transaction parser for an Indian MSME.
Extract structured data from informal cash messages.
You MUST respond with ONLY valid JSON, no other text.

Output format:
{"action": "expense"|"income"|"refund", "amount": <number>, "vendor": "<name>", "category": "<category>"}

Categories: transport, raw_material, wages, utilities, maintenance, misc, sales, refund

Rules:
- "5k" means 5000, "10k" means 10000, "1.5L" means 150000
- Remove ₹ symbol, commas from amounts
- If vendor unclear, use "unknown"
- If category unclear, use "misc"
- "Paid" / "gave" / "spent" = expense
- "Received" / "got" / "collected" = income
"""

# ─── Category Keywords (for regex fallback) ──────────────
CATEGORY_KEYWORDS = {
    "transport": ["transport", "truck", "delivery", "courier", "shipping", "freight", "auto", "petrol", "diesel", "fuel"],
    "raw_material": ["raw", "material", "steel", "metal", "fabric", "cloth", "chemical", "parts", "component", "supply"],
    "wages": ["wages", "salary", "labour", "labor", "worker", "staff", "pay", "advance"],
    "utilities": ["electricity", "water", "phone", "internet", "wifi", "bill", "recharge"],
    "maintenance": ["repair", "maintenance", "fix", "service", "plumber", "electrician"],
    "sales": ["sales", "order", "sold", "revenue", "customer", "payment received"],
    "refund": ["refund", "return", "credit note", "adjustment"],
}


# ─── Amount Normalization ────────────────────────────────
def normalize_amount(text: str) -> float | None:
    """
    Normalize Indian informal amount strings to float.
    Handles: "5k", "₹5,000", "5000", "1.5L", "2.5 lakh", "50K"
    """
    text = text.strip().replace("₹", "").replace(",", "").replace(" ", "")

    # Match patterns like "5k", "10K", "1.5k"
    match = re.match(r'^(\d+\.?\d*)\s*[kK]$', text)
    if match:
        return float(match.group(1)) * 1000

    # Match patterns like "1.5L", "2L", "1.5 lakh"
    match = re.match(r'^(\d+\.?\d*)\s*[lL](?:akh)?$', text, re.IGNORECASE)
    if match:
        return float(match.group(1)) * 100000

    # Plain number
    match = re.match(r'^(\d+\.?\d*)$', text)
    if match:
        return float(match.group(1))

    return None


def _extract_amount_from_text(text: str) -> float | None:
    """Extract the first amount-like token from a full message."""
    # Try patterns in order of specificity
    patterns = [
        r'₹\s*([\d,]+\.?\d*)\s*[kK]',         # ₹5k, ₹ 5K
        r'₹\s*([\d,]+\.?\d*)\s*[lL](?:akh)?',  # ₹1.5L, ₹1.5 lakh
        r'₹\s*([\d,]+\.?\d*)',                   # ₹5,000
        r'(\d+\.?\d*)\s*[kK]\b',                # 5k, 10K
        r'(\d+\.?\d*)\s*[lL](?:akh)?\b',        # 1.5L, 1.5 lakh
        r'\b(\d{3,})\b',                         # 5000, 15000 (3+ digits)
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            raw = match.group(1).replace(",", "")
            val = float(raw)
            # Apply multiplier based on suffix
            suffix_match = re.search(pattern, text)
            full = suffix_match.group(0).lower()
            if 'k' in full and 'lakh' not in full:
                val *= 1000
            elif 'l' in full:
                val *= 100000
            return val
    return None


def _extract_vendor_from_text(text: str) -> str:
    """Extract vendor name from informal message using pattern matching."""
    # "to <Name>" pattern
    match = re.search(r'\bto\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
    if match:
        return match.group(1).strip()

    # "from <Name>" pattern
    match = re.search(r'\bfrom\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
    if match:
        return match.group(1).strip()

    # "<Name> ko" pattern (Hindi)
    match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+ko\b', text)
    if match:
        return match.group(1).strip()

    return "unknown"


def _extract_category_from_text(text: str) -> str:
    """Match category by keyword lookup."""
    text_lower = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category
    return "misc"


def _detect_action(text: str) -> str:
    """Detect whether this is an expense, income, or refund."""
    text_lower = text.lower()
    income_words = ["received", "got", "collected", "incoming", "credit"]
    refund_words = ["refund", "return", "credited back"]
    for w in refund_words:
        if w in text_lower:
            return "refund"
    for w in income_words:
        if w in text_lower:
            return "income"
    return "expense"


# ─── Regex Fallback Parser ───────────────────────────────
def regex_fallback_parse(text: str) -> dict:
    """
    Pure regex parser for when Ollama fails.
    Always returns a valid result — never silently fails.
    """
    amount = _extract_amount_from_text(text)
    vendor = _extract_vendor_from_text(text)
    category = _extract_category_from_text(text)
    action = _detect_action(text)

    return {
        "action": action,
        "amount": amount or 0,
        "vendor": vendor,
        "category": category,
        "confidence": 0.6,
        "parser": "regex_fallback",
    }


# ─── Ollama LLM Parser ──────────────────────────────────
def llm_parse(text: str) -> dict:
    """
    Parse via Ollama Llama 3 in JSON mode.
    Falls back to regex if Ollama is down or returns garbage.
    """
    prompt = f"{SYSTEM_PROMPT}\n\nMessage: \"{text}\"\n\nJSON:"

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
            timeout=OLLAMA_TIMEOUT,
        )

        if response.status_code != 200:
            return regex_fallback_parse(text)

        raw_response = response.json().get("response", "")

        # Try to parse the JSON from Llama's output
        parsed = json.loads(raw_response)

        # Validate required fields
        if not isinstance(parsed.get("amount"), (int, float)):
            parsed["amount"] = _extract_amount_from_text(text) or 0

        llm_amount = float(parsed.get("amount", 0))

        # Cross-validate LLM amount against regex extraction
        # Llama sometimes hallucinates numeric conversions (e.g., 8000 → 800000)
        regex_amount = _extract_amount_from_text(text)
        if regex_amount and llm_amount > 0:
            ratio = max(llm_amount, regex_amount) / max(min(llm_amount, regex_amount), 1)
            if ratio >= 10:
                # LLM amount is wildly off (e.g. extra zero) — trust regex
                llm_amount = regex_amount

        result = {
            "action": parsed.get("action", _detect_action(text)),
            "amount": llm_amount,
            "vendor": parsed.get("vendor", "unknown"),
            "category": parsed.get("category", "misc"),
            "confidence": 0.95,
            "parser": "llama3",
        }
        return result

    except (json.JSONDecodeError, KeyError):
        # Llama returned malformed JSON — regex fallback
        return regex_fallback_parse(text)
    except requests.exceptions.RequestException:
        # Ollama not running — regex fallback
        return regex_fallback_parse(text)


# ─── Main Entry Point ────────────────────────────────────
def parse_cash_message(text: str) -> dict:
    """
    Parse a cash transaction message. Tries Ollama first, falls back to regex.
    Returns: {action, amount, vendor, category, confidence, parser, timestamp}
    """
    result = llm_parse(text)
    result["raw_message"] = text
    result["timestamp"] = datetime.now().isoformat()
    return result


# ─── CLI Test ────────────────────────────────────────────
if __name__ == "__main__":
    test_messages = [
        "Paid 5k cash to Raju for transport",
        "Gave 15000 to Sita Devi for raw material",
        "Received 25k from Kumar Electricals for repairs",
        "Spent 2.5k on diesel for delivery truck",
        "Manoj ko 8000 diya maintenance ke liye",
    ]

    print("=" * 60)
    print("ForeSight LLM Parser — Test Suite")
    print("=" * 60)

    for msg in test_messages:
        print(f"\nInput: \"{msg}\"")
        result = parse_cash_message(msg)
        print(f"  Action:   {result['action']}")
        print(f"  Amount:   Rs.{result['amount']:,.0f}")
        print(f"  Vendor:   {result['vendor']}")
        print(f"  Category: {result['category']}")
        print(f"  Parser:   {result['parser']} (conf: {result['confidence']})")
