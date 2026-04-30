"""
ForeSight — Contract Dark Pattern Detector
Extracts text from buyer agreement PDFs and detects 4 dark-pattern
clause types using spaCy rule-based matching + keyword proximity.

Clause Types:
1. Dispute-Triggered Payment Holds
2. Invoicing-Defect Reset
3. Set-Off Rights
4. Force Majeure Loops
"""

import re
import spacy
from spacy.matcher import PhraseMatcher

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = spacy.blank("en")


# ─── Dark Pattern Definitions ────────────────────────────
DARK_PATTERNS = {
    "dispute_hold": {
        "type": "Dispute-Triggered Hold",
        "severity": "Critical",
        "severity_icon": "RED",
        "primary_keywords": ["suspend", "hold", "withhold", "freeze", "halt", "cease", "stop payment", "stay payment"],
        "context_keywords": ["dispute", "claim", "objection", "grievance", "disagreement", "contested", "challenged"],
        "explanation": "Buyer can halt all payments by raising any dispute, regardless of merit.",
        "impact_pct": 0.65,
    },
    "invoice_defect": {
        "type": "Invoicing-Defect Reset",
        "severity": "Critical",
        "severity_icon": "RED",
        "primary_keywords": ["reject", "defect", "error", "discrepancy", "incorrect", "invalid", "non-conforming"],
        "context_keywords": ["reset", "restart", "recommence", "fresh period", "new period", "clock", "45 day", "forty-five", "payment period"],
        "explanation": "Minor invoice errors restart the payment timer, enabling indefinite delays.",
        "impact_pct": 0.40,
    },
    "set_off": {
        "type": "Set-Off Rights",
        "severity": "High",
        "severity_icon": "YELLOW",
        "primary_keywords": ["set off", "set-off", "setoff", "deduct", "offset", "adjust", "withhold against", "net off"],
        "context_keywords": ["future", "subsequent", "owed", "payable", "outstanding", "any amount", "claim against"],
        "explanation": "Buyer can unilaterally deduct arbitrary amounts from payments owed.",
        "impact_pct": 0.25,
    },
    "force_majeure": {
        "type": "Force Majeure Loop",
        "severity": "High",
        "severity_icon": "YELLOW",
        "primary_keywords": ["force majeure", "act of god", "unforeseen circumstances", "beyond control"],
        "context_keywords": ["market conditions", "economic", "business disruption", "commercial", "downturn", "slowdown", "demand", "supply chain", "pandemic"],
        "explanation": "Overly broad force majeure definition allows indefinite payment deferral.",
        "impact_pct": 0.50,
    },
}


def extract_pdf_text(file_or_path) -> str:
    """Extract all text from a PDF using pdfplumber."""
    import pdfplumber

    if isinstance(file_or_path, str):
        with pdfplumber.open(file_or_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    else:
        # File-like object (Streamlit UploadedFile)
        with pdfplumber.open(file_or_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)


def _find_surrounding_sentence(text: str, match_start: int, match_end: int, context_chars: int = 200) -> str:
    """Extract surrounding context around a match for display."""
    start = max(0, match_start - context_chars)
    end = min(len(text), match_end + context_chars)
    snippet = text[start:end].strip()
    # Clean up to nearest sentence boundaries
    if start > 0:
        dot_pos = snippet.find(".")
        if dot_pos > 0 and dot_pos < 50:
            snippet = snippet[dot_pos + 1:].strip()
    if end < len(text):
        dot_pos = snippet.rfind(".")
        if dot_pos > len(snippet) - 50:
            snippet = snippet[:dot_pos + 1]
    return snippet


def detect_dark_patterns(text: str, total_outstanding: float = 847000) -> list:
    """
    Detect dark-pattern clauses in contract text.
    Uses keyword proximity matching: primary keyword within 150 chars of context keyword.
    
    Returns list of detected patterns with severity, clause text, and impact estimates.
    """
    findings = []
    text_lower = text.lower()

    for pattern_id, pattern in DARK_PATTERNS.items():
        for primary in pattern["primary_keywords"]:
            primary_lower = primary.lower()
            # Find all occurrences of primary keyword
            for match in re.finditer(re.escape(primary_lower), text_lower):
                p_start, p_end = match.start(), match.end()

                # Check if any context keyword appears within 150 chars
                window_start = max(0, p_start - 150)
                window_end = min(len(text_lower), p_end + 150)
                window = text_lower[window_start:window_end]

                for context_kw in pattern["context_keywords"]:
                    if context_kw.lower() in window:
                        clause_text = _find_surrounding_sentence(text, p_start, p_end)
                        impact = total_outstanding * pattern["impact_pct"]

                        findings.append({
                            "type": pattern["type"],
                            "severity": pattern["severity"],
                            "severity_icon": pattern["severity_icon"],
                            "clause": f'"{clause_text[:150]}..."' if len(clause_text) > 150 else f'"{clause_text}"',
                            "impact": f"Rs.{impact:,.0f} at risk" if pattern["impact_pct"] < 1 else "Indefinite delay risk",
                            "explanation": pattern["explanation"],
                            "pattern_id": pattern_id,
                            "matched_primary": primary,
                            "matched_context": context_kw,
                        })
                        break  # One context match per primary is enough
                else:
                    continue
                break  # One primary match per pattern type is enough

    # Deduplicate by pattern type
    seen_types = set()
    deduped = []
    for f in findings:
        if f["type"] not in seen_types:
            seen_types.add(f["type"])
            deduped.append(f)

    return deduped


if __name__ == "__main__":
    import os
    demo_path = os.path.join(os.path.dirname(__file__), "demo_contract.pdf")
    if os.path.exists(demo_path):
        print("=" * 60)
        print("ForeSight Contract Detector -- Demo Contract Analysis")
        print("=" * 60)
        text = extract_pdf_text(demo_path)
        print(f"Extracted {len(text)} chars from PDF\n")
        results = detect_dark_patterns(text)
        for r in results:
            print(f"  [{r['severity']}] {r['type']}")
            print(f"    Impact: {r['impact']}")
            print(f"    {r['explanation']}")
            print(f"    Clause: {r['clause'][:100]}...")
            print()
        print(f"Total patterns detected: {len(results)}/4")
    else:
        print("demo_contract.pdf not found. Run generate_demo_contract first.")
