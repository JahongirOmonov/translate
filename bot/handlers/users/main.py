from aiogram import types, Bot
from datetime import date, datetime
import os
from bot.keyboards.inline import language_markup
from bot.keyboards.outline import switch_language
# from common.tasks import send_echo_celery
from utils.choices import Role
from aiogram.fsm.context import FSMContext
from bot.states.main import SmsForAdmin, TranslationStates
from bot.utils.orm import get_user, get_channels
from common.models import TelegramProfile
from pydub import AudioSegment
import speech_recognition as sr
import common.tasks
from googletrans import Translator
from gtts import gTTS
from aiogram.types import InputFile
import requests


async def start(message: types.Message, bot: Bot):
    user = await get_user(message.chat)
    current_date = date.today()

    current_time = datetime.now().strftime("%H:%M:%S")

    mention = f"<a href='tg://user?id={user.chat_id}'>{user.first_name}</a>"
    notification = (f"Diqqat!!!   ID: {user.id}  \n\n"
                    f"{mention} ro'yhatdan o'tdi✅ \n\n"
                    f"Sana: {current_date}  |  {current_time}")
    matn=f"Assalomu alaykum {mention} \nBotga xush kelibsiz!\n"
    await message.answer(matn, reply_markup=await switch_language(), parse_mode="HTML")

    text = (f"<b>Tilni tanlang!\n"
            f"Choose a language!\n"
            f"Выберите язык!\n</b>")

    await message.answer(text, reply_to_message_id=message.message_id, reply_markup=await language_markup(), parse_mode="HTML")
    admin_users = TelegramProfile.objects.filter(role=Role.ADMIN)
    for admin in admin_users:
        try:
            if admin.chat_id:
                await bot.send_message(chat_id=admin.chat_id, text=notification, parse_mode="HTML")
        except:
            pass
    # await bot.send_message(6956376313, notification)


# async def get_video_file_id(message: types.Message, bot: Bot):
#     await message.answer(message.video.file_id)
from bot.states.main import TranslationStates

# /sms(for admin)
async def sms_for_admin(message: types.Message, bot: Bot, state: FSMContext):
    await message.delete()
    state_data = await state.get_state()
    if state_data in ["TranslationStates:uz_en", "TranslationStates:uz_ru"]:
        await message.answer("Adminga xabar yuborish uchun matnni kiriting: ")
        await state.update_data(lan="uz")
    elif state_data in ["TranslationStates:en_uz", "TranslationStates:en_ru"]:
        await message.answer("Enter the text to send to the admin: ")
        await state.update_data(lan="en")
    elif state_data in ["TranslationStates:ru_uz", "TranslationStates:ru_en"]:
        await message.answer("Введите текст для отправки администратору:")
        await state.update_data(lan="ru")
    else:
        await message.answer("Adminga xabar yuborish uchun matnni kiriting: ")
        await state.update_data(lan="uz")
    await state.set_state(SmsForAdmin.sms)


# /sms(for admin)
async def sms_received(message: types.Message, state: FSMContext, bot: Bot):
    if message.text.startswith("/"):
        await message.answer("Siz hozir statening ichidasiz ")
        return
    await state.update_data(sms=message.text)
    data = await state.get_data()
    user = TelegramProfile.objects.filter(chat_id=message.from_user.id).first()
    admin_users = TelegramProfile.objects.filter(role=Role.ADMIN)

    # Adminlarga xabar yuborish
    for admin in admin_users:
        try:
            # Har bir admin foydalanuvchining chat_id sini olish va unga xabar yuborish
            if admin.chat_id:
                text = (f"ID: {user.id}\n"
                        f"Nick: <a href='tg://user?id={user.chat_id}'>{user.first_name}</a>\n"
                        f"Username: @{user.username}\n\n"
                        f"===message===\n"
                        f"{data.get('sms')}")
                # Adminga xabar yuborish
                await bot.send_message(chat_id=admin.chat_id, text=text, parse_mode="HTML")
        except Exception as e:
            print(f"Xatolik yuz berdi: {e}")
    data = await state.get_data()
    if data.get('lan') =='uz':
        await message.answer("Xabar muvaffaqiyatli yuborildi✅. Iltimos, admin javobini kuting...")
    elif data.get('lan') =='en':
        await message.answer("Message sent successfully✅. Please wait for the admin's response...")
    elif data.get('lan') =='ru':
        await message.answer("Сообщение успешно отправлено✅. Пожалуйста, подождите ответ администратора...")
    else:
        await message.answer("Xabar muvaffaqiyatli yuborildi✅. Iltimos, admin javobini kuting...")
    await state.clear()


    # print(f"Image saved as {file_name}")


async def echo_video(message: types.Message):
    file_id = message.video.file_id
    caption = message.caption or ""
    user = await get_user(message.chat)
    common.tasks.send_echo_video.delay(file_id=file_id,
                                       caption=caption,
                                       chat_id=message.chat.id,
                                       message_id=message.message_id,
                                       user_id=user.id,
                                       first_name=message.from_user.first_name,
                                       username=message.from_user.username
                                       )


async def echo(message: types.Message):
    await message.answer(f"Hurmatli {message.from_user.first_name}!\nIltimos quyidagi menudan birini tanlang! ", reply_to_message_id=message.message_id, reply_markup=await language_markup())


# async def callback_uz_en(callback: types.CallbackQuery, state: FSMContext):
#     await callback.message.edit_text(text="Text ingliz tilga tarjima qilinadi✅\nTextni kiriting!")
#     await state.set_state(TranslationStates.uz_en)
#     await callback.answer()
#
#
# async def translate_uz_en(message: types.Message, state: FSMContext):
#     translator = Translator()
#     translated_text = translator.translate(message.text, src='uz', dest='en').text
#     await message.answer(f"Tarjima (UZ ➡️ EN):\n{translated_text}")


from aiogram import types
from aiogram.fsm.context import FSMContext
from pydub import AudioSegment
import speech_recognition as sr
import os
from googletrans import Translator

import requests
from gtts import gTTS
import os


async def translate_voice_to_text(message: types.Message, state: FSMContext):
    print("Processing voice message...")

    # Fetch the file info from Telegram
    voice_file_id = message.voice.file_id
    voice_file = await bot.get_file(voice_file_id)

    # Download the file
    file_path = f"{voice_file.file_unique_id}.ogg"
    await bot.download_file(voice_file.file_path, file_path)

    # Convert OGG file to WAV format
    audio = AudioSegment.from_file(file_path)
    wav_path = f"{voice_file.file_unique_id}.wav"
    audio.export(wav_path, format="wav")

    # Convert voice to text
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language="uz-UZ")
        except sr.UnknownValueError:
            await message.answer("Ovozli xabarni tushunib bo‘lmadi. Iltimos, qayta yuboring.")
            # Cleanup temporary files
            os.remove(file_path)
            os.remove(wav_path)
            return

    # Translate text
    translator = Translator()
    translated_text = translator.translate(text, src="uz", dest="en").text
    await message.answer(f"Original: {text}\nTarjima (UZ ➡️ EN): {translated_text}")

    # Ovozli faylni yaratish
    tts = gTTS(translated_text, lang="en")

    # Faylni saqlash
    myfile = "voice_message.mp3"
    tts.save(myfile)

    # Send the audio file to Telegram
    with open(myfile, 'rb') as audio_file:
        url = f"https://api.telegram.org/bot{API_TOKEN}/sendVoice"
        payload = {
            "chat_id": message.chat.id
        }
        files = {
            "voice": audio_file
        }
        response = requests.post(url, data=payload, files=files)

        if response.status_code == 200:
            print("Audio sent successfully!")
        else:
            print(f"Failed to send audio: {response.status_code}")

    # Cleanup temporary files
    os.remove(file_path)
    os.remove(wav_path)
    os.remove(myfile)

    # Clear state
    # await state.clear()


async def handle_video_message(message: types.Message, state: FSMContext):
    """
    Video faylni qayta ishlash, ovozini tarjima qilish va ovozli tarjimani yuborish.
    """
    # Video faylni yuklab olish
    print("Processing video message...")
    file_info = await bot.get_file(message.video.file_id)
    file_path = f"{file_info.file_unique_id}.mp4"
    await bot.download_file(file_info.file_path, file_path)

    # Video faylning audio qismini ajratib olish va WAV formatiga aylantirish
    audio = AudioSegment.from_file(file_path)
    wav_path = f"{file_path}.wav"
    audio.export(wav_path, format="wav")

    # Audio ovozini matnga aylantirish
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language="uz-UZ")
        except sr.UnknownValueError:
            await message.answer("Xabarni tushunib bo‘lmadi. Iltimos, qayta yuboring.")
            return

    # Matnni tarjima qilish
    translator = Translator()
    translated_text = translator.translate(text, src="uz", dest="en").text
    await message.answer(f"Original: {text}\nTarjima (UZ ➡️ EN): {translated_text}")

    print(f"Tarjima natijasi: {translated_text}")

    tts = gTTS(translated_text, lang="en")

    # Faylni saqlash
    myfile = "voice_message.mp3"
    tts.save(myfile)

    # Send the audio file to Telegram
    with open(myfile, 'rb') as audio_file:
        url = f"https://api.telegram.org/bot{API_TOKEN}/sendAudio"
        payload = {
            "chat_id": message.chat.id
        }
        files = {
            "audio": audio_file
        }
        response = requests.post(url, data=payload, files=files)

        if response.status_code == 200:
            print("Audio sent successfully!")
        else:
            print(f"Failed to send audio: {response.status_code}")
        os.remove(file_path)
        os.remove(wav_path)
        os.remove(myfile)

async def handle_video_note_message(message: types.Message, state: FSMContext):
    """
    Video note faylni qayta ishlash, ovozini tarjima qilish va ovozli tarjimani yuborish.
    """
    # Video note faylni yuklab olish
    print("Processing video note message...")
    file_info = await bot.get_file(message.video_note.file_id)
    file_path = f"{file_info.file_unique_id}.mp4"
    await bot.download_file(file_info.file_path, file_path)

    # Video faylning audio qismini ajratib olish va WAV formatiga aylantirish
    audio = AudioSegment.from_file(file_path)
    wav_path = f"{file_path}.wav"
    audio.export(wav_path, format="wav")

    # Audio ovozini matnga aylantirish
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language="uz-UZ")
        except sr.UnknownValueError:
            await message.answer("Xabarni tushunib bo‘lmadi. Iltimos, qayta yuboring.")
            return

    # Matnni tarjima qilish
    translator = Translator()
    translated_text = translator.translate(text, src="uz", dest="en").text
    await message.answer(f"Original: {text}\nTarjima (UZ ➡️ EN): {translated_text}")

    print(f"Tarjima natijasi: {translated_text}")

    # Tarjima natijasini ovozli xabarga aylantirish
    tts = gTTS(translated_text, lang="en")

    # Faylni saqlash
    myfile = "voice_message.mp3"
    tts.save(myfile)

    # Telegram orqali audio faylni yuborish
    with open(myfile, 'rb') as audio_file:
        url = f"https://api.telegram.org/bot{API_TOKEN}/sendAudio"
        payload = {
            "chat_id": message.chat.id
        }
        files = {
            "audio": audio_file
        }
        response = requests.post(url, data=payload, files=files)

        if response.status_code == 200:
            print("Audio sent successfully!")
        else:
            print(f"Failed to send audio: {response.status_code}")

    # Vaqtinchalik fayllarni o‘chirish
    os.remove(file_path)
    os.remove(wav_path)
    os.remove(myfile)




from aiogram import types, Bot
from common.models import TelegramProfile, BannedUser
from datetime import datetime
from django.utils.timezone import make_aware
from utils.choices import Role


async def sms_for_banned_user(message: types.Message, state: FSMContext, bot: Bot):
    telegram_id = message.from_user.id
    text = message.text[7:].strip()  # "/sms " qismidan keyingi matnni olish

    # Foydalanuvchi ban qilinganmi?
    profile = TelegramProfile.objects.filter(chat_id=telegram_id).first()
    if not profile:
        await message.answer("Sizning profilingiz topilmadi.")
        return

    # banned_user = BannedUser.objects.filter(telegram_profile=profile).first()
    # if banned_user:
    #     now = make_aware(datetime.now())
    #     if banned_user.banned_until >= now:
    #         # Ban hali davom etmoqda
    #         local_time = banned_user.banned_until.strftime('%Y-%m-%d %H:%M')
    #         await message.answer(
    #             f"Siz ban qilindingiz. Sabab: {banned_user.reason}\n"
    #             f"Ban muddati: {local_time}\n"
    #             "Xabar yuborish imkoniyatingiz yo'q."
    #         )
    #         return

    # Xabarni adminlarga yuborish
    if text:
        user = TelegramProfile.objects.filter(chat_id=telegram_id).first()
        admin_users = TelegramProfile.objects.filter(role__in=[Role.ADMIN, Role.MODERATOR])

        # Adminlarga xabar yuborish
        for admin in admin_users:
            try:
                if admin.chat_id:
                    text_to_send = (
                        "🤕 Ban userdan keldi 🤕\n\n"
                        f"ID: {user.id}\n"
                        f"Nick: {user.first_name}\n"
                        f"Username: @{user.username}\n\n"
                        f"===message===\n"
                        f"{text}"
                    )
                    await bot.send_message(chat_id=admin.chat_id, text=text_to_send)
            except Exception as e:
                print(f"Xatolik yuz berdi: {e}")
        await message.answer("Xabar muvaffaqiyatli yuborildi✅. Iltimos, admin javobini kuting...")
    else:
        await message.answer("Unday emas! <b><i>/xabar [text kiriting]</i></b>.", parse_mode="HTML")

    # State ni tozalash
    await state.clear()


# test InlineKeyboardBuilder
# async def mytest_handler(message: types.Message):
#     await message.answer("qaleeeee", reply_markup=await test_inline_markup())
#
# async def callbaq(callback: types.CallbackQuery):
#     button = callback.data.split("_")[-1]
#     print(button)
#     await callback.message.answer(f"button = {button}")
#     await callback.answer()


async def confirm_callback(callback: types.CallbackQuery):
    kanallar = await get_channels()
    azo_bolmaganlar = []
    for kanal in kanallar:
        try:
            member = await bot.get_chat_member(chat_id=kanal.chat_id, user_id=callback.from_user.id)
            if member.status == "left" or member.status == "kicked":
                azo_bolmaganlar.append(kanal.title)
        except Exception as e:
            print(e)
    if azo_bolmaganlar:
        await callback.message.answer(
            "Siz barcha kanallarga a'zo bo'lmagansiz!❌"
        )
        await callback.answer()
        return
    else:
        await callback.message.answer("Siz barcha kanallarga a'zo bo'ldingiz✅")
        await start(callback.message, bot)
    await callback.answer()


async def change_language(message: types.Message, state: FSMContext):
    await message.delete()
    text = (f"<b>Tilni tanlang!\n"
            f"Choose a language!\n"
            f"Выберите язык!\n</b>")
    await message.answer(text, parse_mode="HTML", reply_markup=await language_markup())
