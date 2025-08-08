import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN, ADMIN_ID

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def check_config():
    """Проверка конфигурации перед запуском"""
    errors = []

    # Проверяем токен
    if not TOKEN or TOKEN == "YOUR_BOT_TOKEN_HERE":
        errors.append("❌ Не установлен TOKEN в config.py")

    # Проверяем ID администратора
    if not ADMIN_ID or ADMIN_ID == 123456789:
        errors.append("❌ Не установлен ADMIN_ID в config.py")

    return errors


async def main():
    """Главная функция запуска бота"""
    print("=" * 50)
    print("🤖 ЗАПУСК TELEGRAM БОТА ДЛЯ ЗАПИСИ")
    print("=" * 50)

    # Проверяем конфигурацию
    config_errors = check_config()
    if config_errors:
        print("\n⚠️ ОШИБКИ КОНФИГУРАЦИИ:")
        for error in config_errors:
            print(f"   {error}")
        print("\n📝 Отредактируйте файл config.py и перезапустите бота")
        return

    print(f"👨‍💼 ID администратора: {ADMIN_ID}")

    # Проверяем и инициализируем базу данных
    try:
        print("\n📊 ПРОВЕРКА БАЗЫ ДАННЫХ:")
        from database import check_database_integrity, get_database_info, cleanup_old_appointments

        if check_database_integrity():
            print("✅ База данных готова к работе")
            print(get_database_info())

            # Очищаем старые записи
            archived = cleanup_old_appointments(60)  # Архивируем записи старше 60 дней
            if archived > 0:
                print(f"🗂️ Архивировано {archived} старых записей")

        else:
            print("⚠️ Обнаружены проблемы с базой данных")
            print("🔧 Попытка автоматического исправления...")

    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        print(f"❌ Критическая ошибка БД: {e}")
        print("🛠️ Проверьте права доступа к файлу базы данных")
        return

    # Импортируем обработчики
    try:
        from handlers import router
        print("\n📡 ИНИЦИАЛИЗАЦИЯ ОБРАБОТЧИКОВ:")
        print("✅ Обработчики загружены")
    except ImportError as e:
        logger.error(f"Handlers import error: {e}")
        print(f"❌ Ошибка импорта обработчиков: {e}")
        return

    # Создаем бота и диспетчер
    try:
        print("\n🚀 ЗАПУСК БОТА:")
        storage = MemoryStorage()
        bot = Bot(token=TOKEN)
        dp = Dispatcher(storage=storage)

        # Подключаем роутер с обработчиками
        dp.include_router(router)

        # Проверяем подключение к Telegram API
        bot_info = await bot.get_me()
        print(f"✅ Подключение к Telegram API успешно")
        print(f"🤖 Имя бота: @{bot_info.username}")
        print(f"🆔 ID бота: {bot_info.id}")

    except Exception as e:
        logger.error(f"Bot initialization error: {e}")
        print(f"❌ Ошибка инициализации бота: {e}")
        print("🔍 Проверьте корректность TOKEN в config.py")
        return

    print("\n" + "=" * 50)
    print("🎯 БОТ УСПЕШНО ЗАПУЩЕН!")
    print("=" * 50)
    print("\n📋 ДОСТУПНЫЕ ФУНКЦИИ:")
    print("\n👨‍💼 Для администратора:")
    print("   📅 Просмотр всех записей")
    print("   ➕ Добавление новых записей")
    print("   ✏️ Редактирование записей")
    print("   🗑️ Удаление записей")
    print("   📊 Статистика и аналитика")
    print("   🔍 Поиск записей")

    print("\n👥 Для клиентов:")
    print("   📅 Просмотр своих записей")
    print("   ➕ Запись на услуги")
    print("   🔄 Перенос записей")
    print("   ❌ Отмена записей")
    print("   📞 Контактная информация")

    print(f"\n📱 Для начала работы отправьте команду /start боту")
    print(f"🔗 Ссылка на бота: https://t.me/{bot_info.username}")
    print("\n📊 Ожидание сообщений...")
    print("📝 Логи сохраняются в файл bot.log")
    print("⏹️ Для остановки нажмите Ctrl+C")
    print("\n" + "-" * 50)

    try:
        # Запускаем бота
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("\n\n⏹️ Получен сигнал остановки (Ctrl+C)")
        print("🔄 Завершение работы бота...")
    except Exception as e:
        logger.error(f"Bot polling error: {e}")
        print(f"❌ Ошибка при работе бота: {e}")
    finally:
        print("👋 Бот остановлен")
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)