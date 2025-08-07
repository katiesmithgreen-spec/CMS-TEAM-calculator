
import streamlit as st
import pandas as pd

# --------------------------
# Brand colours & CSS tweak
# --------------------------
PRIMARY_COLOR   = "#5842ff"
BUTTON_COLOR    = "#ff4861"
SECONDARY_COLOR = "#110854"

st.set_page_config(
    page_title="CMS TEAM ROI Calculator – Current Health",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Inject basic brand styling (limited by Streamlit CSS API)
st.markdown(f"""
<style>
/* Title & headings */
h1, h2, h3, h4 {{
    color: {PRIMARY_COLOR};
}}
/* Buttons */
div.stButton > button:first-child {{
    background-color: {BUTTON_COLOR};
    border-color: {BUTTON_COLOR};
    color: white;
}}
div.stButton > button:hover {{
    background-color: {PRIMARY_COLOR};
    border-color: {PRIMARY_COLOR};
}}
/* Slider accent */
div[role="slider"] > div {{
    background-color: {PRIMARY_COLOR} !important;
}}
/* Sidebar background */
section[data-testid="stSidebar"] > div {{
    background-color: {SECONDARY_COLOR}20; /* 20 = 12% opacity */
}}
</style>
""", unsafe_allow_html=True)

# --------------------------
# Fixed constants for CH
# --------------------------
CMS_DISCOUNT_PCT = 3.0       # Target-price haircut applied by CMS
CH_SAVINGS_PCT   = 6.0       # Extra cost‑reduction percentage points per episode
CH_QUALITY_PPT   = 0.3       # Quality score boost (percentage‑points)
CH_COST_EPISODE  = 1_000     # Current Health program cost per treated episode (USD)

# --------------------------
# App Title
# --------------------------
st.title("CMS TEAM ROI Calculator (2026–2030) – **Current Health Edition**")

st.markdown(
    f"""Enter your **annual episode volumes**.  
The calculator applies fixed Current Health assumptions:

* **–{CH_SAVINGS_PCT:.0f}%** incremental episode‑cost savings  
* **+{CH_QUALITY_PPT:.1f} pp** quality‑score boost  
* **${CH_COST_EPISODE:,}** program cost per treated episode  

Baseline costs use illustrative national averages; adjust in code when CMS releases official target‑price files.""")

# ----------------------------
# Sidebar – select risk track
# ----------------------------
track = st.sidebar.selectbox(
    "TEAM Participation Track",
    [
        "Track 1 – Upside‑only in PY1 (default)",
        "Track 2 – Lower symmetric risk/reward",
        "Track 3 – Full symmetric risk/reward",
    ],
    index=0,
    help="Track affects downside liability. This calculator currently models *upside only*; add downside logic later for Tracks 2/3.",
)

st.sidebar.caption("CMS discount, quality boost, and program cost are fixed.")

# ------------------------------------
# Main area – episode volumes sliders
# ------------------------------------
st.subheader("Annual Episode Volumes")

DEFAULT_EPISODES = {
    "Lower extremity joint replacement": 26_500,
    "Hip/femur fracture": 29_500,
    "Spinal fusion": 42_000,
    "Coronary artery bypass graft": 48_000,
    "Major bowel procedure": 35_000,
}

rows = []
total_volume = 0

for proc, baseline_cost in DEFAULT_EPISODES.items():
    with st.container(border=True):
        st.markdown(f"**{proc}**")
        st.caption(f"Typical bundled payment: **${baseline_cost:,.0f}** (CMS national average)")
        vol = st.slider(
            "Annual volume",
            min_value=0,
            max_value=500,
            value=0,
            step=1,
            key=f"vol_{proc}",
        )
        total_volume += vol
        rows.append(
            {
                "Procedure": proc,
                "Volume": vol,
                "Baseline cost": baseline_cost,
                "Cost-reduction %": CH_SAVINGS_PCT,
            }
        )

if total_volume == 0:
    st.warning("Use the sliders above to enter at least one non‑zero volume.")
    st.stop()

# -------------------------
# Dataframe & calculations
# -------------------------
df = pd.DataFrame(rows)

df["Target price"] = df["Baseline cost"] * (1 - CMS_DISCOUNT_PCT / 100)
df["Expected cost"] = df["Baseline cost"] * (1 - df["Cost-reduction %"] / 100)
df["Reconciliation $/episode"] = df["Target price"] - df["Expected cost"]
df["Annual reconciliation"] = df["Reconciliation $/episode"] * df["Volume"]

df["Quality-adjusted reconciliation"] = df["Annual reconciliation"] * (1 + CH_QUALITY_PPT / 100)

# Program cost
impl_cost_total = total_volume * CH_COST_EPISODE

# -------------------------
# Results output
# -------------------------
st.subheader("Results")

fmt_cols = {
    "Baseline cost": "${:,.0f}",
    "Target price": "${:,.0f}",
    "Expected cost": "${:,.0f}",
    "Reconciliation $/episode": "${:,.0f}",
    "Annual reconciliation": "${:,.0f}",
    "Quality-adjusted reconciliation": "${:,.0f}",
}

with st.expander("Detailed table"):
    st.dataframe(df.style.format(fmt_cols), use_container_width=True)

total_rec = df["Quality-adjusted reconciliation"].sum()
net_impact = total_rec - impl_cost_total
roi_pct = (net_impact / impl_cost_total * 100) if impl_cost_total else 0

st.markdown(f"### 📈 Total expected reconciliation payment: **${total_rec:,.0f}**")
st.markdown(
    f"### 💸 Current Health program cost: **${impl_cost_total:,.0f}** "
    f"*({total_volume} episodes × ${CH_COST_EPISODE:,})*"
)
st.markdown(f"### 💰 Net annual impact: **${net_impact:,.0f}**")
st.markdown(f"### 🔄 Estimated ROI: **{roi_pct:,.1f}%**")

st.caption(
    "ROI reflects upside‑only reconciliation. "
    "Add downside‑risk modeling for Tracks 2/3 to complete the picture."
)
