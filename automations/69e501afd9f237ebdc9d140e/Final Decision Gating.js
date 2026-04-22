// Final Decision Gating - Weighted (confidence-based) aggregation of AI and Orderbook signals per asset
try {
  // Fetch context: AI & Orderbook signals, each expected as { asset: { signal: 'BUY'/'SELL', confidence: number }, ... }
  const aiSignals = getContext("ai_signal") || {}
  const orderbookSignals = getContext("orderbook_signal") || {}

  // Defensive: Asset set = union of assets with both AI & Orderbook entries
  const allAssets = Array.from(new Set([...Object.keys(aiSignals), ...Object.keys(orderbookSignals)]))

  const results = {}

  for (const asset of allAssets) {
    // Try to get signal+confidence structure. Fallback: if string, treat as simple signal w/ confidence = 1.
    const ai = aiSignals[asset]
    const ob = orderbookSignals[asset]

    let aiSignal, aiConf
    if (ai && typeof ai === "object" && ai.signal && typeof ai.confidence === "number") {
      aiSignal = ai.signal.toUpperCase()
      aiConf = ai.confidence
    } else if (typeof ai === "string") {
      aiSignal = ai.toUpperCase()
      aiConf = 1
    } else {
      aiSignal = "HOLD"
      aiConf = 0
    }

    let obSignal, obConf
    if (ob && typeof ob === "object" && ob.signal && typeof ob.confidence === "number") {
      obSignal = ob.signal.toUpperCase()
      obConf = ob.confidence
    } else if (typeof ob === "string") {
      obSignal = ob.toUpperCase()
      obConf = 1
    } else {
      obSignal = "HOLD"
      obConf = 0
    }

    // Aggregate: sum BUY confidence, SELL confidence
    let buyScore = 0,
      sellScore = 0
    if (aiSignal === "BUY") buyScore += aiConf
    else if (aiSignal === "SELL") sellScore += aiConf
    if (obSignal === "BUY") buyScore += obConf
    else if (obSignal === "SELL") sellScore += obConf

    // Decision logic
    let action
    if (buyScore > sellScore) action = "BUY"
    else if (sellScore > buyScore) action = "SELL"
    else action = "HOLD"

    // Detailed diagnostic logging
    console.log(`[Final Decision Gating][${asset}] AI: ${aiSignal} (${aiConf}), Orderbook: ${obSignal} (${obConf}) | BUY score: ${buyScore}, SELL score: ${sellScore} => ACTION: ${action}`)

    results[asset] = {
      action,
      ai: { signal: aiSignal, confidence: aiConf },
      orderbook: { signal: obSignal, confidence: obConf },
      buyScore,
      sellScore
    }
  }

  setContext("final_decision", results)
  console.log("[Final Decision Gating] FINAL DECISIONS:", results)
} catch (e) {
  console.error("[Final Decision Gating] Error:", e)
  process.exit(1)
}
