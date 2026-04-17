# 💀 AJAY AI FUND

## Overview
AI-powered automated trading system with:
- RL Agent
- Orderbook AI
- Portfolio optimization
- Auto retraining
- **CONVA** — Conversational AI interface built for AI

## Run
```
pip install -r requirements.txt
python main.py
```

## CONVA — Built for AI
CONVA is the natural-language conversational front-end for the trading system.
It parses free-text queries, routes them to the right agent (sentiment,
forecaster, execution, portfolio), and returns human-readable responses.

```
python main.py conva
```

Example interactions:
```
You: Analyse AAPL for me
You: What is the sentiment for Tesla? News: Tesla reports record Q4 profits.
You: Buy EURUSD
You: Show my portfolio
```

CONVA is also importable as a Python module:
```python
from agents.conva import ConvaAgent

agent = ConvaAgent()
print(agent.chat("Should I buy TSLA?"))
```

## Dashboard
```
streamlit run dashboard/dashboard.py
```

## Warning
Use SAFE_MODE before real trading.
