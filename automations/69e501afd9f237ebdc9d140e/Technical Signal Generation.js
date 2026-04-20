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

// -- RSI calculation --
function RSI(prices, period = 14) {
  if (prices.length < period + 1) {
    return Array(prices.length).fill(null)
  }
  let gains = 0,
    losses = 0
  const rsis = Array(period).fill(null)
  for (let i = 1; i <= period; i++) {
    const diff = prices[i] - prices[i - 1]
    if (diff >= 0) gains += diff
    else losses -= diff
  }
  gains /= period
  losses /= period
  rsis[period] = losses === 0 ? 100 : 100 - 100 / (1 + gains / losses)
  for (let i = period + 1; i < prices.length; i++) {
    const diff = prices[i] - prices[i - 1]
    const gain = diff > 0 ? diff : 0
    const loss = diff < 0 ? -diff : 0
    gains = (gains * (period - 1) + gain) / period
    losses = (losses * (period - 1) + loss) / period
    rsis[i] = losses === 0 ? 100 : 100 - 100 / (1 + gains / losses)
  }
  return rsis
}

;(async () => {
  try {
    // ... <UNCHANGED CODE FROM LINES 16 to 155> ...

    // === RSI Calculation ===
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

    // <--- INSERT CODE AFTER SIGNAL GENERATION AND BEFORE CONTEXT PROPAGATION LINE 217 (SETCONTEXT)--->

    // ... <UNCHANGED CODE FOLLOWING EXISTING CONTEXT AND LOGIC> ...
    setContext("rsi", rsiArray)
    setContext("rsiSignals", rsiSignals)
    // ... <UNCHANGED CONTEXT> ...

    // ...
    console.log(`Technical Signal Generation step complete. Composite: ${signals.length}, Dual EMA: ${emaCrossoverSignals.length}`)
  } catch (e) {
    console.error("Technical Signal Generation error:", e)
    process.exit(1)
  }
})()
