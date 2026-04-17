"""CONVA response builder — formats agent outputs as conversational text."""

from agents.conva.intent_parser import (
    INTENT_ANALYZE, INTENT_SENTIMENT, INTENT_BUY,
    INTENT_SELL, INTENT_PORTFOLIO,
)


def build_response(
    intent: str,
    symbol: str | None,
    agent_result,
    extra: dict | None = None,
) -> str:
    """Return a human-readable CONVA response.

    Parameters
    ----------
    intent:
        Parsed intent label.
    symbol:
        Ticker extracted from the user message (may be None).
    agent_result:
        Raw output from the underlying agent/service.
    extra:
        Optional dict of supplementary data (e.g. ``{"decision": "BUY"}``).
    """
    sym_str = f" for **{symbol}**" if symbol else ""

    if intent == INTENT_SENTIMENT:
        return (
            f"🧠 Sentiment analysis{sym_str}: **{agent_result}**.\n"
            "This reflects the overall tone of the provided text."
        )

    if intent == INTENT_ANALYZE:
        decision = extra.get("decision", "HOLD") if extra else "HOLD"
        return (
            f"📊 Analysis{sym_str}:\n"
            f"  • Market data snapshot: {agent_result}\n"
            f"  • AI recommendation: **{decision}**"
        )

    if intent == INTENT_BUY:
        return (
            f"💰 Trade signal{sym_str}: **BUY**.\n"
            f"  • Execution result: {agent_result}"
        )

    if intent == INTENT_SELL:
        return (
            f"💰 Trade signal{sym_str}: **SELL**.\n"
            f"  • Execution result: {agent_result}"
        )

    if intent == INTENT_PORTFOLIO:
        return f"📁 Portfolio / balance: **{agent_result}**"

    # INTENT_UNKNOWN
    news_example = (
        "  • \"What is the sentiment for Tesla?"
        " News: Tesla beats earnings.\"\n"
    )
    return (
        "🤖 CONVA: I'm not sure what you mean. "
        "Try asking something like:\n"
        "  • \"Analyse AAPL\"\n"
        + news_example
        + "  • \"Buy EURUSD\"\n"
        "  • \"Show my portfolio\""
    )
