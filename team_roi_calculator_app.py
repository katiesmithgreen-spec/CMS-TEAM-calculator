
import streamlit as st
import pandas as pd

# ---------------- Fixed assumptions ----------------
CMS_DISCOUNT_PCT = 3.0
CH_QUALITY_PPT   = 0.3
CH_COST_EPISODE  = 1_000
HHA_EXTRA_COST   = 200
SNF_DAILY_COST   = 305
SNF_LOS_DAYS     = (22.1 + 30.8) / 2  # 26.5

PROCEDURE_META = {
    "Lower extremity joint replacement": {"baseline": 26_500, "snf_util": 0.45},
    "Hip/femur fracture":                {"baseline": 29_500, "snf_util": 0.70},
    "Spinal fusion":                     {"baseline": 42_000, "snf_util": 0.30},
    "Major bowel procedure":             {"baseline": 35_000, "snf_util": 0.25},
}

for meta in PROCEDURE_META.values():
    snf_saved = meta["snf_util"] * SNF_LOS_DAYS * SNF_DAILY_COST
    net_saved = snf_saved - HHA_EXTRA_COST - CH_COST_EPISODE
    meta["savings_pct"] = round(net_saved / meta["baseline"] * 100, 1)

# ---------------- Streamlit config ----------------
st.set_page_config(page_title="CMS TEAM ROI Calculator – Current Health",
                   layout="centered")

st.title("CMS TEAM ROI Calculator – Current Health Edition")

st.markdown(
    f"""**Model assumptions**

* SNF ${SNF_DAILY_COST:,}/day × {SNF_LOS_DAYS:.1f} days  
* Home‑health increment +${HHA_EXTRA_COST}  
* Current Health cost ${CH_COST_EPISODE:,}/episode  
* Quality boost +{CH_QUALITY_PPT:.1f} pp""")

# Sidebar track selector
track = st.sidebar.radio("TEAM participation track",
                         ("Track 1 – Upside only", "Track 2 – Lower risk", "Track 3 – Full risk"))

# ---------------- Volume inputs ----------------
st.header("Annual episode volumes")

rows = []
total_vol = 0
for proc, meta in PROCEDURE_META.items():
    st.write(f"### {proc}")
    st.caption(f"Bundled payment ${meta['baseline']:,} • "
               f"SNF {int(meta['snf_util']*100)}% × {SNF_LOS_DAYS:.1f} d")
    vol = st.number_input("Volume", 0, 500, 0, 1, key=f"vol_{proc}")
    total_vol += vol
    rows.append({"Procedure": proc,
                 "Volume": vol,
                 "Baseline cost": meta["baseline"],
                 "Cost-reduction %": meta["savings_pct"]})

if total_vol == 0:
    st.warning("Enter at least one volume above zero.")
    st.stop()

df = pd.DataFrame(rows)

# ---------------- Calculations ----------------
df["Target price"]           = df["Baseline cost"] * (1 - CMS_DISCOUNT_PCT / 100)
df["Expected cost"]          = df["Baseline cost"] * (1 - df["Cost-reduction %"] / 100)
df["Recon per episode"]      = df["Target price"] - df["Expected cost"]
df["Annual reconciliation"]  = df["Recon per episode"] * df["Volume"]
df["Quality‑adjusted recon"] = df["Annual reconciliation"] * (1 + CH_QUALITY_PPT / 100)

impl_cost_total = total_vol * CH_COST_EPISODE

# ---------------- Results ----------------
st.header("Results")

total_rec  = df["Quality‑adjusted recon"].sum()
net_impact = total_rec - impl_cost_total
roi_pct    = (net_impact / impl_cost_total * 100) if impl_cost_total else 0.0

st.metric("Reconciliation payment", f"${total_rec:,.0f}")
st.metric("Program cost", f"${impl_cost_total:,.0f}")
st.metric("Net impact", f"${net_impact:,.0f}")
st.metric("ROI", f"{roi_pct:,.1f}%")

with st.expander("Calculation table"):
    st.dataframe(df.style.format({
        "Baseline cost": "${:,.0f}",
        "Target price": "${:,.0f}",
        "Expected cost": "${:,.0f}",
        "Recon per episode": "${:,.0f}",
        "Annual reconciliation": "${:,.0f}",
        "Quality‑adjusted recon": "${:,.0f}",
        "Cost-reduction %": "{:,.1f}%",
    }), use_container_width=True)
