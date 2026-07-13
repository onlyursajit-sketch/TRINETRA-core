from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


class NSEOptionChainError(Exception):
    """Raised when NSE option-chain data cannot be fetched or validated."""


class NSEOptionChainCollector:
    BASE_URL = "https://www.nseindia.com"
    OPTION_CHAIN_URL = (
        "https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    )

    SUPPORTED_SYMBOLS = {
        "NIFTY",
        "BANKNIFTY",
        "FINNIFTY",
        "MIDCPNIFTY",
        "NIFTYNXT50",
    }

    def __init__(
        self,
        cache_dir: str = "cache/option_chain",
        timeout: int = 10,
        retries: int = 2,
     ) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.timeout = timeout
        self.retries = retries

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Linux; Android 13) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Mobile Safari/537.36"
                ),
                "Accept": (
                    "application/json,text/plain,*/*"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "Referer": "https://www.nseindia.com/option-chain",
                "Connection": "keep-alive",
            }
        )

    def _validate_symbol(self, symbol: str) -> str:
        clean_symbol = symbol.strip().upper()

        if clean_symbol not in self.SUPPORTED_SYMBOLS:
            raise ValueError(
                f"Unsupported symbol: {clean_symbol}. "
                f"Supported symbols: {sorted(self.SUPPORTED_SYMBOLS)}"
            )

        return clean_symbol

    def _initialize_session(self) -> None:
        response = self.session.get(
            self.BASE_URL,
            timeout=self.timeout,
        )
        response.raise_for_status()
        time.sleep(0.5)

    def _fetch_raw(self, symbol: str) -> dict[str, Any]:
        url = self.OPTION_CHAIN_URL.format(symbol=symbol)
        last_error: Exception | None = None

        for attempt in range(1, self.retries + 1):
            try:
                self._initialize_session()

                response = self.session.get(
                    url,
                    timeout=self.timeout,
                )

                if response.status_code in (401, 403):
                    self.session.cookies.clear()
                    raise NSEOptionChainError(
                        f"NSE session rejected with HTTP "
                        f"{response.status_code}."
                    )

                response.raise_for_status()

                data = response.json()

                if not isinstance(data, dict):
                    raise NSEOptionChainError(
                        "NSE response is not a JSON object."
                    )

                return data

            except requests.Timeout:
                last_error = NSEOptionChainError(
                    f"NSE request timed out after "
                    f"{self.timeout}s."
                )

            except NSEOptionChainError:
                raise

            except (
                requests.RequestException,
                ValueError,
            ) as exc:
                last_error = exc

            if attempt < self.retries:
                time.sleep(min(attempt, 2))

        raise NSEOptionChainError(
            f"Failed to fetch option chain for "
            f"{symbol}: {last_error}"
        )

    def _validate_response(
        self,
        data: dict[str, Any],
    ) -> None:
        records = data.get("records")

        if not isinstance(records, dict):
            raise NSEOptionChainError(
                "Missing or invalid 'records' section."
            )

        if not isinstance(records.get("data"), list):
            raise NSEOptionChainError(
                "Missing or invalid option-chain records."
            )

        if not isinstance(records.get("expiryDates"), list):
            raise NSEOptionChainError(
                "Missing or invalid expiry-date list."
            )

    def _normalize(
        self,
        symbol: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        records = data["records"]

        underlying_value = records.get("underlyingValue")
        expiry_dates = records.get("expiryDates", [])
        rows = records.get("data", [])

        normalized_rows: list[dict[str, Any]] = []

        for row in rows:
            strike_price = row.get("strikePrice")
            expiry_date = row.get("expiryDate")

            normalized_rows.append(
                {
                    "strike_price": strike_price,
                    "expiry_date": expiry_date,
                    "ce": row.get("CE"),
                    "pe": row.get("PE"),
                }
            )

        atm_strike = None

        if isinstance(underlying_value, (int, float)) and normalized_rows:
            valid_strikes = [
                item["strike_price"]
                for item in normalized_rows
                if isinstance(item["strike_price"], (int, float))
            ]

            if valid_strikes:
                atm_strike = min(
                    valid_strikes,
                    key=lambda strike: abs(strike - underlying_value),
                )

        return {
            "symbol": symbol,
            "source": "NSE",
            "source_confidence": 100,
            "fetched_at": datetime.now().astimezone().isoformat(),
            "underlying_value": underlying_value,
            "expiry_dates": expiry_dates,
            "nearest_expiry": expiry_dates[0] if expiry_dates else None,
            "atm_strike": atm_strike,
            "total_records": len(normalized_rows),
            "records": normalized_rows,
        }

    def _save_cache(
        self,
        symbol: str,
        payload: dict[str, Any],
    ) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol.lower()}_{timestamp}.json"
        path = self.cache_dir / filename

        with path.open("w", encoding="utf-8") as file:
            json.dump(
                payload,
                file,
                indent=2,
                ensure_ascii=False,
            )

        latest_path = self.cache_dir / f"{symbol.lower()}_latest.json"

        with latest_path.open("w", encoding="utf-8") as file:
            json.dump(
                payload,
                file,
                indent=2,
                ensure_ascii=False,
            )

        return path

    def _load_latest_cache(
        self,
        symbol: str,
    ) -> dict[str, Any] | None:
        latest_path = self.cache_dir / f"{symbol.lower()}_latest.json"

        if not latest_path.exists():
            return None

        try:
            with latest_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)

            if not isinstance(payload, dict):
                return None

            payload["data_status"] = "STALE"
            payload["fallback_reason"] = (
                "Live NSE option-chain request failed. "
                "Serving last valid cached snapshot."
            )
            payload["cache_path"] = str(latest_path)

            return payload

        except (OSError, json.JSONDecodeError):
            return None

    def collect(
        self,
        symbol: str = "NIFTY",
    ) -> dict[str, Any]:
        clean_symbol = self._validate_symbol(symbol)

        try:
            raw_data = self._fetch_raw(clean_symbol)
            self._validate_response(raw_data)

            normalized = self._normalize(
                clean_symbol,
                raw_data,
            )

            normalized["data_status"] = "LIVE"
            normalized["fallback_reason"] = None

            cache_path = self._save_cache(
                clean_symbol,
                normalized,
            )

            normalized["cache_path"] = str(cache_path)

            return normalized

        except NSEOptionChainError as exc:
            cached = self._load_latest_cache(clean_symbol)

            if cached is not None:
                return cached

            return {
                "symbol": clean_symbol,
                "source": "NSE",
                "source_confidence": 0,
                "data_status": "NO_DATA",
                "fallback_reason": str(exc),
                "fetched_at": datetime.now().astimezone().isoformat(),
                "underlying_value": None,
                "expiry_dates": [],
                "nearest_expiry": None,
                "atm_strike": None,
                "total_records": 0,
                "records": [],
                "cache_path": None,
            }


if __name__ == "__main__":
    collector = NSEOptionChainCollector()

    result = collector.collect("NIFTY")

    print("=" * 60)
    print("TRINETRA - NSE OPTION CHAIN COLLECTOR")
    print("=" * 60)
    print(f"Symbol          : {result['symbol']}")
    print(f"Underlying      : {result['underlying_value']}")
    print(f"ATM Strike      : {result['atm_strike']}")
    print(f"Nearest Expiry  : {result['nearest_expiry']}")
    print(f"Total Records   : {result['total_records']}")
    print(f"Source          : {result['source']}")
    print(f"Confidence      : {result['source_confidence']}")
    print(f"Data Status     : {result['data_status']}")
    print(f"Fallback Reason : {result['fallback_reason']}")
    print(f"Cache Path      : {result['cache_path']}")

