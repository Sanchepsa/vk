import vk_api
import sqlite3
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from random import randint
import datetime
from vk_api import VkUpload

#подключим базу данных
con = sqlite3.connect('bot_data.db')
cur = con.cursor()

#id группы и основного альбома
group_id = 204207195
album_id = 278944463

# готовимся к работе с api и ботом
vk_session = vk_api.VkApi(
    token='8e063c31978e844cabfb1896980f8c4883387efc910df61c229bdb7c7f256ae3d81772cb190702ad9734f',
    api_version='5.89')
longpoll = VkLongPoll(vk_session)
upload = VkUpload(vk_session)
vk = vk_session.get_api()

# дополнительные клавиаутры с кнопками
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
feed_key = VkKeyboard(one_time=False)
list_for_buttons = ['Оставить', 'Посмотреть', 'В начало']
for el in list_for_buttons:
    feed_key.add_button(el, VkKeyboardColor.POSITIVE)

params = []
#пароль для просмотра отзывов
pass_for_feedback = 'kLDJ;i01pc'


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
        #список отвеченных равен списку всех вопросов
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
            #автор вопроса не может получить свой же вопрос
            num_quest = randint(1, max(numbers))
            while num_quest in answered_by:
                num_quest = randint(1, max(numbers))
            if num_quest not in answered_by:
                quest_itself = cur.execute("SELECT * FROM questions WHERE number = {}".
                                           format(num_quest)).fetchone()
                author_id = quest_itself[1]
                vk.messages.send(
                    user_id=event.user_id,
                    message='''
{}
1) {}
2) {}
3) {}
4) {}
Нажмите на цифру варинта, который считаете верным'''.format(quest_itself[2],
                                                            quest_itself[3], quest_itself[4],
                                                            quest_itself[5], quest_itself[6]),
                    keyboard=variant_key.get_keyboard()
                )
                choosing_question = 1

        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            if event.text == str(quest_itself[7]):
                vk.messages.send(
                    user_id=event.user_id,
                    message='''
Да, верно! 
Вы получаете 5 баллов!''', keyboard=quest_key.get_keyboard()
                )
                vk.messages.send(
                    user_id=author_id,
                    message='''
На Ваш вопрос правильно ответили.
Вы получаете 5 баллов!
Хотите загрузить ещё один вопрос?)''', keyboard=common_key.get_keyboard()
                )
                for el in [event.user_id, author_id]:
                    current_rate = cur.execute("SELECT points FROM rating WHERE id = {}".
                                               format(el)).fetchone()[0]
                    current_rate = int(current_rate) + 5
                    cur.execute("UPDATE rating SET points = {} WHERE id = {}".
                                format(current_rate, el))
                    con.commit()
            else:
                correct_here = 'var' + str(quest_itself[7])
                vk.messages.send(
                    user_id=event.user_id,
                    message='''
К сожалению, это не так(
Правильный ответ: {}'''.format(cur.execute("SELECT {} FROM questions WHERE number = {}".
                                           format(correct_here, num_quest)).fetchone()[0]),
                    keyboard=quest_key.get_keyboard()
                )
                vk.messages.send(
                    user_id=author_id,
                    message='''
На Ваш вопрос не смогли правильно ответить.
Вы получаете 10 баллов!
Хотите загрузить ещё один вопрос?)''', keyboard=common_key.get_keyboard()
                )
                current_rate = cur.execute("SELECT points FROM rating WHERE id = {}".
                                           format(author_id)).fetchone()[0]
                current_rate = int(current_rate) + 10
                cur.execute("UPDATE rating SET points = {} WHERE id = {}".
                            format(current_rate, author_id))
                con.commit()
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
                    message='Какой из них правильный? (Только номер - от 1 до 4)'
                )
                params.append(event.text)
            elif len(params) == 7:
                params.append(event.text)
                break
    cur.execute("INSERT INTO questions VALUES(?, ?, ?, ?, ?, ?, ?, ?)", params)
    #формируем список вопросов, на которые пользователь уже ответил
    answered_by.append(max(numbers) + 1)
    answered_by = ' '.join([str(i) for i in sorted(answered_by)])
    cur.execute("UPDATE rating SET answered = ? WHERE id = ?",
                (str(answered_by), params[1]))
    con.commit()
    vk.messages.send(
        user_id=params[1],
        message='Готово! Теперь Ваш вопрос в базе!'
    )

#вывести рейтинг игроков
def get_rating(whom):
    global vk
    global cur
    global ids
    #максимум 10 мест для вывода
    if len(ids) >= 10:
        how_many = 10
    else:
        how_many = len(ids)
    first10places = cur.execute('''
    SELECT surname, name, points FROM rating ORDER BY points DESC''').fetchall()[0:how_many]
    for person in enumerate(first10places):
        vk.messages.send(
            user_id=whom,
            message=str(person[0] + 1) + '. ' + ' '.join(person[1][:2]) + \
                    ' (' + str(person[1][2]) + ')'
        )

#получить отзыв - забить в базу
def get_feedback():
    global vk
    global cur
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            feed_from_one = event.text
            user = vk.users.get(user_ids=event.user_id)
            params = (str(datetime.datetime.now()).split('.')[0],
                      int(event.user_id), user[0]['last_name'], user[0]['first_name'],
                      feed_from_one)
            cur.execute("INSERT INTO feedback VALUES(?, ?, ?, ?, ?)", params)
            con.commit()
            vk.messages.send(
                user_id=event.user_id,
                message='Спасибо!',
                keyboard=common_key.get_keyboard()
            )
            break

#показать отзывы, если введён пароль
def check_feeds():
    global vk
    global cur
    pass_asked = 0
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            if event.text == pass_for_feedback:
                all_feeds = cur.execute("SELECT * FROM feedback").fetchall()
                for el in all_feeds:
                    vk.messages.send(
                        user_id=event.user_id,
                        message='''
{}
{}
{} {}
(id:{})
{}'''.format(str(el[0]).split()[0], str(el[0]).split()[1], el[2], el[3], el[1], el[4]),
                        keyboard=common_key.get_keyboard()
                    )
            else:
                vk.messages.send(
                    user_id=event.user_id,
                    message='Не то, зайдите чуть позже)'
                )
            break


# основной цикл
for event in longpoll.listen():
    # постоянно обновляем список id пользователей и номера всех вопросов в базе
    ids = [int(i[0]) for i in list(cur.execute("SELECT id FROM rating").fetchall())]
    numbers = [i[0] for i in list(cur.execute("SELECT number FROM questions").fetchall())]
    if numbers == []:
        numbers = [0]
    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text \
            and event.from_user:
        if event.user_id not in ids:
            user = vk.users.get(user_ids=event.user_id)
            params = len(ids) + 1, event.user_id, user[0]['last_name'], user[0]['first_name'], 0, ''
            cur.execute("INSERT INTO rating VALUES(?, ?, ?, ?, ?, ?)", params)
            con.commit()
        answered_by = [int(i) for i in cur.execute("SELECT answered FROM rating WHERE id = {}".
                                                   format(event.user_id)).fetchone()[0].split()]

        if event.text.lower() == 'начать' or event.text.lower() == 'старт' \
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
                keyboard=quest_key.get_keyboard()
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
                keyboard=common_key.get_keyboard()
            )
        if event.text.lower() == 'отзывы':
            vk.messages.send(
                user_id=event.user_id,
                message='''
Хотите оставить свой? 
Или посмотреть другие при наличии пароля?)''',
                keyboard=feed_key.get_keyboard()
            )
        if event.text.lower() == 'оставить':
            vk.messages.send(
                user_id=event.user_id,
                message='''
Напишите, пожалуйста, свой отзыв)'''
            )
            get_feedback()
        if event.text.lower() == 'посмотреть':
            vk.messages.send(
                user_id=event.user_id,
                message='Пароль?)'
            )
            check_feeds()
        if event.text.lower() == 'рейтинг':
            vk.messages.send(
                user_id=event.user_id,
                message='Вот рейтинг по состоянию на ' + str(datetime.datetime.now()).split()[0],
                keyboard=common_key.get_keyboard()
            )
            get_rating(event.user_id)
        if event.text.lower() not in ['вопросы', 'ответить', 'загрузить',
                                      'рейтинг', 'в начало', 'отзывы', 'привет',
                                      'здравствуйте', 'старт', 'начать',
                                      'оставить', 'посмотреть']:
            vk.messages.send(
                user_id=event.user_id,
                message='''
К сожалению, мне неизвестна Ваша команде(
Попробуйте выбрать кнопку на клавиатуре''',
                keyboard=common_key.get_keyboard()
            )

con.close()
