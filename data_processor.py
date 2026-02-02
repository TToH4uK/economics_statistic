import pandas as pd
import os

GDP_PATH = "/home/ivanximik/.cache/kagglehub/datasets/holoong9291/gdp-of-all-countries19602020/versions/3/gdp_1960_2020.csv"
INFLATION_PATH = "/home/ivanximik/.cache/kagglehub/datasets/sazidthe1/global-inflation-data/versions/1/global_inflation_data.csv"
OUTPUT_PATH = "datasets/economic_data_1980_2020.csv"

def load_data():
    print("Loading datasets...")
    gdp_df = pd.read_csv(GDP_PATH)
    inflation_df = pd.read_csv(INFLATION_PATH)
    return gdp_df, inflation_df

def process_gdp(gdp_df):
    print("Processing GDP data...")
    # Filter years 1980-2020
    gdp_df = gdp_df[(gdp_df['year'] >= 1980) & (gdp_df['year'] <= 2020)].copy()
    
    # Rename columns for consistency
    gdp_df = gdp_df.rename(columns={'country': 'Country', 'year': 'Year', 'gdp': 'GDP'})
    
    # Standardize country names for GDP dataset
    # Mappings based on inspection of mismatches with Inflation dataset
    gdp_df['Country'] = gdp_df['Country'].replace({
        'the United States': 'United States',
        'Russia': 'Russian Federation',
        'China': "China, People's Republic of",
        'Turkey': "Türkiye, Republic of",
        'South Korea': "Korea, Republic of",
        'Congo (gold)': "Congo, Dem. Rep. of the",
        'Garner': 'Ghana',
        "C ô te d'Ivoire": "Côte d'Ivoire",
        'Congo (Brazzaville)': "Congo, Republic of ",
        'Central Africa': 'Central African Republic',
        'Gambia': 'Gambia, The',
        'Guinea Bissau': 'Guinea-Bissau',
        'Cape Verde': 'Cabo Verde',
        'Sao Tome and Principe.': 'São Tomé and Príncipe',
        'South Sultan': 'South Sudan, Republic of'
    })
    
    # Ensure GDP is numeric
    gdp_df['GDP'] = pd.to_numeric(gdp_df['GDP'], errors='coerce')
    
    # Calculate Nominal GDP Growth
    # Sort by Country and Year to ensure correct shift
    gdp_df = gdp_df.sort_values(by=['Country', 'Year'])
    gdp_df['GDP_Growth'] = gdp_df.groupby('Country')['GDP'].pct_change() * 100
    
    return gdp_df[['Country', 'Year', 'GDP', 'GDP_Growth', 'state']] # 'state' is continent

def process_inflation(inflation_df):
    print("Processing Inflation data...")
    # Melt from wide to long
    # Columns are country_name, indicator_name, 1980, 1981...
    # We drop indicator_name
    inflation_df = inflation_df.drop(columns=['indicator_name'])
    
    inflation_long = inflation_df.melt(id_vars=['country_name'], var_name='Year', value_name='Inflation')
    
    # Rename columns
    inflation_long = inflation_long.rename(columns={'country_name': 'Country'})
    
    # Convert Year to integer
    inflation_long['Year'] = pd.to_numeric(inflation_long['Year'], errors='coerce')
    
    # Filter years 1980-2020
    inflation_long = inflation_long[(inflation_long['Year'] >= 1980) & (inflation_long['Year'] <= 2020)]
    
    # Ensure Inflation is numeric
    inflation_long['Inflation'] = pd.to_numeric(inflation_long['Inflation'], errors='coerce')
    
    return inflation_long

import pycountry

def get_iso3(country_name):
    """Map country names to ISO-3 codes with a manual dictionary for edge cases."""
    manual_map = {
        "Russia": "RUS",
        "Russian Federation": "RUS",
        "the United States": "USA",
        "United States": "USA",
        "China": "CHN",
        "China, People's Republic of": "CHN",
        "South Korea": "KOR",
        "Korea, Republic of": "KOR",
        "Turkey": "TUR",
        "Türkiye, Republic of": "TUR",
        "Vietnam": "VNM",
        "Venezuela, Bolivarian Republic of": "VEN",
        "Iran, Islamic Republic of": "IRN",
        "Congo, Dem. Rep. of the": "COD",
        "Congo (gold)": "COD",
        "Congo, Republic of": "COG",
        "Congo (Brazzaville)": "COG",
        "Tanzania": "TZA",
        "Egypt": "EGY",
        "Syrian Arab Republic": "SYR",
        "Lao P.D.R.": "LAO",
        "Kyrgyz Republic": "KGZ",
        "Slovak Republic": "SVK",
        "Czech Republic": "CZE",
        "Bahamas, The": "BHS",
        "Gambia, The": "GMB",
        "St. Lucia": "LCA",
        "St. Vincent and the Grenadines": "VCT",
        "St. Kitts and Nevis": "KNA",
        "Bolivia": "BOL",
        "Brunei Darussalam": "BRN",
        "Trinidad and Tobago": "TTO",
        "Micronesia, Fed. States of": "FSM",
        "Cape Verde": "CPV",
        "Cabo Verde": "CPV",
        "Yemen, Republic of": "YEM"
    }
    
    if country_name in manual_map:
        return manual_map[country_name]
    
    try:
        # Search by name
        res = pycountry.countries.search_fuzzy(country_name)
        if res:
            return res[0].alpha_3
    except:
        pass
    return None

def merge_data(gdp_df, inflation_df):
    print("Merging datasets...")
    merged_df = pd.merge(gdp_df, inflation_df, on=['Country', 'Year'], how='inner')
    
    # Add ISO Codes for mapping
    print("Mapping ISO-3 codes...")
    merged_df['ISO_Code'] = merged_df['Country'].apply(get_iso3)
    
    # Log mapping failures for debugging
    failed_counts = merged_df[merged_df['ISO_Code'].isna()]['Country'].unique()
    if len(failed_counts) > 0:
        print(f"Warning: Failed to map {len(failed_counts)} countries: {failed_counts[:10]}...")

    # Calculate Real GDP Growth...
    def calculate_real_growth(row):
        nominal_growth = row['GDP_Growth']
        inflation = row['Inflation']
        if pd.isna(nominal_growth) or pd.isna(inflation): return None
        return ((1 + nominal_growth/100) / (1 + inflation/100) - 1) * 100
    
    merged_df['Real_GDP_Growth'] = merged_df.apply(calculate_real_growth, axis=1)
    
    # Determine Economic Condition...
    def get_detailed_status(row):
        inf, gdp = row['Inflation'], row['Real_GDP_Growth']
        if pd.isna(inf) or pd.isna(gdp): return "Unknown"
        if inf > 100: return "Hyperinflation"
        if inf < 0: return "Deflation"
        if inf > 5 and gdp < 1: return "Stagflation"
        if inf > 5 and gdp > 5: return "Overheating"
        if 0 <= inf <= 5 and gdp > 3: return "Healthy Growth"
        if 0 <= inf <= 5 and 0 < gdp <= 3: return "Steady Growth"
        if gdp <= 0: return "Recession"
        return "Other"

    merged_df['Economic_Condition'] = merged_df.apply(get_detailed_status, axis=1)
    return merged_df

if __name__ == "__main__":
    gdp, inflation = load_data()
    gdp_clean = process_gdp(gdp)
    inflation_clean = process_inflation(inflation)
    
    final_df = merge_data(gdp_clean, inflation_clean)
    
    # Filter only rows with ISO codes to avoid map artifacts
    final_df = final_df[final_df['ISO_Code'].notna()]
    
    print(f"Final data has {len(final_df)} rows and {len(final_df['Country'].unique())} countries.")
    final_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved to {OUTPUT_PATH}")
