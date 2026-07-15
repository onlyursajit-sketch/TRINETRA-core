from src.intelligence.institutional_flow_adapter import (
    InstitutionalFlowAdapter,
)


def test_adapter_converts_fii_dii_result_to_institutional_flow() -> None:
    payload = {
        "fii": {
            "cash_net": -1300.0,
            "index_futures_net": -750.0,
            "stock_futures_net": 420.0,
        },
        "dii": {
            "cash_net": 1600.0,
        },
        "market_bias": "DOMESTICALLY_SUPPORTED",
    }

    flow = InstitutionalFlowAdapter().from_analysis(payload)

    assert flow.fii_cash == -1300.0
    assert flow.dii_cash == 1600.0
    assert flow.fii_index_futures == -750.0
    assert flow.fii_stock_futures == 420.0
    assert flow.fii_bias == "SHORT"
    assert flow.dii_bias == "LONG"


def test_adapter_maps_high_confidence_to_numeric_score() -> None:
    payload = {
        "fii": {"cash_net": 100.0},
        "dii": {"cash_net": 50.0},
        "confidence": "HIGH",
    }

    flow = InstitutionalFlowAdapter().from_analysis(payload)

    assert flow.confidence == 100.0


def test_adapter_uses_source_confidence_when_label_missing() -> None:
    payload = {
        "fii": {"cash_net": 100.0},
        "dii": {"cash_net": 50.0},
        "source_confidence": 72,
    }

    flow = InstitutionalFlowAdapter().from_analysis(payload)

    assert flow.confidence == 72.0
