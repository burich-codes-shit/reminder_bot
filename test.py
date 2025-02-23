from datetime import datetime
from time import sleep

## Преобразуем строку в объект datetime
#notif_date_string = '2025-02-05 15:51:00'
#notif_date = datetime.strptime(notif_date_string, '%Y-%m-%d %H:%M:%S')
#
#
#current_time = datetime.now()
#time_difference = notif_date - current_time
#if str(time_difference)[0] == '-':
#    print(True)
#else:
#    pass
#print(str(time_difference)[0])

minute = 99
while minute != 2:
    minute = datetime.now().minute
    print(minute)
    sleep(10)
while True:
    print("HELLO")
    sleep(10)



