import kagglehub
import os

print("Starting download script...")

try:
    # Download latest version
    print("Downloading GDP data...")
    path_gdp = kagglehub.dataset_download("holoong9291/gdp-of-all-countries19602020")
    print("Path to GDP dataset files:", path_gdp)

    # Download latest version
    print("Downloading Inflation data...")
    path_inflation = kagglehub.dataset_download("sazidthe1/global-inflation-data")
    print("Path to Inflation dataset files:", path_inflation)

except Exception as e:
    print(f"An error occurred: {e}")