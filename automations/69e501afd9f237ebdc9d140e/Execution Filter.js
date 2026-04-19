;(async () => {
  try {
    const analytics = getContext("orderflow_analytics")
    if (!analytics || typeof analytics !== "object") {
      throw new Error("No orderflow_analytics found in context.")
    }

    function executionFilter(spread, pressure) {
      if (typeof spread !== "number" || isNaN(spread)) {
        console.warn(`[filter] Invalid spread: ${spread}. Defaulting to HOLD.`)
        return "HOLD"
      }
      if (spread > 0.0003) {
        return "NO TRADE"
      }
      if (pressure === "BUY" || pressure === "SELL") {
        return pressure
      }
      return "HOLD"
    }

    // Gold filter
    const gold = analytics.gold || {}
    const goldRecommendation = executionFilter(gold.spread, gold.pressure)
    console.log(`[filter] Gold: spread=${gold.spread}, pressure=${gold.pressure} => ${goldRecommendation}`)

    // USDJPY filter
    const usdjpy = analytics.usdjpy || {}
    const usdjpyRecommendation = executionFilter(usdjpy.spread, usdjpy.pressure)
    console.log(`[filter] USDJPY: spread=${usdjpy.spread}, pressure=${usdjpy.pressure} => ${usdjpyRecommendation}`)

    const result = {
      gold: goldRecommendation,
      usdjpy: usdjpyRecommendation
    }
    setContext("execution_filter_result", result)
    console.log("[step] Execution Filter: Result=", result)

    // ---- AI SIGNAL STUB INJECTION ----
    // For demo/testing: produce a static AI signal for each asset and set in context. Replace later with real model inference.
    const ai_signal = {
      gold: "BUY", // DEMO: Change to "SELL", "NEUTRAL", etc as needed
      usdjpy: "SELL" // DEMO: Change as needed
    }
    setContext("ai_signal", ai_signal)
    console.log("[step] AI Signal STUB injected in context:", ai_signal)
    // ---- END AI SIGNAL STUB ----

    // ---- ORDERBOOK SIGNAL STUB INJECTION ----
    const orderbook_signal = {
      gold: gold.pressure || "NEUTRAL",
      usdjpy: usdjpy.signal || "NO_CHANGE"
    }
    setContext("orderbook_signal", orderbook_signal)
    console.log("[Execution Filter] Injected stub orderbook_signal:", orderbook_signal)
    // ---- END ORDERBOOK SIGNAL STUB ----
  } catch (e) {
    console.error("[step] Error in Execution Filter:", e)
    process.exit(1)
  }
})()
