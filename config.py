"""
ForeSight Configuration
"""
import os

# ─── App Settings ──────────────────────────────────────────
APP_NAME = "ForeSight"
APP_TAGLINE = "Privacy-Preserving Cash Flow Intelligence for MSMEs"
APP_VERSION = "1.0.0"

# ─── Database ──────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "foresight.db")

# ─── Maker-Checker Threshold ──────────────────────────────
MAKER_CHECKER_THRESHOLD = 10000  # ₹10,000

# ─── FHE Settings ─────────────────────────────────────────
FHE_TREE_DEPTH = 4
FHE_QUANTIZATION_BITS = 8
FHE_CACHE_POLL_INTERVAL = 3  # seconds

# ─── Differential Privacy ────────────────────────────────
DP_EPSILON = 1.0

# ─── Sector Baselines (RBI MSME Pulse data) ──────────────
SECTOR_BASELINES = {
    "textile":        {"avg_delay": 52, "default_rate": 0.18, "reliability": 62},
    "auto_ancillary": {"avg_delay": 45, "default_rate": 0.12, "reliability": 71},
    "fmcg":           {"avg_delay": 38, "default_rate": 0.08, "reliability": 78},
    "pharma":         {"avg_delay": 42, "default_rate": 0.10, "reliability": 74},
    "it_services":    {"avg_delay": 35, "default_rate": 0.06, "reliability": 82},
    "construction":   {"avg_delay": 68, "default_rate": 0.22, "reliability": 55},
    "electronics":    {"avg_delay": 40, "default_rate": 0.09, "reliability": 76},
}

# ─── Demo Persona ─────────────────────────────────────────
DEMO_MSME = {
    "name": "Rohan's Precision Components",
    "owner": "Rohan Mehta",
    "sector": "auto_ancillary",
    "employees": 12,
    "gstin": "27AABCU9603R1ZM",
    "monthly_burn": 285000,  # ₹2.85L/month
    "digital_reserves": 180000,
    "cash_reserves": 65000,
}

# ─── Color Palette ────────────────────────────────────────
COLORS = {
    "primary":     "#00D4AA",
    "primary_dim": "#00A88A",
    "secondary":   "#6366F1",
    "accent":      "#F59E0B",
    "danger":      "#EF4444",
    "warning":     "#F97316",
    "success":     "#10B981",
    "info":        "#3B82F6",
    "bg_dark":     "#0A0E17",
    "bg_card":     "#111827",
    "bg_hover":    "#1F2937",
    "text":        "#E2E8F0",
    "text_dim":    "#94A3B8",
    "border":      "#1E293B",
}
