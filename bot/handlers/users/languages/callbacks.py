from aiogram import types
from aiogram.fsm.context import FSMContext

from bot.keyboards.outline import switch_language, switch_language_en, switch_language_ru
from bot.states.main import TranslationStates




async def callback_uz_en(callback: types.CallbackQuery, state: FSMContext):
    matn = (f"<b>[UZ-EN]</b> Xabarlar ingliz tiliga tarjima qilinadi✅\n"
            f"Siz quyidagi xabarlarni tarjima qilishingiz mumkin⬇️: \n\n"
            f"📝matnli xabarlar ✅\n "
            f"🎙️audio xabarlar ✅\n "
            f"🖼️rasmli xabarlar ✅\n "
            f"🗣️ovozli xabarlar ✅\n"
            f"📹video xabarlar ✅\n"
            f"🔘aylana video xabarlar ✅\n\n"
            f"🔄Xabarni kiriting!🔄")
    await callback.message.answer(text=matn, parse_mode="HTML", reply_markup=await switch_language())
    await state.set_state(TranslationStates.uz_en)
    await callback.answer()

async def callback_uz_ru(callback: types.CallbackQuery, state: FSMContext):
    matn = (f"<b>[UZ-RU]</b> Xabarlar rus tiliga tarjima qilinadi✅\n"
            f"Siz quyidagi xabarlarni tarjima qilishingiz mumkin⬇️: \n\n"
            f"📝matnli xabarlar ✅\n "
            f"🎙️audio xabarlar ✅\n "
            f"🖼️rasmli xabarlar ✅\n "
            f"🗣️ovozli xabarlar ✅\n"
            f"📹video xabarlar ✅\n"
            f"🔘aylana video xabarlar ✅\n\n"
            f"🔄Xabarni kiriting!🔄")
    await callback.message.answer(text=matn, parse_mode="HTML", reply_markup=await switch_language())
    await state.set_state(TranslationStates.uz_ru)
    await callback.answer()

async def callback_en_ru(callback: types.CallbackQuery, state: FSMContext):
    message = (f"<b>[EN-RU]</b>Messages will be translated into russian✅\n"
               f"You can translate the following types of messages⬇️: \n\n"
               f"📝Text messages ✅\n"
               f"🎙️Audio messages ✅\n"
               f"🖼️Image messages ✅\n"
               f"🗣️Voice messages ✅\n"
               f"📹Video messages ✅\n"
               f"🔘Round video messages ✅\n\n"
               f"🔄Enter your message!🔄")
    await callback.message.answer(text=message, parse_mode="HTML", reply_markup=await switch_language_en())
    await state.set_state(TranslationStates.en_ru)
    await callback.answer()

async def callback_en_uz(callback: types.CallbackQuery, state: FSMContext):
    message = (f"<b>[EN-UZ]</b> Messages will be translated into uzbek✅\n"
               f"You can translate the following types of messages⬇️: \n\n"
               f"📝Text messages ✅\n"
               f"🎙️Audio messages ✅\n"
               f"🖼️Image messages ✅\n"
               f"🗣️Voice messages ✅\n"
               f"📹Video messages ✅\n"
               f"🔘Round video messages ✅\n\n"
               f"🔄Enter your message!🔄")
    await callback.message.answer(text=message, parse_mode="HTML", reply_markup=await switch_language_en())
    await state.set_state(TranslationStates.en_uz)
    await callback.answer()

async def callback_ru_en(callback: types.CallbackQuery, state: FSMContext):
    message = (f"<b>[RU-EN]</b> Сообщения будут переведены на английский язык✅\n"
               f"Вы можете перевести следующие типы сообщений⬇️: \n\n"
               f"📝Текстовые сообщения ✅\n"
               f"🎙️Аудиосообщения ✅\n"
               f"🖼️Сообщения с изображениями ✅\n"
               f"🗣️Голосовые сообщения ✅\n"
               f"📹Видеосообщения ✅\n"
               f"🔘Круговые видеосообщения ✅\n\n"
               f"🔄Введите ваше сообщение!🔄")

    await callback.message.answer(text=message, parse_mode="HTML", reply_markup=await switch_language_ru())
    await state.set_state(TranslationStates.ru_en)
    await callback.answer()

async def callback_ru_uz(callback: types.CallbackQuery, state: FSMContext):
    message = (f"<b>[RU-UZ]</b> Сообщения будут переведены на узбекский язык✅\n"
               f"Вы можете перевести следующие типы сообщений⬇️: \n\n"
               f"📝Текстовые сообщения ✅\n"
               f"🎙️Аудиосообщения ✅\n"
               f"🖼️Сообщения с изображениями ✅\n"
               f"🗣️Голосовые сообщения ✅\n"
               f"📹Видеосообщения ✅\n"
               f"🔘Круговые видеосообщения ✅\n\n"
               f"🔄Введите ваше сообщение!🔄")

    await callback.message.answer(text=message, parse_mode="HTML", reply_markup=await switch_language_ru())
    await state.set_state(TranslationStates.ru_uz)
    await callback.answer()