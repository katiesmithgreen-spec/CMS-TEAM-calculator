
import streamlit as st
import pandas as pd

# --------------------------
# Brand colours
# --------------------------
PRIMARY_COLOR   = "#5842ff"
BUTTON_COLOR    = "#ff4861"
SECONDARY_COLOR = "#110854"

st.set_page_config(
    page_title="CMS TEAM ROI Calculator – Current Health",
    page_icon="🩺",
    layout="centered",
)

# --------------------------
# Custom CSS
# --------------------------
st.markdown(f"""
<style>
/* Brand accents */
h1, h2 {{
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
/* Slider thumb & track */
div[role='slider'] > div {{
    background-color: {PRIMARY_COLOR} !important;
}}
/* --- Slider value label: black text, no bubble --- */
div[data-testid='stSlider'] span {{
    background: transparent !important;
    color: black !important;
    box-shadow: none !important;
}}
/* Results section: standardize font colour & weight */
.results p, .results h3 {{
    color: black !important;
    font-weight: 600;
}}
</style>
""", unsafe_allow_html=True)

# --------------------------
# Fixed parameters
# --------------------------
CMS_DISCOUNT_PCT   = 3.0
CH_QUALITY_PPT     = 0.3
CH_COST_EPISODE    = 1_000
HHA_EXTRA_COST     = 200
SNF_DAILY_COST     = 305
SNF_LOS_DAYS       = (22.1 + 30.8) / 2

PROCEDURE_META = {
    "Lower extremity joint replacement": {"baseline": 26_500, "snf_util": 0.45},
    "Hip/femur fracture":                {"baseline": 29_500, "snf_util": 0.70},
    "Spinal fusion":                     {"baseline": 42_000, "snf_util": 0.30},
    "Major bowel procedure":             {"baseline": 35_000, "snf_util": 0.25},
}

for meta in PROCEDURE_META.values():
    snf_save = meta["snf_util"] * SNF_LOS_DAYS * SNF_DAILY_COST
    net_savings = snf_save - HHA_EXTRA_COST - CH_COST_EPISODE
    meta["savings_pct"] = round(net_savings / meta["baseline"] * 100, 1)

# --------------------------
# UI
# --------------------------
st.title("CMS TEAM ROI Calculator – Current Health Edition")

st.markdown(
    f"""Enter your annual episode volumes. SNF utilisation rates and costs are pre‑filled from national data.
* SNF daily cost **${SNF_DAILY_COST:,}**, LOS **{SNF_LOS_DAYS:.1f} d**
* Home‑health delta +${HHA_EXTRA_COST}
* Current Health cost **${CH_COST_EPISODE:,}** / episode
* Quality boost **+{CH_QUALITY_PPT:.1f} pp**""")

track = st.sidebar.selectbox(
    "TEAM Participation Track",
    ["Track 1 – Upside only", "Track 2 – Lower risk", "Track 3 – Full risk"],
    index=0,
)

st.sidebar.caption("Financial assumptions baked into the model.")

st.subheader("Annual Episode Volumes")

rows = []
total_volume = 0

for proc, meta in PROCEDURE_META.items():
    with st.container(border=True):
        st.markdown(f"**{proc}**")
        st.caption(f"Bundled payment ${meta['baseline']:,}  •  SNF use {int(meta['snf_util']*100)}% × {SNF_LOS_DAYS:.1f} d")
        vol = st.slider(
            "Volume",
            min_value=0,
            max_value=500,
            value=0,
            step=1,
            key=f"vol_{proc}",
        )
        total_volume += vol
        rows.append({
            "Procedure": proc,
            "Volume": vol,
            "Baseline cost": meta["baseline"],
            "Cost-reduction %": meta["savings_pct"],
        })

if total_volume == 0:
    st.warning("Move any slider above zero to calculate ROI.")
    st.stop()

df = pd.DataFrame(rows)

# -------------------------
# Calculations
# -------------------------
df["Target price"] = df["Baseline cost"] * (1 - CMS_DISCOUNT_PCT / 100)
df["Expected cost"] = df["Baseline cost"] * (1 - df["Cost-reduction %"] / 100)
df["Reconciliation $/episode"] = df["Target price"] - df["Expected cost"]
df["Annual reconciliation"] = df["Reconciliation $/episode"] * df["Volume"]
df["Quality-adjusted reconciliation"] = df["Annual reconciliation"] * (1 + CH_QUALITY_PPT / 100)

impl_cost_total = total_volume * CH_COST_EPISODE

# -------------------------
# Results
# -------------------------
with st.container(className="results"):
    st.markdown("### Results")
    total_rec = df["Quality-adjusted reconciliation"].sum()
    net_impact = total_rec - impl_cost_total
    roi_pct = (net_impact / impl_cost_total * 100) if impl_cost_total else 0

    st.markdown(f"**Reconciliation payment:** ${total_rec:,.0f}")
    st.markdown(f"**Current Health program cost:** ${impl_cost_total:,.0f}  ({total_volume} episodes × ${CH_COST_EPISODE:,})")
    st.markdown(f"**Net impact:** ${net_impact:,.0f}")
    st.markdown(f"**ROI:** {roi_pct:,.1f}%")

with st.expander("Detailed table ▼"):
    st.dataframe(df.style.format({
        "Baseline cost": "${:,.0f}",
        "Target price": "${:,.0f}",
        "Expected cost": "${:,.0f}",
        "Reconciliation $/episode": "${:,.0f}",
        "Annual reconciliation": "${:,.0f}",
        "Quality-adjusted reconciliation": "${:,.0f}",
        "Cost-reduction %": "{:,.1f}%",
    }), use_container_width=True)
