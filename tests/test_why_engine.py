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

    assert result["causes"] == [
        {
            "sequence": 1,
            "message": "Put-call ratio structure is bullish.",
        },
        {
            "sequence": 2,
            "message": "Open interest structure is bullish.",
        },
    ]

    assert result["warnings"] == [
        {
            "sequence": 1,
            "message": "India VIX is elevated.",
        }
    ]


def test_why_engine_handles_empty_inputs() -> None:
    result = WhyEngine.build(
        decision="WAIT",
        confidence_score=0.0,
        reasons=[],
        warnings=[],
    )

    assert result["causes"] == []
    assert result["warnings"] == []
