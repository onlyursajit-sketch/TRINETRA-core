from __future__ import annotations

from typing import Any

from src.providers.option_chain_provider import (
    OptionChainProvider,
)


class BrokerOptionChainProvider(
    OptionChainProvider,
):
    """
    Placeholder for future broker APIs.

    Future:
    - Dhan
    - Zerodha
    - Angel
    """

    name = "BROKER"
    confidence = 90

    def fetch(
        self,
        symbol: str,
    ) -> dict[str, Any]:

        return {
            "symbol": self.clean_symbol(symbol),
            "records": [],
            "source": "BROKER",
            "source_confidence": 0,
            "data_status": "NO_DATA",
            "fallback_reason": (
                "Broker API not configured."
            ),
        }

from datetime import datetime
import os

import requests


class DhanOptionChainProvider(OptionChainProvider):
    """Fetches and normalizes Dhan option-chain data."""

    name = "DHAN"
    confidence = 90

    OPTION_CHAIN_URL = "https://api.dhan.co/v2/optionchain"
    EXPIRY_LIST_URL = "https://api.dhan.co/v2/optionchain/expirylist"

    SYMBOLS = {
        "NIFTY": {
            "security_id": 13,
            "segment": "IDX_I",
        },
    }

    def __init__(
        self,
        client_id: str | None = None,
        access_token: str | None = None,
        expiry: str | None = None,
        session: Any | None = None,
    ) -> None:
        self.client_id = client_id or os.getenv("DHAN_CLIENT_ID")
        self.access_token = access_token or os.getenv("DHAN_ACCESS_TOKEN")
        self.expiry = expiry
        self.session = session or requests.Session()

    def _resolve_expiry(
        self,
        instrument: dict[str, Any],
    ) -> str:
        response = self.session.post(
            self.EXPIRY_LIST_URL,
            headers={
                "access-token": self.access_token,
                "client-id": self.client_id,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "UnderlyingScrip": instrument["security_id"],
                "UnderlyingSeg": instrument["segment"],
            },
            timeout=30,
        )

        payload = response.json()

        if response.status_code != 200:
            raise RuntimeError(
                f"Dhan expiry-list API error "
                f"{response.status_code}: {payload}"
            )

        expiries = payload.get("data", [])

        if not isinstance(expiries, list):
            raise RuntimeError(
                "Dhan expiry-list response contains invalid data."
            )

        today = datetime.now().date()
        valid_expiries: list[tuple[object, str]] = []

        for value in expiries:
            if not isinstance(value, str):
                continue

            try:
                parsed = datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                continue

            if parsed < today:
                continue

            valid_expiries.append((parsed, value))

        if not valid_expiries:
            raise RuntimeError(
                "Dhan expiry-list API returned no active expiry."
            )

        return min(valid_expiries, key=lambda item: item[0])[1]

    @staticmethod
    def _display_expiry(expiry: str) -> str:
        try:
            return datetime.strptime(expiry, "%Y-%m-%d").strftime("%d-%b-%Y")
        except ValueError:
            return expiry

    @staticmethod
    def _normalize_side(side: Any) -> dict[str, Any]:
        if not isinstance(side, dict):
            side = {}

        oi = side.get("oi", 0) or 0
        previous_oi = side.get("previous_oi", 0) or 0

        return {
            "openInterest": oi,
            "changeinOpenInterest": oi - previous_oi,
            "totalTradedVolume": side.get("volume", 0) or 0,
            "lastPrice": side.get("last_price", 0) or 0,
        }

    def fetch(self, symbol: str) -> dict[str, Any]:
        clean_symbol = self.clean_symbol(symbol)
        instrument = self.SYMBOLS.get(clean_symbol)

        if instrument is None:
            raise ValueError(
                f"Dhan option chain does not support symbol: {clean_symbol}"
            )

        if not self.client_id or not self.access_token:
            raise RuntimeError(
                "DHAN_CLIENT_ID or DHAN_ACCESS_TOKEN is missing."
            )

        expiry = self.expiry or self._resolve_expiry(instrument)

        response = self.session.post(
            self.OPTION_CHAIN_URL,
            headers={
                "access-token": self.access_token,
                "client-id": self.client_id,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "UnderlyingScrip": instrument["security_id"],
                "UnderlyingSeg": instrument["segment"],
                "Expiry": expiry,
            },
            timeout=30,
        )

        payload = response.json()

        if response.status_code != 200:
            raise RuntimeError(
                f"Dhan option-chain API error {response.status_code}: "
                f"{payload}"
            )

        data = payload.get("data", {})
        option_chain = data.get("oc", {})

        if not isinstance(option_chain, dict):
            option_chain = {}

        display_expiry = self._display_expiry(expiry)
        records: list[dict[str, Any]] = []

        for strike, values in option_chain.items():
            if not isinstance(values, dict):
                continue

            try:
                strike_price = float(strike)
            except (TypeError, ValueError):
                continue

            records.append(
                {
                    "strike_price": strike_price,
                    "expiry_date": display_expiry,
                    "ce": self._normalize_side(values.get("ce")),
                    "pe": self._normalize_side(values.get("pe")),
                }
            )

        records.sort(key=lambda row: row["strike_price"])

        return {
            "symbol": clean_symbol,
            "records": records,
            "nearest_expiry": display_expiry,
            "underlying_value": data.get("last_price"),
            "source": self.name,
            "source_confidence": self.confidence,
            "data_status": "LIVE" if records else "NO_DATA",
        }

