from aiogram import BaseMiddleware
from typing import Callable, Awaitable, Dict, Any
from aiogram.types import Message, TelegramObject
from aiogram.fsm.context import FSMContext
import app.DataBase.requests as db

class IsUserMiddleware(BaseMiddleware):
    async def __call__(self, 
                        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                        event: Message,
                        data: Dict[str, Any]) -> Any:
        state = FSMContext(storage=data['state'].storage, key=data['state'].key)
        curent_state = await state.get_state()
        if await db.is_user(event.chat.id) or event.text == '/start' or curent_state is not None:
            return await handler(event, data)
        else:
            await event.answer("Вас нет в списках.")