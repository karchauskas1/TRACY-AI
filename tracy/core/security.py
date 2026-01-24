"""
==============================================================================
SECURITY.PY - ШИФРОВАНИЕ И БЕЗОПАСНОСТЬ
==============================================================================

Модуль для безопасного хранения чувствительных данных:
- Шифрование OAuth токенов
- Генерация ключей шифрования
- Безопасное хранение credentials

ИСПОЛЬЗОВАНИЕ:
    from tracy.core.security import TokenEncryption

    encryption = TokenEncryption()
    encrypted = encryption.encrypt(oauth_token_json)
    decrypted = encryption.decrypt(encrypted)

ВАЖНО:
    Ключ шифрования должен быть в переменной окружения TOKEN_ENCRYPTION_KEY.
    Если ключ не задан, будет сгенерирован временный (не для production!).

==============================================================================
"""
import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
from typing import Optional

logger = logging.getLogger(__name__)

# Пытаемся импортировать cryptography, но не падаем если её нет
try:
    from cryptography.fernet import Fernet, InvalidToken
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    logger.warning(
        "cryptography не установлен. Шифрование токенов недоступно. "
        "Установите: pip install cryptography"
    )


class TokenEncryption:
    """
    Класс для шифрования/дешифрования OAuth токенов и других секретов.

    Использует Fernet (AES-128-CBC с HMAC-SHA256).
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Инициализация шифрования.

        Args:
            encryption_key: Base64-encoded ключ шифрования (32 bytes).
                           Если не задан, берётся из TOKEN_ENCRYPTION_KEY.
        """
        self._cipher: Optional['Fernet'] = None
        self._key: Optional[bytes] = None

        if not CRYPTOGRAPHY_AVAILABLE:
            logger.warning("Шифрование недоступно - cryptography не установлен")
            return

        # Получаем ключ
        key_source = encryption_key or os.getenv('TOKEN_ENCRYPTION_KEY')

        if key_source:
            try:
                # Ключ должен быть base64-encoded 32 bytes
                self._key = key_source.encode() if isinstance(key_source, str) else key_source
                self._cipher = Fernet(self._key)
                logger.info("TokenEncryption инициализирован с предоставленным ключом")
            except Exception as e:
                logger.error(f"Ошибка инициализации шифрования с ключом: {e}")
                self._generate_temporary_key()
        else:
            logger.warning(
                "TOKEN_ENCRYPTION_KEY не задан! "
                "Используется временный ключ - НЕ ДЛЯ PRODUCTION!"
            )
            self._generate_temporary_key()

    def _generate_temporary_key(self) -> None:
        """Генерация временного ключа (только для разработки)."""
        if not CRYPTOGRAPHY_AVAILABLE:
            return

        self._key = Fernet.generate_key()
        self._cipher = Fernet(self._key)
        logger.warning(f"Сгенерирован временный ключ. Добавьте в .env:\nTOKEN_ENCRYPTION_KEY={self._key.decode()}")

    @property
    def is_available(self) -> bool:
        """Доступно ли шифрование."""
        return self._cipher is not None

    def encrypt(self, plaintext: str) -> str:
        """
        Зашифровать строку.

        Args:
            plaintext: Исходная строка (например, JSON с токеном)

        Returns:
            Base64-encoded зашифрованная строка

        Raises:
            RuntimeError: Если шифрование недоступно
        """
        if not self.is_available:
            logger.error("Попытка шифрования без доступного шифровальщика")
            # Fallback: возвращаем как есть (небезопасно!)
            return plaintext

        try:
            encrypted = self._cipher.encrypt(plaintext.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"Ошибка шифрования: {e}")
            raise RuntimeError(f"Encryption failed: {e}")

    def decrypt(self, ciphertext: str) -> str:
        """
        Расшифровать строку.

        Args:
            ciphertext: Base64-encoded зашифрованная строка

        Returns:
            Расшифрованная строка

        Raises:
            RuntimeError: Если расшифровка не удалась
        """
        if not self.is_available:
            logger.error("Попытка расшифровки без доступного шифровальщика")
            # Fallback: возвращаем как есть (для совместимости со старыми токенами)
            return ciphertext

        try:
            decoded = base64.urlsafe_b64decode(ciphertext.encode('utf-8'))
            decrypted = self._cipher.decrypt(decoded)
            return decrypted.decode('utf-8')
        except InvalidToken:
            logger.warning("Невалидный токен - возможно, не зашифрован (legacy)")
            # Пробуем вернуть как есть для совместимости со старыми данными
            return ciphertext
        except Exception as e:
            logger.error(f"Ошибка расшифровки: {e}")
            # Возвращаем как есть для совместимости
            return ciphertext

    def encrypt_json(self, data: dict) -> str:
        """
        Зашифровать словарь как JSON.

        Args:
            data: Словарь для шифрования

        Returns:
            Зашифрованная строка
        """
        return self.encrypt(json.dumps(data, ensure_ascii=False))

    def decrypt_json(self, ciphertext: str) -> dict:
        """
        Расшифровать JSON в словарь.

        Args:
            ciphertext: Зашифрованная строка

        Returns:
            Расшифрованный словарь
        """
        plaintext = self.decrypt(ciphertext)
        try:
            return json.loads(plaintext)
        except json.JSONDecodeError:
            logger.error("Расшифрованные данные не являются валидным JSON")
            return {}

    @staticmethod
    def generate_key() -> str:
        """
        Сгенерировать новый ключ шифрования.

        Returns:
            Base64-encoded ключ для TOKEN_ENCRYPTION_KEY
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            raise RuntimeError("cryptography не установлен")
        return Fernet.generate_key().decode('utf-8')


class TelegramAuthVerifier:
    """
    Верификация данных авторизации Telegram Mini App.

    Проверяет подпись initData от Telegram WebApp.
    """

    def __init__(self, bot_token: str):
        """
        Args:
            bot_token: Токен Telegram бота
        """
        self.bot_token = bot_token
        # Создаём секретный ключ из токена бота
        self._secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256
        ).digest()

    def verify_init_data(self, init_data: str) -> Optional[dict]:
        """
        Верифицировать initData от Telegram Mini App.

        Args:
            init_data: URL-encoded строка initData от Telegram

        Returns:
            Распарсенные данные если верификация успешна, иначе None
        """
        from urllib.parse import parse_qs, unquote

        try:
            # Парсим данные
            parsed = parse_qs(init_data)
            received_hash = parsed.get('hash', [None])[0]

            if not received_hash:
                logger.warning("initData не содержит hash")
                return None

            # Собираем строку для проверки (без hash, отсортировано)
            data_check_parts = []
            for key, values in sorted(parsed.items()):
                if key != 'hash':
                    data_check_parts.append(f"{key}={values[0]}")

            data_check_string = '\n'.join(data_check_parts)

            # Вычисляем ожидаемый hash
            expected_hash = hmac.new(
                self._secret_key,
                data_check_string.encode(),
                hashlib.sha256
            ).hexdigest()

            # Сравниваем
            if not hmac.compare_digest(received_hash, expected_hash):
                logger.warning("initData hash не совпадает")
                return None

            # Парсим user данные
            result = {}
            for key, values in parsed.items():
                if key == 'user':
                    result['user'] = json.loads(unquote(values[0]))
                elif key == 'hash':
                    result['hash'] = values[0]
                else:
                    result[key] = values[0]

            return result

        except Exception as e:
            logger.error(f"Ошибка верификации initData: {e}")
            return None

    def get_user_id(self, init_data: str) -> Optional[int]:
        """
        Извлечь user_id из initData после верификации.

        Args:
            init_data: URL-encoded строка initData

        Returns:
            user_id если верификация успешна, иначе None
        """
        verified = self.verify_init_data(init_data)
        if verified and 'user' in verified:
            return verified['user'].get('id')
        return None


# Глобальный экземпляр шифрования
_token_encryption: Optional[TokenEncryption] = None


def get_token_encryption() -> TokenEncryption:
    """Получить глобальный экземпляр TokenEncryption."""
    global _token_encryption
    if _token_encryption is None:
        _token_encryption = TokenEncryption()
    return _token_encryption


def generate_api_secret() -> str:
    """Сгенерировать случайный секрет для API."""
    return secrets.token_urlsafe(32)


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """
    Хешировать пароль с солью.

    Args:
        password: Пароль для хеширования
        salt: Опциональная соль (генерируется если не задана)

    Returns:
        Кортеж (hash, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)

    # Используем PBKDF2 с SHA256
    hash_value = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # iterations
    )

    return hash_value.hex(), salt


def verify_password(password: str, hash_value: str, salt: str) -> bool:
    """
    Проверить пароль против хеша.

    Args:
        password: Проверяемый пароль
        hash_value: Хеш для сравнения
        salt: Соль, использованная при хешировании

    Returns:
        True если пароль верный
    """
    computed_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(computed_hash, hash_value)
