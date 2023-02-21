import asyncio
import base64
import datetime
import random

import aioschedule
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, ContentType
from aiogram.utils.executor import start_polling

from food_bd import global_init, create_session, User, Ingestion

TOKEN = 'token'
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
close = InlineKeyboardButton('❌ Закрыть', callback_data='close')
back = InlineKeyboardButton('🏘 Главное меню', callback_data='menu')
inline_btn_1 = InlineKeyboardButton('📜 Список приемов пищи', callback_data='my_ingestions')
main_menu = InlineKeyboardMarkup(row_width=1).add(inline_btn_1, close)


class Save_eat(StatesGroup):
    food_name = State()


def exists(tg_id):
    session = create_session()
    if session.query(User).filter(User.user_tg_id == tg_id).first() == None:
        new_user = User()
        new_user.user_tg_id = tg_id
        new_user.week = 0
        session.add(new_user)
        session.commit()


def get_date_by_weekday(need, delta):
    delta = int(delta) * 7
    today = datetime.datetime.today().weekday() + 1
    return '_'.join(
        str(datetime.datetime.today().date() + datetime.timedelta(delta) - datetime.timedelta(today - need)).split('-'))


def get_ingest(tg_id, date):
    session = create_session()
    ingests = session.query(Ingestion).filter(Ingestion.user_tg_id == tg_id).filter(Ingestion.date == date).all()
    text = ''
    for i in ingests:
        text += f'*{(i.type_eat[0]).upper()}{i.type_eat[1:]}* - {i.food_name}\n'
    return text


@dp.callback_query_handler(
    lambda callback_query: callback_query.data and callback_query.data.startswith('eat'))
async def main_menu_by_callback(callback_query: types.CallbackQuery, state: FSMContext):
    eat_type = callback_query.data.split('_')[-1]
    if eat_type == 'breakfast':
        eat_type = 'Завтрак'
    elif eat_type == 'dinner':
        eat_type = 'Обед'
    else:
        eat_type = 'Ужин'
    async with state.proxy() as data:
        data['eat_type'] = eat_type
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id,
                                text=f'Отлично, можете просто написать или отправить фото(если надо с подписью) того что ели на  {eat_type}.')
    await Save_eat.food_name.set()


@dp.message_handler(state=Save_eat.food_name)
async def main_menu_by_text(message: types.Message, state: FSMContext):
    food_name = message.text
    new_ingest = Ingestion()
    new_ingest.food_name = food_name
    async with state.proxy() as data:
        eat_type = data['eat_type']
    new_ingest.type_eat = eat_type
    new_ingest.user_tg_id = message.chat.id
    new_ingest.date = '_'.join(str(datetime.datetime.today().date()).split('-'))
    session = create_session()
    session.add(new_ingest)
    session.commit()
    await state.finish()
    await bot.send_message(text='Спасибо, сохранили',
                           chat_id=message.chat.id,
                           reply_markup=main_menu)


@dp.message_handler(content_types=ContentType.PHOTO, state=Save_eat.food_name)
async def main_menu_by_text(message: types.Message, state: FSMContext):
    food_name = message.caption
    print(food_name)
    new_ingest = Ingestion()
    new_ingest.food_name = food_name
    async with state.proxy() as data:
        eat_type = data['eat_type']

    new_ingest.food_name = message.caption
    if message.caption == None:
        new_ingest.food_name = "Без подписи"
    new_ingest.type_eat = eat_type
    new_ingest.picture = message.photo[0].file_id
    new_ingest.user_tg_id = message.chat.id
    new_ingest.date = '_'.join(str(datetime.datetime.today().date()).split('-'))
    session = create_session()
    session.add(new_ingest)
    session.commit()
    await state.finish()
    await bot.send_message(text='Спасибо, сохранили',
                           chat_id=message.chat.id,
                           reply_markup=main_menu)


@dp.callback_query_handler(
    lambda callback_query: callback_query.data and callback_query.data.startswith('home'))
async def main_menu_by_callback(callback_query: types.CallbackQuery):
    jk = callback_query.data.split('_')
    if len(jk) != 1:
        f1 = jk[-3]
        f2 = jk[-2]
        f3 = jk[-1]
        await bot.delete_message(message_id=f1, chat_id=callback_query.message.chat.id)
        await bot.delete_message(message_id=f2, chat_id=callback_query.message.chat.id)
        await bot.delete_message(message_id=f3, chat_id=callback_query.message.chat.id)
    await bot.edit_message_text(text='Здравствуйте! 👋 \n\nЭтот бот помогает следить за рационом дня.',
                                chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id,
                                reply_markup=main_menu)


@dp.callback_query_handler(
    lambda callback_query: callback_query.data and callback_query.data.startswith('back'))
async def main_menu_by_callback(callback_query: types.CallbackQuery):
    jk = callback_query.data.split('_')
    session = create_session()
    user = session.query(User).filter(User.user_tg_id == callback_query.message.chat.id).first()
    if len(jk) == 2:
        user.week = int(user.week) + int(jk[-1])
        session.add(user)
        session.commit()
    else:
        if len(jk) != 1:
            f1 = jk[-3]
            f2 = jk[-2]
            f3 = jk[-1]
            await bot.delete_message(message_id=f1, chat_id=callback_query.message.chat.id)
            await bot.delete_message(message_id=f2, chat_id=callback_query.message.chat.id)
            await bot.delete_message(message_id=f3, chat_id=callback_query.message.chat.id)
    await  bot.answer_callback_query(callback_query_id=callback_query.id, show_alert=False,
                                     text="Осталось выбрать день недели 📆")
    inline_btn_1 = InlineKeyboardButton('Понедельник', callback_data=f'week_{get_date_by_weekday(1, user.week)}')
    inline_btn_2 = InlineKeyboardButton('Вторник', callback_data=f'week_{get_date_by_weekday(2, user.week)}')
    inline_btn_3 = InlineKeyboardButton('Среда', callback_data=f'week_{get_date_by_weekday(3, user.week)}')
    inline_btn_4 = InlineKeyboardButton('Четверг', callback_data=f'week_{get_date_by_weekday(4, user.week)}')
    inline_btn_5 = InlineKeyboardButton('Пятница', callback_data=f'week_{get_date_by_weekday(5, user.week)}')
    inline_btn_6 = InlineKeyboardButton('Суббота', callback_data=f'week_{get_date_by_weekday(6, user.week)}')
    inline_btn_7 = InlineKeyboardButton('Воскресенье', callback_data=f'week_{get_date_by_weekday(7, user.week)}')
    next = InlineKeyboardButton('Вперед ▶️', callback_data='back_1')
    past = InlineKeyboardButton('◀️Назад', callback_data='back_-1')
    week_kb = InlineKeyboardMarkup(row_width=1).add(inline_btn_1, inline_btn_2, inline_btn_3, inline_btn_4,
                                                    inline_btn_5, inline_btn_6, inline_btn_7)
    week_kb.row(past, next)
    week_kb.add(back)
    await bot.edit_message_text(
        text=f'Список приемов с {"-".join(get_date_by_weekday(1, user.week).split("_"))} по {"-".join(get_date_by_weekday(7, user.week).split("_"))}\n\nВыберете день недели:',
        message_id=callback_query.message.message_id,
        chat_id=callback_query.message.chat.id,
        reply_markup=week_kb)


@dp.callback_query_handler(
    lambda callback_query: callback_query.data and callback_query.data.startswith('week'))
async def main_menu_by_callback(callback_query: types.CallbackQuery):
    date = callback_query.data.split('_')
    date = f"{date[-3]}_{date[-2]}_{date[-1]}"
    session = create_session()
    user = session.query(User).filter(User.user_tg_id == callback_query.message.chat.id).first()
    back_kb = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton('Назад 🔙', callback_data=f'back'), back)
    text = ingests = session.query(Ingestion).filter(Ingestion.user_tg_id == user.user_tg_id).filter(
        Ingestion.date == date).all()
    if len(text) == 0:
        text = 'Нет информации о приёме пищи за этот день'
        await bot.edit_message_text(text=text, message_id=callback_query.message.message_id,
                                    chat_id=callback_query.message.chat.id,
                                    reply_markup=back_kb, parse_mode=ParseMode.MARKDOWN)
    else:
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        mas = []
        for i in text:
            mas.append(i.type_eat.lower())
        f1, f2, f3 = 0, 0, 0
        if 'завтрак' not in mas:
            a = await bot.send_message(chat_id=user.user_tg_id, text='*Завтрак:* Не заполнен',
                                       parse_mode=ParseMode.MARKDOWN)
            f1 = a.message_id
        else:
            n = session.query(Ingestion).filter(Ingestion.user_tg_id == user.user_tg_id).filter(
                Ingestion.date == date).filter(Ingestion.type_eat == 'Завтрак').first()
            c = n.food_name
            if c != None:
                c = c.title()
            else:
                c = ''
            if n.picture != None:
                a = await bot.send_photo(chat_id=user.user_tg_id, photo=n.picture, caption=f'*Завтрак:* {c}',
                                         parse_mode=ParseMode.MARKDOWN)
            else:
                a = await bot.send_message(chat_id=user.user_tg_id, text=f'*Завтрак:* {c}',
                                           parse_mode=ParseMode.MARKDOWN)
            f1 = a.message_id
        if 'обед' not in mas:
            a = await bot.send_message(chat_id=user.user_tg_id, text='*Обед:* Не заполнен',
                                       parse_mode=ParseMode.MARKDOWN)
            f2 = a.message_id
        else:
            n = session.query(Ingestion).filter(Ingestion.user_tg_id == user.user_tg_id).filter(
                Ingestion.date == date).filter(Ingestion.type_eat == 'Обед').first()
            print(n.food_name)
            c = n.food_name

            if c != None:
                c = c.title()
            else:
                c = ''
            if n.picture != None:
                a = await bot.send_photo(chat_id=user.user_tg_id, photo=n.picture, caption=f'*Обед:* {c}',
                                         parse_mode=ParseMode.MARKDOWN)
            else:
                a = await bot.send_message(chat_id=user.user_tg_id, text=f'*Обед:* {c}', parse_mode=ParseMode.MARKDOWN)
            f2 = a.message_id
        if 'ужин' not in mas:
            a = await bot.send_message(chat_id=user.user_tg_id, text='*Ужин:* Не заполнен',
                                       parse_mode=ParseMode.MARKDOWN)
            f3 = a.message_id
        else:
            n = session.query(Ingestion).filter(Ingestion.user_tg_id == user.user_tg_id).filter(
                Ingestion.date == date).filter(Ingestion.type_eat == 'Ужин').first()
            c = n.food_name
            if c != None:
                c = c.title()
            else:
                c = ''
            if n.picture != None:
                a = await bot.send_photo(chat_id=user.user_tg_id, photo=n.picture, caption=f'*Ужин:* {c}',
                                         parse_mode=ParseMode.MARKDOWN)
            else:
                a = await bot.send_message(chat_id=user.user_tg_id, text=f'*Ужин:* {c}', parse_mode=ParseMode.MARKDOWN)
            f3 = a.message_id
        kl = InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton('Назад 🔙', callback_data=f'back_{f1}_{f2}_{f3}'),
            InlineKeyboardButton('🏘 Главное меню', callback_data=f'home_{f1}_{f2}_{f3}')
        )
        await bot.send_message(chat_id=user.user_tg_id, text='Выберите действие:', reply_markup=kl,
                               parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(content_types=ContentType.PHOTO, state=Save_eat.food_name)
async def photo_handler(message: types.Message, state: FSMContext):
    photo = message.photo.pop()
    name = str(int(datetime.datetime.now().timestamp()) + random.randint(0, 1000))
    await photo.download(f'./{name}.jpg')
    with open(f"{name}.jpg", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    async with state.proxy() as data:
        eat_type = data['eat_type']
    new_ingest = Ingestion()
    new_ingest.type_eat = eat_type
    new_ingest.picture = encoded_string
    new_ingest.user_tg_id = message.chat.id
    new_ingest.date = '_'.join(str(datetime.datetime.today().date()).split('-'))
    session = create_session()
    session.add(new_ingest)
    session.commit()
    await bot.send_message(text='Спасибо, сохранили',
                           chat_id=message.chat.id,
                           reply_markup=main_menu)
    await state.finish()


@dp.callback_query_handler(
    lambda callback_query: callback_query.data and callback_query.data.startswith('my_ingestions'))
async def main_menu_by_callback(callback_query: types.CallbackQuery):
    session = create_session()
    user = session.query(User).filter(User.user_tg_id == callback_query.message.chat.id).first()
    user.week = 0
    session.add(user)
    session.commit()
    await  bot.answer_callback_query(callback_query_id=callback_query.id, show_alert=False,
                                     text="Осталось выбрать день недели 📆")
    inline_btn_1 = InlineKeyboardButton('Понедельник', callback_data=f'week_{get_date_by_weekday(1, user.week)}')
    inline_btn_2 = InlineKeyboardButton('Вторник', callback_data=f'week_{get_date_by_weekday(2, user.week)}')
    inline_btn_3 = InlineKeyboardButton('Среда', callback_data=f'week_{get_date_by_weekday(3, user.week)}')
    inline_btn_4 = InlineKeyboardButton('Четверг', callback_data=f'week_{get_date_by_weekday(4, user.week)}')
    inline_btn_5 = InlineKeyboardButton('Пятница', callback_data=f'week_{get_date_by_weekday(5, user.week)}')
    inline_btn_6 = InlineKeyboardButton('Суббота', callback_data=f'week_{get_date_by_weekday(6, user.week)}')
    inline_btn_7 = InlineKeyboardButton('Воскресенье', callback_data=f'week_{get_date_by_weekday(7, user.week)}')
    next = InlineKeyboardButton('Вперед ▶️', callback_data='back_1')
    past = InlineKeyboardButton('◀️Назад', callback_data='back_-1')
    week_kb = InlineKeyboardMarkup(row_width=1).add(inline_btn_1, inline_btn_2, inline_btn_3, inline_btn_4,
                                                    inline_btn_5, inline_btn_6, inline_btn_7)
    week_kb.row(past, next)
    week_kb.add(back)
    await bot.edit_message_text(
        text=f'Список приемов с {"-".join(get_date_by_weekday(1, user.week).split("_"))} по {"-".join(get_date_by_weekday(7, user.week).split("_"))}\n\nВыберете день недели:',
        message_id=callback_query.message.message_id,
        chat_id=callback_query.message.chat.id,
        reply_markup=week_kb)


@dp.callback_query_handler(lambda callback_query: callback_query.data and callback_query.data.startswith('menu'))
async def main_menu_by_callback(callback_query: types.CallbackQuery):
    exists(callback_query.message.chat.id)
    await bot.edit_message_text(text='Здравствуйте! 👋 \n\nЭтот бот помогает следить за рационом дня.',
                                chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id,
                                reply_markup=main_menu)


@dp.message_handler(commands=['start', 'help'], state=None)
async def process_start_command(message: types.Message):
    exists(message.chat.id)
    await bot.send_message(text='Здравствуйте! 👋 \n\nЭтот бот помогает следить за рационом дня.',
                           chat_id=message.chat.id,
                           reply_markup=main_menu)


@dp.message_handler()
async def main_menu_by_text(message: types.Message):
    exists(message.chat.id)
    await bot.send_message(text='Здравствуйте! 👋 \n\nЭтот бот помогает следить за рационом дня.',
                           chat_id=message.chat.id,
                           reply_markup=main_menu)


async def scheduler():
    aioschedule.every().day.at('10:00').do(check_breakfast)
    aioschedule.every().day.at('13:00').do(check_dinner)
    aioschedule.every().day.at('17:30').do(check_evening)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(10)


async def check_breakfast():
    session = create_session()
    users = session.query(User).all()
    inline_btn_1 = InlineKeyboardButton('Начать заполнение приема пищи', callback_data='eat_breakfast')
    get_eat = InlineKeyboardMarkup(row_width=1).add(inline_btn_1)
    for user in users:
        try:
            await bot.send_message(text='Настало время завтрака. Нажмите на кнопку ниже что бы сохранить приём пищи.',
                                   chat_id=user.user_tg_id, reply_markup=get_eat)
        except:
            pass


async def check_dinner():
    session = create_session()
    users = session.query(User).all()
    inline_btn_1 = InlineKeyboardButton('Начать заполнение приема пищи', callback_data='eat_dinner')
    get_eat = InlineKeyboardMarkup(row_width=1).add(inline_btn_1)
    for user in users:
        try:
            await bot.send_message(text='Настало время обеда. Нажмите на кнопку ниже что бы сохранить приём пищи.',
                                   chat_id=user.user_tg_id, reply_markup=get_eat)
        except:
            pass


async def check_evening():
    session = create_session()
    users = session.query(User).all()
    inline_btn_1 = InlineKeyboardButton('Начать заполнение приема пищи', callback_data='eat_evening')
    get_eat = InlineKeyboardMarkup(row_width=1).add(inline_btn_1)
    for user in users:
        try:
            await bot.send_message(text='Настало время ужина. Нажмите на кнопку ниже что бы сохранить приём пищи.',
                                   chat_id=user.user_tg_id, reply_markup=get_eat)
        except:
            pass


async def on_startup(x):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    global_init("db.sqlite")
    start_polling(dp, on_startup=on_startup)
