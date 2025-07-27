"""Настройки и конфигурация приложения Digital Fortress"""

from pathlib import Path

# Основные настройки приложения
APP_CONFIG = {
    "APP_TITLE": "Digital Fortress",
    "DB_FILENAME": "fortress.db",
    "KDF_FILENAME": "fortress.kdf",
    "LOG_FILENAME": "app.log",
    "MIN_PASSWORD_LENGTH": 8,
    "MASTER_PASSWORD_LENGTH": 6,
    "PBKDF2_ITERATIONS": 100_000,
    "SALT_SIZE": 16,
    "DATA_KEY_SIZE": 32,
    "WINDOW_SIZE": {"width": 900, "height": 600},
    "LOGIN_WINDOW_SIZE": {"width": 460, "height": 280},
    "TOAST_DURATION": 1800,
    "WARNING_DURATION": 3500,
    "CONFIRM_BUTTONS": {
        "yes": "Да",
        "no": "Нет"
    },
    "COMMENT_LABEL_PAD": (8, 0),
    "COMMENT_FIELD_PAD": (4, 0),
}

# Пути к файлам
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / APP_CONFIG["DB_FILENAME"]
KDF_PATH = DATA_DIR / APP_CONFIG["KDF_FILENAME"]

# Создаем папку data если её нет
DATA_DIR.mkdir(exist_ok=True)

# Языковые настройки
LANG = {
    "RU": {
        "login": "Войти",
        "create_vault": "Создать хранилище",
        "success": "Успех",
        "vault_created": "Хранилище создано!",
        "error": "Ошибка",
        "wrong_password": "Неверный пароль.",
        "all_fields_required": "Все поля обязательны для заполнения.",
        "delete_confirm": "Вы точно хотите удалить запись?",
        "delete_title": "Подтвердите удаление",
        "security": "Безопасность",
        "password_length": f"Пароль должен быть не менее {APP_CONFIG['MIN_PASSWORD_LENGTH']} символов.",
        "menu": "Меню",
        "all_records": "Все записи",
        "new_record": "Новая запись",
        "service": "Сервис",
        "login_label": "Логин",
        "password": "Пароль",
        "save": "Сохранить",
        "delete": "Удалить",
        "edit": "Редактирование",
        "new_entry": "Новая запись",
        "search": "Поиск...",
        "password_manager": "Управление паролем",
        "app_title": APP_CONFIG["APP_TITLE"],
    }
}

# Текущий язык интерфейса
CURRENT_LANG = "RU"

def _(key: str) -> str:
    """Функция локализации текста"""
    return LANG[CURRENT_LANG][key]
