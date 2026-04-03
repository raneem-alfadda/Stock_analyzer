import pandas as pd
import numpy as np
from datetime import timedelta


def check_missing_dates(df: pd.DataFrame) -> dict:
    """
    Identify trading days with missing records.
    Compares actual dates vs expected business day range.
    Excludes weekends (Fri/Sat in Saudi market).
    """
    if df.empty:
        return {"status": "error", "message": "No data to check"}

    df["date"] = pd.to_datetime(df["date"])
    date_range = pd.date_range(start=df["date"].min(), end=df["date"].max(), freq="B")

    # Saudi market: Friday & Saturday are weekend (not Mon-Fri)
    # yfinance adjusts for local holidays automatically, so we flag gaps > 3 days
    actual_dates = set(df["date"].dt.date)
    missing = []
    sorted_dates = sorted(actual_dates)

    for i in range(1, len(sorted_dates)):
        gap = (sorted_dates[i] - sorted_dates[i - 1]).days
        if gap > 4:  # more than a long weekend
            missing.append({
                "from": str(sorted_dates[i - 1]),
                "to": str(sorted_dates[i]),
                "gap_days": gap,
            })

    return {
        "total_records": len(df),
        "date_range": f"{df['date'].min().date()} → {df['date'].max().date()}",
        "missing_gaps": missing,
        "missing_gap_count": len(missing),
        "status": " Gaps found" if missing else " No missing gaps",
    }


def check_null_values(df: pd.DataFrame) -> dict:
    """Check for null/NaN values in key columns."""
    key_cols = ["open", "high", "low", "close", "volume"]
    nulls = {col: int(df[col].isnull().sum()) for col in key_cols if col in df.columns}
    total_nulls = sum(nulls.values())

    return {
        "null_counts": nulls,
        "total_nulls": total_nulls,
        "status": "No nulls" if total_nulls == 0 else f" {total_nulls} null values found",
    }


def check_price_anomalies(df: pd.DataFrame, z_threshold: float = 3.0) -> dict:
    """
    Detect price anomalies using Z-score on daily returns.
    Flags days where price moved unusually far from the mean.
    """
    if len(df) < 10:
        return {"status": "insufficient data", "anomalies": []}

    df = df.copy()
    df["daily_return"] = df["close"].pct_change()

    mean_return = df["daily_return"].mean()
    std_return = df["daily_return"].std()

    if std_return == 0:
        return {"status": "no variance", "anomalies": []}

    df["z_score"] = (df["daily_return"] - mean_return) / std_return
    anomalies = df[df["z_score"].abs() > z_threshold][["date", "close", "daily_return", "z_score"]].copy()
    anomalies["daily_return"] = (anomalies["daily_return"] * 100).round(2)
    anomalies["z_score"] = anomalies["z_score"].round(2)
    anomalies["date"] = anomalies["date"].astype(str)

    return {
        "anomaly_count": len(anomalies),
        "anomalies": anomalies.to_dict(orient="records"),
        "status": " No anomalies" if anomalies.empty else f"⚠️ {len(anomalies)} anomalous day(s) detected",
    }


def check_volume_spikes(df: pd.DataFrame, multiplier: float = 2.5) -> dict:
    """
    Flag days where volume is significantly above the rolling average.
    Uses a 20-day rolling mean as the baseline.
    """
    if len(df) < 20:
        return {"status": "insufficient data", "spikes": []}

    df = df.copy()
    df["rolling_avg_vol"] = df["volume"].rolling(window=20, min_periods=5).mean()
    df["vol_ratio"] = df["volume"] / df["rolling_avg_vol"]

    spikes = df[df["vol_ratio"] > multiplier][["date", "volume", "rolling_avg_vol", "vol_ratio"]].copy()
    spikes["vol_ratio"] = spikes["vol_ratio"].round(2)
    spikes["date"] = spikes["date"].astype(str)

    return {
        "spike_count": len(spikes),
        "spikes": spikes.head(5).to_dict(orient="records"),
        "status": " No volume spikes" if spikes.empty else f" {len(spikes)} volume spike(s) detected",
    }


def run_full_quality_check(df: pd.DataFrame) -> dict:
    """Run all quality checks and return a combined report."""
    return {
        "missing_dates": check_missing_dates(df),
        "null_values": check_null_values(df),
        "price_anomalies": check_price_anomalies(df),
        "volume_spikes": check_volume_spikes(df),
    }