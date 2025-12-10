import pandas as pd
import numpy as np

def load_data():
    return pd.read_csv("hdi_processed.csv")


df = load_data()

def detect_sudden_changes(df, attribute_prefix, threshold_abs=None, threshold_pct=None):
    """
    Detects sudden year-to-year changes for a given attribute.
    
    Parameters:
        df : DataFrame with country rows and columns like attr_1990, attr_1991, ...
        attribute_prefix : e.g. "le", "eys", "mys", "gnipc", "hdi"
        threshold_abs : absolute jump threshold (e.g., 5 for LE, 2000 for GNIPC)
        threshold_pct : percentage change threshold (e.g., 0.2 = 20%)
    
    Returns:
        A DataFrame of anomalies with:
        - country
        - year_from -> year_to
        - value_before
        - value_after
        - abs_change
        - pct_change
    """

    # Find all years for this attribute
    cols = [c for c in df.columns if c.startswith(attribute_prefix + "_")]
    years = sorted(int(c.split("_")[1]) for c in cols)
    
    anomalies = []

    for _, row in df.iterrows():
        country = row["country"]
        
        for i in range(len(years) - 1):
            y1, y2 = years[i], years[i+1]
            v1, v2 = row[f"{attribute_prefix}_{y1}"], row[f"{attribute_prefix}_{y2}"]

            # Skip missing values
            if pd.isna(v1) or pd.isna(v2):
                continue
            
            abs_change = abs(v2 - v1)
            pct_change = abs_change / v1 if v1 != 0 else np.nan
            
            triggered = False
            if threshold_abs is not None and abs_change > threshold_abs:
                triggered = True
            if threshold_pct is not None and (not np.isnan(pct_change)) and (pct_change > threshold_pct):
                triggered = True
            
            if triggered:
                anomalies.append({
                    "country": country,
                    "year_from": y1,
                    "year_to": y2,
                    "value_before": v1,
                    "value_after": v2,
                    "abs_change": abs_change,
                    "pct_change": pct_change,
                })
    
    return pd.DataFrame(anomalies)

anomalies_le = detect_sudden_changes(
    df=df,
    attribute_prefix="le",
    threshold_abs=10,     
    threshold_pct=None  
)

print(anomalies_le)



# anomalies_gni = detect_sudden_changes(
#     df=df,
#     attribute_prefix="gnipc",
#     threshold_abs=10000,   # jumps > $3000
#     threshold_pct=None    # OR > 25% change
# )

# print(anomalies_gni)


# anomalies_mys = detect_sudden_changes(
#     df=df,
#     attribute_prefix="eys",
#     threshold_abs=5,   # jumps > $3000
#     threshold_pct=None    # OR > 25% change
# )
# 
# print(anomalies_mys)

