from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

moderation = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Моя анкета"), KeyboardButton(text="Мероприятие")]
    ], 
                                 resize_keyboard=True)

employee = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Мероприятие")],
    [KeyboardButton(text="Моя анкета"), KeyboardButton(text="Обучение"), KeyboardButton(text="Наша команда")]
    ], 
                               resize_keyboard=True)

owner = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Моя анкета"), KeyboardButton(text="Мероприятие"), KeyboardButton(text="Создать мероприятие")],
    [KeyboardButton(text="Проверка анкет"), KeyboardButton(text="Список работников"), KeyboardButton(text="Список мероприятий")]
    ], 
                               resize_keyboard=True)