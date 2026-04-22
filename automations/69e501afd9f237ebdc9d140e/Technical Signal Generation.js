const fs = require("fs")
const Papa = require("papaparse")

// === (existing indicator/calculation functions remain here, but ensure RSI function is defined) ===
// Example (make sure RSI function exists):
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

    // == Existing logic follows, using ohlcvArray as intended ==
    const df = ohlcvArray // <--- CRITICAL: df assigned after successful parse

    // === RSI Calculation (fix variable reference, ensure function defined) ===
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

    // Optionally: Informational signal block (BUY if RSI < 30, SELL if > 70)
    let rsiSignals = []
    let buyCount = 0,
      sellCount = 0
    for (let i = 0; i < df.length; i++) {
      const rsiVal = rsiArray[i]
      if (rsiVal !== null && !isNaN(rsiVal)) {
        if (rsiVal < 30) {
          rsiSignals.push({ index: i, type: "BUY", rsi: rsiVal })
          buyCount++
        } else if (rsiVal > 70) {
          rsiSignals.push({ index: i, type: "SELL", rsi: rsiVal })
          sellCount++
        }
      }
    }
    console.log(`RSI signals: BUY (${buyCount}), SELL (${sellCount})`)

    // ... (rest of your unchanged technical signal/ATR/EMA code follows here)
  } catch (e) {
    console.error("Technical Signal Generation error:", e)
    process.exit(1)
  }
})()
