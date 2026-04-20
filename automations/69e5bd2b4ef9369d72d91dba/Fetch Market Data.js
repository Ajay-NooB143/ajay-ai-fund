const axios = require("axios")
const fs = require("fs")

;(async () => {
  try {
    // Fetch parameters from ENV with sane defaults for demo if not set
    let symbol = process.env.BINANCE_SYMBOL || "BTCUSDT"
    const interval = process.env.BINANCE_INTERVAL || "5m"
    const limit = parseInt(process.env.BINANCE_LIMIT, 10) || 500
    const csvPath = process.env.OHLCV_CSV_PATH || "./ohlcv_data.csv"

    // Validate symbol: 1-50 chars, uppercase letters, numbers, underscore, dash, period; no spaces or arrows
    const symbolRegex = /^[A-Z0-9_.-]{1,50}$/
    if (!symbolRegex.test(symbol)) {
      console.error(`[step] Invalid BINANCE_SYMBOL '${symbol}'. Must be 1-50 chars of A-Z, 0-9, _, ., or -. Example: BTCUSDT`)
      process.exit(1)
    }
    console.log(`[step] Using symbol: ${symbol}`)

    const url = `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`
    console.log(`[step] Fetching Binance OHLCV: ${url}`)

    const response = await axios.get(url, { timeout: 20000 })
    if (!Array.isArray(response.data)) {
      throw new Error("Binance API response not an array")
    }
    const rawData = response.data

    // Map to expected columns: time,open,high,low,close,volume (all as float except time)
    const records = rawData.map(row => ({
      time: +row[0],
      open: parseFloat(row[1]),
      high: parseFloat(row[2]),
      low: parseFloat(row[3]),
      close: parseFloat(row[4]),
      volume: parseFloat(row[5])
    }))

    // Compose CSV header and rows
    const csvHeader = "time,open,high,low,close,volume"
    const csvRows = records.map(r => `${r.time},${r.open},${r.high},${r.low},${r.close},${r.volume}`)
    const csvOutput = [csvHeader, ...csvRows].join("\n")
    fs.writeFileSync(csvPath, csvOutput, "utf8")
    console.log(`[step] Wrote ${records.length} rows to ${csvPath}`)

    // Set context for downstream steps (optional, for direct JS use)
    setContext("ohlcv_data", records)
    setContext("ohlcv_length", records.length)
    setContext("ohlcv_path", csvPath)
    // Log preview
    console.log("[step] First row:", records.length > 0 ? records[0] : "No rows found.")
  } catch (e) {
    console.error("[step] Error fetching Binance OHLCV:", e)
    process.exit(1)
  }
})()
