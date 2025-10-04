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

    def create_tables(self):
        """Создание всех таблиц в базе данных"""
        tables_creation = [
            # Таблица клиентов
            """
            CREATE TABLE IF NOT EXISTS client (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                surname TEXT NOT NULL,
                phone_number VARCHAR(20) NOT NULL,
                email TEXT
            )
            """,
            # Таблица мастеров
            """
            CREATE TABLE IF NOT EXISTS master (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                surname TEXT NOT NULL,
                patronymic TEXT,
                phone_number VARCHAR(20) NOT NULL,
                email TEXT,
                is_available BOOLEAN DEFAULT TRUE,
                current_orders INTEGER DEFAULT 0
            )
            """,
            # Таблица продуктов
            """
            CREATE TABLE IF NOT EXISTS product (
                id SERIAL PRIMARY KEY,
                type TEXT NOT NULL,
                material TEXT NOT NULL,
                sample INTEGER
            )
            """,
            # Таблица заказов
            """
            CREATE TABLE IF NOT EXISTS order_table (
                id SERIAL PRIMARY KEY,
                client_id INTEGER REFERENCES client(id),
                data DATE DEFAULT CURRENT_DATE,
                status TEXT DEFAULT 'new'
            )
            """,
            # Таблица позиций заказа
            """
            CREATE TABLE IF NOT EXISTS order_item (
                id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES order_table(id),
                product_id INTEGER REFERENCES product(id),
                inform TEXT
            )
            """,
            # Таблица рабочих заданий
            """
            CREATE TABLE IF NOT EXISTS work_order (
                id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES order_table(id),
                master_id INTEGER REFERENCES master(id),
                data DATE DEFAULT CURRENT_DATE
            )
            """
        ]

        success_count = 0
        for i, query in enumerate(tables_creation):
            try:
                result = self.execute_query(query)
                if result:
                    success_count += 1
                else:
                    print(f"❌ Ошибка создания таблицы {i + 1}")
            except Exception as e:
                print(f"❌ Ошибка при создании таблицы {i + 1}: {e}")

        print(f"✅ Создано таблиц: {success_count}/{len(tables_creation)}")
        return success_count == len(tables_creation)
    def close(self):
        """Закрытие соединения с базой данных"""
        if self.conn:
            self.conn.close()