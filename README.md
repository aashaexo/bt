# 🔵 Base Wallet Tracker Bot

An interactive Telegram bot where users send a wallet address and get:
- 💰 ETH balance
- 🪙 What memecoins they're buying/selling  
- 📊 Recent token activity
- 🔥 Trending tokens on Base

## How It Works

User sends: `0x1234...abcd`

Bot replies:
```
🔍 WALLET ANALYSIS

📍 0x1234...abcd
💰 ETH Balance: 1.5 ETH ($5,000)

📊 RECENT TOKEN ACTIVITY

🟢 BRETT - BUYING
   Buys: 5 | Sells: 1
   Chart

🔴 DEGEN - SELLING
   Buys: 2 | Sells: 4
   Chart
```

## Setup

### Step 1: Get API Keys

**Telegram Bot:**
1. Open Telegram → @BotFather
2. Send `/newbot`
3. Save the token

**Etherscan API:**
1. Go to https://etherscan.io/myapikey
2. Create a key

### Step 2: Run Locally (Test First)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_TOKEN="your-bot-token"
export ETHERSCAN_API_KEY="your-etherscan-key"

# Run the bot
python bot.py
```

### Step 3: Deploy (Free Options)

Since this bot needs to run 24/7, you need hosting:

**Option A: Railway.app (Recommended)**
1. Go to https://railway.app
2. Sign up with GitHub
3. New Project → Deploy from GitHub repo
4. Add environment variables in Railway dashboard
5. Free tier: $5 credit/month

**Option B: Render.com**
1. Go to https://render.com
2. New → Web Service → Connect GitHub
3. Add environment variables
4. Free tier available (spins down after 15 min inactive)

**Option C: Replit.com**
1. Go to https://replit.com
2. Import from GitHub
3. Add Secrets (environment variables)
4. Keep alive with UptimeRobot

**Option D: Your Computer**
- Just run `python bot.py`
- Must keep terminal open

## Commands

- `/start` - Welcome message
- `/trending` - Top tokens on Base by volume
- Send any wallet address - Get wallet analysis

## Environment Variables

| Name | Description |
|------|-------------|
| `TELEGRAM_TOKEN` | Bot token from @BotFather |
| `ETHERSCAN_API_KEY` | API key from etherscan.io |

## Free Forever

✅ Telegram Bot API - Free
✅ Etherscan API - Free
✅ DexScreener API - Free
✅ Hosting - Free tier available
