import os

import requests
from dotenv import load_dotenv


load_dotenv(".env", override=True)

BASE_URL = "https://www.alphavantage.co/query"


def get_global_quote(symbol: str) -> dict:
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "ALPHA_VANTAGE_API_KEY .env file me missing hai."
        )

    response = requests.get(
        BASE_URL,
        params={
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": api_key,
        },
        timeout=20,
    )

    response.raise_for_status()
    payload = response.json()

    if "Error Message" in payload:
        raise RuntimeError(payload["Error Message"])

    if "Information" in payload:
        raise RuntimeError(payload["Information"])

    if "Note" in payload:
        raise RuntimeError(payload["Note"])

    quote = payload.get("Global Quote") or {}

    if not quote:
        raise RuntimeError(
            f"Alpha Vantage ne {symbol} ke liye quote nahi diya."
        )

    return quote
