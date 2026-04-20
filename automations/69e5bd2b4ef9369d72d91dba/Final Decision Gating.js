// Final Decision Gating - Implements Python execution_engine logic robustly against orderflow structure (flat or nested)
try {
  // Fetch context: AI signals, orderflow analytics (flat), and orderbook signal (if any)
  const aiSignals = getContext("ai_signal") || { gold: "BUY", usdjpy: "SELL" }
  const orderflow = getContext("orderflow_analytics")
  if (!orderflow) throw new Error("Missing 'orderflow_analytics' in context.")

  // Robust shape detection for orderflow (can be flat or nested)
  const hasNestedGold = orderflow.gold && typeof orderflow.gold === "object"
  const hasNestedUSDJPY = orderflow.usdjpy && typeof orderflow.usdjpy === "object"

  // Compose values for each asset regardless of structure
  function getOF(asset) {
    // Prefer nested (legacy), fall back to flat keys used upstream
    if (orderflow[asset] && typeof orderflow[asset] === "object") return orderflow[asset]
    // Try flat keys: e.g., last_spread, last_pressure
    return {
      spread: orderflow[`last_spread`],
      pressure: orderflow[`last_pressure`],
      signal: orderflow[`last_signal`] || undefined
    }
  }

  // Orderbook signal stub; in practice, inject this upstream
  let orderbook = getContext("orderbook_signal")
  if (!orderbook) {
    orderbook = {
      gold: getOF("gold").pressure || "NEUTRAL",
      usdjpy: getOF("usdjpy").signal || "NO_CHANGE"
    }
    console.warn("[Final Decision Gating] No orderbook_signal in context, using fallback pressure/signals.")
  }

  // Python-equivalent execution_engine, now robust to missing or malformed orderflow
  function executionEngine(ai_signal, of, ob_signal, assetLabel = "") {
    if (!of || typeof of !== "object") {
      console.warn(`[engine:${assetLabel}] Invalid orderflow object:`, of)
      return "FILTERED"
    }
    const spread = of.spread
    if (typeof spread !== "number" || isNaN(spread)) {
      console.warn(`[engine:${assetLabel}] Invalid spread:`, spread)
      return "FILTERED"
    }
    if (spread > 0.0003) return "BLOCKED"
    if (ai_signal === "BUY" && ob_signal === "BUY") return "BUY"
    if (ai_signal === "SELL" && ob_signal === "SELL") return "SELL"
    return "FILTERED"
  }

  const goldOF = getOF("gold")
  const usdjpyOF = getOF("usdjpy")
  const goldResult = executionEngine(aiSignals.gold, goldOF, orderbook.gold, "gold")
  const usdjpyResult = executionEngine(aiSignals.usdjpy, usdjpyOF, orderbook.usdjpy, "usdjpy")

  setContext("final_decision", { gold: goldResult, usdjpy: usdjpyResult })
  // Debug/audit log
  console.log("[Final Decision Gating] aiSignals:", aiSignals)
  console.log("[Final Decision Gating] orderflow:", orderflow)
  console.log("[Final Decision Gating] goldOF:", goldOF)
  console.log("[Final Decision Gating] usdjpyOF:", usdjpyOF)
  console.log("[Final Decision Gating] orderbook:", orderbook)
  console.log("[Final Decision Gating] FINAL:", { gold: goldResult, usdjpy: usdjpyResult })
} catch (e) {
  console.error("[Final Decision Gating] Error:", e)
  process.exit(1)
}
