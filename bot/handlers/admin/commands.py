from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.states.main import Messages, MessageStates, InfoUser, ArchiveState
from common.models import TelegramProfile, BannedUser
from aiogram import Bot
import asyncio
import common.tasks
from django.utils.timezone import localtime
import requests
from src.settings import API_TOKEN


#/messages
async def messages_for_users(message: MessageStates, state: FSMContext):
    await message.answer("Barcha foydalanuvchilar uchun xabarni kiriting: ")
    await state.set_state(Messages.messages_for_user)

#/messages
async def received_messages(message: MessageStates, state: FSMContext, bot: Bot):
    await state.update_data(msg_of_admin=message.text)
    data = await state.get_data()
    users = TelegramProfile.objects.all().order_by('id')

    undelivered_users = "Xabar yetib bormagan foydalanuvchilar:\n\n"
    admins_message = (f"👮‍♂️<b>Admin:</b>\n\n"
                      f"<i>{data.get('msg_of_admin')}</i>")
    for user in users:
        try:
            if user.chat_id:
                await bot.send_message(chat_id=user.chat_id, text=admins_message, parse_mode="HTML")
                await asyncio.sleep(1)
        except:
            # mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
            mytext = f"ID: {user.id}, NAME: {user.first_name}, username: @{user.username}\n"
            undelivered_users += mytext
    max_length = 4096
    for i in range(0, len(undelivered_users), max_length):
        chunk = undelivered_users[i:i + max_length]
        # await bot.send_message(chat_id=6956376313, text=chunk)
        url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
        payload = {"chat_id": 6956376313, "text": chunk}
        requests.post(url, json=payload)
    await state.clear()
    # await bot.send_message(chat_id=6956376313, text=undelivered_users)

    await message.answer("Xabar foydalanuvchilarga muvaffaqiyatli yuborildi✅")
    await state.clear()


#/message
async def message_for_user(message: Message, state: FSMContext):
    await message.answer("Foydalanuvchi ID raqamini kiriting: ")
    await state.set_state(MessageStates.id_of_user)

#/message
async def message_received(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(id_of_user=message.text)
    await message.answer("Xabarni kiriting: ")
    await state.set_state(MessageStates.message_for_user)

#/message
async def message_result(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(msg_for_user=message.text)
    data = await state.get_data()
    user = TelegramProfile.objects.filter(id=data.get('id_of_user')).first()
    admins_message = (f"👮‍♂️<b>Admin:</b>\n\n"
                      f"<i>{data.get('msg_for_user')}</i>")
    secret = (f"🔒<b>Secret:</b>\n\n"
              f"Admin: <a href='tg://user?id={message.chat.id}'>{message.from_user.first_name}</a>\n"
              f"ID: {user.id}, <a href='tg://user?id={user.chat_id}'>{user.first_name}</a> ga xabar yozdi:\n\n"
              f"<i>{data.get('msg_for_user')}</i>")
    try:
        await bot.send_message(chat_id=user.chat_id, text=admins_message, parse_mode="HTML")
        if message.chat.id != 6956376313:
            await bot.send_message(chat_id=6956376313, text=secret, parse_mode="HTML")
        await message.answer("Xabar muvaffaqiyatli yuborildi✅")
    except:
        await message.answer("Xabar yetib bormadi❌")
    await state.clear()


#/user
async def info(message: MessageStates, bot: Bot, state: FSMContext):
    await message.answer("Foydalanuvchi ID raqamini kiriting: ")
    await state.set_state(InfoUser.id_of_user)

#/user
async def get_archive(message: MessageStates, bot: Bot, state: FSMContext):
    await message.answer("Foydalanuvchi ID raqamini kiriting: ")
    await state.set_state(ArchiveState.id_of_user)



#/users
async def users(message: MessageStates, bot: Bot):
    common.tasks.send_user_list.delay(bot.token, admin_chat_id=message.chat.id)
    await message.answer("Foydalanuvchilar ro'yxatini yuborildi✅")

#/user
async def info_continue(message: MessageStates, bot: Bot, state: FSMContext):
    await state.update_data(id_of_user=message.text)
    data = await state.get_data()
    user = TelegramProfile.objects.filter(id=data.get('id_of_user')).first()
    if user:
        local_time = localtime(user.created_at)
        if user.first_name and user.chat_id:
            mention = f'<a href="tg://user?id={user.chat_id}">{user.first_name}</a>'
        else:
            mention = "Ismi mavjud emas"
        text = (f"Foydalanuvchi haqida ma`lumot ⬇️\n\n"
                f"ID: {user.id}\n"
                f"Nick: {mention}\n"
                f"Username: @{user.username}\n"
                f"Chat_id: {user.chat_id}\n"
                f"Role: {user.role}\n"
                f"Joined: {local_time.strftime('%d.%m.%Y %H:%M')}\n"
                f"Havola: tg://user?id={user.chat_id}\n")
        try:
            profile_photos =await bot.get_user_profile_photos(user_id=user.chat_id, limit=1)
            if profile_photos.total_count > 0:
                photo = profile_photos.photos[0][-1].file_id
                await bot.send_photo(chat_id=message.chat.id, photo=photo, caption=text, parse_mode=ParseMode.HTML)
            else:
                await message.answer(text, parse_mode="HTML")
        except:
            await message.answer(text, parse_mode="HTML")

    else:
        await message.answer("Bunday foydalanuvchi mavjud emas❌")
    await state.clear()


#/archive
async def archive_result(message: MessageStates, bot: Bot, state: FSMContext):
    await state.update_data(id_of_user=message.text)
    data = await state.get_data()
    common.tasks.send_archive_sync.delay(id=data.get('id_of_user'), chat_id=message.chat.id)
    await state.clear()
    await message.answer("Arxivlar yuborilmoqda. Iltimos, kuting...")


from datetime import timedelta, datetime
from django.utils.timezone import make_aware
from aiogram.types import Message
from common.models import TelegramProfile, BannedUser

async def ban_user(message: Message, bot: Bot):
    try:
        # /ban <telegram_id> <ban_time_in_hours> <reason>
        args = message.text.split(maxsplit=3)

        # Parametrlarni olish
        id = int(args[1])
        ban_time = int(args[2])  # Ban vaqti (soatda)
        reason = args[3]

        # Profilni topamiz
        profile = TelegramProfile.objects.filter(id=id).first()
        if not profile:
            await message.reply(f"Foydalanuvchi topilmadi: {id}")
            return

        # Ban muddati va hozirgi vaqtni hisoblash
        now = make_aware(datetime.now())
        banned_until = now + timedelta(minutes=ban_time)

        # Foydalanuvchini ban qilish
        ban, created = BannedUser.objects.update_or_create(
            telegram_profile=profile,
            defaults={
                "reason": reason,
                "banned_until": banned_until,
                "banned_at": now
            }
        )

        if created:
            await message.reply(
                f"Foydalanuvchi @{profile.username or profile.first_name} ban qilindi.\n"
                f"Sabab: {reason}\n"
                f"Ban muddati: {banned_until.strftime('%Y-%m-%d %H:%M')}"
            )
            await bot.send_message(chat_id=profile.chat_id,
                                   text=f"Siz ban qilindingiz!\nSabab: {reason}\nBan muddati: {banned_until.strftime('%Y-%m-%d %H:%M')}\n\n"
                                        f"Adminga shikoyatingizni \"/xabar text\" ko'rinishida qoldirishingiz mumkin!")

        else:
            await message.reply(
                f"Foydalanuvchi @{profile.username or profile.first_name} uchun ban yangilandi.\n"
                f"Yangi sabab: {reason}\n"
                f"Yangi ban muddati: {banned_until.strftime('%Y-%m-%d %H:%M')}"
            )
            await bot.send_message(chat_id=profile.chat_id, text=f"Sizning ban yangilandi.\nSabab: {reason}\nBan muddati: {banned_until.strftime('%Y-%m-%d %H:%M')}\n\n"
                                                                 f"Adminga shikoyatingizni \"/xabar text\" ko'rinishida qoldirishingiz mumkin!")

    except IndexError:
        await message.reply("Foydalanish: /ban <user_id> <ban_time_in_minutes> <reason>")
    except ValueError:
        await message.reply("Noto'g'ri ma'lumot kiritildi. ID va vaqt son bo'lishi kerak.")
    except Exception as e:
        await message.reply(f"Xato yuz berdi: {str(e)}")


        await message.reply(f"Foydalanuvchi @{profile.first_name or profile.username} {ban_time} minutga ban qilindi.\nSabab: {reason}")
    except (IndexError, ValueError):
        await message.reply("Noto'g'ri format. To'g'ri format:\n/ban <telegram_id> <minut> <sababi>")


# /unban
from aiogram.types import Message
from common.models import TelegramProfile, BannedUser

async def unban_user(message: Message, bot: Bot):
    try:
        # /unban <telegram_id>
        args = message.text.split(maxsplit=1)

        # Parametrlarni olish
        id = int(args[1])

        # Profilni topamiz
        profile = TelegramProfile.objects.filter(id=id).first()
        if not profile:
            await message.reply(f"Foydalanuvchi topilmadi: {id}")
            return

        # Foydalanuvchini ban ro'yxatidan olib tashlash
        banned_user = BannedUser.objects.filter(telegram_profile=profile).first()
        if not banned_user:
            await message.reply(f"Foydalanuvchi @{profile.username or profile.first_name} ban ro'yxatida emas.")
            return

        banned_user.delete()

        await message.reply(f"Foydalanuvchi @{profile.username or profile.first_name} ban ro'yxatidan chiqarildi.")
        await bot.send_message(chat_id=profile.chat_id, text="Sizning ban olib tashlandi. Endi botdan foydalanishingiz mumkin.")

    except IndexError:
        await message.reply("Foydalanish: /unban <user_id>")
    except ValueError:
        await message.reply("Noto'g'ri ma'lumot kiritildi. ID son bo'lishi kerak.")
    except Exception as e:
        await message.reply(f"Xato yuz berdi: {str(e)}")


# /banners - ban userlar
from datetime import datetime
from aiogram import Bot
from aiogram.types import Message


async def show_banned_users(message: Message, bot: Bot):
    # Get current time
    current_time = datetime.now()

    # Query to filter banned users where 'banned_until' is in the future
    banned_users = BannedUser.objects.all()
    count = 0
    text = "Ban foydalanuvchilar⬇️\n\n"

    for banned_user in banned_users:
        # Fetch associated Telegram profile
        profile = banned_user.telegram_profile
        local_time = localtime(banned_user.banned_until)
        text += f"ID: {profile.id}  |  Full Name: {profile.first_name or ''}  |  Username: @{profile.username} | Banned Until: {local_time.strftime('%d/%m/%Y, %H:%M')}, Reason: {banned_user.reason}\n\n"
        count += 1

    text += (
        f"\n===============================\n"
        f"Ayni vaqtdagi ban foydalanuvchilar soni: {count} ta\n"
        f"Matn uzunligi: {len(text)} belgidan iborat"
    )

    max_length = 4096  # Telegram message character limit
    for i in range(0, len(text), max_length):
        chunk = text[i:i + max_length]
        await bot.send_message(chat_id=6956376313, text=chunk)














