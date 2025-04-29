"""
    ╔════════════════════════════════════════════╗
    ║           handlers/request.py              ║
    ╚════════════════════════════════════════════╝
    
    Описание:
        Этот модуль содержит обработчики команд, связанных с запросами товаров
"""

import os
import pandas as pd
from pathlib import Path
import asyncio
from datetime import datetime
import json

from aiogram                   import types
from aiogram.fsm.context       import FSMContext
from aiogram.exceptions        import TelegramBadRequest
from aiogram.types             import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

from src.utils                 import logger
from src.states                import RequestStates
from src.services              import TextGenerator
from src.services              import RasaClient   
from src.utils                 import ExcelProcessor
from src.filters               import filter_only_auth


async def request_handler(message: types.Message, state: FSMContext):
    """
        Обработчик команды /request.
        Отображает пользователю список таблиц для выбора.
    """
    if not await filter_only_auth(message):
        return
    logger.info(f"Received request command from {message.from_user.id}")
    
    request_main_manu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖊️ Текстовый запрос", callback_data="request_text_menu")],
        [InlineKeyboardButton(text="📃 Файловый запрос",  callback_data="request_file_menu")],
        [InlineKeyboardButton(text="❌ Закрыть меню",     callback_data="request_close_menu")],
    ])
    
    sent_message = await message.answer(
        "📚 Пожалуйста, выберите формат поиска:",
        reply_markup=request_main_manu
    )
    await state.update_data(request_message_id=sent_message.message_id)


async def request_text_menu(callback: types.CallbackQuery, state: FSMContext):
    """
        Этот обработчик обрабатывает callback для вывода меню текстового запроса
    """
    if callback.data == "request_text_menu":
        logger.info(f"Get request menu command from {callback.from_user.id}")
        try:
            lists = callback.bot.dm.get_sheet_names()
            request_table_text = InlineKeyboardMarkup(
                inline_keyboard=
                [
                    [InlineKeyboardButton(text=sheet_name, callback_data=f"sheet_{sheet_name}")]
                    for sheet_name in lists
                ] + [
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="request_back_main_menu")]
                ]
            )

            await callback.message.edit_text("📚 Пожалуйста, выберите таблицу для поиска:")
            await callback.message.edit_reply_markup(reply_markup=request_table_text)
            await state.set_state(RequestStates.choosing_list)
            await callback.answer()
            
        except Exception as e:
            logger.exception(f"ERROR in request_text_menu FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {e}", show_alert=True)
            

async def tables_callback_handler(callback_query: types.CallbackQuery, state: FSMContext):
    """
        Обработчик выбора таблицы через inline-кнопку.
    """
    if callback_query.data.startswith("sheet_"):
        chosen_list = callback_query.data.split("_", 1)[1]
        logger.info(f"User selected list: {chosen_list}")

        # Клавиатура с приоритетом поиска
        priority_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Отменить", callback_data="cancel_")
            ]
        ])

        # Обновляем сообщение
        await callback_query.message.edit_text(
            f"✅ Выбрана категория: {chosen_list}\n\n"
            "📝 Теперь введите ваш поисковый запрос:",
            reply_markup=priority_keyboard
        )

        # Сохраняем выбор в состоянии
        await state.update_data(choosing_list=chosen_list)
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
    
    
async def receive_request(message: types.Message, state: FSMContext):
    """
    Обработчик ввода поискового запроса пользователем.
    Выполняет поиск в базе данных и отправляет ответ пользователю.
    """
    logger.info(f"Request received from {message.from_user.id}: {message.text}")

    user_data = await state.get_data()
    request_message_id = user_data.get("request_message_id")
    choosing_list = user_data.get("choosing_list")

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
    
    # Используем контекстный менеджер для RasaClient
    async with RasaClient() as rc:
        search_data = await rc.process_query(message.text)
        search_entity, search_intent, target_column = search_data

        if search_intent == 'search_by_artikul':
            search_entity = search_entity['artikul']
        elif search_intent == 'search_by_naimenovanie':
            search_entity = search_entity['naimenovanie']
        elif search_intent == 'search_by_description':
            search_entity = search_entity['description']
            
        distances, indices = message.bot.em.search(choosing_list, target_column, search_entity)

        if distances is not None and indices is not None:
            found_products = []
            
            for i, (distance, idx) in enumerate(zip(distances, indices), 1):
                product_data = message.bot.dm.get_table_data(choosing_list).iloc[idx]
                product_dict = product_data.to_dict()
                found_products.append(product_dict)
                print(product_dict)

            with pd.option_context('display.max_rows', None):
                result_df = pd.DataFrame(found_products)
            
            # Используем контекстный менеджер для TextGenerator
            async with TextGenerator() as text_generator:
                # Преобразуем DataFrame в более читаемый формат для LLM
                formatted_data = []
                for _, row in result_df.iterrows():
                    product_info = {
                        "Артикул": row.get("Артикул", ""),
                        "Наименование": row.get("Наименование", ""),
                        "Описание": row.get("Описание", ""),
                        "Цена": row.get("Цена", ""),
                        "Цена с НДС": row.get("Цена с НДС", ""),
                        "РРЦ": row.get("РРЦ", ""),
                        "Ед. изм.": row.get("Ед. изм.", ""),
                        "Кол-во листов": row.get("Кол-во листов", ""),
                        "Формат": row.get("Формат", ""),
                        "Класс": row.get("Класс", ""),
                        "Материал": row.get("Материал", ""),
                        "Карты, стенды, таблицы": row.get("Карты, стенды, таблицы", "")
                    }
                    formatted_data.append(product_info)
                
                # Преобразуем в JSON для лучшей читаемости
                formatted_json = json.dumps(formatted_data, ensure_ascii=False, indent=2)
                
                request_kb = InlineKeyboardMarkup(
                    inline_keyboard= [
                        [InlineKeyboardButton(text="📗 Сформировать файл-счет", callback_data="test1")],
                        [InlineKeyboardButton(text="📘 Сформировать файл-кп", callback_data="test2")]
                    ]
                )
                
                generated_text = await text_generator.generate_text(message.text, formatted_json)
                await message.answer(text=generated_text, reply_markup=request_kb)
        else:
            await message.answer("🔍 По вашему запросу ничего не найдено.")
            return


async def request_file_menu(callback: types.CallbackQuery, state: FSMContext):
    """
        Этот обработчик обрабатывает callback для файлового запроса
    """
    if callback.data == "request_file_menu":
        logger.info(f"Get request file command from {callback.from_user.id}")
        try:
            request_file_kb = InlineKeyboardMarkup(
                inline_keyboard= [
                    [InlineKeyboardButton(text="📩 Сформировать КП по вашему файлу", callback_data="request_from_file")],
                    [InlineKeyboardButton(text="📊 Получить формат запроса",         callback_data="request_get_example")],
                    [InlineKeyboardButton(text="⬅️ Назад",                           callback_data="request_back_main_menu")]
                ]
            )

            await callback.message.edit_text("📚 Пожалуйста, отправьте свою таблицу для формирования файла КП, в соответсвии с форматом:")
            await callback.message.edit_reply_markup(reply_markup=request_file_kb)
            await callback.answer()
            
        except Exception as e:
            logger.exception(f"ERROR in request_file_menu FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {e}", show_alert=True)


async def request_get_example(callback: types.CallbackQuery, state: FSMContext):
    """
        Этот обработчик обрабатывает callback для вывода примера для запроса
    """
    if callback.data == "request_get_example":
        logger.info(f"Get request get example menu from {callback.from_user.id}")
        try:
            example_file = FSInputFile("data/excel/example-format.xlsx")
            await callback.message.answer_document(
                document=example_file,
                caption="📊 Вот файл-пример для запроса в систему"
            )
            await callback.answer()
        except Exception as e:
            logger.exception(f"ERROR in admin_download_logs_callback_handler FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)




async def request_from_file(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "request_from_file":
        logger.info(f"Request excel-prfrom file by {callback.from_user.id}")
        try:
            await callback.message.answer("📎 Ожидаем Ваш Excel-файл (.xlsx) для расчета файла КП в соответсвии с нашими товарами")
            await state.set_state(RequestStates.waiting_for_file)
        except Exception as e:
            logger.exception(f"ERROR in request_from_file FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)
            
            
async def handle_request_excel_file(message: types.Message, state: FSMContext):
    logger.info(f"Get request excel by {message.from_user.id}")
    input_file = None
    output_file = None
    progress_message = None
    last_progress_text = None
    
    try:
        document = message.document
        if not document.file_name.endswith(".xlsx"):
            await message.reply("⚠️ Пожалуйста, отправьте файл в формате .xlsx")
            return

        # Создаем временную директорию для файлов
        temp_dir = Path("data/excel/requests_files")
        temp_dir.mkdir(exist_ok=True)

        # Генерируем уникальные имена файлов
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_file = temp_dir / f"input_{timestamp}_{document.file_name}"
        output_file = temp_dir / f"result_{timestamp}_{Path(document.file_name).stem}_РАСЧЕТ_КП.xlsx"
        
        # Отправляем сообщение о начале загрузки
        progress_message = await message.answer("⏳ Начинаю загрузку файла...")
        
        # Скачиваем файл
        await message.bot.download(document, destination=input_file)
        await progress_message.edit_text("✅ Файл загружен. Начинаю обработку...")

        # Функция для обновления прогресса
        async def update_progress(progress: float):
            nonlocal last_progress_text
            progress_text = f"⏳ Обработка файла: {int(progress * 100)}%"
            if progress < 0.3:
                progress_text += "\n🔍 Проверка формата файла..."
            elif progress < 0.8:
                progress_text += "\n📊 Поиск товаров в базе..."
            elif progress < 0.9:
                progress_text += "\n💾 Сохранение результатов..."
            else:
                progress_text += "\n✨ Применение форматирования..."
            
            # Обновляем сообщение только если текст изменился
            if progress_text != last_progress_text:
                try:
                    await progress_message.edit_text(progress_text)
                    last_progress_text = progress_text
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")

        # Обрабатываем файл
        processor = ExcelProcessor()
        processor.set_progress_callback(update_progress)
        
        try:
            success, error_message = await processor.process_file_async(str(input_file), str(output_file))
        except Exception as e:
            logger.exception("Error during file processing")
            success, error_message = False, str(e)

        if success:
            # Отправляем обработанный файл
            await progress_message.edit_text("✅ Файл успешно обработан. Отправляю результат...")
            
            # Отправляем файл и ждем завершения отправки
            sent_document = await message.answer_document(
                document=FSInputFile(output_file),
                caption="✅ Файл успешно обработан. Вот ваш расчет КП:"
            )
            
            # Ждем, пока файл будет полностью отправлен
            await asyncio.sleep(2)
        else:
            await progress_message.edit_text(f"❌ Ошибка при обработке файла: {error_message}")

        await state.clear()
    except Exception as e:     
        logger.exception(f"ERROR in handle_excel_file FOR user_id={message.from_user.id}")
        if progress_message:
            logger.exception(f"ERROR in handle_excel_file FOR user_id={message.from_user.id}")
        else:
            logger.exception(f"ERROR in handle_excel_file FOR user_id={message.from_user.id}")
    finally:
        # Удаляем временные файлы после небольшой задержки
        if input_file or output_file:
            # Даем время на освобождение файлов
            for attempt in range(5):  # Увеличиваем количество попыток
                try:
                    if input_file and input_file.exists():
                        try:
                            # Пробуем закрыть файл перед удалением
                            import gc
                            gc.collect()
                            await asyncio.sleep(1)
                            input_file.unlink()
                            logger.info(f"Successfully deleted input file: {input_file}")
                        except Exception as e:
                            logger.error(f"Error deleting input file (attempt {attempt + 1}): {e}")
                            await asyncio.sleep(2)  # Увеличиваем время ожидания между попытками
                    
                    if output_file and output_file.exists():
                        try:
                            # Пробуем закрыть файл перед удалением
                            import gc
                            gc.collect()
                            await asyncio.sleep(1)
                            output_file.unlink()
                            logger.info(f"Successfully deleted output file: {output_file}")
                        except Exception as e:
                            logger.error(f"Error deleting output file (attempt {attempt + 1}): {e}")
                            await asyncio.sleep(2)  # Увеличиваем время ожидания между попытками
                    
                    # Если оба файла успешно удалены, выходим из цикла
                    if (not input_file or not input_file.exists()) and (not output_file or not output_file.exists()):
                        break
                        
                except Exception as e:
                    logger.error(f"Error in cleanup attempt {attempt + 1}: {e}")
                    await asyncio.sleep(2)


async def request_back_main_menu(callback: types.CallbackQuery, state: FSMContext):
    """
        Этот обработчик обрабатывает callback для возврата в главное меню
    """
    if callback.data == "request_back_main_menu":
        logger.info(f"Get request back main menu from {callback.from_user.id}")
        try:
            request_main_manu = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🖊️ Текстовый запрос", callback_data="request_text_menu")],
                [InlineKeyboardButton(text="📃 Файловый запрос",  callback_data="request_file_menu")],
                [InlineKeyboardButton(text="❌ Закрыть меню",     callback_data="request_close_menu")],
            ])

            await callback.message.edit_text("📚 Пожалуйста, выберите формат поиска:")
            await callback.message.edit_reply_markup(reply_markup=request_main_manu)
            await callback.answer()
            
        except Exception as e:
            logger.exception(f"ERROR in request_file_menu FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {e}", show_alert=True)


async def request_close_menu(callback: types.CallbackQuery, state: FSMContext):
    """
        Этот обработчик обрабатывает callback для закрытия главного меню
    """
    if callback.data == "request_close_menu":
        logger.info(f"Get request close main menu from {callback.from_user.id}")
        try:
            await callback.message.delete()
            await callback.answer()
        except Exception as e:
            logger.exception(f"ERROR in request_close_menu FOR user_id={callback.from_user.id}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)
        



















