const fs = require("fs")
const Papa = require("papaparse")

// -- EMA function (user-supplied) --
function EMA(prices, period) {
  const k = 2 / (period + 1)
  let ema = prices[0]
  return prices.map(price => {
    ema = price * k + ema * (1 - k)
    return ema
  })
}

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

    // --- EMA Integration ----
    // Single EMA (legacy)
    let emaPeriod = 14
    if (process.env.EMA_PERIOD && !isNaN(Number(process.env.EMA_PERIOD))) {
      emaPeriod = Number(process.env.EMA_PERIOD)
      if (emaPeriod < 1) emaPeriod = 1
    }
    const closeArray = df.map(row => row.close)
    let emaArray = []
    if (df.length < emaPeriod) {
      emaArray = Array(df.length).fill(null)
    } else {
      emaArray = Array(emaPeriod - 1)
        .fill(null)
        .concat(EMA(closeArray.slice(emaPeriod - 1), emaPeriod))
    }
    df.forEach((row, idx) => {
      row.ema = emaArray[idx]
    })
    console.log(`EMA Period: ${emaPeriod}`)
    console.log("First 5 EMA values:", emaArray.slice(0, 5))
    // --- End single EMA ----

    // --- Dual EMA integration ----
    let emaFastPeriod = 9 // Default
    let emaSlowPeriod = 21 // Default
    if (process.env.EMA_FAST_PERIOD && !isNaN(Number(process.env.EMA_FAST_PERIOD))) {
      emaFastPeriod = Math.max(1, Number(process.env.EMA_FAST_PERIOD))
    }
    if (process.env.EMA_SLOW_PERIOD && !isNaN(Number(process.env.EMA_SLOW_PERIOD))) {
      emaSlowPeriod = Math.max(1, Number(process.env.EMA_SLOW_PERIOD))
    }
    // Calculate EMA_fast
    let emaFastArray = []
    if (df.length < emaFastPeriod) {
      emaFastArray = Array(df.length).fill(null)
    } else {
      emaFastArray = Array(emaFastPeriod - 1)
        .fill(null)
        .concat(EMA(closeArray.slice(emaFastPeriod - 1), emaFastPeriod))
    }
    // Calculate EMA_slow
    let emaSlowArray = []
    if (df.length < emaSlowPeriod) {
      emaSlowArray = Array(df.length).fill(null)
    } else {
      emaSlowArray = Array(emaSlowPeriod - 1)
        .fill(null)
        .concat(EMA(closeArray.slice(emaSlowPeriod - 1), emaSlowPeriod))
    }
    // Assign both EMAs to dataframe
    df.forEach((row, idx) => {
      row.ema_fast = emaFastArray[idx]
      row.ema_slow = emaSlowArray[idx]
    })
    console.log(`EMA_fast Period: ${emaFastPeriod}, EMA_slow Period: ${emaSlowPeriod}`)
    if (df.length >= 5) {
      console.log("First 5 EMA_fast:", emaFastArray.slice(0, 5))
      console.log("First 5 EMA_slow:", emaSlowArray.slice(0, 5))
    }
    // --- End Dual EMA integration ----

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
      // EMA simple signal (optional): BUY if close > ema, SELL if close < ema (log only)
      if (row.ema !== null && !isNaN(row.ema)) {
        if (row.close > row.ema) {
          console.log(`[EMA] Index ${i}: BUY signal - close (${row.close}) > ema (${row.ema})`)
        } else if (row.close < row.ema) {
          console.log(`[EMA] Index ${i}: SELL signal - close (${row.close}) < ema (${row.ema})`)
        }
      }
    }
    // ---- Dual EMA crossover signals ----
    const emaCrossoverSignals = []
    for (let i = 0; i < df.length; i++) {
      const row = df[i]
      // Only assign signal when both EMAs are defined and valid
      if (row.ema_fast !== null && row.ema_slow !== null && !isNaN(row.ema_fast) && !isNaN(row.ema_slow)) {
        const type = row.ema_fast > row.ema_slow ? "BUY" : "SELL"
        emaCrossoverSignals.push({
          type,
          index: i,
          ema_fast: row.ema_fast,
          ema_slow: row.ema_slow,
          close: row.close
        })
        console.log(`[Dual EMA XOVER] Index ${i}: ${type} - fast (${row.ema_fast}), slow (${row.ema_slow}), close (${row.close})`)
      }
    }
    // Output the legacy and new signals for debug purposes
    for (const s of signals) {
      console.log(s)
    }
    console.log(`Dual EMA crossover signals generated: ${emaCrossoverSignals.length}`)
    setContext("signals", signals)
    setContext("emaCrossoverSignals", emaCrossoverSignals)
    console.log(`Technical Signal Generation step complete. Composite: ${signals.length}, Dual EMA: ${emaCrossoverSignals.length}`)
  } catch (e) {
    console.error("Technical Signal Generation error:", e)
    process.exit(1)
  }
})()
