from aiogram.filters import Filter
from aiogram.types import Message

from bot.utils.orm import check_admin

class AdminFilter(Filter):
    def __init__(self,):
        pass

    async def __call__(self, message: Message):
        return await check_admin(message.chat.id)