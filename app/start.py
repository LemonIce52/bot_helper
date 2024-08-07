from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile, CallbackQuery
from aiogram.filters.command import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from app.InlineButtonHeandler import register_button, register_dont_pass_id
from app.ReplyButtonHeandler import moderation, owner
from app.passCipher import PassEncrypt
import app.DataBase.requests as db
import config

rout = Router()
pass_encrypt = PassEncrypt()

class Registration(StatesGroup):
    message_id = State()
    name = State()
    birthday = State()
    phone_number = State()
    passport = State()
    username = State()
    photo = State()
    
@rout.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    if await db.is_user(message.chat.id):
        await message.answer("Мы с тобой уже знакомы.")
    else:
        await message.answer("Привет, я вижу тебя нет в списках, давай зарагестрируем тебя. Напиши мне свое имя.")
        await state.set_state(Registration.name)

@rout.message(Registration.name, F.text)
async def set_birthday(message: Message, state: FSMContext) -> None:
    await state.update_data(name = message.text)
    await message.answer("Пришлите свой возраст.")
    await state.set_state(Registration.birthday)
    
@rout.message(Registration.birthday, F.text)
async def set_phone_number(message: Message, state: FSMContext) -> None:
    try:
        date_format = "%d.%m.%Y"
        is_birthday = datetime.strptime(message.text, date_format)
        birthday = message.text
        await state.update_data(birthday = birthday)
        await message.answer("Прекрасно, теперь напиши мне свой номер телефона.")
        await state.set_state(Registration.phone_number)
    except Exception:
        await message.answer("Я попросил твой возраст.")

@rout.message(Registration.phone_number, F.text)
async def set_passport(message: Message, state: FSMContext) -> None:
    await state.update_data(phone_number = message.text)
    await state.set_state(Registration.message_id)
    send = await message.answer("Прекрассно, напишите пожалуйста номер своего паспорта если не хотите нажмите кнопку ниже.", reply_markup=register_dont_pass_id)
    await state.update_data(message_id = send.message_id)
    await state.set_state(Registration.passport)

@rout.message(Registration.passport, F.text)
async def is_set_user_name(message: Message, state: FSMContext) -> None:
    message_id = await state.get_data()
    await message.bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message_id["message_id"])
    await set_user_name(message, state, message.text)

async def set_user_name(message: Message, state: FSMContext, pass_id: str) -> None:
    await state.update_data(passport = pass_id)
    await message.answer("прекрассо а теперь пришли свое фото.")
    await state.set_state(Registration.photo)

@rout.message(Registration.photo, F.photo)
async def set_photo(message: Message, state: FSMContext) -> None:
    photo_id = message.photo[-1].file_id
    photo_info = await message.bot.get_file(photo_id)
    photo = await message.bot.download_file(photo_info.file_path)
    photo.seek(0)
    await state.update_data(photo = photo.read())
    await state.set_state(Registration.username)
    await state.update_data(username = message.from_user.username)
    await final_registration(message, state)

async def final_registration(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    username = await set_full_username(data["username"])
    await message.answer_photo(
        BufferedInputFile(data["photo"], filename="photo.jpg"),
        await profile_view(data["name"], data["birthday"], data["phone_number"], data["passport"], username), 
        reply_markup=register_button)

async def profile_view(name, birthday, phone_number, passport, username) -> str:
    message = f'Проверьте вашу анкету, если все правильно отправляйте на модерацию.\nФИО: {name}\nДата рождения: {birthday}\nНомер телефона: {phone_number}\nНомер паспорта: {passport}\nВаше имя пользователя: {username}'
    return message

@rout.callback_query(Registration.passport, F.data == "dont_pass")
async def dont_pass(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=None)
    await set_user_name(callback.message, state, "Не предоставил.")

@rout.callback_query(F.data == 'send')
async def send_profile(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=None)
    data = await state.get_data()
    username = await set_full_username(data["username"])
    
    if await db.count_user() < config.COUNT_OWNER:
        status = config.OWNER_STATUS[0]
    else:
        status = 'Модерация'
    
    await db.set_user(data["photo"], callback.message.chat.id,
                      data["name"], data["birthday"], data["phone_number"],
                      username, 0, status, await pass_encrypt.encrypt(data["passport"]))
    await callback.answer("")
    await message_moderation(callback)
    await state.clear()

async def set_full_username(username: str | None) -> str:
    if username != None:
        username_return = f'@{username}'
    else:
        username_return = 'Не задано.'
    return username_return

async def message_moderation(callback: CallbackQuery) -> None:
    status = await db.get_status(callback.message.chat.id)
    if status == 'Владелец':
        await callback.message.answer("Добро пожаловать.", reply_markup=owner)
    elif status == 'Модерация':
        await callback.message.answer("Я отправил, ожидайте модерацию.", reply_markup=moderation)
        owner_chat = await db.get_id_owner()
        await callback.message.bot.send_message(chat_id=owner_chat, text="Появилась новая анкета, успейте проверить.")

@rout.callback_query(F.data == 'redo')
async def redo_profile(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id, reply_markup=None)
    await callback.answer("")
    await callback.message.answer("Прошу прощение. Напишите мне еще раз свое имя.")
    await state.set_state(Registration.name)