"""
ForeSight — Synthetic Data Generator
Generates realistic MSME invoice and transaction data using Faker (hi_IN locale)
with a fixed seed for reproducible demo scenarios.
"""

import random
import sqlite3
import os
from datetime import datetime, timedelta
from faker import Faker

fake = Faker("en_IN")
Faker.seed(42)
random.seed(42)

# ─── Curated Indian MSME Buyer Names ──────────────────────
BUYER_PROFILES = [
    {
        "id": "BUY001",
        "name": "Apex Manufacturing Pvt Ltd",
        "gstin": "27AADCA1234F1ZP",
        "sector": "auto_ancillary",
        "payment_behavior": "deteriorating",  # key story buyer
        "base_delay": 30,
        "variance": 15,
        "reliability_score": 53,
        "trend": "down",
        "total_outstanding": 847000,
        "retaliation_flag": True,
    },
    {
        "id": "BUY002",
        "name": "Sai Textiles & Exports",
        "gstin": "24BBBCS5678G1ZQ",
        "sector": "textile",
        "payment_behavior": "consistent",
        "base_delay": 22,
        "variance": 5,
        "reliability_score": 88,
        "trend": "stable",
        "total_outstanding": 325000,
        "retaliation_flag": False,
    },
    {
        "id": "BUY003",
        "name": "NovaTech Solutions LLP",
        "gstin": "29CCCNT9012H1ZR",
        "sector": "it_services",
        "payment_behavior": "consistent",
        "base_delay": 18,
        "variance": 4,
        "reliability_score": 91,
        "trend": "up",
        "total_outstanding": 190000,
        "retaliation_flag": False,
    },
    {
        "id": "BUY004",
        "name": "Bharat Heavy Industries Ltd",
        "gstin": "06DDDBH3456I1ZS",
        "sector": "construction",
        "payment_behavior": "erratic",
        "base_delay": 55,
        "variance": 25,
        "reliability_score": 41,
        "trend": "down",
        "total_outstanding": 1250000,
        "retaliation_flag": False,
    },
    {
        "id": "BUY005",
        "name": "GreenLeaf Pharma",
        "gstin": "36EEEGL7890J1ZT",
        "sector": "pharma",
        "payment_behavior": "improving",
        "base_delay": 35,
        "variance": 8,
        "reliability_score": 72,
        "trend": "up",
        "total_outstanding": 410000,
        "retaliation_flag": False,
    },
    {
        "id": "BUY006",
        "name": "Pinnacle Auto Parts Co",
        "gstin": "27FFFPA2345K1ZU",
        "sector": "auto_ancillary",
        "payment_behavior": "erratic",
        "base_delay": 48,
        "variance": 20,
        "reliability_score": 58,
        "trend": "down",
        "total_outstanding": 680000,
        "retaliation_flag": False,
    },
    {
        "id": "BUY007",
        "name": "Mumbai FMCG Distributors",
        "gstin": "27GGGMD6789L1ZV",
        "sector": "fmcg",
        "payment_behavior": "consistent",
        "base_delay": 25,
        "variance": 6,
        "reliability_score": 81,
        "trend": "stable",
        "total_outstanding": 220000,
        "retaliation_flag": False,
    },
    {
        "id": "BUY008",
        "name": "Kiran Electronics Hub",
        "gstin": "29HHHKE1234M1ZW",
        "sector": "electronics",
        "payment_behavior": "cold_start",
        "base_delay": None,  # unknown — uses sector baseline
        "variance": None,
        "reliability_score": None,  # will use sector default
        "trend": "unknown",
        "total_outstanding": 95000,
        "retaliation_flag": False,
    },
]


def generate_invoices(buyer, count=80):
    """Generate synthetic invoices for a buyer over the past 18 months."""
    invoices = []
    base_date = datetime(2025, 11, 1)

    for i in range(count):
        invoice_date = base_date - timedelta(days=random.randint(1, 540))
        amount = random.randint(15000, 250000)

        if buyer["base_delay"] is not None:
            delay = max(0, int(random.gauss(buyer["base_delay"], buyer["variance"])))
        else:
            delay = random.randint(30, 50)

        # For the deteriorating buyer, make recent invoices much worse
        if buyer["payment_behavior"] == "deteriorating" and invoice_date > datetime(2025, 6, 1):
            delay = delay + random.randint(15, 40)

        due_date = invoice_date + timedelta(days=45)  # MSMED 45-day rule
        payment_date = due_date + timedelta(days=delay)
        is_overdue = delay > 0

        # Some invoices are still open
        is_paid = True
        if invoice_date > datetime(2025, 9, 1):
            is_paid = random.random() > 0.35

        invoices.append({
            "invoice_id": f"INV-{buyer['id']}-{i+1:04d}",
            "buyer_id": buyer["id"],
            "buyer_name": buyer["name"],
            "amount": amount,
            "invoice_date": invoice_date.strftime("%Y-%m-%d"),
            "due_date": due_date.strftime("%Y-%m-%d"),
            "payment_date": payment_date.strftime("%Y-%m-%d") if is_paid else None,
            "days_overdue": delay if is_paid else None,
            "status": "paid" if is_paid else ("overdue" if datetime.now() > due_date else "pending"),
            "is_overdue": is_overdue,
        })

    return invoices


def generate_cash_transactions(count=50):
    """Generate synthetic cash transactions (Telegram-logged style)."""
    categories = ["transport", "raw_material", "wages", "utilities", "maintenance", "misc"]
    vendors = ["Raju", "Sita Devi", "Manoj Transport", "Kumar Electricals", "Sharma Ji", "Daily Needs Store"]

    transactions = []
    for i in range(count):
        amount = random.choice([500, 1000, 1500, 2000, 2500, 3000, 5000, 7500, 8000, 12000, 15000, 18000, 25000])
        tx_date = datetime.now() - timedelta(days=random.randint(0, 90))
        vendor = random.choice(vendors)
        category = random.choice(categories)

        needs_approval = amount >= 10000
        is_approved = True if not needs_approval else (random.random() > 0.15)

        transactions.append({
            "tx_id": f"TX-{i+1:04d}",
            "amount": amount,
            "vendor": vendor,
            "category": category,
            "date": tx_date.strftime("%Y-%m-%d %H:%M"),
            "raw_message": f"Paid {amount//1000}k to {vendor} for {category}" if amount >= 1000 else f"Paid {amount} to {vendor} for {category}",
            "status": "approved" if is_approved else "pending",
            "needs_approval": needs_approval,
            "logged_by": random.choice(["Suresh (Employee)", "Priya (Employee)", "Rohan (Owner)"]),
        })

    return transactions


def generate_order_history_for_retaliation(buyer_id="BUY001"):
    """
    Generate order volume history for the retaliation buyer (Apex).
    Pre-event: steady orders. Post-event (legal notice sent Sept 15): 83% volume drop.
    """
    orders = []
    notice_date = datetime(2025, 9, 15)

    # 90 days pre-event: healthy orders
    for i in range(90):
        day = notice_date - timedelta(days=90 - i)
        volume = random.randint(8, 15)  # daily order units
        orders.append({
            "buyer_id": buyer_id,
            "date": day.strftime("%Y-%m-%d"),
            "order_volume": volume,
            "period": "pre_notice",
        })

    # 60 days post-event: collapsed orders
    for i in range(60):
        day = notice_date + timedelta(days=i + 1)
        volume = random.randint(1, 3)  # 83% drop
        orders.append({
            "buyer_id": buyer_id,
            "date": day.strftime("%Y-%m-%d"),
            "order_volume": volume,
            "period": "post_notice",
        })

    return orders


def generate_all_data():
    """Generate all synthetic data and return as a dict."""
    all_invoices = []
    for buyer in BUYER_PROFILES:
        count = 80 if buyer["payment_behavior"] != "cold_start" else 8
        all_invoices.extend(generate_invoices(buyer, count))

    cash_txns = generate_cash_transactions(50)
    retaliation_data = generate_order_history_for_retaliation()

    return {
        "buyers": BUYER_PROFILES,
        "invoices": all_invoices,
        "cash_transactions": cash_txns,
        "retaliation_orders": retaliation_data,
    }
