const fs = require("fs")

;(async () => {
  try {
    // Order Flow Analytics Step: Computes spread, midprice, pressure, etc. from OHLCV data

    // 1. Try to get OHLCV data array from context (preferred), else load from CSV as fallback
    let ohlcvData = getContext("ohlcv_data")
    if (!ohlcvData || !Array.isArray(ohlcvData) || ohlcvData.length === 0) {
      // Fallback to file read (if previous code diverges from context model)
      const csvPath = process.env.OHLCV_CSV_PATH
      if (!csvPath || !fs.existsSync(csvPath)) {
        throw new Error("Order Flow Analytics cannot find OHLCV data in context or at file path: " + csvPath)
      }
      const csvData = fs.readFileSync(csvPath, "utf8")
      const rows = csvData.split("\n").slice(1).filter(Boolean)
      ohlcvData = rows.map(line => {
        // time,open,high,low,close,volume
        const [time, open, high, low, close, volume] = line.split(",")
        return {
          time: +time,
          open: parseFloat(open),
          high: parseFloat(high),
          low: parseFloat(low),
          close: parseFloat(close),
          volume: parseFloat(volume)
        }
      })
    }

    if (!ohlcvData || !Array.isArray(ohlcvData) || ohlcvData.length < 2) {
      throw new Error("Order Flow Analytics: insufficient OHLCV data to compute analytics")
    }

    // 2. Compute spread, midprice, pressure for last N bars (demo logic; production can extend to more stats)
    const analytics = []
    for (let i = 1; i < ohlcvData.length; i++) {
      const prev = ohlcvData[i - 1]
      const curr = ohlcvData[i]
      const spread = Math.abs(curr.close - curr.open)
      const midprice = (curr.high + curr.low) / 2
      const delta_vol = curr.volume - prev.volume
      const pressure = delta_vol / (curr.volume !== 0 ? curr.volume : 1) // crude measure, refine as needed
      analytics.push({
        time: curr.time,
        spread,
        midprice,
        pressure,
        close: curr.close,
        open: curr.open,
        volume: curr.volume
      })
    }

    // 3. Optional aggregate metrics (sums, means, etc. for downstream filters)
    const last = analytics[analytics.length - 1]

    // ---- MULTI-ASSET CONTEXT STRUCTURE FOR DOWNSTREAM COMPATIBILITY ----
    const goldAnalytics = {
      spread: last.spread,
      pressure: last.pressure,
      midprice: last.midprice,
      close: last.close,
      open: last.open,
      volume: last.volume,
      analytics_slice: analytics.slice(-10)
    }
    const usdjpyAnalytics = {
      spread: last.spread,
      pressure: last.pressure,
      midprice: last.midprice,
      close: last.close,
      open: last.open,
      volume: last.volume,
      analytics_slice: analytics.slice(-10)
    }

    // Demo: Copy BTCUSDT analytics as stubs for both gold and usdjpy
    const orderflow_analytics = {
      gold: goldAnalytics,
      usdjpy: usdjpyAnalytics,
      // Optionally, keep the root summary for debug (legacy)
      last_spread: last.spread,
      last_midprice: last.midprice,
      last_pressure: last.pressure,
      analytics_slice: analytics.slice(-10)
    }

    console.log("[Order Flow Analytics] Using BTCUSDT analytics as demo stub for gold and usdjpy. Replace with real market data for production.")

    setContext("orderflow_analytics", orderflow_analytics)
    console.log("Order Flow Analytics set in context:", orderflow_analytics)
  } catch (e) {
    console.error("Order Flow Analytics error:", e)
    process.exit(1)
  }
})()
