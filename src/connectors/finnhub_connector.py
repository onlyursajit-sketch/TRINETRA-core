import os

import requests
from dotenv import load_dotenv


load_dotenv(".env", override=True)

BASE_URL = "https://finnhub.io/api/v1"


def get_quote(symbol: str) -> dict:
    api_key = os.getenv("FINNHUB_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "FINNHUB_API_KEY .env file me missing hai."
        )

    response = requests.get(
        f"{BASE_URL}/quote",
        params={
            "symbol": symbol,
            "token": api_key,
        },
        headers={
            "Accept": "application/json",
        },
        timeout=20,
    )

    if response.status_code == 401:
        raise RuntimeError(
            "Finnhub API key invalid, incomplete, or inactive."
        )

    if response.status_code == 429:
        raise RuntimeError(
            "Finnhub rate limit exceeded."
        )

    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, dict):
        raise RuntimeError(
            "Finnhub ne invalid response diya."
        )

    current = payload.get("c")

    if current in (None, 0):
        raise RuntimeError(
            f"Finnhub ne {symbol} ke liye usable quote nahi diya."
        )

    return payload
