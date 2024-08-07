import asyncio
from aiogram import Dispatcher, Bot
from app.start import rout as rout_start
from app.heandlers import rout as rout_handler
from app.CreateEvents import rout as rout_create_event
from app.callback.callback_event import rout as rout_callback_event
from app.resetProfile import rout as rout_reset_profile
from app.DataBase.models import async_main
from app.Middelware.middelware import IsUserMiddleware
import config

async def main() -> None:
    await async_main()
    bot = Bot(token=config.TOKEN)
    dp = Dispatcher()
    await connect_routers(dp)
    await register_middleware(dp)
    await dp.start_polling(bot)

async def connect_routers(dp: Dispatcher) -> None:
    dp.include_router(rout_start)
    dp.include_router(rout_handler)
    dp.include_router(rout_create_event)
    dp.include_router(rout_callback_event)
    dp.include_router(rout_reset_profile)

async def register_middleware(dp: Dispatcher) -> None:
    dp.message.middleware.register(IsUserMiddleware())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен.")
