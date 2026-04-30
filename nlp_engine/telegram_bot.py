"""
ForeSight — Telegram Bot (Separate Process)
Receives informal cash messages, parses via Llama 3, resolves vendors,
and stores transactions with Maker-Checker flow for amounts >= 10,000.

Run: python -m nlp_engine.telegram_bot
"""

import os
import sys
import logging
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from nlp_engine.llm_parser import parse_cash_message
from nlp_engine.vendor_aliases import resolve_vendor
from config import DB_PATH, MAKER_CHECKER_THRESHOLD, DEMO_MSME

# ─── Logging ─────────────────────────────────────────────
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Load Token ──────────────────────────────────────────
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Owner chat ID — set after first /start from owner
OWNER_CHAT_ID = None


# ─── DB Helpers ──────────────────────────────────────────
def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS cash_transactions (tx_id TEXT PRIMARY KEY, amount REAL, vendor_encrypted TEXT, category TEXT, date TEXT, raw_message_enc TEXT, status TEXT DEFAULT 'pending', needs_approval INTEGER DEFAULT 0, logged_by_enc TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS pending_transactions (tx_id TEXT PRIMARY KEY, amount REAL, vendor_encrypted TEXT, category TEXT, date TEXT, raw_message_enc TEXT, logged_by_enc TEXT, approved INTEGER DEFAULT 0, approved_by TEXT, approved_at TEXT)")
    return conn


def _store_transaction(parsed: dict, vendor_info: dict, user_name: str, status: str = "approved"):
    """Store a parsed transaction in the database."""
    conn = _get_db()
    tx_id = f"TX-TG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{abs(hash(parsed['raw_message'])) % 10000:04d}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if status == "approved":
        conn.execute(
            "INSERT OR REPLACE INTO cash_transactions (tx_id, amount, vendor_encrypted, category, date, raw_message_enc, status, needs_approval, logged_by_enc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (tx_id, parsed["amount"], vendor_info["canonical_name"], parsed["category"], now, parsed["raw_message"], "approved", 0, user_name)
        )
    else:
        conn.execute(
            "INSERT OR REPLACE INTO pending_transactions (tx_id, amount, vendor_encrypted, category, date, raw_message_enc, logged_by_enc) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tx_id, parsed["amount"], vendor_info["canonical_name"], parsed["category"], now, parsed["raw_message"], user_name)
        )
    conn.commit()
    conn.close()
    return tx_id


def _approve_transaction(tx_id: str, approver: str):
    """Move a pending transaction to approved."""
    conn = _get_db()
    row = conn.execute("SELECT * FROM pending_transactions WHERE tx_id = ?", (tx_id,)).fetchone()
    if row:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn.execute(
            "INSERT OR REPLACE INTO cash_transactions (tx_id, amount, vendor_encrypted, category, date, raw_message_enc, status, needs_approval, logged_by_enc) VALUES (?, ?, ?, ?, ?, ?, 'approved', 1, ?)",
            (row[0], row[1], row[2], row[3], row[4], row[5], row[6])
        )
        conn.execute("DELETE FROM pending_transactions WHERE tx_id = ?", (tx_id,))
        conn.commit()
    conn.close()


def _reject_transaction(tx_id: str):
    """Delete a rejected pending transaction."""
    conn = _get_db()
    conn.execute("DELETE FROM pending_transactions WHERE tx_id = ?", (tx_id,))
    conn.commit()
    conn.close()


# ─── Bot Handlers ────────────────────────────────────────
async def start_command(update: Update, context):
    """Handle /start command."""
    global OWNER_CHAT_ID
    OWNER_CHAT_ID = update.effective_chat.id
    await update.message.reply_text(
        f"ForeSight Cash Logger - Active\n"
        f"Business: {DEMO_MSME['name']}\n"
        f"Owner: {DEMO_MSME['owner']}\n\n"
        f"Send cash transactions like:\n"
        f"  'Paid 5k to Raju for transport'\n"
        f"  'Received 25000 from Kumar'\n\n"
        f"Transactions >= Rs.{MAKER_CHECKER_THRESHOLD:,} need your approval.\n"
        f"Type /status for pending approvals."
    )


async def status_command(update: Update, context):
    """Show pending transactions count."""
    conn = _get_db()
    count = conn.execute("SELECT COUNT(*) FROM pending_transactions WHERE approved = 0").fetchone()[0]
    conn.close()
    await update.message.reply_text(f"Pending approvals: {count}\nUse /pending to see details.")


async def pending_command(update: Update, context):
    """List all pending transactions."""
    conn = _get_db()
    rows = conn.execute("SELECT tx_id, amount, vendor_encrypted, category, raw_message_enc FROM pending_transactions WHERE approved = 0 LIMIT 10").fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("No pending transactions.")
        return

    for row in rows:
        tx_id, amount, vendor, category, msg = row
        keyboard = [[
            InlineKeyboardButton("Approve", callback_data=f"approve_{tx_id}"),
            InlineKeyboardButton("Reject", callback_data=f"reject_{tx_id}"),
        ]]
        await update.message.reply_text(
            f"PENDING: Rs.{amount:,.0f}\n"
            f"Vendor: {vendor} | Category: {category}\n"
            f"Message: \"{msg}\"\n"
            f"ID: {tx_id}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_message(update: Update, context):
    """Process incoming cash transaction message."""
    text = update.message.text
    user = update.effective_user
    user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Unknown"

    # Parse the message
    parsed = parse_cash_message(text)

    if parsed["amount"] <= 0:
        await update.message.reply_text(
            "Could not extract amount from your message.\n"
            "Try: 'Paid 5k to Raju for transport'"
        )
        return

    # Resolve vendor
    vendor_info = resolve_vendor(parsed["vendor"])

    # Maker-Checker check
    needs_approval = parsed["amount"] >= MAKER_CHECKER_THRESHOLD

    if needs_approval:
        tx_id = _store_transaction(parsed, vendor_info, user_name, status="pending")

        # Confirm to sender
        await update.message.reply_text(
            f"Logged (PENDING APPROVAL):\n"
            f"  Rs.{parsed['amount']:,.0f} | {parsed['action']}\n"
            f"  Vendor: {vendor_info['canonical_name']}\n"
            f"  Category: {parsed['category']}\n"
            f"  Parser: {parsed['parser']}\n\n"
            f"Awaiting owner approval (>= Rs.{MAKER_CHECKER_THRESHOLD:,})"
        )

        # Send approval request to owner
        if OWNER_CHAT_ID:
            keyboard = [[
                InlineKeyboardButton("Approve", callback_data=f"approve_{tx_id}"),
                InlineKeyboardButton("Reject", callback_data=f"reject_{tx_id}"),
            ]]
            await context.bot.send_message(
                chat_id=OWNER_CHAT_ID,
                text=f"APPROVAL NEEDED\n"
                     f"Rs.{parsed['amount']:,.0f} | {parsed['action']}\n"
                     f"Vendor: {vendor_info['canonical_name']}\n"
                     f"Category: {parsed['category']}\n"
                     f"Logged by: {user_name}\n"
                     f"Message: \"{text}\"",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    else:
        _store_transaction(parsed, vendor_info, user_name, status="approved")
        await update.message.reply_text(
            f"Logged:\n"
            f"  Rs.{parsed['amount']:,.0f} | {parsed['action']}\n"
            f"  Vendor: {vendor_info['canonical_name']}\n"
            f"  Category: {parsed['category']}\n"
            f"  Parser: {parsed['parser']}"
        )


async def handle_approval_callback(update: Update, context):
    """Handle approve/reject button presses."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("approve_"):
        tx_id = data[8:]
        _approve_transaction(tx_id, query.from_user.first_name or "Owner")
        await query.edit_message_text(f"APPROVED: {tx_id}")
    elif data.startswith("reject_"):
        tx_id = data[7:]
        _reject_transaction(tx_id)
        await query.edit_message_text(f"REJECTED: {tx_id}")


# ─── Main ────────────────────────────────────────────────
def main():
    if not BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set in nlp_engine/.env")
        sys.exit(1)

    print(f"ForeSight Telegram Bot starting...")
    print(f"  Business: {DEMO_MSME['name']}")
    print(f"  Maker-Checker threshold: Rs.{MAKER_CHECKER_THRESHOLD:,}")
    print(f"  Database: {DB_PATH}")
    print(f"  Press Ctrl+C to stop.\n")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("pending", pending_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_approval_callback))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
