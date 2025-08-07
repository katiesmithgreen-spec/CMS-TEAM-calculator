import streamlit as st
import pandas as pd

# ── Fixed economic assumptions ───────────────────────────────────────────────
CMS_DISCOUNT_PCT = 3.0            # CMS target-price haircut
CH_QUALITY_PPT   = 0.3            # quality-score boost (pp)
CH_COST_EPISODE  = 1_000          # Current Health program cost per episode (USD)
HHA_EXTRA_COST   = 200            # ↑ home-health spend when SNF avoided
SNF_DAILY_COST   = 305            # national median SNF per-day cost
SNF_LOS_DAYS     = (22.1 + 30.8) / 2   # midpoint length of stay ≈ 26.5 d

PROCEDURE_META = {
    "Lower extremity joint replacement": {"baseline": 26_500, "snf_util": 0.45},
    "Hip/femur fracture":                {"baseline": 29_500, "snf_util": 0.70},
    "Spinal fusion":                     {"baseline": 42_000, "snf_util": 0.30},
    "Major bowel procedure":             {"baseline": 35_000, "snf_util": 0.25},
}

# Pre-compute implicit cost-reduction % for each procedure
for meta in PROCEDURE_META.values():
    snf_saved  = meta["snf_util"] * SNF_LOS_DAYS * SNF_DAILY_COST
    net_saved  = snf_saved - HHA_EXTRA_COST - CH_COST_EPISODE
    meta["savings_pct"] = round(net_saved / meta["baseline"] * 100, 1)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="CMS TEAM ROI Calculator – Current Health",
                   layout="centered")

# ── Header ───────────────────────────────────────────────────────────────────
st.title("CMS TEAM ROI Calculator – Current Health Edition")
st.markdown(
    f"""
**Model assumptions**

• SNF ${SNF_DAILY_COST:,}/day × {SNF_LOS_DAYS:.1f} days  
• Home-health increment +${HHA_EXTRA_COST}  
• Current Health cost ${CH_COST_EPISODE:,}/episode  
• Quality boost +{CH_QUALITY_PPT:.1f} pp
"""
)

# ── Sidebar track selector ───────────────────────────────────────────────────
track = st.sidebar.radio(
    "TEAM participation track",
    ["Track 1 - Upside only", "Track 2 - Lower risk", "Track 3 - Full risk"],
    index=0,
)
