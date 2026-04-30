import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import time
import json

# Page Configuration
st.set_page_config(
    page_title="InvoiceIQ | MSME Early Warning",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1a1c24;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #00d4ff;
    }
    .stAlert {
        border-radius: 10px;
    }
    .sidebar .sidebar-content {
        background-color: #1a1c24;
    }
    h1, h2, h3 {
        color: #00d4ff;
    }
    </style>
    """, unsafe_allow_html=True)

# API Base URL
API_URL = "http://localhost:8000"

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/clouds/100/000000/shield.png", width=100)
    st.title("InvoiceIQ")
    st.info("Privacy-Preserving AI for MSMEs")
    st.divider()
    page = st.radio("Navigation", ["Dashboard", "Buyer Reliability", "Interventions", "Privacy Audit"])

# --- DASHBOARD PAGE ---
if page == "Dashboard":
    st.title("🚀 Cash Flow Command Center")
    
    # Fetch Runway Data
    try:
        runway_data = requests.get(f"{API_URL}/runway").json()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Animated Gauge
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = runway_data["runway_days"],
                title = {'text': "Survival Runway (Days)"},
                gauge = {
                    'axis': {'range': [None, 90]},
                    'bar': {'color': "#00d4ff"},
                    'steps': [
                        {'range': [0, 30], 'color': "#ff4b4b"},
                        {'range': [30, 60], 'color': "#ffa500"},
                        {'range': [60, 90], 'color': "#00cc00"}
                    ],
                    'threshold': {
                        'line': {'color': "white", 'width': 4},
                        'thickness': 0.75,
                        'value': runway_data["ci_lower"]}
                }
            ))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white", 'family': "Arial"})
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"80% CI: {runway_data['ci_lower']} – {runway_data['ci_upper']} Days")

        with col2:
            st.metric("Cash Reserves", f"₹{runway_data['cash_reserves']:,.0f}", "+₹5k (Today)")
            st.metric("Open Receivables", f"₹{runway_data['open_receivables']:,.0f}", "-12% (MoM)")
            
        with col3:
            st.metric("Daily Burn Rate", f"₹{runway_data['daily_burn_rate']:,.0f}", "Stable")
            st.warning("⚠️ Concentration Risk: 67% of runway depends on Apex Manufacturing.")

    except Exception as e:
        st.error(f"Waiting for Backend API... {e}")

    st.divider()
    
    # What-If Slider
    st.subheader("🛠️ What-If Simulation")
    delay = st.slider("What if Top Buyer delays payment by (days):", 0, 60, 15)
    new_runway = runway_data["runway_days"] - (delay * 0.4) # Mock calculation
    st.write(f"Estimated Impact: **Runway drops to {new_runway:.1f} days.**")

# --- BUYER RELIABILITY PAGE ---
elif page == "Buyer Reliability":
    st.title("🔍 Buyer Reliability Network")
    
    buyers = [
        {"id": "apex_manufacturing_pvt_ltd", "name": "Apex Manufacturing Ltd."},
        {"id": "shree_retail_distributors", "name": "Shree Retail"},
        {"id": "metro_infra_suppliers", "name": "Metro Infra"},
        {"id": "bright_foods_trading_co", "name": "Bright Foods"},
        {"id": "zenith_pharma_supplies", "name": "Zenith Pharma"},
        {"id": "kaveri_engineering_works", "name": "Kaveri Engineering"}
    ]
    
    cols = st.columns(3)
    for i, buyer in enumerate(buyers):
        with cols[i % 3]:
            with st.container():
                st.markdown(f"### {buyer['name']}")
                if st.button(f"Analyze {buyer['name']}", key=buyer['id']):
                    with st.spinner("Performing FHE Inference..."):
                        res = requests.get(f"{API_URL}/buyer/{buyer['id']}/reliability").json()
                        st.metric("Reliability Score", f"{res['reliability_score']}/100", res['trend_arrow'])
                        
                        # SHAP waterfall simulation
                        st.subheader("Feature Impact (SHAP)")
                        st.bar_chart({
                            "Avg Delay": -15,
                            "P90 Delay": -10,
                            "Invoice Vol": 5,
                            "Default Prob": -20,
                            "Sector History": 12
                        })
                        
                        with st.expander("FHE Architecture Logs"):
                            st.code(f"Ciphertext In: {res['fhe_metadata']['ciphertext_in'][:30]}...")
                            st.code(f"Ciphertext Out: {res['fhe_metadata']['ciphertext_out'][:30]}...")
                            st.success(f"Inference Latency: {res['fhe_metadata']['latency_seconds']}s")

# --- INTERVENTIONS PAGE ---
elif page == "Interventions":
    st.title("⚖️ Legal & Recovery Interventions")
    
    st.subheader("Detect Retaliation")
    if st.button("Run Retaliation Test (Apex)"):
        res = requests.post(f"{API_URL}/retaliation/detect?buyer_id=apex_manufacturing_pvt_ltd").json()
        if res["retaliation_detected"]:
            st.error(f"🚨 RETALIATION DETECTED: {res['buyer_name']} volume dropped {res['volume_drop']*100:.1f}%")
            st.write(f"P-Value: {res['p_value']} (Statistically Significant)")
            
            if st.button("Generate Legal Notice"):
                notice_res = requests.post(f"{API_URL}/legal-notice/generate?buyer_id=apex&buyer_name=Apex%20Manufacturing")
                st.success("Notice Generated!")
                st.download_button("Download PDF", notice_res.content, "legal_notice.pdf")

    st.divider()
    
    st.subheader("Contract Analyzer")
    st.file_uploader("Upload Buyer Agreement (PDF)")
    if st.button("Analyze Clauses"):
        st.info("Scanning for dark patterns...")
        time.sleep(2)
        st.error("⚠️ Dispute Trigger: High Severity | Impact: ₹5.0L")
        st.warning("⚠️ Extended Payment: Medium Severity | Impact: ₹1.2L")

# --- PRIVACY AUDIT PAGE ---
elif page == "Privacy Audit":
    st.title("🔐 Privacy & Encryption Audit")
    
    st.subheader("FHE Inference Flow")
    st.json({
        "encryption": "Paillier/TFHE (Concrete-ML)",
        "plaintext_exposure": "None (End-to-End)",
        "server_visibility": "Ciphertext Only",
        "numeric_features": ["avg_delay", "p90_delay", "vol", "default_prob"]
    })
    
    st.divider()
    
    st.subheader("AES-GCM Metadata Protection")
    test_str = "Ayesha Plastics"
    encrypted = "0a2b4c... (Sample Ciphertext)"
    st.write(f"Plaintext: `{test_str}`")
    st.write(f"Encrypted Storage: `{encrypted}`")
    
    st.divider()
    
    st.subheader("Differential Privacy (Laplace)")
    val = 1500000
    noisy_val = val + 142.5 # Mock noise
    st.write(f"Aggregated Defaults (Plain): ₹{val:,.2f}")
    st.write(f"Aggregated Defaults (DP ε=1.0): ₹{noisy_val:,.2f}")
    st.success("Individual MSME privacy preserved in federated stats.")

# Telegram Cash Demo (Always visible at bottom)
st.divider()
st.subheader("💬 Telegram Cash Log Demo")
msg = st.text_input("Enter message (e.g., 'Paid 5k to Raju for transport')", "Paid 12k to Raju for transport")
if st.button("Send to Bot"):
    res = requests.post(f"{API_URL}/cash/telegram", json={"user_message": msg}).json()
    st.write(res)
    if res["status"] == "pending_approval":
        st.warning("⚠️ High value transaction ( >₹10k ) held for Owner approval.")
    else:
        st.success("✓ Transaction recorded in ledger.")
