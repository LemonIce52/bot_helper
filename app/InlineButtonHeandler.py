from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import app.DataBase.requests as db

register_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Отправить", callback_data="send"), InlineKeyboardButton(text="Переделать", callback_data="redo")]
    ])

register_dont_pass_id = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Не предоставлять.", callback_data="dont_pass")]
    ])

moderation_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Принять", callback_data="accept"), InlineKeyboardButton(text="Отказать", callback_data="canceled")]
    ])

create_event = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Создать", callback_data="create"), InlineKeyboardButton(text="Переделать", callback_data="remake")],
    [InlineKeyboardButton(text="Отменить создание", callback_data="canceled_create")]
    ])

event_owner = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Люди согласные поехать", callback_data="countSubscribes")],
    [InlineKeyboardButton(text="Рассылка.", callback_data="newsletter")],
    [InlineKeyboardButton(text="Прошло", callback_data="passed"), InlineKeyboardButton(text="Отменено", callback_data="canceled_event")]
    ])

event_owner_more_one = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="<--", callback_data="<--:view_event_planing"), InlineKeyboardButton(text="-->", callback_data="-->:view_event_planing")],
    [InlineKeyboardButton(text="Люди согласные поехать", callback_data="countSubscribes")],
    [InlineKeyboardButton(text="Рассылка.", callback_data="newsletter")],
    [InlineKeyboardButton(text="Прошло", callback_data="passed"), InlineKeyboardButton(text="Отменено", callback_data="canceled_event")]
    ])

canceled_newsletter_time = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Отмена", callback_data="canceled_time")]
    ]) 

rating_profile = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Пришел", callback_data="came"), InlineKeyboardButton(text="Не пришел", callback_data="did_not_came")]
    ])

worker_profile = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⬆️ рейтинг", callback_data="rating_up"), InlineKeyboardButton(text="⬇️ рейтинг", callback_data="rating_down")],
    [InlineKeyboardButton(text="Отправить сообщение", callback_data="send_message")],
    [InlineKeyboardButton(text="Присвоить новый статус", callback_data="new_staus")],
    [InlineKeyboardButton(text="Уволить", callback_data="fire")]
    ])

event_people_view = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Показать пришедших", callback_data="view_people_event")]
    ])

fire_worker = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Да", callback_data="yes"), InlineKeyboardButton(text="Нет", callback_data="no")]
    ])

canceled_list_worker = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Отмена", callback_data="canceled_list_worker")]
    ])

button_on_reset = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Переделать анкету", callback_data="reset_profile")]
    ])

reset_profile_buttons = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Изменить ФИО", callback_data="reset_full_name")],
    [InlineKeyboardButton(text="Изменить номер телефона", callback_data="reset_phone_number")],
    [InlineKeyboardButton(text="Изменить ник телеграмм",callback_data="reset_user_name")],
    [InlineKeyboardButton(text="Изменить паспортные данные", callback_data="reset_pass_data")],
    [InlineKeyboardButton(text="вернутся назад", callback_data="return")]
    ])

reset_yes_or_no = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Да", callback_data="yes_reset"), InlineKeyboardButton(text="Нет", callback_data="no_reset")]
    ])

cancel_reset = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Отмена", callback_data="canceled_reset")]
    ])

async def view_event(count: int, other_filter: str) -> InlineKeyboardMarkup:
    from app.heandlers import view_event_filters
    keyboard = InlineKeyboardBuilder()
    translate_filter = ""
    if count > 10:
        keyboard.row(InlineKeyboardButton(text="<--", callback_data="<--:events"), InlineKeyboardButton(text="-->", callback_data="-->:events"))
    for filter in view_event_filters:
        if other_filter == filter:
            keyboard.add(InlineKeyboardButton(text="Все", callback_data="all_event"))
        else:
            if filter == 'Планируется':
                translate_filter = "planing"
            elif filter == 'Отменено':
                translate_filter = "canceled_event_filter"
            elif filter == 'Прошло':
                translate_filter = 'passed_event_filter'
            keyboard.add(InlineKeyboardButton(text=filter, callback_data=translate_filter))
    keyboard.add(InlineKeyboardButton(text="Показать мероприятие", callback_data="view_event"))
    return keyboard.adjust(2).as_markup()

async def view_profile(count: int, other_filter: str) -> InlineKeyboardMarkup:
    from app.heandlers import view_profile_filters
    keyboard = InlineKeyboardBuilder()
    translate_filter = ""
    if count > 10:
        keyboard.row(InlineKeyboardButton(text="<--", callback_data="<--:worker"), InlineKeyboardButton(text="-->", callback_data="-->:worker"))
    for filter in view_profile_filters:
        if other_filter == filter:
            keyboard.add(InlineKeyboardButton(text="Все", callback_data="all"))
        else:
            if filter == 'Начинающий':
                translate_filter = "beginning"
            elif filter == 'Маршал':
                translate_filter = "marshal"
            elif filter == 'Основной состав':
                translate_filter ="main_cast"
            keyboard.add(InlineKeyboardButton(text=filter, callback_data=f"{translate_filter}"))
    keyboard.add(InlineKeyboardButton(text="Показать анкету", callback_data="view_profile"))
    return keyboard.adjust(2).as_markup()    

async def sub_or_unSub_button(chat_id, count_event = 1, offset = 0) -> InlineKeyboardMarkup:
    from app.heandlers import count_event_subscribes, day_count
    from app.DataBase.models import Event
    data: Event = await db.get_event(offset)
    keyboard = InlineKeyboardBuilder()
    if count_event > 1:
        keyboard.add(InlineKeyboardButton(text="<--", callback_data="<--:view_event_planing"))
        keyboard.add(InlineKeyboardButton(text="-->", callback_data="-->:view_event_planing"))
    if data.method_of_work == "Вахта":
        if data.count_people != len(count_event_subscribes[f'{data.date}-{data.count_days}']) and (chat_id in count_event_subscribes[f'{data.date}-{data.count_days}']) == False:
            keyboard.add(InlineKeyboardButton(text="Подписатся", callback_data="tour:subscribe"))
        elif chat_id in count_event_subscribes[f'{data.date}-{data.count_days}']:
            keyboard.add(InlineKeyboardButton(text="Отписатся", callback_data="tour:unsubscribe"))
    else:
        for number_day in range(0, len(day_count[data.date])):
            if data.count_people != len(count_event_subscribes[f'{data.date}-{number_day + 1}']) and (chat_id in count_event_subscribes[f'{data.date}-{number_day + 1}']) == False:
                keyboard.add(InlineKeyboardButton(text=f"Подписаться {day_count[data.date][number_day]}!", callback_data=f"{number_day + 1}:subscribe"))
            elif chat_id in count_event_subscribes[f'{data.date}-{number_day + 1}']:
                keyboard.add(InlineKeyboardButton(text=f"Отписаться {day_count[data.date][number_day]}!", callback_data=f"{number_day + 1}:unsubscribe"))
    
    return keyboard.adjust(2).as_markup()