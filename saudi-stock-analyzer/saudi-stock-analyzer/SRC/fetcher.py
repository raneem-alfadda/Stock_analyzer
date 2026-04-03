import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

TADAWUL_STOCKS = {
    "Al Rajhi Bank": "1120.SR",
    "Saudi Aramco": "2222.SR",
    "Saudi National Bank": "1180.SR",
    "SABIC": "2010.SR",
    "Riyad Bank": "1010.SR",
    "STC": "7010.SR",
    "Alinma Bank": "1150.SR",
}

def get_ticker_symbol(company_name):
    return TADAWUL_STOCKS.get(company_name, company_name)

def fetch_current_snapshot(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    current_price = info.get("currentPrice") or info.get("regularMarketPrice")
    prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
    if current_price and prev_close:
        change = current_price - prev_close
        change_pct = (change / prev_close) * 100
    else:
        change = None
        change_pct = None
    return {
        "ticker": ticker,
        "company": info.get("longName", ticker),
        "current_price": current_price,
        "previous_close": prev_close,
        "change": change,
        "change_pct": change_pct,
        "volume": info.get("volume") or info.get("regularMarketVolume"),
        "avg_volume": info.get("averageVolume"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
        "currency": info.get("currency", "SAR"),
        "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

def fetch_historical(ticker, period_days=90):
    end = datetime.today()
    start = end - timedelta(days=period_days)
    stock = yf.Ticker(ticker)
    df = stock.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))
    if df.empty:
        return pd.DataFrame()
    df = df.reset_index()
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
    df.columns = ["date", "open", "high", "low", "close", "volume"]
    df = df.sort_values("date").reset_index(drop=True)
    return df