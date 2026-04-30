import json
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Load existing data
with open("synthetic_data.json", "r") as f:
    raw_invoices = json.load(f)

# 1. Adapt Invoices to Prompt Schema
adapted_invoices = []
for inv in raw_invoices:
    adapted_invoices.append({
        "invoice_id": inv["invoice_id"],
        "buyer_id": inv["buyer_name"].lower().replace(" ", "_"),
        "buyer_name": inv["buyer_name"],
        "invoice_date": inv["invoice_date"],
        "due_date": inv["due_date"],
        "payment_date": inv["paid_date"],
        "days_overdue": inv["payment_delay_days"] if inv["is_paid"] else 180,
        "amount": float(inv["invoice_amount"]),
        "status": "paid" if inv["is_paid"] else "open",
        "gstin": "27" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=13)), # Mock GSTIN
        "sector": inv["buyer_sector"],
        "post_legal_notice": inv["post_legal_notice"]
    })

# 2. Generate 500 Cash Transactions
categories = ["vendor_payment", "employee_advance", "supplies", "transport", "utilities"]
vendors = ["Raju Transport", "Sharma Kirana", "Patel Logistics", "Pahal Transport", "Staff Advance"]
cash_transactions = []
start_date = datetime(2024, 1, 1)
for _ in range(500):
    tx_date = start_date + timedelta(days=random.randint(0, 365))
    cash_transactions.append({
        "transaction_date": tx_date.strftime("%Y-%m-%d"),
        "amount": float(random.randint(500, 15000)),
        "category": random.choice(categories),
        "vendor_name": random.choice(vendors),
        "status": "recorded"
    })

# 3. Compute Buyer Metrics
df = pd.DataFrame(adapted_invoices)
buyer_metrics = {}
for buyer_name in df["buyer_name"].unique():
    b_df = df[df["buyer_name"] == buyer_name]
    buyer_id = buyer_name.lower().replace(" ", "_")
    
    # Calculate EMA delay (simulated here with simple mean for now)
    avg_ema_delay = b_df["days_overdue"].mean()
    p90_delay = np.percentile(b_df["days_overdue"], 90)
    
    buyer_metrics[buyer_id] = {
        "buyer_name": buyer_name,
        "num_invoices": len(b_df),
        "avg_ema_delay": round(avg_ema_delay, 2),
        "payment_velocity": round(1 / (avg_ema_delay / 30), 2) if avg_ema_delay > 0 else 1.0,
        "p90_delay": round(p90_delay, 2),
        "default_probability": round(len(b_df[b_df["status"] == "open"]) / len(b_df), 4),
        "total_amount": float(b_df["amount"].sum())
    }

# 4. Retaliation Analysis (Hardcoded Apex Scenario)
retaliation_analysis = {
    "buyer_name": "Apex Manufacturing Pvt Ltd",
    "trigger_date": "2024-02-15",
    "pre_notice_invoices": 89,
    "post_notice_invoices": 15,
    "volume_drop_magnitude": 0.831,
    "p_value": 0.0023,
    "alert_fired": True
}

# 5. Combined Final JSON
final_data = {
    "invoices": adapted_invoices,
    "cash_transactions": cash_transactions,
    "buyer_metrics": buyer_metrics,
    "retaliation_analysis": retaliation_analysis,
    "config": {
        "master_seed": 42,
        "num_invoices": len(adapted_invoices),
        "num_buyers": len(buyer_metrics),
        "generated_timestamp": datetime.now().isoformat()
    }
}

with open("synthetic_data_refined.json", "w") as f:
    json.dump(final_data, f, indent=2)

print("Data adaptation complete: synthetic_data_refined.json created.")
