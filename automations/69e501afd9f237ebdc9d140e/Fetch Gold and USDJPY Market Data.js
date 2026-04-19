const api = require("metalpriceapi")
const dayjs = require("dayjs")

;(async () => {
  try {
    const apiKey = process.env.METALPRICEAPI_KEY
    if (!apiKey) throw new Error("Missing METALPRICEAPI_KEY env variable")
    api.setAPIKey(apiKey)

    // Fetch Gold (XAUUSD) - MetalPriceAPI does support bid/ask for XAU
    let xauusd_bid = null
    let xauusd_ask = null
    // USDJPY spot rate (bid/ask not supported; fallback to spot/mid)
    let usdjpy_spot = null
    let usdjpy_previous_spot = null

    // Gold bid/ask
    const metals = await api.fetchLive("USD", ["XAU-BID", "XAU-ASK"])
    if (metals && metals.rates) {
      xauusd_bid = metals.rates["XAU-BID"] || null
      xauusd_ask = metals.rates["XAU-ASK"] || null
    }
    // USDJPY: Only spot/mid available via MetalPriceAPI (bid/ask NOT supported for forex—confirmed by docs & API)
    // Use base 'USD', currencies: 'JPY' gives the USDJPY mid/spot
    const fx = await api.fetchLive("USD", ["JPY"])
    if (fx && fx.rates) {
      usdjpy_spot = fx.rates["JPY"] || null
    }
    // Previous day's USDJPY spot/mid
    const prevDate = dayjs().subtract(1, "day").format("YYYY-MM-DD")
    let fxHist = null
    try {
      fxHist = await api.fetchHistorical(prevDate, "USD", ["JPY"])
      if (fxHist && fxHist.rates && fxHist.rates["JPY"]) {
        usdjpy_previous_spot = fxHist.rates["JPY"]
      }
    } catch (err) {
      console.error("[metalpriceapi][historical] Error fetching previous USDJPY spot:", err)
    }
    if (typeof usdjpy_previous_spot !== "number" || usdjpy_previous_spot <= 0) usdjpy_previous_spot = null

    // Debug/Log API results for easier troubleshooting
    console.log("[debug] MetalPriceAPI metals:", metals)
    console.log("[debug] MetalPriceAPI fx:", fx)
    console.log("[debug] MetalPriceAPI fxHist:", fxHist)

    // Error handling - only set context if data is valid
    let fatalError = false
    if (!xauusd_bid || !xauusd_ask || !usdjpy_spot || !usdjpy_previous_spot) {
      console.error("[step] Missing required data for XAU or USDJPY:", {
        xauusd_bid,
        xauusd_ask,
        usdjpy_spot,
        usdjpy_previous_spot
      })
      fatalError = true
    }

    if (fatalError) {
      throw new Error("Cannot continue: One or more required prices missing")
    }
    setContext("xauusd_bid", xauusd_bid)
    setContext("xauusd_ask", xauusd_ask)
    setContext("usdjpy_spot", usdjpy_spot)
    setContext("usdjpy_previous_spot", usdjpy_previous_spot)
    console.log("[step] SUCCESS: Gold/FX prices:", {
      xauusd_bid,
      xauusd_ask,
      usdjpy_spot,
      usdjpy_previous_spot
    })
  } catch (e) {
    console.error("[step] Error in Fetch Gold & USDJPY Market Data:", e)
    process.exit(1)
  }
})()
