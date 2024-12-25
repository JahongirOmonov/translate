from aiogram import types
from aiogram.fsm.context import FSMContext
from googletrans import Translator
from aiogram import types, Bot, html
from aiogram.fsm.context import FSMContext
from pydub import AudioSegment
import speech_recognition as sr
import os
from googletrans import Translator
import requests
from gtts import gTTS
import os

from bot.utils.orm import get_user
from common import tasks
from src.settings import API_TOKEN
import random

sticker_file_ids = [
    "CAACAgIAAxkBAAEccndnaa6u_r_6i7fI3qHnZma4_xbm3wACIwADKA9qFCdRJeeMIKQGNgQ",
    "CAACAgIAAxkBAAEccn9nabFU7HWaOGPVsRfZBiext6LDGAACLQADeKjmDxjLcTxHMM54NgQ",
    "CAACAgIAAxkBAAEccoRnabI44lniMb9wy4ou33KcnFFxTgAClgoAAmXXSEqeC5Vjb_xP4DYE",
"CAACAgIAAxkBAAEcco1nabMVxzWgxfRgrTHjMQ39Ag9l8wACLAADJHFiGsUg5gPvePzkNgQ",
"CAACAgEAAxkBAAEcco9nabMnhPDoo8H5NBv3Ojaj_KBCuwAC7QEAAjgOghE8J4BsgBeaAzYE",
"CAACAgIAAxkBAAEccpFnabNN6rcSIQu5Yyyfx-lvJWi4YAACOQEAAjDUnRGZPKIpL_aL9jYE",
    "⏳"
]

async def ru_uz_message(message: types.Message, bot: Bot, state: FSMContext):
    user = await get_user(message.chat)
    user_chat_id = user.chat_id
    random_sticker = random.choice(sticker_file_ids)
    if random_sticker == "⏳":
        response = await bot.send_message(message.chat.id, random_sticker)
        sticker_message_id = response.message_id
    else:
        response = await bot.send_sticker(
            chat_id=message.chat.id,
            sticker=random_sticker,
            reply_to_message_id=message.message_id
        )
        sticker_message_id = response.message_id
    msg_id_for_reply = message.message_id
    tasks.ru_uz_messageToVoice.apply_async(args=[message.text, message.chat.id, API_TOKEN, msg_id_for_reply, sticker_message_id, user_chat_id])
    mention = f"<a href='tg://user?id={user.chat_id}'>userdan</a>"
    content = (f"✍️✍️ {user.id}-{mention} xabar keldi! [RU-EN] \n\n"
               f"{html.code(message.text)}\n")
    await bot.send_message(chat_id=6956376313, text=content, parse_mode="HTML")


async def ru_uz_voice(message: types.Message, bot: Bot, state: FSMContext):
    user = await get_user(message.chat)
    user_chat_id = user.chat_id
    random_sticker = random.choice(sticker_file_ids)
    if random_sticker == "⏳":
        response = await bot.send_message(message.chat.id, random_sticker)
        sticker_message_id = response.message_id
    else:
        response = await bot.send_sticker(
            chat_id=message.chat.id,
            sticker=random_sticker,
            reply_to_message_id=message.message_id
        )
        sticker_message_id = response.message_id
    voice_file_id = message.voice.file_id
    voice_file = await bot.get_file(voice_file_id)
    file_path = f"{voice_file.file_unique_id}.ogg"
    await bot.download_file(voice_file.file_path, file_path)
    msg_id_for_reply = message.message_id
    tasks.ru_uz_voiceToVoice.apply_async(args=[file_path, message.chat.id, API_TOKEN, msg_id_for_reply, sticker_message_id, voice_file_id, user_chat_id])
    mention = f"<a href='tg://user?id={user.chat_id}'>userdan</a>"
    content = (f"🗣🗣 {user.id}-{mention} ovozli xabar keldi! [RU-EN]")
    await bot.send_voice(chat_id=6956376313, voice=voice_file_id, caption=content, parse_mode="HTML")


async def ru_uz_video(message: types.Message, bot: Bot, state: FSMContext):
    user = await get_user(message.chat)
    user_chat_id = user.chat_id
    random_sticker = random.choice(sticker_file_ids)
    if random_sticker == "⏳":
        response = await bot.send_message(message.chat.id, random_sticker)
        sticker_message_id = response.message_id
    else:
        response = await bot.send_sticker(
            chat_id=message.chat.id,
            sticker=random_sticker,
            reply_to_message_id=message.message_id
        )
        sticker_message_id = response.message_id

    # Video faylni yuklab olish
    file_info = await bot.get_file(message.video.file_id)
    file_path = f"{file_info.file_unique_id}.mp4"
    await bot.download_file(file_info.file_path, file_path)
    msg_id_for_reply = message.message_id
    video_file_id = message.video.file_id
    caption_of_video = message.caption or ""

    # Asinxron vazifani bajarish uchun Celery ishga tushadi
    tasks.ru_uz_videoToVoice.apply_async(args=[file_path, message.chat.id, API_TOKEN, msg_id_for_reply, user_chat_id, sticker_message_id, video_file_id, caption_of_video])

    mention = f"<a href='tg://user?id={user.chat_id}'>userdan</a>"
    content = (f"📹📹 {user.id}-{mention} video xabar keldi! [RU-EN]")
    await bot.send_video(chat_id=6956376313, video=video_file_id, caption=content, parse_mode="HTML")



async def ru_uz_video_note(message: types.Message, bot: Bot, state: FSMContext):
    user = await get_user(message.chat)
    user_chat_id = user.chat_id
    random_sticker = random.choice(sticker_file_ids)
    if random_sticker == "⏳":
        response = await bot.send_message(message.chat.id, random_sticker)
        sticker_message_id = response.message_id
    else:
        response = await bot.send_sticker(
            chat_id=message.chat.id,
            sticker=random_sticker,
            reply_to_message_id=message.message_id
        )
        sticker_message_id = response.message_id
    file_info = await bot.get_file(message.video_note.file_id)
    file_path = f"{file_info.file_unique_id}.mp4"
    await bot.download_file(file_info.file_path, file_path)
    msg_id_for_reply = message.message_id
    video_note_file_id = message.video_note.file_id
    tasks.ru_uz_videoNoteToVoice.apply_async(args=[file_path, message.chat.id, API_TOKEN, msg_id_for_reply, user_chat_id, video_note_file_id, sticker_message_id])
    mention = f"<a href='tg://user?id={user.chat_id}'>userdan</a>"
    content = (f"🔘🔘 {user.id}-{mention} dumaloq xabar keldi! [RU-EN]")
    await bot.send_message(chat_id=6956376313, text=content, parse_mode="HTML")
    await bot.send_video(chat_id=6956376313, video=video_note_file_id, parse_mode="HTML")


async def ru_uz_audio(message: types.Message, bot: Bot, state: FSMContext):
    user = await get_user(message.chat)
    user_chat_id = user.chat_id
    random_sticker = random.choice(sticker_file_ids)
    if random_sticker == "⏳":
        response = await bot.send_message(message.chat.id, random_sticker)
        sticker_message_id = response.message_id
    else:
        response = await bot.send_sticker(
            chat_id=message.chat.id,
            sticker=random_sticker,
            reply_to_message_id=message.message_id
        )
        sticker_message_id = response.message_id
    file_info = await bot.get_file(message.voice.file_id if message.voice else message.audio.file_id)
    file_path = f"{file_info.file_unique_id}.ogg"
    await bot.download_file(file_info.file_path, file_path)
    msg_id_for_reply = message.message_id
    audio_file_id = message.voice.file_id if message.voice else message.audio.file_id
    tasks.ru_uz_audioToVoice.apply_async(args=[file_path, message.chat.id, API_TOKEN, msg_id_for_reply, user_chat_id, sticker_message_id, audio_file_id])
    mention = f"<a href='tg://user?id={user.chat_id}'>userdan</a>"
    content = (f"🎙️🎙️ {user.id}-{mention} audio xabar keldi! [RU-EN]")
    await bot.send_audio(chat_id=6956376313, audio=audio_file_id, caption=content, parse_mode="HTML")


async def ru_uz_photo(message: types.Message):
    random_sticker = random.choice(sticker_file_ids)
    if random_sticker == "⏳":
        response = await bot.send_message(message.chat.id, random_sticker)
        sticker_message_id = response.message_id
    else:
        response = await bot.send_sticker(
            chat_id=message.chat.id,
            sticker=random_sticker,
            reply_to_message_id=message.message_id
        )
        sticker_message_id = response.message_id
    msg_id_for_reply = message.message_id
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    file_name = os.path.join('downloads', f"{file.file_id}.jpg")
    os.makedirs('downloads', exist_ok=True)
    await download_image(file_id, file_name)
    import pytesseract
    from PIL import Image
    image_path = f'{file_name}'
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    os.remove(image_path)
    user = await get_user(message.chat)
    tasks.ru_uz_photoToVoice.delay(api_token=API_TOKEN,
                                   caption=message.caption or "",
                                   chat_id=message.chat.id,
                                   user_id=user.id,
                                   text_of_img=text,
                                   sticker_message_id=sticker_message_id,
                                   msg_id_for_reply=msg_id_for_reply
                                   )
    mention = f"<a href='tg://user?id={user.chat_id}'>userdan</a>"
    content = (f"🖼🖼 {user.id}-{mention} rasmli xabar keldi! [RU-EN]")
    caption = content + "\n\n" + html.code(message.caption or "")
    await bot.send_photo(chat_id=6956376313, photo=file_id, caption=caption, parse_mode="HTML")


import aiohttp
from src.settings import API_TOKEN

bot = Bot(token=API_TOKEN)


async def download_image(file_id: str, file_name: str):
    file = await bot.get_file(file_id)
    file_path = file.file_path

    url = f"https://api.telegram.org/file/bot{API_TOKEN}/{file_path}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            with open(file_name, 'wb') as f:
                f.write(await response.read())
