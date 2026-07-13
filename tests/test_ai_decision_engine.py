from src.intelligence.ai_decision_engine import AIDecisionEngine
from src.intelligence.market_context import MarketContext


def test_buy_signal():
    engine = AIDecisionEngine()

    ctx = MarketContext(symbol="NIFTY")
    ctx.confidence = 80
    ctx.fii_bias = "LONG"
    ctx.oi_bullish = True
    ctx.volume_bullish = True

    result = engine.decide(ctx)

    assert result["action"] == "BUY"


def test_sell_signal():
    engine = AIDecisionEngine()

    ctx = MarketContext(symbol="NIFTY")
    ctx.confidence = 20
    ctx.fii_bias = "SHORT"
    ctx.oi_bullish = False
    ctx.volume_bullish = False

    result = engine.decide(ctx)

    assert result["action"] == "SELL"


def test_hold_signal():
    engine = AIDecisionEngine()

    ctx = MarketContext(symbol="NIFTY")
    ctx.confidence = 50

    result = engine.decide(ctx)

    assert result["action"] == "HOLD"
