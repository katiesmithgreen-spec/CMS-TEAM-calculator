
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
# Custom CSS (slider bubble fix & brand accents)
# --------------------------
st.markdown(f"""
<style>
/* Headings in brand colour */
h1, h2 {{
    color: {PRIMARY_COLOR};
}}
/* Button styling */
div.stButton > button:first-child {{
    background-color: {BUTTON_COLOR};
    border-color: {BUTTON_COLOR};
    color: #ffffff;
}}
div.stButton > button:hover {{
    background-color: {PRIMARY_COLOR};
    border-color: {PRIMARY_COLOR};
}}
/* Slider rail accent */
div[role='slider'] > div {{

}}
/* --- Slider value bubble -------------------------------------------------- */
div[data-testid='stThumbValue'] {{
    background: #ffffff !important;  /* transparent/white bubble */
    color:  #5842ff !important;      /* near‑black text */
    box-shadow: none !important;
    border: none !important;
}}
/* Results text */
.results p, .results h3 {{
    color: #010203 !important;
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
SNF_LOS_DAYS       = (22.1 + 30.8) / 2  # midpoint ≈ 26.5 days

PROCEDURE_META = {
    "Lower extremity joint replacement": {"baseline": 26_500, "snf_util": 0.45},
    "Hip/femur fracture":                {"baseline": 29_500, "snf_util": 0.70},
    "Spinal fusion":                     {"baseline": 42_000, "snf_util": 0.30},
    "Major bowel procedure":             {"baseline": 35_000, "snf_util": 0.25},
}

# Pre‑compute cost‑reduction % for each procedure
for meta in PROCEDURE_META.values():
    snf_savings = meta["snf_util"] * SNF_LOS_DAYS * SNF_DAILY_COST
    net_savings = snf_savings - HHA_EXTRA_COST - CH_COST_EPISODE
    meta["savings_pct"] = round(net_savings / meta["baseline"] * 100, 1)

# --------------------------
# Header
# --------------------------
st.title("CMS TEAM ROI Calculator – Current Health Edition")

st.markdown(
    f"""Enter annual episode volumes. Assumptions baked in:

* SNF daily cost **${SNF_DAILY_COST:,}**, LOS **{SNF_LOS_DAYS:.1f} days**
* Home‑health delta +${HHA_EXTRA_COST}
* Current Health cost **${CH_COST_EPISODE:,}** per episode
* Quality boost **+{CH_QUALITY_PPT:.1f} pp**""")

# ----------------------------
# Sidebar – risk track
# ----------------------------
track = st.sidebar.selectbox(
    "TEAM Participation Track",
    ("Track 1 – Upside only", "Track 2 – Lower risk", "Track 3 – Full risk"),
    index=0,
)
st.sidebar.caption("Financial assumptions are fixed in code.")

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
            f"Bundled payment ${meta['baseline']:,} • "
            f"SNF use {int(meta['snf_util']*100)}% × {SNF_LOS_DAYS:.1f} d"
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
with st.container():
    st.markdown('<div class="results">', unsafe_allow_html=True)

    total_rec = df["Quality-adjusted reconciliation"].sum()
    net_impact = total_rec - impl_cost_total
    roi_pct = (net_impact / impl_cost_total * 100) if impl_cost_total else 0

    st.markdown(f"### Reconciliation payment: **${total_rec:,.0f}**")
    st.markdown(f"### Current Health program cost: **${impl_cost_total:,.0f}** "
                f"({total_volume} episodes × ${CH_COST_EPISODE:,})")
    st.markdown(f"### Net impact: **${net_impact:,.0f}**")
    st.markdown(f"### ROI: **{roi_pct:,.1f}%**")

    st.markdown('</div>', unsafe_allow_html=True)

with st.expander("Detailed table ▼"):
    st.dataframe(
        df.style.format({
            "Baseline cost": "${:,.0f}",
            "Target price": "${:,.0f}",
            "Expected cost": "${:,.0f}",
            "Reconciliation $/episode": "${:,.0f}",
            "Annual reconciliation": "${:,.0f}",
            "Quality-adjusted reconciliation": "${:,.0f}",
            "Cost-reduction %": "{:,.1f}%",
        }),
        use_container_width=True
    )
