import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fetcher import TADAWUL_STOCKS, get_ticker_symbol, fetch_current_snapshot, fetch_historical
from quality_check import run_full_quality_check
from interpreter import interpret_snapshot, format_snapshot_report


def print_quality_report(qc: dict):
    print("\n🔍 DATA QUALITY CHECK")
    print("-" * 40)

   
    md = qc["missing_dates"]
    print(f"  Date Coverage : {md.get('status', 'N/A')}")
    print(f"  Records Found : {md.get('total_records', 'N/A')}")
    if md.get("missing_gap_count", 0) > 0:
        for gap in md["missing_gaps"]:
            print(f"    ↳ Gap: {gap['from']} → {gap['to']} ({gap['gap_days']} days)")

    
    nv = qc["null_values"]
    print(f"  Null Values   : {nv.get('status', 'N/A')}")

 
    pa = qc["price_anomalies"]
    print(f"  Price Anomaly : {pa.get('status', 'N/A')}")
    if pa.get("anomaly_count", 0) > 0:
        for a in pa["anomalies"]:
            print(f"    ↳ {a['date']} | Return: {a['daily_return']}% | Z-score: {a['z_score']}")

    vs = qc["volume_spikes"]
    print(f"  Volume Spikes : {vs.get('status', 'N/A')}")
    if vs.get("spike_count", 0) > 0:
        for s in vs["spikes"][:3]:
            print(f"    ↳ {s['date']} | Ratio: {s['vol_ratio']}x avg")

    print("-" * 40)


def select_company() -> tuple:
    """Interactive company selector."""
    companies = list(TADAWUL_STOCKS.keys())
    print("\n📋 Available Tadawul Companies:")
    for i, name in enumerate(companies, 1):
        print(f"  {i:2}. {name}  ({TADAWUL_STOCKS[name]})")

    print("\n  0. Enter a custom ticker (e.g., 2350.SR)")
    print()

    while True:
        choice = input("Select a company (number or 0 for custom): ").strip()
        if choice == "0":
            ticker = input("Enter ticker symbol: ").strip().upper()
            return ticker, ticker
        elif choice.isdigit() and 1 <= int(choice) <= len(companies):
            name = companies[int(choice) - 1]
            return name, TADAWUL_STOCKS[name]
        else:
            print("  Invalid input. Please try again.")


def main():
    print("\n" + "=" * 55)
    print("  🇸🇦 Saudi Stock Decision Assistant")
    print("  Powered by Yahoo Finance (Tadawul .SR tickers)")
    print("=" * 55)

    company_name, ticker = select_company()

    print(f"\n⏳ Fetching data for {ticker}...")

    # Fetch current snapshot
    snapshot = fetch_current_snapshot(ticker)

    # Fetch historical for quality checks
    print("Loading 90-day historical data for quality checks...")
    historical = fetch_historical(ticker, period_days=90)

    # Interpret signal
    signal = interpret_snapshot(snapshot)

    # Print full report
    print("\n" + format_snapshot_report(snapshot, signal))

    # Print quality report
    if not historical.empty:
        qc = run_full_quality_check(historical)
        print_quality_report(qc)
    else:
        print("\n Could not fetch historical data for quality checks.")

    print("\nDone. \n")


if __name__ == "__main__":
    main()