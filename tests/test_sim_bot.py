"""Tests for the simulation bot module."""

from simulation.sim_bot import (
    calculate_position,
    generate_signal,
    get_market_price,
    get_news_sentiment,
    log_trade,
    stop_loss,
    strategy_weights,
    total_pnl,
    trades,
    update_strategy,
)


def setup_function():
    """Reset shared state before each test."""
    trades.clear()
    strategy_weights["trend"] = 1.0
    strategy_weights["sentiment"] = 1.0


def test_get_market_price():
    for _ in range(50):
        price = get_market_price()
        assert 80 <= price <= 150


def test_get_news_sentiment():
    for _ in range(50):
        sentiment = get_news_sentiment()
        assert sentiment in ("POSITIVE", "NEGATIVE")


def test_generate_signal_buy():
    """High price + positive sentiment should produce BUY."""
    assert generate_signal(120, "POSITIVE") == "BUY"


def test_generate_signal_sell():
    """Low price + negative sentiment should produce SELL."""
    assert generate_signal(80, "NEGATIVE") == "SELL"


def test_calculate_position():
    assert calculate_position(1000) == 20.0
    assert calculate_position(500) == 10.0


def test_stop_loss_triggered():
    assert stop_loss(100, 97) is True


def test_stop_loss_not_triggered():
    assert stop_loss(100, 99) is False


def test_log_trade_and_pnl():
    log_trade("BUY", 10)
    log_trade("SELL", -5)
    assert len(trades) == 2
    assert total_pnl() == 5


def test_update_strategy_positive():
    update_strategy(10)
    assert strategy_weights["trend"] == 1.1
    assert strategy_weights["sentiment"] == 1.1


def test_update_strategy_negative():
    update_strategy(-5)
    assert strategy_weights["trend"] == 0.9
    assert strategy_weights["sentiment"] == 0.9


def test_update_strategy_clamp():
    """Weights should never drop below 0.1."""
    strategy_weights["trend"] = 0.1
    strategy_weights["sentiment"] = 0.1
    update_strategy(-5)
    assert strategy_weights["trend"] == 0.1
    assert strategy_weights["sentiment"] == 0.1
