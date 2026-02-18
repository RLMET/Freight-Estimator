"""
A2 Road Freight Rate Estimator - Warkworth Origin
Streamlit application for estimating freight costs based on historical invoices
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os
from math import radians, cos, sin, asin, sqrt

# ============================================================================
# CONFIGURATION
# ============================================================================

VOLUMETRIC_CONVERSION = 333  # 1m³ = 333kg
WARKWORTH_LAT = -36.4000  # Warkworth latitude
WARKWORTH_LNG = 174.6667  # Warkworth longitude

# Regional latitude boundaries
UPPER_NORTH_THRESHOLD = -39.0
LOWER_NORTH_THRESHOLD = -41.5

SAFETY_MARGIN = 1.10  # 10% safety buffer for northern towns

# File paths
LOCATION_DATA_PATH = "nz.xlsx"
HISTORICAL_DATA_PATH = "historical_freight_data.csv"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    Returns distance in kilometers
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

def calculate_volumetric_weight(volume_m3):
    """Calculate volumetric weight: 1m³ = 333kg"""
    return volume_m3 * VOLUMETRIC_CONVERSION

def calculate_chargeable_weight(actual_weight, volume_m3):
    """Return the greater of actual weight or volumetric weight"""
    volumetric = calculate_volumetric_weight(volume_m3)
    return max(actual_weight, volumetric)

def categorize_region(latitude):
    """
    Categorize destination by latitude:
    - Upper North Island: lat > -39.0
    - Lower North Island: -41.5 < lat <= -39.0
    - South Island: lat <= -41.5
    """
    if latitude > UPPER_NORTH_THRESHOLD:
        return "Upper North Island"
    elif latitude > LOWER_NORTH_THRESHOLD:
        return "Lower North Island"
    else:
        return "South Island"

def load_location_data():
    """Load NZ location data with coordinates"""
    try:
        df = pd.read_excel(LOCATION_DATA_PATH)
        # Normalize column names
        df.columns = ['city', 'latitude', 'longitude']
        df['city'] = df['city'].str.strip().str.title()
        df['region'] = df['latitude'].apply(categorize_region)
        return df
    except Exception as e:
        st.error(f"Error loading location data: {e}")
        return pd.DataFrame()

def load_historical_data():
    """Load historical freight invoice data"""
    if os.path.exists(HISTORICAL_DATA_PATH):
        try:
            df = pd.read_csv(HISTORICAL_DATA_PATH)
            return df
        except Exception as e:
            st.error(f"Error loading historical data: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def save_historical_data(df):
    """Save historical freight data to CSV"""
    try:
        df.to_csv(HISTORICAL_DATA_PATH, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

def process_invoice_data(invoice_df, location_df):
    """
    Process raw invoice data:
    1. Calculate volumetric weight
    2. Determine chargeable weight (greater of actual or volumetric)
    3. Calculate cost per unit (Single Price / Chargeable Weight)
    4. Match with location data to get coordinates and region
    """
    processed = invoice_df.copy()

    # Normalize town names
    processed['Town'] = processed['Town'].str.strip().str.title()

    # Clean Single_Price - remove $ signs and convert to float
    if processed['Single_Price'].dtype == object:
        processed['Single_Price'] = processed['Single_Price'].str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype(float)

    # Calculate volumetric weight
    processed['Volumetric_Weight_kg'] = processed['Volume_m3'] * VOLUMETRIC_CONVERSION

    # Calculate chargeable weight (greater of)
    processed['Chargeable_Weight_kg'] = processed[['Actual_Weight_kg', 'Volumetric_Weight_kg']].max(axis=1)

    # Calculate cost per kg
    processed['Cost_Per_kg'] = processed['Single_Price'] / processed['Chargeable_Weight_kg']

    # Merge with location data
    processed = processed.merge(
        location_df[['city', 'latitude', 'longitude', 'region']],
        left_on='Town',
        right_on='city',
        how='left'
    )

    # Calculate distance from Warkworth
    processed['Distance_from_Warkworth_km'] = processed.apply(
        lambda row: haversine_distance(WARKWORTH_LAT, WARKWORTH_LNG, row['latitude'], row['longitude'])
        if pd.notna(row['latitude']) else np.nan,
        axis=1
    )

    return processed

def find_similar_towns(target_town, target_lat, target_region, historical_df, n=2):
    """
    Find similar towns for rate estimation using "southward bias":
    1. Same region
    2. Equal or south of (more negative latitude than) target town
    3. Return the n closest towns by geographic distance
    """
    # Filter to same region
    same_region = historical_df[historical_df['region'] == target_region].copy()

    if same_region.empty:
        return pd.DataFrame(), False

    # Filter to towns at or south of target (more negative latitude)
    southward = same_region[same_region['latitude'] <= target_lat].copy()

    # Check if we found southward towns
    found_southward = not southward.empty

    # If no southward towns, use all towns in region (will apply safety margin)
    search_df = southward if found_southward else same_region

    # Calculate distance from target
    search_df = search_df.copy()
    search_df['distance_to_target'] = search_df.apply(
        lambda row: haversine_distance(target_lat, row['longitude'], row['latitude'], row['longitude'])
        if pd.notna(row['latitude']) else np.nan,
        axis=1
    )

    # Get n closest towns
    closest = search_df.nsmallest(n, 'distance_to_target')

    return closest, found_southward

def estimate_freight_cost(town_name, actual_weight, volume_m3, location_df, historical_df):
    """
    Estimate freight cost for a new delivery:
    1. Check if town exists in history -> use average historical rate
    2. If new town -> find 2 closest towns with southward bias
    3. Apply 10% safety margin if only northern towns available
    """
    town_name = town_name.strip().title()

    # Calculate chargeable weight
    chargeable_weight = calculate_chargeable_weight(actual_weight, volume_m3)
    volumetric_weight = calculate_volumetric_weight(volume_m3)

    # Get town coordinates
    town_info = location_df[location_df['city'] == town_name]

    if town_info.empty:
        return {
            'error': f"Town '{town_name}' not found in location database",
            'chargeable_weight': chargeable_weight,
            'volumetric_weight': volumetric_weight
        }

    target_lat = town_info.iloc[0]['latitude']
    target_lng = town_info.iloc[0]['longitude']
    target_region = town_info.iloc[0]['region']

    # Check if town exists in historical data
    historical_town = historical_df[historical_df['Town'] == town_name]

    if not historical_town.empty:
        # Use average historical rate for this town
        avg_rate = historical_town['Cost_Per_kg'].mean()
        estimated_cost = avg_rate * chargeable_weight

        return {
            'success': True,
            'town': town_name,
            'region': target_region,
            'latitude': target_lat,
            'actual_weight': actual_weight,
            'volume_m3': volume_m3,
            'volumetric_weight': volumetric_weight,
            'chargeable_weight': chargeable_weight,
            'rate_per_kg': avg_rate,
            'estimated_cost': estimated_cost,
            'method': 'Historical Average',
            'reference_towns': [town_name],
            'safety_margin_applied': False,
            'num_historical_records': len(historical_town)
        }

    # Town is new - find similar towns with southward bias
    similar_towns, found_southward = find_similar_towns(
        town_name, target_lat, target_region, historical_df, n=2
    )

    if similar_towns.empty:
        return {
            'error': f"No historical data found for region '{target_region}'",
            'chargeable_weight': chargeable_weight,
            'volumetric_weight': volumetric_weight,
            'region': target_region
        }

    # Calculate average rate from similar towns
    avg_rate = similar_towns['Cost_Per_kg'].mean()

    # Apply safety margin if only northern towns were available
    if not found_southward:
        avg_rate = avg_rate * SAFETY_MARGIN

    estimated_cost = avg_rate * chargeable_weight

    return {
        'success': True,
        'town': town_name,
        'region': target_region,
        'latitude': target_lat,
        'actual_weight': actual_weight,
        'volume_m3': volume_m3,
        'volumetric_weight': volumetric_weight,
        'chargeable_weight': chargeable_weight,
        'rate_per_kg': avg_rate,
        'estimated_cost': estimated_cost,
        'method': 'Similar Towns Estimate',
        'reference_towns': similar_towns['Town'].tolist(),
        'safety_margin_applied': not found_southward,
        'southward_bias_used': found_southward
    }

# ============================================================================
# STREAMLIT APP
# ============================================================================

def main():
    st.set_page_config(
        page_title="A2 Road Freight Estimator",
        page_icon="🚚",
        layout="wide"
    )

    st.title("🚚 A2 Road Freight Rate Estimator")
    st.markdown("**Origin Hub: Warkworth, New Zealand**")
    st.markdown("---")

    # Load data
    location_df = load_location_data()
    historical_df = load_historical_data()

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Rate Calculator",
        "📤 Data Sandbox",
        "📈 Historical Data",
        "ℹ️ How It Works"
    ])

    # ========================================================================
    # TAB 1: RATE CALCULATOR
    # ========================================================================
    with tab1:
        st.header("Freight Rate Calculator")

        if historical_df.empty:
            st.warning("⚠️ No historical data loaded. Please upload invoice data in the 'Data Sandbox' tab.")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Delivery Details")

            # Town selection
            if not location_df.empty:
                town_options = sorted(location_df['city'].unique())
                selected_town = st.selectbox("Destination Town", town_options)
            else:
                selected_town = st.text_input("Destination Town")

            actual_weight = st.number_input(
                "Actual Weight (kg)",
                min_value=0.0,
                value=100.0,
                step=1.0
            )

            volume_m3 = st.number_input(
                "Volume (m³)",
                min_value=0.0,
                value=0.5,
                step=0.01,
                format="%.2f"
            )

            calculate_btn = st.button("Calculate Estimate", type="primary", use_container_width=True)

        with col2:
            st.subheader("Estimation Result")

            if calculate_btn:
                if historical_df.empty:
                    st.error("Cannot calculate estimate without historical data. Please upload invoice data first.")
                else:
                    result = estimate_freight_cost(
                        selected_town,
                        actual_weight,
                        volume_m3,
                        location_df,
                        historical_df
                    )

                    if 'error' in result:
                        st.error(result['error'])
                        st.info(f"**Chargeable Weight:** {result['chargeable_weight']:.2f} kg")
                    else:
                        # Display results
                        st.success(f"**Estimated Total Cost: ${result['estimated_cost']:.2f}**")

                        st.markdown("---")

                        # Details
                        st.markdown("**Weight Analysis:**")
                        st.write(f"- Actual Weight: {result['actual_weight']:.2f} kg")
                        st.write(f"- Volumetric Weight: {result['volumetric_weight']:.2f} kg (at 1m³ = 333kg)")
                        st.write(f"- **Chargeable Weight: {result['chargeable_weight']:.2f} kg** (greater of the two)")

                        st.markdown("**Location:**")
                        st.write(f"- Region: {result['region']}")
                        st.write(f"- Latitude: {result['latitude']:.4f}")

                        st.markdown("**Rate Calculation:**")
                        st.write(f"- Rate per kg: ${result['rate_per_kg']:.4f}")
                        st.write(f"- Method: {result['method']}")

                        if result['method'] == 'Similar Towns Estimate':
                            st.write(f"- Reference Towns: {', '.join(result['reference_towns'])}")
                            if result['safety_margin_applied']:
                                st.warning("⚠️ **10% Safety Margin Applied** - No southward towns available in region")
                            else:
                                st.info("✓ Southward bias applied (reference towns are south of destination)")
                        else:
                            st.write(f"- Historical Records: {result['num_historical_records']}")

    # ========================================================================
    # TAB 2: DATA SANDBOX
    # ========================================================================
    with tab2:
        st.header("Data Sandbox - Upload Historical Invoices")

        st.markdown("""
        Upload a CSV file containing historical freight invoices. The file must have these columns:
        - **Town**: Destination town name
        - **Actual_Weight_kg**: Actual weight in kilograms
        - **Volume_m3**: Volume in cubic meters
        - **Single_Price**: Total all-inclusive price for the delivery
        """)

        uploaded_file = st.file_uploader("Upload Invoice CSV", type=['csv'])

        if uploaded_file is not None:
            try:
                # Read uploaded file
                new_data = pd.read_csv(uploaded_file)

                st.subheader("Preview of Uploaded Data")
                st.dataframe(new_data.head(10))

                # Validate required columns
                required_cols = ['Town', 'Actual_Weight_kg', 'Volume_m3', 'Single_Price']
                missing_cols = [col for col in required_cols if col not in new_data.columns]

                if missing_cols:
                    st.error(f"Missing required columns: {', '.join(missing_cols)}")
                else:
                    st.success("✓ All required columns present")

                    # Process the data
                    if st.button("Process and Save Data", type="primary"):
                        with st.spinner("Processing invoice data..."):
                            processed = process_invoice_data(new_data, location_df)

                            # Show processing results
                            st.subheader("Processed Data Preview")
                            display_cols = [
                                'Town', 'region', 'Actual_Weight_kg', 'Volume_m3',
                                'Volumetric_Weight_kg', 'Chargeable_Weight_kg',
                                'Single_Price', 'Cost_Per_kg', 'Distance_from_Warkworth_km'
                            ]
                            st.dataframe(processed[display_cols].head(10))

                            # Save to file
                            if save_historical_data(processed):
                                st.success("✓ Data saved successfully! You can now use the Rate Calculator.")
                                st.rerun()
                            else:
                                st.error("Failed to save data")

            except Exception as e:
                st.error(f"Error processing file: {e}")

        # Show current data status
        st.markdown("---")
        st.subheader("Current Data Status")

        if not historical_df.empty:
            st.info(f"📊 **{len(historical_df)} historical records loaded**")

            # Summary statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Unique Towns", historical_df['Town'].nunique())
            with col2:
                st.metric("Avg Cost/kg", f"${historical_df['Cost_Per_kg'].mean():.4f}")
            with col3:
                st.metric("Total Deliveries", len(historical_df))

            # Clear data button
            if st.button("Clear All Historical Data", type="secondary"):
                if os.path.exists(HISTORICAL_DATA_PATH):
                    os.remove(HISTORICAL_DATA_PATH)
                    st.success("Historical data cleared")
                    st.rerun()
        else:
            st.warning("No historical data loaded yet")

    # ========================================================================
    # TAB 3: HISTORICAL DATA VIEW
    # ========================================================================
    with tab3:
        st.header("Historical Freight Data")

        if not historical_df.empty:
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                region_filter = st.multiselect(
                    "Filter by Region",
                    options=historical_df['region'].unique(),
                    default=historical_df['region'].unique()
                )

            with col2:
                town_filter = st.multiselect(
                    "Filter by Town",
                    options=sorted(historical_df['Town'].unique())
                )

            # Apply filters
            filtered_df = historical_df.copy()
            if region_filter:
                filtered_df = filtered_df[filtered_df['region'].isin(region_filter)]
            if town_filter:
                filtered_df = filtered_df[filtered_df['Town'].isin(town_filter)]

            # Display data
            st.dataframe(
                filtered_df[[
                    'Town', 'region', 'latitude', 'Actual_Weight_kg',
                    'Volume_m3', 'Chargeable_Weight_kg', 'Single_Price',
                    'Cost_Per_kg', 'Distance_from_Warkworth_km'
                ]],
                height=400
            )

            # Summary by town
            st.subheader("Average Rates by Town")
            town_summary = filtered_df.groupby('Town').agg({
                'Cost_Per_kg': ['mean', 'min', 'max', 'count'],
                'region': 'first'
            }).round(4)
            town_summary.columns = ['Avg Rate/kg', 'Min Rate/kg', 'Max Rate/kg', 'Count', 'Region']
            st.dataframe(town_summary.sort_values('Avg Rate/kg', ascending=False))

        else:
            st.info("No historical data available. Upload data in the 'Data Sandbox' tab.")

    # ========================================================================
    # TAB 4: HOW IT WORKS
    # ========================================================================
    with tab4:
        st.header("How the Estimator Works")

        st.markdown("""
        ### 1. The "Greater Of" Rule

        For every delivery, we calculate:
        - **Volumetric Weight** = Volume (m³) × 333 kg/m³
        - **Chargeable Weight** = Maximum of (Actual Weight, Volumetric Weight)

        This ensures you're charged fairly whether cargo is heavy or bulky.

        ### 2. Regional Categorization

        Destinations are categorized by latitude:
        - **Upper North Island**: Latitude > -39.0° (e.g., Auckland, Hamilton)
        - **Lower North Island**: -41.5° < Latitude ≤ -39.0° (e.g., Wellington, Palmerston North)
        - **South Island**: Latitude ≤ -41.5° (e.g., Christchurch, Dunedin)

        ### 3. Estimation Logic

        **When estimating costs for a new town:**

        1. **Check History First**: If we have historical data for that exact town, we use the average historical rate.

        2. **Southward Bias Search**: If the town is new:
           - Search for the 2 closest towns in the **same region**
           - These towns must be at the **same latitude or south** (more negative) of the destination
           - This prevents undercharging since freight typically costs more for longer distances from Warkworth

        3. **Safety Buffer**: If only northern towns are available:
           - Calculate the average rate from available towns
           - Apply a **10% safety margin** to account for the extra distance

        ### 4. Cost Calculation

        **Estimated Total Cost** = Rate per kg × Chargeable Weight

        ### 5. Data Updates

        Use the **Data Sandbox** tab to upload new CSV invoices monthly. The system will:
        - Process the invoices automatically
        - Calculate all weights and rates
        - Update the historical database
        - Improve estimation accuracy over time
        """)

        st.markdown("---")
        st.markdown("**Origin Hub:** Warkworth (-36.4000°, 174.6667°)")
        st.markdown("**Built for:** A2 Road Freight")

if __name__ == "__main__":
    main()
