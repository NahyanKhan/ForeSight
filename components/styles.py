"""
ForeSight — Custom CSS Theme
Premium dark mode with glassmorphism, gradients, and micro-animations.
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --primary: #00D4AA;
    --primary-dim: #00A88A;
    --secondary: #6366F1;
    --accent: #F59E0B;
    --danger: #EF4444;
    --warning: #F97316;
    --success: #10B981;
    --bg-dark: #0A0E17;
    --bg-card: #111827;
    --bg-hover: #1F2937;
    --text: #E2E8F0;
    --text-dim: #94A3B8;
    --border: #1E293B;
    --glow-primary: 0 0 20px rgba(0, 212, 170, 0.3);
    --glow-danger: 0 0 20px rgba(239, 68, 68, 0.3);
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif !important;
    background: var(--bg-dark) !important;
}

/* ─── Header ─── */
.main-header {
    text-align: center;
    padding: 1.5rem 0 1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}
.main-header h1 {
    font-size: 2.8rem;
    font-weight: 900;
    background: linear-gradient(135deg, #00D4AA, #6366F1, #F59E0B);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    letter-spacing: -1px;
}
.main-header .tagline {
    color: var(--text-dim);
    font-size: 0.95rem;
    margin-top: 0.3rem;
    font-weight: 400;
}

/* ─── Metric Cards ─── */
.metric-card {
    background: linear-gradient(145deg, #111827, #1a2235);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}
.metric-card:hover {
    border-color: var(--primary);
    box-shadow: var(--glow-primary);
    transform: translateY(-2px);
}
.metric-card .label {
    font-size: 0.8rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-weight: 600;
}
.metric-card .value {
    font-size: 2.2rem;
    font-weight: 800;
    color: var(--text);
    margin: 0.3rem 0;
    font-family: 'JetBrains Mono', monospace;
}
.metric-card .sub {
    font-size: 0.8rem;
    color: var(--text-dim);
    font-weight: 400;
}
.metric-card.danger { border-left: 4px solid var(--danger); }
.metric-card.warning { border-left: 4px solid var(--warning); }
.metric-card.success { border-left: 4px solid var(--success); }
.metric-card.primary { border-left: 4px solid var(--primary); }
.metric-card.secondary { border-left: 4px solid var(--secondary); }

/* ─── Runway Gauge ─── */
.runway-display {
    text-align: center;
    padding: 2rem;
    background: linear-gradient(145deg, #0d1320, #131b2e);
    border: 1px solid var(--border);
    border-radius: 20px;
    position: relative;
}
.runway-display .days {
    font-size: 5rem;
    font-weight: 900;
    font-family: 'JetBrains Mono', monospace;
    background: linear-gradient(135deg, #00D4AA, #10B981);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
}
.runway-display .days.critical {
    background: linear-gradient(135deg, #EF4444, #F97316);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: pulse-danger 2s ease-in-out infinite;
}
.runway-display .ci {
    font-size: 1.1rem;
    color: var(--text-dim);
    margin-top: 0.5rem;
    font-family: 'JetBrains Mono', monospace;
}
.runway-display .runway-label {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--primary);
    font-weight: 700;
    margin-bottom: 0.5rem;
}

@keyframes pulse-danger {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

/* ─── Buyer Cards ─── */
.buyer-card {
    background: linear-gradient(145deg, #111827, #1a2235);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
    transition: all 0.3s ease;
    cursor: pointer;
}
.buyer-card:hover {
    border-color: var(--primary);
    box-shadow: var(--glow-primary);
    transform: translateX(4px);
}
.buyer-card .buyer-name {
    font-weight: 700;
    font-size: 1rem;
    color: var(--text);
}
.buyer-card .buyer-score {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 800;
    font-size: 1.6rem;
}
.buyer-card .buyer-trend {
    font-size: 0.85rem;
    font-weight: 600;
}
.score-high { color: #10B981; }
.score-mid { color: #F59E0B; }
.score-low { color: #EF4444; }

/* ─── Section Headers ─── */
.section-header {
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--text);
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--primary);
    margin: 1.5rem 0 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ─── FHE Panel ─── */
.fhe-panel {
    background: linear-gradient(145deg, #0d1320, #131b2e);
    border: 1px solid #1E293B;
    border-radius: 14px;
    padding: 1.2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
}
.fhe-step {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.5rem 0;
    border-bottom: 1px solid #1a2235;
    color: var(--text-dim);
}
.fhe-step:last-child { border-bottom: none; }

/* ─── Alert Boxes ─── */
.alert-box {
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin: 0.8rem 0;
    font-size: 0.9rem;
}
.alert-danger {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #FCA5A5;
}
.alert-warning {
    background: rgba(249, 115, 22, 0.1);
    border: 1px solid rgba(249, 115, 22, 0.3);
    color: #FDBA74;
}
.alert-success {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #6EE7B7;
}

/* ─── Cash Transaction Table ─── */
.tx-pending {
    background: rgba(249, 115, 22, 0.08);
    border-left: 3px solid var(--warning);
    padding: 0.6rem;
    border-radius: 8px;
    margin-bottom: 0.4rem;
}
.tx-approved {
    background: rgba(16, 185, 129, 0.05);
    border-left: 3px solid var(--success);
    padding: 0.6rem;
    border-radius: 8px;
    margin-bottom: 0.4rem;
}

/* ─── Navigation Tabs ─── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: #111827;
    border-radius: 12px;
    padding: 4px;
    border: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 0.6rem 1.5rem;
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--text-dim);
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(0, 212, 170, 0.15), rgba(99, 102, 241, 0.15)) !important;
    color: var(--primary) !important;
}

/* ─── Scrollbar ─── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-dark); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--primary-dim); }

/* ─── Plotly Chart Containers ─── */
.js-plotly-plot { border-radius: 12px !important; }

/* ─── Sidebar ─── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1320, #111827) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .stMarkdown h1 {
    font-size: 1.4rem;
    background: linear-gradient(135deg, #00D4AA, #6366F1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* ─── Hide Streamlit Branding ─── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }

/* ─── Glassmorphism containers ─── */
.glass-container {
    background: rgba(17, 24, 39, 0.7);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 1.5rem;
}
</style>
"""
