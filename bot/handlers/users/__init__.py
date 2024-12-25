from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ContentType
from bot import states
from bot.handlers.users.main import start, sms_for_admin, sms_received, echo, echo_video, \
    sms_for_banned_user, confirm_callback, change_language

from .languages.uz_en.uz_en_file import uz_en_message, uz_en_voice, \
uz_en_video, uz_en_video_note, uz_en_audio, uz_en_photo

from .languages.uz_ru.uz_ru_file import uz_ru_message, uz_ru_voice, uz_ru_video, uz_ru_video_note, uz_ru_audio, \
    uz_ru_photo

from .languages.en_ru.en_ru_file import en_ru_message, en_ru_voice, en_ru_video, en_ru_video_note, en_ru_audio, \
    en_ru_photo

from .languages.en_uz.en_uz_file import en_uz_message, en_uz_voice, en_uz_video, en_uz_video_note, en_uz_audio, \
    en_uz_photo

from .languages.ru_en.ru_en_file import ru_en_message, ru_en_voice, ru_en_video, ru_en_video_note, ru_en_audio, \
    ru_en_photo

from .languages.ru_uz.ru_uz_file import ru_uz_message, ru_uz_voice, ru_uz_video, ru_uz_video_note, ru_uz_audio, \
    ru_uz_photo
from .languages.callbacks import callback_uz_en, callback_uz_ru, callback_en_ru, callback_ru_en, callback_en_uz, \
    callback_ru_uz


def prepare_router() -> Router:

    router = Router()
    router.message.filter(F.chat.type == "private")
    # router.message.filter(mytest_handler, Command("test"))  <-- bu test edi. har ehtimolga qarshi qoldirildi.
    # router.callback_query.register(callbaq, F.data.startswith("button")) <-- bu ham.
    router.callback_query.register(confirm_callback, F.data == "confirm_channels")

    router.message.register(change_language, F.text == "Tilni almashtirish")
    router.message.register(change_language, F.text == "Change language")
    router.message.register(change_language, F.text == "Сменить язык")
    # sms for admin
    router.message.register(sms_received, states.main.SmsForAdmin.sms)
    router.message.register(sms_for_admin, F.text == "Adminga xabar yozish")
    router.message.register(sms_for_admin, F.text == "Message to Admin")
    router.message.register(sms_for_admin, F.text == "Написать администратору")
    router.message.register(sms_for_banned_user, Command("xabar"))

    #tillar callback inline
    router.callback_query.register(callback_uz_en, F.data == "uz_en")
    router.callback_query.register(callback_uz_ru, F.data == "uz_ru")
    router.callback_query.register(callback_en_ru, F.data == "en_ru")
    router.callback_query.register(callback_ru_en, F.data == "ru_en")
    router.callback_query.register(callback_en_uz, F.data == "en_uz")
    router.callback_query.register(callback_ru_uz, F.data == "ru_uz")

    #language state uz_en
    router.message.register(uz_en_voice, states.main.TranslationStates.uz_en, F.content_type == ContentType.VOICE)
    router.message.register(uz_en_video, states.main.TranslationStates.uz_en, F.content_type == ContentType.VIDEO)
    router.message.register(uz_en_video_note, states.main.TranslationStates.uz_en, F.content_type == ContentType.VIDEO_NOTE)
    router.message.register(uz_en_audio, states.main.TranslationStates.uz_en, F.content_type == ContentType.AUDIO)
    router.message.register(uz_en_photo, states.main.TranslationStates.uz_en, F.content_type == ContentType.PHOTO)
    router.message.register(uz_en_message, states.main.TranslationStates.uz_en)

    #language state uz_ru
    router.message.register(uz_ru_voice, states.main.TranslationStates.uz_ru, F.content_type == ContentType.VOICE)
    router.message.register(uz_ru_video, states.main.TranslationStates.uz_ru, F.content_type == ContentType.VIDEO)
    router.message.register(uz_ru_video_note, states.main.TranslationStates.uz_ru, F.content_type == ContentType.VIDEO_NOTE)
    router.message.register(uz_ru_audio, states.main.TranslationStates.uz_ru, F.content_type == ContentType.AUDIO)
    router.message.register(uz_ru_photo, states.main.TranslationStates.uz_ru, F.content_type == ContentType.PHOTO)
    router.message.register(uz_ru_message, states.main.TranslationStates.uz_ru)

    #language state en_ru
    router.message.register(en_ru_voice, states.main.TranslationStates.en_ru, F.content_type == ContentType.VOICE)
    router.message.register(en_ru_video, states.main.TranslationStates.en_ru, F.content_type == ContentType.VIDEO)
    router.message.register(en_ru_video_note, states.main.TranslationStates.en_ru, F.content_type == ContentType.VIDEO_NOTE)
    router.message.register(en_ru_audio, states.main.TranslationStates.en_ru, F.content_type == ContentType.AUDIO)
    router.message.register(en_ru_photo, states.main.TranslationStates.en_ru, F.content_type == ContentType.PHOTO)
    router.message.register(en_ru_message, states.main.TranslationStates.en_ru)

    #language state en_uz
    router.message.register(en_uz_voice, states.main.TranslationStates.en_uz, F.content_type == ContentType.VOICE)
    router.message.register(en_uz_video, states.main.TranslationStates.en_uz, F.content_type == ContentType.VIDEO)
    router.message.register(en_uz_video_note, states.main.TranslationStates.en_uz, F.content_type == ContentType.VIDEO_NOTE)
    router.message.register(en_uz_audio, states.main.TranslationStates.en_uz, F.content_type == ContentType.AUDIO)
    router.message.register(en_uz_photo, states.main.TranslationStates.en_uz, F.content_type == ContentType.PHOTO)
    router.message.register(en_uz_message, states.main.TranslationStates.en_uz)

    #language state ru_en
    router.message.register(ru_en_voice, states.main.TranslationStates.ru_en, F.content_type == ContentType.VOICE)
    router.message.register(ru_en_video, states.main.TranslationStates.ru_en, F.content_type == ContentType.VIDEO)
    router.message.register(ru_en_video_note, states.main.TranslationStates.ru_en, F.content_type == ContentType.VIDEO_NOTE)
    router.message.register(ru_en_audio, states.main.TranslationStates.ru_en, F.content_type == ContentType.AUDIO)
    router.message.register(ru_en_photo, states.main.TranslationStates.ru_en, F.content_type == ContentType.PHOTO)
    router.message.register(ru_en_message, states.main.TranslationStates.ru_en)

    #language state ru_uz
    router.message.register(ru_uz_voice, states.main.TranslationStates.ru_uz, F.content_type == ContentType.VOICE)
    router.message.register(ru_uz_video, states.main.TranslationStates.ru_uz, F.content_type == ContentType.VIDEO)
    router.message.register(ru_uz_video_note, states.main.TranslationStates.ru_uz, F.content_type == ContentType.VIDEO_NOTE)
    router.message.register(ru_uz_audio, states.main.TranslationStates.ru_uz, F.content_type == ContentType.AUDIO)
    router.message.register(ru_uz_photo, states.main.TranslationStates.ru_uz, F.content_type == ContentType.PHOTO)
    router.message.register(ru_uz_message, states.main.TranslationStates.ru_uz)



    router.message.register(start, Command("start"))
    # router.message.register(get_video_file_id, F.content_type==ContentType.VIDEO)


    # echo_photo

    # echo_video
    router.message.register(echo_video, F.content_type == ContentType.VIDEO)

    # echo
    router.message.register(echo)

    return router
