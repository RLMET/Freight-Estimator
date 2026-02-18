[Uploading README.md…]()
# A2 Road Freight Rate Estimator

A Streamlit-based freight rate estimation tool for A2 Road Freight, originating from Warkworth, New Zealand.

## Features

- **Volumetric Weight Calculation**: Automatically calculates volumetric weight using the 1m³ = 333kg conversion
- **"Greater Of" Logic**: Uses the higher value between actual weight and volumetric weight
- **Regional Categorization**: Classifies destinations into Upper North Island, Lower North Island, and South Island based on latitude
- **Southward Bias Estimation**: Prevents undercharging by preferring reference towns at equal or southern latitudes
- **Safety Margin**: Applies 10% buffer when only northern reference towns are available
- **Multi-User Access**: Web-based interface for simultaneous use by multiple team members

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install Dependencies

```bash
pip install streamlit pandas openpyxl numpy
```

## Running the Application

### Local Development

```bash
cd "/path/to/A2 Road Freight Model Data For Claude"
streamlit run freight_estimator.py
```

The app will open in your default browser at `http://localhost:8501`

### Deployment (for multi-user access)

For production use with multiple users, deploy to Streamlit Cloud:

1. Create a GitHub repository with these files:
   - `freight_estimator.py`
   - `nz.xlsx`
   - `requirements.txt` (see below)

2. Visit [share.streamlit.io](https://share.streamlit.io)

3. Connect your GitHub repository

4. Deploy the app

**requirements.txt:**
```
streamlit>=1.28.0
pandas>=2.0.0
openpyxl>=3.1.0
numpy>=1.24.0
```

## How to Use

### 1. Upload Historical Invoice Data (First Time Setup)

1. Navigate to the **"Data Sandbox"** tab
2. Prepare your invoice CSV with these columns:
   - `Town`: Destination town name
   - `Actual_Weight_kg`: Actual weight in kilograms
   - `Volume_m3`: Volume in cubic meters
   - `Single_Price`: Total all-inclusive delivery price
3. Upload the CSV file
4. Click **"Process and Save Data"**

**Example CSV format:**
```csv
Town,Actual_Weight_kg,Volume_m3,Single_Price
Auckland,150,0.45,85.50
Christchurch,300,0.90,175.00
Hamilton,200,0.60,95.00
```

A sample template (`sample_invoice_template.csv`) is provided in this folder.

### 2. Calculate Freight Estimates

1. Go to the **"Rate Calculator"** tab
2. Select destination town from dropdown
3. Enter actual weight (kg)
4. Enter volume (m³)
5. Click **"Calculate Estimate"**

The tool will display:
- Estimated total cost
- Chargeable weight (greater of actual or volumetric)
- Rate per kg
- Calculation method used
- Reference towns (if applicable)
- Whether safety margin was applied

### 3. View Historical Data

Use the **"Historical Data"** tab to:
- Browse all processed invoices
- Filter by region or town
- See average rates by destination
- Identify pricing trends

### 4. Monthly Updates

To update the database with new invoices:
1. Export your monthly invoices to CSV format
2. Go to **"Data Sandbox"** tab
3. Upload the new CSV file
4. The system will append the new data to existing records

## Calculation Logic

### The "Greater Of" Rule

For every delivery:
```
Volumetric Weight = Volume (m³) × 333 kg/m³
Chargeable Weight = MAX(Actual Weight, Volumetric Weight)
```

### Regional Categories (by Latitude)

- **Upper North Island**: Latitude > -39.0°
- **Lower North Island**: -41.5° < Latitude ≤ -39.0°
- **South Island**: Latitude ≤ -41.5°

### Estimation Methods

**Method 1: Historical Average**
- If the destination town exists in your historical data
- Uses the average rate/kg from all previous deliveries to that town

**Method 2: Similar Towns with Southward Bias**
- If the destination is new (no historical data)
- Finds the 2 closest towns that are:
  - In the same region
  - At the same latitude OR south (more negative) of the destination
- Averages their rates to estimate

**Safety Margin (10%)**
- Applied when only northern towns are available as references
- Prevents undercharging for longer distances from Warkworth

### Cost Formula

```
Estimated Cost = Rate per kg × Chargeable Weight
```

## File Structure

```
A2 Road Freight Model Data For Claude/
├── freight_estimator.py              # Main Streamlit application
├── nz.xlsx                           # NZ location database (city, lat, lng)
├── sample_invoice_template.csv       # Example invoice format
├── historical_freight_data.csv       # Auto-generated from uploads
└── README.md                         # This file
```

## Troubleshooting

### "Town not found in location database"
- Check spelling of town name
- Ensure town exists in `nz.xlsx`
- Town names are case-insensitive but must match exactly

### "No historical data found for region"
- Upload more invoice data covering that region
- The tool needs at least one historical record in the region

### Data not saving
- Check file permissions in the directory
- Ensure you have write access to create `historical_freight_data.csv`

### App won't start
- Verify all dependencies are installed: `pip list`
- Check Python version: `python --version` (must be 3.8+)
- Ensure `nz.xlsx` is in the same directory as `freight_estimator.py`

## Support & Feedback

For technical issues or feature requests, contact your system administrator.

## Version History

- **v1.0** (February 2026) - Initial release
  - Core estimation engine
  - Southward bias logic
  - Data sandbox for CSV uploads
  - Multi-user Streamlit interface

---

**Built for A2 Road Freight | Origin: Warkworth, New Zealand**
