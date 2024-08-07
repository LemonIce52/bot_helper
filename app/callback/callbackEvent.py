from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from app.heandlers import count_event_subscribes
from app.InlineButtonHeandler import sub_or_unSub_button, canceled_newsletter_time, rating_profile
from app.passCipher import PassDecrypt
from app.DataBase.models import Event, User
import app.DataBase.requests as db
import config

rout = Router()
pass_decrypt = PassDecrypt()

message_id = 0
message_id_passed_or_canceled = 0
count_day = 0
checking_days_event = 0
count_events_people = []

class state_accept(StatesGroup):
    message_id = State()
    passed = State()
    canceled = State()

@rout.callback_query(F.data.regexp(config.CALLBACK_PATTERN_SUBSCRIBE))
async def subscribe(callback: CallbackQuery) -> None:
    from app.heandlers import number_list_event_worker
    try:
        await callback.answer("")
        if await db.get_status(callback.message.chat.id) != "Модерация":
            count_event = await db.count_event_where_planing()
            chat_id = callback.message.chat.id
            split_data = callback.data.split(':')
            first_part_data = split_data[0]
            data_event = await db.get_event(number_list_event_worker[f'{callback.message.chat.id}'] - 1)
            if first_part_data == "tour":
                count_event_subscribes[f'{data_event.date}-{data_event.count_days}'].append(chat_id)
            else:
                count_event_subscribes[f'{data_event.date}-{first_part_data}'].append(chat_id)
            await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=await sub_or_unSub_button(chat_id, count_event, number_list_event_worker[f'{callback.message.chat.id}'] - 1))
        else:
            await callback.message.answer("Вы еще на модерации и не можете принимать участие на мероприятиях")
    except KeyError:
        await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=None)
        await callback.answer("")
        await callback.message.answer("Мероприятие уже закончилось, списков больше нет.")

@rout.callback_query(F.data.regexp(config.CALLBACK_PATTERN_UNSUBSCRIBE))
async def unsubscribe(callback: CallbackQuery) -> None:
    from app.heandlers import number_list_event_worker
    try:
        await callback.answer("")
        if await db.get_status(callback.message.chat.id) != "Модерация":
            count_event = await db.count_event_where_planing()
            chat_id = callback.message.chat.id
            split_data = callback.data.split(':')
            first_part_data = split_data[0]
            data_event = await db.get_event(number_list_event_worker[f'{callback.message.chat.id}'] - 1)
            if first_part_data == "tour":
                count_event_subscribes[f'{data_event.date}-{data_event.count_days}'].remove(chat_id)
            else:
                count_event_subscribes[f'{data_event.date}-{first_part_data}'].remove(chat_id)
            await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=await sub_or_unSub_button(chat_id, count_event, number_list_event_worker[f'{callback.message.chat.id}'] - 1))
    except KeyError:
        await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=None)
        await callback.answer("")
        await callback.message.answer("Мероприятие уже закончилось, списков больше нет.")

@rout.callback_query(F.data == 'countSubscribes')
async def count_subscribes(callback: CallbackQuery) -> None:
    from app.heandlers import number_list_event_worker
    await callback.answer("")
    data_event = await db.get_event(number_list_event_worker[f'{callback.message.chat.id}'] - 1)
    if data_event.method_of_work == "Вахта":
        await partTimeJob(callback.message, data_event)
    else:
        await watch(callback.message, data_event)

async def watch(message: Message, data_event: object) -> None:
    message_text = ""
    for days in range(1, data_event.count_days + 1):
        day_key = f"{data_event.date}-{days}"
        if day_key in count_event_subscribes:
            message_text += f"День {days}. Подписавшиеся:\n\n"
            if count_event_subscribes[day_key]:
                for count, user_id in enumerate(count_event_subscribes[day_key], start=1):
                    data = await db.get_profile(user_id)
                    message_text += f"{count}. {data.full_name} - {data.username}\n"
                    
                message_text += "\n"
            else:
                message_text += "--------\n"
    if message_text:
        await message.answer(message_text)

async def partTimeJob(message: Message, data_event: object) -> None:
    message_text = ""
    day_key = f"{data_event.date}-{data_event.count_days}"
    if day_key in count_event_subscribes:
        message_text += f"Подписавшиеся:\n\n"
        if count_event_subscribes[day_key]:
            for count, user_id in enumerate(count_event_subscribes[day_key], start=1):
                data = await db.get_profile(user_id)
                message_text += f"{count}. {data.full_name} - {data.username}\n"
                    
                message_text += "\n"
        else:
            message_text += "--------\n"
    if message_text:
        await message.answer(message_text)

@rout.callback_query(F.data == 'newsletter')
async def newsletter_time(callback: CallbackQuery, state: FSMContext) -> None:
    global message_id
    message_id = callback.inline_message_id
    await callback.answer("")
    await state.set_state(state_accept.message_id)
    send = await callback.message.answer("Напишите то отправить людям которые подписались если нажали случайно нажмите кнопку отмена.", reply_markup=canceled_newsletter_time)
    await state.update_data(message_id = send.message_id)

@rout.message(state_accept.message_id, F.text)
async def time(message: Message, state: FSMContext) -> None:
    from app.heandlers import number_list_event_worker
    data = await state.get_data()
    await message.bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=data["message_id"], reply_markup=None)
    text = message.text
    data = await db.get_event(number_list_event_worker[f'{message.chat.id}'] - 1)
    if data.method_of_work == "Вахта" and count_event_subscribes.get(f'{data.date}-{data.count_days}'):
        for number_people in range(0, len(count_event_subscribes[f'{data.date}-{data.count_days}'])):
            await message.bot.send_message(count_event_subscribes[f'{data.date}-{data.count_days}'][number_people], f"Сообщение по поводу мероприятия {data.name}:\n{text}")
    else:
        exceptions = []
        for countDay in range(1, data.count_days + 1):
            key = f'{data.date}-{countDay}'
            for countPeople in range(0, len(count_event_subscribes[key])):
                if (count_event_subscribes[key][countPeople] in exceptions) == False:
                    exceptions.append(count_event_subscribes[key][countPeople])
                    await message.bot.send_message(count_event_subscribes[key][countPeople], f"Сообщение по поводу мероприятия {data.name}:\n{text}")
    await message.answer("Я разослал время всем подписавшимся.")
    await state.clear()

@rout.callback_query(state_accept.message_id, F.data == 'canceled_time')
async def canceled_time(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=None)
    await callback.message.bot.edit_message_text("Я отменил рассылку.", chat_id=callback.message.chat.id, inline_message_id=callback.inline_message_id)
    await state.clear()

@rout.callback_query(F.data == 'passed')
async def passed_event(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=None)
    await callback.answer("")
    await state.set_state(state_accept.passed)
    await callback.message.answer("Вы точно хотите поставить статус прошло? (напишите да или нет)")

@rout.message(state_accept.passed, F.text)
async def passed(message: Message, state: FSMContext) -> None:
    if message.text.lower() == "да":
        message.answer("Прекрассно, а теперь оценим присутсвующих")
        await count_length_direct(message, 'Прошло')
        await state.clear()
    elif message.text.lower() != "нет":
        await message.answer("Я вас не понял, напишите нет или да.")
    else:
        await message.answer("Я понял вас.")
        await state.clear()

@rout.callback_query(F.data == 'canceled_event')
async def canceled_event(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=None)
    await callback.answer("")
    await state.set_state(state_accept.canceled)
    await callback.message.answer("Вы точно хотите поставить статус отменено? (напишите да или нет)")

@rout.message(state_accept.canceled, F.text)
async def canceled(message: Message, state: FSMContext) -> None:
    if message.text == "Да" or message.text == "да":
        await count_length_direct(message, 'Отменено')
        await cancel_event(message)
        await state.clear()
    elif message.text.lower() != "нет":
        await message.answer("Я вас не понял, напишите нет или да.")
    else:
        await message.answer("Я понял вас.")
        await state.clear()

async def cancel_event(message: Message) -> None:
    chat_id = await db.get_worker_id()
    for id in chat_id:
       await message.bot.send_message(id, "Мероприятие отменилось по техническим причинам, приносим свои извенения.")

async def count_length_direct(message: Message, status: str) -> None:
    from app.heandlers import number_list_event_worker
    global count_event_subscribes, checking_days_event, count_day
    data = await db.get_event(number_list_event_worker[f'{message.chat.id}'] - 1)
    if data.method_of_work == "Подработка":
        for days in range(1, data.count_days + 1):
            key = f'{data.date}-{days}'
            if count_event_subscribes.get(key):
                count_day = days
                await ratingProfiles(message, count_day)
                checking_days_event = days
                break
            elif key in count_event_subscribes:
                del count_event_subscribes[key]
    else:
        key = f'{data.date}-{data.count_days}'
        if count_event_subscribes.get(key):
            checking_days_event = data[8]
            await ratingProfiles(message, count_day)      
        elif key in count_event_subscribes:
            del count_event_subscribes[key]

    await replyByStatus(message, status, data.date)

async def ratingProfiles(message: Message, day: int) -> None:
    from app.heandlers import number_list_event_worker
    data: Event = await db.get_event()
    if count_event_subscribes.get(f'{data.date}-{day}'):
        dataEvent = await db.get_event(number_list_event_worker[f'{message.chat.id}'] - 1)
        data: User = await db.get_profile(count_event_subscribes[f'{dataEvent.date}-{day}'][0])
        text = await rating_account_text(data, await pass_decrypt.decrypt(data.passport_data))
        await message.answer(text, reply_markup=rating_profile)
    else:
        await count_length_direct(message, 'Прошло')

async def replyByStatus(message: Message, status: str, date) -> None:
    from app.heandlers import number_list_event_worker
    offset = number_list_event_worker[f'{message.chat.id}'] - 1
    if status == 'Прошло' and await is_key(date):
        await message.answer("Оценка закончена спасибо.")
        await db.update_username_people(count_events_people, offset)
        await db.update_status_events(status, offset)
    elif status == 'Отменено' and await is_key(date):
        await message.answer("Очень жаль что оно отменилось.")
        await db.update_username_people([], offset)
        await db.update_status_events(status, offset)

async def is_key(date) -> bool:
    for key in count_event_subscribes:
        if key.startswith(date):
            return False
    return True

async def rating_account_text(data, passport) -> str:
    ratingAccount = f"Номер сотрудника: {data.id} \nФИО: {data.full_name} \nВозраст: {data.year}\nНомер телефона: {data.phone_number}\nНик телеграмм: {data.username}\nПаспортные данные: {passport}\nРейтин: {data.rating}\nСтатус: {data.status}"
    return ratingAccount

@rout.callback_query(F.data == "came")
async def came(callback: CallbackQuery) -> None:
    from app.heandlers import number_list_event_worker
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=None)
    data = await db.get_event(number_list_event_worker[f'{callback.message.chat.id}'] - 1)
    await db.update_rating_up(count_event_subscribes[f'{data.date}-{checking_days_event}'][0])
    data_profile = await db.get_profile(count_event_subscribes[f'{data.date}-{checking_days_event}'][0])
    count_events_people.append(data_profile.username)
    del count_event_subscribes[f'{data.date}-{checking_days_event}'][0]
    await ratingProfiles(callback.message, count_day)

@rout.callback_query(F.data == "did_not_came")
async def did_not_came(callback: CallbackQuery) -> None:
    from app.heandlers import number_list_event_worker
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=None)
    data = await db.get_event(number_list_event_worker[f'{callback.message.chat.id}'] - 1)
    await db.update_rating_down(count_event_subscribes[f'{data.date}-{checking_days_event}'][0])
    del count_event_subscribes[f'{data.date}-{checking_days_event}'][0]
    await ratingProfiles(callback.message, count_day)