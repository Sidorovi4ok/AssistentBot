from aiogram.types import Message

async def unknown_message_handler(message: Message):
    await message.answer("Я вас не понял 😕\nПопробуйте команду /help, чтобы узнать, что я умею.")