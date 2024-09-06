import os
import random
import smtplib
from email.message import EmailMessage
from typing import Type
from dotenv import load_dotenv

from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram import Router, types, F
from data import questions, responses, weights, description_animals, animals
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup

load_dotenv()
router = Router()
user_answers = {}


@router.message(Command("victory"))
async def victory_question(message: types.Message, state=FSMContext):
    current_question_key = (list(questions.keys())[0])
    await state.set_state(current_question_key)
    await message.answer(responses["start"])
    await ask_question(message, questions["Q1"])


@router.callback_query(lambda query: query.data == "victory")
async def start_victory_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.delete()
    current_question_key = (list(questions.keys())[0])
    await state.set_state(current_question_key)
    await callback_query.message.answer(responses["start"])
    await ask_question(callback_query.message, questions["Q1"])


@router.message(Command("feedback"))
async def handle_feedback(message: types.Message):
    if message.content_type == types.ContentType.TEXT:
        feed = message.text[len("/feedback"):].strip()
        user_id = message.from_user.id
        user_name = message.from_user.full_name

        await save_feedback_to_file(user_id, user_name, feed)
        await message.answer("Спасибо за ваш отзыв!")
    else:
        await message.answer("Пожалуйста, отправьте текстовое сообщение после команды /feedback.")


async def save_feedback_to_file(user_id: int, user_name: str, feedback: str):
    with open('feedback.txt', 'a', encoding='utf-8') as file:
        file.write(f"User ID: {user_id}, User name: {user_name}, Feedback: {feedback}\n")


async def ask_question(message: types.Message, question_text: str):
    kb = [[types.KeyboardButton(text="Да"), types.KeyboardButton(text="Возможно"), types.KeyboardButton(text="Нет")]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(question_text, reply_markup=keyboard)


@router.message(lambda message: message.text in ["Да", "Возможно", "Нет"])
async def answer_question_and_send_result(message: types.Message, state: FSMContext):
    current_question_key = await state.get_state()
    user_answer = message.text
    user_answers[current_question_key] = user_answer
    next_question_key = f"Q{int(current_question_key[1:]) + 1}"

    if next_question_key in questions:
        await state.set_state(next_question_key)
        await message.answer(responses[next_question_key])
        await ask_question(message, questions[next_question_key])
    else:
        result_message = await analyze_answers(state)
        await send_result(message, state)
        await guarding(message)
        user_name = message.from_user.full_name
        await send_email(user_name, animals[f"{result_message}"])


async def analyze_answers(state: FSMContext):
    def analyze(answers):
        return {animal: weight_fn(answers) for animal, weight_fn in weights.items()}

    result = analyze(user_answers)
    print(result)
    sorted_result = {k: v for k, v in sorted(result.items(), key=lambda item: item[1], reverse=True)}
    max_weight = max(sorted_result.values())
    max_weight_animals = [animal for animal, weight in sorted_result.items() if weight == max_weight]
    selected_animal = random.choice(max_weight_animals)
    await state.set_data({'selected_animal': selected_animal})
    return selected_animal


@router.message(lambda message: message.text.lower() in ["конечно", "может быть позже"])
async def guarding(message: types.Message):
    if message.text.lower() == "конечно":
        current_directory = os.getcwd()
        video_path = os.path.join(current_directory, "video", "опека.mp4")
        await message.answer_video(video=types.FSInputFile(video_path), reply_markup=ReplyKeyboardRemove())
    elif message.text.lower() == "может быть позже":
        await message.answer("Спасибо, что приняли участие☺", reply_markup=ReplyKeyboardRemove())


@router.message(F.text.lower() == "попробовать ещё раз?")
async def restart_victory(message: types.Message, state: Type[FSMContext]):
    await victory_question(message, state)


@router.callback_query(lambda query: query.data == "share")
async def share_results(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_animal = data.get('selected_animal')
    photo_animals_path = os.path.join(os.getcwd(), "photo_animals", f"{selected_animal}.jpg")
    share_message = f"Друзья я прошёл викторину! Моё тотемное животное: {animals[selected_animal]}.\
Присоединяйтесь к викторине в нашем боте: [https://t.me/ZooVictory_bot]."

    vk_share_link = f"https://vk.com/share.php?url=https://t.me/ZooVictory_bot&title={share_message}"

    await callback_query.answer()
    await callback_query.message.answer_photo(
        photo=types.FSInputFile(photo_animals_path),
        caption=share_message,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Поделиться", url=vk_share_link)]]),
    )


@router.message()
async def send_result(message: types.Message, state: FSMContext):
    data = await state.get_data()
    result_message = data.get('selected_animal')
    current_directory = os.getcwd()
    photo_animals_path = os.path.join(current_directory, "photo_animals", f"{result_message}.jpg")

    kb = [
        [types.KeyboardButton(text="Конечно"), types.KeyboardButton(text="Может быть позже")],
        [types.KeyboardButton(text="Попробовать ещё раз?")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    kb_inline = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Поделиться результатом",
                                                                            callback_data="share")]])

    caption = f"Поздравляю, это твой тотем☺! {description_animals[result_message]}\n\n"

    await message.answer_photo(
        caption=caption,
        photo=types.FSInputFile(photo_animals_path),
        reply_markup=kb_inline
    )
    await message.answer("Кстати, ты можешь стать его опекуном, хочешь узнать больше?", reply_markup=keyboard)


@router.message()
async def send_email(user_name, selected_animal):
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = os.getenv('SMTP_PORT')
    email_login = os.getenv('EMAIL_LOGIN')
    email_password = os.getenv('EMAIL_PASSWORD')

    recipient_email = 'bac9.91@mail.ru'

    message = EmailMessage()
    message['From'] = email_login
    message['To'] = recipient_email
    message['Subject'] = 'Результаты викторины'
    message_text = f'Пользователь: {user_name} - Тотемное животное: {selected_animal}'
    message.set_content(message_text)
    try:
        with smtplib.SMTP(smtp_host, int(smtp_port)) as smtp_server:
            smtp_server.starttls()
            smtp_server.login(email_login, email_password)
            smtp_server.send_message(message)
        print('Письмо успешно отправлено')
    except Exception as e:
        print('Ошибка при отправке письма:', e)
