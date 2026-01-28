// Robinhood Crypto Trading API Client
const nacl = require('tweetnacl');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

// Load env
const envPath = path.join(__dirname, '..', '.env');
const envContent = fs.readFileSync(envPath, 'utf8');
function getEnv(key) {
  const match = envContent.match(new RegExp(`^${key}=["']?([^"'\\n]+)["']?`, 'm'));
  return match ? match[1] : null;
}

const API_KEY = getEnv('ROBINHOOD_API_KEY');
const PRIVATE_KEY_B64 = getEnv('ROBINHOOD_PRIVATE_KEY');
const privateKeySeed = Buffer.from(PRIVATE_KEY_B64, 'base64');
const keyPair = nacl.sign.keyPair.fromSeed(privateKeySeed);

function makeRequest(method, requestPath, body) {
  const timestamp = Math.floor(Date.now() / 1000);
  const bodyStr = body ? JSON.stringify(body) : '';
  const message = API_KEY + timestamp + requestPath + method + bodyStr;
  const msgBytes = new TextEncoder().encode(message);
  const signed = nacl.sign.detached(msgBytes, keyPair.secretKey);
  const signature = Buffer.from(signed).toString('base64');

  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'trading.robinhood.com',
      path: requestPath,
      method: method,
      headers: {
        'x-api-key': API_KEY,
        'x-signature': signature,
        'x-timestamp': String(timestamp),
        'Content-Type': 'application/json; charset=utf-8'
      }
    };
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, data: JSON.parse(data) }); }
        catch(e) { resolve({ status: res.statusCode, data: data }); }
      });
    });
    req.on('error', reject);
    if (bodyStr) req.write(bodyStr);
    req.end();
  });
}

async function getAccount() {
  const r = await makeRequest('GET', '/api/v1/crypto/trading/accounts/');
  return r.data;
}

async function getHoldings() {
  const r = await makeRequest('GET', '/api/v1/crypto/trading/holdings/');
  return r.data.results || [];
}

async function getBestPrices(...symbols) {
  const symParam = symbols.map(s => 'symbol=' + s).join('&');
  const r = await makeRequest('GET', '/api/v1/crypto/marketdata/best_bid_ask/?' + symParam);
  return r.data.results || [];
}

async function getEstimatedPrice(symbol, side, quantity) {
  const r = await makeRequest('GET', `/api/v1/crypto/marketdata/estimated_price/?symbol=${symbol}&side=${side}&quantity=${quantity}`);
  return r.data.results || [];
}

async function buyMarket(symbol, assetQuantity) {
  const body = {
    client_order_id: crypto.randomUUID(),
    side: 'buy',
    type: 'market',
    symbol: symbol,
    market_order_config: { asset_quantity: String(assetQuantity) }
  };
  return makeRequest('POST', '/api/v1/crypto/trading/orders/', body);
}

async function sellMarket(symbol, assetQuantity) {
  const body = {
    client_order_id: crypto.randomUUID(),
    side: 'sell',
    type: 'market',
    symbol: symbol,
    market_order_config: { asset_quantity: String(assetQuantity) }
  };
  return makeRequest('POST', '/api/v1/crypto/trading/orders/', body);
}

async function buyLimit(symbol, assetQuantity, limitPrice, timeInForce = 'gtc') {
  const body = {
    client_order_id: crypto.randomUUID(),
    side: 'buy',
    type: 'limit',
    symbol: symbol,
    limit_order_config: {
      asset_quantity: String(assetQuantity),
      limit_price: String(limitPrice),
      time_in_force: timeInForce
    }
  };
  return makeRequest('POST', '/api/v1/crypto/trading/orders/', body);
}

async function sellLimit(symbol, assetQuantity, limitPrice, timeInForce = 'gtc') {
  const body = {
    client_order_id: crypto.randomUUID(),
    side: 'sell',
    type: 'limit',
    symbol: symbol,
    limit_order_config: {
      asset_quantity: String(assetQuantity),
      limit_price: String(limitPrice),
      time_in_force: timeInForce
    }
  };
  return makeRequest('POST', '/api/v1/crypto/trading/orders/', body);
}

async function getOrders(params = {}) {
  const qp = Object.entries(params).map(([k,v]) => `${k}=${v}`).join('&');
  const path = '/api/v1/crypto/trading/orders/' + (qp ? '?' + qp : '');
  const r = await makeRequest('GET', path);
  return r.data;
}

async function getOrder(orderId) {
  const r = await makeRequest('GET', `/api/v1/crypto/trading/orders/${orderId}/`);
  return r.data;
}

async function cancelOrder(orderId) {
  return makeRequest('POST', `/api/v1/crypto/trading/orders/${orderId}/cancel/`);
}

async function getTradingPairs(...symbols) {
  const symParam = symbols.length ? '?' + symbols.map(s => 'symbol=' + s).join('&') : '';
  const r = await makeRequest('GET', '/api/v1/crypto/trading/trading_pairs/' + symParam);
  return r.data.results || [];
}

// Get portfolio with current values
async function getPortfolio() {
  const holdings = await getHoldings();
  if (!holdings.length) return [];
  
  const symbols = holdings.map(h => h.asset_code + '-USD');
  const prices = await getBestPrices(...symbols);
  const priceMap = {};
  for (const p of prices) {
    priceMap[p.symbol.replace('-USD', '')] = parseFloat(p.price);
  }
  
  return holdings.map(h => ({
    asset: h.asset_code,
    quantity: parseFloat(h.total_quantity),
    available: parseFloat(h.quantity_available_for_trading),
    price: priceMap[h.asset_code] || 0,
    value: parseFloat(h.total_quantity) * (priceMap[h.asset_code] || 0)
  })).sort((a, b) => b.value - a.value);
}

module.exports = {
  getAccount, getHoldings, getBestPrices, getEstimatedPrice,
  buyMarket, sellMarket, buyLimit, sellLimit,
  getOrders, getOrder, cancelOrder, getTradingPairs, getPortfolio
};
