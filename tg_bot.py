import telebot
import hh_parser
import os
import create_db

# Замените токен на свой
TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Привет! Введи название вакансии, которую хочешь найти.')

@bot.message_handler(content_types=['text'])
def get_vacancy(message):
    search = message.text
    try:
        text = hh_parser.parseing(search)
        bot.send_message(message.chat.id, text)
        for file in os.listdir('pics'):
            with open(os.path.join('pics', file), 'rb') as f:
                bot.send_photo(message.chat.id, f)
    except:
        bot.send_message(message.chat.id, 'Произошла ошибка! Попробуйте ввести другую вакансию.')


if __name__ == '__main__':
    create_db.create_db()
    bot.polling(none_stop=True)
