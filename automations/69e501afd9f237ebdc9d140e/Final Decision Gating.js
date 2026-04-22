// Final Decision Gating - Weighted (confidence-based) aggregation of AI and Orderbook signals per asset, with adaptive scaling
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

    // Calculate scaling factor for this asset
    // If a key signal (here: Orderbook) is missing/conf=0, reduce scale, otherwise full size
    let rationale, scale
    if (obConf === 0 || obSignal === "HOLD" || obSignal === "MISSING") {
      scale = 0.5
      rationale = "Orderbook signal missing or weak: executing smaller position (scale=0.5)"
    } else {
      scale = 1.0
      rationale = "All key signals present: executing full position (scale=1.0)"
    }

    // Detailed diagnostic logging, with rationale
    console.log(`[Final Decision Gating][${asset}] AI: ${aiSignal} (${aiConf}), Orderbook: ${obSignal} (${obConf}) | BUY score: ${buyScore}, SELL score: ${sellScore} => ACTION: ${action} | SCALE: ${scale} (${rationale})`)

    results[asset] = {
      action,
      ai: { signal: aiSignal, confidence: aiConf },
      orderbook: { signal: obSignal, confidence: obConf },
      buyScore,
      sellScore,
      scale, // Propagate the scaling factor
      rationale // Propagate rationale for transparency
    }
  }

  setContext("final_decision", results)
  console.log("[Final Decision Gating] FINAL DECISIONS (with scale):", results)
} catch (e) {
  console.error("[Final Decision Gating] Error:", e)
  process.exit(1)
}
