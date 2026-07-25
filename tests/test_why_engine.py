from src.decision.why_engine import WhyEngine


def test_why_engine_builds_structured_causes() -> None:
    result = WhyEngine.build(
        decision="BUY_BIAS",
        confidence_score=82.5,
        reasons=[
            "Put-call ratio structure is bullish.",
            "Open interest structure is bullish.",
        ],
        warnings=["India VIX is elevated."],
    )

    assert result["schema_version"] == "1.0"
    assert result["decision"] == "BUY_BIAS"
    assert result["confidence_score"] == 82.5

    assert result["causes"][0]["sequence"] == 1
    assert result["causes"][0]["message"] == (
        "Put-call ratio structure is bullish."
    )
    assert result["causes"][1]["sequence"] == 2
    assert result["causes"][1]["message"] == (
        "Open interest structure is bullish."
    )

    assert result["warnings"][0]["sequence"] == 1
    assert result["warnings"][0]["message"] == "India VIX is elevated."


def test_why_engine_handles_empty_inputs() -> None:
    result = WhyEngine.build(
        decision="WAIT",
        confidence_score=0.0,
        reasons=[],
        warnings=[],
    )

    assert result["causes"] == []
    assert result["warnings"] == []


def test_why_engine_adds_evidence_metadata() -> None:
    result = WhyEngine.build(
        decision="BUY_BIAS",
        confidence_score=88.0,
        reasons=[
            "Put-call ratio structure is bullish.",
            "Open interest structure is bullish.",
            "Bullish multi-signal confluence strengthens market conviction.",
        ],
        warnings=[],
    )

    assert result["causes"][0] == {
        "sequence": 1,
        "message": "Put-call ratio structure is bullish.",
        "category": "PCR",
        "bias": "BULLISH",
        "source": "OPTION_CHAIN",
        "strength": "MODERATE",
    }

    assert result["causes"][1]["category"] == "OPEN_INTEREST"
    assert result["causes"][1]["bias"] == "BULLISH"
    assert result["causes"][1]["source"] == "OPTION_CHAIN"

    assert result["causes"][2]["category"] == "CONFLUENCE"
    assert result["causes"][2]["bias"] == "BULLISH"
    assert result["causes"][2]["strength"] == "STRONG"


def test_why_engine_classifies_warning_severity() -> None:
    result = WhyEngine.build(
        decision="NO_TRADE",
        confidence_score=0.0,
        reasons=[],
        warnings=[
            "India VIX is extremely elevated.",
            "Source confidence is low.",
            "Market data is stale.",
        ],
    )

    assert result["warnings"][0] == {
        "sequence": 1,
        "message": "India VIX is extremely elevated.",
        "category": "VOLATILITY",
        "source": "INDIA_VIX",
        "severity": "CRITICAL",
    }

    assert result["warnings"][1]["category"] == "DATA_QUALITY"
    assert result["warnings"][1]["source"] == "SOURCE_CONFIDENCE"
    assert result["warnings"][1]["severity"] == "HIGH"

    assert result["warnings"][2]["category"] == "DATA_FRESHNESS"
    assert result["warnings"][2]["source"] == "MARKET_DATA"
    assert result["warnings"][2]["severity"] == "HIGH"


def test_why_engine_identifies_dominant_drivers() -> None:
    result = WhyEngine.build(
        decision="BUY_BIAS",
        confidence_score=91.0,
        reasons=[
            "Put-call ratio structure is bullish.",
            "Open interest structure is bearish.",
            "Bullish multi-signal confluence strengthens market conviction.",
        ],
        warnings=[
            "Source confidence is low.",
            "India VIX is extremely elevated.",
        ],
    )

    assert result["dominant_drivers"]["bullish"]["category"] == "CONFLUENCE"
    assert result["dominant_drivers"]["bullish"]["strength"] == "STRONG"

    assert result["dominant_drivers"]["bearish"]["category"] == "OPEN_INTEREST"
    assert result["dominant_drivers"]["bearish"]["bias"] == "BEARISH"

    assert result["dominant_drivers"]["risk"]["category"] == "VOLATILITY"
    assert result["dominant_drivers"]["risk"]["severity"] == "CRITICAL"
