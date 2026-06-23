import json
import time
import pandas as pd
from bs4 import BeautifulSoup
from camoufox.sync_api import Camoufox

KNOWN_NEIGHBORHOODS = [
    "copou", "tatarasi", "nicolina", "cantemir", "pacurari", "cug", "bularga",
    "bucium", "centru", "podu ros", "dacia", "mircea", "galata", "alexandru",
    "tudor", "frumoasa", "manta rosie", "gara", "sararie", "socola"
]


def resolve_exact_neighborhood(title, slug, extracted_val):
    search_zone = f"{title} {slug}".lower()
    if "v luplui" in search_zone or "v lupului" in search_zone or "valea lupului" in search_zone:
        return "Valea Lupului"

    clean_val = str(extracted_val).strip()
    if clean_val in ["Iași", "Necunoscut", "", "None"]:
        for zone in KNOWN_NEIGHBORHOODS:
            if zone in search_zone:
                return zone.title()
        return "Iași Central / General"
    return clean_val


def run_production_pipeline():
    base_url = "https://www.storia.ro/ro/rezultate/vanzare/apartament/iasi/iasi"
    all_properties = []
    total_pages = 3
    processed_announcements_count = 0

    print("[*] Launching Crash-Proofed Production Stealth Engine...")
    with Camoufox(headless=False) as browser:
        # Create browser context explicitly
        context = browser.new_context()

        # FIX: Intercept and discard any unhandled page-level scripts errors
        # to prevent the internal coreBundle.js driver from crashing.
        context.on("pageerror", lambda err: None)

        page = context.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        for current_page in range(1, total_pages + 1):
            target_url = base_url if current_page == 1 else f"{base_url}?page={current_page}"
            print(f"\n[*] Processing Page {current_page}/{total_pages}: {target_url}")

            try:
                # Target HTML structures directly on layout completion
                page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(2.5)

                soup = BeautifulSoup(page.content(), "html.parser")
                next_data_script = soup.find("script", id="__NEXT_DATA__")

                if not next_data_script or not next_data_script.string:
                    print(f"[-] Data script target container skipped on page {current_page}")
                    continue

                raw_json = json.loads(next_data_script.string)
                items = raw_json["props"]["pageProps"]["data"]["searchAds"]["items"]

                print(f"[+] Found {len(items)} items on page {current_page} JSON structure.")

                for item in items:
                    if not item or not isinstance(item, dict):
                        continue

                    title = item.get("title", "Fără Titlu")
                    slug = item.get("slug", "")

                    # --- UPDATED: Dynamic Routing Switcher to use /oferta/ ---
                    if slug:
                        # Explicitly maps the path to use /oferta/ instead of /anunt/
                        full_url = f"https://www.storia.ro/ro/oferta/{slug}"
                    else:
                        href = item.get("href", "")
                        # Fallback to catch alternative link structures and swap them out if present
                        if "/anunt/" in href:
                            href = href.replace("/anunt/", "/oferta/")
                        elif "/ad/" in href:
                            href = href.replace("/ad/", "/oferta/")

                        full_url = href if href.startswith("http") else f"https://www.storia.ro/{href.lstrip('/')}"

                    location_obj = item.get("location", {})
                    labels = location_obj.get("labels", [])
                    raw_neighborhood = "Necunoscut"
                    if labels:
                        for label in reversed(labels):
                            if label.get("type") in ["QUARTER", "SUB_DISTRICT"]:
                                raw_neighborhood = label.get("label")
                                break

                    neighborhood = resolve_exact_neighborhood(title, slug, raw_neighborhood)

                    total_price_obj = item.get("totalPrice") or {}
                    total_price = total_price_obj.get("value") if isinstance(total_price_obj, dict) else None
                    surface_m2 = item.get("areaInSquareMeters")
                    rooms = item.get("roomsNumber")

                    if total_price and surface_m2 and float(surface_m2) > 0:
                        computed_price_per_m2 = round(total_price / float(surface_m2), 2)

                        all_properties.append({
                            "Cartier": neighborhood,
                            "Camere": rooms,
                            "Suprafata (m2)": surface_m2,
                            "Pret Total (EUR)": total_price,
                            "Pret/m2 (EUR)": computed_price_per_m2,
                            "Link Proprietate": full_url
                        })

                        processed_announcements_count += 1
                        print(
                            f"    -> Processed announcement #{processed_announcements_count}: {title[:40]}... [{neighborhood}]")

            except Exception as e:
                print(f"[-] Handled structural layout skip on page {current_page}: {e}")

    if all_properties:
        df = pd.DataFrame(all_properties)
        df.to_excel("iasi_market_data.xlsx", index=False)

        print(f"\n[*] Execution Cycle Complete. Total Announcements Tracked: {processed_announcements_count}")
        print("[*] Extrapolating baseline analysis assets...")

        neighborhood_medians = df.groupby("Cartier")["Pret/m2 (EUR)"].median().to_dict()
        df["Medie Cartier (EUR/m2)"] = df["Cartier"].map(neighborhood_medians)
        df["Deviatie Piata (%)"] = round(
            ((df["Pret/m2 (EUR)"] - df["Medie Cartier (EUR/m2)"]) / df["Medie Cartier (EUR/m2)"]) * 100, 2)

        underpriced_deals = df[df["Deviatie Piata (%)"] <= -5.0].sort_values(by="Deviatie Piata (%)")

        output_filename = "iasi_underpriced_deals.xlsx"
        underpriced_deals.to_excel(output_filename, index=False)
        print(f"[++] PRODUCTION DATA SET DEPLOYED: '{output_filename}'")
    else:
        print("[-] Pipeline executed completely but data vectors returned empty.")


if __name__ == "__main__":
    run_production_pipeline()