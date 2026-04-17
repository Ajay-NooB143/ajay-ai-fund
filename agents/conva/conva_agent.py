"""CONVA — Conversational AI agent built for Ajay AI Fund.

Orchestrates user messages through intent parsing, agent dispatch, and
response building to provide a natural-language interface to the trading
system.
"""

from agents.conva.intent_parser import (
    parse_intent,
    INTENT_ANALYZE,
    INTENT_SENTIMENT,
    INTENT_BUY,
    INTENT_SELL,
    INTENT_PORTFOLIO,
)
from agents.conva.response_builder import build_response


class ConvaAgent:
    """CONVA — Built for AI.

    Usage::

        agent = ConvaAgent()
        response = agent.chat("Analyse AAPL for me")
        print(response)
    """

    def __init__(self):
        self._history: list[dict] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(self, message: str) -> str:
        """Process *message* and return a conversational response."""
        parsed = parse_intent(message)
        intent = parsed["intent"]
        symbol = parsed["symbol"] or "AAPL"
        text = parsed["text"]

        result = self._dispatch(intent, symbol, text)
        response = build_response(
            intent, parsed["symbol"],
            result["agent_output"], extra=result.get("extra"),
        )

        self._history.append({"user": message, "conva": response})
        return response

    @property
    def history(self) -> list[dict]:
        """Return conversation history as a list of ``{user, conva}`` dicts."""
        return list(self._history)

    def reset(self) -> None:
        """Clear conversation history."""
        self._history.clear()

    # ------------------------------------------------------------------
    # Internal dispatch
    # ------------------------------------------------------------------

    def _dispatch(self, intent: str, symbol: str, text: str) -> dict:
        if intent == INTENT_SENTIMENT:
            return self._run_sentiment(text)

        if intent == INTENT_ANALYZE:
            return self._run_analyze(symbol, text)

        if intent in (INTENT_BUY, INTENT_SELL):
            return self._run_trade(intent, symbol)

        if intent == INTENT_PORTFOLIO:
            return self._run_portfolio()

        return {"agent_output": None}

    # ------------------------------------------------------------------
    # Agent runners (lazy imports to keep startup fast)
    # ------------------------------------------------------------------

    def _run_sentiment(self, text: str) -> dict:
        try:
            from agents.sentiment.sentiment_agent import analyze_sentiment
            label = analyze_sentiment(text)
        except Exception as exc:  # noqa: BLE001
            label = f"unavailable ({exc})"
        return {"agent_output": label}

    def _run_analyze(self, symbol: str, text: str) -> dict:
        try:
            from agents.forecaster.data_fetcher import get_stock_data
            data = get_stock_data(symbol)
        except Exception as exc:  # noqa: BLE001
            data = f"unavailable ({exc})"

        try:
            from agents.sentiment.sentiment_agent import analyze_sentiment
            from agents.strategy import trading_decision
            sentiment = analyze_sentiment(text) if text.strip() else "NEUTRAL"
            decision = trading_decision(sentiment)
        except Exception as exc:  # noqa: BLE001
            decision = f"unavailable ({exc})"

        return {"agent_output": data, "extra": {"decision": decision}}

    def _run_trade(self, intent: str, symbol: str) -> dict:
        try:
            from execution.trade_executor import execute_trade
            decision = "BUY" if intent == INTENT_BUY else "SELL"
            result = execute_trade(decision)
        except Exception as exc:  # noqa: BLE001
            result = f"unavailable ({exc})"
        return {"agent_output": result}

    def _run_portfolio(self) -> dict:
        try:
            from portfolio.portfolio_manager import get_balance
            balance = get_balance()
        except Exception as exc:  # noqa: BLE001
            balance = f"unavailable ({exc})"
        return {"agent_output": balance}
