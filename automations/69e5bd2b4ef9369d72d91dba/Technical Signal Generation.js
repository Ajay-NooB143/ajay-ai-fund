const fs = require("fs")
const Papa = require("papaparse")

;(async () => {
  try {
    // 1. Validate and read environment variable for OHLCV CSV path
    const csvPath = process.env.OHLCV_CSV_PATH
    if (!csvPath) {
      throw new Error("Missing environment variable: OHLCV_CSV_PATH")
    }
    if (!fs.existsSync(csvPath)) {
      throw new Error(`OHLCV data file not found at: ${csvPath}`)
    }

    // 2. Read CSV file
    const csvData = fs.readFileSync(csvPath, "utf8")
    // 3. Parse CSV
    const parsed = Papa.parse(csvData, {
      header: true,
      skipEmptyLines: true,
      dynamicTyping: true
    })

    let df = parsed.data
    if (!Array.isArray(df) || df.length === 0) {
      throw new Error("CSV file is empty or malformed")
    }

    // Ensure required columns exist
    const requiredCols = ["time", "open", "high", "low", "close", "volume"]
    for (const col of requiredCols) {
      if (!Object.hasOwn(df[0], col)) {
        throw new Error(`Missing required column: ${col}`)
      }
    }

    // Numeric conversions for all relevant fields
    df = df.map(row => {
      for (const col of requiredCols.slice(1)) {
        row[col] = Number(row[col])
      }
      return row
    })

    // VWAP calculation
    let cumulativePV = 0,
      cumulativeVol = 0
    df = df.map((row, idx) => {
      cumulativePV += row.close * row.volume
      cumulativeVol += row.volume
      row.vwap = cumulativeVol !== 0 ? cumulativePV / cumulativeVol : null
      return row
    })

    // FVG calculation: fvg_up and fvg_down
    for (let i = 2; i < df.length; i++) {
      df[i].fvg_up = df[i - 1].low > df[i - 2].high ? 1 : 0
      df[i].fvg_down = df[i - 1].high < df[i - 2].low ? 1 : 0
    }
    // fill first two
    if (df.length >= 2) {
      df[0].fvg_up = df[0].fvg_down = df[1].fvg_up = df[1].fvg_down = 0
    }

    // Order Block calculation
    for (let i = 1; i < df.length; i++) {
      df[i].bull_ob = df[i - 1].close < df[i - 1].open && df[i].close > df[i - 1].high ? 1 : 0
      df[i].bear_ob = df[i - 1].close > df[i - 1].open && df[i].close < df[i - 1].low ? 1 : 0
    }
    if (df.length >= 1) {
      df[0].bull_ob = df[0].bear_ob = 0
    }

    // Liquidity sweep calculation
    for (let i = 5; i < df.length; i++) {
      let highestPrev5 = Math.max(...df.slice(i - 5, i).map(x => x.high))
      let lowestPrev5 = Math.min(...df.slice(i - 5, i).map(x => x.low))
      df[i].sweep_high = df[i].high > highestPrev5 ? 1 : 0
      df[i].sweep_low = df[i].low < lowestPrev5 ? 1 : 0
    }
    for (let i = 0; i < 5 && i < df.length; i++) {
      df[i].sweep_high = df[i].sweep_low = 0
    }

    // Signal generation
    const signals = []
    for (let i = 3; i < df.length; i++) {
      const row = df[i]
      // BUY CONDITIONS
      if (row.close > row.vwap && row.sweep_low === 1 && row.fvg_up === 1 && row.bull_ob === 1) {
        const entry = row.close
        const sl = df[i - 1].low
        const tp = entry + (entry - sl) * 2
        signals.push({
          type: "BUY",
          price: entry,
          sl,
          tp,
          index: i
        })
      }
      // SELL CONDITIONS
      else if (row.close < row.vwap && row.sweep_high === 1 && row.fvg_down === 1 && row.bear_ob === 1) {
        const entry = row.close
        const sl = df[i - 1].high
        const tp = entry - (sl - entry) * 2
        signals.push({
          type: "SELL",
          price: entry,
          sl,
          tp,
          index: i
        })
      }
    }

    // Output the signals for debug purposes
    for (const s of signals) {
      console.log(s)
    }
    // Store signals in context for downstream
    setContext("signals", signals)
    console.log(`Technical Signal Generation step complete. Signals generated: ${signals.length}`)
  } catch (e) {
    console.error("Technical Signal Generation error:", e)
    process.exit(1)
  }
})()
