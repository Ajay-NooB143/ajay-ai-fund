"""Tests for the CONVA conversational AI module."""

from agents.conva.intent_parser import (
    parse_intent,
    INTENT_ANALYZE,
    INTENT_SENTIMENT,
    INTENT_BUY,
    INTENT_SELL,
    INTENT_PORTFOLIO,
    INTENT_UNKNOWN,
)
from agents.conva.response_builder import build_response
from agents.conva.conva_agent import ConvaAgent


# ---------------------------------------------------------------------------
# Intent parser
# ---------------------------------------------------------------------------

class TestParseIntent:
    def test_buy_intent(self):
        result = parse_intent("Should I buy AAPL?")
        assert result["intent"] == INTENT_BUY

    def test_sell_intent(self):
        result = parse_intent("I want to sell TSLA")
        assert result["intent"] == INTENT_SELL

    def test_analyze_intent(self):
        result = parse_intent("Analyse MSFT for me")
        assert result["intent"] == INTENT_ANALYZE

    def test_sentiment_intent(self):
        result = parse_intent("What is the sentiment for this news?")
        assert result["intent"] == INTENT_SENTIMENT

    def test_portfolio_intent(self):
        result = parse_intent("Show my portfolio balance")
        assert result["intent"] == INTENT_PORTFOLIO

    def test_unknown_intent(self):
        result = parse_intent("Hello there!")
        assert result["intent"] == INTENT_UNKNOWN

    def test_symbol_extraction_ticker(self):
        result = parse_intent("Buy NVDA stock")
        assert result["symbol"] == "NVDA"

    def test_symbol_extraction_company_name(self):
        result = parse_intent("Analyse Tesla for me")
        assert result["symbol"] == "TSLA"

    def test_raw_preserved(self):
        msg = "Buy AAPL right now"
        result = parse_intent(msg)
        assert result["raw"] == msg


# ---------------------------------------------------------------------------
# Response builder
# ---------------------------------------------------------------------------

class TestBuildResponse:
    def test_sentiment_response(self):
        resp = build_response(INTENT_SENTIMENT, "TSLA", "POSITIVE")
        assert "POSITIVE" in resp
        assert "TSLA" in resp

    def test_analyze_response(self):
        resp = build_response(INTENT_ANALYZE, "AAPL", "some data",
                              extra={"decision": "BUY"})
        assert "BUY" in resp

    def test_buy_response(self):
        resp = build_response(INTENT_BUY, "EURUSD", "order placed")
        assert "BUY" in resp

    def test_sell_response(self):
        resp = build_response(INTENT_SELL, "GBPUSD", "order placed")
        assert "SELL" in resp

    def test_portfolio_response(self):
        resp = build_response(INTENT_PORTFOLIO, None, 10000)
        assert "10000" in resp

    def test_unknown_response_contains_examples(self):
        resp = build_response(INTENT_UNKNOWN, None, None)
        assert "Analyse" in resp or "portfolio" in resp.lower()


# ---------------------------------------------------------------------------
# ConvaAgent
# ---------------------------------------------------------------------------

class TestConvaAgent:
    def test_instantiation(self):
        agent = ConvaAgent()
        assert agent is not None

    def test_chat_returns_string(self):
        agent = ConvaAgent()
        response = agent.chat("Hello")
        assert isinstance(response, str)

    def test_history_recorded(self):
        agent = ConvaAgent()
        agent.chat("Show my portfolio")
        assert len(agent.history) == 1
        assert "user" in agent.history[0]
        assert "conva" in agent.history[0]

    def test_reset_clears_history(self):
        agent = ConvaAgent()
        agent.chat("Buy AAPL")
        agent.reset()
        assert agent.history == []

    def test_buy_intent_response(self):
        agent = ConvaAgent()
        resp = agent.chat("Buy EURUSD")
        assert isinstance(resp, str)
        assert len(resp) > 0

    def test_unknown_intent_response(self):
        agent = ConvaAgent()
        resp = agent.chat("xyzzy plugh")
        assert "CONVA" in resp or "not sure" in resp.lower()
