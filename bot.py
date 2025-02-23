import telebot
from telebot import types
from sqlalchemy import insert, select, delete, and_

from models.bot_notifications_model import Notification
from models.bot_users_model import User
from backend.db_depends import get_db

from config import API_TOKEN, DATE, ADMIN_PASSWORD, ADMIN_CHAT_ID
from time import sleep
from datetime import datetime
import threading
from functions_for_bot import dict_to_datetime, get_weather

API_TOKEN = API_TOKEN
bot = telebot.TeleBot(API_TOKEN)

# 932802232 Liykin_id
user_input_datetime = {
    'year': '',
    'month': '',
    'day': '',
    'time': '',
}
user_message_status = {}
class UserState:
    WAITING = "waiting",
    WAITING_FOR_PASSWORD = "waiting_for_password",
    WAITING_FOR_NOTIFICATION_TEXT = "waiting_for_notification_text",
    WAITING_FOR_SENDER_TEXT = "waiting_for_sender_text",
    WAITING_FOR_NUMBER_TO_DELETE = "waiting_for_number_to_delete",
@bot.message_handler(commands=['admin'])
def admin_password(message):
    if ADMIN_CHAT_ID == message.chat.id:
        user_id = message.chat.id
        user_message_status[user_id] = UserState.WAITING_FOR_PASSWORD
        msg = 'Здарова бурыч, мне нужен, пароль'
        bot.send_message(user_id, msg)
        bot.register_next_step_handler(message, check_password)
    else:
        bot.send_message(message.chat.id, "Ты не бурыч, уходи")


@bot.message_handler(commands=['start', 'menu'])
def main_menu(message):
    user_id = message.chat.id
    user_message_status[user_id] = UserState.WAITING
    user_message_status[user_id] = 'AWAIT'
    print(user_message_status)
    print(message.chat.id, message.chat.first_name, message.chat.last_name, message.chat.username)
    db = next(get_db())
    user_data = (db.execute(select(User).where(User.chat_id == user_id))).fetchall()
    if not user_data:
        user_data = db.execute(insert(User).values(chat_id=user_id,
                                                   name='John Doe',
                                                   first_name=message.chat.first_name,
                                                   last_name=message.chat.last_name,
                                                   username=message.chat.username))
        db.commit()
        bot.send_sticker(user_id, 'CAACAgIAAxkBAAMrZ5sZ_1U15wfDDRTSjfRvGtaxL_UAAhgUAAJOc2BKmEJg3mpifbQ2BA')
        bot.send_message(user_id, 'Занес тебя в базу данных')
        db.close()

    msg = "Выберите опцию:"
    buttons = [
        types.InlineKeyboardButton("✅ Список всех дел ✅", callback_data="button1"),
        types.InlineKeyboardButton("ℹ Создать новое уведомление ℹ", callback_data="button2"),
        types.InlineKeyboardButton("❌ Удалить уведомление ❌", callback_data="button3"),
    ]
    reply_markup = types.InlineKeyboardMarkup(row_width=2)
    for button in buttons:
        reply_markup.add(button)
    bot.send_message(user_id, msg, reply_markup=reply_markup)


@bot.callback_query_handler(lambda c: c.data == 'button1')
def show_all_notifications(callback_query):
    user_id = callback_query.from_user.id
    db = next(get_db())
    all_notifications = db.execute(select(Notification).where(Notification.user_chat_id == user_id)).fetchall()
    db_message = ''
    for notification in all_notifications:
        notification = notification[0]
        db_message += f"№{notification.id}\n{notification.notification_text}\nDate: {notification.date}\n\n"
    db.close()
    if len(all_notifications) == 0:
        bot.send_message(user_id, 'Список дел пуст')
    else:
        bot.send_message(user_id, db_message)


@bot.callback_query_handler(lambda c: c.data == 'button2')
def add_notifications(callback_query):
    user_id = callback_query.from_user.id
    buttons = [types.InlineKeyboardButton(f"{year}", callback_data=f"button_year{i}") for i, year in enumerate(DATE['year'])]
    reply_markup = types.InlineKeyboardMarkup(row_width=2)
    reply_markup.add(*buttons)
    bot.send_message(user_id, 'Введи год', reply_markup=reply_markup)


@bot.callback_query_handler(lambda c: c.data == 'button3')
def add_notifications(callback_query):
    user_id = callback_query.from_user.id
    db = next(get_db())
    all_notifications = db.execute(select(Notification).where(Notification.user_chat_id == user_id)).fetchall()
    db_message = ''
    for notification in all_notifications:
        notification = notification[0]
        db_message += f"Выбирай уведомление, которое хочешь удалить и отравь мне его номер\n\n" \
                      f"№{notification.id}\n{notification.notification_text}\nDate: {notification.date}\n\n"
    db.close()
    if len(all_notifications) == 0:
        bot.send_message(user_id, 'Список дел пуст')
    else:
        bot.send_message(user_id, db_message)
        user_message_status[user_id] = UserState.WAITING_FOR_NUMBER_TO_DELETE


@bot.message_handler(func=lambda message: user_message_status.get(message.chat.id) == UserState.WAITING_FOR_NUMBER_TO_DELETE)
def delete_notification_input(message):
    user_id = message.chat.id
    db = next(get_db())
    db.query(Notification).filter(
        and_(
            Notification.id == int(message.text),
            Notification.user_chat_id == user_id
        )).delete()
    db.commit()
    bot.send_message(user_id, f'Уведомление удалено')
    user_message_status[user_id] = UserState.WAITING


@bot.callback_query_handler(func=lambda c: c.data.startswith('button_year'))
def get_month(callback_query):
    user_id = callback_query.from_user.id
    print(callback_query.data)
    # Извлекаем индекс года из callback_data
    year_index = int(callback_query.data[len('button_year'):])
    # Получаем выбранный год
    selected_year = DATE['year'][year_index]
    user_input_datetime['year'] = str(selected_year)
    buttons = [
        types.InlineKeyboardButton("январь", callback_data="month_1"),
        types.InlineKeyboardButton("февраль", callback_data="month_2"),
        types.InlineKeyboardButton("март", callback_data="month_3"),
        types.InlineKeyboardButton("апрель", callback_data="month_4"),
        types.InlineKeyboardButton("май", callback_data="month_5"),
        types.InlineKeyboardButton("июнь", callback_data="month_6"),
        types.InlineKeyboardButton("июль", callback_data="month_7"),
        types.InlineKeyboardButton("август", callback_data="month_8"),
        types.InlineKeyboardButton("сентябрь", callback_data="month_9"),
        types.InlineKeyboardButton("октябрь", callback_data="month_10"),
        types.InlineKeyboardButton("ноябрь", callback_data="month_11"),
        types.InlineKeyboardButton("декабрь", callback_data="month_12"),
    ]
    reply_markup = types.InlineKeyboardMarkup(row_width=3)
    reply_markup.add(*buttons)
    bot.send_message(callback_query.from_user.id, 'Выбери месяц', reply_markup=reply_markup)


@bot.callback_query_handler(func=lambda c: c.data.startswith('month'))
def get_day(callback_query):
    days_per_month = {
        '01': 31,
        '02': 28,
        '03': 31,
        '04': 30,
        '05': 31,
        '06': 30,
        '07': 31,
        '08': 31,
        '09': 30,
        '10': 31,
        '11': 30,
        '12': 31
    }

    month_index = int(callback_query.data[len('month_'):])
    user_input_datetime['month'] = str(month_index).zfill(2)
    #selected_month = DATE['month'][month_index-1]
    buttons = [types.InlineKeyboardButton(f"{i}", callback_data=f"button_day{i}") for i in range(1, int(days_per_month[user_input_datetime['month']]+1))]
    reply_markup = types.InlineKeyboardMarkup(row_width=7)
    reply_markup.add(*buttons)
    bot.send_message(callback_query.from_user.id, 'Выбери число', reply_markup=reply_markup)


@bot.callback_query_handler(func=lambda c: c.data.startswith('button_day'))
def get_day(callback_query):
    user_input_datetime['day'] = callback_query.data[len('button_day'):]
    print(user_input_datetime)
    buttons = [types.InlineKeyboardButton(f"{time}", callback_data=f"time{i}") for i, time in enumerate(DATE['time'])]
    reply_markup = types.InlineKeyboardMarkup(row_width=6)
    reply_markup.add(*buttons)
    bot.send_message(callback_query.from_user.id, 'Выбери время', reply_markup=reply_markup)


@bot.callback_query_handler(func=lambda c: c.data.startswith('time'))
def get_day(callback_query):
    user_message_status[callback_query.from_user.id] = UserState.WAITING_FOR_NOTIFICATION_TEXT
    user_input_datetime['time'] = DATE['time'][int(callback_query.data[len('time'):])]
    print(user_input_datetime)
    bot.send_message(callback_query.from_user.id, "Введи текст уведомления")
    print(user_message_status)


@bot.message_handler(func=lambda message: user_message_status.get(message.chat.id) == UserState.WAITING_FOR_NOTIFICATION_TEXT)
def notification_text_input(message):
    user_id = message.chat.id
    db = next(get_db())
    user = db.execute(select(User).where(User.chat_id == user_id)).scalar_one_or_none()
    if user:
        # Создаем новое уведомление
        new_notification = Notification(
            notification_text=message.text,
            date=dict_to_datetime(user_input_datetime),
            user=user
        )
        print(f'{message.text}++++++++++++++')
        print(user)
        # Добавляем уведомление в сессию
        db.add(new_notification)
        db.commit()
    user_message_status[user_id] = UserState.WAITING
    bot.send_message(user_id, f"Внес уведомление!")


#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
# Панель админа с проверкой пароля для манипуляций с БД
@bot.message_handler(func=lambda message: user_message_status.get(message.chat.id) == UserState.WAITING_FOR_PASSWORD)
def check_password(message):
    user_id = message.chat.id

    if message.text != ADMIN_PASSWORD:
        print(message.text)
        bot.send_message(user_id, "Пароль неверный")
    else:
        bot.send_message(user_id, "Пароль верный")
        msg = 'Добро пожаловать в админку'

        buttons = [
            types.InlineKeyboardButton("⚡️Рассылка погоды  ⚡️", callback_data="WEATHER"),
            types.InlineKeyboardButton("❤️Радуем подписчиков❤️", callback_data="SENDER"),
            types.InlineKeyboardButton("✅ БД USERS ✅", callback_data="БД USERS"),
            types.InlineKeyboardButton("✅ БД NOTIFICATIONS ✅", callback_data="БД NOTIFICATIONS"),
            types.InlineKeyboardButton("☠ Drop table USERS ☠", callback_data="Drop table USERS"),
            types.InlineKeyboardButton("☠ Drop table NOTIFICATIONS ☠", callback_data="Drop table NOTIFICATIONS"),
        ]
        reply_markup = types.InlineKeyboardMarkup(row_width=2)
        for button in buttons:
            reply_markup.add(button)
        bot.send_message(message.chat.id, msg, reply_markup=reply_markup)
    user_message_status[user_id] = UserState.WAITING



@bot.callback_query_handler(lambda c: c.data == 'БД USERS')
def show_users(callback_query):
    user_id = callback_query.from_user.id
    db = next(get_db())
    all_users = db.execute(select(User)).fetchall()
    db_message = ''
    for user_tuple in all_users:
        user = user_tuple[0]
        db_message += f"ID: {user.id}\nChat ID: {user.chat_id}\nИмя: {user.first_name}\nФамилия: {user.last_name}\n\n"
    db.close()
    if db_message == '':
        bot.send_message(user_id, 'БД USERS пустая')
    else:
        bot.send_message(user_id, db_message)


@bot.callback_query_handler(lambda c: c.data == 'БД NOTIFICATIONS')
def show_notifications(callback_query):
    user_id = callback_query.from_user.id
    db = next(get_db())

    # Выполняем запрос
    all_notifications = db.execute(select(Notification)).fetchall()
    db_message = ''
    for notification in all_notifications:
        notification = notification[0]
        db_message += f"USER: {notification.user_chat_id}\nNotification: {notification.notification_text}\nDate: {notification.date}\n\n"
    db.close()
    if db_message == '':
        bot.send_message(user_id, 'БД NOTIFICATIONS пустая')
    else:
        bot.send_message(user_id, db_message)


@bot.callback_query_handler(lambda c: c.data == 'Drop table USERS')
def drop_table_users(callback_query):
    user_id = callback_query.from_user.id
    db = next(get_db())
    db.execute(delete(User).where(User.name == 'John Doe'))
    db.commit()
    db.close()
    bot.send_message(user_id, "Очистил БД USERS")


@bot.callback_query_handler(lambda c: c.data == 'Drop table NOTIFICATIONS')
def drop_table_notifications(callback_query):
    user_id = callback_query.from_user.id
    db = next(get_db())
    db.execute(delete(Notification))
    db.commit()
    db.close()
    bot.send_message(user_id, "Очистил БД NOTIFICATIONS")


@bot.callback_query_handler(lambda c: c.data == 'SENDER')
def sender(callback_query):
    user_id = callback_query.from_user.id
    user_message_status[user_id] = UserState.WAITING_FOR_SENDER_TEXT
    bot.send_message(user_id, "Введи рассылку шеф")

@bot.message_handler(func=lambda message: user_message_status.get(message.chat.id) == UserState.WAITING_FOR_SENDER_TEXT)
def sender_finisher(message):
    user_id = message.chat.id
    db = next(get_db())
    all_users = db.execute(select(User)).fetchall()
    for user in all_users:
        user = user[0]
        bot.send_message(user.chat_id, message.text)
    db.close()
    bot.send_message(user_id, "Рассылка выполнена, шеф!")


@bot.callback_query_handler(lambda c: c.data == 'WEATHER')
def sender(callback_query):
    user_id = ADMIN_CHAT_ID
    response_from_weather_apis = get_weather()
    db = next(get_db())
    all_users = db.execute(select(User)).fetchall()
    for user in all_users:
        user = user[0]
        bot.send_message(user.chat_id, response_from_weather_apis)
    db.close()
    bot.send_message(user_id, "Рассылка выполнена, шеф!")

#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
# Цикл отправки уведомлений
def check_and_send_notifications():
    db = next(get_db())

    all_data_notifications = db.execute(select(Notification)).fetchall()
    for elem in all_data_notifications:
        notification = elem[0]
        print(notification.date)
        notif_date = notification.date
        current_time = datetime.now()
        time_difference = notif_date - current_time
        if str(time_difference)[0] == '-':
            bot.send_message(notification.user_chat_id, f"Дружище, напоминаю, что у тебя было дельце\n {notification.notification_text}")
            db.execute(delete(Notification).where(Notification.id == notification.id))
            db.commit()
        else:
            pass
    db.close()


def loop1():
    while True:
        check_and_send_notifications()
        sleep(60)

def loop2():
    hour = 0
    while hour != 10:
        hour = datetime.now().hour
        sleep(3600)
    while True:
        user_id = ADMIN_CHAT_ID
        response_from_weather_apis = get_weather()
        db = next(get_db())
        all_users = db.execute(select(User)).fetchall()
        for user in all_users:
            user = user[0]
            bot.send_message(user.chat_id, response_from_weather_apis)
        db.close()
        bot.send_message(user_id, "Рассылка выполнена, шеф!")
        sleep(86400)


thread1 = threading.Thread(target=loop1)
thread2 = threading.Thread(target=loop2)
thread1.start()
thread2.start()


#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as _ex:
            print(f'Блядская ошибка {_ex}')
            sleep(0.3)
#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
# TODO:
#   - Идеи для написания бота
#   - ультрафиолет ✅
#   - том бд
#   - цикл для погоды ✅
#   - расслыка сообщений от админа
#   - изменение клавиатуры без отправки сообщений
#   - поменять систему статуса ожидания сообщения ботом ✅
