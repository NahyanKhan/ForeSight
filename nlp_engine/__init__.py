"""
nlp_engine — NLP & Telegram Bot Silo
Handles: Ollama/Llama 3 JSON parsing, regex fallback parser,
         vendor alias table, spaCy contract clause detection,
         Telegram bot webhook integration.
"""

from nlp_engine.llm_parser import parse_cash_message
from nlp_engine.vendor_aliases import resolve_vendor
from nlp_engine.contract_detector import extract_pdf_text, detect_dark_patterns
