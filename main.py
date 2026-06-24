# main.py
from scraper import run_production_pipeline
from market_intelligence import analyze_market_trends
from database import save_daily_snapshot


def main():
    print("=== STARTING IAȘI REAL ESTATE TELEMETRY PIPELINE ===")

    # 1. Scrape data fields across pages
    raw_data = run_production_pipeline(total_pages=3)

    if raw_data:
        # 2. Clean data and capture the DE-DUPLICATED output list
        clean_data = analyze_market_trends(raw_data)

        # 3. Stream ONLY the perfectly unique listings to SQL storage
        print("[*] Syncing unique listings with SQL engine storage...")
        save_daily_snapshot(clean_data)

        print("=== PIPELINE LIFECYCLE COMPLETED SUCCESSFULLY ===")
    else:
        print("[-] Data capture array empty. Execution sequence halted.")


if __name__ == "__main__":
    main()