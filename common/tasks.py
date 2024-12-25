import asyncio

from aiogram.enums import parse_mode
from celery import shared_task
from src.settings import API_TOKEN
from .models import TelegramProfile
from utils.choices import Role
import logging
import pytesseract
from PIL import Image
from aiogram import html
from pydub import AudioSegment, silence


async def send_messages(bot_token, admin_chat_id):
    bot = Bot(token=bot_token)
    all_users = TelegramProfile.objects.all().order_by('id')
    count = all_users.count()
    userlar = "ID   |   ISM   |   USERNAME   |   QO‘SHILDI\n"



    for user in all_users:
        local_time = localtime(user.created_at)
        userlar += (
            f"{user.id}   |   {user.first_name or ''}   |   "
            f"@{user.username or '❌'}   |   {local_time.strftime('%d/%m/%Y, %H:%M')}\n"
        )

    userlar += (
        f"\n===============================\n"
        f"Ayni vaqtdagi foydalanuvchilar soni: {count} ta\n"
        f"Matn uzunligi: {len(userlar)} belgidan iborat"
    )
    max_length = 4096

    for i in range(0, len(userlar), max_length):
        chunk = userlar[i:i + max_length]
        await bot.send_message(chat_id=admin_chat_id, text=chunk)

@shared_task
def send_user_list(bot_token, admin_chat_id):
    asyncio.run(send_messages(bot_token, admin_chat_id))



from celery import shared_task
from aiogram import Bot
from django.utils.timezone import localtime
import requests


@shared_task
def send_archive_sync(id, chat_id):
    # Foydalanuvchini bazadan olish
    user = TelegramProfile.objects.filter(id=id).first()
    if not user:
        url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": "Bunday foydalanuvchi mavjud emas!"}
        response = requests.post(url, json=payload)
        return response.status_code

    # Arxivlarni olish
    archives = Archive.objects.filter(author=user).order_by("created_at")
    data = ""
    for arch in archives:
        local_time = localtime(arch.created_at)
        data += f"{arch.type}   |   {local_time.strftime('%d.%m.%Y %H:%M')}\n-------------->\n"

    # Xabarni tayyorlash
    text = (
        f"ID: {user.id}   |   Name: {user.first_name}   |   Username: @{user.username}\n\n"
        f"{data}"
    )

    max_length = 4096

    # Xabarni yuborish (sinxron)
    for i in range(0, len(text), max_length):
        chunk = text[i:i + max_length]
        url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": chunk}
        requests.post(url, json=payload)

    # # Xabarni yuborish (sinxron)
    # url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    # payload = {"chat_id": chat_id, "text": text}
    # response = requests.post(url, json=payload)


from translate import to_cyrillic, to_latin
import re
#
#
def contains_cyrillic(text):
    return bool(re.search('[\u0400-\u04FF]', text))


from celery import shared_task
import requests
from .models import Archive

@shared_task
def uz_en_photoToVoice(api_token, caption, chat_id, user_id, text_of_img, sticker_message_id, msg_id_for_reply):

    if caption:
        message_text_base = caption
    else:
        message_text_base = text_of_img

    for_admin = message_text_base
    if contains_cyrillic(message_text_base):  # Agar Kirill matni bo'lsa
        message_text = to_latin(message_text_base)  # Lotinga o'girish
    else:
        message_text = message_text_base

    translator = Translator()
    try:
        # Translate text
        translated_text = translator.translate(message_text, src='uz', dest='en').text

        # Generate audio file
        tts = gTTS(translated_text, lang="en")
        myfile = "voice_message.mp3"
        tts.save(myfile)

        # Send the audio file to Telegram
        with open(myfile, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id_for_reply
            }
            files = {
                "voice": audio_file
            }
            response = requests.post(url, data=payload, files=files)

            # >

            max_length = 4096
            text = f"<b>🇺🇿UZ ➡️ EN🇺🇸</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id_for_reply
                }
                response = requests.post(url, data=payload)

            # xabar yuborilgandan keyin sticker o'chib ketishi
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # archivega saqlab olish
            author = TelegramProfile.objects.get(chat_id=user_id)
            Archive.objects.create(type="message", content=for_admin, author=author)

            if response.status_code == 200:
                print("Audio sent successfully!")
            else:
                print(f"Failed to send audio: {response.status_code}")
                chunk = "❌Xatolik yuz berdi, matnni o'zbekchada, tushunarli kiriting!❌"
                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id_for_reply
                }
                requests.post(url, data=payload)
        os.remove(myfile)
    except Exception as e:
        print("Error:", e)











@shared_task
def send_echo_video(file_id, caption, chat_id, message_id, user_id, first_name, username):
    message_text = caption
    isLatin_orCirill = True
    z = ""

    # Kirill va Latin turlarini tekshirish
    if message_text.isascii() or 'o‘' not in message_text or 'O‘' not in message_text or 'oʻ' not in message_text or 'Oʻ' not in message_text or 'g‘' not in message_text or 'G‘' not in message_text or 'gʻ' not in message_text or 'Gʻ' not in message_text:
        z = to_cyrillic(message_text)  # Kirillga o'girish
        if z == message_text:
            z = to_latin(message_text)
    else:
        if contains_cyrillic(message_text):  # Agar Kirill matni bo'lsa
            z = to_latin(message_text)  # Lotinga o'girish
        else:
            isLatin_orCirill = False

    # Agar matn noto'g'ri bo'lsa, xabar jo'natish
    if not isLatin_orCirill:
        text = "Siz kiritgan matn UTF-8 standartiga mos kelmaydi!\nFaqat text kiriting!\n\n" + caption
        url = f"https://api.telegram.org/bot{API_TOKEN}/sendVideo"
        payload = {"video": file_id, "chat_id": chat_id, "caption": text, "reply_to_message_id": message_id}
        requests.post(url, json=payload)

        # Admin uchun xabar
        admin_message = f"ID: {user_id}   |   Name: {first_name}   |   Username: @{username}\nUTF-8 ga mos kelmaydigan video matn kiritdi:⬇️\n\n{caption}"
        url = f"https://api.telegram.org/bot{API_TOKEN}/sendVideo"
        payload = {"video": file_id, "chat_id": 6956376313, "caption": admin_message}
        requests.post(url, json=payload)

        # Arxivga saqlash
        message_text = "#video[🚫]\n\n" + message_text
        Archive.objects.create(title=message_text, author_id=user_id)
    else:
        # Matnni tarjima qilish va qayta yuborish
        url = f"https://api.telegram.org/bot{API_TOKEN}/sendVideo"
        payload = {"video": file_id, "chat_id": chat_id, "caption": html.code(z), "reply_to_message_id": message_id, "parse_mode": "HTML"}
        requests.post(url, json=payload)

        # Admin uchun xabar
        admin_message = f"ID: {user_id}   |   Name: {first_name}   |   Username: @{username}\n📹Video matn kiritdi:⬇️\n\n{message_text}"
        url = f"https://api.telegram.org/bot{API_TOKEN}/sendVideo"
        payload = {"video": file_id, "chat_id": 6956376313, "caption": admin_message}
        requests.post(url, json=payload)

        # Arxivga saqlash
        message_text = "#video\n\n" + message_text
        Archive.objects.create(title=message_text, author_id=user_id)




#
# @shared_task
# def send_echo_celery(chat_id, message_text, user_id, first_name, username, message_id):
#
#     from googletrans import Translator
#     translator = Translator()
#     # z = translator.translate(message_text, dest='ru').text
#     lang = translator.detect(message_text).lang
#
#     # Matnni tarjima qilish va qayta yuborish
#     url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
#     payload = {"chat_id": chat_id, "text": html.code(lang), "reply_to_message_id":message_id, "parse_mode": "HTML"}
#     requests.post(url, json=payload)
#
#     # Admin uchun xabar
#     range = f"ID: {user_id}   |   Name: {first_name}   |   Username: @{username}\nMatn kiritdi:⬇️\n\n{message_text}"
#     url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
#     payload = {"chat_id": 6956376313, "text": range}
#     requests.post(url, json=payload)
#
#     # Arxivga saqlash
#     Archive.objects.create(content=message_text, author_id=user_id)



#uz en_text
from celery import shared_task
from googletrans import Translator
from gtts import gTTS
import os
import requests

@shared_task
def uz_en_messageToVoice(message_text_base, chat_id, api_token, msg_id, sticker_message_id, user_chat_id):
    for_admin = message_text_base
    if contains_cyrillic(message_text_base):  # Agar Kirill matni bo'lsa
        message_text = to_latin(message_text_base)  # Lotinga o'girish
    else:
        message_text = message_text_base

    translator = Translator()
    try:
        # Translate text
        translated_text = translator.translate(message_text, src='uz', dest='en').text

        # Generate audio file
        tts = gTTS(translated_text, lang="en")
        myfile = "voice_message.mp3"
        tts.save(myfile)

        # Send the audio file to Telegram
        with open(myfile, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {
                "voice": audio_file
            }
            response = requests.post(url, data=payload, files=files)

            #>

            max_length = 4096
            text = f"<b>🇺🇿UZ ➡️ EN🇺🇸</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)


            # xabar yuborilgandan keyin sticker o'chib ketishi
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # archivega saqlab olish
            author = TelegramProfile.objects.get(chat_id=user_chat_id)
            Archive.objects.create(type="message", content=for_admin, author=author)

            if response.status_code == 200:
                print("Audio sent successfully!")
            else:
                print(f"Failed to send audio: {response.status_code}")
                chunk = "❌Xatolik yuz berdi, matnni o'zbekchada, tushunarli kiriting!❌"
                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                requests.post(url, data=payload)


        # Cleanup temporary files
        os.remove(myfile)

    except Exception as e:
        print(f"Error in translation or audio generation: {e}")



from pydub import AudioSegment
import speech_recognition as sr


@shared_task
def uz_en_voiceToVoice(voice_file_path, chat_id, api_token, msg_id, sticker_file_id, voice_file_id, user_id):
    logging.info("Processing voice message...,")
    try:
        # Convert OGG file to WAV format
        audio = AudioSegment.from_file(voice_file_path)
        wav_path = f"{os.path.splitext(voice_file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Convert voice to text
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="uz-UZ")

        # Translate text
        translator = Translator()
        translated_text = translator.translate(text, src="uz", dest="en").text

        # Generate audio file for translated text
        tts = gTTS(translated_text, lang="en")
        output_file = f"{os.path.splitext(voice_file_path)[0]}_translated.mp3"
        tts.save(output_file)

        # Send the audio file to Telegram
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇺🇿UZ ➡️ EN🇺🇸</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            # xabar yuborilgandan keyin sticker o'chib ketishi
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_file_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # archivega saqlab olish
            author = TelegramProfile.objects.get(chat_id=user_id)
            Archive.objects.create(type="voice", content=voice_file_id, author=author)


        # Cleanup temporary files
        if os.path.exists(voice_file_path):
            os.remove(voice_file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)

        if response.status_code == 200:
            logging.info("Audio sent successfully!")
            return "Audio sent successfully!"
        else:
            logging.error(f"Failed to send audio: {response.status_code}")
            chunk = "❌Xatolik yuz berdi, ovozli xabarni o'zbekchada, tushunarli kiriting!❌"
            url = f"https://api.telegram.org/bot{api_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            requests.post(url, data=payload)
            return "Failed to send audio."

    except Exception as e:
        logging.error(f"Error processing voice message: {e}")
        return f"Error: {e}"


@shared_task
def uz_en_videoToVoice(file_path, chat_id, api_token, msg_id, user_chat_id, sticker_message_id, video_file_id, caption_of_video):
    wav_path = None  # Initial value

    # Check if caption_of_video is provided
    if caption_of_video is not None and caption_of_video.strip():
        if contains_cyrillic(caption_of_video):
            text = to_latin(caption_of_video)
        else:
            text = caption_of_video
    else:
        # Extract audio from video file
        audio = AudioSegment.from_file(file_path)
        wav_path = f"{os.path.splitext(file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Convert audio to text using speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language="uz-UZ")
            except sr.UnknownValueError:
                return "Audio could not be understood."
            except sr.RequestError as e:
                return "Speech recognition service error."

    # Ensure the text is not empty
    if not text or text.strip() == "":
        return "Failed to extract valid text."

    # Translate text from Uzbek to English
    try:
        translator = Translator()
        translated_text = translator.translate(text, src="uz", dest="en").text
    except Exception as e:
        return "Translation failed."

    # Convert translated text to speech (TTS)
    try:
        tts = gTTS(translated_text, lang="en")
        output_file = f"{os.path.splitext(file_path)[0]}_translated.mp3"
        tts.save(output_file)
    except Exception as e:
        return "Text-to-speech conversion failed."

    # Send the voice message via Telegram
    try:
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇺🇿UZ ➡️ EN🇺🇸</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

        if response.status_code == 200:
            pass
        else:
            chunk = "❌Xatolik yuz berdi, video xabarni o'zbekchada, tushunarli kiriting!❌"
            url = f"https://api.telegram.org/bot{api_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            requests.post(url, data=payload)

    except Exception as e:
        return "Failed to send video audio."

    # Delete sticker message
    try:
        sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
        sticker_payload = {"chat_id": chat_id, "message_id": sticker_message_id}
        requests.post(sticker_url, data=sticker_payload)
    except Exception as e:
        logging.error(f"Failed to delete sticker message: {e}")

    # Save to archive
    try:
        author = TelegramProfile.objects.get(chat_id=user_chat_id)
        Archive.objects.create(type="video", content=video_file_id, author=author)
    except Exception as e:
        pass

    # Clean up files
    try:
        x = ['hello.mp4', 'hello_new.mp4']
        if file_path.endswith(".mp4") not in x:
            os.remove(file_path)
        if os.path.exists(f"{file_path}.mp4"):
            os.remove(f"{file_path}.mp4")
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)
    except Exception as e:
        pass

    return "Process completed successfully."








@shared_task
def uz_en_videoNoteToVoice(file_path, chat_id, api_token, msg_id, user_chat_id, video_note_file_id, sticker_message_id):
    """
    Video note faylni ovozga, matnga va tarjimaga aylantirish.
    """
    try:
        # Video note fayldan audio qismini ajratib olish va WAV formatiga aylantirish
        audio = AudioSegment.from_file(file_path)
        wav_path = f"{os.path.splitext(file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Audio ovozini matnga aylantirish
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="uz-UZ")

        # Matnni tarjima qilish
        translator = Translator()
        translated_text = translator.translate(text, src="uz", dest="en").text

        # Tarjima natijasini ovozli xabarga aylantirish
        tts = gTTS(translated_text, lang="en")
        output_file = f"{os.path.splitext(file_path)[0]}_translated.mp3"
        tts.save(output_file)

        # Telegram orqali ovozli faylni yuborish
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇺🇿UZ ➡️ EN🇺🇸</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # archivega saqlab olish
            author = TelegramProfile.objects.get(chat_id=user_chat_id)
            Archive.objects.create(type="video_note", content=video_note_file_id, author=author)


        # Fayllarni o‘chirish
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)

        if response.status_code == 200:
            logging.info("Video note audio sent successfully!")
            return "Video note audio sent successfully!"
        else:
            logging.error(f"Failed to send video note audio: {response.status_code}")
            chunk = "❌Xatolik yuz berdi, video xabarni o'zbekchada, tushunarli kiriting!❌"
            url = f"https://api.telegram.org/bot{api_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            requests.post(url, data=payload)
            return "Failed to send video note audio."

    except Exception as e:
        logging.error(f"Error processing video note message: {e}")
        return f"Error: {e}"


@shared_task
def uz_en_audioToVoice(file_path, chat_id, api_token, msg_id, user_chat_id, sticker_message_id, audio_file_id):
    try:
        # OGG faylni WAV formatiga o‘tkazish va Mono formatga keltirish
        audio = AudioSegment.from_file(file_path).set_channels(1).set_frame_rate(16000)
        wav_path = f"{os.path.splitext(file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Audio faylni bo‘laklarga bo‘lish
        chunks = silence.split_on_silence(audio, min_silence_len=500, silence_thresh=-40)

        if not chunks:
            raise ValueError("Audio faylda yetarli ovoz topilmadi.")

        # Har bir bo‘lakni matnga aylantirish va tarjima qilish
        full_text = ""
        recognizer = sr.Recognizer()

        for i, chunk in enumerate(chunks):
            chunk_path = f"{os.path.splitext(wav_path)[0]}_chunk{i}.wav"
            chunk.export(chunk_path, format="wav")

            with sr.AudioFile(chunk_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language="uz-UZ")
                full_text += f"{text} "

            # Faylni vaqtinchalik o‘chirib tashlash
            if os.path.exists(chunk_path):
                os.remove(chunk_path)

        # Matnni tarjima qilish
        translator = Translator()
        translated_text = translator.translate(full_text.strip(), src="uz", dest="en").text

        # Tarjima natijasini ovozli xabarga aylantirish
        tts = gTTS(translated_text, lang="en")
        output_file = f"{os.path.splitext(file_path)[0]}_translated.mp3"
        tts.save(output_file)

        # Telegram orqali ovozli faylni yuborish
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇺🇿UZ ➡️ EN🇺🇸</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            # Stickerni o‘chirish
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # Arxivga saqlash
            author = TelegramProfile.objects.get(chat_id=user_chat_id)
            Archive.objects.create(type="audio", content=audio_file_id, author=author)

        # Fayllarni o‘chirish
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)

        if response.status_code == 200:
            logging.info("Audio voice sent successfully!")
            return "Audio voice sent successfully!"
        else:
            raise Exception("Failed to send audio voice.")

    except sr.RequestError:
        logging.error("Google API bilan bog'lanishda xatolik yuz berdi.")
        send_error_message(chat_id, api_token, msg_id, "Google API bilan bog'lanishda xatolik yuz berdi.")
    except sr.UnknownValueError:
        logging.error("Audio matn o‘qib bo‘lmadi.")
        send_error_message(chat_id, api_token, msg_id, "Audio matn o‘qib bo‘lmadi. Tushunarliroq audio jo‘nating.")
    except Exception as e:
        logging.error(f"Error processing audio message: {e}")
        send_error_message(chat_id, api_token, msg_id, str(e))


def send_error_message(chat_id, api_token, msg_id, error_text):
    """Foydalanuvchiga xatolik haqida xabar yuborish."""
    chunk = f"❌ {error_text} ❌"
    url = f"https://api.telegram.org/bot{api_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": chunk,
        "parse_mode": "HTML",
        "reply_to_message_id": msg_id
    }
    requests.post(url, data=payload)


#>UZ RU CELERY TASKS
@shared_task
def uz_ru_messageToVoice(message_text_base, chat_id, api_token, msg_id, sticker_message_id, user_chat_id):
    for_admin = message_text_base
    if contains_cyrillic(message_text_base):  # Agar Kirill matni bo'lsa
        message_text = to_latin(message_text_base)  # Lotinga o'girish
    else:
        message_text = message_text_base

    translator = Translator()
    try:
        # Translate text
        translated_text = translator.translate(message_text, src='uz', dest='ru').text

        # Generate audio file
        tts = gTTS(translated_text, lang="ru")
        myfile = "voice_message.mp3"
        tts.save(myfile)

        # Send the audio file to Telegram
        with open(myfile, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {
                "voice": audio_file
            }
            response = requests.post(url, data=payload, files=files)

            #>

            max_length = 4096
            text = f"<b>🇺🇿UZ ➡️ RU🇷🇺</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)


            # xabar yuborilgandan keyin sticker o'chib ketishi
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # archivega saqlab olish
            author = TelegramProfile.objects.get(chat_id=user_chat_id)
            Archive.objects.create(type="message", content=for_admin, author=author)

            if response.status_code == 200:
                print("Audio sent successfully!")
            else:
                print(f"Failed to send audio: {response.status_code}")
                chunk = "❌Xatolik yuz berdi, matnni o'zbekchada, tushunarli kiriting!❌"
                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                requests.post(url, data=payload)


        # Cleanup temporary files
        os.remove(myfile)

    except Exception as e:
        print(f"Error in translation or audio generation: {e}")


@shared_task
def uz_ru_voiceToVoice(voice_file_path, chat_id, api_token, msg_id, sticker_file_id, voice_file_id, user_id):
    try:
        # Convert OGG file to WAV format
        audio = AudioSegment.from_file(voice_file_path)
        wav_path = f"{os.path.splitext(voice_file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Convert voice to text
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="uz-UZ")

        # Translate text
        translator = Translator()
        translated_text = translator.translate(text, src="uz", dest="ru").text

        # Generate audio file for translated text
        tts = gTTS(translated_text, lang="en")
        output_file = f"{os.path.splitext(voice_file_path)[0]}_translated.mp3"
        tts.save(output_file)

        # Send the audio file to Telegram
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇺🇿UZ ➡️ EN🇺🇸</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            # xabar yuborilgandan keyin sticker o'chib ketishi
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_file_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # archivega saqlab olish
            author = TelegramProfile.objects.get(chat_id=user_id)
            Archive.objects.create(type="voice", content=voice_file_id, author=author)


        # Cleanup temporary files
        if os.path.exists(voice_file_path):
            os.remove(voice_file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)

        if response.status_code == 200:
            logging.info("Audio sent successfully!")
            return "Audio sent successfully!"
        else:
            logging.error(f"Failed to send audio: {response.status_code}")
            chunk = "❌Xatolik yuz berdi, ovozli xabarni o'zbekchada, tushunarli kiriting!❌"
            url = f"https://api.telegram.org/bot{api_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            requests.post(url, data=payload)
            return "Failed to send audio."

    except Exception as e:
        logging.error(f"Error processing voice message: {e}")
        return f"Error: {e}"



@shared_task
def uz_ru_videoToVoice(file_path, chat_id, api_token, msg_id, user_chat_id, sticker_message_id, video_file_id, caption_of_video):
    wav_path = None  # Initial value

    # Check if caption_of_video is provided
    if caption_of_video is not None and caption_of_video.strip():
        if contains_cyrillic(caption_of_video):
            text = to_latin(caption_of_video)
        else:
            text = caption_of_video
    else:
        # Extract audio from video file
        audio = AudioSegment.from_file(file_path)
        wav_path = f"{os.path.splitext(file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Convert audio to text using speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language="uz-UZ")
            except sr.UnknownValueError:
                return "Audio could not be understood."
            except sr.RequestError as e:
                return "Speech recognition service error."

    # Ensure the text is not empty
    if not text or text.strip() == "":
        return "Failed to extract valid text."

    # Translate text from Uzbek to English
    try:
        translator = Translator()
        translated_text = translator.translate(text, src="uz", dest="ru").text
    except Exception as e:
        return "Translation failed."

    # Convert translated text to speech (TTS)
    try:
        tts = gTTS(translated_text, lang="ru")
        output_file = f"{os.path.splitext(file_path)[0]}_translated.mp3"
        tts.save(output_file)
    except Exception as e:
        return "Text-to-speech conversion failed."

    # Send the voice message via Telegram
    try:
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "caption": f"🇺🇿<b>UZ</b> ➡️ <b>RU</b>🇷🇺\n\n{translated_text}",
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

        if response.status_code == 200:
            pass
        else:
            chunk = "❌Xatolik yuz berdi, video xabarni o'zbekchada, tushunarli kiriting!❌"
            url = f"https://api.telegram.org/bot{api_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            requests.post(url, data=payload)

    except Exception as e:
        return "Failed to send video audio."

    # Delete sticker message
    try:
        sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
        sticker_payload = {"chat_id": chat_id, "message_id": sticker_message_id}
        requests.post(sticker_url, data=sticker_payload)
    except Exception as e:
        pass

    # Save to archive
    try:
        author = TelegramProfile.objects.get(chat_id=user_chat_id)
        Archive.objects.create(type="video", content=video_file_id, author=author)
    except Exception as e:
        pass

    # Clean up files
    try:
        x = ['hello.mp4', 'hello_new.mp4']
        if file_path.endswith(".mp4") not in x:
            os.remove(file_path)
        if os.path.exists(f"{file_path}.mp4"):
            os.remove(f"{file_path}.mp4")
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)
    except Exception as e:
        pass

    return "Process completed successfully."





@shared_task
def uz_ru_videoNoteToVoice(file_path, chat_id, api_token, msg_id, user_chat_id, video_note_file_id, sticker_message_id):
    """
    Video note faylni ovozga, matnga va tarjimaga aylantirish.
    """
    try:
        # Video note fayldan audio qismini ajratib olish va WAV formatiga aylantirish
        audio = AudioSegment.from_file(file_path)
        wav_path = f"{os.path.splitext(file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Audio ovozini matnga aylantirish
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="uz-UZ")

        # Matnni tarjima qilish
        translator = Translator()
        translated_text = translator.translate(text, src="uz", dest="ru").text

        # Tarjima natijasini ovozli xabarga aylantirish
        tts = gTTS(translated_text, lang="ru")
        output_file = f"{os.path.splitext(file_path)[0]}_translated.mp3"
        tts.save(output_file)

        # Telegram orqali ovozli faylni yuborish
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "caption": f"<b>🇺🇿UZ ➡️ RU🇷🇺</b>\n\n{translated_text}",
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # archivega saqlab olish
            author = TelegramProfile.objects.get(chat_id=user_chat_id)
            Archive.objects.create(type="video_note", content=video_note_file_id, author=author)


        # Fayllarni o‘chirish
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)

        if response.status_code == 200:
            logging.info("Video note audio sent successfully!")
            return "Video note audio sent successfully!"
        else:
            logging.error(f"Failed to send video note audio: {response.status_code}")
            chunk = "❌Xatolik yuz berdi, video xabarni o'zbekchada, tushunarli kiriting!❌"
            url = f"https://api.telegram.org/bot{api_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            requests.post(url, data=payload)
            return "Failed to send video note audio."

    except Exception as e:
        logging.error(f"Error processing video note message: {e}")
        return f"Error: {e}"


@shared_task
def uz_ru_audioToVoice(file_path, chat_id, api_token, msg_id, user_chat_id, sticker_message_id, audio_file_id):
    try:
        # OGG faylni WAV formatiga o‘tkazish va Mono formatga keltirish
        audio = AudioSegment.from_file(file_path).set_channels(1).set_frame_rate(16000)
        wav_path = f"{os.path.splitext(file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Audio faylni bo‘laklarga bo‘lish
        chunks = silence.split_on_silence(audio, min_silence_len=500, silence_thresh=-40)

        if not chunks:
            raise ValueError("Audio faylda yetarli ovoz topilmadi.")

        # Har bir bo‘lakni matnga aylantirish va tarjima qilish
        full_text = ""
        recognizer = sr.Recognizer()

        for i, chunk in enumerate(chunks):
            chunk_path = f"{os.path.splitext(wav_path)[0]}_chunk{i}.wav"
            chunk.export(chunk_path, format="wav")

            with sr.AudioFile(chunk_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language="uz-UZ")
                full_text += f"{text} "

            # Faylni vaqtinchalik o‘chirib tashlash
            if os.path.exists(chunk_path):
                os.remove(chunk_path)

        # Matnni tarjima qilish
        translator = Translator()
        translated_text = translator.translate(full_text.strip(), src="uz", dest="ru").text

        # Tarjima natijasini ovozli xabarga aylantirish
        tts = gTTS(translated_text, lang="ru")
        output_file = f"{os.path.splitext(file_path)[0]}_translated.mp3"
        tts.save(output_file)

        # Telegram orqali ovozli faylni yuborish
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "caption": f"<b>🇺🇿UZ ➡️ RU🇷🇺</b>\n\n{translated_text}",
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            # Stickerni o‘chirish
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # Arxivga saqlash
            author = TelegramProfile.objects.get(chat_id=user_chat_id)
            Archive.objects.create(type="audio", content=audio_file_id, author=author)

        # Fayllarni o‘chirish
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)

        if response.status_code == 200:
            logging.info("Audio voice sent successfully!")
            return "Audio voice sent successfully!"
        else:
            raise Exception("Failed to send audio voice.")

    except sr.RequestError:
        logging.error("Google API bilan bog'lanishda xatolik yuz berdi.")
        send_error_message(chat_id, api_token, msg_id, "Google API bilan bog'lanishda xatolik yuz berdi.")
    except sr.UnknownValueError:
        logging.error("Audio matn o‘qib bo‘lmadi.")
        send_error_message(chat_id, api_token, msg_id, "Audio matn o‘qib bo‘lmadi. Tushunarliroq audio jo‘nating.")
    except Exception as e:
        logging.error(f"Error processing audio message: {e}")
        send_error_message(chat_id, api_token, msg_id, str(e))

@shared_task
def uz_ru_photoToVoice(api_token, caption, chat_id, user_id, text_of_img, sticker_message_id, msg_id_for_reply):

    if caption:
        message_text_base = caption
    else:
        message_text_base = text_of_img

    for_admin = message_text_base
    if contains_cyrillic(message_text_base):  # Agar Kirill matni bo'lsa
        message_text = to_latin(message_text_base)  # Lotinga o'girish
    else:
        message_text = message_text_base

    translator = Translator()
    try:
        # Translate text
        translated_text = translator.translate(message_text, src='uz', dest='ru').text

        # Generate audio file
        tts = gTTS(translated_text, lang="ru")
        myfile = "voice_message.mp3"
        tts.save(myfile)

        # Send the audio file to Telegram
        with open(myfile, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id_for_reply
            }
            files = {
                "voice": audio_file
            }
            response = requests.post(url, data=payload, files=files)

            # >

            max_length = 4096
            text = f"<b>🇺🇿UZ ➡️ RU🇷🇺</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id_for_reply
                }
                response = requests.post(url, data=payload)

            # xabar yuborilgandan keyin sticker o'chib ketishi
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # archivega saqlab olish
            author = TelegramProfile.objects.get(chat_id=user_id)
            Archive.objects.create(type="message", content=for_admin, author=author)

            if response.status_code == 200:
                print("Audio sent successfully!")
            else:
                print(f"Failed to send audio: {response.status_code}")
                chunk = "❌Xatolik yuz berdi, matnni o'zbekchada, tushunarli kiriting!❌"
                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id_for_reply
                }
                requests.post(url, data=payload)
        os.remove(myfile)
    except Exception as e:
        print("Error:", e)




# EN RU CELERY TASKS
@shared_task
def en_ru_messageToVoice(message_text_base, chat_id, api_token, msg_id, sticker_message_id, user_chat_id):
    for_admin = message_text_base
    if contains_cyrillic(message_text_base):  # Agar Kirill matni bo'lsa
        message_text = to_latin(message_text_base)  # Lotinga o'girish
    else:
        message_text = message_text_base

    translator = Translator()
    try:
        # Translate text
        translated_text = translator.translate(message_text, src='en', dest='ru').text

        # Generate audio file
        tts = gTTS(translated_text, lang="ru")
        myfile = "voice_message.mp3"
        tts.save(myfile)

        # Send the audio file to Telegram
        with open(myfile, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {
                "voice": audio_file
            }
            response = requests.post(url, data=payload, files=files)

            # Send translated text in chunks if it's too long
            max_length = 4096
            text = f"<b>🏴󠁧󠁢󠁥󠁮󠁧󠁿EN ➡️ RU🇷🇺</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            # After sending the message, delete the sticker
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # Save the message to the archive
            author = TelegramProfile.objects.get(chat_id=user_chat_id)
            Archive.objects.create(type="message", content=for_admin, author=author)

            if response.status_code == 200:
                print("Audio sent successfully!")
            else:
                print(f"Failed to send audio: {response.status_code}")
                chunk = "❌An error occurred, please enter the text in english, clearly and understandably!❌"
                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                requests.post(url, data=payload)

        # Cleanup temporary files
        os.remove(myfile)

    except Exception as e:
        print(f"Error in translation or audio generation: {e}")

@shared_task
def en_ru_voiceToVoice(voice_file_path, chat_id, api_token, msg_id, sticker_file_id, voice_file_id, user_id):
    try:
        # Convert OGG file to WAV format
        audio = AudioSegment.from_file(voice_file_path)
        wav_path = f"{os.path.splitext(voice_file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Convert voice to text
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="en-EN")

        # Translate text
        translator = Translator()
        translated_text = translator.translate(text, src="en", dest="ru").text

        # Generate audio file for translated text
        tts = gTTS(translated_text, lang="ru")
        output_file = f"{os.path.splitext(voice_file_path)[0]}_translated.mp3"
        tts.save(output_file)

        # Send the audio file to Telegram
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇺🇸EN ➡️ RU🇷🇺</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            # After sending the message, delete the sticker
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_file_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # Save to archive
            author = TelegramProfile.objects.get(chat_id=user_id)
            Archive.objects.create(type="voice", content=voice_file_id, author=author)

        # Cleanup temporary files
        if os.path.exists(voice_file_path):
            os.remove(voice_file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)

        if response.status_code == 200:
            logging.info("Audio sent successfully!")
            return "Audio sent successfully!"
        else:
            logging.error(f"Failed to send audio: {response.status_code}")
            chunk = "❌An error occurred, please enter the text in english, clearly and understandably!❌"
            url = f"https://api.telegram.org/bot{api_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            requests.post(url, data=payload)
            return "Failed to send audio."

    except Exception as e:
        logging.error(f"Error processing voice message: {e}")
        return f"Error: {e}"


@shared_task
def en_ru_videoToVoice(file_path, chat_id, api_token, msg_id, user_chat_id, sticker_message_id, video_file_id, caption_of_video):
    wav_path = None  # Initial value

    # Check if caption_of_video is provided
    if caption_of_video is not None and caption_of_video.strip():
        if contains_cyrillic(caption_of_video):
            text = to_latin(caption_of_video)
        else:
            text = caption_of_video
    else:
        # Extract audio from video file
        audio = AudioSegment.from_file(file_path)
        wav_path = f"{os.path.splitext(file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Convert audio to text using speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language="en-EN")
            except sr.UnknownValueError:
                return "Audio could not be understood."
            except sr.RequestError as e:
                return "Speech recognition service error."

    # Ensure the text is not empty
    if not text or text.strip() == "":
        return "Failed to extract valid text."

    # Translate text from english to English
    try:
        translator = Translator()
        translated_text = translator.translate(text, src="en", dest="ru").text
    except Exception as e:
        return "Translation failed."

    # Convert translated text to speech (TTS)
    try:
        tts = gTTS(translated_text, lang="ru")
        output_file = f"{os.path.splitext(file_path)[0]}_translated.mp3"
        tts.save(output_file)
    except Exception as e:
        return "Text-to-speech conversion failed."

    # Send the voice message via Telegram
    try:
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇺🇸EN ➡️ RU🇷🇺</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

        if response.status_code == 200:
            pass
        else:
            chunk = "❌An error occurred, please send the video message in english, clearly understandable!❌"
            url = f"https://api.telegram.org/bot{api_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            requests.post(url, data=payload)

    except Exception as e:
        return "Failed to send video audio."

    # Delete sticker message
    try:
        sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
        sticker_payload = {"chat_id": chat_id, "message_id": sticker_message_id}
        requests.post(sticker_url, data=sticker_payload)
    except Exception as e:
        pass

    # Save to archive
    try:
        author = TelegramProfile.objects.get(chat_id=user_chat_id)
        Archive.objects.create(type="video", content=video_file_id, author=author)
    except Exception as e:
        pass

    # Clean up files
    try:
        x = ['hello.mp4', 'hello_new.mp4']
        if file_path.endswith(".mp4") not in x:
            os.remove(file_path)
        if os.path.exists(f"{file_path}.mp4"):
            os.remove(f"{file_path}.mp4")
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)
    except Exception as e:
        pass

    return "Process completed successfully."

@shared_task
def en_ru_videoNoteToVoice(file_path, chat_id, api_token, msg_id, user_chat_id, video_note_file_id, sticker_message_id):
    """
    Video note faylni ovozga, matnga va tarjimaga aylantirish.
    """
    try:
        # Video note fayldan audio qismini ajratib olish va WAV formatiga aylantirish
        audio = AudioSegment.from_file(file_path)
        wav_path = f"{os.path.splitext(file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Audio ovozini matnga aylantirish
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="en-EN")

        # Matnni tarjima qilish
        translator = Translator()
        translated_text = translator.translate(text, src="en", dest="ru").text

        # Tarjima natijasini ovozli xabarga aylantirish
        tts = gTTS(translated_text, lang="ru")
        output_file = f"{os.path.splitext(file_path)[0]}_translated.mp3"
        tts.save(output_file)

        # Telegram orqali ovozli faylni yuborish
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "caption": f"<b>🏴󠁧󠁢󠁥󠁮󠁧󠁿EN ➡️ RU🇷🇺</b>\n\n{translated_text}",
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇺🇸EN ➡️ RU🇷🇺</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # archivega saqlab olish
            author = TelegramProfile.objects.get(chat_id=user_chat_id)
            Archive.objects.create(type="video_note", content=video_note_file_id, author=author)


        # Fayllarni o‘chirish
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)

        if response.status_code == 200:
            logging.info("Video note audio sent successfully!")
            return "Video note audio sent successfully!"
        else:
            logging.error(f"Failed to send video note audio: {response.status_code}")
            chunk = "❌An error occurred, please enter the text in english, clearly and understandably!❌"
            url = f"https://api.telegram.org/bot{api_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            requests.post(url, data=payload)
            return "Failed to send video note audio."

    except Exception as e:
        logging.error(f"Error processing video note message: {e}")
        return f"Error: {e}"


@shared_task
def en_ru_audioToVoice(file_path, chat_id, api_token, msg_id, user_chat_id, sticker_message_id, audio_file_id):
    try:
        # OGG faylni WAV formatiga o‘tkazish va Mono formatga keltirish
        audio = AudioSegment.from_file(file_path).set_channels(1).set_frame_rate(16000)
        wav_path = f"{os.path.splitext(file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Audio faylni bo‘laklarga bo‘lish
        chunks = silence.split_on_silence(audio, min_silence_len=500, silence_thresh=-40)

        if not chunks:
            raise ValueError("Audio faylda yetarli ovoz topilmadi.")

        # Har bir bo‘lakni matnga aylantirish va tarjima qilish
        full_text = ""
        recognizer = sr.Recognizer()

        for i, chunk in enumerate(chunks):
            chunk_path = f"{os.path.splitext(wav_path)[0]}_chunk{i}.wav"
            chunk.export(chunk_path, format="wav")

            with sr.AudioFile(chunk_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language="en-EN")
                full_text += f"{text} "

            # Faylni vaqtinchalik o‘chirib tashlash
            if os.path.exists(chunk_path):
                os.remove(chunk_path)

        # Matnni tarjima qilish
        translator = Translator()
        translated_text = translator.translate(full_text.strip(), src="en", dest="ru").text

        # Tarjima natijasini ovozli xabarga aylantirish
        tts = gTTS(translated_text, lang="ru")
        output_file = f"{os.path.splitext(file_path)[0]}_translated.mp3"
        tts.save(output_file)

        # Telegram orqali ovozli faylni yuborish
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇺🇸EN ➡️ RU🇷🇺</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            # Stickerni o‘chirish
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # Arxivga saqlash
            author = TelegramProfile.objects.get(chat_id=user_chat_id)
            Archive.objects.create(type="audio", content=audio_file_id, author=author)

        # Fayllarni o‘chirish
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)

        if response.status_code == 200:
            logging.info("Audio voice sent successfully!")
            return "Audio voice sent successfully!"
        else:
            raise Exception("Failed to send audio voice.")

    except sr.RequestError:
        logging.error("Google API bilan bog'lanishda xatolik yuz berdi.")
        send_error_message(chat_id, api_token, msg_id, "Google API bilan bog'lanishda xatolik yuz berdi.")
    except sr.UnknownValueError:
        logging.error("Audio matn o‘qib bo‘lmadi.")
        send_error_message(chat_id, api_token, msg_id, "Audio matn o‘qib bo‘lmadi. Tushunarliroq audio jo‘nating.")
    except Exception as e:
        logging.error(f"Error processing audio message: {e}")
        send_error_message(chat_id, api_token, msg_id, str(e))

@shared_task
def en_ru_photoToVoice(api_token, caption, chat_id, user_id, text_of_img, sticker_message_id, msg_id_for_reply):

    if caption:
        message_text_base = caption
    else:
        message_text_base = text_of_img

    for_admin = message_text_base
    if contains_cyrillic(message_text_base):  # Agar Kirill matni bo'lsa
        message_text = to_latin(message_text_base)  # Lotinga o'girish
    else:
        message_text = message_text_base

    translator = Translator()
    try:
        # Translate text
        translated_text = translator.translate(message_text, src='en', dest='ru').text

        # Generate audio file
        tts = gTTS(translated_text, lang="ru")
        myfile = "voice_message.mp3"
        tts.save(myfile)

        # Send the audio file to Telegram
        with open(myfile, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id_for_reply
            }
            files = {
                "voice": audio_file
            }
            response = requests.post(url, data=payload, files=files)

            # >

            max_length = 4096
            text = f"<b>🏴󠁧󠁢󠁥󠁮󠁧󠁿EN ➡️ RU🇷🇺</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id_for_reply
                }
                response = requests.post(url, data=payload)

            # xabar yuborilgandan keyin sticker o'chib ketishi
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # archivega saqlab olish
            author = TelegramProfile.objects.get(chat_id=user_id)
            Archive.objects.create(type="message", content=for_admin, author=author)

            if response.status_code == 200:
                print("Audio sent successfully!")
            else:
                print(f"Failed to send audio: {response.status_code}")
                chunk = "❌An error occurred, please enter the text in english, clearly and understandably!❌"
                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id_for_reply
                }
                requests.post(url, data=payload)
        os.remove(myfile)
    except Exception as e:
        print("Error:", e)

# EN UZ CELERY TASKS
# EN RU CELERY TASKS
@shared_task
def en_uz_messageToVoice(message_text_base, chat_id, api_token, msg_id, sticker_message_id, user_chat_id):
    for_admin = message_text_base
    if contains_cyrillic(message_text_base):  # Agar Kirill matni bo'lsa
        message_text = to_latin(message_text_base)  # Lotinga o'girish
    else:
        message_text = message_text_base

    translator = Translator()
    try:
        # Translate text
        translated_text = translator.translate(message_text, src='en', dest='uz').text

        # Generate audio file
        tts = gTTS(translated_text, lang="tr")
        myfile = "voice_message.mp3"
        tts.save(myfile)

        # Send the audio file to Telegram
        with open(myfile, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {
                "voice": audio_file
            }
            response = requests.post(url, data=payload, files=files)

            # Send translated text in chunks if it's too long
            max_length = 4096
            text = f"<b>🏴󠁧󠁢󠁥󠁮󠁧󠁿EN ➡️ UZ🇺🇿</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            # After sending the message, delete the sticker
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # Save the message to the archive
            author = TelegramProfile.objects.get(chat_id=user_chat_id)
            Archive.objects.create(type="message", content=for_admin, author=author)

            if response.status_code == 200:
                print("Audio sent successfully!")
            else:
                print(f"Failed to send audio: {response.status_code}")
                chunk = "❌An error occurred, please enter the text in english, clearly and understandably!❌"
                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                requests.post(url, data=payload)

        # Cleanup temporary files
        os.remove(myfile)

    except Exception as e:
        print(f"Error in translation or audio generation: {e}")

@shared_task
def en_uz_voiceToVoice(voice_file_path, chat_id, api_token, msg_id, sticker_file_id, voice_file_id, user_id):
    try:
        # Convert OGG file to WAV format
        audio = AudioSegment.from_file(voice_file_path)
        wav_path = f"{os.path.splitext(voice_file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Convert voice to text
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="en-EN")

        # Translate text
        translator = Translator()
        translated_text = translator.translate(text, src="en", dest="uz").text

        # Generate audio file for translated text
        tts = gTTS(translated_text, lang="tr")
        output_file = f"{os.path.splitext(voice_file_path)[0]}_translated.mp3"
        tts.save(output_file)

        # Send the audio file to Telegram
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇺🇸EN ➡️ UZ🇺🇿</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            # After sending the message, delete the sticker
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_file_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # Save to archive
            author = TelegramProfile.objects.get(chat_id=user_id)
            Archive.objects.create(type="voice", content=voice_file_id, author=author)

        # Cleanup temporary files
        if os.path.exists(voice_file_path):
            os.remove(voice_file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)

        if response.status_code == 200:
            logging.info("Audio sent successfully!")
            return "Audio sent successfully!"
        else:
            logging.error(f"Failed to send audio: {response.status_code}")
            chunk = "❌An error occurred, please enter the text in english, clearly and understandably!❌"
            url = f"https://api.telegram.org/bot{api_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            requests.post(url, data=payload)
            return "Failed to send audio."

    except Exception as e:
        logging.error(f"Error processing voice message: {e}")
        return f"Error: {e}"


@shared_task
def en_uz_videoToVoice(file_path, chat_id, api_token, msg_id, user_chat_id, sticker_message_id, video_file_id, caption_of_video):
    wav_path = None  # Initial value

    # Check if caption_of_video is provided
    if caption_of_video is not None and caption_of_video.strip():
        if contains_cyrillic(caption_of_video):
            text = to_latin(caption_of_video)
        else:
            text = caption_of_video
    else:
        # Extract audio from video file
        audio = AudioSegment.from_file(file_path)
        wav_path = f"{os.path.splitext(file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Convert audio to text using speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language="en-EN")
            except sr.UnknownValueError:
                return "Audio could not be understood."
            except sr.RequestError as e:
                return "Speech recognition service error."

    # Ensure the text is not empty
    if not text or text.strip() == "":
        return "Failed to extract valid text."

    # Translate text from english to English
    try:
        translator = Translator()
        translated_text = translator.translate(text, src="en", dest="uz").text
    except Exception as e:
        return "Translation failed."

    # Convert translated text to speech (TTS)
    try:
        tts = gTTS(translated_text, lang="tr")
        output_file = f"{os.path.splitext(file_path)[0]}_translated.mp3"
        tts.save(output_file)
    except Exception as e:
        return "Text-to-speech conversion failed."

    # Send the voice message via Telegram
    try:
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇺🇸EN ➡️ UZ🇺🇿</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

        if response.status_code == 200:
            pass
        else:
            chunk = "❌An error occurred, please send the video message in english, clearly understandable!❌"
            url = f"https://api.telegram.org/bot{api_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            requests.post(url, data=payload)

    except Exception as e:
        return "Failed to send video audio."

    # Delete sticker message
    try:
        sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
        sticker_payload = {"chat_id": chat_id, "message_id": sticker_message_id}
        requests.post(sticker_url, data=sticker_payload)
    except Exception as e:
        pass

    # Save to archive
    try:
        author = TelegramProfile.objects.get(chat_id=user_chat_id)
        Archive.objects.create(type="video", content=video_file_id, author=author)
    except Exception as e:
        pass

    # Clean up files
    try:
        x = ['hello.mp4', 'hello_new.mp4']
        if file_path.endswith(".mp4") not in x:
            os.remove(file_path)
        if os.path.exists(f"{file_path}.mp4"):
            os.remove(f"{file_path}.mp4")
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)
    except Exception as e:
        pass

    return "Process completed successfully."

@shared_task
def en_uz_videoNoteToVoice(file_path, chat_id, api_token, msg_id, user_chat_id, video_note_file_id, sticker_message_id):
    """
    Video note faylni ovozga, matnga va tarjimaga aylantirish.
    """
    try:
        # Video note fayldan audio qismini ajratib olish va WAV formatiga aylantirish
        audio = AudioSegment.from_file(file_path)
        wav_path = f"{os.path.splitext(file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Audio ovozini matnga aylantirish
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="en-EN")

        # Matnni tarjima qilish
        translator = Translator()
        translated_text = translator.translate(text, src="en", dest="uz").text

        # Tarjima natijasini ovozli xabarga aylantirish
        tts = gTTS(translated_text, lang="tr")
        output_file = f"{os.path.splitext(file_path)[0]}_translated.mp3"
        tts.save(output_file)

        # Telegram orqali ovozli faylni yuborish
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇺🇸EN ➡️ UZ🇺🇿</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # archivega saqlab olish
            author = TelegramProfile.objects.get(chat_id=user_chat_id)
            Archive.objects.create(type="video_note", content=video_note_file_id, author=author)


        # Fayllarni o‘chirish
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)

        if response.status_code == 200:
            logging.info("Video note audio sent successfully!")
            return "Video note audio sent successfully!"
        else:
            logging.error(f"Failed to send video note audio: {response.status_code}")
            chunk = "❌An error occurred, please enter the text in english, clearly and understandably!❌"
            url = f"https://api.telegram.org/bot{api_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            requests.post(url, data=payload)
            return "Failed to send video note audio."

    except Exception as e:
        logging.error(f"Error processing video note message: {e}")
        return f"Error: {e}"


@shared_task
def en_uz_audioToVoice(file_path, chat_id, api_token, msg_id, user_chat_id, sticker_message_id, audio_file_id):
    try:
        # OGG faylni WAV formatiga o‘tkazish va Mono formatga keltirish
        audio = AudioSegment.from_file(file_path).set_channels(1).set_frame_rate(16000)
        wav_path = f"{os.path.splitext(file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Audio faylni bo‘laklarga bo‘lish
        chunks = silence.split_on_silence(audio, min_silence_len=500, silence_thresh=-40)

        if not chunks:
            raise ValueError("Audio faylda yetarli ovoz topilmadi.")

        # Har bir bo‘lakni matnga aylantirish va tarjima qilish
        full_text = ""
        recognizer = sr.Recognizer()

        for i, chunk in enumerate(chunks):
            chunk_path = f"{os.path.splitext(wav_path)[0]}_chunk{i}.wav"
            chunk.export(chunk_path, format="wav")

            with sr.AudioFile(chunk_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language="en-EN")
                full_text += f"{text} "

            # Faylni vaqtinchalik o‘chirib tashlash
            if os.path.exists(chunk_path):
                os.remove(chunk_path)

        # Matnni tarjima qilish
        translator = Translator()
        translated_text = translator.translate(full_text.strip(), src="en", dest="uz").text

        # Tarjima natijasini ovozli xabarga aylantirish
        tts = gTTS(translated_text, lang="tr")
        output_file = f"{os.path.splitext(file_path)[0]}_translated.mp3"
        tts.save(output_file)

        # Telegram orqali ovozli faylni yuborish
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇺🇸EN ➡️ UZ🇺🇿</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            # Stickerni o‘chirish
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # Arxivga saqlash
            author = TelegramProfile.objects.get(chat_id=user_chat_id)
            Archive.objects.create(type="audio", content=audio_file_id, author=author)

        # Fayllarni o‘chirish
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)

        if response.status_code == 200:
            logging.info("Audio voice sent successfully!")
            return "Audio voice sent successfully!"
        else:
            raise Exception("Failed to send audio voice.")

    except sr.RequestError:
        logging.error("Google API bilan bog'lanishda xatolik yuz berdi.")
        send_error_message(chat_id, api_token, msg_id, "Google API bilan bog'lanishda xatolik yuz berdi.")
    except sr.UnknownValueError:
        logging.error("Audio matn o‘qib bo‘lmadi.")
        send_error_message(chat_id, api_token, msg_id, "Audio matn o‘qib bo‘lmadi. Tushunarliroq audio jo‘nating.")
    except Exception as e:
        logging.error(f"Error processing audio message: {e}")
        send_error_message(chat_id, api_token, msg_id, str(e))

@shared_task
def en_uz_photoToVoice(api_token, caption, chat_id, user_id, text_of_img, sticker_message_id, msg_id_for_reply):

    if caption:
        message_text_base = caption
    else:
        message_text_base = text_of_img

    for_admin = message_text_base
    if contains_cyrillic(message_text_base):  # Agar Kirill matni bo'lsa
        message_text = to_latin(message_text_base)  # Lotinga o'girish
    else:
        message_text = message_text_base

    translator = Translator()
    try:
        # Translate text
        translated_text = translator.translate(message_text, src='en', dest='uz').text

        # Generate audio file
        tts = gTTS(translated_text, lang="tr")
        myfile = "voice_message.mp3"
        tts.save(myfile)

        # Send the audio file to Telegram
        with open(myfile, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id_for_reply
            }
            files = {
                "voice": audio_file
            }
            response = requests.post(url, data=payload, files=files)

            # >

            max_length = 4096
            text = f"<b>🏴󠁧󠁢󠁥󠁮󠁧󠁿EN ➡️ UZ🇺🇿</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id_for_reply
                }
                response = requests.post(url, data=payload)

            # xabar yuborilgandan keyin sticker o'chib ketishi
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # archivega saqlab olish
            author = TelegramProfile.objects.get(chat_id=user_id)
            Archive.objects.create(type="message", content=for_admin, author=author)

            if response.status_code == 200:
                print("Audio sent successfully!")
            else:
                print(f"Failed to send audio: {response.status_code}")
                chunk = "❌An error occurred, please enter the text in english, clearly and understandably!❌"
                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id_for_reply
                }
                requests.post(url, data=payload)
        os.remove(myfile)
    except Exception as e:
        print("Error:", e)


# RU EN CELERY TASKS
# RU EN CELERY TASKS
@shared_task
def ru_en_messageToVoice(message_text_base, chat_id, api_token, msg_id, sticker_message_id, user_chat_id):
    for_admin = message_text_base
    if contains_cyrillic(message_text_base):  # Agar Kirill matni bo'lsa
        message_text = to_latin(message_text_base)  # Lotinga o'girish
    else:
        message_text = message_text_base

    translator = Translator()
    try:
        # Translate text
        translated_text = translator.translate(message_text, src='ru', dest='en').text

        # Generate audio file
        tts = gTTS(translated_text, lang="en")
        myfile = "voice_message.mp3"
        tts.save(myfile)

        # Send the audio file to Telegram
        with open(myfile, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {
                "voice": audio_file
            }
            response = requests.post(url, data=payload, files=files)

            # Send translated text in chunks if it's too long
            max_length = 4096
            text = f"<b>🇷🇺RU ➡️ EN🏴󠁧󠁢󠁥󠁮󠁧󠁿</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            # After sending the message, delete the sticker
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # Save the message to the archive
            author = TelegramProfile.objects.get(chat_id=user_chat_id)
            Archive.objects.create(type="message", content=for_admin, author=author)

            if response.status_code == 200:
                print("Audio sent successfully!")
            else:
                print(f"Failed to send audio: {response.status_code}")
                chunk = "❌Произошла ошибка, пожалуйста, введите текст на русском языке, ясно и понятно!❌"
                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                requests.post(url, data=payload)

        # Cleanup temporary files
        os.remove(myfile)

    except Exception as e:
        print(f"Error in translation or audio generation: {e}")

@shared_task
def ru_en_voiceToVoice(voice_file_path, chat_id, api_token, msg_id, sticker_file_id, voice_file_id, user_id):
    logging.info("Processing voice message...,")
    try:
        # Convert OGG file to WAV format
        audio = AudioSegment.from_file(voice_file_path)
        wav_path = f"{os.path.splitext(voice_file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Convert voice to text
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="ru-RU")

        # Translate text
        translator = Translator()
        translated_text = translator.translate(text, src="ru", dest="en").text

        # Generate audio file for translated text
        tts = gTTS(translated_text, lang="en")
        output_file = f"{os.path.splitext(voice_file_path)[0]}_translated.mp3"
        tts.save(output_file)

        # Send the audio file to Telegram
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇷🇺RU ➡️ EN🇺🇸</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            # After sending the message, delete the sticker
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_file_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # Save to archive
            author = TelegramProfile.objects.get(chat_id=user_id)
            Archive.objects.create(type="voice", content=voice_file_id, author=author)

        # Cleanup temporary files
        if os.path.exists(voice_file_path):
            os.remove(voice_file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)

        if response.status_code == 200:
            logging.info("Audio sent successfully!")
            return "Audio sent successfully!"
        else:
            logging.error(f"Failed to send audio: {response.status_code}")
            chunk = "❌Произошла ошибка, пожалуйста, введите текст на русском языке, ясно и понятно!❌"
            url = f"https://api.telegram.org/bot{api_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            requests.post(url, data=payload)
            return "Failed to send audio."

    except Exception as e:
        logging.error(f"Error processing voice message: {e}")
        return f"Error: {e}"


@shared_task
def ru_en_videoToVoice(file_path, chat_id, api_token, msg_id, user_chat_id, sticker_message_id, video_file_id, caption_of_video):
    wav_path = None  # Initial value

    # Check if caption_of_video is provided
    if caption_of_video is not None and caption_of_video.strip():
        if contains_cyrillic(caption_of_video):
            text = to_latin(caption_of_video)
        else:
            text = caption_of_video
    else:
        # Extract audio from video file
        audio = AudioSegment.from_file(file_path)
        wav_path = f"{os.path.splitext(file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Convert audio to text using speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language="ru-RU")
            except sr.UnknownValueError:
                return "Audio could not be understood."
            except sr.RequestError as e:
                return "Speech recognition service error."

    # Ensure the text is not empty
    if not text or text.strip() == "":
        return "Failed to extract valid text."

    # Translate text from Uzbek to English
    try:
        translator = Translator()
        translated_text = translator.translate(text, src="ru", dest="en").text
    except Exception as e:
        return "Translation failed."

    # Convert translated text to speech (TTS)
    try:
        tts = gTTS(translated_text, lang="en")
        output_file = f"{os.path.splitext(file_path)[0]}_translated.mp3"
        tts.save(output_file)
    except Exception as e:
        return "Text-to-speech conversion failed."

    # Send the voice message via Telegram
    try:
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇷🇺RU ➡️ EN🇺🇸</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

        if response.status_code == 200:
            pass
        else:
            chunk = "❌Произошла ошибка, пожалуйста, введите текст на русском языке, ясно и понятно!❌"
            url = f"https://api.telegram.org/bot{api_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            requests.post(url, data=payload)

    except Exception as e:
        return "Failed to send video audio."

    # Delete sticker message
    try:
        sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
        sticker_payload = {"chat_id": chat_id, "message_id": sticker_message_id}
        requests.post(sticker_url, data=sticker_payload)
    except Exception as e:
        pass

    # Save to archive
    try:
        author = TelegramProfile.objects.get(chat_id=user_chat_id)
        Archive.objects.create(type="video", content=video_file_id, author=author)
    except Exception as e:
        pass

    # Clean up files
    try:
        x = ['hello.mp4', 'hello_new.mp4']
        if file_path.endswith(".mp4") not in x:
            os.remove(file_path)
        if os.path.exists(f"{file_path}.mp4"):
            os.remove(f"{file_path}.mp4")
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)
    except Exception as e:
        pass

    return "Process completed successfully."

@shared_task
def ru_en_videoNoteToVoice(file_path, chat_id, api_token, msg_id, user_chat_id, video_note_file_id, sticker_message_id):
    """
    Video note faylni ovozga, matnga va tarjimaga aylantirish.
    """
    try:
        # Video note fayldan audio qismini ajratib olish va WAV formatiga aylantirish
        audio = AudioSegment.from_file(file_path)
        wav_path = f"{os.path.splitext(file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Audio ovozini matnga aylantirish
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="ru-RU")

        # Matnni tarjima qilish
        translator = Translator()
        translated_text = translator.translate(text, src="ru", dest="en").text

        # Tarjima natijasini ovozli xabarga aylantirish
        tts = gTTS(translated_text, lang="en")
        output_file = f"{os.path.splitext(file_path)[0]}_translated.mp3"
        tts.save(output_file)

        # Telegram orqali ovozli faylni yuborish
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇷🇺RU ➡️ EN🏴󠁧󠁢󠁥󠁮󠁧󠁿</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # archivega saqlab olish
            author = TelegramProfile.objects.get(chat_id=user_chat_id)
            Archive.objects.create(type="video_note", content=video_note_file_id, author=author)


        # Fayllarni o‘chirish
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)

        if response.status_code == 200:
            logging.info("Video note audio sent successfully!")
            return "Video note audio sent successfully!"
        else:
            logging.error(f"Failed to send video note audio: {response.status_code}")
            chunk = "❌Произошла ошибка, пожалуйста, введите текст на русском языке, ясно и понятно!❌"
            url = f"https://api.telegram.org/bot{api_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            requests.post(url, data=payload)
            return "Failed to send video note audio."

    except Exception as e:
        logging.error(f"Error processing video note message: {e}")
        return f"Error: {e}"


@shared_task
def ru_en_audioToVoice(file_path, chat_id, api_token, msg_id, user_chat_id, sticker_message_id, audio_file_id):
    try:
        # OGG faylni WAV formatiga o‘tkazish va Mono formatga keltirish
        audio = AudioSegment.from_file(file_path).set_channels(1).set_frame_rate(16000)
        wav_path = f"{os.path.splitext(file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Audio faylni bo‘laklarga bo‘lish
        chunks = silence.split_on_silence(audio, min_silence_len=500, silence_thresh=-40)

        if not chunks:
            raise ValueError("Audio faylda yetarli ovoz topilmadi.")

        # Har bir bo‘lakni matnga aylantirish va tarjima qilish
        full_text = ""
        recognizer = sr.Recognizer()

        for i, chunk in enumerate(chunks):
            chunk_path = f"{os.path.splitext(wav_path)[0]}_chunk{i}.wav"
            chunk.export(chunk_path, format="wav")

            with sr.AudioFile(chunk_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language="ru-RU")
                full_text += f"{text} "

            # Faylni vaqtinchalik o‘chirib tashlash
            if os.path.exists(chunk_path):
                os.remove(chunk_path)

        # Matnni tarjima qilish
        translator = Translator()
        translated_text = translator.translate(full_text.strip(), src="ru", dest="en").text

        # Tarjima natijasini ovozli xabarga aylantirish
        tts = gTTS(translated_text, lang="en")
        output_file = f"{os.path.splitext(file_path)[0]}_translated.mp3"
        tts.save(output_file)

        # Telegram orqali ovozli faylni yuborish
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇷🇺RU ➡️ EN🇺🇸</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            # Stickerni o‘chirish
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # Arxivga saqlash
            author = TelegramProfile.objects.get(chat_id=user_chat_id)
            Archive.objects.create(type="audio", content=audio_file_id, author=author)

        # Fayllarni o‘chirish
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)

        if response.status_code == 200:
            logging.info("Audio voice sent successfully!")
            return "Audio voice sent successfully!"
        else:
            raise Exception("Failed to send audio voice.")

    except sr.RequestError:
        send_error_message(chat_id, api_token, msg_id, "Google API bilan bog'lanishda xatolik yuz berdi.")
    except sr.UnknownValueError:
        send_error_message(chat_id, api_token, msg_id, "Audio matn o‘qib bo‘lmadi. Tushunarliroq audio jo‘nating.")
    except Exception as e:
        send_error_message(chat_id, api_token, msg_id, str(e))

@shared_task
def ru_en_photoToVoice(api_token, caption, chat_id, user_id, text_of_img, sticker_message_id, msg_id_for_reply):

    if caption:
        message_text_base = caption
    else:
        message_text_base = text_of_img

    for_admin = message_text_base
    if contains_cyrillic(message_text_base):  # Agar Kirill matni bo'lsa
        message_text = to_latin(message_text_base)  # Lotinga o'girish
    else:
        message_text = message_text_base

    translator = Translator()
    try:
        # Translate text
        translated_text = translator.translate(message_text, src='ru', dest='en').text

        # Generate audio file
        tts = gTTS(translated_text, lang="en")
        myfile = "voice_message.mp3"
        tts.save(myfile)

        # Send the audio file to Telegram
        with open(myfile, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id_for_reply
            }
            files = {
                "voice": audio_file
            }
            response = requests.post(url, data=payload, files=files)

            # >

            max_length = 4096
            text = f"<b>🇷🇺RU ➡️ EN🏴󠁧󠁢󠁥󠁮󠁧󠁿</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id_for_reply
                }
                response = requests.post(url, data=payload)

            # xabar yuborilgandan keyin sticker o'chib ketishi
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # archivega saqlab olish
            author = TelegramProfile.objects.get(chat_id=user_id)
            Archive.objects.create(type="message", content=for_admin, author=author)

            if response.status_code == 200:
                print("Audio sent successfully!")
            else:
                print(f"Failed to send audio: {response.status_code}")
                chunk = "❌Произошла ошибка, пожалуйста, введите текст на русском языке, ясно и понятно!❌"
                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id_for_reply
                }
                requests.post(url, data=payload)
        os.remove(myfile)
    except Exception as e:
        print("Error:", e)


# RU UZ CELERY TASKS
@shared_task
def ru_uz_messageToVoice(message_text_base, chat_id, api_token, msg_id, sticker_message_id, user_chat_id):
    for_admin = message_text_base
    if contains_cyrillic(message_text_base):  # Agar Kirill matni bo'lsa
        message_text = to_latin(message_text_base)  # Lotinga o'girish
    else:
        message_text = message_text_base

    translator = Translator()
    try:
        # Translate text
        translated_text = translator.translate(message_text, src='ru', dest='uz').text

        # Generate audio file
        tts = gTTS(translated_text, lang="tr")
        myfile = "voice_message.mp3"
        tts.save(myfile)

        # Send the audio file to Telegram
        with open(myfile, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {
                "voice": audio_file
            }
            response = requests.post(url, data=payload, files=files)

            # Send translated text in chunks if it's too long
            max_length = 4096
            text = f"<b>🇷🇺RU ➡️ UZ🇺🇿</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            # After sending the message, delete the sticker
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # Save the message to the archive
            author = TelegramProfile.objects.get(chat_id=user_chat_id)
            Archive.objects.create(type="message", content=for_admin, author=author)

            if response.status_code == 200:
                print("Audio sent successfully!")
            else:
                print(f"Failed to send audio: {response.status_code}")
                chunk = "❌Произошла ошибка, пожалуйста, введите текст на русском языке, ясно и понятно!❌"
                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                requests.post(url, data=payload)

        # Cleanup temporary files
        os.remove(myfile)

    except Exception as e:
        print(f"Error in translation or audio generation: {e}")

@shared_task
def ru_uz_voiceToVoice(voice_file_path, chat_id, api_token, msg_id, sticker_file_id, voice_file_id, user_id):
    logging.info("Processing voice message...,")
    try:
        # Convert OGG file to WAV format
        audio = AudioSegment.from_file(voice_file_path)
        wav_path = f"{os.path.splitext(voice_file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Convert voice to text
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="ru-RU")

        # Translate text
        translator = Translator()
        translated_text = translator.translate(text, src="ru", dest="uz").text

        # Generate audio file for translated text
        tts = gTTS(translated_text, lang="tr")
        output_file = f"{os.path.splitext(voice_file_path)[0]}_translated.mp3"
        tts.save(output_file)

        # Send the audio file to Telegram
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇷🇺RU ➡️ UZ🇺🇿</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            # After sending the message, delete the sticker
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_file_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # Save to archive
            author = TelegramProfile.objects.get(chat_id=user_id)
            Archive.objects.create(type="voice", content=voice_file_id, author=author)

        # Cleanup temporary files
        if os.path.exists(voice_file_path):
            os.remove(voice_file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)

        if response.status_code == 200:
            logging.info("Audio sent successfully!")
            return "Audio sent successfully!"
        else:
            logging.error(f"Failed to send audio: {response.status_code}")
            chunk = "❌Произошла ошибка, пожалуйста, введите текст на русском языке, ясно и понятно!❌"
            url = f"https://api.telegram.org/bot{api_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            requests.post(url, data=payload)
            return "Failed to send audio."

    except Exception as e:
        logging.error(f"Error processing voice message: {e}")
        return f"Error: {e}"


@shared_task
def ru_uz_videoToVoice(file_path, chat_id, api_token, msg_id, user_chat_id, sticker_message_id, video_file_id, caption_of_video):
    wav_path = None  # Initial value

    # Check if caption_of_video is provided
    if caption_of_video is not None and caption_of_video.strip():
        if contains_cyrillic(caption_of_video):
            text = to_latin(caption_of_video)
        else:
            text = caption_of_video
    else:
        # Extract audio from video file
        audio = AudioSegment.from_file(file_path)
        wav_path = f"{os.path.splitext(file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Convert audio to text using speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language="ru-RU")
            except sr.UnknownValueError:
                return "Audio could not be understood."
            except sr.RequestError as e:
                return "Speech recognition service error."

    # Ensure the text is not empty
    if not text or text.strip() == "":
        return "Failed to extract valid text."

    # Translate text from Uzbek to English
    try:
        translator = Translator()
        translated_text = translator.translate(text, src="ru", dest="uz").text
    except Exception as e:
        return "Translation failed."

    # Convert translated text to speech (TTS)
    try:
        tts = gTTS(translated_text, lang="tr")
        output_file = f"{os.path.splitext(file_path)[0]}_translated.mp3"
        tts.save(output_file)
    except Exception as e:
        return "Text-to-speech conversion failed."

    # Send the voice message via Telegram
    try:
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇷🇺RU ➡️ UZ🇺🇿</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

        if response.status_code == 200:
            pass
        else:
            chunk = "❌Произошла ошибка, пожалуйста, введите текст на русском языке, ясно и понятно!❌"
            url = f"https://api.telegram.org/bot{api_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            requests.post(url, data=payload)

    except Exception as e:
        return "Failed to send video audio."

    # Delete sticker message
    try:
        sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
        sticker_payload = {"chat_id": chat_id, "message_id": sticker_message_id}
        requests.post(sticker_url, data=sticker_payload)
    except Exception as e:
        pass

    # Save to archive
    try:
        author = TelegramProfile.objects.get(chat_id=user_chat_id)
        Archive.objects.create(type="video", content=video_file_id, author=author)
    except Exception as e:
        pass

    # Clean up files
    try:
        x = ['hello.mp4', 'hello_new.mp4']
        if file_path.endswith(".mp4") not in x:
            os.remove(file_path)
        if os.path.exists(f"{file_path}.mp4"):
            os.remove(f"{file_path}.mp4")
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)
    except Exception as e:
        pass

    return "Process completed successfully."

@shared_task
def ru_uz_videoNoteToVoice(file_path, chat_id, api_token, msg_id, user_chat_id, video_note_file_id, sticker_message_id):
    """
    Video note faylni ovozga, matnga va tarjimaga aylantirish.
    """
    try:
        # Video note fayldan audio qismini ajratib olish va WAV formatiga aylantirish
        audio = AudioSegment.from_file(file_path)
        wav_path = f"{os.path.splitext(file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Audio ovozini matnga aylantirish
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="ru-RU")

        # Matnni tarjima qilish
        translator = Translator()
        translated_text = translator.translate(text, src="ru", dest="uz").text

        # Tarjima natijasini ovozli xabarga aylantirish
        tts = gTTS(translated_text, lang="tr")
        output_file = f"{os.path.splitext(file_path)[0]}_translated.mp3"
        tts.save(output_file)

        # Telegram orqali ovozli faylni yuborish
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇷🇺RU ➡️ UZ🇺🇿</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # archivega saqlab olish
            author = TelegramProfile.objects.get(chat_id=user_chat_id)
            Archive.objects.create(type="video_note", content=video_note_file_id, author=author)


        # Fayllarni o‘chirish
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)

        if response.status_code == 200:
            logging.info("Video note audio sent successfully!")
            return "Video note audio sent successfully!"
        else:
            logging.error(f"Failed to send video note audio: {response.status_code}")
            chunk = "❌Произошла ошибка, пожалуйста, введите текст на русском языке, ясно и понятно!❌"
            url = f"https://api.telegram.org/bot{api_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "reply_to_message_id": msg_id
            }
            requests.post(url, data=payload)
            return "Failed to send video note audio."

    except Exception as e:
        logging.error(f"Error processing video note message: {e}")
        return f"Error: {e}"


@shared_task
def ru_uz_audioToVoice(file_path, chat_id, api_token, msg_id, user_chat_id, sticker_message_id, audio_file_id):
    try:
        # OGG faylni WAV formatiga o‘tkazish va Mono formatga keltirish
        audio = AudioSegment.from_file(file_path).set_channels(1).set_frame_rate(16000)
        wav_path = f"{os.path.splitext(file_path)[0]}.wav"
        audio.export(wav_path, format="wav")

        # Audio faylni bo‘laklarga bo‘lish
        chunks = silence.split_on_silence(audio, min_silence_len=500, silence_thresh=-40)

        if not chunks:
            raise ValueError("Audio faylda yetarli ovoz topilmadi.")

        # Har bir bo‘lakni matnga aylantirish va tarjima qilish
        full_text = ""
        recognizer = sr.Recognizer()

        for i, chunk in enumerate(chunks):
            chunk_path = f"{os.path.splitext(wav_path)[0]}_chunk{i}.wav"
            chunk.export(chunk_path, format="wav")

            with sr.AudioFile(chunk_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language="ru-RU")
                full_text += f"{text} "

            # Faylni vaqtinchalik o‘chirib tashlash
            if os.path.exists(chunk_path):
                os.remove(chunk_path)

        # Matnni tarjima qilish
        translator = Translator()
        translated_text = translator.translate(full_text.strip(), src="ru", dest="uz").text

        # Tarjima natijasini ovozli xabarga aylantirish
        tts = gTTS(translated_text, lang="tr")
        output_file = f"{os.path.splitext(file_path)[0]}_translated.mp3"
        tts.save(output_file)

        # Telegram orqali ovozli faylni yuborish
        with open(output_file, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id
            }
            files = {"voice": audio_file}
            response = requests.post(url, data=payload, files=files)

            max_length = 4096
            text = f"<b>🇷🇺RU ➡️ UZ🇺🇿</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id
                }
                response = requests.post(url, data=payload)

            # Stickerni o‘chirish
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # Arxivga saqlash
            author = TelegramProfile.objects.get(chat_id=user_chat_id)
            Archive.objects.create(type="audio", content=audio_file_id, author=author)

        # Fayllarni o‘chirish
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(output_file):
            os.remove(output_file)

        if response.status_code == 200:
            logging.info("Audio voice sent successfully!")
            return "Audio voice sent successfully!"
        else:
            raise Exception("Failed to send audio voice.")

    except sr.RequestError:
        send_error_message(chat_id, api_token, msg_id, "Google API bilan bog'lanishda xatolik yuz berdi.")
    except sr.UnknownValueError:
        send_error_message(chat_id, api_token, msg_id, "Audio matn o‘qib bo‘lmadi. Tushunarliroq audio jo‘nating.")
    except Exception as e:
        send_error_message(chat_id, api_token, msg_id, str(e))

@shared_task
def ru_uz_photoToVoice(api_token, caption, chat_id, user_id, text_of_img, sticker_message_id, msg_id_for_reply):

    if caption:
        message_text_base = caption
    else:
        message_text_base = text_of_img

    for_admin = message_text_base
    if contains_cyrillic(message_text_base):  # Agar Kirill matni bo'lsa
        message_text = to_latin(message_text_base)  # Lotinga o'girish
    else:
        message_text = message_text_base

    translator = Translator()
    try:
        # Translate text
        translated_text = translator.translate(message_text, src='ru', dest='uz').text

        # Generate audio file
        tts = gTTS(translated_text, lang="tr")
        myfile = "voice_message.mp3"
        tts.save(myfile)

        # Send the audio file to Telegram
        with open(myfile, 'rb') as audio_file:
            url = f"https://api.telegram.org/bot{api_token}/sendVoice"
            payload = {
                "chat_id": chat_id,
                "reply_to_message_id": msg_id_for_reply
            }
            files = {
                "voice": audio_file
            }
            response = requests.post(url, data=payload, files=files)

            # >

            max_length = 4096
            text = f"<b>🇷🇺RU ➡️ UZ🇺🇿</b>\n\n{translated_text}"
            for i in range(0, len(text), max_length):
                chunk = text[i:i + max_length]

                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id_for_reply
                }
                response = requests.post(url, data=payload)

            # xabar yuborilgandan keyin sticker o'chib ketishi
            sticker_url = f"https://api.telegram.org/bot{api_token}/deleteMessage"
            sticker_payload = {
                "chat_id": chat_id,
                "message_id": sticker_message_id
            }
            requests.post(sticker_url, data=sticker_payload)

            # archivega saqlab olish
            author = TelegramProfile.objects.get(chat_id=user_id)
            Archive.objects.create(type="message", content=for_admin, author=author)

            if response.status_code == 200:
                print("Audio sent successfully!")
            else:
                print(f"Failed to send audio: {response.status_code}")
                chunk = "❌Произошла ошибка, пожалуйста, введите текст на русском языке, ясно и понятно!❌"
                url = f"https://api.telegram.org/bot{api_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "reply_to_message_id": msg_id_for_reply
                }
                requests.post(url, data=payload)
        os.remove(myfile)
    except Exception as e:
        print("Error:", e)















