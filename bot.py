import asyncio
import aiohttp
import re
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load from environment variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY")

BASE_CHAIN_ID = 8453


# ============ API FUNCTIONS ============

async def get_eth_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return data.get("ethereum", {}).get("usd", 0)
    except:
        return 0


async def get_eth_balance(wallet: str):
    url = "https://api.etherscan.io/v2/api"
    params = {
        "chainid": BASE_CHAIN_ID,
        "module": "account",
        "action": "balance",
        "address": wallet,
        "apikey": ETHERSCAN_API_KEY,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                balance_wei = int(data.get("result", 0))
                return balance_wei / 10**18
    except:
        return 0


async def get_token_transactions(wallet: str, limit: int = 20):
    url = "https://api.etherscan.io/v2/api"
    params = {
        "chainid": BASE_CHAIN_ID,
        "module": "account",
        "action": "tokentx",
        "address": wallet,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": limit,
        "sort": "desc",
        "apikey": ETHERSCAN_API_KEY,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                return data.get("result", [])
    except:
        return []


async def get_eth_transactions(wallet: str, limit: int = 10):
    url = "https://api.etherscan.io/v2/api"
    params = {
        "chainid": BASE_CHAIN_ID,
        "module": "account",
        "action": "txlist",
        "address": wallet,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": limit,
        "sort": "desc",
        "apikey": ETHERSCAN_API_KEY,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                return data.get("result", [])
    except:
        return []


async def get_token_info(token_address: str):
    """Get token info from DexScreener"""
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                pairs = data.get("pairs", [])
                if pairs:
                    pair = pairs[0]
                    return {
                        "name": pair.get("baseToken", {}).get("name", "Unknown"),
                        "symbol": pair.get("baseToken", {}).get("symbol", "???"),
                        "price": float(pair.get("priceUsd", 0) or 0),
                        "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0) or 0),
                        "volume_24h": float(pair.get("volume", {}).get("h24", 0) or 0),
                        "liquidity": float(pair.get("liquidity", {}).get("usd", 0) or 0),
                    }
    except:
        pass
    return None


async def get_trending_base():
    """Get trending tokens on Base"""
    url = "https://api.dexscreener.com/latest/dex/search?q=base"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                pairs = data.get("pairs", [])
                base_pairs = [p for p in pairs if p.get("chainId") == "base"]
                base_pairs.sort(key=lambda x: float(x.get("volume", {}).get("h24", 0) or 0), reverse=True)
                return base_pairs[:10]
    except:
        return []


# ============ MESSAGE FORMATTING ============

def shorten_address(address: str) -> str:
    return f"{address[:6]}...{address[-4:]}"


async def format_wallet_analysis(wallet: str):
    """Analyze a wallet and format the response"""
    
    # Get data
    eth_price = await get_eth_price()
    eth_balance = await get_eth_balance(wallet)
    token_txns = await get_token_transactions(wallet, 30)
    
    if not token_txns and eth_balance == 0:
        return f"❌ No activity found for this wallet on Base.\n\nMake sure it's a valid Base wallet address."
    
    eth_value_usd = eth_balance * eth_price
    
    # Analyze token activity
    buys = []
    sells = []
    tokens_seen = {}
    
    for tx in token_txns:
        token_address = tx.get("contractAddress", "")
        token_symbol = tx.get("tokenSymbol", "???")
        token_name = tx.get("tokenName", "Unknown")
        decimals = int(tx.get("tokenDecimal", 18))
        value = int(tx.get("value", 0)) / (10 ** decimals)
        
        is_buy = tx.get("to", "").lower() == wallet.lower()
        
        if token_address not in tokens_seen:
            tokens_seen[token_address] = {
                "symbol": token_symbol,
                "name": token_name,
                "address": token_address,
                "buys": 0,
                "sells": 0,
                "buy_amount": 0,
                "sell_amount": 0,
            }
        
        if is_buy:
            tokens_seen[token_address]["buys"] += 1
            tokens_seen[token_address]["buy_amount"] += value
        else:
            tokens_seen[token_address]["sells"] += 1
            tokens_seen[token_address]["sell_amount"] += value
    
    # Build message
    msg = f"""
🔍 *WALLET ANALYSIS*

📍 `{shorten_address(wallet)}`
🔗 [View on Basescan](https://basescan.org/address/{wallet})

💰 *ETH Balance:* {eth_balance:.4f} ETH (${eth_value_usd:,.2f})

"""
    
    # Recent token activity
    if tokens_seen:
        msg += "📊 *RECENT TOKEN ACTIVITY*\n\n"
        
        # Sort by most activity
        sorted_tokens = sorted(tokens_seen.values(), key=lambda x: x["buys"] + x["sells"], reverse=True)[:8]
        
        for token in sorted_tokens:
            symbol = token["symbol"]
            buys = token["buys"]
            sells = token["sells"]
            address = token["address"]
            
            if buys > sells:
                emoji = "🟢"
                action = "BUYING"
            elif sells > buys:
                emoji = "🔴"
                action = "SELLING"
            else:
                emoji = "⚪"
                action = "MIXED"
            
            msg += f"{emoji} *{symbol}* - {action}\n"
            msg += f"   Buys: {buys} | Sells: {sells}\n"
            msg += f"   [Chart](https://dexscreener.com/base/{address})\n\n"
    else:
        msg += "📊 No recent token activity found.\n\n"
    
    # Get info on most traded token
    if sorted_tokens:
        top_token = sorted_tokens[0]
        token_info = await get_token_info(top_token["address"])
        if token_info:
            msg += f"🎯 *TOP TRADED: {token_info['symbol']}*\n"
            msg += f"   💵 Price: ${token_info['price']:.6f}\n"
            msg += f"   📈 24h: {token_info['price_change_24h']:+.1f}%\n"
            msg += f"   💧 Liquidity: ${token_info['liquidity']:,.0f}\n"
    
    return msg


async def format_trending():
    """Format trending tokens message"""
    pairs = await get_trending_base()
    
    if not pairs:
        return "❌ Couldn't fetch trending tokens. Try again later."
    
    msg = "🔥 *TOP TOKENS ON BASE (by 24h volume)*\n\n"
    
    for i, pair in enumerate(pairs[:10], 1):
        symbol = pair.get("baseToken", {}).get("symbol", "???")
        price = float(pair.get("priceUsd", 0) or 0)
        change = float(pair.get("priceChange", {}).get("h24", 0) or 0)
        volume = float(pair.get("volume", {}).get("h24", 0) or 0)
        address = pair.get("baseToken", {}).get("address", "")
        
        if change > 0:
            emoji = "🟢"
        else:
            emoji = "🔴"
        
        msg += f"{i}. *{symbol}* {emoji} {change:+.1f}%\n"
        msg += f"   💵 ${price:.6f} | Vol: ${volume:,.0f}\n"
        msg += f"   [Chart](https://dexscreener.com/base/{address})\n\n"
    
    return msg


# ============ BOT HANDLERS ============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = """
🔵 *Base Wallet Tracker Bot*

Send me any Base wallet address and I'll show you:
• 💰 ETH balance
• 🪙 What tokens they're buying/selling
• 📊 Recent activity

*Commands:*
/trending - Top tokens on Base
/help - Show this message

*Example:*
Just paste a wallet address like:
`0x1234...abcd`
"""
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_command(update, context)


async def trending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Fetching trending tokens...")
    msg = await format_trending()
    await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    # Check if it's a wallet address
    if re.match(r"^0x[a-fA-F0-9]{40}$", text):
        await update.message.reply_text("🔍 Analyzing wallet...")
        msg = await format_wallet_analysis(text.lower())
        await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await update.message.reply_text(
            "❌ That doesn't look like a valid wallet address.\n\n"
            "Send me a Base wallet address (starts with 0x, 42 characters).\n\n"
            "Example: `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`",
            parse_mode="Markdown"
        )


# ============ MAIN ============

def main():
    print("🔵 Base Wallet Bot Starting...")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("trending", trending_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Bot is running! Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
