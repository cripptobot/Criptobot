import telebot
import requests
import pandas as pd
import numpy as np
import time

# Sizning Telegram bot tokeningiz
API_TOKEN = '8090315267:AAGIBZsJXx88IGcXw1a37s8mHlwiaprVEBQ'

bot = telebot.TeleBot(API_TOKEN)

# Binance API endpointlari
BINANCE_API = 'https://api.binance.com/api/v3/klines'

# Funksiya: Binance dan OHLCV ma'lumotlarni olish (1 soatlik)
def get_ohlcv(symbol='BTCUSDT', interval='1h', limit=100):
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }
    try:
        response = requests.get(BINANCE_API, params=params)
        data = response.json()
        df = pd.DataFrame(data, columns=[
            'OpenTime', 'Open', 'High', 'Low', 'Close', 'Volume',
            'CloseTime', 'QuoteAssetVolume', 'NumberOfTrades',
            'TakerBuyBaseAssetVolume', 'TakerBuyQuoteAssetVolume', 'Ignore'
        ])
        df['Close'] = df['Close'].astype(float)
        df['Open'] = df['Open'].astype(float)
        df['High'] = df['High'].astype(float)
        df['Low'] = df['Low'].astype(float)
        df['Volume'] = df['Volume'].astype(float)
        return df
    except Exception as e:
        print(f"Error fetching OHLCV: {e}")
        return None

# Funksiya: RSI hisoblash
def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Funksiya: MACD hisoblash
def calculate_macd(data, fast=12, slow=26, signal=9):
    exp1 = data['Close'].ewm(span=fast, adjust=False).mean()
    exp2 = data['Close'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

# Funksiya: ATR (Average True Range) hisoblash (volatility)
def calculate_atr(data, period=14):
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    return atr

# Funksiya: Signal aniqlash (oddiy misol, yaxshilash mumkin)
def generate_signal(df):
    rsi = calculate_rsi(df).iloc[-1]
    macd, signal_line, hist = calculate_macd(df)
    macd_val = macd.iloc[-1]
    signal_val = signal_line.iloc[-1]
    atr = calculate_atr(df).iloc[-1]
    close_price = df['Close'].iloc[-1]

    signal = "Aniq signal yo‘q"
    risk_level = "O‘rtacha"
    
    # Oddiy shartlar bilan signal
    if rsi < 30 and macd_val > signal_val:
        signal = "BUY"
        risk_level = "Past"
    elif rsi > 70 and macd_val < signal_val:
        signal = "SELL"
        risk_level = "Past"

    # Stop loss va take profit oddiy hisoblash
    stop_loss = close_price * 0.98 if signal == "BUY" else close_price * 1.02
    take_profit = close_price * 1.05 if signal == "BUY" else close_price * 0.95

    return {
        "signal": signal,
        "rsi": round(rsi, 2),
        "macd": round(macd_val, 5),
        "close_price": round(close_price, 5),
        "stop_loss": round(stop_loss, 5),
        "take_profit": round(take_profit, 5),
        "risk_level": risk_level,
        "atr": round(atr, 5)
    }

# Telegram bot komandasi: /start va /help
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message,
                 "Salom! Bu kripto signal bot.\n"
                 "Buyruqlar:\n"
                 "/signal - Kripto signalini ko‘rsatadi")

# Telegram bot komandasi: /signal
@bot.message_handler(commands=['signal'])
def send_signal(message):
    df = get_ohlcv('BTCUSDT')
    if df is None:
        bot.reply_to(message, "Ma'lumotlarni olishda xatolik yuz berdi.")
        return
    
    signal_data = generate_signal(df)
    if signal_data['signal'] == "Aniq signal yo‘q":
        bot.reply_to(message, "Hozircha aniq signal mavjud emas.")
    else:
        text = (f"Signal: {signal_data['signal']}\n"
                f"Narx: {signal_data['close_price']} USD\n"
                f"RSI: {signal_data['rsi']}\n"
                f"MACD: {signal_data['macd']}\n"
                f"ATR: {signal_data['atr']}\n"
                f"Risk darajasi: {signal_data['risk_level']}\n"
                f"Stop-Loss: {signal_data['stop_loss']}\n"
                f"Take-Profit: {signal_data['take_profit']}\n"
                f"Vaqt: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} UTC")
        bot.reply_to(message, text)

# Boshqa xabarlarga oddiy javob
@bot.message_handler(func=lambda message: True)
def fallback(message):
    bot.reply_to(message, "Iltimos, /signal komandasidan foydalaning.")

# Botni ishga tushirish
bot.polling()
