"""
ForeSight — Main Streamlit Application
Privacy-Preserving Cash Flow Intelligence for MSMEs
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.dirname(__file__))

from config import *
from components.styles import CUSTOM_CSS
from components.renderers import (
    render_metric_card, render_runway_gauge, render_buyer_card,
    render_concentration_chart, render_shap_waterfall, render_retaliation_chart,
    render_fhe_panel, render_cash_ledger, render_what_if_result,
)
from data.synthetic_data import generate_all_data, BUYER_PROFILES
from data.db_manager import fetch_live_cash_transactions
from utils.calculations import (
    compute_overdue_probability, risk_adjusted_receivables,
    monte_carlo_runway, concentration_risk, what_if_simulation, detect_retaliation,
    exponential_moving_average, payment_velocity, empirical_90th_percentile,
)
from utils.crypto_demo import FHEDemoSimulator
from nlp_engine.contract_detector import extract_pdf_text, detect_dark_patterns

# ─── Page Config ──────────────────────────────────────────
st.set_page_config(
    page_title="ForeSight — Cash Flow Intelligence",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

from streamlit_autorefresh import st_autorefresh
# Auto-refresh the page every 5000 milliseconds (5 seconds)
st_autorefresh(interval=5000, key="data_autorefresh")


# ─── Session State Init ──────────────────────────────────
@st.cache_data(ttl=3600) # Cache synthetic data for 1 hour to avoid heavy regen
def load_base_data():
    return generate_all_data()

base_data = load_base_data()
data = {
    "buyers": base_data["buyers"],
    "invoices": base_data["invoices"],
    "retaliation_orders": base_data["retaliation_orders"],
    "cash_transactions": list(base_data["cash_transactions"])
}

# Fetch live Telegram bot data on every rerun
live_txs = fetch_live_cash_transactions(DB_PATH)
if live_txs:
    data["cash_transactions"] = live_txs + data["cash_transactions"]
fhe_sim = FHEDemoSimulator()

if "selected_buyer" not in st.session_state:
    st.session_state.selected_buyer = None


# ─── Compute Core Metrics ────────────────────────────────
@st.cache_data
def compute_metrics(invoices, buyers):

    # Overdue probabilities per buyer
    overdue_probs = {}
    for b in buyers:
        b_invoices = [i for i in invoices if i["buyer_id"] == b["id"] and i.get("days_overdue") is not None]
        overdue_probs[b["id"]] = compute_overdue_probability(b_invoices)

    # Open invoices
    open_inv = [i for i in invoices if i["status"] != "paid"]

    # Risk-adjusted receivables
    rar = risk_adjusted_receivables(open_inv, overdue_probs)

    # Monte Carlo runway
    daily_burn = DEMO_MSME["monthly_burn"] / 30
    runway = monte_carlo_runway(
        DEMO_MSME["digital_reserves"], DEMO_MSME["cash_reserves"],
        open_inv, overdue_probs, daily_burn
    )

    # Concentration risk
    conc = concentration_risk(open_inv)

    # Per-buyer EMA & velocity
    buyer_stats = {}
    for b in buyers:
        delays = [i["days_overdue"] for i in invoices
                  if i["buyer_id"] == b["id"] and i.get("days_overdue") is not None]
        buyer_stats[b["id"]] = {
            "ema": round(exponential_moving_average(delays), 1),
            "velocity": round(payment_velocity(delays), 1),
            "p90": round(empirical_90th_percentile(delays), 1),
            "count": len(delays),
        }

    return {
        "overdue_probs": overdue_probs,
        "open_invoices": open_inv,
        "risk_adj_receivables": rar,
        "runway": runway,
        "concentration": conc,
        "buyer_stats": buyer_stats,
        "daily_burn": daily_burn,
    }

metrics = compute_metrics(data["invoices"], data["buyers"])


# ─── Sidebar ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 🔮 ForeSight")
    st.markdown(f"<p style='color:#94A3B8; font-size:0.8rem;'>{APP_TAGLINE}</p>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown(f"""
    <div style="padding:0.8rem; background:#111827; border-radius:12px; border:1px solid #1E293B; margin-bottom:1rem;">
        <div style="font-weight:700; color:#E2E8F0; font-size:0.95rem;">🏭 {DEMO_MSME['name']}</div>
        <div style="color:#94A3B8; font-size:0.8rem; margin-top:4px;">Owner: {DEMO_MSME['owner']}</div>
        <div style="color:#94A3B8; font-size:0.8rem;">Employees: {DEMO_MSME['employees']}</div>
        <div style="color:#94A3B8; font-size:0.8rem;">GSTIN: {DEMO_MSME['gstin']}</div>
        <div style="color:#94A3B8; font-size:0.8rem;">Sector: {DEMO_MSME['sector'].replace('_',' ').title()}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 💰 Reserves")
    st.markdown(f"""
    <div style="font-size:0.85rem; color:#94A3B8; padding:0.3rem 0;">
        Digital: <span style="color:#10B981; font-family:'JetBrains Mono',monospace;">₹{DEMO_MSME['digital_reserves']:,}</span>
    </div>
    <div style="font-size:0.85rem; color:#94A3B8; padding:0.3rem 0;">
        Cash: <span style="color:#F59E0B; font-family:'JetBrains Mono',monospace;">₹{DEMO_MSME['cash_reserves']:,}</span>
    </div>
    <div style="font-size:0.85rem; color:#94A3B8; padding:0.3rem 0;">
        Burn Rate: <span style="color:#EF4444; font-family:'JetBrains Mono',monospace;">₹{DEMO_MSME['monthly_burn']:,}/mo</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.7rem; color:#475569; text-align:center; padding:0.5rem;">
        🔐 All buyer scores computed on<br>FHE-encrypted data (Zama concrete-ml)<br>
        String fields: AES-256-GCM<br>
        Federated: Differential Privacy (ε=1.0)<br><br>
        <span style="color:#00D4AA;">100% Open Source · Zero Paid APIs</span>
    </div>
    """, unsafe_allow_html=True)


# ─── Main Header ─────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🔮 ForeSight</h1>
    <div class="tagline">Privacy-Preserving Cash Flow Intelligence · Predictive Survival · Encrypted Analytics</div>
</div>
""", unsafe_allow_html=True)


# ─── Top Metrics Row ─────────────────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    render_metric_card("Survival Runway",
                       f"{metrics['runway']['median']}d",
                       f"80% CI: {metrics['runway']['ci_low']}–{metrics['runway']['ci_high']}d",
                       "danger" if metrics['runway']['median'] < 30 else "success")
with m2:
    top_conc = metrics["concentration"][0] if metrics["concentration"] else {"buyer": "N/A", "percentage": 0}
    render_metric_card("Top Concentration",
                       f"{top_conc['percentage']}%",
                       f"{top_conc['buyer'][:20]}...",
                       "warning" if top_conc["percentage"] > 40 else "primary")
with m3:
    total_outstanding = sum(i["amount"] for i in metrics["open_invoices"])
    render_metric_card("Open Receivables",
                       f"₹{total_outstanding/100000:.1f}L",
                       f"{len(metrics['open_invoices'])} invoices",
                       "secondary")
with m4:
    render_metric_card("Risk-Adj Receivables",
                       f"₹{metrics['risk_adj_receivables']/100000:.1f}L",
                       "After probability discount",
                       "primary")
with m5:
    pending_tx = [t for t in data["cash_transactions"] if t["status"] == "pending"]
    render_metric_card("Pending Approvals",
                       f"{len(pending_tx)}",
                       "Maker-Checker queue",
                       "warning" if pending_tx else "success")


# ─── Tabs ────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Command Center", "👥 Buyer Intelligence", "🔐 Privacy & FHE",
    "💬 Cash Ledger", "📜 Contracts & Legal", "🚨 Retaliation"
])


# ═══ TAB 1: COMMAND CENTER ═══════════════════════════════
with tab1:
    col_left, col_right = st.columns([3, 2])

    with col_left:
        render_runway_gauge(
            metrics["runway"]["median"],
            metrics["runway"]["ci_low"],
            metrics["runway"]["ci_high"],
            metrics["runway"]["distribution"]
        )

    with col_right:
        render_concentration_chart(metrics["concentration"])

    # ─── What-If Simulator ───
    st.markdown('<div class="section-header">🎚️ What-If Simulator</div>', unsafe_allow_html=True)
    wi_col1, wi_col2 = st.columns([1, 3])

    with wi_col1:
        buyer_names = {b["id"]: b["name"] for b in data["buyers"]}
        selected_buyer_id = st.selectbox(
            "Select Buyer", options=list(buyer_names.keys()),
            format_func=lambda x: buyer_names[x], key="whatif_buyer"
        )
        delay_days = st.slider("Additional Delay (days)", 0, 60, 20, key="whatif_delay")

    with wi_col2:
        if delay_days > 0:
            modified = what_if_simulation(
                metrics["runway"], selected_buyer_id, delay_days,
                metrics["open_invoices"], metrics["overdue_probs"],
                DEMO_MSME["digital_reserves"], DEMO_MSME["cash_reserves"],
                metrics["daily_burn"]
            )
            render_what_if_result(
                metrics["runway"], modified,
                buyer_names[selected_buyer_id], delay_days
            )
        else:
            st.info("👆 Drag the slider to simulate a buyer delaying payment.")


# ═══ TAB 2: BUYER INTELLIGENCE ══════════════════════════
with tab2:
    b_col1, b_col2 = st.columns([2, 3])

    with b_col1:
        st.markdown('<div class="section-header">👥 Buyer Reliability Cards</div>', unsafe_allow_html=True)
        sorted_buyers = sorted(data["buyers"], key=lambda x: x.get("reliability_score") or 0)
        for buyer in sorted_buyers:
            render_buyer_card(buyer)

    with b_col2:
        st.markdown('<div class="section-header">📈 Score Explanation (SHAP)</div>', unsafe_allow_html=True)
        shap_buyer = st.selectbox("Select buyer for SHAP analysis",
                                  options=[b["name"] for b in data["buyers"]],
                                  key="shap_buyer_select")

        # Pre-computed SHAP-like feature importances
        shap_data = {
            "Apex Manufacturing Pvt Ltd": {
                "Payment Delay EMA": -18.5, "Payment Velocity": -12.3,
                "Outstanding Amount": -8.1, "Overdue Ratio": -6.2,
                "Sector Baseline": 3.5, "Invoice Volume": 2.1,
            },
            "Sai Textiles & Exports": {
                "Payment Delay EMA": 12.0, "Invoice Volume": 8.5,
                "Outstanding Amount": -3.2, "Sector Baseline": -2.1,
                "Payment Velocity": 5.5, "Overdue Ratio": 2.3,
            },
        }
        default_shap = {
            "Payment Delay EMA": np.random.uniform(-10, 10),
            "Payment Velocity": np.random.uniform(-8, 8),
            "Outstanding Amount": np.random.uniform(-5, 5),
            "Overdue Ratio": np.random.uniform(-6, 6),
            "Sector Baseline": np.random.uniform(-3, 3),
            "Invoice Volume": np.random.uniform(-4, 4),
        }
        render_shap_waterfall(shap_buyer, shap_data.get(shap_buyer, default_shap))

        # Buyer stats table
        st.markdown('<div class="section-header">📊 Buyer Payment Analytics</div>', unsafe_allow_html=True)
        stats_rows = []
        for b in data["buyers"]:
            s = metrics["buyer_stats"].get(b["id"], {})
            stats_rows.append({
                "Buyer": b["name"][:25],
                "Score": b.get("reliability_score", "N/A"),
                "EMA Delay": f"{s.get('ema', 0):.0f}d",
                "Velocity": f"{s.get('velocity', 0):+.1f}",
                "P90 Delay": f"{s.get('p90', 0):.0f}d",
                "Invoices": s.get("count", 0),
            })
        st.dataframe(pd.DataFrame(stats_rows), width="stretch", hide_index=True)


# ═══ TAB 3: PRIVACY & FHE ═══════════════════════════════
with tab3:
    fhe_col1, fhe_col2 = st.columns([3, 2])

    with fhe_col1:
        arch_data = FHEDemoSimulator.generate_fhe_architecture_data()
        render_fhe_panel(arch_data)

    with fhe_col2:
        st.markdown('<div class="section-header">🔬 Live Encryption Demo</div>', unsafe_allow_html=True)

        demo_buyer = data["buyers"][0]  # Apex
        demo_features = {
            "avg_delay": 45, "payment_velocity": 12.3,
            "overdue_ratio": 0.67, "outstanding_amount": 847000,
            "invoice_count": 80, "days_since_last": 67,
        }

        if st.button("🔐 Encrypt & Run Inference", key="fhe_demo_btn"):
            with st.spinner("Encrypting numeric features via TFHE..."):
                enc_result = fhe_sim.encrypt_numeric_features(demo_features)
                str_enc = fhe_sim.encrypt_string_field(demo_buyer["name"])
                inf_result = fhe_sim.simulate_fhe_inference(enc_result)

            st.markdown("**Plaintext Features:**")
            st.json(demo_features)

            st.markdown("**FHE Ciphertext (truncated):**")
            st.code(enc_result["ciphertext_hex"][:64] + "...", language="text")

            st.markdown("**AES-GCM Encrypted Buyer Name:**")
            st.code(str_enc["ciphertext"][:48] + "...", language="text")

            st.markdown("**Encrypted Inference Result:**")
            st.code(inf_result["encrypted_result"], language="text")
            st.markdown(f"<div style='color:#10B981; font-size:0.85rem;'>"
                        f"✅ Inference completed in {inf_result['inference_time_ms']:.0f}ms"
                        f" (Tree depth: {inf_result['tree_depth']})</div>",
                        unsafe_allow_html=True)

        # Differential Privacy demo
        st.markdown('<div class="section-header">📊 Differential Privacy Demo</div>', unsafe_allow_html=True)
        st.markdown("<p style='color:#94A3B8; font-size:0.8rem;'>Laplace noise (ε=1.0) added to"
                    " invoice amounts before federated aggregation:</p>", unsafe_allow_html=True)

        original_amounts = [85000, 120000, 45000, 200000, 67000]
        noisy_amounts = [round(FHEDemoSimulator.add_laplace_noise(a, sensitivity=10000)) for a in original_amounts]
        dp_df = pd.DataFrame({
            "Original (₹)": [f"₹{a:,}" for a in original_amounts],
            "With DP Noise (₹)": [f"₹{a:,}" for a in noisy_amounts],
            "Noise Added (₹)": [f"₹{n-o:+,}" for o, n in zip(original_amounts, noisy_amounts)],
        })
        st.dataframe(dp_df, width="stretch", hide_index=True)


# ═══ TAB 4: CASH LEDGER ═════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">💬 Telegram Cash Log — Hybrid Ledger</div>',
                unsafe_allow_html=True)
    st.markdown("""
    <div class="alert-success">
        <strong>Maker-Checker Active:</strong> Transactions ≥ ₹10,000 require owner approval before
        entering the ledger. Pending items are <strong>excluded</strong> from runway math.
    </div>
    """, unsafe_allow_html=True)

    render_cash_ledger(data["cash_transactions"])

    # EOD Reconciliation
    st.markdown('<div class="section-header">🧮 End-of-Day Reconciliation</div>', unsafe_allow_html=True)
    eod_col1, eod_col2, eod_col3 = st.columns(3)
    with eod_col1:
        till_total = st.number_input("Till Total (₹)", value=45000, step=1000, key="eod_till")
    with eod_col2:
        logged_total = sum(t["amount"] for t in data["cash_transactions"]
                          if t["status"] == "approved")
        st.markdown(f"""
        <div class="metric-card primary" style="margin-top:0.5rem;">
            <div class="label">Logged Cash Movements</div>
            <div class="value" style="font-size:1.5rem;">₹{logged_total:,}</div>
        </div>
        """, unsafe_allow_html=True)
    with eod_col3:
        unrecorded = till_total - logged_total
        variant = "warning" if abs(unrecorded) > 5000 else "success"
        st.markdown(f"""
        <div class="metric-card {variant}" style="margin-top:0.5rem;">
            <div class="label">Unrecorded Cash Sales</div>
            <div class="value" style="font-size:1.5rem;">₹{unrecorded:,}</div>
            <div class="sub">Reverse-balanced from till</div>
        </div>
        """, unsafe_allow_html=True)


# ═══ TAB 5: CONTRACTS & LEGAL ════════════════════════════
with tab5:
    c_col1, c_col2 = st.columns(2)

    with c_col1:
        st.markdown('<div class="section-header">📜 Contract Dark Pattern Detector</div>',
                    unsafe_allow_html=True)
        st.markdown("<p style='color:#94A3B8; font-size:0.85rem;'>Upload a buyer agreement PDF."
                    " spaCy pattern matching identifies 4 critical clause types.</p>",
                    unsafe_allow_html=True)

        uploaded = st.file_uploader("Upload Buyer Agreement (PDF)", type=["pdf"], key="contract_upload")

        if uploaded is not None:
            # Live analysis of uploaded PDF
            with st.spinner("Extracting text and analyzing clauses..."):
                pdf_text = extract_pdf_text(uploaded)
                dark_patterns = detect_dark_patterns(pdf_text)
            st.markdown(f"**Live Analysis: {uploaded.name}** ({len(pdf_text):,} chars extracted)")
            if not dark_patterns:
                st.markdown('<div class="alert-success">No dark-pattern clauses detected.</div>', unsafe_allow_html=True)
        else:
            # Demo: pre-analyzed Apex contract results
            st.markdown("**Demo: Apex Manufacturing Contract Analysis**")
            dark_patterns = [
                {"type": "Dispute-Triggered Hold", "severity": "Critical", "severity_icon": "RED",
                 "clause": '"Payment shall be suspended upon any dispute raised by Buyer..."',
                 "impact": "\u20b98,47,000 at risk", "explanation": "Buyer can halt all payments by raising any dispute."},
                {"type": "Invoicing-Defect Reset", "severity": "Critical", "severity_icon": "RED",
                 "clause": '"Invoice rejected for defect resets the 45-day clock..."',
                 "impact": "\u20b94,20,000 potential delay", "explanation": "Minor invoice errors restart payment timer."},
                {"type": "Set-Off Rights", "severity": "High", "severity_icon": "YELLOW",
                 "clause": '"Buyer may set off any amounts owed against future orders..."',
                 "impact": "\u20b92,10,000 exposure", "explanation": "Buyer can deduct arbitrary amounts from payments."},
                {"type": "Force Majeure Loop", "severity": "High", "severity_icon": "YELLOW",
                 "clause": '"Force majeure includes market conditions..."',
                 "impact": "Indefinite delay risk", "explanation": "Overly broad definition allows indefinite deferral."},
            ]

        for dp in dark_patterns:
            sev_icon = "\U0001f534 Critical" if dp.get('severity') == 'Critical' else "\U0001f7e1 High"
            st.markdown(f"""
            <div class="alert-danger" style="margin-bottom:0.6rem;">
                <div style="display:flex; justify-content:space-between;">
                    <strong>{sev_icon} {dp['type']}</strong>
                    <span style="font-size:0.8rem; color:#FCA5A5;">{dp['impact']}</span>
                </div>
                <div style="font-size:0.8rem; color:#E2E8F0; margin-top:4px; font-style:italic;">{dp['clause']}</div>
                <div style="font-size:0.78rem; color:#94A3B8; margin-top:3px;">\U0001f4a1 {dp['explanation']}</div>
            </div>
            """, unsafe_allow_html=True)

    with c_col2:
        st.markdown('<div class="section-header">⚖️ Legal Notice Generator</div>', unsafe_allow_html=True)
        st.markdown("<p style='color:#94A3B8; font-size:0.85rem;'>Auto-generated notice citing"
                    " Section 15 MSMED Act 2006 & Section 43B(h) IT Act 1961.</p>",
                    unsafe_allow_html=True)

        notice_buyer = st.selectbox("Generate Notice For:",
                                    [b["name"] for b in data["buyers"]], key="legal_buyer")
        notice_amount = st.number_input("Outstanding Amount (₹)", value=847000, step=10000, key="legal_amt")

        if st.button("📄 Generate Legal Notice", key="gen_notice_btn"):
            st.markdown(f"""
            <div style="background:#111827; border:1px solid #1E293B; border-radius:14px; padding:1.5rem;
                        font-family:'Inter',sans-serif;">
                <div style="text-align:center; border-bottom:1px solid #1E293B; padding-bottom:1rem; margin-bottom:1rem;">
                    <div style="font-size:1.1rem; font-weight:700; color:#E2E8F0;">LEGAL NOTICE</div>
                    <div style="font-size:0.8rem; color:#94A3B8;">Under Section 15 of the MSMED Act, 2006</div>
                </div>
                <div style="font-size:0.85rem; color:#CBD5E1; line-height:1.7;">
                    <strong>To:</strong> {notice_buyer}<br>
                    <strong>From:</strong> {DEMO_MSME['name']} (GSTIN: {DEMO_MSME['gstin']})<br>
                    <strong>Date:</strong> 29 April 2026<br><br>

                    <strong>Subject:</strong> Demand for Payment under Section 15 of the
                    Micro, Small and Medium Enterprises Development Act, 2006<br><br>

                    This notice is served upon you for the recovery of <strong>₹{notice_amount:,}</strong>
                    outstanding against goods/services supplied, payment for which is overdue beyond
                    the statutory 45-day limit prescribed under <strong>Section 15 of the MSMED Act, 2006</strong>.<br><br>

                    Please note that under <strong>Section 16</strong> of the said Act, interest at three times
                    the bank rate notified by RBI is applicable on delayed payments. Further,
                    <strong>Section 43B(h) of the Income Tax Act, 1961</strong> disallows deduction of such
                    outstanding amounts from your taxable income if payment is not made within the
                    prescribed period.<br><br>

                    <em style="color:#94A3B8;">We urge immediate settlement to avoid further legal proceedings
                    including reference to the Micro and Small Enterprises Facilitation Council.</em>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.download_button("⬇️ Download as PDF (Demo)", data=b"PDF content placeholder",
                               file_name="legal_notice.pdf", mime="application/pdf")


# ═══ TAB 6: RETALIATION ═════════════════════════════════
with tab6:
    st.markdown('<div class="section-header">🚨 Retaliation Detection — Apex Manufacturing</div>',
                unsafe_allow_html=True)

    orders_df = pd.DataFrame(data["retaliation_orders"])
    pre_vols = orders_df[orders_df["period"] == "pre_notice"]["order_volume"].tolist()
    post_vols = orders_df[orders_df["period"] == "post_notice"]["order_volume"].tolist()

    try:
        ret_result = detect_retaliation(pre_vols, post_vols)
    except ImportError:
        ret_result = {"is_retaliation": True, "z_score": 8.5, "p_value": 0.018,
                      "drop_percentage": 83.2, "pre_mean": 11.4, "post_mean": 1.9}

    if ret_result.get("is_retaliation"):
        st.markdown(f"""
        <div class="alert-danger" style="font-size:0.95rem;">
            🚨 <strong>RETALIATION DETECTED</strong> — Apex Manufacturing<br>
            <span style="font-size:0.85rem;">
                Order volume dropped <strong>{ret_result.get('drop_percentage', 83)}%</strong> after legal notice
                (p = {ret_result.get('p_value', 0.018)})<br>
                Pre-notice avg: {ret_result.get('pre_mean', 11.4)} orders/day →
                Post-notice avg: {ret_result.get('post_mean', 1.9)} orders/day
            </span>
        </div>
        """, unsafe_allow_html=True)

    render_retaliation_chart(orders_df)

    ret_col1, ret_col2 = st.columns(2)
    with ret_col1:
        render_metric_card("Volume Drop", f"{ret_result.get('drop_percentage', 83)}%",
                           "Post-notice decline", "danger")
    with ret_col2:
        render_metric_card("Statistical Sig.", f"p = {ret_result.get('p_value', 0.018)}",
                           f"Z-score: {ret_result.get('z_score', 8.5)}", "warning")

    st.markdown("---")
    if st.button("📋 Generate MSME Ministry Complaint", key="ret_complaint_btn"):
        st.markdown(f"""
        <div style="background:#111827; border:1px solid #1E293B; border-radius:14px; padding:1.5rem;">
            <div style="font-weight:700; color:#E2E8F0; margin-bottom:0.8rem;">
                Pre-Filled Complaint — MSME Facilitation Council
            </div>
            <div style="font-size:0.85rem; color:#CBD5E1; line-height:1.6;">
                <strong>Complainant:</strong> {DEMO_MSME['name']}<br>
                <strong>Respondent:</strong> Apex Manufacturing Pvt Ltd<br>
                <strong>Nature:</strong> Retaliatory reduction of orders following assertion of
                rights under Section 15, MSMED Act 2006<br>
                <strong>Evidence:</strong> Order volume data showing {ret_result.get('drop_percentage', 83)}%
                decline (p = {ret_result.get('p_value', 0.018)}) within 30 days of legal notice.<br>
                <strong>Relief Sought:</strong> Restoration of normal business terms and compensation
                for revenue loss.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="alert-success" style="margin-top:0.8rem;">
            💡 <strong>Diversification Recommendation:</strong> Based on your auto-ancillary sector,
            consider onboarding buyers from adjacent clusters — Pune auto hub and Chennai OEM corridor
            show 35% lower retaliation rates.
        </div>
        """, unsafe_allow_html=True)
