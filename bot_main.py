import asyncio
import os

from aiogram.enums import ParseMode
import logging
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram import F
from aiogram.utils.formatting import (Bold, as_list, as_marked_section)
from victory_handler import router
from data import answers
from aiogram.types import ReplyKeyboardRemove
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


TOKEN = os.getenv('TOKEN')
dp = Dispatcher()
dp.include_router(router)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    kb = [
        [
            types.KeyboardButton(text="Команды"),
            types.KeyboardButton(text="Контакты"),
            types.KeyboardButton(text="Описание бота"),
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
    )

    kb_inline = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Да", callback_data="victory")]])

    await message.answer(
        f"Привет *{message.from_user.full_name}!* Рад видеть! У меня есть для тебя увлекательная игра. Давай \
проверим, какое татемное животное сответствует твоему характеру! Просто отвечай на мои вопросы, и мы узнаем \
какой зверь подходит тебе, а может быть и птица, но не будем загадывать. Готов начать приключение?☺",
        parse_mode=ParseMode.MARKDOWN, reply_markup=kb_inline
    )
    await message.answer("Или можешь ознакомиться с моими функциями и командами подробнее☺", reply_markup=keyboard)


@dp.message(F.text.lower() == "описание бота")
async def description_button(message: types.Message):
    await description_command(message)


@dp.message(F.text.lower() == "контакты")
async def contact_button(message: types.Message):
    await contact_command(message)


@dp.message((F.text.lower() == "/description" or F.text.lower() == "описание бота"))
async def description_command(message: types.Message):
    if message.text.lower() == "/description":
        await message.answer(
            "Это бот-викторина, помогающая пользователю подобрать тотемное животное в формате развлечения. \
            А также рассказать посетителям канала о программе опеки",
            reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Это бот-викторина, помогающая пользователю подобрать тотемное животное в формате \
развлечения. \nА также рассказать посетителям канала о программе опеки.")


@dp.message(F.text.lower() == "/contact" or F.text.lower() == "контакты")
async def contact_command(message: types.Message):
    if message.text.lower() == "/contact":
        await message.answer(
            "Если у вас возникли вопросы вы можете\nсвязаться с нами:\nE-mail: bac9.91@mail.ru\n"
            "Телефон: 8(999)960-05-80\nУзнать подробнее о программе опеки по адресу:\n"
            "https://www.moscowzoo.ru/my-zoo/become-a-guardian/",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer("Если у вас возникли вопросы вы можете\nсвязаться с нами:\nE-mail: bac9.91@mail.ru\n"
                             "Телефон: 8(999)960-05-80\nУзнать подробнее о программе опеки по адресу:\n"
                             "https://www.moscowzoo.ru/my-zoo/become-a-guardian/")


@dp.message(F.text.lower() == "/feedback")
async def send_feedback_request(message: types.Message):
    await message.answer(
        'Пожалуйста, отправьте ваш отзыв о боте\nВ формате "/feedback - ваш отзыв ".',
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message(F.text.lower() == "команды")
async def commands(message: types.Message):
    response = as_list(
        as_marked_section(
            Bold("Команды:"),
            "/victory - запуск викторины",
                "/contact - контактная информация",
                "/description - описание бота",
                "/feedback - оставить отзыв",
            marker="✅ ",
        ),
    )
    await message.answer(
        **response.as_kwargs()
    )


@dp.message(
    ~F.text.in_(answers), ~F.text.lower().startswith("/feedback"),
    ~F.text.lower().startswith("/start"), ~F.text.lower().startswith("/contact"),
    ~F.text.lower().startswith("/description"), ~F.text.lower().startswith("/victory")
)
async def handle_invalid_message(message: types.Message):
    await message.answer("Простите, я не понимаю вашего сообщения. Пожалуйста, используйте доступные команды.")


async def main() -> None:
    bot = Bot(TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
