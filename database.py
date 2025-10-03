import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()


class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Инициализация подключения к базе данных"""
        self.conn = None
        self.connect()

    def connect(self):
        """Подключение к базе данных с явным указанием кодировки"""
        try:
            self.conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'jewelry_orders'),
                user=os.getenv('DB_USER', 'jewelry_user'),
                password=os.getenv('DB_PASSWORD', 'simplepassword'),
                port=os.getenv('DB_PORT', '5432'),
                client_encoding='UTF-8'
            )

            print("✅ Успешное подключение к базе данных")
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
        return True

    def execute_query(self, query, params=None, fetch=False):
        """Выполнение запроса к базе данных с обработкой кодировки"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Устанавливаем кодировку перед выполнением запроса
                cursor.execute("SET client_encoding TO 'UTF8';")
                cursor.execute(query, params)
                if fetch:
                    result = cursor.fetchall()
                    # Декодируем строки если нужно
                    return self._decode_result(result)
                self.conn.commit()
                return True
        except Exception as e:
            print(f"❌ Ошибка выполнения запроса: {e}")
            self.conn.rollback()
            return False

    def _decode_result(self, result):
        """Декодирует строки в результатах запроса"""
        if not result:
            return result

        decoded_result = []
        for row in result:
            decoded_row = {}
            for key, value in row.items():
                if isinstance(value, str):
                    try:
                        # Пробуем декодировать строку
                        decoded_row[key] = value.encode('utf-8').decode('utf-8')
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        # Если не получается, оставляем как есть
                        decoded_row[key] = value
                else:
                    decoded_row[key] = value
            decoded_result.append(decoded_row)

        return decoded_result

    def test_connection(self):
        """Тестирование подключения к базе данных"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SET client_encoding TO 'UTF8';")
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                print(f"📊 Версия PostgreSQL: {version[0]}")

            return True
        except Exception as e:
            print(f"❌ Ошибка тестирования подключения: {e}")
            return False

    def close(self):
        """Закрытие соединения с базой данных"""
        if self.conn:
            self.conn.close()