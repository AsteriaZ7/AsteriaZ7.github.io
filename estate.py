import pandas as pd
import json
import numpy as np

# Load the Excel file
df = pd.read_excel("Estate2.xlsx")  # Replace with your filename

# Replace NaN (Not a Number) with None (which becomes `null` in JSON) kkk
df = df.replace({np.nan: None})

# Ensure EstateNameCode is converted to string of int (e.g. 22.0 → "22")
if "EstateNameCode" in df.columns:
    df["EstateNameCode"] = df["EstateNameCode"].apply(
        lambda x: str(int(x)) if isinstance(x, (int, float)) and not pd.isna(x) else None
    )

# Convert DataFrame to list of dictionaries
data = df.to_dict(orient='records')

# Write JSON with Thai text preserved and proper nulls
with open("output.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("Clean JSON with Thai characters saved and EstateNameCode standardized.")
