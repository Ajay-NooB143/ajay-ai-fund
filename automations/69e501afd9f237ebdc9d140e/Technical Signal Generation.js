const fs = require("fs")
const Papa = require("papaparse")

// === (existing indicator/calculation functions remain here, but ensure RSI function is defined) ===
function RSI(closes, period) {
  let rsis = Array(closes.length).fill(null)
  if (closes.length <= period) return rsis
  let gains = 0,
    losses = 0
  for (let i = 1; i <= period; i++) {
    const change = closes[i] - closes[i - 1]
    if (change > 0) gains += change
    else losses -= change
  }
  gains /= period
  losses /= period
  let rs = losses === 0 ? 100 : gains / losses
  rsis[period] = 100 - 100 / (1 + rs)
  for (let i = period + 1; i < closes.length; i++) {
    const change = closes[i] - closes[i - 1]
    let gain = change > 0 ? change : 0
    let loss = change < 0 ? -change : 0
    gains = (gains * (period - 1) + gain) / period
    losses = (losses * (period - 1) + loss) / period
    rs = losses === 0 ? 100 : gains / losses
    rsis[i] = 100 - 100 / (1 + rs)
  }
  return rsis
}

// === EMA Calculation ===
function EMA(closes, period) {
  let emas = Array(closes.length).fill(null)
  if (closes.length < period) return emas
  let multiplier = 2 / (period + 1)
  // Simple average for first EMA value
  let sum = 0
  for (let i = 0; i < period; i++) sum += closes[i]
  emas[period - 1] = sum / period
  for (let i = period; i < closes.length; i++) {
    emas[i] = (closes[i] - emas[i - 1]) * multiplier + emas[i - 1]
  }
  return emas
}

;(async () => {
  try {
    // === [NEW CODE] Read and parse OHLCV CSV before any signal calculation ===
    let ohlcvArray = []
    const ohlcvPath = process.env.OHLCV_CSV_PATH
    if (!ohlcvPath) {
      console.error("OHLCV_CSV_PATH environment variable not set.")
      process.exit(1)
    }
    let fileRaw = null
    try {
      fileRaw = fs.readFileSync(ohlcvPath, "utf8")
    } catch (err) {
      console.error("Error reading OHLCV CSV file:", err)
      process.exit(1)
    }
    const parsed = Papa.parse(fileRaw, { header: true, skipEmptyLines: true })
    if (!parsed.data || !Array.isArray(parsed.data) || parsed.data.length === 0) {
      console.error("Papaparse failed or CSV has no valid rows.")
      process.exit(1)
    }
    ohlcvArray = parsed.data.map(row => {
      // Robust type conversion for OHLCV fields
      return {
        ...row,
        open: Number(row.open),
        high: Number(row.high),
        low: Number(row.low),
        close: Number(row.close),
        volume: Number(row.volume)
        // Add any additional fields as necessary
      }
    })
    console.log(`Parsed OHLCV: ${ohlcvArray.length} rows from '${ohlcvPath}'`)

    const df = ohlcvArray // parsed data array

    // RSI Calculation
    let rsiPeriod = 14
    if (process.env.RSI_PERIOD && !isNaN(Number(process.env.RSI_PERIOD))) {
      rsiPeriod = Math.max(1, Number(process.env.RSI_PERIOD))
    }
    let rsiArray = []
    if (df.length < rsiPeriod + 1) {
      rsiArray = Array(df.length).fill(null)
    } else {
      rsiArray = RSI(
        df.map(row => row.close),
        rsiPeriod
      )
    }
    df.forEach((row, idx) => {
      row.rsi = rsiArray[idx]
    })
    console.log(`RSI Period: ${rsiPeriod}`)
    console.log("First 10 RSI values:", rsiArray.slice(0, 10))

    // --- EMA Calculation ---
    let emaPeriod = 14
    if (process.env.EMA_PERIOD && !isNaN(Number(process.env.EMA_PERIOD))) {
      emaPeriod = Math.max(1, Number(process.env.EMA_PERIOD))
    }
    let emaArray = []
    if (df.length < emaPeriod) {
      emaArray = Array(df.length).fill(null)
    } else {
      emaArray = EMA(
        df.map(row => row.close),
        emaPeriod
      )
    }
    df.forEach((row, idx) => {
      row.ema = emaArray[idx]
    })
    console.log(`EMA Period: ${emaPeriod}`)
    console.log("First 10 EMA:", emaArray.slice(0, 10))

    // --- Signal assignment as per user request ---
    let buyCount = 0,
      sellCount = 0,
      holdCount = 0
    df.forEach(row => {
      row.signal = null
      if (row.ema !== null && !isNaN(row.ema) && row.rsi !== null && !isNaN(row.rsi) && row.close !== null && !isNaN(row.close)) {
        if (row.close > row.ema && row.rsi < 30) {
          row.signal = "BUY"
          buyCount++
        } else if (row.close < row.ema && row.rsi > 70) {
          row.signal = "SELL"
          sellCount++
        } else {
          row.signal = "HOLD"
          holdCount++
        }
      }
    })
    console.log(`Signal assignment complete. BUY: ${buyCount}, SELL: ${sellCount}, HOLD/Other: ${holdCount}`)

    setContext("technical_signals", df)
    console.log("technical_signals context set with full indicator results.")
  } catch (e) {
    console.error("Technical Signal Generation error:", e)
    process.exit(1)
  }
})()
