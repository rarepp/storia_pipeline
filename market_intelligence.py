# market_intelligence.py

import pandas as pd


def analyze_market_trends(properties_list, raw_export_path="iasi_market_data.xlsx",
                          curated_export_path="iasi_underpriced_deals.xlsx"):
    if not properties_list:
        print("[-] Market intelligence execution aborted: Data vectors are empty.")
        return

    print("[*] Loading real estate data vectors into DataFrame...")
    df = pd.DataFrame(properties_list)

    # Export raw snapshot
    df.to_excel(raw_export_path, index=False)
    print(f"[+] Raw base market dataset exported to '{raw_export_path}'")

    print("[*] Extrapolating baseline analysis assets...")
    # Using median prevents luxury outliers from warping baseline metrics
    neighborhood_medians = df.groupby("Cartier")["Pret/m2 (EUR)"].median().to_dict()

    df["Medie Cartier (EUR/m2)"] = df["Cartier"].map(neighborhood_medians)
    df["Deviatie Piata (%)"] = round(
        ((df["Pret/m2 (EUR)"] - df["Medie Cartier (EUR/m2)"]) / df["Medie Cartier (EUR/m2)"]) * 100, 2
    )

    # Isolate targets with a threshold under -5% market median cost
    underpriced_deals = df[df["Deviatie Piata (%)"] <= -5.0].sort_values(by="Deviatie Piata (%)")

    # Export curated opportunities
    underpriced_deals.to_excel(curated_export_path, index=False)
    print(f"[++] PRODUCTION DATA SET DEPLOYED: '{curated_export_path}'")