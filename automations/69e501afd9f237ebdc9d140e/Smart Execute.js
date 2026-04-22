// This step performs smart order execution: splits trades into multiple parts, applies delays, and simulates orders (stub). Now supports adaptive position size via scaling factor.
try {
  // --- Configurable params ---
  const BASE_LOT_SIZE = 10 // Unscaled base size per asset
  const EXEC_PARTS = 5 // Split each order into this many parts
  const EXEC_DELAY_MS = 200 // Delay between parts in ms (Python: 0.2s)

  // Access final trading decision (from gating logic)
  const finalDecision = getContext("final_decision")
  if (!finalDecision || typeof finalDecision !== "object") {
    throw new Error("Missing or invalid final_decision in context.")
  }

  // Define assets and map side based on decision
  const assets = [
    { symbol: "gold", readable: "Gold", decision: finalDecision.gold },
    { symbol: "usdjpy", readable: "USDJPY", decision: finalDecision.usdjpy }
  ]

  for (const asset of assets) {
    const { symbol, readable, decision } = asset
    if (!decision || typeof decision !== "object") {
      console.log(`[Smart Execute] ${readable}: Missing final decision object, skipping.`)
      continue
    }
    const { action, scale = 1.0, rationale } = decision
    // Only proceed for real trade signals (BUY or SELL)
    if (action === "BUY" || action === "SELL") {
      // Calculate scaled lot size; defensive: minimum 1, rounded to 4 decimals
      const scaledLot = Math.max(1, +(BASE_LOT_SIZE * scale).toFixed(4))
      const splitLot = +(scaledLot / EXEC_PARTS).toFixed(4)

      // Log trade details and scaling rationale
      console.log(`[Smart Execute] ${readable} Trade: ${action}, BASE_Lot: ${BASE_LOT_SIZE}, SCALE: ${scale}, Used Lot: ${scaledLot}, Split: ${splitLot} x ${EXEC_PARTS}`)
      if (typeof rationale === "string") {
        console.log(`[Smart Execute] Scaling rationale: ${rationale}`)
      }
      for (let i = 0; i < EXEC_PARTS; i++) {
        safe_order(symbol, splitLot, action, i + 1)
        if (i < EXEC_PARTS - 1) {
          // Await between each part except last
          Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, EXEC_DELAY_MS) // Node.js 19+ compliant pause
        }
      }
    } else {
      // Log if blocked/filtered/hold
      console.log(`[Smart Execute] ${readable}: No eligible trade (decision = ${action})`)
    }
  }

  // Simulated order executor (stub)
  function safe_order(symbol, lot, side, partNum) {
    console.log(`[safe_order] Executing part ${partNum} for ${symbol.toUpperCase()}: Lot=${lot}, Side=${side}`)
    // In a real implementation, connect to a broker/trading API here.
    // For now, just log the simulated order.
  }
} catch (e) {
  console.error("[Smart Execute] Error:", e)
  process.exit(1)
}
