import pandas as pd

# === INPUT FILES ===
# Your main spreadsheet (the one to merge into)
main_file = "hdi_processed.csv"         # or "your_data.xlsx"
# The subregion file we created earlier
subregion_file = "iso3_to_un_subregion.csv"
# Output merged file
output_file = "merged_with_subregion.csv"

# === READ FILES ===
df_main = pd.read_csv(main_file)

df_sub = pd.read_csv(subregion_file)

# === MERGE ON iso3 CODE ===
merged = df_main.merge(df_sub, on="iso3", how="left")

# === SAVE RESULT ===
merged.to_csv(output_file, index=False)

print("✅ Merged file saved as:", output_file)
print("Columns added:", [c for c in merged.columns if c not in df_main.columns])
