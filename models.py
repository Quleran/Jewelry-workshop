from database import Database
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


# ==============================
# PATTERN 1: SINGLETON для Database
# ==============================
class DatabaseSingleton:
    """Паттерн Одиночка для управления соединением с базой данных"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._db = Database()
        return cls._instance

    def get_db(self):
        return self._db

    def create_tables(self):
        """Создание всех таблиц через экземпляр Database"""
        return self._db.create_tables()


# ==============================
# PATTERN 2: FACTORY METHOD для моделей
# ==============================
class ModelFactory(ABC):
    """Абстрактная фабрика для создания моделей"""

    @abstractmethod
    def create_model(self, **kwargs):
        pass

    @classmethod
    def create_from_db_row(cls, data):
        """Фабричный метод для создания объекта из строки БД"""
        return cls().create_model(**data)


class ClientFactory(ModelFactory):
    def create_model(self, **kwargs):
        return Client(**kwargs)


class MasterFactory(ModelFactory):
    def create_model(self, **kwargs):
        return Master(**kwargs)


class ProductFactory(ModelFactory):
    def create_model(self, **kwargs):
        return Product(**kwargs)


class OrderFactory(ModelFactory):
    def create_model(self, **kwargs):
        return Order(**kwargs)


class OrderItemFactory(ModelFactory):
    def create_model(self, **kwargs):
        return OrderItem(**kwargs)


class WorkOrderFactory(ModelFactory):
    def create_model(self, **kwargs):
        return WorkOrder(**kwargs)


# ==============================
# PATTERN 3: BUILDER для сложных объектов
# ==============================
class OrderBuilder:
    """Строитель для создания сложных заказов"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.order = None
        self.client = None
        self.order_items = []
        self.work_order = None
        return self

    def set_client(self, name, surname, phone_number, email=None):
        """Установка клиента"""
        self.client = Client(
            name=name,
            surname=surname,
            phone_number=phone_number,
            email=email
        )
        return self

    def set_existing_client(self, client_id):
        """Установка существующего клиента"""
        self.client = Client.get_by_id(client_id)
        if not self.client:
            raise ValueError(f"Клиент с ID {client_id} не найден")
        return self

    def add_product(self, product_type, material, sample, inform=None):
        """Добавление продукта в заказ"""
        # Ищем или создаем продукт
        product = Product.get_by_params(product_type, material, sample)
        if not product:
            product = Product(
                type=product_type,
                material=material,
                sample=sample
            )
            product.save()

        # Создаем позицию заказа
        order_item = OrderItem(
            product_id=product.id,
            inform=inform
        )
        self.order_items.append(order_item)
        return self

    def add_existing_product(self, product_id, inform=None):
        """Добавление существующего продукта в заказ"""
        product = Product.get_by_id(product_id)
        if not product:
            raise ValueError(f"Продукт с ID {product_id} не найден")

        order_item = OrderItem(
            product_id=product.id,
            inform=inform
        )
        self.order_items.append(order_item)
        return self

    def assign_master(self, master_id=None):
        """Назначение мастера (автоматически или вручную)"""
        if master_id:
            master = Master.get_by_id(master_id)
            if not master:
                raise ValueError(f"Мастер с ID {master_id} не найден")
        else:
            # Автоматически находим доступного мастера
            available_masters = Master.get_available_masters()
            if not available_masters:
                raise ValueError("Нет доступных мастеров")
            master = available_masters[0]

        self.work_order = WorkOrder(master_id=master.id)
        return self

    def set_status(self, status):
        """Установка статуса заказа"""
        if not self.order:
            self.order = Order()
        self.order.status = status
        return self

    def build(self):
        """Сборка полного заказа"""
        if not self.client:
            raise ValueError("Клиент не указан")

        if not self.order_items:
            raise ValueError("Нет товаров в заказе")

        # Сохраняем клиента если он новый
        if not self.client.id:
            existing_client = Client.get_by_phone(self.client.phone_number)
            if existing_client:
                self.client = existing_client
            else:
                self.client.save()

        # Создаем заказ
        if not self.order:
            self.order = Order(client_id=self.client.id)
        else:
            self.order.client_id = self.client.id

        self.order.save()

        # Сохраняем позиции заказа
        for item in self.order_items:
            item.order_id = self.order.id
            item.save()

        # Создаем рабочее задание если назначен мастер
        if self.work_order:
            self.work_order.order_id = self.order.id
            self.work_order.save()

            # Обновляем счетчик заказов мастера
            master = Master.get_by_id(self.work_order.master_id)
            if master:
                master.current_orders += 1
                master.update_availability()

        result = {
            'order': self.order,
            'client': self.client,
            'items': self.order_items,
            'work_order': self.work_order
        }

        return result


class BaseModel:
    """Базовый класс для всех моделей"""

    def __init__(self):
        # Используем Singleton для получения соединения с БД
        self.db = DatabaseSingleton().get_db()

    def save(self):
        """Сохранение объекта в базу данных"""
        raise NotImplementedError("Метод save должен быть реализован в дочернем классе")

    @classmethod
    def get_by_id(cls, id):
        """Получение объекта по ID"""
        raise NotImplementedError("Метод get_by_id должен быть реализован в дочернем классе")

    @classmethod
    def get_all(cls):
        """Получение всех объектов"""
        raise NotImplementedError("Метод get_all должен быть реализован в дочернем классе")


class Client(BaseModel):
    """Класс для таблицы Client"""

    def __init__(self, name=None, surname=None, phone_number=None, email=None, id=None):
        super().__init__()
        self.id = id
        self.name = name
        self.surname = surname
        self.phone_number = phone_number
        self.email = email

    def save(self):
        """Сохранение клиента в базу данных"""
        if self.id:
            # Обновление существующего клиента
            query = """
            UPDATE client 
            SET name = %s, surname = %s, phone_number = %s, email = %s
            WHERE id = %s
            """
            params = (self.name, self.surname, self.phone_number, self.email, self.id)
            result = self.db.execute_query(query, params)
            return result is not False
        else:
            # Создание нового клиента
            query = """
            INSERT INTO client (name, surname, phone_number, email) 
            VALUES (%s, %s, %s, %s) RETURNING id
            """
            params = (self.name, self.surname, self.phone_number, self.email)
            result = self.db.execute_query(query, params, fetch=True)
            if result:
                self.id = result[0]['id']
                return True
            return False

    @classmethod
    def get_by_id(cls, id):
        """Получение клиента по ID с использованием Factory"""
        query = "SELECT * FROM client WHERE id = %s"
        db = DatabaseSingleton().get_db()
        result = db.execute_query(query, (id,), fetch=True)
        if result:
            return ClientFactory.create_from_db_row(result[0])
        return None

    @classmethod
    def get_by_phone(cls, phone_number):
        """Получение клиента по номеру телефона с использованием Factory"""
        query = "SELECT * FROM client WHERE phone_number = %s"
        db = DatabaseSingleton().get_db()
        result = db.execute_query(query, (phone_number,), fetch=True)
        if result:
            return ClientFactory.create_from_db_row(result[0])
        return None

    @classmethod
    def get_all(cls):
        """Получение всех клиентов с использованием Factory"""
        query = "SELECT * FROM client ORDER BY id"
        db = DatabaseSingleton().get_db()
        result = db.execute_query(query, fetch=True)
        return [ClientFactory.create_from_db_row(data) for data in result]

    @classmethod
    def create_factory(cls):
        """Фабричный метод для создания клиента"""
        return ClientFactory()

    def __str__(self):
        return f"Client(id={self.id}, name={self.name} {self.surname}, phone={self.phone_number})"

    def __repr__(self):
        return self.__str__()


class Master(BaseModel):
    """Класс для таблицы Master"""

    def __init__(self, name=None, surname=None, patronymic=None, phone_number=None, email=None,
                 is_available=True, current_orders=0, id=None):
        super().__init__()
        self.id = id
        self.name = name
        self.surname = surname
        self.patronymic = patronymic
        self.phone_number = phone_number
        self.email = email
        self.is_available = is_available
        self.current_orders = current_orders

    def save(self):
        """Сохранение мастера в базу данных"""
        if self.id:
            # Обновление существующего мастера
            query = """
            UPDATE master 
            SET name = %s, surname = %s, patronymic = %s, phone_number = %s, 
                email = %s, is_available = %s, current_orders = %s
            WHERE id = %s
            """
            params = (self.name, self.surname, self.patronymic, self.phone_number,
                      self.email, self.is_available, self.current_orders, self.id)
            result = self.db.execute_query(query, params)
            return result is not False
        else:
            # Создание нового мастера
            query = """
            INSERT INTO master (name, surname, patronymic, phone_number, email, is_available, current_orders) 
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            """
            params = (self.name, self.surname, self.patronymic, self.phone_number,
                      self.email, self.is_available, self.current_orders)
            result = self.db.execute_query(query, params, fetch=True)
            if result:
                self.id = result[0]['id']
                return True
            return False

    @classmethod
    def get_by_id(cls, id):
        """Получение мастера по ID с использованием Factory"""
        query = "SELECT * FROM master WHERE id = %s"
        db = DatabaseSingleton().get_db()
        result = db.execute_query(query, (id,), fetch=True)
        if result:
            return MasterFactory.create_from_db_row(result[0])
        return None

    @classmethod
    def get_available_masters(cls):
        """Получение доступных мастеров с использованием Factory"""
        query = "SELECT * FROM master WHERE is_available = TRUE ORDER BY current_orders"
        db = DatabaseSingleton().get_db()
        result = db.execute_query(query, fetch=True)
        return [MasterFactory.create_from_db_row(data) for data in result]

    @classmethod
    def get_all(cls):
        """Получение всех мастеров с использованием Factory"""
        query = "SELECT * FROM master ORDER BY id"
        db = DatabaseSingleton().get_db()
        result = db.execute_query(query, fetch=True)
        return [MasterFactory.create_from_db_row(data) for data in result]

    def update_availability(self):
        """Обновление доступности мастера"""
        self.is_available = self.current_orders < 3
        return self.save()

    @classmethod
    def create_factory(cls):
        """Фабричный метод для создания мастера"""
        return MasterFactory()

    def __str__(self):
        status = "✅ Свободен" if self.is_available else "⚠️ Занят"
        return f"Master(id={self.id}, name={self.surname} {self.name} {self.patronymic or ''}, orders={self.current_orders}, {status})"

    def __repr__(self):
        return self.__str__()


class Product(BaseModel):
    """Класс для таблицы Product"""

    def __init__(self, type=None, material=None, sample=None, id=None):
        super().__init__()
        self.id = id
        self.type = type
        self.material = material
        self.sample = sample

    def save(self):
        """Сохранение продукта в базу данных"""
        if self.id:
            # Обновление существующего продукта
            query = """
            UPDATE product 
            SET type = %s, material = %s, sample = %s
            WHERE id = %s
            """
            params = (self.type, self.material, self.sample, self.id)
            result = self.db.execute_query(query, params)
            return result is not False
        else:
            # Создание нового продукта
            query = """
            INSERT INTO product (type, material, sample) 
            VALUES (%s, %s, %s) RETURNING id
            """
            params = (self.type, self.material, self.sample)
            result = self.db.execute_query(query, params, fetch=True)
            if result:
                self.id = result[0]['id']
                return True
            return False

    @classmethod
    def get_by_id(cls, id):
        """Получение продукта по ID с использованием Factory"""
        query = "SELECT * FROM product WHERE id = %s"
        db = DatabaseSingleton().get_db()
        result = db.execute_query(query, (id,), fetch=True)
        if result:
            return ProductFactory.create_from_db_row(result[0])
        return None

    @classmethod
    def get_by_params(cls, type, material, sample):
        """Получение продукта по параметрам"""
        query = "SELECT * FROM product WHERE type = %s AND material = %s AND sample = %s"
        db = DatabaseSingleton().get_db()
        result = db.execute_query(query, (type, material, sample), fetch=True)
        if result:
            return ProductFactory.create_from_db_row(result[0])
        return None

    @classmethod
    def get_all(cls):
        """Получение всех продуктов с использованием Factory"""
        query = "SELECT * FROM product ORDER BY id"
        db = DatabaseSingleton().get_db()
        result = db.execute_query(query, fetch=True)
        return [ProductFactory.create_from_db_row(data) for data in result]

    @classmethod
    def create_factory(cls):
        """Фабричный метод для создания продукта"""
        return ProductFactory()

    def __str__(self):
        return f"Product(id={self.id}, type={self.type}, material={self.material}, sample={self.sample})"

    def __repr__(self):
        return self.__str__()


class Order(BaseModel):
    """Класс для таблицы Order"""

    def __init__(self, client_id=None, data=None, status='new', id=None):
        super().__init__()
        self.id = id
        self.client_id = client_id
        self.data = data or datetime.now().date()
        self.status = status

    def save(self):
        """Сохранение заказа в базу данных"""
        if self.id:
            # Обновление существующего заказа
            query = """
            UPDATE order_table 
            SET client_id = %s, data = %s, status = %s
            WHERE id = %s
            """
            params = (self.client_id, self.data, self.status, self.id)
            result = self.db.execute_query(query, params)
            return result is not False
        else:
            # Создание нового заказа
            query = """
            INSERT INTO order_table (client_id, data, status) 
            VALUES (%s, %s, %s) RETURNING id
            """
            params = (self.client_id, self.data, self.status)
            result = self.db.execute_query(query, params, fetch=True)
            if result:
                self.id = result[0]['id']
                return True
            return False

    @classmethod
    def get_by_id(cls, id):
        """Получение заказа по ID с использованием Factory"""
        query = "SELECT * FROM order_table WHERE id = %s"
        db = DatabaseSingleton().get_db()
        result = db.execute_query(query, (id,), fetch=True)
        if result:
            return OrderFactory.create_from_db_row(result[0])
        return None

    @classmethod
    def get_by_status(cls, status):
        """Получение заказов по статусу с использованием Factory"""
        query = "SELECT * FROM order_table WHERE status = %s ORDER BY id"
        db = DatabaseSingleton().get_db()
        result = db.execute_query(query, (status,), fetch=True)
        return [OrderFactory.create_from_db_row(data) for data in result]

    @classmethod
    def get_all(cls):
        """Получение всех заказов с использованием Factory"""
        query = "SELECT * FROM order_table ORDER BY id"
        db = DatabaseSingleton().get_db()
        result = db.execute_query(query, fetch=True)
        return [OrderFactory.create_from_db_row(data) for data in result]

    def get_client(self):
        """Получение клиента заказа"""
        return Client.get_by_id(self.client_id) if self.client_id else None

    def get_order_items(self):
        """Получение позиций заказа"""
        return OrderItem.get_by_order_id(self.id) if self.id else []

    def get_work_order(self):
        """Получение рабочего задания"""
        return WorkOrder.get_by_order_id(self.id) if self.id else None

    @classmethod
    def create_factory(cls):
        """Фабричный метод для создания заказа"""
        return OrderFactory()

    def __str__(self):
        return f"Order(id={self.id}, client_id={self.client_id}, status={self.status}, date={self.data})"

    def __repr__(self):
        return self.__str__()


class OrderItem(BaseModel):
    """Класс для таблицы OrderItem"""

    def __init__(self, order_id=None, product_id=None, inform=None, id=None):
        super().__init__()
        self.id = id
        self.order_id = order_id
        self.product_id = product_id
        self.inform = inform

    def save(self):
        """Сохранение позиции заказа в базу данных"""
        if self.id:
            # Обновление существующей позиции
            query = """
            UPDATE order_item 
            SET order_id = %s, product_id = %s, inform = %s
            WHERE id = %s
            """
            params = (self.order_id, self.product_id, self.inform, self.id)
            result = self.db.execute_query(query, params)
            return result is not False
        else:
            # Создание новой позиции
            query = """
            INSERT INTO order_item (order_id, product_id, inform) 
            VALUES (%s, %s, %s) RETURNING id
            """
            params = (self.order_id, self.product_id, self.inform)
            result = self.db.execute_query(query, params, fetch=True)
            if result:
                self.id = result[0]['id']
                return True
            return False

    @classmethod
    def get_by_order_id(cls, order_id):
        """Получение позиций заказа по ID заказа с использованием Factory"""
        query = "SELECT * FROM order_item WHERE order_id = %s"
        db = DatabaseSingleton().get_db()
        result = db.execute_query(query, (order_id,), fetch=True)
        return [OrderItemFactory.create_from_db_row(data) for data in result]

    def get_order(self):
        """Получение заказа"""
        return Order.get_by_id(self.order_id) if self.order_id else None

    def get_product(self):
        """Получение продукта"""
        return Product.get_by_id(self.product_id) if self.product_id else None

    @classmethod
    def create_factory(cls):
        """Фабричный метод для создания позиции заказа"""
        return OrderItemFactory()

    def __str__(self):
        return f"OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id}, info={self.inform})"

    def __repr__(self):
        return self.__str__()


class WorkOrder(BaseModel):
    """Класс для таблицы WorkOrder"""

    def __init__(self, order_id=None, master_id=None, data=None, id=None):
        super().__init__()
        self.id = id
        self.order_id = order_id
        self.master_id = master_id
        self.data = data or datetime.now().date()

    def save(self):
        """Сохранение рабочего задания в базу данных"""
        if self.id:
            # Обновление существующего задания
            query = """
            UPDATE work_order 
            SET order_id = %s, master_id = %s, data = %s
            WHERE id = %s
            """
            params = (self.order_id, self.master_id, self.data, self.id)
            result = self.db.execute_query(query, params)
            return result is not False
        else:
            # Создание нового задания
            query = """
            INSERT INTO work_order (order_id, master_id, data) 
            VALUES (%s, %s, %s) RETURNING id
            """
            params = (self.order_id, self.master_id, self.data)
            result = self.db.execute_query(query, params, fetch=True)
            if result:
                self.id = result[0]['id']
                return True
            return False

    @classmethod
    def get_by_order_id(cls, order_id):
        """Получение рабочего задания по ID заказа с использованием Factory"""
        query = "SELECT * FROM work_order WHERE order_id = %s"
        db = DatabaseSingleton().get_db()
        result = db.execute_query(query, (order_id,), fetch=True)
        if result:
            return WorkOrderFactory.create_from_db_row(result[0])
        return None

    @classmethod
    def get_by_master_id(cls, master_id):
        """Получение рабочих заданий по ID мастера с использованием Factory"""
        query = "SELECT * FROM work_order WHERE master_id = %s"
        db = DatabaseSingleton().get_db()
        result = db.execute_query(query, (master_id,), fetch=True)
        return [WorkOrderFactory.create_from_db_row(data) for data in result]

    def get_order(self):
        """Получение заказа"""
        return Order.get_by_id(self.order_id) if self.order_id else None

    def get_master(self):
        """Получение мастера"""
        return Master.get_by_id(self.master_id) if self.master_id else None

    @classmethod
    def create_factory(cls):
        """Фабричный метод для создания рабочего задания"""
        return WorkOrderFactory()

    def __str__(self):
        return f"WorkOrder(id={self.id}, order_id={self.order_id}, master_id={self.master_id}, date={self.data})"

    def __repr__(self):
        return self.__str__()


class JewelrySystem:
    """Основной класс системы"""

    def __init__(self):
        self.db = DatabaseSingleton().get_db()
        self.init_database()

    def init_database(self):
        """Инициализация всех таблиц через класс Database"""
        if not self.db.create_tables():
            print("❌ Ошибка создания таблиц")
            return False

        # Добавляем тестовые данные если таблицы пустые
        if not Master.get_all():
            self.add_sample_data()

        print("✅ База данных инициализирована")
        return True

    def add_sample_data(self):
        """Добавление тестовых данных"""
        # Используем фабрики для создания мастеров
        master_factory = MasterFactory()
        masters_data = [
            {"name": "Иван", "surname": "Петров", "patronymic": "Сергеевич",
             "phone_number": "+79161111111", "email": "master1@almaz.ru"},
            {"name": "Мария", "surname": "Сидорова", "patronymic": "Ивановna",
             "phone_number": "+79162222222", "email": "master2@almaz.ru"},
            {"name": "Алексей", "surname": "Козлов", "patronymic": "Петрович",
             "phone_number": "+79163333333", "email": "master3@almaz.ru"}
        ]

        for master_data in masters_data:
            master = master_factory.create_model(**master_data)
            master.save()

        print("✅ Добавлены тестовые данные")

    def create_complex_order(self, client_data, products_data, assign_master=True, master_id=None):
        """Создание сложного заказа с использованием строителя"""
        try:
            builder = OrderBuilder()

            # Устанавливаем клиента
            builder.set_client(**client_data)

            # Добавляем продукты
            for product in products_data:
                builder.add_product(**product)

            # Назначаем мастера если требуется
            if assign_master:
                if master_id:
                    builder.assign_master(master_id=master_id)
                else:
                    builder.assign_master()

            # Собираем заказ
            result = builder.build()

            print(f"✅ Создан сложный заказ ID: {result['order'].id}")
            return result

        except Exception as e:
            print(f"❌ Ошибка создания заказа: {e}")
            return None

    def get_order_builder(self):
        """Получение нового строителя заказов"""
        return OrderBuilder()

    def display_system_status(self):
        """Отображение статуса системы"""
        print("\n" + "=" * 50)
        print("СТАТУС СИСТЕМЫ ЮВЕЛИРНОЙ МАСТЕРСКОЙ")
        print("=" * 50)

        # Клиенты
        clients = Client.get_all()
        print(f"👥 Клиенты: {len(clients)}")

        # Мастера
        masters = Master.get_all()
        available_masters = Master.get_available_masters()
        print(f"👨‍🔧 Мастера: {len(masters)} (свободных: {len(available_masters)})")

        # Продукты
        products = Product.get_all()
        print(f"💎 Продукты: {len(products)}")

        # Заказы
        orders = Order.get_all()
        new_orders = Order.get_by_status('new')
        print(f"📦 Заказы: {len(orders)} (новых: {len(new_orders)})")

        print("=" * 50)