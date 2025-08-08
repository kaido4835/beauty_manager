import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN
from handlers import router


async def main():
    """Главная функция запуска бота"""
    print("🤖 Бот запускается...")

    # Создаем хранилище для состояний и инициализируем бота
    storage = MemoryStorage()
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=storage)

    # Подключаем роутер с обработчиками
    dp.include_router(router)

    print("🚀 Бот успешно запущен и готов к работе!")
    print("📱 Ожидание сообщений...")

    # Запускаем бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())