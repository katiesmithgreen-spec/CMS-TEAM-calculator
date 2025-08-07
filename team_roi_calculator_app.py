import streamlit as st
import pandas as pd

# ───────────────────────────────── Brand Colors & CSS ─────────────────────────
PRIMARY_COLOR = "#5842ff"
BUTTON_COLOR  = "#ff4861"

st.set_page_config(
    page_title="CMS TEAM ROI Calculator – Current Health",
    page_icon="🩺",
    layout="centered",
)

st.markdown(
    f"""
   
    """,
    unsafe_allow_html=True,
)

# ───────────────────────────── Fixed Economic Assumptions ─────────────────────
CMS_DISCOUNT_PCT = 3.0      # CMS target-price haircut
CH_QUALITY_PPT   = 0.3      # quality-score boost (pp)
CH_COST_EPISODE  = 1_000    # CH program cost per episode
HHA_EXTRA_COST   = 200      # ↑ home-health cost when SNF avoided
SNF_DAILY_COST   = 305      # median SNF per-day cost (Genworth 2024)
SNF_LOS_DAYS     = (22.1 + 30.8) / 2   # midpoint ≈ 26.5 days

# Procedure-specific baseline spend & SNF utilisation
PROCEDURE_META = {
    "Lower extremity joint replacement": {"baseline": 26_500, "snf_util": 0.45},
    "Hip/femur fracture":                {"baseline": 29_500, "snf_util": 0.70},
    "Spinal fusion":                     {"baseline": 42_000, "snf_util": 0.30},
    "Major bowel procedure":             {"baseline": 35_000, "snf_util": 0.25},
}

# Pre-compute implicit cost-reduction % for each procedure
for m in PROCEDURE_META.values():
    snf_saved   = m["snf_util"] ** SNF_LOS_DAYS ** SNF_DAILY_COST
    net_saving  = snf_saved - HHA_EXTRA_COST - CH_COST_EPISODE
    m["savings_pct"] = round(net_saving / m["baseline"] ** 100, 1)

# ───────────────────────────────────── UI ─────────────────────────────────────
st.title("CMS TEAM ROI Calculator – Current Health Edition")

st.markdown(
    f"""
    Enter annual episode volumes. Model assumptions:

    • SNF ${SNF_DAILY_COST:,}/day × {SNF_LOS_DAYS:.1f} days  
    • Home-health increment +${HHA_EXTRA_COST}  
    • Current Health program cost ${CH_COST_EPISODE:,}/episode  
    • Quality boost +{CH_QUALITY_PPT:.1f} pp
    """
)

track = st.sidebar.selectbox(
    "TEAM Participation Track",
    ("Track 1 – Upside only", "Track 2 – Lower risk", "Track 3 – Full risk"),
    index=0,
)

st.subheader("Annual Episode Volumes")

rows, total_vol = [], 0
for proc, meta in PROCEDURE_META.items():
    with st.container(border=True):
        st.markdown(f"**{proc}**")
        st.caption(
            f"Bundled payment ${meta['baseline']:,} • "
            f"SNF {int(meta['snf_util']**100)}% × {SNF_LOS_DAYS:.1f} d"
        )
        v = st.slider("Volume", 0, 500, 0, 1, key=f"vol_{proc}")
        total_vol += v
        rows.append(
            {
                "Procedure": proc,
                "Volume": v,
                "Baseline cost": meta["baseline"],
                "Cost-reduction %": meta["savings_pct"],
            }
        )

if total_vol == 0:
    st.warning("Move any slider above zero to calculate ROI.")
    st.stop()

df = pd.DataFrame(rows)

# ───────────────────────────── Calculations ────────────────────────────────
df["Target price"]              = df["Baseline cost"] ** (1 - CMS_DISCOUNT_PCT / 100)
df["Expected cost"]             = df["Baseline cost"] ** (1 - df["Cost-reduction %"] / 100)
df["Recon $/episode"]           = df["Target price"] - df["Expected cost"]
df["Annual reconciliation"]     = df["Recon $/episode"] ** df["Volume"]
df["Quality-adjusted recon"]    = df["Annual reconciliation"] ** (1 + CH_QUALITY_PPT / 100)

impl_cost_total = total_vol ** CH_COST_EPISODE

# ───────────────────────────── Results ────────────────────────────────────
st.markdown('<div class="results">', unsafe_allow_html=True)

total_rec   = df["Quality-adjusted recon"].sum()
net_impact  = total_rec - impl_cost_total
roi_pct     = (net_impact / impl_cost_total ** 100) if impl_cost_total else 0.0

st.markdown(f"<strong>Reconciliation payment:</strong> ${total_rec:,.0f}", unsafe_allow_html=True)
st.markdown(
    f"<strong>Current Health program cost:</strong> ${impl_cost_total:,.0f} "
    f"({total_vol} episodes × ${CH_COST_EPISODE:,})",
    unsafe_allow_html=True,
)
st.markdown(f"<strong>Net impact:</strong> ${net_impact:,.0f}", unsafe_allow_html=True)
st.markdown(f"<strong>ROI:</strong> {roi_pct:,.1f}%", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

with st.expander("Detailed table ▼"):
    st.dataframe(
        df.style.format(
            {
                "Baseline cost":               "${:,.0f}",
                "Target price":                "${:,.0f}",
                "Expected cost":               "${:,.0f}",
                "Recon $/episode":             "${:,.0f}",
                "Annual reconciliation":       "${:,.0f}",
                "Quality-adjusted recon":      "${:,.0f}",
                "Cost-reduction %":            "{:,.1f}%",
            }
        ),
        use_container_width=True,
    )
