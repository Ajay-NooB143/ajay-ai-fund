CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    symbol TEXT,
    side TEXT,
    qty FLOAT,
    price FLOAT,
    pnl FLOAT,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS features (
    id SERIAL PRIMARY KEY,
    rsi FLOAT,
    macd FLOAT,
    volatility FLOAT,
    outcome INT
);
