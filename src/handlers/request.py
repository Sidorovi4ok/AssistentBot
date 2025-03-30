
"""
request.py

Этот модуль содержит обработчики команд, связанных с запросами товаров.
Бот позволяет пользователям выбирать таблицу, приоритет поиска и находить товары по заданному запросу.
"""

# Импортируем необходимые модули
import requests
import pandas as pd

# Импортируем необходимые классы из библиотеки aiogram для обработки сообщений.
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Импортируем утилиты и менеджеры
from src.utils.logger import logger
from src.utils.manager import DataManager
from src.utils.search import VectorSearchManager
from src.utils.filters import filter_article_extract, filter_product_name


class RequestStates(StatesGroup):
    """Класс состояний FSM для управления процессом запроса."""
    choosing_list       = State()  # Выбор таблицы
    waiting_for_request = State()  # Ожидание ввода поискового запроса


async def request_handler(message: types.Message, state: FSMContext):
    """
    Обработчик команды /request.
    Отображает пользователю список таблиц для выбора.
    """
    logger.info(f"Received request command from {message.from_user.id}")

    data_manager = message.bot.data_manager
    lists = data_manager.get_sheet_names()

    # Создаем inline-клавиатуру с таблицами
    list_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=sheet_name, callback_data=f"sheet_{sheet_name}")]
            for sheet_name in lists
        ] + [
            [InlineKeyboardButton(text="Отменить", callback_data="cancel_")]
        ]
    )

    # Отправляем сообщение с выбором таблицы и сохраняем его ID
    sent_message = await message.answer(
        "📚 Пожалуйста, выберите таблицу для поиска:",
        reply_markup=list_keyboard
    )

    await state.set_state(RequestStates.choosing_list)
    await state.update_data(request_message_id=sent_message.message_id)


async def receive_request(message: types.Message, state: FSMContext):
    """
    Обработчик ввода поискового запроса пользователем.
    Выполняет поиск в базе данных и отправляет ответ пользователю.
    """
    logger.info(f"Request received from {message.from_user.id}: {message.text}")

    user_data = await state.get_data()
    request_message_id = user_data.get("request_message_id")
    choosing_list = user_data.get("choosing_list")
    priority = user_data.get("search_priority")

    data_manager = message.bot.data_manager
    data_frame = data_manager.get_table_data(choosing_list)

    # Убираем клавиатуру с выбора таблицы
    if request_message_id:
        try:
            await message.bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=request_message_id,
                reply_markup=None
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                logger.error(f"Error editing message: {e}")

    # Отправляем подтверждение
    await message.answer("✅ Запрос принят в обработку. Ожидайте ответа.")

    # Очищаем состояние
    await state.clear()

    # Создаем экземпляр поиска по векторным эмбеддингам
    vector_search = VectorSearchManager(data_manager, table_name=choosing_list, text_column=priority)

    search_query = filter_article_extract(message.text) if priority == "Артикул" else filter_product_name(message.text)
    logger.info(f"Запрос для эмбеддингов: {search_query}")

    # Выполняем поиск по запросу пользователя
    results, distances = vector_search.search(search_query, top_k=3)

    # Преобразуем результаты в JSON
    filtered_data = results.to_json(orient="records", force_ascii=False)

    # Запрос к API для генерации ответа
    url = "https://api.intelligence.io.solutions/api/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjcxZjA0YjZhLTIxMjQtNDI4MS1iMTkxLTUyMzAwN2JiYjk4NSIsImV4cCI6NDg5NjQ5MzM3NH0.QXE6r9Gbdkpv_fzI6lbgIG8uU8EkKpH3vMw-KK7enDimGsQWfrl6xdIT5MD0Lg_xUwGWyAdm5haLix_rf4mlcw",
    }

    data = {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [
            {
                "role": "system",
                "content": """Ты бот-ассистент для работы с товарами. Формат ответа ДОЛЖЕН СТРОГО СОБЛЮДАТЬСЯ:

                [Точный ответ на интересующий вопрос пользователя]

                [Название товара]

                [Информация]
                • Характеристики из данных
                • Наличие на складе
                • Цена и акции
                • Ключевые особенности

                [Рекомендации]
                • Предложения по сопутствующим товарам
                • Альтернативные варианты

                Если информации недостаточно — уточни запрос.""" +
                           f"Используй только предоставленные данные: {filtered_data}."
            },
            {
                "role": "user",
                "content": f"Запрос: {message.text}. Ответь строго в требуемом формате."
            }
        ],
    }


    response = requests.post(url, headers=headers, json=data)
    data = response.json()

    text = data['choices'][0]['message']['content']
    bot_text = text.split('</think>\n\n')[1]

    await message.answer(bot_text, parse_mode="Markdown")


async def tables_callback_handler(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик выбора таблицы через inline-кнопку.
    Запрашивает у пользователя критерий поиска (Артикул / Наименование).
    """
    if callback_query.data.startswith("sheet_"):
        chosen_list = callback_query.data.split("_", 1)[1]
        logger.info(f"User selected list: {chosen_list}")

        # Клавиатура с приоритетом поиска
        priority_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Артикул", callback_data="priority_Артикул"),
                InlineKeyboardButton(text="Наименование", callback_data="priority_Наименование")
            ],
            [
                InlineKeyboardButton(text="Отменить", callback_data="cancel_")
            ]
        ])

        # Обновляем сообщение
        await callback_query.message.edit_text(
            f"✅ Выбрана категория: {chosen_list}\n\n"
            "Пожалуйста, выберите поле для точного поиска:",
            reply_markup=priority_keyboard
        )

        # Сохраняем выбор в состоянии
        await state.update_data(choosing_list=chosen_list)
        await callback_query.answer()


async def search_priority_callback_handler(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик выбора приоритета поиска (Артикул / Наименование).
    Запрашивает у пользователя ввод поискового запроса.
    """
    if callback_query.data.startswith("priority_"):
        priority = callback_query.data.split("_", 1)[1]
        logger.info(f"Search priority selected: {priority}")

        # Обновляем сообщение
        await callback_query.message.edit_text(
            callback_query.message.text + f"\n\nВыбран приоритет поиска: {priority}\n\n"
                                          "📝 Теперь введите ваш поисковый запрос:",
            reply_markup=None
        )

        # Сохраняем приоритет поиска
        await state.update_data(search_priority=priority)
        await state.set_state(RequestStates.waiting_for_request)
        await callback_query.answer()


async def cancel_callback_handler(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик отмены через inline-кнопку.
    Очищает состояние и отменяет запрос.
    """
    if callback_query.data == "cancel_":
        logger.info(f"Cancel by {callback_query.from_user.id}")

        user_data = await state.get_data()
        request_message_id = user_data.get("request_message_id")

        try:
            if request_message_id:
                await callback_query.bot.edit_message_reply_markup(
                    chat_id=callback_query.message.chat.id,
                    message_id=request_message_id,
                    reply_markup=None
                )
        except TelegramBadRequest:
            pass

        await state.clear()
        await callback_query.message.edit_text("🚫 Запрос отменен. Возврат в главное меню")
        await callback_query.answer()
