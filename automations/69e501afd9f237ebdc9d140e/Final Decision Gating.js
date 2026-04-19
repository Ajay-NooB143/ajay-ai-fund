// Final Decision Gating - Implements Python execution_engine logic based on ai_signal, orderflow, orderbook
try {
  // Fetch needed context: AI signals (should be passed/set by upstream step in real deployment),
  // orderflow analytics (for spread), and an orderbook/signal (stub if missing)

  const aiSignals = getContext("ai_signal") || { gold: "BUY", usdjpy: "SELL" } // REPLACE with real upstream AI outputs when available
  const orderflow = getContext("orderflow_analytics")
  if (!orderflow) throw new Error("Missing 'orderflow_analytics' in context.")

  // Orderbook signal stub; in practice, inject this upstream
  let orderbook = getContext("orderbook_signal")
  if (!orderbook) {
    // Fallback - default to match pressure, can be replaced with real orderbook signal generator per asset
    orderbook = {
      gold: orderflow.gold.pressure || "NEUTRAL",
      usdjpy: orderflow.usdjpy.signal || "NO_CHANGE"
    }
    console.warn("[Final Decision Gating] No orderbook_signal in context, using fallback pressure/signals.")
  }

  // Define Python-equivalent execution_engine logic for each asset
  function executionEngine(ai_signal, of, ob_signal) {
    const spread = of.spread
    if (typeof spread !== "number" || isNaN(spread)) {
      console.warn(`[engine] Invalid spread: ${spread}`)
      return "FILTERED"
    }
    if (spread > 0.0003) return "BLOCKED"
    if (ai_signal === "BUY" && ob_signal === "BUY") return "BUY"
    if (ai_signal === "SELL" && ob_signal === "SELL") return "SELL"
    return "FILTERED"
  }

  const goldResult = executionEngine(aiSignals.gold, orderflow.gold, orderbook.gold)
  const usdjpyResult = executionEngine(aiSignals.usdjpy, orderflow.usdjpy, orderbook.usdjpy)

  setContext("final_decision", { gold: goldResult, usdjpy: usdjpyResult })

  // Audit log for debugging and traceability
  console.log("[Final Decision Gating] aiSignals:", aiSignals)
  console.log("[Final Decision Gating] orderflow:", orderflow)
  console.log("[Final Decision Gating] orderbook:", orderbook)
  console.log("[Final Decision Gating] FINAL:", { gold: goldResult, usdjpy: usdjpyResult })
} catch (e) {
  console.error("[Final Decision Gating] Error:", e)
  process.exit(1)
}
