import streamlit as st
import pandas as pd

    st.set_page_config(page_title="CMS TEAM ROI Calculator", layout="centered")

    st.title("CMS TEAM Model ROI Calculator (2026–2030)")

    st.markdown(
        """
This interactive tool helps hospitals estimate the *financial return on investment (ROI)* from participating in the **Centers for Medicare & Medicaid Services (CMS) Transforming Episode Accountability Model (TEAM)**, which begins January 1, 2026.

**How it works**  
▪ **You provide** your current episode volumes, baseline costs, expected cost‑reduction percentages, and global assumptions such as the CMS discount factor, quality adjustment, and annual implementation cost.  
▪ **The calculator estimates** the annual reconciliation payment (or repayment) under TEAM and computes a simple ROI:  
`ROI = (Annual reconciliation payment – Implementation cost) ÷ Implementation cost`.

> *Disclaimer – This calculator is for planning purposes only. It uses simplified assumptions and does **not** model every nuance of TEAM (e.g., cap thresholds, stop‑loss / stop‑gain, high‑cost outlier payments). Replace the default assumptions with your own hospital’s data and the official CMS target pricing files once released.*
"""
    )

    # ----------------------------
    # Sidebar – global assumptions
    # ----------------------------

    st.sidebar.header("Global Assumptions")

    track = st.sidebar.selectbox(
        "TEAM Participation Track",
        [
            "Track 1 – No downside risk in PY1 (default)",
            "Track 2 – Lower risk / reward (PY2‑PY5)",
            "Track 3 – Full risk / reward (PY1‑PY5)",
        ],
        help="TEAM offers three graduated risk tracks. This calculator assumes upside‑only in PY1 for Track 1 and symmetric risk for Tracks 2 & 3. Adjust additional modeling offline if needed.",
    )

    discount_pct = st.sidebar.number_input(
        "CMS discount applied to target price (%)",
        min_value=0.0,
        max_value=10.0,
        value=3.0,
        step=0.1,
        help="CMS typically discounts historical average spend to set the target price (3 % is used in many prior bundled models).",
    )

    quality_adj_pct = st.sidebar.number_input(
        "Quality performance adjustment (%)",
        min_value=-5.0,
        max_value=5.0,
        value=0.0,
        step=0.1,
        help="Positive value boosts reconciliation; negative reduces it. Range here mirrors ±5 percentage points cap in prior CMS models.",
    )

    impl_cost_total = st.sidebar.number_input(
        "Total annual implementation cost ($)",
        min_value=0.0,
        value=250_000.0,
        step=10_000.0,
        help="Include staffing, care‑redesign programs, IT, analytics, and vendor fees.",
    )

    st.sidebar.markdown("---")

    # ------------------------------------
    # Main area – episode‑level assumptions
    # ------------------------------------

    st.subheader("Episode Inputs (per performance year)")

    DEFAULT_EPISODES = {
        "Lower extremity joint replacement": {"volume": 150, "baseline_cost": 26_500},
        "Hip/femur fracture": {"volume": 80, "baseline_cost": 29_500},
        "Spinal fusion": {"volume": 40, "baseline_cost": 42_000},
        "Coronary artery bypass graft": {"volume": 30, "baseline_cost": 48_000},
        "Major bowel procedure": {"volume": 25, "baseline_cost": 35_000},
    }

    rows = []
    for proc, defaults in DEFAULT_EPISODES.items():
        with st.expander(proc, expanded=False):
            vol = st.number_input(
                f"Annual volume – {proc}",
                min_value=0,
                value=defaults["volume"],
                step=1,
                key=f"vol_{proc}",
            )
            base_cost = st.number_input(
                f"Baseline average cost per episode – {proc} ($)",
                min_value=0.0,
                value=float(defaults["baseline_cost"]),  # cast to float so all numeric args are same type
                step=500.0,
                key=f"base_{proc}",
            )
            reduction = st.slider(
                f"Expected % cost reduction for {proc}",
                min_value=0.0,
                max_value=30.0,
                value=5.0,
                step=0.5,
                help="Percent decrease in *total episode spend* due to initiatives such as care coordination, post‑acute network management, etc.",
                key=f"red_{proc}",
            )
            rows.append(
                {
                    "Procedure": proc,
                    "Volume": vol,
                    "Baseline cost": base_cost,
                    "Cost‑reduction %": reduction,
                }
            )

    if not rows:
        st.warning("Add at least one episode to calculate ROI.")
        st.stop()

    # -------------------------
    # Dataframe & calculations
    # -------------------------

    df = pd.DataFrame(rows)

    df["Target price"] = df["Baseline cost"] * (1 - discount_pct / 100)
    df["Expected cost"] = df["Baseline cost"] * (1 - df["Cost‑reduction %"] / 100)
    df["Reconciliation $/episode"] = df["Target price"] - df["Expected cost"]
    df["Annual reconciliation"] = df["Reconciliation $/episode"] * df["Volume"]

    df["Quality‑adjusted reconciliation"] = df["Annual reconciliation"] * (1 + quality_adj_pct / 100)

    # -------------------------
    # Results output
    # -------------------------

    st.subheader("Results")

    fmt = {
        "Baseline cost": "${:,.0f}",
        "Target price": "${:,.0f}",
        "Expected cost": "${:,.0f}",
        "Reconciliation $/episode": "${:,.0f}",
        "Annual reconciliation": "${:,.0f}",
        "Quality‑adjusted reconciliation": "${:,.0f}",
    }

    st.dataframe(df.style.format(fmt))

    total_rec = df["Quality‑adjusted reconciliation"].sum()
    net_impact = total_rec - impl_cost_total
    roi_pct = (net_impact / impl_cost_total * 100) if impl_cost_total else 0

    st.markdown(f"**Total expected annual reconciliation payment:** ${total_rec:,.0f}")
    st.markdown(f"**Annual implementation cost:** ${impl_cost_total:,.0f}")
    st.markdown(f"**Net annual impact:** ${net_impact:,.0f}")
    st.markdown(f"**Estimated ROI:** {roi_pct:,.1f}%")

    st.caption("ROI assumes upside‑only reconciliation. For Tracks 2 & 3 or post‑glide‑path years, model potential downside losses separately.")
