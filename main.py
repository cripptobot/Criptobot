import telebot

API_TOKEN = '8090315267:AAGIBZsJXx88IGcXw1a37s8mHlwiaprVEBQ'

bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Bu mening Telegram kripto signal botim.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Kechirasiz, men hozir faqat /start va /help komandalarini tushunaman.")

bot.polling()
