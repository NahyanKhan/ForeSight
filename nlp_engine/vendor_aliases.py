"""
ForeSight — Vendor Alias Table
Maps colloquial vendor names to canonical IDs using RapidFuzz fuzzy matching.
"""

from rapidfuzz import fuzz, process

# ─── Pre-Seeded Vendor Registry ──────────────────────────
VENDOR_REGISTRY = {
    "VND001": {"canonical_name": "Raju Transport", "aliases": ["Raju", "Raju bhai", "Raju Transport", "Raju Transporter"], "category_default": "transport"},
    "VND002": {"canonical_name": "Sita Devi", "aliases": ["Sita", "Sita Devi", "Sita ji", "Sita aunty"], "category_default": "raw_material"},
    "VND003": {"canonical_name": "Manoj Transport", "aliases": ["Manoj", "Manoj Transport", "Manoj bhai", "Manoj Logistics"], "category_default": "transport"},
    "VND004": {"canonical_name": "Kumar Electricals", "aliases": ["Kumar", "Kumar Electricals", "Kumar Electric", "Kumar ji"], "category_default": "utilities"},
    "VND005": {"canonical_name": "Sharma Ji", "aliases": ["Sharma", "Sharma Ji", "Sharma uncle", "Sharmaji"], "category_default": "maintenance"},
    "VND006": {"canonical_name": "Daily Needs Store", "aliases": ["Daily Needs", "Daily Needs Store", "kirana", "kirana store"], "category_default": "misc"},
    "VND007": {"canonical_name": "Priya Metals", "aliases": ["Priya", "Priya Metals", "Priya Steel"], "category_default": "raw_material"},
    "VND008": {"canonical_name": "Gupta Hardware", "aliases": ["Gupta", "Gupta Hardware", "Gupta ji"], "category_default": "raw_material"},
}

FUZZY_THRESHOLD = 75


def _build_alias_index():
    index = {}
    for vid, info in VENDOR_REGISTRY.items():
        for alias in info["aliases"]:
            index[alias.lower()] = (vid, info["canonical_name"])
    return index

_ALIAS_INDEX = _build_alias_index()


def resolve_vendor(name: str) -> dict:
    """Resolve informal vendor name to canonical entry via exact then fuzzy match."""
    if not name or name.lower() == "unknown":
        return {"canonical_name": "Unknown Vendor", "vendor_id": "VND_UNKNOWN", "confidence": 0.0, "matched_alias": None, "category_default": "misc", "is_new": True}

    name_lower = name.lower().strip()

    # Exact match
    if name_lower in _ALIAS_INDEX:
        vid, canonical = _ALIAS_INDEX[name_lower]
        return {"canonical_name": canonical, "vendor_id": vid, "confidence": 1.0, "matched_alias": name_lower, "category_default": VENDOR_REGISTRY[vid]["category_default"], "is_new": False}

    # Fuzzy match
    result = process.extractOne(name_lower, list(_ALIAS_INDEX.keys()), scorer=fuzz.ratio, score_cutoff=FUZZY_THRESHOLD)
    if result:
        matched_alias, score, _ = result
        vid, canonical = _ALIAS_INDEX[matched_alias]
        return {"canonical_name": canonical, "vendor_id": vid, "confidence": round(score / 100, 2), "matched_alias": matched_alias, "category_default": VENDOR_REGISTRY[vid]["category_default"], "is_new": False}

    # No match — new vendor
    return {"canonical_name": name.strip().title(), "vendor_id": f"VND_NEW_{abs(hash(name_lower)) % 10000:04d}", "confidence": 0.0, "matched_alias": None, "category_default": "misc", "is_new": True}


def get_all_vendors():
    return [{"id": vid, "name": info["canonical_name"], "category": info["category_default"]} for vid, info in VENDOR_REGISTRY.items()]


if __name__ == "__main__":
    tests = ["Raju", "Raju bhai", "Raju Tranport", "Sita", "sita devi", "Sharmaji", "Kumar Electric", "New Vendor XYZ", "unknown"]
    print("=" * 60)
    print("ForeSight Vendor Alias Resolver -- Test Suite")
    print("=" * 60)
    for name in tests:
        r = resolve_vendor(name)
        status = "MATCHED" if not r["is_new"] else "NEW"
        print(f"  \"{name}\" -> {r['canonical_name']} ({r['vendor_id']}) [{status}, conf={r['confidence']:.0%}]")
