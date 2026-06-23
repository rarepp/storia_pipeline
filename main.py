# main.py

from scraper import run_production_pipeline
from market_intelligence import analyze_market_trends


def main():
    print("=== STARTING IAȘI REAL ESTATE DATA PIPELINE ===")

    # 1. Execute scraper routine (Targeting first 3 pages)
    extracted_data = run_production_pipeline(total_pages=3)

    # 2. Feed raw matrix into the intelligence module for transformation & export
    analyze_market_trends(extracted_data)

    print("=== PIPELINE LIFECYCLE COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()