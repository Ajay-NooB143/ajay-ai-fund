// Final Decision Gating - Implements score-based gating based on ai_signal, orderflow, orderbook
try {
  // Fetch context: AI signals, orderflow analytics, orderbook signal
  const aiSignals = getContext("ai_signal") || { gold: "BUY", usdjpy: "SELL" }
  const orderflow = getContext("orderflow_analytics")
  if (!orderflow) throw new Error("Missing 'orderflow_analytics' in context.")

  let orderbook = getContext("orderbook_signal")
  if (!orderbook) {
    orderbook = {
      gold: orderflow.gold.pressure || "NEUTRAL",
      usdjpy: orderflow.usdjpy.signal || "NO_CHANGE"
    }
    console.warn("[Final Decision Gating] No orderbook_signal in context, using fallback pressure/signals.")
  }

  // Map signal string to +1/-1, otherwise 0
  function signalToNum(signal) {
    if (!signal || typeof signal !== "string") return 0
    const s = signal.toUpperCase()
    if (s === "BUY") return 1
    if (s === "SELL") return -1
    return 0
  }

  // For each asset, sum the three signals
  const assets = Object.keys(aiSignals).filter(a => orderflow[a] && orderbook[a])
  const results = {}

  for (const asset of assets) {
    const ai = aiSignals[asset]
    const of = orderflow[asset]?.signal // orderflow step should pass a signal (BUY/SELL)
    const ob = orderbook[asset]

    const aiNum = signalToNum(ai)
    const ofNum = signalToNum(of)
    const obNum = signalToNum(ob)
    const score = aiNum + ofNum + obNum

    let action = "FILTER"
    if (score === 2 || score === 3) action = "BUY"
    else if (score === -2 || score === -3) action = "SELL"

    // Emit log for traceability
    console.log(`[Final Decision Gating][${asset}] Signals => AI: ${ai} (${aiNum}), Orderflow: ${of} (${ofNum}), Orderbook: ${ob} (${obNum}), Score: ${score}, ACTION: ${action}`)

    results[asset] = action
  }

  setContext("final_decision", results)
  console.log("[Final Decision Gating] FINAL DECISIONS:", results)
} catch (e) {
  console.error("[Final Decision Gating] Error:", e)
  process.exit(1)
}
