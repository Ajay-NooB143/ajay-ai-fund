class OrderFlow {
  constructor() {
    this.bid = 0.0
    this.ask = 0.0
  }
  update(bid, ask) {
    this.bid = typeof bid === "number" ? bid : 0.0
    this.ask = typeof ask === "number" ? ask : 0.0
  }
  spread() {
    return this.ask - this.bid
  }
  midPrice() {
    return (this.ask + this.bid) / 2
  }
  pressure() {
    if (this.ask > this.bid) return "BUY"
    else if (this.bid > this.ask) return "SELL"
    return "NEUTRAL"
  }
}

;(async () => {
  try {
    // Read updated context: Gold bid/ask/spot, USDJPY spot only (since no bid/ask for forex)
    const xauusd_bid = getContext("xauusd_bid")
    const xauusd_ask = getContext("xauusd_ask")
    const usdjpy_spot = getContext("usdjpy_spot")
    const usdjpy_previous_spot = getContext("usdjpy_previous_spot")

    // Defensive: If context keys missing, abort
    if (typeof xauusd_bid !== "number" || typeof xauusd_ask !== "number" || typeof usdjpy_spot !== "number" || typeof usdjpy_previous_spot !== "number") {
      throw new Error("Missing context keys for order flow analytics. Check upstream market data step and logs.")
    }

    // Gold Order Flow (true bid/ask)
    const goldFlow = new OrderFlow()
    goldFlow.update(xauusd_bid, xauusd_ask)
    const gold_spread = goldFlow.spread()
    const gold_mid = goldFlow.midPrice()
    const gold_pressure = goldFlow.pressure()

    // USDJPY "Order Flow" (no bid/ask, use spot/mid as both)
    const usdjpyFlow = new OrderFlow()
    usdjpyFlow.update(usdjpy_spot, usdjpy_spot) // pressure will always be NEUTRAL!
    const usdjpy_spread = usdjpyFlow.spread()
    const usdjpy_mid = usdjpyFlow.midPrice()
    const usdjpy_pressure = usdjpyFlow.pressure() // always NEUTRAL

    // Include USDJPY momentum (today vs yesterday spot)
    const usdjpy_momentum = usdjpy_spot - usdjpy_previous_spot
    const usdjpy_signal = usdjpy_momentum > 0 ? "USD_STRENGTH" : usdjpy_momentum < 0 ? "USD_WEAKNESS" : "NO_CHANGE"

    const out = {
      gold: {
        bid: xauusd_bid,
        ask: xauusd_ask,
        spread: gold_spread,
        mid: gold_mid,
        pressure: gold_pressure
      },
      usdjpy: {
        spot: usdjpy_spot,
        prev_spot: usdjpy_previous_spot,
        spread: usdjpy_spread,
        mid: usdjpy_mid,
        pressure: usdjpy_pressure,
        momentum: usdjpy_momentum,
        signal: usdjpy_signal
      }
    }
    setContext("orderflow_analytics", out)
    console.log("[step] Order Flow Analytics:", out)
  } catch (e) {
    console.error("[step] Error in Order Flow Analytics (updated):", e)
    process.exit(1)
  }
})()
