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


def test_why_engine_builds_narrative_summary() -> None:
    result = WhyEngine.build(
        decision="BUY_BIAS",
        confidence_score=91.0,
        reasons=[
            "Put-call ratio structure is bullish.",
            "Open interest structure is bearish.",
            "Bullish multi-signal confluence strengthens market conviction.",
        ],
        warnings=[
            "India VIX is extremely elevated.",
        ],
    )

    assert result["narrative"]["headline"] == (
        "BUY_BIAS supported by bullish CONFLUENCE."
    )

    assert result["narrative"]["counter_signal"] == (
        "Primary counter-signal: bearish OPEN_INTEREST."
    )

    assert result["narrative"]["risk"] == (
        "Primary risk: CRITICAL VOLATILITY warning."
    )


def test_why_engine_aligns_narrative_with_confidence() -> None:
    result = WhyEngine.build(
        decision="BUY_BIAS",
        confidence_score=91.0,
        reasons=[
            "Bullish multi-signal confluence strengthens market conviction.",
        ],
        warnings=[],
    )

    assert result["narrative"]["confidence_level"] == "HIGH"
    assert result["narrative"]["confidence_statement"] == (
        "Decision confidence is HIGH at 91.0%."
    )


def test_why_engine_builds_sell_bias_narrative() -> None:
    result = WhyEngine.build(
        decision="SELL_BIAS",
        confidence_score=84.0,
        reasons=[
            "Open interest structure is bearish.",
        ],
        warnings=[],
    )

    assert result["narrative"]["headline"] == (
        "SELL_BIAS supported by bearish OPEN_INTEREST."
    )


def test_why_engine_builds_wait_narrative() -> None:
    result = WhyEngine.build(
        decision="WAIT",
        confidence_score=55.0,
        reasons=[],
        warnings=[],
    )

    assert result["narrative"]["headline"] == (
        "WAIT until a dominant directional driver emerges."
    )
    assert result["narrative"]["counter_signal"] is None


def test_why_engine_builds_no_trade_narrative() -> None:
    result = WhyEngine.build(
        decision="NO_TRADE",
        confidence_score=0.0,
        reasons=[],
        warnings=[
            "Market data is stale.",
        ],
    )

    assert result["narrative"]["headline"] == (
        "NO_TRADE because decision-quality requirements are not met."
    )
    assert result["narrative"]["risk"] == (
        "Primary risk: HIGH DATA_FRESHNESS warning."
    )


def test_why_engine_handles_malformed_inputs_defensively() -> None:
    result = WhyEngine.build(
        decision="WAIT",
        confidence_score=150.0,
        reasons=[
            "",
            "  Put-call ratio structure is bullish.  ",
            None,
        ],
        warnings=[
            None,
            "  Market data is stale.  ",
            "",
        ],
    )

    assert result["confidence_score"] == 100.0

    assert len(result["causes"]) == 1
    assert result["causes"][0]["message"] == (
        "Put-call ratio structure is bullish."
    )

    assert len(result["warnings"]) == 1
    assert result["warnings"][0]["message"] == "Market data is stale."


def test_why_engine_exposes_valid_contract() -> None:
    result = WhyEngine.build(
        decision="BUY_BIAS",
        confidence_score=85.0,
        reasons=[
            "Put-call ratio structure is bullish.",
        ],
        warnings=[
            "Market data is stale.",
        ],
    )

    assert result["schema_version"] == "1.0"
    assert result["contract_valid"] is True
    assert result["contract_errors"] == []


def test_why_engine_contract_validation_detects_invalid_payload() -> None:
    payload = {
        "schema_version": "1.0",
        "decision": "",
        "confidence_score": 101.0,
        "causes": "invalid",
        "warnings": [],
        "dominant_drivers": {},
        "narrative": {},
    }

    errors = WhyEngine.validate_contract(payload)

    assert "decision must be a non-empty string" in errors
    assert "confidence_score must be between 0 and 100" in errors
    assert "causes must be a list" in errors


def test_why_engine_normalises_invalid_contract_inputs() -> None:
    result = WhyEngine.build(
        decision="   ",
        confidence_score=float("nan"),
        reasons="invalid",
        warnings={"invalid": True},
    )

    assert result["decision"] == "WAIT"
    assert result["confidence_score"] == 0.0
    assert result["causes"] == []
    assert result["warnings"] == []
    assert result["contract_valid"] is True
    assert result["contract_errors"] == []
