import sqlite3
import json
import os

DB_NAME = "database.db"
DATA_FILE = "synthetic_data_refined.json"

def init_db():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create tables
    cursor.executescript("""
    CREATE TABLE buyers_registry (
      buyer_id TEXT PRIMARY KEY,
      buyer_name TEXT,
      sector TEXT,
      gstin TEXT,
      avg_ema_delay REAL,
      payment_velocity REAL,
      p90_delay REAL,
      default_probability REAL,
      reliability_score REAL
    );

    CREATE TABLE invoices_ledger (
      invoice_id TEXT PRIMARY KEY,
      buyer_id TEXT,
      buyer_name TEXT,
      invoice_date DATE,
      due_date DATE,
      payment_date DATE,
      days_overdue INTEGER,
      amount REAL,
      status TEXT,
      gstin TEXT,
      sector TEXT,
      post_legal_notice INTEGER,
      FOREIGN KEY (buyer_id) REFERENCES buyers_registry(buyer_id)
    );

    CREATE TABLE cash_transactions (
      transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
      transaction_date DATE,
      amount REAL,
      category TEXT,
      vendor_name TEXT,
      status TEXT
    );

    CREATE TABLE pending_transactions (
      transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
      transaction_date DATE,
      amount REAL,
      category TEXT,
      vendor_name TEXT,
      status TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      awaiting_approval INTEGER DEFAULT 1
    );

    CREATE TABLE buyer_metrics (
      buyer_id TEXT PRIMARY KEY,
      num_invoices INTEGER,
      avg_ema_delay REAL,
      payment_velocity REAL,
      p90_delay REAL,
      default_probability REAL,
      total_amount REAL,
      FOREIGN KEY (buyer_id) REFERENCES buyers_registry(buyer_id)
    );

    CREATE TABLE fhe_cache (
      buyer_id TEXT PRIMARY KEY,
      ciphertext BLOB,
      computed_at TIMESTAMP,
      is_stale INTEGER DEFAULT 0,
      FOREIGN KEY (buyer_id) REFERENCES buyers_registry(buyer_id)
    );
    """)

    # Load data from JSON
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    # Insert Buyers
    for b_id, metrics in data["buyer_metrics"].items():
        # Get sector and gstin from first invoice match
        sector = ""
        gstin = ""
        for inv in data["invoices"]:
            if inv["buyer_id"] == b_id:
                sector = inv["sector"]
                gstin = inv["gstin"]
                break
        
        cursor.execute("""
            INSERT INTO buyers_registry (buyer_id, buyer_name, sector, gstin, avg_ema_delay, payment_velocity, p90_delay, default_probability, reliability_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (b_id, metrics["buyer_name"], sector, gstin, metrics["avg_ema_delay"], metrics["payment_velocity"], metrics["p90_delay"], metrics["default_probability"], 0.0))

        cursor.execute("""
            INSERT INTO buyer_metrics (buyer_id, num_invoices, avg_ema_delay, payment_velocity, p90_delay, default_probability, total_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (b_id, metrics["num_invoices"], metrics["avg_ema_delay"], metrics["payment_velocity"], metrics["p90_delay"], metrics["default_probability"], metrics["total_amount"]))

    # Insert Invoices
    for inv in data["invoices"]:
        cursor.execute("""
            INSERT INTO invoices_ledger (invoice_id, buyer_id, buyer_name, invoice_date, due_date, payment_date, days_overdue, amount, status, gstin, sector, post_legal_notice)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (inv["invoice_id"], inv["buyer_id"], inv["buyer_name"], inv["invoice_date"], inv["due_date"], inv["payment_date"], inv["days_overdue"], inv["amount"], inv["status"], inv["gstin"], inv["sector"], inv["post_legal_notice"]))

    # Insert Cash Transactions
    for tx in data["cash_transactions"]:
        cursor.execute("""
            INSERT INTO cash_transactions (transaction_date, amount, category, vendor_name, status)
            VALUES (?, ?, ?, ?, ?)
        """, (tx["transaction_date"], tx["amount"], tx["category"], tx["vendor_name"], tx["status"]))

    conn.commit()
    conn.close()
    print(f"Database {DB_NAME} initialized and data loaded.")

if __name__ == "__main__":
    init_db()
