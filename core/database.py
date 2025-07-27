"""Модуль для работы с базой данных паролей"""

import sqlite3
from typing import List, Tuple, Optional

from config.settings import DB_PATH
from core.crypto import crypto_manager


class DatabaseManager:
    """Класс для управления базой данных паролей"""

    def __init__(self):
        self.setup_database()

    def setup_database(self, clear: bool = False) -> None:
        """Настроить базу данных и создать таблицы"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()

                # Создаем таблицу если её нет
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS credentials (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service TEXT NOT NULL UNIQUE,
                        login TEXT NOT NULL,
                        encrypted_password BLOB NOT NULL,
                        comment TEXT
                    )
                """)

                # Проверяем наличие колонки comment
                cursor.execute("PRAGMA table_info(credentials)")
                columns = [row[1] for row in cursor.fetchall()]
                if "comment" not in columns:
                    cursor.execute("ALTER TABLE credentials ADD COLUMN comment TEXT")

                # Очищаем если нужно
                if clear:
                    cursor.execute("DELETE FROM credentials")

                conn.commit()

        except Exception as e:
            raise RuntimeError(f"Ошибка настройки базы данных: {e}")

    def save_credential(self, service: str, login: str, password: str, comment: str = "", credential_id: Optional[int] = None) -> None:
        """Сохранить или обновить учетные данные"""
        encrypted_password = crypto_manager.encrypt_password(password)

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            if credential_id:
                # Обновляем существующую запись
                cursor.execute("""
                    UPDATE credentials SET service = ?, login = ?, encrypted_password = ?, comment = ?
                    WHERE id = ?
                """, (service, login, encrypted_password, comment, credential_id))
            else:
                # Создаем новую запись
                cursor.execute("""
                    INSERT INTO credentials (service, login, encrypted_password, comment)
                    VALUES (?, ?, ?, ?)
                """, (service, login, encrypted_password, comment))

            conn.commit()

    def get_credential(self, service: str) -> Optional[Tuple[int, str, str, str]]:
        """Получить учетные данные по имени сервиса"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, login, encrypted_password, comment
                FROM credentials WHERE service = ?
            """, (service,))
            result = cursor.fetchone()

            if result:
                credential_id, login, encrypted_password, comment = result
                decrypted_password = crypto_manager.decrypt_password(encrypted_password)
                return credential_id, login, decrypted_password, comment or ""

            return None

    def get_all_credentials(self) -> List[Tuple[str, str]]:
        """Получить список всех сервисов и логинов"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT service, login FROM credentials
                ORDER BY service COLLATE NOCASE ASC
            """)
            return cursor.fetchall()

    def delete_credential(self, credential_id: int) -> None:
        """Удалить учетные данные по ID"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM credentials WHERE id = ?", (credential_id,))
            conn.commit()

    def service_exists(self, service: str) -> bool:
        """Проверить существование сервиса в базе"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM credentials WHERE service = ?", (service,))
            return cursor.fetchone() is not None


# Глобальный экземпляр менеджера базы данных
db_manager = DatabaseManager()
