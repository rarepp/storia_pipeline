# market_intelligence.py

import pandas as pd
import re


def extract_storia_id(url):
    """Extracts the unique internal ID (e.g., IDHvsX) from anywhere inside the URL slug."""
    if not url:
        return None
    url_str = str(url).strip().rstrip('/')
    match = re.search(r'-([iI][dD][a-zA-Z0-9]+)(?:[\?#&]|$)', url_str)
    return match.group(1).upper() if match else url_str


def analyze_market_trends(properties_list, raw_export_path="iasi_market_data.xlsx",
                          curated_export_path="iasi_underpriced_deals.xlsx"):
    if not properties_list:
        print("[-] Market intelligence execution aborted: Data vectors are empty.")
        return

    print("[*] Loading real estate data vectors into DataFrame...")
    df = pd.DataFrame(properties_list)
    initial_count = len(df)

    # --- LAYER 1: REMOVE DUPLICATE LINK HASHES ---
    df["_internal_hash_id"] = df["Link Proprietate"].apply(extract_storia_id)
    df = df.drop_duplicates(subset=["_internal_hash_id"], keep="first")
    df = df.drop(columns=["_internal_hash_id"])

    # --- LAYER 2: REMOVE CLONED LISTINGS (Same Features, Different IDs) ---
    # Drops properties that share the exact same Neighborhood, Room count, Area, and Price
    df = df.drop_duplicates(
        subset=["Cartier", "Camere", "Suprafata (m2)", "Pret Total (EUR)"],
        keep="first"
    )

    duplicates_removed = initial_count - len(df)
    if duplicates_removed > 0:
        print(f"[+] SUCCESS: Filtered out {duplicates_removed} duplicate/cloned listings from the dataset.")
    else:
        print("[+] Verification complete: No structural duplicate variations detected.")

    # Export raw unique snapshot
    df.to_excel(raw_export_path, index=False)
    print(f"[+] Raw base market dataset exported to '{raw_export_path}'")

    print("[*] Extrapolating baseline analysis assets...")
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

    return df.to_dict(orient="records")