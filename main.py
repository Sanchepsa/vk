import vk_api
import sqlite3
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import requests
from random import randint

#245574df4fc0ca71a3b3d51e9278c0b1323cf3d56b4c92119e1f2dbd22f5c459b9dd663f64064d5109c61

#подключим базу данных
con = sqlite3.connect('bot_data.db')
cur = con.cursor()

#готовимся к работе с api и ботом
vk_session = vk_api.VkApi(token='8e063c31978e844cabfb1896980f8c4883387efc910df61c229bdb7c7f256ae3d81772cb190702ad9734f',
                          api_version='5.89')
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()

#дополнительные клавиаутры с кнопками
list_for_buttons = ['Вопросы', 'Отзывы', 'Рейтинг']
common_key = VkKeyboard(one_time=False)
for el in list_for_buttons:
    common_key.add_button(el, VkKeyboardColor.POSITIVE)
list_for_buttons = ['Ответить', 'Загрузить', 'В начало']
quest_key = VkKeyboard(one_time=False)
for el in list_for_buttons:
    quest_key.add_button(el, VkKeyboardColor.POSITIVE)
list_for_buttons = [str(i) for i in range(1, 5)]
variant_key = VkKeyboard(one_time=False)
for el in list_for_buttons:
    variant_key.add_button(el, VkKeyboardColor.PRIMARY)
yes_no_key = VkKeyboard(one_time=False)
yes_no_key.add_button('Да', VkKeyboardColor.POSITIVE)
yes_no_key.add_button('Нет', VkKeyboardColor.NEGATIVE)

params = []

#задаём вопрос пользователю
def ask_me():
    global vk
    global cur
    global quest_key
    global variant_key
    global numbers
    global answered_by
    choosing_question = 0
    for event in longpoll.listen():
        print(answered_by, numbers, sep=' ')
        if answered_by == numbers:
            vk.messages.send(
                user_id=event.user_id,
                message='''
Ого! Видимо, Вы ответили на все вопросы в базе! 
Не хотите ли загрузить свой?
''', keyboard=quest_key.get_keyboard()
            )
            break
        if choosing_question == 0 and event.from_user:
            num_quest = randint(1, max(numbers))
            while num_quest in answered_by:
                num_quest = randint(1, max(numbers))
            if num_quest not in answered_by:
                quest_itself = cur.execute("SELECT quest FROM questions WHERE number = {}".
                                           format(num_quest)).fetchone()
                vk.messages.send(
                    user_id=event.user_id,
                    message=quest_itself, keyboard=variant_key.get_keyboard()
                    )
                choosing_question = 1

        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            correct_here = cur.execute("SELECT correct FROM questions WHERE number = {}".
                                       format(num_quest)).fetchone()[0]
            if event.text == str(correct_here):
                vk.messages.send(
                    user_id=event.user_id,
                    message='Да, верно! Вы получаете 5 баллов в рейтинг!', keyboard=quest_key.get_keyboard()
                )
                current_rate = cur.execute("SELECT points FROM rating WHERE id = {}".
                                       format(event.user_id)).fetchone()[0]
                current_rate = int(current_rate) + 5
                cur.execute("UPDATE rating SET points = {} WHERE id = {}".
                            format(current_rate, event.user_id))
                con.commit()
            else:
                correct_here = 'var' + str(correct_here)
                vk.messages.send(
                    user_id=event.user_id,
                    message='''
К сожалению, это не так(
Правильный ответ: {}'''.format(cur.execute("SELECT {} FROM questions WHERE number = {}".
                                           format(correct_here, num_quest)).fetchone()[0]), keyboard=quest_key.get_keyboard()
                )
            answered_by.append(num_quest)
            answered_by = ' '.join([str(i) for i in sorted(answered_by)])
            print(answered_by)
            cur.execute("UPDATE rating SET answered = ? WHERE id = ?",
                    (str(answered_by), event.user_id))
            con.commit()
            break

# функция загрузки своего вопроса
def load_quest():
    global vk
    global numbers
    global answered_by
    enough = 0
    params = []
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            if enough == 0:
                params = [max(numbers) + 1, event.user_id]
                enough = 1
            print(params, 'here')
            if len(params) == 2:
                vk.messages.send(
                    user_id=event.user_id,
                    message='Нужны 4 варианта ответа. Какой будет первым?'
                )
                params.append(event.text)
            elif len(params) == 3:
                vk.messages.send(
                    user_id=event.user_id,
                    message='Теперь второй'
                )
                params.append(event.text)
            elif len(params) == 4:
                vk.messages.send(
                    user_id=event.user_id,
                    message='Давайте третий'
                )
                params.append(event.text)
            elif len(params) == 5:
                vk.messages.send(
                    user_id=event.user_id,
                    message='И последний - четвёртый'
                )
                params.append(event.text)
            elif len(params) == 6:
                vk.messages.send(
                    user_id=event.user_id,
                    message='Какой из них правильный?'
                )
                params.append(event.text)
            elif len(params) == 7:
                params.append(event.text)
                break
    print(params)
    cur.execute("INSERT INTO questions VALUES(?, ?, ?, ?, ?, ?, ?, ?)", params)
    answered_by.append(max(numbers) + 1)
    answered_by = ' '.join([str(i) for i in sorted(answered_by)])
    print(answered_by)
    cur.execute("UPDATE rating SET answered = ? WHERE id = ?",
                (str(answered_by), params[1]))
    con.commit()
    vk.messages.send(
        user_id=params[1],
        message='Готово! Теперь Ваш вопрос в базе!'
    )


# основной цикл
for event in longpoll.listen():
    #постоянно обновляем список id пользователей и номера всех вопросов в базе
    ids = [int(i[0]) for i in list(cur.execute("SELECT id FROM rating").fetchall())]
    numbers = [i[0] for i in list(cur.execute("SELECT number FROM questions").fetchall())]
    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text\
            and event.from_user:
        answered_by = [int(i) for i in cur.execute("SELECT answered FROM rating WHERE id = {}".
                                                   format(event.user_id)).fetchone()[0].split()]
        if event.user_id not in ids:
            user = vk.users.get(user_ids=event.user_id)
            params = len(ids) + 1, event.user_id, user[0]['first_name'], user[0]['last_name'], 0
            cur.execute("INSERT INTO rating VALUES(?, ?, ?, ?, ?)", params)
            con.commit()
        if event.text.lower() == 'начать' or event.text.lower() == 'старт'\
                or event.text.lower() == 'привет' or event.text.lower() == 'здравствуйте':
            vk.messages.send(
                user_id=event.user_id,
                message='Здравствуйте! Что будем делать?',
                keyboard=common_key.get_keyboard()
            )
        if event.text.lower() == 'вопросы':
            vk.messages.send(
                    user_id=event.user_id,
                    message='Хотите ответить на чей-то? Или загрузить свой?',
                    keyboard=quest_key.get_keyboard()
            )
        if event.text.lower() == 'ответить':
            vk.messages.send(
                    user_id=event.user_id,
                    message='Ищем вопрос...',
                    keyboard = quest_key.get_keyboard()
            )
            ask_me()
        if event.text.lower() == 'загрузить':
            vk.messages.send(
                    user_id=event.user_id,
                    message='Отлично! Сначала введите сам вопрос:')
            load_quest()
        if event.text.lower() == 'в начало':
            vk.messages.send(
                    user_id=event.user_id,
                    message='Возвращаемся обратно)',
                    keyboard = common_key.get_keyboard()
            )
        if event.text.lower() not in ['вопросы', 'ответить', 'загрузить',
                              'рейтинг', 'в начало', 'отзывы', 'привет',
                                      'здравствуйте', 'старт', 'начать']:
            vk.messages.send(
                user_id=event.user_id,
                message='''
К сожалению, мне неизвестна Ваша команде(
Попробуйте выбрать кнопку на клавиатуре''',
                keyboard=common_key.get_keyboard()
            )

con.close()