import vk_api
import sqlite3
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import requests

#подключим базу данных
con = sqlite3.connect('bot_data.db')
cur = con.cursor()

#готовимся к работе с api и ботом
vk_session = vk_api.VkApi(token='245574df4fc0ca71a3b3d51e9278c0b1323cf3d56b4c92119e1f2dbd22f5c459b9dd663f64064d5109c61',
                          api_version='5.89')
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()

#дополнительные клавиаутры с кнопками
list_for_buttons = ['Вопросы', 'Отзывы', 'Рейтинг']
common_key = VkKeyboard(one_time=True)
for el in list_for_buttons:
    common_key.add_button(el, VkKeyboardColor.POSITIVE)
list_for_buttons = ['Ответить на вопрос', 'Залить вопрос']
quest_key = VkKeyboard(one_time=True)
for el in list_for_buttons:
    quest_key.add_button(el, VkKeyboardColor.POSITIVE)
list_for_buttons = [str(i) for i in range(1, 5)]
variant_key = VkKeyboard(one_time=True)
for el in list_for_buttons:
    variant_key.add_button(el, VkKeyboardColor.PRIMARY)
yes_no_key = VkKeyboard(one_time=True)
yes_no_key.add_button('Да', VkKeyboardColor.POSITIVE)
yes_no_key.add_button('Нет', VkKeyboardColor.NEGATIVE)


# основной цикл
here_or_not = 0
for event in longpoll.listen():
    if here_or_not == 0:
        vk.messages.send(
            user_id=event.user_id,
            message='''
Добро пожаловать в бота-викторину! 

Здесь Вы можете отвечать на вопросы других игроков, загружать собственные и получать баллы. 

Сможете попасть в топ-10 рейтинга?)

Открывайте клавиаутру и начинайте))''', random_id=0,
            keyboard=common_key.get_keyboard()
        )
        here_or_not = 1
    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text\
            and event.from_user:
        if event.text == 'Вопросы':
            vk.messages.send(
                    user_id=event.user_id,
                    message='Хотите ответить на чей-то? Или загрузить свой?', random_id=0,
                    keyboard=quest_key.get_keyboard()
            )
        if event.text == 'Ответить на вопрос':
            vk.messages.send(
                    user_id=event.user_id,
                    message='Хорошо',
                    keyboard = quest_key.get_keyboard()
            )
            ask_me(event, variant_key, vk)

con.close()