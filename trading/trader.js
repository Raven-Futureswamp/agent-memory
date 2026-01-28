#!/usr/bin/env node
// Raven Crypto Trader — Robinhood + Grok Sentiment + J Bravo TA
const rh = require('./robinhood');
const grok = require('./grok');
const ta = require('./technicals');
const fs = require('fs');
const path = require('path');

const LOG_FILE = path.join(__dirname, 'log.md');
const STATE_FILE = path.join(__dirname, 'state.json');
const TRADES_FILE = path.join(__dirname, 'trades.json');

// Trading rules
const RULES = {
  maxSingleTrade: 250,       // Max $ per trade
  maxDailyLoss: 150,         // Stop trading if daily loss exceeds this
  minConfidence: 60,         // Minimum Grok confidence to act
  protectedAssets: ['BTC', 'DOGE'],  // Don't sell these (long-term holds)
  tradableSymbols: ['DOGE-USD', 'SOL-USD', 'XRP-USD', 'TRUMP-USD', 'PEPE-USD', 'BONK-USD', 'BTC-USD'],
  maxPositionPct: 0.20,      // Max 20% of portfolio in one asset (excluding DOGE/BTC)
};

function loadState() {
  try { return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8')); }
  catch(e) { return { trades: [], dailyPnL: 0, lastTradeDate: null, totalPnL: 0 }; }
}

function saveState(state) {
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

function logTrade(trade) {
  const trades = loadTrades();
  trades.push(trade);
  fs.writeFileSync(TRADES_FILE, JSON.stringify(trades, null, 2));
  
  // Also append to markdown log
  const line = `| ${trade.timestamp} | ${trade.symbol} | ${trade.side} | ${trade.quantity} | $${trade.price} | $${trade.value} | ${trade.reasoning} |\n`;
  fs.appendFileSync(LOG_FILE, line);
}

function loadTrades() {
  try { return JSON.parse(fs.readFileSync(TRADES_FILE, 'utf8')); }
  catch(e) { return []; }
}

// Calculate cost basis from trade history
function getCostBasis(coin) {
  const trades = loadTrades();
  let totalSpent = 0;
  let totalQty = 0;
  for (const t of trades) {
    if (!t.symbol || !t.symbol.startsWith(coin)) continue;
    if (t.side === 'BUY') {
      totalSpent += parseFloat(t.value) || 0;
      totalQty += parseFloat(t.quantity) || 0;
    } else if (t.side === 'SELL') {
      // Reduce cost basis proportionally
      const soldPct = totalQty > 0 ? (parseFloat(t.quantity) / totalQty) : 0;
      totalSpent -= totalSpent * soldPct;
      totalQty -= parseFloat(t.quantity) || 0;
    }
  }
  return totalSpent > 0 ? totalSpent : null;
}

async function run() {
  console.log('=== RAVEN CRYPTO TRADER ===');
  console.log('Time:', new Date().toISOString());
  console.log('');

  // 1. Get current state
  const state = loadState();
  const today = new Date().toISOString().split('T')[0];
  
  // Reset daily P&L if new day
  if (state.lastTradeDate !== today) {
    state.dailyPnL = 0;
    state.lastTradeDate = today;
  }
  
  // Check daily loss limit
  if (state.dailyPnL <= -RULES.maxDailyLoss) {
    console.log('⛔ Daily loss limit reached ($' + state.dailyPnL + '). No more trades today.');
    return { action: 'STOPPED', reason: 'Daily loss limit' };
  }

  // 2. Get portfolio & account
  const [account, portfolio] = await Promise.all([
    rh.getAccount(),
    rh.getPortfolio()
  ]);
  
  const buyingPower = parseFloat(account.buying_power);
  console.log('💰 Buying Power: $' + buyingPower.toFixed(2));
  console.log('📊 Portfolio:');
  let totalValue = buyingPower;
  for (const p of portfolio) {
    console.log(`  ${p.asset.padEnd(6)} ${p.quantity.toString().padEnd(20)} $${p.price.toFixed(p.price < 1 ? 8 : 2).padEnd(12)} = $${p.value.toFixed(2)}`);
    totalValue += p.value;
  }
  console.log('  TOTAL: $' + totalValue.toFixed(2));
  console.log('');

  // 3. Get Grok sentiment
  const tradableAssets = RULES.tradableSymbols.map(s => s.replace('-USD', ''));
  console.log('🤖 Consulting Grok for sentiment on:', tradableAssets.join(', '));
  const sentiment = await grok.getSentiment(tradableAssets);
  
  if (sentiment.parsed) {
    console.log('📈 Overall Sentiment:', sentiment.parsed.overall_sentiment);
    console.log('🌍 Macro:', sentiment.parsed.macro_factors);
    console.log('');
    
    // 4. Run J Bravo Technical Analysis
    console.log('📐 Running J Bravo Technical Analysis...');
    let bravoSignals = {};
    try {
      bravoSignals = await ta.analyzeAll(tradableAssets);
      for (const [coin, sig] of Object.entries(bravoSignals)) {
        if (sig.error) {
          console.log(`  ${coin}: ⚠️ ${sig.error}`);
        } else {
          console.log(`  ${coin}: Signal=${sig.signal} Confidence=${sig.confidence}% | SMA9=${sig.indicators.sma9} EMA20=${sig.indicators.ema20} RSI=${sig.indicators.rsi} MA=${sig.indicators.maAlignment}`);
          console.log(`    ${sig.reasons.join(' | ')}`);
        }
      }
    } catch(e) {
      console.log('  ⚠️ TA analysis failed:', e.message);
    }
    console.log('');
    
    // 5. Combine Grok + Bravo signals
    const actions = [];
    
    for (const [coin, data] of Object.entries(sentiment.parsed.coins || {})) {
      const symbol = coin + '-USD';
      if (!RULES.tradableSymbols.includes(symbol)) continue;
      
      const holding = portfolio.find(p => p.asset === coin);
      const currentQty = holding ? holding.quantity : 0;
      const currentValue = holding ? holding.value : 0;
      const currentPrice = holding ? holding.price : 0;
      
      // Get Bravo TA signal for this coin
      const bravo = bravoSignals[coin] || {};
      const bravoSignal = bravo.signal || 'UNKNOWN';
      const bravoConfidence = bravo.confidence || 0;
      
      // HARD FIX: If sentiment score is negative, force action to SELL regardless of what Grok says
      let effectiveAction = data.action;
      if (typeof data.sentiment === 'number' && data.sentiment < 0 && data.action === 'BUY') {
        console.log(`  🚫 ${coin}: Grok sentiment NEGATIVE (${data.sentiment}) but says BUY. Overriding to HOLD.`);
        effectiveAction = 'HOLD';
      }
      
      // J Bravo override: If Bravo says SELL (below EMA20), don't buy regardless
      if (bravoSignal === 'SELL' && effectiveAction === 'BUY') {
        console.log(`  📐 ${coin}: Bravo says SELL (below EMA20) — blocking BUY.`);
        effectiveAction = 'HOLD';
      }
      
      // J Bravo boost: If Bravo says SELL and Grok is neutral/bearish, force SELL
      if (bravoSignal === 'SELL' && effectiveAction === 'HOLD' && currentQty > 0) {
        console.log(`  📐 ${coin}: Bravo SELL + Grok HOLD — triggering SELL.`);
        effectiveAction = 'SELL';
      }
      
      console.log(`${coin}: Grok=${data.action}(${data.sentiment}) + Bravo=${bravoSignal}(${bravoConfidence}%) → Effective: ${effectiveAction}`);
      console.log(`  Catalysts: ${data.catalysts}`);
      console.log(`  Outlook: ${data.outlook}`);
      
      // Skip protected assets for selling
      if (effectiveAction === 'SELL' && RULES.protectedAssets.includes(coin)) {
        console.log(`  ⚠️ ${coin} is protected (long-term hold). Skipping sell.`);
        continue;
      }
      
      // If Grok says SELL a non-protected asset — only sell if we're in PROFIT on it
      // Never sell at a loss unless sentiment is extremely bearish (< -60)
      if (effectiveAction === 'SELL' && currentQty > 0 && currentValue > 5) {
        const costBasis = getCostBasis(coin);
        const inProfit = costBasis ? (currentValue > costBasis) : false;
        const extremelyBearish = typeof data.sentiment === 'number' && data.sentiment <= -60;
        
        if (inProfit) {
          console.log(`  📉 Grok says SELL ${coin}. In profit ($${currentValue.toFixed(2)} vs cost $${costBasis?.toFixed(2)}). Selling 50%.`);
          actions.push({
            coin, symbol, currentPrice, currentQty, currentValue,
            action: 'SELL',
            confidence: Math.abs(data.sentiment) || 70,
            amount_usd: currentValue * 0.5,
            reasoning: `PROFIT TAKE — Grok SELL (${data.sentiment}): ${data.catalysts}`.slice(0, 200)
          });
        } else if (extremelyBearish) {
          console.log(`  🚨 Grok EXTREMELY BEARISH on ${coin} (${data.sentiment}). Selling 25% to cut losses.`);
          actions.push({
            coin, symbol, currentPrice, currentQty, currentValue,
            action: 'SELL',
            confidence: Math.abs(data.sentiment) || 70,
            amount_usd: currentValue * 0.25,  // Only 25% on loss cuts
            reasoning: `LOSS CUT — Grok extreme bearish (${data.sentiment}): ${data.catalysts}`.slice(0, 200)
          });
        } else {
          console.log(`  ⏸️ Grok says SELL ${coin} but we're at a LOSS (cost: $${costBasis?.toFixed(2) || '?'}). Holding — not selling at a loss unless extreme.`);
        }
        continue;
      }
      
      // Get detailed trade setup from Grok for BUY signals only
      if (effectiveAction === 'BUY' && currentPrice > 0) {
        const setup = await grok.analyzeTradeSetup(symbol, currentPrice, currentQty, buyingPower);
        if (setup.parsed && setup.parsed.action === 'BUY') {
          // Combine Grok confidence with Bravo signal
          let combinedConfidence = setup.parsed.confidence;
          if (bravoSignal === 'BUY') {
            combinedConfidence += 15;  // Bravo agrees — boost
            console.log(`  📐✅ Bravo confirms BUY — confidence boosted (+15)`);
          } else if (bravoSignal === 'HOLD') {
            combinedConfidence -= 10;  // Bravo neutral — slight penalty
            console.log(`  📐⏸️ Bravo says HOLD — confidence reduced (-10)`);
          }
          
          if (combinedConfidence >= RULES.minConfidence) {
            actions.push({
              coin, symbol, currentPrice, currentQty, currentValue,
              ...setup.parsed,
              confidence: Math.min(combinedConfidence, 100),
              reasoning: `[Grok+Bravo] ${setup.parsed.reasoning}`.slice(0, 200)
            });
          } else {
            console.log(`  ⏸️ Combined confidence too low (${combinedConfidence}%). Skipping.`);
          }
        } else if (setup.parsed) {
          console.log(`  ⚠️ Trade setup says ${setup.parsed.action}, not BUY. Skipping.`);
        }
      }
      console.log('');
    }
    
    // Execute highest confidence trades
    actions.sort((a, b) => b.confidence - a.confidence);
    
    let tradesExecuted = 0;
    for (const trade of actions) {
      if (tradesExecuted >= 3) break; // Max 3 trades per run
      
      const tradeAmount = Math.min(trade.amount_usd || 0, RULES.maxSingleTrade);
      if (tradeAmount < 5) continue; // Skip tiny trades
      
      if (trade.action === 'BUY' && tradeAmount <= buyingPower) {
        // Position concentration check — don't let any single asset exceed maxPositionPct
        const newPositionValue = trade.currentValue + tradeAmount;
        const positionPct = newPositionValue / totalValue;
        if (positionPct > RULES.maxPositionPct) {
          console.log(`  ⚠️ ${trade.coin} would be ${(positionPct*100).toFixed(1)}% of portfolio (max ${RULES.maxPositionPct*100}%). Skipping buy.`);
          continue;
        }
        // Round quantity based on price magnitude to avoid precision errors
        let decimals = 2;
        if (trade.currentPrice > 10000) decimals = 6;      // BTC
        else if (trade.currentPrice > 100) decimals = 4;    // SOL
        else if (trade.currentPrice > 1) decimals = 4;      // XRP, TRUMP, DOGE
        else if (trade.currentPrice > 0.001) decimals = 0;  // SHIB-like
        else decimals = 0;                                   // PEPE, BONK
        const qty = Math.floor((tradeAmount / trade.currentPrice) * Math.pow(10, decimals)) / Math.pow(10, decimals);
        console.log(`🟢 BUYING ${qty} ${trade.coin} (~$${tradeAmount}) — Confidence: ${trade.confidence}%`);
        console.log(`   Reasoning: ${trade.reasoning}`);
        
        const result = await rh.buyMarket(trade.symbol, qty);
        if (result.status === 201) {
          console.log('   ✅ Order placed! ID:', result.data.id);
          logTrade({
            timestamp: new Date().toISOString(),
            symbol: trade.symbol,
            side: 'BUY',
            quantity: qty,
            price: trade.currentPrice,
            value: tradeAmount.toFixed(2),
            reasoning: trade.reasoning.slice(0, 100),
            confidence: trade.confidence,
            orderId: result.data.id
          });
          tradesExecuted++;
        } else {
          console.log('   ❌ Order failed:', JSON.stringify(result.data));
        }
      } else if (trade.action === 'SELL' && trade.currentQty > 0) {
        const sellPct = Math.min(tradeAmount / trade.currentValue, 1);
        let decimals = 2;
        if (trade.currentPrice > 10000) decimals = 6;
        else if (trade.currentPrice > 100) decimals = 4;
        else if (trade.currentPrice > 1) decimals = 4;
        else if (trade.currentPrice > 0.001) decimals = 0;
        else decimals = 0;
        const qty = Math.floor((trade.currentQty * sellPct) * Math.pow(10, decimals)) / Math.pow(10, decimals);
        console.log(`🔴 SELLING ${qty} ${trade.coin} (~$${tradeAmount}) — Confidence: ${trade.confidence}%`);
        console.log(`   Reasoning: ${trade.reasoning}`);
        
        const result = await rh.sellMarket(trade.symbol, qty);
        if (result.status === 201) {
          console.log('   ✅ Order placed! ID:', result.data.id);
          logTrade({
            timestamp: new Date().toISOString(),
            symbol: trade.symbol,
            side: 'SELL',
            quantity: qty,
            price: trade.currentPrice,
            value: tradeAmount.toFixed(2),
            reasoning: trade.reasoning.slice(0, 100),
            confidence: trade.confidence,
            orderId: result.data.id
          });
          tradesExecuted++;
        } else {
          console.log('   ❌ Order failed:', JSON.stringify(result.data));
        }
      }
    }
    
    if (tradesExecuted === 0) {
      console.log('📊 No high-confidence trades found this cycle. Holding.');
    }
    
    saveState(state);
    return { tradesExecuted, sentiment: sentiment.parsed.overall_sentiment };
    
  } else {
    console.log('⚠️ Could not parse Grok sentiment. Raw response:');
    console.log(sentiment.raw.slice(0, 500));
    return { action: 'ERROR', reason: 'Grok parse failure' };
  }
}

// Run if called directly
if (require.main === module) {
  run().then(result => {
    console.log('\n=== RUN COMPLETE ===');
    console.log(JSON.stringify(result, null, 2));
  }).catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
}

module.exports = { run };
