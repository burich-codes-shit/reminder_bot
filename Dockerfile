FROM python:3.11
# Устанавливаем переменную окружения для московского времени
ENV TZ=Europe/Moscow

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Настраиваем часовой пояс
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Запускаем бота
CMD ["python", "bot.py"]
