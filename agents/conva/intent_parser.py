"""CONVA intent parser.

Maps natural language to structured intent and entities.
"""

import re

# Recognised intent labels
INTENT_ANALYZE = "analyze"
INTENT_SENTIMENT = "sentiment"
INTENT_BUY = "buy"
INTENT_SELL = "sell"
INTENT_PORTFOLIO = "portfolio"
INTENT_UNKNOWN = "unknown"

# Common stock symbols that appear verbatim in text
_KNOWN_SYMBOLS = {
    "aapl", "apple",
    "tsla", "tesla",
    "goog", "google",
    "amzn", "amazon",
    "msft", "microsoft",
    "nvda", "nvidia",
    "meta", "btc", "bitcoin",
    "eth", "ethereum",
    "eurusd", "gbpusd", "xauusd",
}

# Alias map: plain name → ticker
_SYMBOL_ALIAS = {
    "apple": "AAPL",
    "tesla": "TSLA",
    "google": "GOOG",
    "amazon": "AMZN",
    "microsoft": "MSFT",
    "nvidia": "NVDA",
    "meta": "META",
    "bitcoin": "BTC",
    "ethereum": "ETH",
}


def _normalise_symbol(raw: str) -> str:
    """Return an upper-case ticker for *raw* (which may be a company name)."""
    lower = raw.lower()
    return _SYMBOL_ALIAS.get(lower, raw.upper())


def parse_intent(message: str) -> dict:
    """Parse *message* and return a dict with keys:

    - ``intent`` — one of the INTENT_* constants
    - ``symbol`` — extracted ticker (may be None)
    - ``text``   — leftover free text (e.g. news snippet for sentiment)
    - ``raw``    — original message
    """
    msg_lower = message.lower()

    # --- intent detection (order matters: specific before general) ---
    portfolio_words = ("portfolio", "balance", "holdings", "position")
    sentiment_words = ("sentiment", "news", "feel", "opinion")
    buy_words = ("buy", "purchase", "long")
    sell_words = ("sell", "short", "exit")
    analyze_words = ("analyze", "analyse", "forecast", "predict",
                     "should i", "recommend", "outlook")

    if any(w in msg_lower for w in portfolio_words):
        intent = INTENT_PORTFOLIO
    elif any(w in msg_lower for w in sentiment_words):
        intent = INTENT_SENTIMENT
    elif any(w in msg_lower for w in buy_words):
        intent = INTENT_BUY
    elif any(w in msg_lower for w in sell_words):
        intent = INTENT_SELL
    elif any(w in msg_lower for w in analyze_words):
        intent = INTENT_ANALYZE
    else:
        intent = INTENT_UNKNOWN

    # --- symbol extraction ---
    symbol = None
    # 1. explicit uppercase ticker like $AAPL or AAPL
    ticker_match = re.search(r'\$?([A-Z]{2,6})', message)
    if ticker_match:
        candidate = ticker_match.group(1)
        if candidate.lower() in _KNOWN_SYMBOLS or len(candidate) <= 5:
            symbol = candidate

    # 2. known company/coin names
    if symbol is None:
        for alias in sorted(_SYMBOL_ALIAS.keys(), key=len, reverse=True):
            if alias in msg_lower:
                symbol = _SYMBOL_ALIAS[alias]
                break

    # --- free text (strip the symbol token so it reads naturally) ---
    text = message
    if symbol:
        text = re.sub(
            re.escape(symbol), "", text, flags=re.IGNORECASE
        ).strip(" ,:")

    return {
        "intent": intent,
        "symbol": symbol,
        "text": text,
        "raw": message,
    }
