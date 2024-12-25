from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.enums import ChatMemberStatus
from aiogram.types import Update, Message
from datetime import datetime
from django.utils.timezone import make_aware, localtime

from bot.keyboards import inline
from bot.utils.orm import get_channels
from common.models import BannedUser, TelegramProfile, RequiredChannels  # Replace with your actual model import


class BanMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()

    async def __call__(self, handler, event: Update, data):
        if hasattr(event, 'message') and isinstance(event.message, Message):
            message = event.message
            telegram_id = message.from_user.id
            now = make_aware(datetime.now())

            # Agar xabar /xabar bilan boshlasa, ban tekshiruvidan o'tmasin
            if message and message.text and message.text.startswith("/xabar"):
                return await handler(event, data)  # Skip ban check for /xabar messages

            # Check if TelegramProfile exists
            profile = TelegramProfile.objects.filter(chat_id=telegram_id).first()
            if not profile:
                return await handler(event, data)  # No profile, proceed to the next handler

            # Check if the user is banned
            banned_user = BannedUser.objects.filter(telegram_profile=profile).first()

            if banned_user:
                local_time = localtime(banned_user.banned_until)
                if banned_user.banned_until >= now:
                    # User is still banned
                    await message.answer(
                        f"Siz ban qilindingiz. Sabab: {banned_user.reason}\n"
                        f"Ban muddati: {local_time.strftime('%Y-%m-%d %H:%M')}\n\n"
                        f"Adminga shikoyatingizni \"/xabar text\" ko'rinishida qoldirishingiz mumkin!"
                    )
                    return  # Stop further processing
                else:
                    await message.answer(f"Sizning ban muddatingiz o'z nihoyasiga yetdi.\n"
                                         f"Endi bemalol botdan foydalanishingiz mumkin😊")
                    # Ban has expired, remove the ban
                    banned_user.delete()

        # Continue to the next handler
        return await handler(event, data)

from aiogram import BaseMiddleware
from aiogram.types import Message


class RequiredChannelsMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.noneSubscribed = []



    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        message = event.message
        is_member=True
        self.noneSubscribed.clear()
        channels = await get_channels()
        for channel in channels:
            try:
                # Kanalga obuna bo'lish holatini tekshirish
                member = await event.bot.get_chat_member(chat_id=channel.chat_id, user_id=message.chat.id)
                if member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
                    is_member = False
                    self.noneSubscribed.append(channel)
            except Exception as e:
                print(f"Error checking membership for channel {channel.username}: {e}")
                continue

        if self.noneSubscribed:
            await message.answer("🚫 Siz kanalga obuna bo'lmagansiz! 🚫", reply_markup=await inline.get_subscribed_channels_markup(self.noneSubscribed))
            return
        return await handler(event, data)








