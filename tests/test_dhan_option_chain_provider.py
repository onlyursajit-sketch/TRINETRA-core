from __future__ import annotations

from unittest.mock import Mock

from src.providers.broker.broker_provider import DhanOptionChainProvider


def test_dhan_provider_normalizes_option_chain() -> None:
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "status": "success",
        "data": {
            "last_price": 25010.5,
            "oc": {
                "25000.000000": {
                    "ce": {
                        "oi": 1200,
                        "previous_oi": 1000,
                        "volume": 500,
                        "last_price": 120.5,
                    },
                    "pe": {
                        "oi": 1500,
                        "previous_oi": 1300,
                        "volume": 700,
                        "last_price": 105.0,
                    },
                }
            },
        },
    }

    session = Mock()
    session.post.return_value = response

    provider = DhanOptionChainProvider(
        client_id="demo-client",
        access_token="demo-token",
        expiry="2026-07-16",
        session=session,
    )

    result = provider.fetch("NIFTY")

    assert result["symbol"] == "NIFTY"
    assert result["source"] == "DHAN"
    assert result["data_status"] == "LIVE"
    assert result["underlying_value"] == 25010.5
    assert result["nearest_expiry"] == "16-Jul-2026"

    assert result["records"] == [
        {
            "strike_price": 25000.0,
            "expiry_date": "16-Jul-2026",
            "ce": {
                "openInterest": 1200,
                "changeinOpenInterest": 200,
                "totalTradedVolume": 500,
                "lastPrice": 120.5,
            },
            "pe": {
                "openInterest": 1500,
                "changeinOpenInterest": 200,
                "totalTradedVolume": 700,
                "lastPrice": 105.0,
            },
        }
    ]

    session.post.assert_called_once()
