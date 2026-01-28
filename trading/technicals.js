// Technical Analysis Module — J Bravo Method
// SMA(9) entry, EMA(20) exit, 200 DMA filter, VWAP "GoGo Juice"
const https = require('https');

// Fetch historical candles from CoinGecko (free, no API key)
async function fetchDailyPrices(coinId, days = 210) {
  return new Promise((resolve, reject) => {
    const url = `https://api.coingecko.com/api/v3/coins/${coinId}/market_chart?vs_currency=usd&days=${days}&interval=daily`;
    https.get(url, { headers: { 'Accept': 'application/json', 'User-Agent': 'RavenTrader/1.0' } }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          if (parsed.prices) {
            resolve(parsed.prices.map(([ts, price]) => ({ timestamp: ts, price })));
          } else {
            resolve([]);
          }
        } catch(e) { resolve([]); }
      });
    }).on('error', reject);
  });
}

// Map our trading symbols to CoinGecko IDs
const COINGECKO_MAP = {
  'BTC': 'bitcoin',
  'DOGE': 'dogecoin',
  'SOL': 'solana',
  'XRP': 'ripple',
  'TRUMP': 'official-trump',
  'PEPE': 'pepe',
  'BONK': 'bonk',
  'ETH': 'ethereum',
};

// Calculate Simple Moving Average
function SMA(prices, period) {
  if (prices.length < period) return null;
  const slice = prices.slice(-period);
  return slice.reduce((sum, p) => sum + p, 0) / period;
}

// Calculate Exponential Moving Average
function EMA(prices, period) {
  if (prices.length < period) return null;
  const k = 2 / (period + 1);
  let ema = SMA(prices.slice(0, period), period);
  for (let i = period; i < prices.length; i++) {
    ema = prices[i] * k + ema * (1 - k);
  }
  return ema;
}

// Check if last candle CLOSED above a moving average (full body close)
function closedAbove(prices, maValue) {
  if (!maValue || prices.length < 2) return false;
  return prices[prices.length - 1] > maValue;
}

// Check if last candle CLOSED below a moving average
function closedBelow(prices, maValue) {
  if (!maValue || prices.length < 2) return false;
  return prices[prices.length - 1] < maValue;
}

// Check MA alignment (bullish: 9 > 20 > 180, bearish: 180 > 20 > 9)
function maAlignment(sma9, ema20, sma180) {
  if (!sma9 || !ema20 || !sma180) return 'unknown';
  if (sma9 > ema20 && ema20 > sma180) return 'bullish';
  if (sma180 > ema20 && ema20 > sma9) return 'bearish';
  return 'mixed';
}

// Calculate RSI
function RSI(prices, period = 14) {
  if (prices.length < period + 1) return null;
  let gains = 0, losses = 0;
  for (let i = prices.length - period; i < prices.length; i++) {
    const diff = prices[i] - prices[i - 1];
    if (diff > 0) gains += diff;
    else losses -= diff;
  }
  const avgGain = gains / period;
  const avgLoss = losses / period;
  if (avgLoss === 0) return 100;
  const rs = avgGain / avgLoss;
  return 100 - (100 / (1 + rs));
}

// Main analysis function — returns J Bravo signals for a coin
async function analyze(coin) {
  const coinId = COINGECKO_MAP[coin];
  if (!coinId) return { error: `No CoinGecko mapping for ${coin}` };

  try {
    const history = await fetchDailyPrices(coinId, 210);
    if (history.length < 30) return { error: `Not enough price data for ${coin}` };

    const prices = history.map(h => h.price);
    const currentPrice = prices[prices.length - 1];
    const prevPrice = prices[prices.length - 2];

    // Calculate indicators
    const sma9 = SMA(prices, 9);
    const ema20 = EMA(prices, 20);
    const sma180 = SMA(prices, 180);
    const sma200 = SMA(prices, 200);
    const rsi = RSI(prices);

    // J Bravo Signals
    const aboveSMA9 = closedAbove(prices, sma9);
    const belowEMA20 = closedBelow(prices, ema20);
    const above200DMA = sma200 ? currentPrice > sma200 : true; // default true if not enough data
    const alignment = maAlignment(sma9, ema20, sma180);
    const rsiOverbought = rsi && rsi > 70;
    const rsiOversold = rsi && rsi < 30;

    // Generate signal
    let signal = 'HOLD';
    let confidence = 0;
    let reasons = [];

    // BUY signal: candle closes above SMA(9)
    if (aboveSMA9 && !belowEMA20 && above200DMA) {
      signal = 'BUY';
      confidence = 50;
      reasons.push('Price closed above SMA(9) — Bravo BUY signal');

      if (alignment === 'bullish') {
        confidence += 20;
        reasons.push('MA alignment bullish (9>20>180) — STRONG BUY');
      }
      if (!rsiOverbought) {
        confidence += 10;
        reasons.push('RSI not overbought');
      } else {
        confidence -= 15;
        reasons.push('⚠️ RSI overbought (>70) — risky entry');
      }
    }

    // SELL signal: candle closes below EMA(20)
    if (belowEMA20) {
      signal = 'SELL';
      confidence = 50;
      reasons = ['Price closed below EMA(20) — Bravo SELL signal'];

      if (alignment === 'bearish') {
        confidence += 20;
        reasons.push('MA alignment bearish (180>20>9) — STRONG SELL');
      }
      if (!above200DMA) {
        confidence += 10;
        reasons.push('Below 200 DMA — bearish trend');
      }
    }

    // No clear signal
    if (signal === 'HOLD') {
      reasons.push('No clear Bravo signal — between SMA(9) and EMA(20)');
      if (!above200DMA) reasons.push('Below 200 DMA — caution');
      if (rsiOversold) reasons.push('RSI oversold — potential bounce');
    }

    return {
      coin,
      currentPrice,
      signal,
      confidence: Math.min(confidence, 100),
      indicators: {
        sma9: sma9?.toFixed(6),
        ema20: ema20?.toFixed(6),
        sma180: sma180?.toFixed(6),
        sma200: sma200?.toFixed(6),
        rsi: rsi?.toFixed(1),
        maAlignment: alignment,
      },
      checks: {
        aboveSMA9,
        belowEMA20,
        above200DMA,
        rsiOverbought,
        rsiOversold,
      },
      reasons,
    };
  } catch(e) {
    return { error: `Failed to analyze ${coin}: ${e.message}` };
  }
}

// Analyze all coins
async function analyzeAll(coins) {
  const results = {};
  for (const coin of coins) {
    results[coin] = await analyze(coin);
    // Rate limit: CoinGecko free tier = 10-30 req/min
    await new Promise(r => setTimeout(r, 2500));
  }
  return results;
}

module.exports = { analyze, analyzeAll, SMA, EMA, RSI, fetchDailyPrices };
