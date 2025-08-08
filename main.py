import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN, ADMIN_ID
from handlers import router


async def main():
    """Главная функция запуска бота"""
    print("🤖 Бот запускается...")
    print(f"👨‍💼 ID администратора: {ADMIN_ID}")
    print("📝 ВАЖНО: Замените ADMIN_ID в config.py на свой Telegram ID!")

    # Создаем хранилище для состояний и инициализируем бота
    storage = MemoryStorage()
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=storage)

    # Подключаем роутер с обработчиками
    dp.include_router(router)

    print("🚀 Бот успешно запущен и готов к работе!")
    print("📱 Функции администратора:")
    print("   ✅ Просмотр всех записей")
    print("   ✅ Добавление записей")
    print("   ✅ Редактирование записей")
    print("   ✅ Удаление записей")
    print("   ✅ Статистика")
    print()
    print("👥 Функции для клиентов:")
    print("   ✅ Просмотр своих записей")
    print("   ✅ Запись на услуги")
    print("   ✅ Перенос записей")
    print("   ✅ Отмена записей")
    print("   ✅ Контакты и информация")
    print()
    print("📊 Ожидание сообщений...")

    # Запускаем бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())