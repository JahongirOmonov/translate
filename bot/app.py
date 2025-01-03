import asyncio
import orjson

from django.conf import settings

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from bot.middlewares import BanMiddleware, RequiredChannelsMiddleware

from bot import handlers
from bot.middlewares.main import RequiredChannelsMiddleware


def setup_handlers(dp: Dispatcher) -> None:
    dp.include_router(handlers.admin.prepare_router())
    dp.include_router(handlers.users.prepare_router())


def setup_middlewares(dp: Dispatcher) -> None:
    dp.update.middleware(RequiredChannelsMiddleware())
    dp.update.middleware(BanMiddleware())


async def setup_aiogram(dp: Dispatcher) -> None:
    setup_handlers(dp)
    setup_middlewares(dp)

async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish")
       #   BotCommand(command="sms", description="Adminga xabar yuborish"),
    ]
    await bot.set_my_commands(commands)


async def aiogram_on_startup_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    await set_bot_commands(bot)
    await setup_aiogram(dispatcher)
    await bot.delete_webhook(drop_pending_updates=True)


async def aiogram_on_shutdown_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    await bot.session.close()
    await dispatcher.storage.close()


def main() -> None:
    session = AiohttpSession(
        json_loads=orjson.loads,
    )

    bot = Bot(
        token=settings.API_TOKEN,
        session=session,
        # default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    storage = MemoryStorage()

    dp = Dispatcher(
        storage=storage,
    )
    dp.startup.register(aiogram_on_startup_polling)
    dp.shutdown.register(aiogram_on_shutdown_polling)
    asyncio.run(dp.start_polling(bot))

