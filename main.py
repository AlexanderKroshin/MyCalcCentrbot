import telebot
import mariadb
import sys
import datetime


dict_config = {}
with open('config.txt', 'r', encoding='utf-8') as f1:
    lines = f1.readlines()
    for line in lines:
        key = (line.strip().split('='))[0].strip()
        value = (line.strip().split('='))[1].strip()
        if key == 'port':
            value = int(value)
        dict_config[key] = value


bot = telebot.TeleBot(dict_config['bot'])


def find_in_base(find_chet, find_nom=''):
    try:
        with mariadb.connect(
                user=dict_config['user'],
                password=dict_config['password'],
                host=dict_config['host'],
                port=dict_config['port'],
                database=dict_config['database']
        ) as connection:
            print(connection)

            try:
                if len(find_nom) == 0:
                    select_query = f'select flat_chet from counters where flat_chet = {find_chet}'
                else:
                    select_query = f'select flat_chet, counter_srv, counter_nomer, last_evidence from counters where ' \
                                   f'flat_chet = {find_chet} and counter_nomer = {find_nom}'

                with connection.cursor() as cursor:
                    cursor.execute(select_query)
                    result = cursor.fetchall()

                    usl = ''
                    if len(result) > 0 and len(find_nom) != 0:
                        usl = result[0][1]

                    if len(result) > 0:
                        return True, usl
                    else:
                        return False

            except mariadb.Error as e2:
                print(f'Request execution error: {e2}')
                sys.exit(2)

    except mariadb.Error as e:
        print(f'Error connecting to MariaDB Platform: {e}')
        sys.exit(1)


def insert_into_base(text, usl):
    try:
        with mariadb.connect(
                user=dict_config['user'],
                password=dict_config['password'],
                host=dict_config['host'],
                port=dict_config['port'],
                database=dict_config['database']
        ) as connection:
            print(connection)

            try:
                select_query = f'insert into evidences ( ' \
                               f'flat_chet, counter_srv, counter_nomer, evidence_date, evidence_value ) values' \
                               f' ( "{text[1]}", "{usl}", "{text[2]}", "{datetime.date.today()}", {float(text[3])})'
                with connection.cursor() as cursor:
                    cursor.execute(select_query)
                    connection.commit()
                    return True

            except mariadb.Error as e2:
                print(f'Request execution error: {e2}')
                sys.exit(2)

    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)


@bot.message_handler(commands=['start'])
def start(message):
    mess = f'Здравствуйте <b>{message.from_user.first_name} {message.from_user.last_name}! </b>' \
           f'Для передачи показаний приборов учета отправьте сообщение в формате: слово "показание" ' \
           f'9-значный номер лицевого счета из квитанции [пробел] последние 4 цифры номера ' \
           f'Вашего счетчика [пробел] все цифры показания счетчика. ' \
           f'Пример: Предположим, что у Вас в квартире установлен счетчик с номером 03451889, ' \
           f'показание по которому составляет 57.450. 9-значный номер лицевого счета, ' \
           f'указанный в квитанции: 0123-4567-8. В этом случае сообщение будет иметь следующий вид: ' \
           f'<b>показание 012345678 1889 57.450 </b>'
    bot.send_message(message.chat.id, mess, parse_mode='html')


def is_number(s):
    if ',' in s:
        s = s.replace(',', '.')
    try:
        float(s)
        return True
    except ValueError:
        return False


@bot.message_handler()
def get_user_text(message):
    text = message.text.split()

    if len(text) > 0 and text[0].strip().lower() == 'показание':

        if len(text) > 1 and text[1].strip().isdigit() and len(text[1].strip()) == 9:
            ok, _ = find_in_base(text[1].strip())
            if ok:

                if len(text) > 2 and text[2].strip().isdigit() and len(text[2].strip()) == 4:
                    ok, usl_code = find_in_base(text[1].strip(), text[2].strip())
                    if ok:

                        if len(text) > 3 and (text[3].strip().isdigit() or is_number(text[3].strip())):
                            text[3] = text[3].strip().replace(',', '.')

                            if insert_into_base(text, usl_code):
                                mess = f'Ваше показание принято! Благодарим!'
                            else:
                                mess = f'Ошибка передачи показания на сервер!'
                        else:
                            mess = f'Не верно указано показание! (должно быть число)'
                    else:
                        mess = f'Счетчик не найден'
                else:
                    mess = f'Не верно заполнен номер счетчика! (4 последние цифры номера счетчика)'
            else:
                mess = f'Лицевой счет не найден'
        else:
            mess = f'Не верно заполнен номер лицевого счета! (должно быть 9 цифр)'
    else:
        mess = f'Передача показание начинается с ключевого слова "показание" !'

    bot.send_message(message.chat.id, mess)


bot.polling(none_stop=True)
