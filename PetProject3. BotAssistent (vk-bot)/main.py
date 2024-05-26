import datetime
import sqlite3
import random
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

#####  ВСТАВИТЬ СВОЮ ИНФОРМАЦИЮ  ###
				   #
TOKEN = Ключ_Доступа		   #			
CLUB = ID_Сообщества		   #
vk_prepod = ID_пользователя	   #
				   #
####################################

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, CLUB)

keyboard4 = open('keyboard4.json', 'r', encoding='UTF-8').read()
group_keyboard = open('group_keyboard.json', 'r', encoding='UTF-8').read()


def sender(vk_id, text, keyboard=None):
    """
    Функция для отправки пользователю сообщения
    :param vk_id: ID пользователя, приславшего сообщение, в ВКонтакте
    :param text: текст сообщения, которое будет отправлено пользователю
    :param keyboard: клавиатура, которая будет отправлена пользователю
    :return: None
    """
    vk_session.method('messages.send', {'user_id': vk_id, 'message': text,
                                        'random_id': random.randint(0, 2 ** 64),
                                        'keyboard': keyboard})


def get_groups():
    """
    Функция для получения из БД списка групп
    :return: Словарь со списком групп {"Группа": "Код"}
    """
    con = sqlite3.connect("IIT_1kurs.db")
    cur = con.cursor()
    results = cur.execute("SELECT * FROM groups").fetchall()
    con.close()  # Закрываем подключение к БД
    d = {}
    for elem in results:
        d[elem[1].lower()] = elem[0]
    return d


def check_id(vk_id):
    """
    Функция для поиска в БД информации о пользователе по его ID в ВКонтакте
    :param vk_id: ID пользователя, приславшего сообщение, в ВКонтакте
    :return: кортеж значений из таблицы students, или None (если пользователь пишет впервые и в БД не зафиксирован)
    """
    con = sqlite3.connect("IIT_1kurs.db")
    cur = con.cursor()
    results = cur.execute("SELECT * FROM students WHERE vk_id = ?", (str(vk_id),)).fetchall()
    con.close()  # Закрываем подключение к БД
    return results


def check_fam_group(fam, group):
    """
    Функция для поиска в БД информации о пользователе по его фамилии и группе
    :param fam: фамилия пользователя, как он сам ее написал
    :param group: группа пользователя, из клавиатуры
    :return: кортеж значений из таблицы students, или None (если пользователь ошибся в написании фамилии)
    """
    con = sqlite3.connect("IIT_1kurs.db")
    cur = con.cursor()
    group_id = GROUPS[group]
    res = cur.execute("SELECT * FROM students WHERE fam = ? and group_id = ?", (fam.capitalize(), group_id,)).fetchall()
    con.close()  # Закрываем подключение к БД
    return res


def update_vk_id(vk_id, fam, group):
    """
    Функция находит по фамилии и группе студента и записывает в БД ID пользователя в ВКонтакте
    :param vk_id: ID пользователя в ВКонтакте
    :param fam: фамилия пользователя, как он сам ее написал
    :param group: группа пользователя, из клавиатуры
    :return: None
    """
    try:
        con = sqlite3.connect("IIT_1kurs.db")
        cur = con.cursor()
        print('Подключен к  SQLite')
        group_id = GROUPS[group]
        print(vk_id, fam.capitalize(), group, group_id)
        cur.execute("UPDATE students SET vk_id = ? WHERE fam = ? and group_id = ?", (vk_id, fam.capitalize(), group_id,)).fetchall()
        con.commit()
        print('Запись успешно обновлена')
        con.close()  # Закрываем подключение к БД

    except sqlite3.Error as error:
        print("Ошибка при работе с SQLite", error)

    finally:
        if con:
            con.close()
            print("Соединение с SQLite закрыто")


def get_progress(vk_id):
    """
    Функция получает из БД список зачтенных лабораторных работ для конкретного пользователя
    :param vk_id: ID пользователя в ВКонтакте
    :return: список кортежей вида ("Название работы", "Тема")
    """
    con = sqlite3.connect("IIT_1kurs.db")
    cur = con.cursor()
    res = cur.execute("SELECT works.name, works.theme FROM (vedomost INNER JOIN students \
                    ON students.student_id = vedomost.student_id) INNER JOIN works \
                    ON vedomost.work_id = works.work_id WHERE students.vk_id = ?", (str(vk_id),)).fetchall()
    con.close()  # Закрываем подключение к БД
    return res

class User():
    """
    класс Пользователя для внутреннего использования в программе
    """
    def __init__(self, vk_id, status, group_id, student_id, fam, name):
        self.student_id = student_id
        self.fam = fam
        self.name = name
        self.group_id = group_id
        self.vk_id = vk_id
        self.status = status    # для запоминания, в каком пункте меню он сейчас находится


#####################################################################################################################
GROUPS = get_groups()   # получаем группы из БД (словарь "группа": "код")
users = []              # список пользователей, с которыми в данный момент ведутся беседы (чтобы робот не путал реплики)

for event in longpoll.listen():

    if event.type == VkBotEventType.MESSAGE_NEW:

        vk_id = event.obj.message['from_id']
        msg = event.obj.message['text'].lower()

        check = check_id(vk_id)  # проверяем, есть ли у нас такой ID в базе

        flag = 0                # признак наличия такого ID в списке users (оперативные данные)
        for user in users:      # ищем пользователя в списке users (все, с кем сейчас ведутся беседы)
            if user.vk_id == vk_id:     # если нашелся - значит работаем с известным собеседником, занесенным в users

                if user.status < 10:        # статус<10 - пользователь, не зарегистрированный в БД

                    if check:
                        menu0 = f"Привет, {check[0][2].capitalize()}! Выбери, что хочешь сделать:\n1 - Решить задачу" \
                                f"\n2 - Узнать дату экзамена(зачета)\n3 - Посмотреть успеваемость\n4 - Написать преподавателю"
                        sender(user.vk_id, menu0, keyboard4)
                        user.status = 10    # статус=10 - зарегистрированный пользователь, с ним общаемся в другой части программы

                    elif not check and user.status == 0:
                        sender(user.vk_id, 'Привет! Вижу, ты здесь первый раз! Из какой ты группы?', group_keyboard)
                        user.status = 1         # неопознанная антилопа, пришла в первый раз. Ожидается группа
                    elif not check and user.status == 1:
                        if msg not in GROUPS:
                            sender(user.vk_id, 'Твоя группа?', group_keyboard)
                            user.status = 1     # незарегистрированный пользователь, ошибся с вводом группы. Ожидается группа
                        else:
                            group = msg
                            sender(user.vk_id, 'Твоя фамилия?')
                            user.status = 2     # незарегистрированный пользователь, ожидается фамилия
                    elif not check and user.status == 2:
                        sender(user.vk_id, 'Проверяю, есть ли такой студент...')
                        check2 = check_fam_group(msg, group)
                        if check2:
                            fam = msg
                            sender(user.vk_id, f'Окей, я тебя запомнила {chr(128515)}\nНапиши что-нибудь')
                            update_vk_id(vk_id, fam, group)
                            user.status = 10    # пользователь идентифицирован, его ID в vk внесен в БД
                        else:
                            sender(user.vk_id, 'Такого студента не нашлось... Попробуй еще раз :-)')
                            user.status = 0     # идентификация не прошла, начинаем всё заново


                else:                       # статус >= 10  - зарегистрированный пользователь, общаемся здесь
                    menu0 = f"Привет, {check[0][2].capitalize()}! Выбери, что хочешь сделать:\n1 - Решить задачу" \
                            f"\n2 - Узнать дату экзамена(зачета)\n3 - Посмотреть успеваемость\n4 - Написать преподавателю"

                    if user.status == 10 and msg not in ['1', '2', '3', '4']:   # нажал что попало
                        sender(user.vk_id, menu0, keyboard4)

                    elif user.status == 10 and msg == '1':                      # пункт меню "Решить задачу"
                        con = sqlite3.connect("IIT_1kurs.db")
                        cur = con.cursor()
                        res = cur.execute("SELECT * FROM tasks").fetchall()     # получаем список задач из БД
                        con.close()  # Закрываем подключение к БД

                        sender(user.vk_id, 'Реши задачу:')
                        elem = random.choice(res)
                        question, answer = elem[1], elem[2]
                        sender(user.vk_id, question)
                        user.status = 101                                       # статус "ожидается ответ на задачу"

                    elif user.status == 101:                                    # ожидается ответ на задачу
                        if msg == answer.lower():
                            sender(user.vk_id, "Правильно! Молодец :-)")
                        else:
                            sender(user.vk_id, f"Ответ неверный {chr(128128)}")
                        user.status = 10
                        sender(user.vk_id, '-' * 15)
                        sender(user.vk_id, menu0, keyboard4)

                    elif user.status == 10 and msg == '2':                      # пункт меню "Узнать дату экзамена"
                        con = sqlite3.connect("IIT_1kurs.db")
                        cur = con.cursor()
                        res = cur.execute("SELECT * FROM exams WHERE group_id = ?", (str(check[0][4]),)).fetchall()
                        con.close()  # Закрываем подключение к БД

                        for elem in GROUPS.items():
                            if elem[1] == check[0][4]:
                                group = elem[0].upper()
                                break
                        fepo = 'В форме тестирования ФЕПО.' if res[0][3] == 1 else ""
                        message = f'Экзамен(зачет) по Информатике в группе {group} состоится {res[0][1]}, ауд.{res[0][2]}.\n{fepo}'
                        sender(user.vk_id, message)

                        d, m, y = res[0][1].split('.')
                        exam_date = datetime.date(int(y), int(m), int(d))
                        now = datetime.datetime.now().date()
                        days_last = str(exam_date - now).split()[0]     # посчитать, сколько дней осталось до экзамена
                        message = f'{days_last} дней осталось {chr(128293)} Пора начинать готовиться!\n\n'

                        sender(user.vk_id, message)
                        sender(user.vk_id, '-' * 15)
                        sender(user.vk_id, menu0, keyboard4)

                    elif user.status == 10 and msg == '3':                      # пункт меню "Посмотреть успеваемость"
                        works = get_progress(vk_id)
                        if len(works):
                            d = {}
                            for work in works:
                                if work[1] in d:
                                    d[work[1]].append(work[0])
                                else:
                                    d[work[1]] = [work[0]]
                            sender(user.vk_id, "Список зачтенных работ по темам:")
                            for theme, work in d.items():
                                accepted_works = "\n".join(work)
                                sender(user.vk_id, f'{theme}:\n{accepted_works}')
                        else:
                            sender(user.vk_id, f"Что-то ни одной работы не зачтено. \n"
                                               f"Надо поднапрячься {chr(128170)}{chr(128515)}")

                        sender(user.vk_id, '-' * 15)
                        sender(user.vk_id, menu0, keyboard4)

                    elif user.status == 10 and msg == '4':                      # пункт меню "Написать преподавателю"
                        sender(user.vk_id, "Пиши, я всё передааам...")
                        user.status = 104                                       # статус "пишет сообщение преподавателю"

                    elif user.status == 104:                                    # пишет сообщение преподавателю
                        for elem in GROUPS.items():
                            if elem[1] == check[0][4]:
                                group = elem[0].upper()
                                break
                        message = f'Эгей, Хозяин! Студент(ка) {check[0][1]} {check[0][2]} из группы {group} тебе вот что написал(а):\n {msg}'
                        sender(vk_prepod, message)                              # сообщение преподавателю от робота
                        sender(user.vk_id, 'Преподаватель получил твоё сообщение, он ответит на него позже...')   # сообщение студенту
                        user.status = 10

                        sender(user.vk_id, '-' * 15)
                        sender(user.vk_id, menu0, keyboard4)

                flag = 1    # пользователь находится в списке users, и мы с ним отработали одну реплику

        if flag == 0:           # пользователя не нашлось в списке users
            users.append(User(vk_id, 0, 'group_id', 'student_id', 'fam', 'name'))
            sender(vk_id, "Начнём?")
