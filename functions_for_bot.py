from datetime import datetime
import requests
from config import API_KEY_WEATHER


def dict_to_datetime(user_input_datetime: dict):
    year = int(user_input_datetime['year'])
    month = int(user_input_datetime['month'])
    day = int(user_input_datetime['day'])
    time_str = user_input_datetime['time']

    hours, minutes = map(int, time_str.split(':'))
    dt = datetime(year, month, day, hours, minutes)
    user_input_datetime['year'] = ''
    user_input_datetime['month'] = ''
    user_input_datetime['day'] = ''
    user_input_datetime['time'] = ''
    return dt


def get_weather(city_name="Москва"):
    # URL для запроса текущей погоды
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_KEY_WEATHER}&units=metric&lang=ru"

    try:
        # Отправляем GET-запрос
        response = requests.get(url)
        data = response.json()  # Парсим JSON-ответ

        # Проверяем, успешен ли запрос
        if data["cod"] != 200:
            print(f"Ошибка: {data['message']}")
            return

        # Извлекаем данные о погоде
        weather_description = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
        wind_speed = data["wind"]["speed"]
        feels_like = data["main"]["feels_like"]
        temp_min = data["main"]["temp_min"]
        temp_max = data["main"]["temp_max"]

        url_1 = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
        response = requests.get(url_1)
        data = response.json()
        today = datetime.utcnow().strftime("%Y-%m-%d")
        today_data = [entry for entry in data if entry[0].startswith(today)]
        k_index_values = [float(entry[1]) for entry in today_data]
        max_k_index = max(k_index_values)

        # Выводим информацию
        result = (
            f"🌤️Погода в городе {city_name}🌤️:\n"
            f"Описание: {weather_description}\n"
            f"Температура сейчас: {temperature}°C\n"
            f"Температура на протяжение дня: {temp_min} ... {temp_max}\n"
            f"Скорость ветра: {wind_speed} м/с\n"
            f"Ощущается как: {feels_like}\n"
            f"🧲Магнитные бури: {max_k_index}🧲")

        return result

    except Exception as e:
        print(f"Произошла ошибка: {e}")


get_weather()


