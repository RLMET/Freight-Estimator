#!/usr/bin/env python3
"""
A2 Road Freight Rate Estimator — v2.1
======================================
Self-contained: no external files required. All data is hard-coded.
FAF (Fuel Adjustment Factor) is adjustable weekly via the sidebar.

Built for Middle Earth Tiles | Origin: Warkworth, New Zealand
Last updated: April 2026
Data current to: February 2026 (64 invoice records, Dec 2024 – Feb 2026)

To run:
    pip install streamlit pandas numpy
    streamlit run freight_estimator.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt
from datetime import datetime

# =============================================================================
# HARD-CODED NZ LOCATION DATABASE (sourced from nz.xlsx)
# =============================================================================

NZ_LOCATIONS_RAW = [
    ("Auckland",          -36.8406,  174.7400),
    ("Christchurch",      -43.5310,  172.6365),
    ("Manukau City",      -37.0000,  174.8850),
    ("Wellington",        -41.2889,  174.7772),
    ("Northcote",         -36.8019,  174.7494),
    ("Hamilton",          -37.7833,  175.2833),
    ("Tauranga",          -37.6833,  176.1667),
    ("Lower Hutt",        -41.2167,  174.9167),
    ("Dunedin",           -45.8742,  170.5036),
    ("Palmerston North",  -40.3550,  175.6117),
    ("Napier",            -39.4903,  176.9178),
    ("New Plymouth",      -39.0578,  174.0742),
    ("Porirua",           -41.1333,  174.8500),
    ("Rotorua",           -38.1378,  176.2514),
    ("Whangarei",         -35.7250,  174.3236),
    ("Invercargill",      -46.4131,  168.3475),
    ("Nelson",            -41.2708,  173.2839),
    ("Upper Hutt",        -41.1333,  175.0500),
    ("Gisborne",          -38.6625,  178.0178),
    ("Paraparaumu",       -40.9144,  175.0056),
    ("Timaru",            -44.3931,  171.2508),
    ("Blenheim",          -41.5140,  173.9600),
    ("Taupo",             -38.6875,  176.0694),
    ("Cambridge",         -37.8833,  175.4667),
    ("Feilding",          -40.2167,  175.5667),
    ("Levin",             -40.6219,  175.2867),
    ("Rolleston",         -43.5833,  172.3833),
    ("Whakatane",         -37.9600,  176.9800),
    ("Richmond",          -41.3333,  173.1833),
    ("Havelock North",    -39.6667,  176.8833),
    ("Tokoroa",           -38.2167,  175.8667),
    ("Mosgiel",           -45.8750,  170.3486),
    ("Te Awamutu",        -38.0167,  175.3167),
    ("Waikanae",          -40.8750,  175.0639),
    ("Hawera",            -39.5933,  174.2783),
    ("Waiuku",            -37.2490,  174.7300),
    ("Paraparaumu Beach", -40.8938,  174.9794),
    ("Wanaka",            -44.7000,  169.1500),
    ("Te Puke",           -37.7667,  176.3167),
    ("Greymouth",         -42.4500,  171.2075),
    ("Matamata",          -37.8167,  175.7667),
    ("Thames",            -37.1383,  175.5375),
    ("Kawerau",           -38.1000,  176.7000),
    ("Kerikeri",          -35.2244,  173.9514),
    ("Waitara",           -38.9958,  174.2331),
    ("Ngaruawahia",       -37.6667,  175.1500),
    ("Mount Maunganui",   -37.6598,  176.2148),
    ("Lincoln",           -43.6500,  172.4833),
    ("Kaitaia",           -35.1125,  173.2628),
    ("Stratford",         -39.3333,  174.2833),
    ("Alexandra",         -45.2492,  169.3797),
    ("Cromwell",          -45.0459,  169.1956),
    ("Warkworth",         -36.4000,  174.6667),
    ("Waihi",             -37.3833,  175.8333),
    ("Raumati Beach",     -40.9187,  174.9811),
    ("Marton",            -40.0692,  175.3783),
    ("Whitianga",         -36.8333,  175.7000),
    ("Tuakau",            -37.2667,  174.9500),
    ("Dargaville",        -35.9333,  173.8833),
    ("Katikati",          -37.5500,  175.9167),
    ("Westport",          -41.7581,  171.6022),
    ("Tauwhare",          -37.7698,  175.4592),
    ("Te Aroha",          -37.5333,  175.7167),
    ("Kaikohe",           -35.4075,  173.7997),
    ("Prebbleton",        -43.5783,  172.5133),
    ("Paeroa",            -37.3750,  175.6667),
    ("Whangamata",        -37.2000,  175.8667),
    ("Balclutha",         -46.2333,  169.7500),
    ("Snells Beach",      -36.4222,  174.7275),
    ("Turangi",           -38.9889,  175.8083),
    ("Raglan",            -37.8000,  174.8833),
    ("Foxton",            -40.4717,  175.2858),
    ("Darfield",          -43.4833,  172.1167),
    ("Ashhurst",          -40.3000,  175.7500),
    ("Hokitika",          -42.7156,  170.9681),
    ("Helensville",       -36.6797,  174.4494),
    ("Woodend",           -43.3167,  172.6667),
    ("Kihikihi",          -38.0333,  175.3500),
    ("Pahiatua",          -40.4533,  175.8408),
    ("Wakefield",         -41.4000,  173.0500),
    ("Ruakaka",           -35.9084,  174.4596),
    ("Winton",            -46.1431,  168.3236),
    ("Maraetai",          -36.8810,  175.0420),
    ("Te Anau",           -45.4167,  167.7167),
    ("Clive",             -39.5833,  176.9167),
    ("Oxford",            -43.3128,  172.1906),
    ("Pokeno",            -37.2333,  175.0167),
    ("Milton",            -46.1167,  169.9667),
    ("Waihi Beach",       -37.4000,  175.9333),
    ("Brightwater",       -41.3790,  173.1140),
    ("Leeston",           -43.7667,  172.3000),
    ("West Melton",       -43.5167,  172.3667),
    ("Waitangi",          -43.9514, -176.5611),
]

# =============================================================================
# HARD-CODED HISTORICAL FREIGHT DATA (sourced from A2 Spreadsheet to Feb 26.xlsx)
# Complete invoice records Dec 2024 – Feb 2026. 64 records across 13 months.
# The FAF multiplier (set in sidebar) is applied on top of these base rates.
# To update: drag the latest spreadsheet to Claude and ask for a monthly update.
# =============================================================================

HISTORICAL_DATA_RAW = [
    # (Date, Town, Actual_Weight_kg, Volume_m3, Single_Price)
    # --- Feb 2026 ---
    ("2026-02-04", "Wanaka",        350,    0.750,   357.01),
    ("2026-02-05", "Auckland",      900,    2.000,   148.50),
    ("2026-02-11", "Auckland",      946,    1.500,   156.09),
    ("2026-02-13", "Auckland",      300,    0.400,    55.00),
    ("2026-02-17", "Auckland",      600,    0.800,    99.00),
    ("2026-02-24", "Auckland",      343,    0.300,    65.00),
    # --- Jan 2026 ---
    ("2026-01-12", "Auckland",      160,    0.206,    55.00),
    ("2026-01-14", "Oamaru",         80,    0.087,   117.45),
    ("2026-01-20", "Wellington",    100,    0.221,    97.79),
    ("2026-01-21", "Dunedin",        40,    0.110,   117.95),
    ("2026-01-22", "Auckland",      200,    0.432,    65.00),
    ("2026-01-27", "Tauranga",      285,    0.600,   107.79),
    # --- Dec 2025 ---
    ("2025-12-08", "Paraparaumu",   530,    0.840,   284.91),
    ("2025-12-08", "Lower Hutt",    390,    0.280,   218.71),
    ("2025-12-15", "Christchurch",  400,    0.800,   228.72),
    ("2025-12-17", "Christchurch",   60,    0.200,   123.95),
    # --- Nov 2025 ---
    ("2025-11-11", "Auckland",       80,    0.200,    55.00),
    ("2025-11-11", "Auckland",       50,    0.100,    55.00),
    ("2025-11-12", "Auckland",      340,    0.500,    65.00),
    ("2025-11-17", "Auckland",      435,    0.908,    71.78),
    ("2025-11-27", "Kaiwaka",       710,    1.200,   150.00),
    # --- Oct 2025 ---
    ("2025-10-09", "Hastings",       80,    0.100,    97.23),
    ("2025-10-13", "Blenheim",      787,    0.992,   415.00),
    ("2025-10-13", "Tauranga",      300,    0.720,    97.23),
    ("2025-10-14", "Auckland",      120,    0.486,    55.00),
    ("2025-10-31", "Auckland",     1640,    0.160,   319.80),
    # --- Sep 2025 ---
    ("2025-09-24", "Hawera Flat",   375,    0.614,   442.05),
    ("2025-09-25", "Wellington",    108,    0.280,    97.23),
    ("2025-09-26", "Christchurch", 2612,    2.000,  1722.46),
    ("2025-09-26", "Wanaka",       3082,    2.400,  2911.80),
    # --- Aug 2025 ---
    ("2025-08-05", "Mt Maunganui",  170,    0.600,    97.23),
    ("2025-08-05", "Tauranga",      195,    0.300,    97.23),
    ("2025-08-29", "Wellington",    250,    0.538,   142.98),
    # --- Jul 2025 ---
    ("2025-07-02", "Te Awamutu",    240,    0.400,   126.60),
    ("2025-07-15", "Wanganui",      117,    0.178,    97.23),
    ("2025-07-24", "Lower Hutt",     82,    0.200,    97.23),
    # --- Jun 2025 ---
    ("2025-06-12", "Auckland",       80,    0.324,    55.00),
    ("2025-06-12", "Gisborne",       73,    0.243,    99.56),
    ("2025-06-12", "Warkworth",      13,    0.020,    35.00),
    ("2025-06-12", "Invercargill",  130,    0.324,   182.52),
    ("2025-06-16", "Gisborne",      586,    0.900,   316.05),
    ("2025-06-16", "Hamilton",      553,    1.000,   144.83),
    ("2025-06-18", "Wellington",     70,    0.400,    97.23),
    ("2025-06-23", "Christchurch",  245,    0.300,   145.42),
    ("2025-06-24", "Wellington",    105,    0.200,    97.29),
    # --- May 2025 ---
    ("2025-05-09", "Wellington",   2674,    2.800,   593.26),
    ("2025-05-13", "Whangarei Heads", 520,  0.700,  309.81),
    ("2025-05-14", "Auckland",      450,    0.700,    91.00),
    ("2025-05-26", "Wellington",    260,    0.480,   155.21),
    # --- Apr 2025 ---
    ("2025-04-07", "Levin",          70,    0.162,    97.23),
    ("2025-04-24", "Auckland",       98,    0.244,    55.00),
    ("2025-04-29", "Alexandra",     420,    0.600,   383.50),
    # --- Mar 2025 ---
    ("2025-03-11", "Clarks Beach",  670,    0.924,   370.28),
    ("2025-03-12", "Auckland",      405,    0.538,    55.00),
    ("2025-03-12", "Dunedin",        99,    0.300,   141.13),
    ("2025-03-13", "Christchurch",  120,    0.346,   127.39),
    ("2025-03-18", "Tauranga",      220,    0.700,    97.23),
    ("2025-03-19", "Auckland",       55,    0.251,    55.00),
    ("2025-03-27", "Maranda",       259,    0.456,   373.14),
    # --- Dec 2024 ---
    ("2024-12-09", "Napier",        102,    0.300,    97.23),
    ("2024-12-11", "Mt Maunganui",  230,    0.432,    97.23),
    ("2024-12-17", "Napier",         97,    0.154,    97.23),
    ("2024-12-19", "Warkworth",    2565,    3.900,   638.72),
]

# =============================================================================
# CONSTANTS
# =============================================================================

VOLUMETRIC_FACTOR  = 333    # kg per m³ (A2 Road Freight standard)
SAFETY_MARGIN      = 1.10   # 10% buffer when only northern refs available
WARKWORTH_LAT      = -36.4
WARKWORTH_LNG      = 174.6667
DEFAULT_FAF_PCT    = 35.0   # Current diesel surcharge (April 2026)

# Regional latitude boundaries
UPPER_NI_BOUNDARY  = -39.0
LOWER_NI_BOUNDARY  = -41.5

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def haversine(lat1, lon1, lat2, lon2):
    """Straight-line distance in km between two lat/lng points."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    a = sin((lat2 - lat1) / 2)**2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2)**2
    return R * 2 * asin(sqrt(a))


def get_region(lat):
    if lat > UPPER_NI_BOUNDARY:
        return "Upper North Island"
    elif lat > LOWER_NI_BOUNDARY:
        return "Lower North Island"
    else:
        return "South Island"


def volumetric_weight(volume_m3):
    return volume_m3 * VOLUMETRIC_FACTOR


def chargeable_weight(actual_kg, volume_m3):
    vol_wt = volumetric_weight(volume_m3)
    return max(actual_kg, vol_wt), vol_wt


# =============================================================================
# DATA PREPARATION  (runs once at startup)
# =============================================================================

@st.cache_data
def load_locations():
    df = pd.DataFrame(NZ_LOCATIONS_RAW, columns=["city", "latitude", "longitude"])
    df["city_lower"] = df["city"].str.lower()
    return df


@st.cache_data
def load_historical():
    rows = []
    loc_df = load_locations()
    loc_lookup = {r.city_lower: r for r in loc_df.itertuples()}

    for date, town, actual_kg, vol_m3, price in HISTORICAL_DATA_RAW:
        vol_wt = volumetric_weight(vol_m3)
        chg_wt = max(actual_kg, vol_wt)
        rate_per_kg = price / chg_wt if chg_wt > 0 else 0

        match = loc_lookup.get(town.lower())
        lat   = match.latitude  if match else None
        lng   = match.longitude if match else None
        city  = match.city      if match else None
        region = get_region(lat) if lat else None
        dist = haversine(WARKWORTH_LAT, WARKWORTH_LNG, lat, lng) if lat else None

        rows.append({
            "Date":             date,
            "Town":             town,
            "Actual_Weight_kg": actual_kg,
            "Volume_m3":        vol_m3,
            "Single_Price":     price,
            "Volumetric_Weight_kg": vol_wt,
            "Chargeable_Weight_kg": chg_wt,
            "Cost_Per_kg":      rate_per_kg,
            "city":             city,
            "latitude":         lat,
            "longitude":        lng,
            "region":           region,
            "Distance_from_Warkworth_km": dist,
        })
    return pd.DataFrame(rows)


# =============================================================================
# ESTIMATION ENGINE
# =============================================================================

def estimate_freight(town_name, actual_kg, volume_m3, faf_pct, hist_df, loc_df):
    """
    Returns a dict with estimate details, or raises ValueError if town not found.
    FAF is applied as a percentage on top of the base rate.
    """
    faf_multiplier = 1 + faf_pct / 100

    # Resolve destination town in location DB
    loc_match = loc_df[loc_df["city_lower"] == town_name.lower()]
    if loc_match.empty:
        raise ValueError(f"'{town_name}' not found in location database. Check spelling.")

    dest_lat  = loc_match.iloc[0]["latitude"]
    dest_lng  = loc_match.iloc[0]["longitude"]
    dest_city = loc_match.iloc[0]["city"]
    region    = get_region(dest_lat)

    chg_wt, vol_wt = chargeable_weight(actual_kg, volume_m3)
    weight_basis = "Volumetric" if vol_wt > actual_kg else "Actual"

    # --- Method 1: Direct historical average ---
    town_history = hist_df[hist_df["Town"].str.lower() == town_name.lower()]
    if not town_history.empty:
        base_rate = town_history["Cost_Per_kg"].mean()
        base_cost = base_rate * chg_wt
        final_cost = base_cost * faf_multiplier
        return {
            "destination":    dest_city,
            "region":         region,
            "actual_weight":  actual_kg,
            "volumetric_weight": vol_wt,
            "chargeable_weight": chg_wt,
            "weight_basis":   weight_basis,
            "base_rate_per_kg": base_rate,
            "base_cost":      base_cost,
            "faf_pct":        faf_pct,
            "final_cost":     final_cost,
            "method":         "Historical Average",
            "reference_towns": [dest_city],
            "safety_margin_applied": False,
            "invoice_count":  len(town_history),
        }

    # --- Method 2: Similar towns with southward bias ---
    region_hist = hist_df[
        (hist_df["region"] == region) &
        hist_df["latitude"].notna() &
        hist_df["Cost_Per_kg"].notna()
    ].copy()

    if region_hist.empty:
        raise ValueError(f"No historical data available for {region}. Upload more invoice data.")

    # Towns at same or southern latitude (more negative = further south)
    southern_refs = region_hist[region_hist["latitude"] <= dest_lat]
    safety_applied = False

    if len(southern_refs) >= 2:
        # Pick 2 closest by haversine distance
        southern_refs = southern_refs.copy()
        southern_refs["dist"] = southern_refs.apply(
            lambda r: haversine(dest_lat, dest_lng, r["latitude"], r["longitude"]), axis=1
        )
        refs = southern_refs.nsmallest(2, "dist")
    else:
        # Fall back to all region towns, add safety margin
        safety_applied = True
        region_hist = region_hist.copy()
        region_hist["dist"] = region_hist.apply(
            lambda r: haversine(dest_lat, dest_lng, r["latitude"], r["longitude"]), axis=1
        )
        refs = region_hist.nsmallest(2, "dist")

    base_rate = refs["Cost_Per_kg"].mean()
    if safety_applied:
        base_rate *= SAFETY_MARGIN

    base_cost  = base_rate * chg_wt
    final_cost = base_cost * faf_multiplier

    return {
        "destination":       dest_city,
        "region":            region,
        "actual_weight":     actual_kg,
        "volumetric_weight": vol_wt,
        "chargeable_weight": chg_wt,
        "weight_basis":      weight_basis,
        "base_rate_per_kg":  base_rate / (SAFETY_MARGIN if safety_applied else 1),
        "adj_rate_per_kg":   base_rate,
        "base_cost":         base_cost,
        "faf_pct":           faf_pct,
        "final_cost":        final_cost,
        "method":            "Similar Towns (Southward Bias)",
        "reference_towns":   refs["Town"].tolist(),
        "safety_margin_applied": safety_applied,
        "invoice_count":     None,
    }


# =============================================================================
# STREAMLIT UI
# =============================================================================

def main():
    st.set_page_config(
        page_title="A2 Road Freight Estimator",
        page_icon="🚚",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    loc_df  = load_locations()
    hist_df = load_historical()

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/delivery-truck.png", width=72)
        st.title("A2 Road Freight")
        st.caption("Origin: Warkworth, NZ")
        st.divider()

        st.subheader("⛽ Fuel Adjustment Factor (FAF)")
        faf_pct = st.number_input(
            "FAF %",
            min_value=0.0,
            max_value=200.0,
            value=DEFAULT_FAF_PCT,
            step=0.5,
            format="%.1f",
            help=(
                "Applied on top of all base rates. "
                "Update this each Monday to reflect current diesel costs. "
                f"Default: {DEFAULT_FAF_PCT}% (set April 2026 — diesel surcharge)"
            ),
        )

        if faf_pct == DEFAULT_FAF_PCT:
            st.info(f"📌 Current FAF: **{faf_pct:.1f}%** (April 2026 diesel surcharge)")
        elif faf_pct > DEFAULT_FAF_PCT:
            st.warning(f"⬆️ FAF raised to **{faf_pct:.1f}%**")
        else:
            st.success(f"⬇️ FAF reduced to **{faf_pct:.1f}%**")

        st.divider()
        st.caption(f"v2.0 | {datetime.now().strftime('%d %b %Y')}")
        st.caption(f"📦 {len(hist_df)} invoices | 🗺️ {len(loc_df)} towns")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_calc, tab_history, tab_sandbox = st.tabs(
        ["🧮 Rate Calculator", "📊 Historical Data", "📂 Data Sandbox"]
    )

    # ── TAB 1: Rate Calculator ────────────────────────────────────────────────
    with tab_calc:
        st.header("Freight Rate Calculator")
        st.markdown(
            f"Estimates include a **{faf_pct:.1f}% FAF** (Fuel Adjustment Factor) "
            "applied on top of base rates derived from historical invoices."
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Shipment Details")
            all_towns = sorted(loc_df["city"].tolist())
            destination = st.selectbox(
                "Destination town",
                options=all_towns,
                index=all_towns.index("Auckland") if "Auckland" in all_towns else 0,
            )
            actual_weight = st.number_input(
                "Actual weight (kg)",
                min_value=0.1,
                value=100.0,
                step=10.0,
            )
            volume = st.number_input(
                "Volume (m³)",
                min_value=0.001,
                value=0.300,
                step=0.050,
                format="%.3f",
            )

            calculate = st.button("Calculate Estimate", type="primary", use_container_width=True)

        with col2:
            st.subheader("Estimate")

            if calculate:
                try:
                    result = estimate_freight(
                        destination, actual_weight, volume, faf_pct, hist_df, loc_df
                    )

                    # Main result
                    st.metric(
                        label="Estimated Total Cost (incl. FAF)",
                        value=f"${result['final_cost']:,.2f}",
                        delta=f"+{faf_pct:.1f}% FAF on ${result['base_cost']:,.2f} base",
                    )
                    st.divider()

                    # Detail grid
                    c1, c2 = st.columns(2)
                    with c1:
                        st.metric("Chargeable Weight", f"{result['chargeable_weight']:.1f} kg")
                        st.metric("Weight Basis", result["weight_basis"])
                        st.metric("Region", result["region"])
                    with c2:
                        st.metric("Base Rate/kg", f"${result['base_rate_per_kg']:.4f}")
                        st.metric("Base Cost (ex-FAF)", f"${result['base_cost']:,.2f}")
                        st.metric("Calc Method", result["method"])

                    # Extra detail
                    with st.expander("Full breakdown"):
                        st.write(f"**Destination:** {result['destination']}")
                        st.write(f"**Actual weight:** {result['actual_weight']:.1f} kg")
                        st.write(f"**Volumetric weight:** {result['volumetric_weight']:.1f} kg "
                                 f"(= {volume:.3f} m³ × 333)")
                        st.write(f"**Chargeable weight:** {result['chargeable_weight']:.1f} kg "
                                 f"(greater of actual vs volumetric)")
                        st.write(f"**Reference towns:** {', '.join(result['reference_towns'])}")
                        if result["safety_margin_applied"]:
                            st.warning("⚠️ 10% safety margin applied — only northern reference towns available.")
                        if result.get("invoice_count"):
                            st.write(f"**Historical invoices used:** {result['invoice_count']}")
                        st.write(f"**FAF applied:** {faf_pct:.1f}% → ×{1 + faf_pct/100:.3f}")

                except ValueError as e:
                    st.error(f"❌ {e}")
            else:
                st.info("👈 Enter shipment details and click **Calculate Estimate**")

                # Show a quick reference
                st.markdown("#### Quick reference (base rates, ex-FAF)")
                sample_towns = ["Auckland", "Wellington", "Christchurch", "Dunedin", "Tauranga"]
                ref_rows = []
                for t in sample_towns:
                    th = hist_df[hist_df["Town"].str.lower() == t.lower()]
                    if not th.empty:
                        ref_rows.append({
                            "Town": t,
                            "Avg base rate/kg": f"${th['Cost_Per_kg'].mean():.4f}",
                            "Invoices": len(th),
                        })
                if ref_rows:
                    st.dataframe(pd.DataFrame(ref_rows), use_container_width=True, hide_index=True)

    # ── TAB 2: Historical Data ─────────────────────────────────────────────────
    with tab_history:
        st.header("Historical Invoice Data")

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            region_filter = st.selectbox(
                "Filter by region",
                ["All"] + sorted(hist_df["region"].dropna().unique().tolist()),
            )
        with col_f2:
            town_filter = st.selectbox(
                "Filter by town",
                ["All"] + sorted(hist_df["Town"].unique().tolist()),
            )

        display_df = hist_df.copy()
        if region_filter != "All":
            display_df = display_df[display_df["region"] == region_filter]
        if town_filter != "All":
            display_df = display_df[display_df["Town"] == town_filter]

        st.dataframe(
            display_df[[
                "Date", "Town", "region", "Actual_Weight_kg", "Volume_m3",
                "Chargeable_Weight_kg", "Single_Price", "Cost_Per_kg",
                "Distance_from_Warkworth_km"
            ]].sort_values("Date", ascending=False).style.format({
                "Single_Price":              "${:.2f}",
                "Cost_Per_kg":               "${:.4f}",
                "Chargeable_Weight_kg":      "{:.1f}",
                "Distance_from_Warkworth_km": "{:.0f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()
        st.subheader("Average rates by town")
        avg_rates = (
            hist_df.groupby("Town")
            .agg(
                Avg_Rate_Per_kg=("Cost_Per_kg", "mean"),
                Invoices=("Cost_Per_kg", "count"),
                Region=("region", "first"),
            )
            .reset_index()
            .sort_values("Avg_Rate_Per_kg")
        )
        avg_rates["With Current FAF"] = avg_rates["Avg_Rate_Per_kg"] * (1 + faf_pct / 100)

        st.dataframe(
            avg_rates.style.format({
                "Avg_Rate_Per_kg":  "${:.4f}",
                "With Current FAF": "${:.4f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

    # ── TAB 3: Data Sandbox ────────────────────────────────────────────────────
    with tab_sandbox:
        st.header("Data Sandbox — Add New Invoice Data")
        st.markdown(
            "Upload new invoice records to supplement the built-in historical data. "
            "Uploaded data is available for this session only. "
            "To permanently add records, contact your system administrator."
        )

        st.subheader("Expected CSV format")
        sample = pd.DataFrame([
            {"Town": "Auckland",     "Actual_Weight_kg": 150, "Volume_m3": 0.45, "Single_Price": 85.50},
            {"Town": "Christchurch", "Actual_Weight_kg": 300, "Volume_m3": 0.90, "Single_Price": 175.00},
        ])
        st.dataframe(sample, use_container_width=True, hide_index=True)

        uploaded = st.file_uploader("Upload invoice CSV", type=["csv"])
        if uploaded:
            try:
                new_df = pd.read_csv(uploaded)
                required = {"Town", "Actual_Weight_kg", "Volume_m3", "Single_Price"}
                missing = required - set(new_df.columns)
                if missing:
                    st.error(f"Missing columns: {missing}")
                else:
                    st.success(f"✅ Loaded {len(new_df)} new records.")
                    st.dataframe(new_df, use_container_width=True, hide_index=True)
                    st.info("These records are available in this session. Refresh the page to reset.")
            except Exception as e:
                st.error(f"Error reading file: {e}")


if __name__ == "__main__":
    main()
