import os
import requests
import pandas as pd

# =========================
# SETTINGS
# =========================

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

SYMBOL = "ETHUSDT"
INTERVAL = "15m"

BB_LENGTH = 20
BB_MULT = 3


# =========================
# GET CANDLES
# =========================

def get_candles():
    url = "https://data-api.binance.vision/api/v3/klines"

    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "limit": 100
    }

    response = requests.get(
        url,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        raise RuntimeError("Invalid candle data received")

    if len(data) < BB_LENGTH + 3:
        raise RuntimeError(
            f"Not enough candle data: {len(data)}"
        )

    df = pd.DataFrame(
        data,
        columns=[
            "time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "qav",
            "trades",
            "tbbav",
            "tbqav",
            "ignore"
        ]
    )

    df["close"] = pd.to_numeric(df["close"])

    return df


# =========================
# CALCULATE BB%B
# =========================

def calculate_bbp(df):
    middle = df["close"].rolling(BB_LENGTH).mean()

    std = df["close"].rolling(
        BB_LENGTH
    ).std(ddof=0)

    upper = middle + BB_MULT * std
    lower = middle - BB_MULT * std

    bbp = (
        (df["close"] - lower)
        / (upper - lower)
    )

    return bbp


# =========================
# TELEGRAM
# =========================

def send_telegram(message):
    url = (
        "https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/sendMessage"
    )

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=15
    )

    response.raise_for_status()


# =========================
# CHECK SIGNAL
# =========================

def check_signal():
    df = get_candles()

    bbp = calculate_bbp(df)

    # Last two CLOSED candles
    previous = float(bbp.iloc[-3])
    current = float(bbp.iloc[-2])

    price = float(df["close"].iloc[-2])

    # -------------------------
    # BELOW 0
    # -------------------------

    if previous >= 0 and current < 0:
        send_telegram(
            "🔴 ETH BB%B CROSSED BELOW 0\n\n"
            f"ETH: ${price:,.2f}\n"
            f"BB%B: {current:.4f}\n"
            "Timeframe: 15m\n"
            "BB Length: 20\n"
            "BB Multiplier: 3"
        )
        return

    # -------------------------
    # ABOVE 0
    # -------------------------

    if previous <= 0 and current > 0:
        send_telegram(
            "🟢 ETH BB%B CROSSED ABOVE 0\n\n"
            f"ETH: ${price:,.2f}\n"
            f"BB%B: {current:.4f}\n"
            "Timeframe: 15m\n"
            "BB Length: 20\n"
            "BB Multiplier: 3"
        )
        return

    # -------------------------
    # ABOVE 1
    # -------------------------

    if previous <= 1 and current > 1:
        send_telegram(
            "🟢 ETH BB%B CROSSED ABOVE 1\n\n"
            f"ETH: ${price:,.2f}\n"
            f"BB%B: {current:.4f}\n"
            "Timeframe: 15m\n"
            "BB Length: 20\n"
            "BB Multiplier: 3"
        )
        return

    # -------------------------
    # BELOW 1
    # -------------------------

    if previous >= 1 and current < 1:
        send_telegram(
            "🔴 ETH BB%B CROSSED BELOW 1\n\n"
            f"ETH: ${price:,.2f}\n"
            f"BB%B: {current:.4f}\n"
            "Timeframe: 15m\n"
            "BB Length: 20\n"
            "BB Multiplier: 3"
        )
        return


# =========================
# START
# =========================

if __name__ == "__main__":
    check_signal()
