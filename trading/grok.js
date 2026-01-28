// Grok (xAI) Sentiment & Analysis Module
const https = require('https');
const fs = require('fs');
const path = require('path');

const envPath = path.join(__dirname, '..', '.env');
const envContent = fs.readFileSync(envPath, 'utf8');
function getEnv(key) {
  const match = envContent.match(new RegExp(`^${key}=["']?([^"'\\n]+)["']?`, 'm'));
  return match ? match[1] : null;
}

const XAI_API_KEY = getEnv('XAI_API_KEY');

function askGrok(prompt, model = 'grok-3-mini') {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      model: model,
      messages: [
        { role: 'system', content: 'You are a crypto trading analyst. Give concise, actionable analysis. Include sentiment score (-100 to +100), key factors, and a clear BUY/SELL/HOLD recommendation. Be direct.' },
        { role: 'user', content: prompt }
      ],
      temperature: 0.3,
      max_tokens: 1000
    });

    const options = {
      hostname: 'api.x.ai',
      path: '/v1/chat/completions',
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + XAI_API_KEY,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body)
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          const content = parsed.choices?.[0]?.message?.content || 'No response';
          resolve(content);
        } catch(e) {
          resolve('Error parsing Grok response: ' + data.slice(0, 200));
        }
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

async function getSentiment(symbols) {
  const symbolList = symbols.join(', ');
  const prompt = `Analyze the current crypto market sentiment for: ${symbolList}

For each coin, provide:
1. Sentiment score (-100 bearish to +100 bullish)
2. Key recent catalysts or news
3. Short-term outlook (next 24-48 hours)
4. Recommendation: BUY / SELL / HOLD

Also give an overall market sentiment score and any macro factors to watch.

Format as JSON like:
{
  "overall_sentiment": 0,
  "macro_factors": "...",
  "coins": {
    "BTC": { "sentiment": 0, "catalysts": "...", "outlook": "...", "action": "HOLD" },
    ...
  }
}`;

  const response = await askGrok(prompt);
  
  // Try to extract JSON from response
  try {
    const jsonMatch = response.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return { raw: response, parsed: JSON.parse(jsonMatch[0]) };
    }
  } catch(e) {}
  
  return { raw: response, parsed: null };
}

async function analyzeTradeSetup(symbol, currentPrice, holdings, buyingPower) {
  const prompt = `I'm considering a trade on ${symbol} (current price: $${currentPrice}).

My situation:
- Buying power: $${buyingPower}
- Current holdings in ${symbol}: ${holdings} units

Should I:
1. Buy more? If yes, how much (in USD)?
2. Sell some/all? If yes, what %?
3. Hold and wait?

Consider momentum, sentiment, support/resistance levels, and risk management.
Max single trade size: $250. 
I want aggressive growth but protect capital.

Respond in JSON:
{
  "action": "BUY|SELL|HOLD",
  "confidence": 0-100,
  "amount_usd": 0,
  "reasoning": "...",
  "entry_price": 0,
  "target_price": 0,
  "stop_loss_price": 0
}`;

  const response = await askGrok(prompt);
  
  try {
    const jsonMatch = response.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return { raw: response, parsed: JSON.parse(jsonMatch[0]) };
    }
  } catch(e) {}
  
  return { raw: response, parsed: null };
}

module.exports = { askGrok, getSentiment, analyzeTradeSetup };
