from aiogram import types
from aiogram.types import Chat, User
from utils.choices import Role
from common.models import TelegramProfile, Archive, RequiredChannels


async def get_user(chat: Chat | User):
    user = TelegramProfile.objects.filter(chat_id=chat.id)
    username = chat.username if chat.username else None
    last_name = chat.last_name if chat.last_name else None
    if not user.exists():
        prepared_user = TelegramProfile.objects.create(
            chat_id=chat.id,
            username=username,
            first_name=chat.first_name,
            last_name=last_name
        )
        return prepared_user
    return user.first()

async def check_admin(chat_id: int):
    return TelegramProfile.objects.filter(chat_id=chat_id, role__in=[Role.ADMIN]).exists()

async def save_archive(message: types.Message):
    user = await get_user(message.chat)
    archive = Archive.objects.create(title=message.chat.title, author=user)
    return archive

async def get_channels():
    return RequiredChannels.objects.all()




