import os
import time
import requests
import pandas as pd

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

SYMBOL = "ETHUSDT"
INTERVAL = "15m"
BB_LENGTH = 20
BB_MULT = 3


def get_candles():
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "limit": BB_LENGTH + 5
    }

    data = requests.get(url, params=params, timeout=10).json()

    df = pd.DataFrame(data, columns=[
        "time", "open", "high", "low", "close",
        "volume", "close_time", "qav", "trades",
        "tbbav", "tbqav", "ignore"
    ])

    df["close"] = df["close"].astype(float)

    return df


def calculate_bbp(df):
    middle = df["close"].rolling(BB_LENGTH).mean()
    std = df["close"].rolling(BB_LENGTH).std(ddof=0)

    upper = middle + BB_MULT * std
    lower = middle - BB_MULT * std

    bbp = (df["close"] - lower) / (upper - lower)

    return bbp


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=10
    )


def check_signal():
    df = get_candles()

    bbp = calculate_bbp(df)

    # Use the last CLOSED 15-minute candle
    previous = bbp.iloc[-3]
    current = bbp.iloc[-2]

    price = df["close"].iloc[-2]

    # Cross DOWN through 0
    if previous >= 0 and current < 0:
        send_telegram(
            f"🔴 ETH BB%B crossed BELOW 0\n\n"
            f"ETH: ${price:,.2f}\n"
            f"BB%B: {current:.4f}\n"
            f"Timeframe: 15m\n"
            f"BB: Length 20 / Mult 3"
        )

    # Cross UP through 0
    elif previous <= 0 and current > 0:
        send_telegram(
            f"🟢 ETH BB%B crossed ABOVE 0\n\n"
            f"ETH: ${price:,.2f}\n"
            f"BB%B: {current:.4f}\n"
            f"Timeframe: 15m\n"
            f"BB: Length 20 / Mult 3"
        )

    # Cross UP through 1
    elif previous <= 1 and current > 1:
        send_telegram(
            f"🟢 ETH BB%B crossed ABOVE 1\n\n"
            f"ETH: ${price:,.2f}\n"
            f"BB%B: {current:.4f}\n"
            f"Timeframe: 15m\n"
            f"BB: Length 20 / Mult 3"
        )

    # Cross DOWN through 1
    elif previous >= 1 and current < 1:
        send_telegram(
            f"🔴 ETH BB%B crossed BELOW 1\n\n"
            f"ETH: ${price:,.2f}\n"
            f"BB%B: {current:.4f}\n"
            f"Timeframe: 15m\n"
            f"BB: Length 20 / Mult 3"
        )


if __name__ == "__main__":
    check_signal()
