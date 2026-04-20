const axios = require("axios")
const fs = require("fs")

async function fetchBinance(symbol, interval, limit) {
  const url = `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`
  console.log(`[step] Trying Binance: ${url}`)
  const response = await axios.get(url, { timeout: 20000 })
  if (!Array.isArray(response.data)) {
    throw new Error("Binance API response not an array")
  }
  // Binance schema: [time, open, high, low, close, volume, ...]
  return response.data.map(row => ({
    time: +row[0],
    open: parseFloat(row[1]),
    high: parseFloat(row[2]),
    low: parseFloat(row[3]),
    close: parseFloat(row[4]),
    volume: parseFloat(row[5])
  }))
}

async function fetchBybit(symbol, interval, limit) {
  // Bybit symbols are usually like BTCUSDT or ETHUSDT, and intervals like 5,15,30, etc
  // See https://bybit-exchange.github.io/docs/v5/market/kline
  let convertedInterval = interval
  // Convert binance interval string to minutes (e.g. '5m' to '5')
  if (interval.endsWith("m")) {
    convertedInterval = interval.replace("m", "")
  }

  const url = `https://api.bybit.com/v5/market/kline?symbol=${symbol}&interval=${convertedInterval}&limit=${limit}`
  console.log(`[step] Trying Bybit: ${url}`)
  const response = await axios.get(url, { timeout: 20000 })
  if (!response.data || response.data.retCode !== 0 || !Array.isArray(response.data.result.list)) {
    throw new Error("Bybit response invalid")
  }
  // Bybit schema: [open_time, open_price, high_price, low_price, close_price, volume,...] (as strings)
  return response.data.result.list.map(row => ({
    time: +row[0],
    open: parseFloat(row[1]),
    high: parseFloat(row[2]),
    low: parseFloat(row[3]),
    close: parseFloat(row[4]),
    volume: parseFloat(row[5])
  }))
}

async function fetchAlphaVantage(symbol, interval, limit) {
  // https://www.alphavantage.co/documentation/#intraday
  // Symbol might need adjustment: BTCUSDT => BTC/USD
  // AlphaVantage free API key is demo, but in production would require env
  const avSymbol = symbol.replace("USDT", "/USD")
  // Only supports intervals: 1min, 5min, 15min, 30min, 60min
  let avInterval = interval
  if (interval.endsWith("m")) {
    avInterval = interval.replace("m", "min")
  }
  const apikey = process.env.ALPHAVANTAGE_API_KEY || "demo"
  const url = `https://www.alphavantage.co/query?function=CRYPTO_INTRADAY&symbol=${avSymbol}&market=USD&interval=${avInterval}&apikey=${apikey}`
  console.log(`[step] Trying AlphaVantage: ${url}`)
  const response = await axios.get(url, { timeout: 20000 })
  if (!response.data || !response.data["Time Series Crypto (" + avInterval + ")"]) {
    throw new Error("AlphaVantage data missing")
  }
  const raw = response.data["Time Series Crypto (" + avInterval + ")"]
  const records = Object.keys(raw)
    .slice(0, limit)
    .reverse()
    .map(ts => ({
      time: Date.parse(ts),
      open: parseFloat(raw[ts]["1. open"]),
      high: parseFloat(raw[ts]["2. high"]),
      low: parseFloat(raw[ts]["3. low"]),
      close: parseFloat(raw[ts]["4. close"]),
      volume: parseFloat(raw[ts]["5. volume"])
    }))
  return records
}

;(async () => {
  try {
    let symbol = process.env.BINANCE_SYMBOL || "BTCUSDT"
    const interval = process.env.BINANCE_INTERVAL || "5m"
    const limit = parseInt(process.env.BINANCE_LIMIT, 10) || 500
    const csvPath = process.env.OHLCV_CSV_PATH || "./ohlcv_data.csv"

    const symbolRegex = /^[A-Z0-9_.-]{1,50}$/
    if (!symbolRegex.test(symbol)) {
      console.error(`[step] Invalid BINANCE_SYMBOL '${symbol}'. Must be 1-50 chars of A-Z, 0-9, _, ., or -. Example: BTCUSDT`)
      process.exit(1)
    }
    console.log(`[step] Using symbol: ${symbol}`)
    let records, provider
    try {
      records = await fetchBinance(symbol, interval, limit)
      provider = "Binance"
      console.log(`[step] Binance succeeded, records: ${records.length}`)
    } catch (e1) {
      console.error("[step] Binance failed:", e1 && e1.toString())
      try {
        records = await fetchBybit(symbol, interval, limit)
        provider = "Bybit"
        console.log(`[step] Bybit succeeded, records: ${records.length}`)
      } catch (e2) {
        console.error("[step] Bybit failed:", e2 && e2.toString())
        try {
          records = await fetchAlphaVantage(symbol, interval, limit)
          provider = "AlphaVantage"
          console.log(`[step] AlphaVantage succeeded, records: ${records.length}`)
        } catch (e3) {
          console.error("[step] AlphaVantage failed:", e3 && e3.toString())
          console.error("[step] Fetch failed from all providers.")
          process.exit(1)
        }
      }
    }
    // CSV output (normalized)
    const csvHeader = "time,open,high,low,close,volume"
    const csvRows = records.map(r => `${r.time},${r.open},${r.high},${r.low},${r.close},${r.volume}`)
    const csvOutput = [csvHeader, ...csvRows].join("\n")
    fs.writeFileSync(csvPath, csvOutput, "utf8")
    console.log(`[step] Wrote ${records.length} rows from ${provider} to ${csvPath}`)

    // Set context for downstream steps
    setContext("ohlcv_data", records)
    setContext("ohlcv_length", records.length)
    setContext("ohlcv_path", csvPath)
    setContext("ohlcv_source", provider)
    // Log preview
    console.log("[step] First row:", records.length > 0 ? records[0] : "No rows found.")
  } catch (e) {
    console.error("[step] Fatal error fetching OHLCV:", e)
    process.exit(1)
  }
})()
