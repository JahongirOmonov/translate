from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

async def switch_language():
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Tilni almashtirish"),
                KeyboardButton(text="Adminga xabar yozish")
            ]
        ],
        resize_keyboard=True
    )
    return markup

async def switch_language_en():
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Change language"),
                KeyboardButton(text="Message to Admin")
            ]
        ],
        resize_keyboard=True
    )
    return markup

async def switch_language_ru():
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Сменить язык"),
                KeyboardButton(text="Написать администратору")
            ]
        ],
        resize_keyboard=True
    )
    return markup
from aiogram.fsm.context import FSMContext


# async def switch_language(state: FSMContext):
#     # Hozirgi holatni olish
#     current_state = await state.get_state()
#
#     # Statelarga qarab textlarni o'rnatish
#     if current_state in ["TranslationStates:uz_en", "TranslationStates:uz_ru"]:
#         button1_text = "Tilni almashtirish"
#         button2_text = "Adminga xabar yozish"
#     elif current_state in ["TranslationStates:en_uz", "TranslationStates:en_ru"]:
#         button1_text = "Change language"
#         button2_text = "Message to Admin"
#     elif current_state in ["TranslationStates:ru_uz", "TranslationStates:ru_en"]:
#         button1_text = "Сменить язык"
#         button2_text = "Написать администратору"
#     else:
#         # Default textlar
#         button1_text = "Tilni almashtirish"
#         button2_text = "Adminga xabar yozish"
#
#     # Klaviatura yaratish
#     markup = ReplyKeyboardMarkup(
#         keyboard=[
#             [
#                 KeyboardButton(text=button1_text),
#                 KeyboardButton(text=button2_text),
#             ]
#         ],
#         resize_keyboard=True
#     )
#     return markup
