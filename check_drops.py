# check_drops.py
import pandas as pd
from sqlalchemy import create_engine


def view_price_changes():
    engine = create_engine("sqlite:///storia_market_telemetry.db")

    # SQL query to pull items with multiple price entries
    query = """
    SELECT 
        p.storia_id,
        p.neighborhood,
        p.rooms,
        p.surface_m2,
        ph.price_eur,
        ph.recorded_at
    FROM properties p
    JOIN price_history ph ON p.storia_id = ph.storia_id
    WHERE p.storia_id IN (
        SELECT storia_id FROM price_history GROUP BY storia_id HAVING COUNT(id) > 1
    )
    ORDER BY p.storia_id, ph.recorded_at ASC;
    """

    df = pd.read_sql(query, con=engine)

    if df.empty:
        print("[*] No historical price modifications detected yet.")
        return

    print("\n=== HISTORICAL PRICE MODIFICATIONS DETECTED ===\n")

    # Group by id to display the timeline for each individual property cleanly
    for name, group in df.groupby("storia_id"):
        print(
            f"🏠 Property ID: {name} | Cartier: {group['neighborhood'].iloc[0]} | {group['rooms'].iloc[0]} Camere - {group['surface_m2'].iloc[0]}m2")

        # Print the history chain for this property
        for idx, row in group.iterrows():
            print(f"   -> {row['recorded_at']} | Price: {row['price_eur']} EUR")

        # Calculate final delta change
        prices = group['price_eur'].tolist()
        delta = prices[-1] - prices[0]
        direction = "📉 DROP" if delta < 0 else "📈 INCREASE"
        print(f"   ⚡ Delta Modification: {direction} of {abs(delta)} EUR\n" + "-" * 50)


if __name__ == "__main__":
    view_price_changes()