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

// === MACD Calculation ===
function MACD(closes, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
  const emaFast = EMA(closes, fastPeriod)
  const emaSlow = EMA(closes, slowPeriod)
  let macd = Array(closes.length).fill(null)
  for (let i = 0; i < closes.length; i++) {
    if (emaFast[i] !== null && emaSlow[i] !== null) {
      macd[i] = emaFast[i] - emaSlow[i]
    } else {
      macd[i] = null
    }
  }
  const macdValid = macd.map(v => (v !== null ? v : 0))
  const signal = EMA(macdValid, signalPeriod)
  return { macd, signal }
}

// === Support/Resistance Detection ===
function detectLevels(df) {
  let levels = []
  for (let i = 2; i < df.length - 2; i++) {
    const low = df[i].low
    const prevLow = df[i - 1].low
    const nextLow = df[i + 1].low
    const high = df[i].high
    const prevHigh = df[i - 1].high
    const nextHigh = df[i + 1].high
    if (low < prevLow && low < nextLow) {
      levels.push({ type: "support", value: low, idx: i })
    }
    if (high > prevHigh && high > nextHigh) {
      levels.push({ type: "resistance", value: high, idx: i })
    }
  }
  return levels
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
    const closes = df.map(row => row.close)

    // RSI Calculation
    let rsiPeriod = 14
    if (process.env.RSI_PERIOD && !isNaN(Number(process.env.RSI_PERIOD))) {
      rsiPeriod = Math.max(1, Number(process.env.RSI_PERIOD))
    }
    let rsiArray = []
    if (df.length < rsiPeriod + 1) {
      rsiArray = Array(df.length).fill(null)
    } else {
      rsiArray = RSI(closes, rsiPeriod)
    }
    df.forEach((row, idx) => {
      row.rsi = rsiArray[idx]
    })
    console.log(`RSI Period: ${rsiPeriod}`)
    console.log("First 10 RSI values:", rsiArray.slice(0, 10))

    // --- EMA20 and EMA50 Calculation ---
    let ema20 = EMA(closes, 20)
    let ema50 = EMA(closes, 50)
    df.forEach((row, idx) => {
      row.ema20 = ema20[idx]
      row.ema50 = ema50[idx]
    })
    console.log("EMA20/EMA50 calculated. First few:", ema20.slice(0, 5), ema50.slice(0, 5))

    // --- MACD Calculation ---
    let { macd, signal } = MACD(closes, 12, 26, 9)
    df.forEach((row, idx) => {
      row.macd = macd[idx]
      row.signal = signal[idx]
    })
    console.log("MACD & Signal lines calculated. Last 5 values:", macd.slice(-5), signal.slice(-5))

    // --- Support/Resistance Level Detection ---
    const levels = detectLevels(df)
    console.log(`Support/Resistance levels detected: ${levels.length}`)

    // --- Signal assignment as per user request logic: BUY if ema20 > ema50 & rsi > 50 & macd > signal
    // SELL if ema20 < ema50 & rsi < 50 & macd < signal ---
    let buyCount = 0,
      sellCount = 0,
      holdCount = 0
    df.forEach(row => {
      row.BUY = false
      row.SELL = false
      if (row.ema20 !== null && row.ema50 !== null && row.macd !== null && row.signal !== null && row.rsi !== null && !isNaN(row.ema20) && !isNaN(row.ema50) && !isNaN(row.macd) && !isNaN(row.signal) && !isNaN(row.rsi)) {
        if (row.ema20 > row.ema50 && row.rsi > 50 && row.macd > row.signal) {
          row.BUY = true
          buyCount++
        } else if (row.ema20 < row.ema50 && row.rsi < 50 && row.macd < row.signal) {
          row.SELL = true
          sellCount++
        } else {
          holdCount++
        }
      }
    })
    console.log(`Signal assignment complete. BUY: ${buyCount}, SELL: ${sellCount}, HOLD/Other: ${holdCount}`)

    setContext("technical_signals", {
      indicators: df,
      support_resistance: levels
    })
    console.log("technical_signals context set with full enriched results.")
  } catch (e) {
    console.error("Technical Signal Generation error:", e)
    process.exit(1)
  }
})()
