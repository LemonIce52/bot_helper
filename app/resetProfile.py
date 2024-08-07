from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from app.InlineButtonHeandler import cancel_reset, reset_yes_or_no, button_on_reset
from app.DataBase.models import User
from app.passCipher import PassEncrypt, PassDecrypt
import app.DataBase.requests as db
import config

rout = Router()
pass_encrypt = PassEncrypt()
pass_decrypt = PassDecrypt()

edit_message_reset = {}

class ResetState(StatesGroup):
    reset_full_name = State()
    reset_phone_number = State()
    reset_user_name = State()
    reset_pass_data = State()

@rout.callback_query(F.data == "reset_full_name")
async def reset_full_name(callback: CallbackQuery, state: FSMContext) -> None:
    global edit_message_reset
    await callback.answer("")
    await state.set_state(ResetState.reset_full_name)
    send = await callback.message.answer("Пришлите пожалуйста новое ФИО.", reply_markup=cancel_reset)
    edit_message_reset[f'{callback.message.chat.id}'] = send.message_id

@rout.message(ResetState.reset_full_name, F.text)
async def set_new_full_name(message: Message, state: FSMContext) -> None:
    await state.update_data(reset_full_name = message.text)
    data: User = await db.get_profile(message.chat.id)
    await message.answer_photo(photo=BufferedInputFile(data.photo, filename="photo.jpg"),
                               caption=await profile_view(message.text, data.year, data.phone_number,await pass_decrypt.decrypt(data.passport_data, config.KEY_CIPHER), data.username),
                               reply_markup=reset_yes_or_no)

@rout.callback_query(F.data == "reset_phone_number")
async def reset_phone_number(callback: CallbackQuery, state: FSMContext) -> None:
    global edit_message_reset
    await callback.answer("")
    await state.set_state(ResetState.reset_phone_number)
    send = await callback.message.answer("Пришлите пожалуйста новый номер телефона.", reply_markup=cancel_reset)
    edit_message_reset[f'{callback.message.chat.id}'] = send.message_id

@rout.message(ResetState.reset_phone_number, F.text)
async def set_phone_number(message: Message, state: FSMContext) -> None:
    await state.update_data(reset_phone_number = message.text)
    data: User = await db.get_profile(message.chat.id)
    await message.answer_photo(photo=BufferedInputFile(data.photo, filename="photo.jpg"),
                               caption=await profile_view(data.full_name, data.year, message.text, await pass_decrypt.decrypt(data.passport_data, config.KEY_CIPHER), data.username),
                               reply_markup=reset_yes_or_no)

@rout.callback_query(F.data == "reset_user_name")
async def reset_phone_number(callback: CallbackQuery, state: FSMContext) -> None:
    global edit_message_reset
    await callback.answer("")
    await state.set_state(ResetState.reset_user_name)
    send = await callback.message.answer("Пришлите пожалуйста любой текст.", reply_markup=cancel_reset)
    edit_message_reset[f'{callback.message.chat.id}'] = send.message_id

@rout.message(ResetState.reset_user_name, F.text)
async def set_phone_number(message: Message, state: FSMContext) -> None:
    user_name = f'@{message.from_user.username}'
    await state.update_data(reset_user_name = user_name)
    data: User = await db.get_profile(message.chat.id)
    await message.answer_photo(photo=BufferedInputFile(data.photo, filename="photo.jpg"),
                               caption=await profile_view(data.full_name, data.year, data.phone_number, await pass_decrypt.decrypt(data.passport_data, config.KEY_CIPHER), user_name),
                               reply_markup=reset_yes_or_no)

@rout.callback_query(F.data == "reset_pass_data")
async def reset_phone_number(callback: CallbackQuery, state: FSMContext) -> None:
    global edit_message_reset
    await callback.answer("")
    await state.set_state(ResetState.reset_pass_data)
    send = await callback.message.answer("Пришлите пожалуйста новый номер паспорта.", reply_markup=cancel_reset)
    edit_message_reset[f'{callback.message.chat.id}'] = send.message_id

@rout.message(ResetState.reset_pass_data, F.text)
async def set_phone_number(message: Message, state: FSMContext) -> None:
    await state.update_data(reset_pass_data = message.text)
    data: User = await db.get_profile(message.chat.id)
    await message.answer_photo(photo=BufferedInputFile(data.photo, filename="photo.jpg"),
                               caption=await profile_view(data.full_name, data.year, data.phone_number, message.text, data.username),
                               reply_markup=reset_yes_or_no)

@rout.callback_query(F.data == "yes_reset")
async def yes_reset(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("")
    await deleted_message(callback.message, edit_message_reset[f'{callback.message.chat.id}'], 1)
    other_state =''
    new_value = None
    data = await state.get_data()
    match await state.get_state():
        case 'ResetState:reset_full_name':
            other_state = 'full_name'
            new_value = data['reset_full_name']
        case 'ResetState:reset_phone_number':
            other_state = 'phone_number'
            new_value = data['reset_phone_number']
        case 'ResetState:reset_user_name':
            other_state = 'username'
            new_value = data['reset_user_name']
        case 'ResetState:reset_pass_data':
            other_state = 'pass_data'
            new_value = await pass_encrypt.encrypt(data['reset_pass_data'])
    await db.update_profile(other_state, new_value, callback.message.chat.id)
    data: User = await db.get_profile(callback.message.chat.id)
    await callback.message.answer_photo(photo=BufferedInputFile(data.photo, "photo.jpg"), caption=await message_my_profile(data), reply_markup=button_on_reset)
    id_owner = await db.get_id_owner()
    await state.clear()
    await callback.message.bot.send_message(chat_id=id_owner, 
                                            text=f"Пользователь {data.username} изменил данные в анкете, проверьте (команда 'анкета <ник телеграмм>'),если чтото не так то попросите его изменить на корректные данные")

@rout.callback_query(F.data == "no_reset")
async def no_reset(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("")
    await deleted_message(callback.message, edit_message_reset[f'{callback.message.chat.id}'], 1)
    data: User = await db.get_profile(callback.message.chat.id)
    await callback.message.answer_photo(photo=BufferedInputFile(data.photo, "photo.jpg"), caption=await message_my_profile(data), reply_markup=button_on_reset)
    name_reset = ''
    match await state.get_state():
        case 'ResetState:reset_full_name':
            name_reset = "новое ФИО"
        case 'ResetState:reset_phone_number':
            name_reset = "новый номер телефона"
        case 'ResetState:reset_user_name':
            name_reset = "любой текст"
        case 'ResetState:reset_pass_data':
            name_reset = "новый паспортный номер"
    send = await callback.message.answer(f"Видимо я вас не так понял, пришлите пожалуйста {name_reset}.", reply_markup=cancel_reset)
    edit_message_reset[f'{callback.message.chat.id}'] = send.message_id

async def profile_view(name, birthday, phone_number, passport, username) -> str:
    message = f'Проверьте вашу анкету, все правильно?\nФИО: {name}\nДата рождения: {birthday}\nНомер телефона: {phone_number}\nНомер паспорта: {passport}\nВаше имя пользователя: {username}'
    return message

async def message_my_profile(data: object) -> str:
    passport = await pass_decrypt.decrypt(data.passport_data, config.KEY_CIPHER)
    message = f'Ваша анкета:\nФИО: {data.full_name} \nДата рождения: {data.year}\nНомер телефона: {data.phone_number}\nНик телеграмм: {data.username}\nПаспортные данные: {passport}\nРейтин: {data.rating}\nСтатус: {data.status}'
    return message

async def edit_message(message: Message) -> None:
    global edit_message_reset
    key = f'{message.chat.id}'
    if key in edit_message_reset:
        await message.bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=edit_message_reset[key])
        del edit_message_reset[key]

async def edit_message_set(message: Message, value) -> None:
    global edit_message_reset
    key = f'{message.chat.id}'
    edit_message_reset[key] = value

async def deleted_message(message: Message, message_id: int, back_message: int) -> None:
    if back_message != 0:
        await message.bot.delete_message(message.chat.id, message_id - back_message)
    for number_message in range(3):
        await message.bot.delete_message(message.chat.id, message_id + number_message)