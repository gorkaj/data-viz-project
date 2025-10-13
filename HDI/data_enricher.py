import pandas as pd
import numpy as np

df = pd.read_csv("HDI.csv")

years = range(1990, 2024)

for y in years:
    le_col = f"le_{y}"
    eys_col = f"eys_{y}"
    mys_col = f"mys_{y}"
    gni_col = f"gnipc_{y}"

    # Life Expectancy Index (LEI)
    df[f"life_expectancy_index_{y}"] = np.where(
        df[le_col].notna(),
        (df[le_col] - 20) / (85 - 20),
        np.nan
    )

    # Education Index (EI)
    eysi = np.where(df[eys_col].notna(), df[eys_col] / 18, np.nan)
    mysi = np.where(df[mys_col].notna(), df[mys_col] / 15, np.nan)
    df[f"education_index_{y}"] = np.where(
        (~np.isnan(eysi)) & (~np.isnan(mysi)),
        (eysi + mysi) / 2,
        np.nan
    )

    # Income Index (II)
    df[f"income_index_{y}"] = np.where(
        df[gni_col].notna(),
        (np.log(df[gni_col]) - np.log(100)) / (np.log(75000) - np.log(100)),
        np.nan
    )

# === Clip indices between 0 and 1 ===
for y in years:
    for comp in ["life_expectancy_index", "education_index", "income_index"]:
        col = df[f"{comp}_{y}"]
        if ((col < 0) | (col > 1)).any():
            print(f"Warning: {comp}_{y} out of bounds")

df.to_csv("hdi_processed.csv", index=False)

