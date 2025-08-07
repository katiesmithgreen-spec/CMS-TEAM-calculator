
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
)

st.markdown(f"""
<style>
h1, h2, h3 {{
    color: {PRIMARY_COLOR};
}}
div.stButton > button:first-child {{
    background-color: {BUTTON_COLOR};
    border-color: {BUTTON_COLOR};
    color: white;
}}
div.stButton > button:hover {{
    background-color: {PRIMARY_COLOR};
    border-color: {PRIMARY_COLOR};
}}
div[role="slider"] > div {{
    background-color: {PRIMARY_COLOR} !important;
}}
section[data-testid="stSidebar"] > div {{
    background-color: {SECONDARY_COLOR}20;
}}
</style>
""", unsafe_allow_html=True)

# --------------------------
# Fixed parameters
# --------------------------
CMS_DISCOUNT_PCT   = 3.0      # target-price haircut
CH_QUALITY_PPT     = 0.3      # reconciliation quality boost
CH_COST_EPISODE    = 1_000    # Current Health program cost per episode
HHA_EXTRA_COST     = 200      # delta vs baseline home-health
SNF_DAILY_COST     = 305      # median semi‑private room (Genworth 2024)
SNF_LOS_DAYS       = (22.1 + 30.8) / 2    # midpoint LOS

# Procedure‑specific baseline bundle cost ($) and SNF utilisation rate
PROCEDURE_META = {
    "Lower extremity joint replacement": {"baseline": 26_500, "snf_util": 0.45},
    "Hip/femur fracture":                {"baseline": 29_500, "snf_util": 0.70},
    "Spinal fusion":                     {"baseline": 42_000, "snf_util": 0.30},
    "Major bowel procedure":             {"baseline": 35_000, "snf_util": 0.25},
}

# Pre‑compute implicit cost‑reduction % for each procedure
for meta in PROCEDURE_META.values():
    snf_save      = meta["snf_util"] * SNF_LOS_DAYS * SNF_DAILY_COST
    net_savings   = snf_save - HHA_EXTRA_COST - CH_COST_EPISODE
    meta["savings_pct"] = round(net_savings / meta["baseline"] * 100, 1)

# --------------------------
# Header
# --------------------------
st.title("CMS TEAM ROI Calculator (2026–2030) – **Current Health Edition**")

st.markdown(
    """Enter your annual episode volumes. Cost deltas are auto‑calculated from
national averages:

* SNF daily cost **${:,.0f}**, LOS **{:.1f} days**
* Home‑health +${} per episode
* Current Health cost **${:,}** per episode
* Quality boost **+{:.1f} pp**

These can be adjusted in code when local data are available.""".format(
        SNF_DAILY_COST, SNF_LOS_DAYS, HHA_EXTRA_COST, CH_COST_EPISODE, CH_QUALITY_PPT)
)

# ----------------------------
# Sidebar – risk track
# ----------------------------
track = st.sidebar.selectbox(
    "TEAM Participation Track",
    [
        "Track 1 – Upside‑only in PY1",
        "Track 2 – Lower symmetric risk/reward",
        "Track 3 – Full symmetric risk/reward",
    ],
    index=0,
)

st.sidebar.caption("CMS discount, quality boost, and CH program cost are fixed.")

# ------------------------------------
# Volume sliders
# ------------------------------------
st.subheader("Annual Episode Volumes")

rows = []
total_volume = 0

for proc, meta in PROCEDURE_META.items():
    with st.container(border=True):
        st.markdown(f"**{proc}**")
        st.caption(
            f"Bundled payment: **${meta['baseline']:,.0f}**  • "
            f"SNF use: {int(meta['snf_util']*100)}% × {SNF_LOS_DAYS:.1f} d"
        )
        vol = st.slider(
            "Volume",
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
                "Baseline cost": meta["baseline"],
                "Cost‑reduction %": meta["savings_pct"],
            }
        )

if total_volume == 0:
    st.warning("Use the sliders above to enter at least one non‑zero volume.")
    st.stop()

df = pd.DataFrame(rows)

# -------------------------
# Calculations
# -------------------------
df["Target price"] = df["Baseline cost"] * (1 - CMS_DISCOUNT_PCT / 100)
df["Expected cost"] = df["Baseline cost"] * (1 - df["Cost‑reduction %"] / 100)
df["Reconciliation $/episode"] = df["Target price"] - df["Expected cost"]
df["Annual reconciliation"] = df["Reconciliation $/episode"] * df["Volume"]
df["Quality‑adjusted reconciliation"] = df["Annual reconciliation"] * (1 + CH_QUALITY_PPT / 100)

impl_cost_total = total_volume * CH_COST_EPISODE

# -------------------------
# Results
# -------------------------
st.subheader("Results")

fmt = {"$": "${:,.0f}", "%": "{:,.1f}%"}

with st.expander("Detailed calculations"):
    st.dataframe(df.style.format({
        "Baseline cost": "${:,.0f}",
        "Target price": "${:,.0f}",
        "Expected cost": "${:,.0f}",
        "Reconciliation $/episode": "${:,.0f}",
        "Annual reconciliation": "${:,.0f}",
        "Quality‑adjusted reconciliation": "${:,.0f}",
        "Cost‑reduction %": "{:,.1f}%",
    }), use_container_width=True)

total_rec = df["Quality‑adjusted reconciliation"].sum()
net_impact = total_rec - impl_cost_total
roi_pct = (net_impact / impl_cost_total * 100) if impl_cost_total else 0

st.markdown(f"### 📈 Reconciliation payment: **${total_rec:,.0f}**")
st.markdown(
    f"### 💸 Current Health program cost: **${impl_cost_total:,.0f}** "
    f"*({total_volume} episodes × ${CH_COST_EPISODE:,})*"
)
st.markdown(f"### 💰 Net impact: **${net_impact:,.0f}**")
st.markdown(f"### 🔄 ROI: **{roi_pct:,.1f}%**")

st.caption(
    "Results assume upside‑only reconciliation. Downside risk not yet modelled for Tracks 2‑3."
)
