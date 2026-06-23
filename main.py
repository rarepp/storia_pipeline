# main.py
from scraper import run_production_pipeline
from market_intelligence import analyze_market_trends
from database import save_daily_snapshot


def main():
    print("=== STARTING IAȘI REAL ESTATE TELEMETRY PIPELINE ===")

    # 1. Scrape data fields across pages
    extracted_data = run_production_pipeline(total_pages=3)

    if extracted_data:
        # 2. Run clean analytics and get rid of clones/duplicates
        # We will modify your market_intelligence to return the clean dictionary list
        analyze_market_trends(extracted_data)

        # 3. Stream data straight into your local SQL database
        print("[*] Syncing unique listings with SQL engine storage...")
        save_daily_snapshot(extracted_data)

        print("=== PIPELINE LIFECYCLE COMPLETED SUCCESSFULLY ===")
    else:
        print("[-] Data capture array empty. Execution sequence halted.")


if __name__ == "__main__":
    main()