import asyncio
import logging
import sys
import signal
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN, ADMIN_ID

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Глобальные переменные для graceful shutdown
bot = None
dp = None


def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    print(f"\n⏹️  Получен сигнал {signum}. Завершение работы...")
    if bot:
        asyncio.create_task(bot.session.close())
    sys.exit(0)


def check_config():
    """Проверка конфигурации перед запуском"""
    errors = []

    # Проверяем токен
    if not TOKEN or TOKEN == "YOUR_BOT_TOKEN_HERE" or len(TOKEN) < 45:
        errors.append("❌ Не установлен или некорректный TOKEN в config.py")

    # Проверяем ID администратора
    if not ADMIN_ID or ADMIN_ID == 123456789:
        errors.append("❌ Не установлен ADMIN_ID в config.py")

    return errors


async def init_database_safely():
    """Безопасная инициализация базы данных"""
    try:
        print("\n📊 ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ:")
        from database import init_database, check_database_integrity, get_database_info, cleanup_old_appointments

        # Инициализируем БД
        init_database()

        # Проверяем целостность
        if check_database_integrity():
            print("✅ База данных готова к работе")
            print(get_database_info())

            # Очищаем старые записи
            try:
                archived = cleanup_old_appointments(60)  # Архивируем записи старше 60 дней
                if archived > 0:
                    print(f"🗂️ Архивировано {archived} старых записей")
            except Exception as e:
                logger.warning(f"Не удалось очистить старые записи: {e}")

        else:
            print("⚠️ Обнаружены проблемы с базой данных")
            print("🔧 База данных была переинициализирована")

        return True

    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        print(f"❌ Критическая ошибка БД: {e}")
        print("🛠️ Попробуйте запустить reset_database.py для сброса БД")
        return False


async def cleanup_on_shutdown():
    """Очистка ресурсов при завершении работы"""
    global bot
    try:
        if bot:
            await bot.session.close()
            print("🔌 Соединения закрыты")

        # Закрываем соединения с БД
        from database import close_connection
        close_connection()
        print("💾 Соединения с БД закрыты")

    except Exception as e:
        logger.error(f"Ошибка при очистке ресурсов: {e}")


async def main():
    """Главная функция запуска бота"""
    global bot, dp

    # Устанавливаем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

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
        return False

    print(f"👨‍💼 ID администратора: {ADMIN_ID}")

    # Инициализируем базу данных
    if not await init_database_safely():
        return False

    # Импортируем обработчики
    try:
        from handlers import router
        print("\n📡 ИНИЦИАЛИЗАЦИЯ ОБРАБОТЧИКОВ:")
        print("✅ Обработчики загружены")
    except ImportError as e:
        logger.error(f"Handlers import error: {e}")
        print(f"❌ Ошибка импорта обработчиков: {e}")
        return False

    # Создаем бота и диспетчер
    try:
        print("\n🚀 ИНИЦИАЛИЗАЦИЯ БОТА:")
        storage = MemoryStorage()
        bot = Bot(token=TOKEN)
        dp = Dispatcher(storage=storage)

        # Подключаем роутер с обработчиками
        dp.include_router(router)

        # Проверяем подключение к Telegram API
        try:
            bot_info = await bot.get_me()
            print(f"✅ Подключение к Telegram API успешно")
            print(f"🤖 Имя бота: @{bot_info.username}")
            print(f"🆔 ID бота: {bot_info.id}")
        except Exception as api_error:
            logger.error(f"Telegram API error: {api_error}")
            print(f"❌ Ошибка подключения к Telegram API: {api_error}")
            print("🔍 Проверьте:")
            print("   - Корректность TOKEN в config.py")
            print("   - Подключение к интернету")
            print("   - Не заблокирован ли бот")
            await cleanup_on_shutdown()
            return False

    except Exception as e:
        logger.error(f"Bot initialization error: {e}")
        print(f"❌ Ошибка инициализации бота: {e}")
        return False

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
    except Exception as e:
        logger.error(f"Bot polling error: {e}")
        print(f"❌ Ошибка при работе бота: {e}")
    finally:
        print("🔄 Завершение работы бота...")
        await cleanup_on_shutdown()
        print("👋 Бот остановлен")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if not success:
            print("\n❌ Бот не смог запуститься из-за ошибок")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)