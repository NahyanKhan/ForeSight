import os
import json
import random
import joblib
import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

# =========================================================
# INVOICEIQ DEV 3 - ALL IN ONE (HACKATHON VERSION)
# =========================================================
# This script does everything:
# 1. Sets deterministic seeds
# 2. Generates synthetic Indian MSME invoice data
# 3. Simulates retaliation scenario (Apex volume drop)
# 4. Builds buyer reliability model
# 5. Calculates survival runway
# 6. Saves outputs for Dev 1 / Dev 2 handoff
# =========================================================

# -----------------------------
# 1) GLOBAL CONFIG / SEEDS
# -----------------------------
MASTER_RANDOM_SEED = 42
random.seed(MASTER_RANDOM_SEED)
np.random.seed(MASTER_RANDOM_SEED)

try:
    fake = Faker("en_IN")   # safer than hi_IN in many environments
except:
    fake = Faker()

Faker.seed(MASTER_RANDOM_SEED)

OUTPUT_DIR = "."
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2024, 12, 31)
LEGAL_NOTICE_DATE = datetime(2024, 9, 1)

# -----------------------------
# 2) BUYER PERSONAS
# -----------------------------
BUYERS = [
    {
        "buyer_name": "Apex Manufacturing Pvt Ltd",
        "sector": "Manufacturing",
        "base_delay_mean": 75,
        "base_delay_std": 18,
        "invoice_value_mean": 145000,
        "invoice_value_std": 40000,
        "risk_level": "high",
        "retaliation_target": True
    },
    {
        "buyer_name": "Shree Retail Distributors",
        "sector": "Retail",
        "base_delay_mean": 42,
        "base_delay_std": 10,
        "invoice_value_mean": 80000,
        "invoice_value_std": 20000,
        "risk_level": "medium",
        "retaliation_target": False
    },
    {
        "buyer_name": "Metro Infra Suppliers",
        "sector": "Infrastructure",
        "base_delay_mean": 65,
        "base_delay_std": 15,
        "invoice_value_mean": 175000,
        "invoice_value_std": 50000,
        "risk_level": "high",
        "retaliation_target": False
    },
    {
        "buyer_name": "Bright Foods Trading Co",
        "sector": "FMCG",
        "base_delay_mean": 28,
        "base_delay_std": 8,
        "invoice_value_mean": 60000,
        "invoice_value_std": 15000,
        "risk_level": "low",
        "retaliation_target": False
    },
    {
        "buyer_name": "Zenith Pharma Supplies",
        "sector": "Pharma",
        "base_delay_mean": 38,
        "base_delay_std": 12,
        "invoice_value_mean": 95000,
        "invoice_value_std": 25000,
        "risk_level": "medium",
        "retaliation_target": False
    },
    {
        "buyer_name": "Kaveri Engineering Works",
        "sector": "Engineering",
        "base_delay_mean": 55,
        "base_delay_std": 14,
        "invoice_value_mean": 125000,
        "invoice_value_std": 35000,
        "risk_level": "medium",
        "retaliation_target": False
    },
    {
        "buyer_name": "National Packaging House",
        "sector": "Packaging",
        "base_delay_mean": 32,
        "base_delay_std": 9,
        "invoice_value_mean": 70000,
        "invoice_value_std": 18000,
        "risk_level": "low",
        "retaliation_target": False
    },
    {
        "buyer_name": "Urban Build Projects Ltd",
        "sector": "Construction",
        "base_delay_mean": 58,
        "base_delay_std": 16,
        "invoice_value_mean": 160000,
        "invoice_value_std": 45000,
        "risk_level": "high",
        "retaliation_target": False
    }
]

MSME_COMPANIES = [
    "Noor Textiles",
    "Ayesha Plastics",
    "Star Agro Traders",
    "Green Leaf Components",
    "Safa Metal Works",
    "BlueStone Electricals",
    "Mira Fabrication",
    "Unity Packaging",
    "Crescent Fasteners",
    "Nova Tooling Solutions"
]

# -----------------------------
# 3) HELPER FUNCTIONS
# -----------------------------
def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))

def random_invoice_date():
    delta_days = (END_DATE - START_DATE).days
    offset = random.randint(0, delta_days)
    return START_DATE + timedelta(days=offset)

def make_invoice_id(i):
    return f"INV-{2024}-{i:05d}"

def make_company_profile():
    company_name = random.choice(MSME_COMPANIES)
    monthly_fixed_cost = random.randint(300000, 900000)
    cash_reserves = random.randint(600000, 2500000)
    avg_monthly_revenue = random.randint(500000, 2200000)
    return {
        "msme_company": company_name,
        "monthly_fixed_cost": monthly_fixed_cost,
        "cash_reserves": cash_reserves,
        "avg_monthly_revenue": avg_monthly_revenue
    }

# -----------------------------
# 4) GENERATE SYNTHETIC INVOICES
# -----------------------------
def generate_invoices(num_invoices=5000):
    invoices = []
    company_profile = make_company_profile()

    buyer_weights_pre = {
        "Apex Manufacturing Pvt Ltd": 0.28,
        "Shree Retail Distributors": 0.10,
        "Metro Infra Suppliers": 0.12,
        "Bright Foods Trading Co": 0.10,
        "Zenith Pharma Supplies": 0.10,
        "Kaveri Engineering Works": 0.10,
        "National Packaging House": 0.10,
        "Urban Build Projects Ltd": 0.10,
    }

    buyer_weights_post = {
        "Apex Manufacturing Pvt Ltd": 0.05,
        "Shree Retail Distributors": 0.14,
        "Metro Infra Suppliers": 0.14,
        "Bright Foods Trading Co": 0.14,
        "Zenith Pharma Supplies": 0.13,
        "Kaveri Engineering Works": 0.13,
        "National Packaging House": 0.13,
        "Urban Build Projects Ltd": 0.14,
    }

    buyer_map = {b["buyer_name"]: b for b in BUYERS}

    def weighted_choice(weight_dict):
        items = list(weight_dict.items())
        names = [x[0] for x in items]
        weights = [x[1] for x in items]
        return random.choices(names, weights=weights, k=1)[0]

    for i in range(1, num_invoices + 1):
        inv_date = random_invoice_date()

        if inv_date < LEGAL_NOTICE_DATE:
            buyer_name = weighted_choice(buyer_weights_pre)
        else:
            buyer_name = weighted_choice(buyer_weights_post)

        buyer = buyer_map[buyer_name]

        amount = max(
            15000,
            int(np.random.normal(buyer["invoice_value_mean"], buyer["invoice_value_std"]))
        )

        delay = int(np.random.normal(buyer["base_delay_mean"], buyer["base_delay_std"]))

        if buyer["retaliation_target"] and inv_date >= LEGAL_NOTICE_DATE:
            delay += random.randint(10, 30)

        delay = clamp(delay, 7, 180)

        due_date = inv_date + timedelta(days=30)
        paid_date = due_date + timedelta(days=delay)
        is_paid = 1

        default_prob = 0.01
        if buyer["risk_level"] == "medium":
            default_prob = 0.03
        elif buyer["risk_level"] == "high":
            default_prob = 0.07

        if buyer["retaliation_target"] and inv_date >= LEGAL_NOTICE_DATE:
            default_prob += 0.05

        if random.random() < default_prob:
            is_paid = 0
            paid_date = None

        invoice = {
            "invoice_id": make_invoice_id(i),
            "msme_company": company_profile["msme_company"],
            "buyer_name": buyer_name,
            "buyer_sector": buyer["sector"],
            "invoice_date": inv_date.strftime("%Y-%m-%d"),
            "due_date": due_date.strftime("%Y-%m-%d"),
            "paid_date": paid_date.strftime("%Y-%m-%d") if paid_date else None,
            "invoice_amount": amount,
            "payment_delay_days": delay if is_paid else 180,
            "is_paid": is_paid,
            "monthly_fixed_cost": company_profile["monthly_fixed_cost"],
            "cash_reserves": company_profile["cash_reserves"],
            "avg_monthly_revenue": company_profile["avg_monthly_revenue"],
            "buyer_risk_level": buyer["risk_level"],
            "post_legal_notice": 1 if inv_date >= LEGAL_NOTICE_DATE else 0
        }

        invoices.append(invoice)

    return pd.DataFrame(invoices)

# -----------------------------
# 5) RETALIATION ANALYSIS
# -----------------------------
def analyze_retaliation(df):
    apex = df[df["buyer_name"] == "Apex Manufacturing Pvt Ltd"].copy()
    apex["invoice_date"] = pd.to_datetime(apex["invoice_date"])

    pre = apex[apex["invoice_date"] < LEGAL_NOTICE_DATE]
    post = apex[apex["invoice_date"] >= LEGAL_NOTICE_DATE]

    pre_count = len(pre)
    post_count = len(post)

    pre_monthly = pre_count / 8 if pre_count > 0 else 0
    post_monthly = post_count / 4 if post_count > 0 else 0

    drop_pct = 0
    if pre_monthly > 0:
        drop_pct = (pre_monthly - post_monthly) / pre_monthly

    alert_fired = drop_pct >= 0.60

    return {
        "buyer": "Apex Manufacturing Pvt Ltd",
        "pre_legal_invoice_count": pre_count,
        "post_legal_invoice_count": post_count,
        "pre_monthly_avg": round(pre_monthly, 2),
        "post_monthly_avg": round(post_monthly, 2),
        "volume_drop_magnitude": round(drop_pct, 4),
        "alert_fired": alert_fired
    }

# -----------------------------
# 6) BUYER SUMMARY FEATURES
# -----------------------------
def build_buyer_summary(df):
    summary = df.groupby("buyer_name").agg(
        total_invoices=("invoice_id", "count"),
        total_value=("invoice_amount", "sum"),
        avg_invoice_value=("invoice_amount", "mean"),
        avg_delay=("payment_delay_days", "mean"),
        max_delay=("payment_delay_days", "max"),
        paid_ratio=("is_paid", "mean"),
        post_legal_share=("post_legal_notice", "mean")
    ).reset_index()

    total_portfolio_value = summary["total_value"].sum()
    summary["concentration_ratio"] = summary["total_value"] / total_portfolio_value

    # reliability score heuristic target (0-100)
    # lower delay, higher paid ratio, lower concentration risk = better
    summary["reliability_score_target"] = (
        100
        - (summary["avg_delay"] * 0.45)
        - ((1 - summary["paid_ratio"]) * 40)
        - (summary["concentration_ratio"] * 25)
        - (summary["post_legal_share"] * 5)
    )

    summary["reliability_score_target"] = summary["reliability_score_target"].clip(5, 95)

    return summary

# -----------------------------
# 7) TRAIN MODEL
# -----------------------------
def train_buyer_model(summary_df):
    features = [
        "total_invoices",
        "total_value",
        "avg_invoice_value",
        "avg_delay",
        "max_delay",
        "paid_ratio",
        "post_legal_share",
        "concentration_ratio"
    ]

    X = summary_df[features].copy()
    y = summary_df["reliability_score_target"].copy()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # small dataset -> use all data; split only if enough
    if len(summary_df) >= 6:
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.25, random_state=MASTER_RANDOM_SEED
        )
        model = RandomForestRegressor(
            n_estimators=150,
            max_depth=5,
            random_state=MASTER_RANDOM_SEED
        )
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        r2 = r2_score(y_test, preds)
    else:
        model = RandomForestRegressor(
            n_estimators=150,
            max_depth=5,
            random_state=MASTER_RANDOM_SEED
        )
        model.fit(X_scaled, y)
        preds = model.predict(X_scaled)
        r2 = r2_score(y, preds)

    summary_df["predicted_reliability_score"] = model.predict(X_scaled).round(2)

    return model, scaler, summary_df, r2

# -----------------------------
# 8) RUNWAY CALCULATOR
# -----------------------------
def calculate_runway(df):
    company_row = df.iloc[0]

    cash_reserves = float(company_row["cash_reserves"])
    monthly_fixed_cost = float(company_row["monthly_fixed_cost"])

    # Monthly collections estimate from paid invoices
    paid_df = df[df["is_paid"] == 1].copy()
    paid_df["invoice_date"] = pd.to_datetime(paid_df["invoice_date"])
    paid_df["month"] = paid_df["invoice_date"].dt.to_period("M")

    monthly_collections = paid_df.groupby("month")["invoice_amount"].sum()

    if len(monthly_collections) == 0:
        avg_monthly_collections = 0
        std_monthly_collections = 0
    else:
        avg_monthly_collections = monthly_collections.mean()
        std_monthly_collections = monthly_collections.std() if len(monthly_collections) > 1 else monthly_collections.mean() * 0.15

    # Burn = fixed cost - collections (if positive)
    avg_monthly_burn = max(monthly_fixed_cost - avg_monthly_collections, monthly_fixed_cost * 0.20)

    base_runway_days = (cash_reserves / avg_monthly_burn) * 30

    # Monte Carlo for 80% CI
    sims = []
    np.random.seed(MASTER_RANDOM_SEED)

    for _ in range(1000):
        simulated_collections = np.random.normal(
            avg_monthly_collections,
            max(std_monthly_collections, avg_monthly_collections * 0.10)
        )
        simulated_collections = max(0, simulated_collections)

        simulated_burn = max(monthly_fixed_cost - simulated_collections, monthly_fixed_cost * 0.20)
        runway_days = (cash_reserves / simulated_burn) * 30
        sims.append(runway_days)

    lower = np.percentile(sims, 10)
    upper = np.percentile(sims, 90)

    return {
        "cash_reserves": round(cash_reserves, 2),
        "monthly_fixed_cost": round(monthly_fixed_cost, 2),
        "avg_monthly_collections": round(avg_monthly_collections, 2),
        "avg_monthly_burn": round(avg_monthly_burn, 2),
        "base_runway_days": round(base_runway_days, 2),
        "runway_80pct_ci_lower": round(lower, 2),
        "runway_80pct_ci_upper": round(upper, 2)
    }

# -----------------------------
# 9) SAVE OUTPUTS
# -----------------------------
def save_outputs(df, buyer_summary, model, scaler, retaliation_report, runway_report):
    csv_path = os.path.join(OUTPUT_DIR, "synthetic_data.csv")
    json_path = os.path.join(OUTPUT_DIR, "synthetic_data.json")
    summary_path = os.path.join(OUTPUT_DIR, "buyer_summary.csv")
    model_path = os.path.join(OUTPUT_DIR, "buyer_reliability_model.pkl")
    scaler_path = os.path.join(OUTPUT_DIR, "scaler.pkl")
    report_path = os.path.join(OUTPUT_DIR, "dev3_report.json")

    df.to_csv(csv_path, index=False)
    df.to_json(json_path, orient="records", indent=2)
    buyer_summary.to_csv(summary_path, index=False)

    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    combined_report = {
        "retaliation_report": retaliation_report,
        "runway_report": runway_report
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(combined_report, f, indent=2)

# -----------------------------
# 10) MAIN EXECUTION
# -----------------------------
def main():
    print("=" * 60)
    print("INVOICEIQ DEV 3 - ALL IN ONE PIPELINE STARTING")
    print("=" * 60)

    # Generate synthetic data
    print("\n[1/5] Generating synthetic invoices...")
    df = generate_invoices(num_invoices=5000)
    print(f"Generated {len(df)} invoices.")

    # Retaliation analysis
    print("\n[2/5] Running retaliation analysis...")
    retaliation_report = analyze_retaliation(df)
    print("Retaliation Report:")
    print(json.dumps(retaliation_report, indent=2))

    # Buyer summary
    print("\n[3/5] Building buyer summary + training reliability model...")
    buyer_summary = build_buyer_summary(df)
    model, scaler, buyer_summary, r2 = train_buyer_model(buyer_summary)

    print(f"Model R² score: {round(r2, 4)}")
    print("\nBuyer Risk Ranking (lowest reliability first):")
    print(
        buyer_summary[["buyer_name", "predicted_reliability_score", "avg_delay", "paid_ratio", "concentration_ratio"]]
        .sort_values("predicted_reliability_score")
        .to_string(index=False)
    )

    # Runway
    print("\n[4/5] Calculating survival runway...")
    runway_report = calculate_runway(df)
    print("Runway Report:")
    print(json.dumps(runway_report, indent=2))

    # Save outputs
    print("\n[5/5] Saving outputs...")
    save_outputs(df, buyer_summary, model, scaler, retaliation_report, runway_report)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE ✅")
    print("=" * 60)
    print("\nGenerated files:")
    print("- synthetic_data.csv")
    print("- synthetic_data.json")
    print("- buyer_summary.csv")
    print("- buyer_reliability_model.pkl")
    print("- scaler.pkl")
    print("- dev3_report.json")

if __name__ == "__main__":
    main()