from database import Database
from datetime import datetime


class BaseModel:
    """Базовый класс для всех моделей"""

    def __init__(self):
        self.db = Database()

    @classmethod
    def create_table(cls):
        """Создание таблицы в базе данных"""
        raise NotImplementedError("Метод create_table должен быть реализован в дочернем классе")

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

    @classmethod
    def create_table(cls):
        """Создание таблицы клиентов"""
        query = """
        CREATE TABLE IF NOT EXISTS client (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            surname TEXT NOT NULL,
            phone_number VARCHAR(20) NOT NULL,
            email TEXT
        )
        """
        db = Database()
        return db.execute_query(query)

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

        return self.db.execute_query(query, params)

    @classmethod
    def get_by_id(cls, id):
        """Получение клиента по ID"""
        query = "SELECT * FROM client WHERE id = %s"
        db = Database()
        result = db.execute_query(query, (id,), fetch=True)
        if result:
            data = result[0]
            return cls(
                id=data['id'],
                name=data['name'],
                surname=data['surname'],
                phone_number=data['phone_number'],
                email=data['email']
            )
        return None

    @classmethod
    def get_by_phone(cls, phone_number):
        """Получение клиента по номеру телефона"""
        query = "SELECT * FROM client WHERE phone_number = %s"
        db = Database()
        result = db.execute_query(query, (phone_number,), fetch=True)
        if result:
            data = result[0]
            return cls(
                id=data['id'],
                name=data['name'],
                surname=data['surname'],
                phone_number=data['phone_number'],
                email=data['email']
            )
        return None

    @classmethod
    def get_all(cls):
        """Получение всех клиентов"""
        query = "SELECT * FROM client ORDER BY id"
        db = Database()
        result = db.execute_query(query, fetch=True)
        clients = []
        for data in result:
            clients.append(cls(
                id=data['id'],
                name=data['name'],
                surname=data['surname'],
                phone_number=data['phone_number'],
                email=data['email']
            ))
        return clients

    def __str__(self):
        return f"Client(id={self.id}, name={self.name} {self.surname}, phone={self.phone_number})"


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

    @classmethod
    def create_table(cls):
        """Создание таблицы мастеров"""
        query = """
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
        """
        db = Database()
        return db.execute_query(query)

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

        return self.db.execute_query(query, params)

    @classmethod
    def get_by_id(cls, id):
        """Получение мастера по ID"""
        query = "SELECT * FROM master WHERE id = %s"
        db = Database()
        result = db.execute_query(query, (id,), fetch=True)
        if result:
            data = result[0]
            return cls(
                id=data['id'],
                name=data['name'],
                surname=data['surname'],
                patronymic=data['patronymic'],
                phone_number=data['phone_number'],
                email=data['email'],
                is_available=data['is_available'],
                current_orders=data['current_orders']
            )
        return None

    @classmethod
    def get_available_masters(cls):
        """Получение доступных мастеров"""
        query = "SELECT * FROM master WHERE is_available = TRUE ORDER BY current_orders"
        db = Database()
        result = db.execute_query(query, fetch=True)
        masters = []
        for data in result:
            masters.append(cls(
                id=data['id'],
                name=data['name'],
                surname=data['surname'],
                patronymic=data['patronymic'],
                phone_number=data['phone_number'],
                email=data['email'],
                is_available=data['is_available'],
                current_orders=data['current_orders']
            ))
        return masters

    @classmethod
    def get_all(cls):
        """Получение всех мастеров"""
        query = "SELECT * FROM master ORDER BY id"
        db = Database()
        result = db.execute_query(query, fetch=True)
        masters = []
        for data in result:
            masters.append(cls(
                id=data['id'],
                name=data['name'],
                surname=data['surname'],
                patronymic=data['patronymic'],
                phone_number=data['phone_number'],
                email=data['email'],
                is_available=data['is_available'],
                current_orders=data['current_orders']
            ))
        return masters

    def update_availability(self):
        """Обновление доступности мастера"""
        self.is_available = self.current_orders < 3
        return self.save()

    def __str__(self):
        status = "✅ Свободен" if self.is_available else "⚠️ Занят"
        return f"Master(id={self.id}, name={self.name} {self.surname}, orders={self.current_orders}, {status})"


class Product(BaseModel):
    """Класс для таблицы Product"""

    def __init__(self, type=None, material=None, sample=None, id=None):
        super().__init__()
        self.id = id
        self.type = type
        self.material = material
        self.sample = sample

    @classmethod
    def create_table(cls):
        """Создание таблицы продуктов"""
        query = """
        CREATE TABLE IF NOT EXISTS product (
            id SERIAL PRIMARY KEY,
            type TEXT NOT NULL,
            material TEXT NOT NULL,
            sample INTEGER
        )
        """
        db = Database()
        return db.execute_query(query)

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

        return self.db.execute_query(query, params)

    @classmethod
    def get_by_id(cls, id):
        """Получение продукта по ID"""
        query = "SELECT * FROM product WHERE id = %s"
        db = Database()
        result = db.execute_query(query, (id,), fetch=True)
        if result:
            data = result[0]
            return cls(
                id=data['id'],
                type=data['type'],
                material=data['material'],
                sample=data['sample']
            )
        return None

    @classmethod
    def get_by_params(cls, type, material, sample):
        """Получение продукта по параметрам"""
        query = "SELECT * FROM product WHERE type = %s AND material = %s AND sample = %s"
        db = Database()
        result = db.execute_query(query, (type, material, sample), fetch=True)
        if result:
            data = result[0]
            return cls(
                id=data['id'],
                type=data['type'],
                material=data['material'],
                sample=data['sample']
            )
        return None

    @classmethod
    def get_all(cls):
        """Получение всех продуктов"""
        query = "SELECT * FROM product ORDER BY id"
        db = Database()
        result = db.execute_query(query, fetch=True)
        products = []
        for data in result:
            products.append(cls(
                id=data['id'],
                type=data['type'],
                material=data['material'],
                sample=data['sample']
            ))
        return products

    def __str__(self):
        return f"Product(id={self.id}, type={self.type}, material={self.material}, sample={self.sample})"


class Order(BaseModel):
    """Класс для таблицы Order"""

    def __init__(self, client_id=None, data=None, status='new', id=None):
        super().__init__()
        self.id = id
        self.client_id = client_id
        self.data = data or datetime.now().date()
        self.status = status

    @classmethod
    def create_table(cls):
        """Создание таблицы заказов"""
        query = """
        CREATE TABLE IF NOT EXISTS order_table (
            id SERIAL PRIMARY KEY,
            client_id INTEGER REFERENCES client(id),
            data DATE DEFAULT CURRENT_DATE,
            status TEXT DEFAULT 'new'
        )
        """
        db = Database()
        return db.execute_query(query)

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

        return self.db.execute_query(query, params)

    @classmethod
    def get_by_id(cls, id):
        """Получение заказа по ID"""
        query = "SELECT * FROM order_table WHERE id = %s"
        db = Database()
        result = db.execute_query(query, (id,), fetch=True)
        if result:
            data = result[0]
            return cls(
                id=data['id'],
                client_id=data['client_id'],
                data=data['data'],
                status=data['status']
            )
        return None

    @classmethod
    def get_by_status(cls, status):
        """Получение заказов по статусу"""
        query = "SELECT * FROM order_table WHERE status = %s ORDER BY id"
        db = Database()
        result = db.execute_query(query, (status,), fetch=True)
        orders = []
        for data in result:
            orders.append(cls(
                id=data['id'],
                client_id=data['client_id'],
                data=data['data'],
                status=data['status']
            ))
        return orders

    @classmethod
    def get_all(cls):
        """Получение всех заказов"""
        query = "SELECT * FROM order_table ORDER BY id"
        db = Database()
        result = db.execute_query(query, fetch=True)
        orders = []
        for data in result:
            orders.append(cls(
                id=data['id'],
                client_id=data['client_id'],
                data=data['data'],
                status=data['status']
            ))
        return orders

    def get_client(self):
        """Получение клиента заказа"""
        return Client.get_by_id(self.client_id) if self.client_id else None

    def __str__(self):
        return f"Order(id={self.id}, client_id={self.client_id}, status={self.status}, date={self.data})"


class OrderItem(BaseModel):
    """Класс для таблицы OrderItem"""

    def __init__(self, order_id=None, product_id=None, inform=None, id=None):
        super().__init__()
        self.id = id
        self.order_id = order_id
        self.product_id = product_id
        self.inform = inform

    @classmethod
    def create_table(cls):
        """Создание таблицы позиций заказа"""
        query = """
        CREATE TABLE IF NOT EXISTS order_item (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES order_table(id),
            product_id INTEGER REFERENCES product(id),
            inform TEXT
        )
        """
        db = Database()
        return db.execute_query(query)

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

        return self.db.execute_query(query, params)

    @classmethod
    def get_by_order_id(cls, order_id):
        """Получение позиций заказа по ID заказа"""
        query = "SELECT * FROM order_item WHERE order_id = %s"
        db = Database()
        result = db.execute_query(query, (order_id,), fetch=True)
        items = []
        for data in result:
            items.append(cls(
                id=data['id'],
                order_id=data['order_id'],
                product_id=data['product_id'],
                inform=data['inform']
            ))
        return items

    def get_order(self):
        """Получение заказа"""
        return Order.get_by_id(self.order_id) if self.order_id else None

    def get_product(self):
        """Получение продукта"""
        return Product.get_by_id(self.product_id) if self.product_id else None

    def __str__(self):
        return f"OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id})"


class WorkOrder(BaseModel):
    """Класс для таблицы WorkOrder"""

    def __init__(self, order_id=None, master_id=None, data=None, id=None):
        super().__init__()
        self.id = id
        self.order_id = order_id
        self.master_id = master_id
        self.data = data or datetime.now().date()

    @classmethod
    def create_table(cls):
        """Создание таблицы рабочих заданий"""
        query = """
        CREATE TABLE IF NOT EXISTS work_order (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES order_table(id),
            master_id INTEGER REFERENCES master(id),
            data DATE DEFAULT CURRENT_DATE
        )
        """
        db = Database()
        return db.execute_query(query)

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

        return self.db.execute_query(query, params)

    @classmethod
    def get_by_order_id(cls, order_id):
        """Получение рабочего задания по ID заказа"""
        query = "SELECT * FROM work_order WHERE order_id = %s"
        db = Database()
        result = db.execute_query(query, (order_id,), fetch=True)
        if result:
            data = result[0]
            return cls(
                id=data['id'],
                order_id=data['order_id'],
                master_id=data['master_id'],
                data=data['data']
            )
        return None

    @classmethod
    def get_by_master_id(cls, master_id):
        """Получение рабочих заданий по ID мастера"""
        query = "SELECT * FROM work_order WHERE master_id = %s"
        db = Database()
        result = db.execute_query(query, (master_id,), fetch=True)
        work_orders = []
        for data in result:
            work_orders.append(cls(
                id=data['id'],
                order_id=data['order_id'],
                master_id=data['master_id'],
                data=data['data']
            ))
        return work_orders

    def get_order(self):
        """Получение заказа"""
        return Order.get_by_id(self.order_id) if self.order_id else None

    def get_master(self):
        """Получение мастера"""
        return Master.get_by_id(self.master_id) if self.master_id else None

    def __str__(self):
        return f"WorkOrder(id={self.id}, order_id={self.order_id}, master_id={self.master_id})"


class JewelrySystem:
    """Основной класс системы"""

    def __init__(self):
        self.db = Database()
        self.init_database()

    def init_database(self):
        """Инициализация всех таблиц"""
        tables = [Client, Master, Product, Order, OrderItem, WorkOrder]
        for table_class in tables:
            if not table_class.create_table():
                print(f"❌ Ошибка создания таблицы {table_class.__name__}")
                return False

        # Добавляем тестовые данные если таблицы пустые
        if Master.get_all() == []:
            self.add_sample_data()

        print("✅ База данных инициализирована")
        return True

    def add_sample_data(self):
        """Добавление тестовых данных"""
        # Добавляем мастеров
        masters_data = [
            ("Иван", "Петров", "Сергеевич", "+79161111111", "master1@almaz.ru"),
            ("Мария", "Сидорова", "Ивановна", "+79162222222", "master2@almaz.ru"),
            ("Алексей", "Козлов", "Петрович", "+79163333333", "master3@almaz.ru")
        ]

        for master_data in masters_data:
            master = Master(*master_data)
            master.save()

        # Добавляем продукты
        products_data = [
            ("Кольцо", "Золото", 585),
            ("Серьги", "Серебро", 925),
            ("Подвеска", "Золото", 585),
            ("Браслет", "Серебро", 925)
        ]

        for product_data in products_data:
            product = Product(*product_data)
            product.save()

        print("✅ Добавлены тестовые данные")