from dataclasses import dataclass

@dataclass
class StockSignal:
    direction: str
    strength: str
    label: str
    explanation: str
    recommendation: str

def interpret_snapshot(snapshot):
    change_pct = snapshot.get("change_pct")
    volume = snapshot.get("volume")
    avg_volume = snapshot.get("avg_volume")
    price = snapshot.get("current_price")
    high_52w = snapshot.get("52w_high")
    low_52w = snapshot.get("52w_low")
    if change_pct is None:
        return StockSignal(direction="UNKNOWN", strength="UNKNOWN",
            label="No Data", explanation="Could not retrieve price data.",
            recommendation="Verify the ticker symbol or try again later.")
    if change_pct > 0.5:
        direction = "UP"
    elif change_pct < -0.5:
        direction = "DOWN"
    else:
        direction = "FLAT"
    if volume and avg_volume and avg_volume > 0:
        vol_ratio = volume / avg_volume
        high_volume = vol_ratio >= 1.5
        low_volume = vol_ratio <= 0.6
    else:
        vol_ratio = None
        high_volume = False
        low_volume = False
    near_high = price and high_52w and (price >= high_52w * 0.97)
    near_low = price and low_52w and (price <= low_52w * 1.03)
    if direction == "UP" and high_volume:
        return StockSignal(direction="UP", strength="STRONG", label="Strong Bullish",
            explanation="Price rose {:.2f}% with volume {:.1f}x above average.".format(change_pct, vol_ratio),
            recommendation="Watch for continuation." + (" Near 52-week high." if near_high else ""))
    elif direction == "UP" and low_volume:
        return StockSignal(direction="UP", strength="WEAK", label="Weak Bullish",
            explanation="Price rose {:.2f}% but volume was low ({:.1f}x).".format(change_pct, vol_ratio),
            recommendation="Wait for volume confirmation.")
    elif direction == "DOWN" and high_volume:
        return StockSignal(direction="DOWN", strength="STRONG", label="Strong Bearish",
            explanation="Price dropped {:.2f}% with volume {:.1f}x above average.".format(abs(change_pct), vol_ratio),
            recommendation="Caution advised." + (" Near 52-week low." if near_low else ""))
    elif direction == "DOWN" and low_volume:
        return StockSignal(direction="DOWN", strength="WEAK", label="Weak Bearish",
            explanation="Price dropped {:.2f}% but volume was low ({:.1f}x).".format(abs(change_pct), vol_ratio),
            recommendation="Watch next session for direction.")
    elif direction == "FLAT":
        return StockSignal(direction="FLAT", strength="NEUTRAL", label="Neutral",
            explanation="Price moved only {:.2f}%. Market consolidating.".format(change_pct),
            recommendation="No clear signal. Review fundamentals.")
    else:
        return StockSignal(direction=direction, strength="UNKNOWN", label="Unknown",
            explanation="Price changed {:.2f}% but volume data unavailable.".format(change_pct),
            recommendation="Interpret with caution.")

def format_snapshot_report(snapshot, signal):
    def fmt(val, suffix="", decimals=2):
        if val is None:
            return "N/A"
        return "{:,.{}f}{}".format(val, decimals, suffix)
    arrow = "UP" if (snapshot.get("change") or 0) >= 0 else "DOWN"
    sign = "+" if (snapshot.get("change") or 0) >= 0 else ""
    lines = [
        "=" * 55,
        "  {}".format(snapshot.get("company", "Unknown")),
        "  {}  |  {}".format(snapshot.get("ticker", ""), snapshot.get("fetched_at", "")),
        "=" * 55,
        "",
        "MARKET SNAPSHOT",
        "  Current Price : {}".format(fmt(snapshot.get("current_price"), suffix=" SAR")),
        "  Change        : {} {}{}  ({}{}%)".format(arrow, sign, fmt(snapshot.get("change"), suffix=" SAR"), sign, fmt(snapshot.get("change_pct"))),
        "  Volume        : {}".format(fmt(snapshot.get("volume"), decimals=0)),
        "  Avg Volume    : {}".format(fmt(snapshot.get("avg_volume"), decimals=0)),
        "  52W High      : {}".format(fmt(snapshot.get("52w_high"), suffix=" SAR")),
        "  52W Low       : {}".
format(fmt(snapshot.get("52w_low"), suffix=" SAR")),
        "",
        "SMART INTERPRETATION",
        "  Signal    : {}".format(signal.label),
        "  Strength  : {}".format(signal.strength),
        "  Meaning   : {}".format(signal.explanation),
        "  Watch     : {}".format(signal.recommendation),
        "",
        "=" * 55,
        "  This is not financial advice.",
        "=" * 55,
    ]
    return "\n".join(lines)