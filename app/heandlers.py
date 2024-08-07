from aiogram import Router, F, types
from aiogram.types import Message, BufferedInputFile, CallbackQuery, TelegramObject
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import BaseFilter
from aiogram.filters.command import Command
from typing import Any, Union
from app.InlineButtonHeandler import (moderation_button, event_owner, sub_or_unSub_button, view_profile, canceled_list_worker, worker_profile, fire_worker,
                                      view_event, event_people_view, event_owner_more_one, button_on_reset, reset_profile_buttons)
from app.ReplyButtonHeandler import moderation, owner, employee
from app.CreateEvents import start_create
from datetime import datetime, timedelta
from translate import Translator
from app.DataBase.models import User, Event
from app.passCipher import PassDecrypt

import app.DataBase.requests as db
import math
import config
import pyjokes

rout = Router()
pass_decrypt = PassDecrypt()

chat_id_waiting = 0
count_profile_checking = 0
count_create_event = 0
view_profile_filters = ['Начинающий', 'Маршал', 'Основной состав']
view_event_filters = ['Планируется', 'Отменено', 'Прошло']
start_filter = None

user_id = {}
canceled_edit_message_id = {}
edit_message_id_profile = {}
number_list = {}
max_number_list = {}
date_event = {}
edit_message = {}
count_event_subscribes = {}
number_list_event_worker = {}
number_message_id_event = {}
day_count = {}
other_filter_profiles = {}
other_filter_events = {}

class states(StatesGroup):
    send_message = State()
    new_status = State()
    rating_up = State()
    rating_down = State()
    fire_worker = State()
    view = State()
    view_event = State()
    text_canceled = State()
    is_crate = State()

class IsStatusUser(BaseFilter):
    def __init__(self, status: list) -> None:
        super().__init__()
        self.status = status
    
    async def __call__(self, obj: Union[Message, TelegramObject]) -> bool:
        user_id = obj.chat.id
        status = await db.get_status(user_id)
        if status in self.status:
            return True
        else:
            await obj.answer("У вас недосстаточно прав.")
            return False

@rout.message(Command("reset"))
async def reset(message: Message) -> None:
    status = await db.get_status(message.chat.id)
    markup = None
    if status == "Владелец":
        markup = owner
    elif status != "Модерция":
        markup = employee
    else:
        markup = moderation
    
    await message.answer("Я перезапустил клавиатуру.", reply_markup=markup)

@rout.message(F.text.lower() == "моя анкета")
async def my_profile(message: Message) -> None:
    await edit_message_function(message)
    data: User | None = await db.get_profile(message.chat.id)
    if data == None: 
        await message.answer("Произошла ошибка, попробуйте еще раз.")
    else:
        send = await message.answer_photo(BufferedInputFile(data.photo, filename="photo.jpg"), caption= await message_my_profile(data), reply_markup=button_on_reset)
        await edit_message_set(message, send.message_id)

async def message_my_profile(data: User) -> str:
    passport = await pass_decrypt.decrypt(data.passport_data)
    message = f'Ваша анкета:\nФИО: {data.full_name} \nДата рождения: {data.year}\nНомер телефона: {data.phone_number}\nНик телеграмм: {data.username}\nПаспортные данные: {passport}\nРейтин: {data.rating}\nСтатус: {data.status}'
    return message

@rout.message(F.text.lower() == "мероприятие")
async def view_event_planning(message: Message) -> None:
    global number_list_event_worker, number_message_id_event
    await edit_message_function(message)
    chat_id = message.chat.id
    count_event = await db.count_event_where_planing()
    data: Event | None = await db.get_event()
    number_list_event_worker[f'{message.chat.id}'] = 1
    status = await db.get_status(chat_id)
    if data == None:
        await message.answer("Мероприятий нет, ожидайте.")
    else:
        if status == "Владелец" and count_event <= 1:
            send = await message.answer(await message_view_event(data, count_event, message), reply_markup=event_owner)
        elif status == "Владелец" and count_event > 1:
            send = await message.answer(await message_view_event(data, count_event, message), reply_markup=event_owner_more_one)
        elif status != "Модерация":
            send = await message.answer(await message_view_event(data, count_event, message), reply_markup=await sub_or_unSub_button(chat_id, count_event, number_list_event_worker[f'{message.chat.id}']-1))
        elif status == "Модерация":
            send = await message.answer(await message_view_event(data, 1, message))
        number_message_id_event[f'{message.chat.id}'] = send.message_id
        await edit_message_set(message, send.message_id)

async def message_view_event(data: Event, count_event: int, message: Message) -> str:
    eventText = f"Мероприятие под названием {data.name}:\nОписание: {data.description}\nДата проведения: {data.date}\nКоличество дней: {data.count_days}\nМетод работы: {data.method_of_work}\nКоличество маршалов: {data.count_people}\nСтатус: {data.status}\nМесто на картах: {data.URL}\n"
    if count_event > 1:
        eventText += f"{' '*10}{number_list_event_worker[f'{message.chat.id}']}/{count_event}{' '*10}"
    return eventText

@rout.message(F.text.lower() == "создать мероприятие", IsStatusUser(config.OWNER_STATUS))
async def create_event(message: Message, state: FSMContext) -> None:
    global count_create_event
    if await is_create_count(message):
        count_create_event = message.chat.id
        await state.set_state(states.is_crate)
        await message.answer("Вы точно хотите создать мероприятие? (напишите да или нет)")

async def is_create_count(message: Message) -> bool:
    global count_create_event
    if message.chat.id == count_create_event or count_create_event == 0:
        return True
    else:
        await message.answer("Мероприятие уже создают.")
        return False

@rout.message(states.is_crate, F.text)
async def is_create(message: Message, state: FSMContext) -> None:
    global count_create_event
    yes_or_no = message.text
    if yes_or_no.lower() == "да":
        await state.clear()
        await start_create(message, state)
    elif yes_or_no.lower() == "нет":
        await message.answer("Прошу прощения.")
        await state.clear()
        count_create_event = 0
    else:
        await message.answer("Я вас не понял, напишите Да или Нет.")

@rout.message(F.text.lower() == "проверка анкет", IsStatusUser(config.OWNER_STATUS))
async def checking_profile(message: Message) -> None:
    if await is_checking(message):
        await checking(message)

async def is_checking(message: Message) -> bool:
    global count_profile_checking
    if message.chat.id == count_profile_checking or count_profile_checking == 0:
        return True
    else:
        await message.answer("Анкеты уже проверяют.")
        return False

async def checking(message: Message) -> None:
    global count_profile_checking
    count_profile_checking = message.chat.id
    data: User | None = await db.get_profile_moderation()
    if data == None:
        await message.answer("Новых анкет не поступало, как поступят я сообщу.")
    else:
        await profile_moderation(message, data)

async def profile_moderation(message: Message, data: User) -> None:
    global chat_id_waiting
    chat_id_waiting = data.chat_id
    passport = await pass_decrypt.decrypt(data.passport_data, config.KEY_CIPHER)
    profile = f"новая анкета:\nФИО: {data.full_name}\nДата рождения: {data.year}\nНомер телефона: {data.phone_number}\nНик телеграмм: {data.username}\nПаспортные данные: {passport}"
    await message.answer_photo(BufferedInputFile(data.photo, filename="photo.jpg"), caption=profile, reply_markup=moderation_button)

@rout.message(F.text.lower() == "список работников", IsStatusUser(config.OWNER_STATUS))
async def list_worker_view(message: Message) -> None:
    global other_filter_profiles
    other_filter_profiles[f'{message.chat.id}'] = start_filter
    await edit_message_function(message)
    count = await db.count_user(other_filter_profiles[f'{message.chat.id}'])
    await set_count_user(message)
    send_message = await message.answer(await create_message_text(message), reply_markup=await view_profile(count, other_filter_profiles[f'{message.chat.id}']))
    await edit_message_set(message, send_message.message_id)

async def set_count_user(message: Message) -> None:
    global max_number_list, number_list
    count = await db.count_user(other_filter_profiles[f'{message.chat.id}'])
    number_list[message.chat.id] = 1
    max_number_list[message.chat.id] = await count_list(count)

async def create_message_text(message: Message) -> str:
    limit = 10
    offset = 1
    if number_list[message.chat.id] <= 1:
        workers = await db.get_profiles(filter=other_filter_profiles[f'{message.chat.id}'])
    else:
        final_offset = (offset * limit * number_list[message.chat.id]) - 10
        workers = await db.get_profiles(limit, final_offset, other_filter_profiles[f'{message.chat.id}'])
    message_text = 'Работники:\n'
    for worker in workers:
        message_text += f'{worker.id}. {worker.full_name} | {worker.username} | {worker.status}\n'
    message_text += f'{" " * 40}{number_list[message.chat.id]}/{max_number_list[message.chat.id]}{" " * 40}'
    
    return message_text

@rout.message(F.text.lower() == "список мероприятий", IsStatusUser(config.OWNER_STATUS))
async def list_events_view(message: Message) -> None:
    global other_filter_events
    other_filter_events[f'{message.chat.id}'] = start_filter
    await edit_message_function(message)
    count = await db.count_events(other_filter_events[f'{message.chat.id}'])
    await set_count_event(message)
    send_message = await message.answer(await create_message_text_event(message), reply_markup=await view_event(count, other_filter_events[f'{message.chat.id}']))
    await edit_message_set(message, send_message.message_id)

async def create_message_text_event(message: Message) -> str:
    limit = 10
    offset = 1
    if number_list[message.chat.id] <= 1:
        events = await db.get_events(filter=other_filter_events[f'{message.chat.id}'])
    else:
        final_offset = (offset * limit * number_list[message.chat.id]) - 10
        events = await db.get_events(limit, final_offset, other_filter_events[f'{message.chat.id}'])
    message_text = 'Мероприятия:\n'
    count = 1
    for event in events:
        message_text += f'{count}. {event.name} | {event.date} | {event.status}\n'
        count += 1
    message_text += f'{" " * 40}{number_list[message.chat.id]}/{max_number_list[message.chat.id]}{" " * 40}'
    
    return message_text

async def set_count_event(message: Message) -> None:
    global max_number_list, number_list
    count = await db.count_events(other_filter_events[f'{message.chat.id}'])
    number_list[message.chat.id] = 1
    max_number_list[message.chat.id] = await count_list(count)

async def count_list(count) -> int:
    list = count / 10
    return math.ceil(list)

@rout.message(F.text.lower() == "forge")
async def easter_egg(message: Message) -> None:
    joke = pyjokes.get_joke()
    translation = Translator(to_lang='ru')
    await message.answer(translation.translate(joke))

@rout.message(F.text.regexp(config.PATTERN_PROFILE_VIEW), IsStatusUser(config.OWNER_STATUS))
async def is_message(message: Message) -> None:
    text = message.text.split(" ")
    await is_profile(message, text[1])

async def is_profile(message: Message, user_name: str) -> None:
    global user_id, edit_message_id_profile
    data: User | None = await db.get_profile_for_user_name(user_name)
    if data != None:
        user_id[message.chat.id] = data.chat_id
        data_message = await message.answer_photo(BufferedInputFile(data.photo, filename="photo.jpg"), caption=await message_profile_view(data), reply_markup=worker_profile)
        edit_message_id_profile[message.chat.id] = data_message.message_id

@rout.callback_query(F.data == "reset_profile")
async def reset_profile(callback: CallbackQuery) -> None:
    await callback.answer("")
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=reset_profile_buttons)

@rout.callback_query(F.data == "return")
async def ret_button(callback: CallbackQuery) -> None:
    await callback.answer("")
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=button_on_reset)

@rout.callback_query(F.data.regexp(config.CALLBACK_PATTERN_LEFT))
async def list_left(callback: CallbackQuery) -> None:
    global number_list
    try:
        await callback.answer("")
        split = callback.data.split(":")
        if split[1] == "view_event_planing":
            await down_number_list_event_planing(callback.message)
        elif split[1] == "worker":
            if number_list[callback.message.chat.id] > 1:
                count = await db.count_user()
                number_list[callback.message.chat.id] -= 1
                await callback.message.edit_text(text=await create_message_text(callback.message),
                                                 inline_message_id=callback.inline_message_id,
                                                 reply_markup=await view_profile(count, other_filter_profiles[f'{callback.message.chat.id}']))
        else:
            if number_list[callback.message.chat.id] > 1:
                count = await db.count_events()
                number_list[callback.message.chat.id] -= 1
                await callback.message.edit_text(text=await create_message_text_event(callback.message),
                                                 inline_message_id=callback.inline_message_id,
                                                 reply_markup=await view_event(count, other_filter_events[f'{callback.message.chat.id}']))
    except Exception:
        await callback.answer("Произошла ошибка, попробуйте еще раз")

async def down_number_list_event_planing(message: Message) -> None:
    if number_list_event_worker[f'{message.chat.id}'] != 1:
        number_list_event_worker[f'{message.chat.id}'] -= 1
        data: Event | None = await db.get_event(number_list_event_worker[f'{message.chat.id}'] - 1)
        await message_event_planing(data, message)

@rout.callback_query(F.data.regexp(config.CALLBACK_PATTERN_RIGHT))
async def list_right(callback: CallbackQuery) -> None:
    global number_list
    try:
        await callback.answer("")
        split = callback.data.split(":")
        if split[1] == "view_event_planing":
            await up_number_list_event_planing(callback.message)
        elif split[1] == "worker":
            if number_list[callback.message.chat.id] < max_number_list[callback.message.chat.id]:
                count = await db.count_user()
                number_list[callback.message.chat.id] += 1
                await callback.message.edit_text(text=await create_message_text(callback.message),
                                                 inline_message_id=callback.inline_message_id,
                                                 reply_markup=await view_profile(count, other_filter_profiles[f'{callback.message.chat.id}']))
        else:
            if number_list[callback.message.chat.id] < max_number_list[callback.message.chat.id]:
                count = await db.count_events()
                number_list[callback.message.chat.id] += 1
                await callback.message.edit_text(text=await create_message_text_event(callback.message),
                                                 inline_message_id=callback.inline_message_id,
                                                 reply_markup=await view_event(count, other_filter_events[f'{callback.message.chat.id}']))
    except Exception:
        await callback.answer("Произошла ошибка, попробуйте еще раз")

async def up_number_list_event_planing(message: Message) -> None:
    if number_list_event_worker[f'{message.chat.id}'] != await db.count_event_where_planing():
        number_list_event_worker[f'{message.chat.id}'] += 1
        data: Event | None = await db.get_event(number_list_event_worker[f'{message.chat.id}'] - 1)
        await message_event_planing(data, message)

async def message_event_planing(data: object, message: Message) -> None:
    count_event = await db.count_event_where_planing()
    eventText = (f"Мероприятие под названием {data.name}:\nОписание: {data.description}\nДата проведения: {data.date}\nКоличество дней: {data.count_days}\nМетод работы: {data.method_of_work}\nКоличество маршалов: {data.count_people}\nСтатус: {data.status}\nМесто на картах: {data.URL}\n")
    eventText += f"{' '*10}{number_list_event_worker[f'{message.chat.id}']}/{count_event}{' '*10}"
    markup = None
    status = await db.get_status(message.chat.id)
    if status == "Владелец":
        markup = event_owner_more_one
    else:
        markup = await sub_or_unSub_button(message.chat.id, count_event,  number_list_event_worker[f'{message.chat.id}']-1)
    await message.bot.edit_message_text(chat_id=message.chat.id, message_id=number_message_id_event[f'{message.chat.id}'], text=eventText, reply_markup=markup)

@rout.callback_query(F.data == "beginning")
async def beginning_filter(callback: CallbackQuery) -> None:
    global other_filter_profiles
    other_filter_profiles[f'{callback.message.chat.id}'] = view_profile_filters[0]
    count = await db.count_user(other_filter_profiles[f'{callback.message.chat.id}'])
    await set_count_user(callback.message)
    await callback.message.edit_text(text=await create_message_text(callback.message),
                                     inline_message_id=callback.inline_message_id,
                                     reply_markup=await view_profile(count, other_filter_profiles[f'{callback.message.chat.id}'] ))

@rout.callback_query(F.data == "marshal")
async def marshal_filter(callback: CallbackQuery) -> None:
    global other_filter_profiles
    other_filter_profiles[f'{callback.message.chat.id}']  = view_profile_filters[1]
    count = await db.count_user(other_filter_profiles[f'{callback.message.chat.id}'])
    await set_count_user(callback.message)
    await callback.message.edit_text(text=await create_message_text(callback.message),
                                     inline_message_id=callback.inline_message_id,
                                     reply_markup=await view_profile(count, other_filter_profiles[f'{callback.message.chat.id}'] ))

@rout.callback_query(F.data == "main_cast")
async def main_cast_filter(callback: CallbackQuery) -> None:
    global other_filter_profiles
    other_filter_profiles[f'{callback.message.chat.id}']  = view_profile_filters[2]
    count = await db.count_user(other_filter_profiles[f'{callback.message.chat.id}'])
    await set_count_user(callback.message)
    await callback.message.edit_text(text=await create_message_text(callback.message),
                                     inline_message_id=callback.inline_message_id
                                     , reply_markup=await view_profile(count, other_filter_profiles[f'{callback.message.chat.id}'] ))

@rout.callback_query(F.data == "all")
async def all_filter(callback: CallbackQuery) -> None:
    global other_filter_profiles
    other_filter_profiles[f'{callback.message.chat.id}']  = start_filter
    count = await db.count_user(other_filter_profiles[f'{callback.message.chat.id}'])
    await set_count_user(callback.message)
    await callback.message.edit_text(text=await create_message_text(callback.message),
                                     inline_message_id=callback.inline_message_id,
                                     reply_markup=await view_profile(count, other_filter_profiles[f'{callback.message.chat.id}'] ))

@rout.callback_query(F.data == "planing")
async def planing_filter(callback: CallbackQuery) -> None:
    global other_filter_events
    other_filter_events[f'{callback.message.chat.id}'] = view_event_filters[0]
    count = await db.count_events(other_filter_events[f'{callback.message.chat.id}'])
    await set_count_event(callback.message)
    await callback.message.edit_text(text=await create_message_text_event(callback.message),
                                     inline_message_id=callback.inline_message_id,
                                     reply_markup=await view_event(count, other_filter_events[f'{callback.message.chat.id}']))

@rout.callback_query(F.data == "canceled_event_filter")
async def canceled_event_filter(callback: CallbackQuery) -> None:
    global other_filter_events
    other_filter_events[f'{callback.message.chat.id}'] = view_event_filters[1]
    count = await db.count_events(other_filter_events[f'{callback.message.chat.id}'])
    await set_count_event(callback.message)
    await callback.message.edit_text(text=await create_message_text_event(callback.message),
                                     inline_message_id=callback.inline_message_id,
                                     reply_markup=await view_event(count, other_filter_events[f'{callback.message.chat.id}']))

@rout.callback_query(F.data == "passed_event_filter")
async def passed_event_filter(callback: CallbackQuery) -> None:
    global other_filter_events
    other_filter_events[f'{callback.message.chat.id}'] = view_event_filters[2]
    count = await db.count_events(other_filter_events[f'{callback.message.chat.id}'])
    await set_count_event(callback.message)
    await callback.message.edit_text(text=await create_message_text_event(callback.message),
                                     inline_message_id=callback.inline_message_id,
                                     reply_markup=await view_event(count, other_filter_events[f'{callback.message.chat.id}']))

@rout.callback_query(F.data == "all_event")
async def all_event_filter(callback: CallbackQuery) -> None:
    global other_filter_events
    other_filter_events[f'{callback.message.chat.id}'] = start_filter
    count = await db.count_events(other_filter_events[f'{callback.message.chat.id}'])
    await set_count_event(callback.message)
    await callback.message.edit_text(text=await create_message_text_event(callback.message),
                                     inline_message_id=callback.inline_message_id,
                                     reply_markup=await view_event(count, other_filter_events[f'{callback.message.chat.id}']))

@rout.callback_query(F.data == "accept")
async def accept_profile(callback: CallbackQuery) -> None:
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=None)
    await db.update_status(chat_id_waiting, config.WORKER_STATUS[0])
    await callback.message.bot.send_message(chat_id=chat_id_waiting, text="Поздравляю, вы приняты.", reply_markup=employee)
    await checking(callback.message)

@rout.callback_query(F.data == "canceled")
async def canceled_profile(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=None)
    await state.set_state(states.text_canceled)
    await callback.message.answer("Напишите пожалуйста причину отказа.")

@rout.message(states.text_canceled, F.text)
async def canceled_message(message: Message, state: FSMContext) -> None:
    await state.clear()
    await db.delete_profile(chat_id_waiting)
    await message.bot.send_message(chat_id=chat_id_waiting, text=f"Вам отказано, причина:\n{message.text}", reply_markup=types.ReplyKeyboardRemove())
    await checking(message)

@rout.callback_query(F.data == "view_event")
async def view_event_in_name(callback: CallbackQuery, state: FSMContext) -> None:
    global canceled_edit_message_id
    await callback.answer("")
    send_message = await callback.message.answer("Введите название мероприятия (если передумали нажмите отмена).", reply_markup=canceled_list_worker)
    canceled_edit_message_id[callback.message.chat.id] = send_message.message_id
    await state.set_state(states.view_event)

@rout.message(states.view_event, F.text)
async def is_view(message: Message, state: FSMContext) -> None:
    global canceled_edit_message_id, date_event
    if (message.chat.id in canceled_edit_message_id) and canceled_edit_message_id[message.chat.id] != 0:
        await delete_message(message=message, message_id=canceled_edit_message_id[message.chat.id])
        canceled_edit_message_id[message.chat.id] = 0
    data = await db.get_event_view(message.text)
    if data != None:
        markup = None
        if data.status != "Отменено":
            markup = event_people_view
        await message.answer(await message_view_events(data), reply_markup=markup)
        await state.clear()
        date_event[message.chat.id] = data.date
    else:
        send = await message.answer("Такого мероприятия нет, введите название мероприятия или нажмите кнопку отмена", reply_markup=canceled_list_worker)
        canceled_edit_message_id[message.chat.id] = send.message_id

async def message_view_events(data: object) -> str:
    eventText = f"Я нашел мероприятие под названием {data.name}:\nОписание: {data.description}\nКоличество дней: {data.count_days}\nДата проведения: {data.date}\nМетод работы: {data.method_of_work}\nКоличество маршалов: {data.count_people}\nСтатус: {data.status}\nМесто на картах: {data.URL}"
    return eventText

@rout.callback_query(F.data == "view_people_event")
async def view_people_event(callback: CallbackQuery) -> None:
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=None)
    await callback.answer("")
    message_text = "Вот те кто пришел:\n"
    count = 1
    user_name = await db.get_username_people_event(date_event[callback.message.chat.id])
    for user in user_name:
        data: User | None= await db.get_profile_for_user_name(user)
        if data != None:
            message_text += f"{count}. {data.full_name} | {data.username} | {data.status}\n"
            count += 1
    await callback.message.answer(message_text)

@rout.callback_query(F.data == "view_profile")
async def view_profile_worker(callback: CallbackQuery, state: FSMContext) -> None:
    global canceled_edit_message_id
    await callback.answer("")
    send_message = await callback.message.answer("Введите ФИО работника или его ник телеграмм (если передумали нажмите отмена).", reply_markup=canceled_list_worker)
    canceled_edit_message_id[callback.message.chat.id] = send_message.message_id
    await state.set_state(states.view)

@rout.message(states.view, F.text)
async def is_view(message: Message, state: FSMContext) -> None:
    global user_id, canceled_edit_message_id, edit_message_id_profile
    if (message.chat.id in canceled_edit_message_id) and canceled_edit_message_id[message.chat.id] != 0:
        await delete_message(message=message, message_id=canceled_edit_message_id[message.chat.id])
        canceled_edit_message_id[message.chat.id] = 0
    if message.text[0] == '@':
        data: User | None = await db.get_profile_view_username(message.text)
    else:
        data: User | None = await db.get_profile_view(message.text)
    if data != None:
        user_id[message.chat.id] = data.chat_id
        data_message = await message.answer_photo(BufferedInputFile(data.photo, filename="photo.jpg"), caption=await message_profile_view(data), reply_markup=worker_profile)
        edit_message_id_profile[message.chat.id] = data_message.message_id
        await state.clear()
    else:
        send = await message.answer("Такого работника нет, введите ФИО работника или его ник телеграмм, если передумали нажмите кнопку отмена", reply_markup=canceled_list_worker)
        canceled_edit_message_id[message.chat.id] = send.message_id

async def message_profile_view(data: User) -> str:
    passport = await pass_decrypt.decrypt(data.passport_data, config.KEY_CIPHER)
    message = f'Вот что я нашел:\nФИО: {data.full_name} \nВозраст: {data.year}\nНомер телефона: {data.phone_number}\nНик телеграмм: {data.username}\nПаспортные данные: {passport}\nРейтин: {data.rating}\nСтатус: {data.status}'
    return message

@rout.callback_query(F.data == "new_staus")
async def new_status(callback: CallbackQuery, state: FSMContext) -> None:
    global canceled_edit_message_id
    await callback.answer("")
    await state.set_state(states.new_status)
    send_message = await callback.message.answer("выбирете статус и пришлите его номер мне (1 - Начинающий, 2 - Маршал, 3 - Основной состав).",
                                                 reply_markup=canceled_list_worker)
    canceled_edit_message_id[callback.message.chat.id] = send_message.message_id

@rout.message(states.new_status, F.text)
async def set_new_status(message: Message, state: FSMContext) -> None:
    global canceled_edit_message_id
    try:
        if (message.chat.id in canceled_edit_message_id) and canceled_edit_message_id[message.chat.id] != 0:
            await delete_message(message=message, message_id=canceled_edit_message_id[message.chat.id])
            canceled_edit_message_id[message.chat.id] = 0
        number = (int(message.text) - 1)
        new_status = config.WORKER_STATUS[number]
        if await db.get_status(user_id[message.chat.id]) != new_status:
            await db.update_status(user_id[message.chat.id], new_status)
            await edit_message_profile(message)
        await state.clear()
    except Exception:
        send = await message.answer("Произошла ошибка, попробуйте еще раз (1 - Начинающий, 2 - Маршал, 3 - Основной состав).",
                             reply_markup=canceled_list_worker)
        canceled_edit_message_id[message.chat.id] = send.message_id

@rout.callback_query(F.data =="send_message")
async def send_message(callback: CallbackQuery, state: FSMContext) -> None:
    global edit_message
    await callback.answer("")
    await state.set_state(states.send_message)
    send = await callback.message.answer("напишите сообщение которое хотите отправить.", reply_markup=canceled_list_worker)
    edit_message[callback.message.chat.id] = send.message_id

@rout.message(states.send_message, F.text)
async def send(message: Message, state: FSMContext) -> None:
    await message.bot.send_message(chat_id=user_id[message.chat.id], text=f"Вам сообщение:\n{message.text}")
    await message.bot.edit_message_text(text="Я отправил данное сообщение.", chat_id=message.chat.id, message_id=edit_message[message.chat.id])
    await state.clear()

@rout.callback_query(F.data == "fire")
async def is_fire(callback: CallbackQuery) -> None:
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=None)
    await callback.answer("")
    await callback.message.answer("Вы точно хотите уволить данного сотрудника?", reply_markup=fire_worker)

@rout.callback_query(F.data == "rating_up")
async def rating_up(callback: CallbackQuery, state: FSMContext) -> None:
    global canceled_edit_message_id
    await callback.answer("")
    send_message = await callback.message.answer("напишите число на сколько поднть рейтинг данного пользователя если нажали случайно нажмите кнопку отмены.", 
                                                 reply_markup=canceled_list_worker)
    canceled_edit_message_id[callback.message.chat.id] = send_message.message_id
    await state.set_state(states.rating_up)

@rout.message(states.rating_up, F.text)
async def is_up(message: Message, state: FSMContext) -> None:
    global canceled_edit_message_id
    try:
        if (message.chat.id in canceled_edit_message_id) and canceled_edit_message_id[message.chat.id] != 0:
            await delete_message(message=message, message_id=canceled_edit_message_id[message.chat.id])
            canceled_edit_message_id[message.chat.id] = 0
        count = abs(int(message.text))
        await db.update_rating_up_value(user_id[message.chat.id], count)
        await edit_message_profile(message)
        await state.clear()
    except Exception:
        send = await message.answer("Произошла ошибка, напишите число еще раз.",
                             reply_markup=canceled_list_worker)
        canceled_edit_message_id[message.chat.id] = send.message_id

@rout.callback_query(F.data == "rating_down")
async def rating_down(callback: CallbackQuery, state: FSMContext) -> None:
    global canceled_edit_message_id
    await callback.answer("")
    send_message = await callback.message.answer("напишите число на сколько опустить рейтинг данного пользователя если нажали случайно нажмите кнопку отмены.",
                                                reply_markup=canceled_list_worker)
    canceled_edit_message_id[callback.message.chat.id] = send_message.message_id
    await state.set_state(states.rating_down)

@rout.message(states.rating_down, F.text)
async def is_up(message: Message, state: FSMContext) -> None:
    global canceled_edit_message_id
    try:
        if (message.chat.id in canceled_edit_message_id) and canceled_edit_message_id[message.chat.id] != 0:
            await delete_message(message=message, message_id=canceled_edit_message_id[message.chat.id])
            canceled_edit_message_id[message.chat.id] = 0
        count = abs(int(message.text))
        await db.update_rating_down_value(user_id[message.chat.id], count)
        await edit_message_profile(message)
        await state.clear()
    except Exception:
        send = await message.answer("Произошла ошибка, напишите число еще раз.",
                             reply_markup=canceled_list_worker)
        canceled_edit_message_id[message.chat.id] = send.message_id

@rout.callback_query(F.data == "yes")
async def yes_fire(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("")
    await callback.message.edit_text("Напишите причину увольнения.", inline_message_id=callback.inline_message_id, reply_markup=None)
    await state.set_state(states.fire_worker)
    await state.update_data(fire_worker = callback.message.message_id)

@rout.message(states.fire_worker, F.text)
async def fire(message: Message, state: FSMContext) -> None:
    message_id = await state.get_data()
    await message.bot.edit_message_text("Я передал приину увольнения бывшему сотруднику.", chat_id=message.chat.id, message_id=message_id["fire_worker"])
    await message.bot.send_message(chat_id=user_id[message.chat.id], text=f"Вас уволили по причине '{message.text}'", reply_markup=types.ReplyKeyboardRemove())
    await db.delete_profile(user_id[message.chat.id])
    await state.clear()

@rout.callback_query(F.data == "no")
async def no_fire(callback: CallbackQuery) -> None:
    await callback.answer("")
    await callback.message.edit_text("Я вас понял.", inline_message_id=callback.inline_message_id, reply_markup=None)

@rout.callback_query(F.data == "canceled_list_worker")
async def canceled_worker_list(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=None)
    await callback.message.edit_text("Можете заниматся своими делами дальше.", inline_message_id=callback.inline_message_id)
    await state.clear()

async def edit_message_function(message: Message) -> None:
    key = f'{message.chat.id}'
    if key in edit_message:
        await message.bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=edit_message[key], reply_markup=None)

async def edit_message_set(message: Message, value) -> None:
    global edit_message
    key = f'{message.chat.id}'
    edit_message[key] = value

async def zero_count_create_event() -> None:
    global count_create_event
    count_create_event = 0

async def create_dict_event() -> None:
    global count_event_subscribes
    data: Event | None = await db.get_event_created()
    if data != None:
        if data.method_of_work == "Вахта":
            count_event_subscribes[f'{data.date}-{data.count_days}'] = []
        else:
            for day in range(1, data.count_days + 1):
                count_event_subscribes[f'{data.date}-{day}'] = []

async def create_list_days() -> None:
    global day_count
    data: Event | None = await db.get_event_created()
    if data != None:
        date = data.date
        date_split = date.split("-")
        date_format = '%d.%m.%Y'
        date_start = datetime.strptime(date_split[0].strip(), date_format)
        date_end = datetime.strptime(date_split[1].strip(), date_format)
        date_curent = date_start
        count_day = []
        while date_curent <= date_end:
            count_day.append(date_curent.strftime("%d"))
            date_curent += timedelta(days=1)
        day_count[data.date] = count_day

async def update_status_event() -> None:
    await db.update_status_planing()

async def edit_message_profile(message: Message) -> None:
    data: User | None = await db.get_profile(user_id[message.chat.id])
    await message.bot.edit_message_caption(chat_id=message.chat.id, message_id=edit_message_id_profile[message.chat.id], caption=await message_profile_view(data), reply_markup=worker_profile)

async def delete_message(message: Message, message_id: int) -> None:
    await message.bot.delete_message(chat_id=message.chat.id, message_id=message_id)
    await message.bot.delete_message(chat_id=message.chat.id, message_id=message_id + 1)