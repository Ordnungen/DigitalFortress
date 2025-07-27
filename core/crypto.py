"""Модуль для работы с криптографией и шифрованием данных"""

import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from config.settings import APP_CONFIG, KDF_PATH


class CryptoManager:
    """Класс для управления криптографическими операциями"""

    def __init__(self):
        self.decrypted_key = None

    def get_derived_key(self, password: str, salt: bytes) -> bytes:
        """Получить производный ключ из пароля и соли"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=APP_CONFIG["PBKDF2_ITERATIONS"],
            backend=default_backend()
        )
        return kdf.derive(password.encode())

    def create_vault(self, password: str) -> None:
        """Создать новое хранилище с мастер-паролем"""
        # Генерируем соль и создаем мастер-ключ
        salt = os.urandom(APP_CONFIG["SALT_SIZE"])
        master_key = self.get_derived_key(password, salt)

        # Генерируем ключ для данных
        data_key = Fernet.generate_key()

        # Шифруем ключ данных мастер-ключом
        f = Fernet(base64.urlsafe_b64encode(master_key))
        encrypted_data_key = f.encrypt(data_key)

        # Сохраняем в файл
        with open(KDF_PATH, "wb") as f_out:
            f_out.write(salt)
            f_out.write(encrypted_data_key)

    def verify_password(self, password: str) -> bool:
        """Проверить мастер-пароль и получить ключ данных"""
        try:
            with open(KDF_PATH, "rb") as f:
                salt = f.read(APP_CONFIG["SALT_SIZE"])
                encrypted_data_key = f.read()

            # Получаем мастер-ключ
            master_key = self.get_derived_key(password, salt)
            f = Fernet(base64.urlsafe_b64encode(master_key))

            # Расшифровываем ключ данных
            self.decrypted_key = f.decrypt(encrypted_data_key)
            return True

        except (InvalidToken, FileNotFoundError, IndexError):
            return False

    def get_data_key(self) -> bytes:
        """Получить ключ для шифрования данных"""
        if self.decrypted_key is None:
            raise RuntimeError("Ключ шифрования не загружен. Войдите в систему.")
        return self.decrypted_key

    def encrypt_password(self, password: str) -> bytes:
        """Зашифровать пароль"""
        key = self.get_data_key()
        fernet = Fernet(key)
        return fernet.encrypt(password.encode())

    def decrypt_password(self, encrypted_password: bytes) -> str:
        """Расшифровать пароль"""
        key = self.get_data_key()
        fernet = Fernet(key)
        return fernet.decrypt(encrypted_password).decode('utf-8')


# Глобальный экземпляр менеджера криптографии
crypto_manager = CryptoManager()
