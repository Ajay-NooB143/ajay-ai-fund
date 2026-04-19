;(async () => {
  try {
    // --- DEMO DATA (Replace with real API/env-source as needed) ---
    // Gold (XAUUSD)
    const xauusd_bid = 2392.47 // example fixed bid
    const xauusd_ask = 2392.95 // example fixed ask

    // USDJPY
    const usdjpy_spot = 154.18 // current spot example
    const usdjpy_previous_spot = 153.85 // yesterday's spot example

    // Set these required context keys so that analytics step can run
    setContext("xauusd_bid", xauusd_bid)
    setContext("xauusd_ask", xauusd_ask)
    setContext("usdjpy_spot", usdjpy_spot)
    setContext("usdjpy_previous_spot", usdjpy_previous_spot)

    console.log("[step] Fetch Market Data (DEMO values set):")
    console.log(`  xauusd_bid: ${xauusd_bid}\n  xauusd_ask: ${xauusd_ask}\n  usdjpy_spot: ${usdjpy_spot}\n  usdjpy_previous_spot: ${usdjpy_previous_spot}`)
  } catch (e) {
    console.error("[step] Error in Fetch Market Data:", e)
    process.exit(1)
  }
})()
