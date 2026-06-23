# scraper.py

import json
import time
from bs4 import BeautifulSoup
from camoufox.sync_api import Camoufox
from config import resolve_exact_neighborhood


def run_production_pipeline(total_pages=3):
    base_url = "https://www.storia.ro/ro/rezultate/vanzare/apartament/iasi/iasi"
    all_properties = []
    processed_announcements_count = 0

    print("[*] Launching Crash-Proofed Production Stealth Engine...")
    with Camoufox(headless=False) as browser:
        context = browser.new_context()

        # Intercept and discard unhandled page-level scripts errors
        context.on("pageerror", lambda err: None)

        page = context.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        for current_page in range(1, total_pages + 1):
            target_url = base_url if current_page == 1 else f"{base_url}?page={current_page}"
            print(f"\n[*] Processing Page {current_page}/{total_pages}: {target_url}")

            try:
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

                    # Dynamic Routing Switcher to use /oferta/
                    if slug:
                        full_url = f"https://www.storia.ro/ro/oferta/{slug}"
                    else:
                        href = item.get("href", "")
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

    print(f"\n[*] Execution Cycle Complete. Total Announcements Tracked: {processed_announcements_count}")
    return all_properties