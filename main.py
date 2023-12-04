TOKEN = "6021826926:AAEdTcE1WoJ9fXia5ivv1jVwe0qXlap1Ybk"
import telebot
from telebot import types
from functools import  lru_cache

import requests

bot = telebot.TeleBot(TOKEN)

users_data = {}

def replace_last_three_chars(input_str):
    if len(input_str) < 3:
        return "***"  # Если строка короче трех символов, заменяем все символы на звездочки
    else:
        return input_str[:-3] + '***'
def format_weather_response(weather_data):
    formatted_text = "Прогноз погоды:\n"

    for i in range(len(weather_data['daily']['time'])):
        date = weather_data['daily']['time'][i]
        min_temp = weather_data['daily']['temperature_2m_min'][i]
        max_temp = weather_data['daily']['temperature_2m_max'][i]
        precipitation = weather_data['daily']['precipitation_sum'][i]

        formatted_text += f"\nДата: {date}\nМинимальная температура: {min_temp}°C\nМаксимальная температура: {max_temp}°C\nСумма осадков: {precipitation} мм\n"

    return formatted_text


@lru_cache(maxsize=10)
def get_weather_by_coordinates(latitude, longitude):
    api_url = f'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&daily=temperature_2m_min,temperature_2m_max,precipitation_sum&timezone=GMT'
    try:
        response = requests.get(api_url)
        data = response.json()
        print(data)
        return data
    except requests.RequestException as e:
        print(f"Error making request: {e}")


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_weather = types.KeyboardButton("Погода")
    markup.add(button_weather)

    bot.send_message(message.chat.id, "Привет! Я бот прогноза погоды.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Погода")
def handle_weather(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_location = types.KeyboardButton("Отправить мою локацию", request_location=True)
    markup.add(button_location)
    bot.send_message(message.chat.id, "Выберите способ ввода местоположения:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Отправить мою локацию")
def handle_location(message):
    bot.send_message(message.chat.id, "Отправьте свою локацию.")

# Обработчик локации
@bot.message_handler(content_types=['location'])
def handle_location_received(message):
    location = message.location
    user_id = message.from_user.id
    user_name = message.from_user.username
    bot.send_message(message.chat.id, f"Получены координаты: {location.latitude}, {location.longitude}")
    wather = get_weather_by_coordinates(location.latitude, location.longitude)
    bot.send_message(message.chat.id, format_weather_response(wather))

    if user_id not in users_data:
        users_data[user_id] = {'username': user_name, 'locations_count': 0}

    users_data[user_id]['locations_count'] += 1

@bot.message_handler(commands=['top'])
def handle_top(message):
    # Сортируем пользователей
    top_users = sorted(users_data.values(), key=lambda x: x['locations_count'], reverse=True)

    # Отправляем топ пользователей в чат
    top_message = "Топ пользователей по количеству отправленных локаций:\n"
    for i, user in enumerate(top_users[:5], start=1):
        top_message += f"{i}. {replace_last_three_chars(user['username'])} - {user['locations_count']} раз(а)\n"

    bot.send_message(message.chat.id, top_message)

# Главная функция
if __name__ == '__main__':
    bot.polling(none_stop=True)