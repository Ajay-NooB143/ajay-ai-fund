const fs = require("fs")
const Papa = require("papaparse")

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

function EMA(closes, period) {
  let emas = Array(closes.length).fill(null)
  if (closes.length < period) return emas
  let multiplier = 2 / (period + 1)
  let sum = 0
  for (let i = 0; i < period; i++) sum += closes[i]
  emas[period - 1] = sum / period
  for (let i = period; i < closes.length; i++) {
    emas[i] = (closes[i] - emas[i - 1]) * multiplier + emas[i - 1]
  }
  return emas
}

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
      return {
        ...row,
        open: Number(row.open),
        high: Number(row.high),
        low: Number(row.low),
        close: Number(row.close),
        volume: Number(row.volume)
      }
    })
    console.log(`Parsed OHLCV: ${ohlcvArray.length} rows from '${ohlcvPath}'`)

    const df = ohlcvArray
    const closes = df.map(row => row.close)

    // Calculate EMA with period from ENV or fallback to 20
    let emaPeriod = 20
    if (process.env.EMA_PERIOD && !isNaN(Number(process.env.EMA_PERIOD))) {
      emaPeriod = Math.max(1, Number(process.env.EMA_PERIOD))
    }
    let ema = EMA(closes, emaPeriod)
    df.forEach((row, idx) => {
      row.ema = ema[idx]
    })
    console.log(`EMA calculated. Period: ${emaPeriod}, First 5:`, ema.slice(0, 5))

    // RSI/MACD/Support/Resistance kept for context/enrichment for downstream steps (but not for signal gating)
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

    let { macd, signal } = MACD(closes, 12, 26, 9)
    df.forEach((row, idx) => {
      row.macd = macd[idx]
      row.signal = signal[idx]
    })

    const levels = detectLevels(df)
    console.log(`Support/Resistance levels detected: ${levels.length}`)

    // === Strict signal gating: if close > ema => BUY, else if close < ema => SELL, else neither ===
    let buyCount = 0,
      sellCount = 0,
      neitherCount = 0
    df.forEach(row => {
      row.BUY = false
      row.SELL = false
      if (row.ema !== null && !isNaN(row.ema) && row.close !== null && !isNaN(row.close)) {
        if (row.close > row.ema) {
          row.BUY = true
          buyCount++
        } else if (row.close < row.ema) {
          row.SELL = true
          sellCount++
        } else {
          neitherCount++
        }
      } else {
        neitherCount++
      }
    })
    console.log(`Strict signal gating applied. BUY: ${buyCount}, SELL: ${sellCount}, NEITHER: ${neitherCount}`)

    setContext("technical_signals", {
      indicators: df,
      support_resistance: levels
    })
    console.log("technical_signals context set with strict BUY/SELL signals.")
  } catch (e) {
    console.error("Technical Signal Generation error:", e)
    process.exit(1)
  }
})()
