from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from app.InlineButtonHeandler import create_event
from datetime import datetime

import app.DataBase.requests as db
import re
import config

rout = Router()
days_event = 0

class Create(StatesGroup):
    name = State()
    description = State()
    date = State()
    method_of_work = State()
    count_people = State()
    location = State()

async def start_create(message: Message, state: FSMContext) -> None:
    await state.set_state(Create.name)
    await message.answer("Напишите название мероприятия, в названии также укажите город.")

@rout.message(Create.name, F.text)
async def set_name_event(message: Message, state: FSMContext) -> None:
    await state.update_data(name = message.text)
    await state.set_state(Create.description)
    await message.answer("Напишите небольшое описание мероприятия.")

@rout.message(Create.description, F.text)
async def set_description_event(message: Message, state: FSMContext) -> None:
    await state.update_data(description = message.text)
    await state.set_state(Create.method_of_work)
    await message.answer("Напишите цифру метода работы. (1 - вахта, 2 - подработка)")
    

@rout.message(Create.method_of_work, F.text)
async def set_method_of_work_event(message: Message, state: FSMContext) -> None:
    try:
        count = int(message.text)
        if count >= 1 and count <= 2:
            if count == 1:
                await state.update_data(method_of_work = "Вахта")
            elif count == 2:
                await state.update_data(method_of_work = "Подработка")
            await message.answer("Напишите дату начала и конца мероприятия (дд.мм.гггг - дд.мм.гггг)")
            await state.set_state(Create.date)
        else:
            await message.answer("Не понял вас, напишите цифру метода работы еще раз. (1 - вахта, 2 - подработка)")
    except Exception:
        await message.answer("Произошла ошибка, напишите число еще раз.")

@rout.message(Create.date, F.text)
async def set_date_event(message: Message, state: FSMContext) -> None:
    try:
        split_text = message.text.split("-")
        event_data_1 = datetime.strptime(split_text[0].strip(), '%d.%m.%Y')
        event_data_2 = datetime.strptime(split_text[1].strip(), '%d.%m.%Y')
        if event_data_1 > event_data_2:
            await message.answer("Дата начала не может быть больше даты конца, напишите правильную дату.")
        else:
            await state.update_data(date = message.text)
            await state.set_state(Create.count_people)
            await message.answer("Напишите количество требуемых маршалов.")
    except Exception:
        await message.answer("Не верный фрмат даты, напишите дату еще раз.")

@rout.message(Create.count_people, F.text)
async def set_count_people(message: Message, state: FSMContext) -> None:
    try:
        count_people = int(message.text)
        await state.update_data(count_people = count_people)
        await state.set_state(Create.location)
        await message.answer("Пришлите пожалуйста ссылку на место проведени взятую из карт или напишите 'нет' если ее нет.")
    except Exception:
        await message.answer("Произошла ошибка, напишите количество человек еще раз.")

@rout.message(Create.location, F.text)
async def set_location_event(message: Message, state: FSMContext) -> None:
    if re.match(config.MAP_LINK_PATTERN, message.text) or message.text.lower() == "нет":
        await state.update_data(location = message.text)
        data = await state.get_data()
        await set_count_day(message, data)
    else:
        await message.answer("Я вас не понял, пришлите ссылку или напишите 'нет' если ее нет")

async def set_count_day(message: Message, data) -> None:
    date = data["date"]
    date_split = date.split("-")
    date_format = '%d.%m.%Y'
    dateOne = datetime.strptime(date_split[0].strip(), date_format)
    dateTwo = datetime.strptime(date_split[1].strip(), date_format)
    days = (dateTwo - dateOne).days + 1
    await final_create_event(message, data, days)

async def final_create_event(message: Message, data, days) -> None:
    global days_event
    await message.answer(text=await view_event(data, days), reply_markup=create_event)
    days_event = days

async def view_event(data, days) -> str:
    returnCreateEventText = f'Проверте анкету мероприятия:\nНазвание: {data["name"]}\nОписание: {data["description"]}\nДата проведения: {data["date"]}\nКоличество дней: {days}\nМетод работы: {data["method_of_work"]}\nКоличество маршалов: {data["count_people"]}\nМесто на картах: {data["location"]}'
    return returnCreateEventText

@rout.callback_query(F.data == "create")
async def create(callback: CallbackQuery, state: FSMContext) -> None:
    from app.heandlers import update_status_event
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=None)
    await callback.answer("")
    data = await state.get_data()
    status = "Создается"
    await db.set_event(data["name"], data["description"], data["date"], data["method_of_work"],
                       data["count_people"], data["location"], status, days_event)
    await state.clear()
    await callback.message.answer("Вы успешно создали мероприятие.")
    await signal_create_dict(status)
    await signal_create_list_days(status)
    await zero_count()
    await newsletter(callback.message, status)
    await update_status_event()

async def newsletter(message: Message, status: str) -> None:
    if status == "Создается":
        chat_id = await db.get_worker_id()
        for id in chat_id:
            await message.bot.send_message(chat_id=id, text="Появилось новое мероприятие успейте записатся.")

async def signal_create_dict(status: str) -> None:
    if status == "Создается":
        from app.heandlers import create_dict_event
        await create_dict_event()

async def signal_create_list_days(status: str) -> None:
    if status == "Создается":
        from app.heandlers import create_list_days
        await create_list_days() 

@rout.callback_query(F.data == "remake")
async def remake(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=None)
    await callback.answer("")
    await callback.message.answer("Давайте переделаем анкту мероприятия, напишите название мероприятия, в названии также укажите город проведения.")
    await state.set_state(Create.name)

@rout.callback_query(F.data =="canceled_create")
async def canceled_create_event(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=None)
    await zero_count()
    await callback.answer("")
    await callback.message.answer("Я отменил создание мероприятия.")
    await state.clear()

async def zero_count() -> None:
    from app.heandlers import zero_count_create_event
    await zero_count_create_event()