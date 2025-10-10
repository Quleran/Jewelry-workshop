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


# ==============================
# PATTERN 4: FACADE для управления заказами
# ==============================
class OrderManagementFacade:
    """Фасад для упрощенного управления сложной системой заказов"""

    def __init__(self, jewelry_system):
        self.system = jewelry_system
        self._logger = OrderLogger()

    def create_simple_order(self, client_name, client_surname, client_phone,
                            product_type, material, sample, client_email=None, product_info=None):
        """Создание простого заказа в одну операцию"""
        print(f"\n🎯 Создание простого заказа для {client_name} {client_surname}")

        try:
            # Используем строитель через фасад
            builder = self.system.get_order_builder()

            result = (builder
                      .set_client(
                name=client_name,
                surname=client_surname,
                phone_number=client_phone,
                email=client_email
            )
                      .add_product(
                product_type=product_type,
                material=material,
                sample=sample,
                inform=product_info
            )
                      .assign_master()  # Автоматическое назначение мастера
                      .build())

            # Логируем создание заказа
            self._logger.log(f"Создан заказ #{result['order'].id} для клиента {client_phone}")

            print(f"✅ Заказ успешно создан! ID: {result['order'].id}")
            return result

        except Exception as e:
            error_msg = f"Ошибка создания заказа: {e}"
            self._logger.log(error_msg, level="ERROR")
            print(f"❌ {error_msg}")
            return None

    def create_advanced_order(self, client_data, products_data, master_id=None, status='new'):
        """Создание продвинутого заказа с дополнительными опциями"""
        print(f"\n🎯 Создание продвинутого заказа")

        try:
            builder = self.system.get_order_builder()

            # Установка клиента
            if 'id' in client_data:
                builder.set_existing_client(client_data['id'])
            else:
                builder.set_client(**client_data)

            # Добавление продуктов
            for product in products_data:
                if 'id' in product:
                    builder.add_existing_product(**product)
                else:
                    builder.add_product(**product)

            # Назначение мастера
            if master_id:
                builder.assign_master(master_id=master_id)
            else:
                builder.assign_master()

            # Установка статуса
            builder.set_status(status)

            result = builder.build()

            # Логируем создание заказа
            order_info = f"Создан продвинутый заказ #{result['order'].id}, статус: {status}"
            self._logger.log(order_info)

            print(f"✅ Продвинутый заказ создан! ID: {result['order'].id}, Статус: {status}")
            return result

        except Exception as e:
            error_msg = f"Ошибка создания продвинутого заказа: {e}"
            self._logger.log(error_msg, level="ERROR")
            print(f"❌ {error_msg}")
            return None

    def get_order_summary(self, order_id):
        """Получение сводной информации о заказе"""
        print(f"\n📊 Получение сводки по заказу #{order_id}")

        order = Order.get_by_id(order_id)
        if not order:
            print("❌ Заказ не найден")
            return None

        client = order.get_client()
        items = order.get_order_items()
        work_order = order.get_work_order()
        master = work_order.get_master() if work_order else None

        summary = {
            'order': order,
            'client': client,
            'items': items,
            'master': master,
            'work_order': work_order,
            'total_products': len(items)
        }

        # Вывод информации
        print(f"📦 Заказ #{order.id}")
        print(f"👤 Клиент: {client.name} {client.surname}")
        print(f"📞 Телефон: {client.phone_number}")
        print(f"🔄 Статус: {order.status}")
        print(f"👨‍🔧 Мастер: {master.name if master else 'Не назначен'}")
        print(f"📋 Товаров в заказе: {len(items)}")

        return summary

    def change_order_status(self, order_id, new_status):
        """Изменение статуса заказа"""
        print(f"\n🔄 Изменение статуса заказа #{order_id} на '{new_status}'")

        order = Order.get_by_id(order_id)
        if not order:
            print("❌ Заказ не найден")
            return False

        old_status = order.status
        order.status = new_status
        success = order.save()

        if success:
            self._logger.log(f"Статус заказа #{order_id} изменен: {old_status} -> {new_status}")
            print(f"✅ Статус заказа успешно изменен")
        else:
            print(f"❌ Ошибка изменения статуса заказа")

        return success


class OrderLogger:
    """Простой логгер для фасада"""

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(f"📝 {log_entry}")


# ==============================
# PATTERN 5: DECORATOR для дополнительных услуг заказа
# ==============================
class OrderDecorator(ABC):
    """Абстрактный декоратор для заказов"""

    def __init__(self, order_component):
        self._order_component = order_component

    @abstractmethod
    def get_description(self):
        pass

    @abstractmethod
    def get_total_cost(self):
        pass

    @abstractmethod
    def get_additional_info(self):
        pass


class BaseOrderComponent:
    """Базовый компонент заказа"""

    def __init__(self, order, base_cost=0):
        self.order = order
        self._base_cost = base_cost

    def get_description(self):
        return "Базовый заказ"

    def get_total_cost(self):
        return self._base_cost

    def get_additional_info(self):
        return {}


class UrgentOrderDecorator(OrderDecorator):
    """Декоратор срочного заказа"""

    def __init__(self, order_component, urgency_level="standard"):
        super().__init__(order_component)
        self.urgency_level = urgency_level
        self._urgency_costs = {
            "standard": 500,
            "express": 1000,
            "super_express": 2000
        }

    def get_description(self):
        base_desc = self._order_component.get_description()
        level_names = {
            "standard": "Срочный",
            "express": "Экспресс",
            "super_express": "Супер-экспресс"
        }
        return f"{base_desc} + {level_names[self.urgency_level]}"

    def get_total_cost(self):
        base_cost = self._order_component.get_total_cost()
        urgency_cost = self._urgency_costs.get(self.urgency_level, 0)
        return base_cost + urgency_cost

    def get_additional_info(self):
        base_info = self._order_component.get_additional_info()
        base_info.update({
            "urgent": True,
            "urgency_level": self.urgency_level,
            "urgency_cost": self._urgency_costs.get(self.urgency_level, 0)
        })
        return base_info


class InsuranceDecorator(OrderDecorator):
    """Декоратор страхования заказа"""

    def __init__(self, order_component, insurance_amount=10000):
        super().__init__(order_component)
        self.insurance_amount = insurance_amount
        self._insurance_cost = insurance_amount * 0.01  # 1% от страховой суммы

    def get_description(self):
        base_desc = self._order_component.get_description()
        return f"{base_desc} + Страхование ({self.insurance_amount} руб.)"

    def get_total_cost(self):
        base_cost = self._order_component.get_total_cost()
        return base_cost + self._insurance_cost

    def get_additional_info(self):
        base_info = self._order_component.get_additional_info()
        base_info.update({
            "insured": True,
            "insurance_amount": self.insurance_amount,
            "insurance_cost": self._insurance_cost
        })
        return base_info


class GiftPackageDecorator(OrderDecorator):
    """Декоратор подарочной упаковки"""

    def __init__(self, order_component, package_type="standard"):
        super().__init__(order_component)
        self.package_type = package_type
        self._package_costs = {
            "standard": 300,
            "premium": 800,
            "luxury": 1500
        }

    def get_description(self):
        base_desc = self._order_component.get_description()
        type_names = {
            "standard": "Подарочная упаковка",
            "premium": "Премиум упаковка",
            "luxury": "Элитная упаковка"
        }
        return f"{base_desc} + {type_names[self.package_type]}"

    def get_total_cost(self):
        base_cost = self._order_component.get_total_cost()
        package_cost = self._package_costs.get(self.package_type, 0)
        return base_cost + package_cost

    def get_additional_info(self):
        base_info = self._order_component.get_additional_info()
        base_info.update({
            "gift_package": True,
            "package_type": self.package_type,
            "package_cost": self._package_costs.get(self.package_type, 0)
        })
        return base_info


class OrderEnhancementService:
    """Сервис для применения декораторов к заказам"""

    @staticmethod
    def create_enhanced_order(base_order, enhancements):
        """
        Создание улучшенного заказа с применением декораторов

        Args:
            base_order: Базовый объект заказа
            enhancements: Словарь с улучшениями
                Пример: {
                    'urgent': 'express',
                    'insurance': 15000,
                    'gift_package': 'premium'
                }
        """
        base_cost = 0  # Базовая стоимость может рассчитываться из продуктов заказа

        order_component = BaseOrderComponent(base_order, base_cost)

        # Применяем декораторы в зависимости от запрошенных улучшений
        if 'urgent' in enhancements:
            order_component = UrgentOrderDecorator(order_component, enhancements['urgent'])

        if 'insurance' in enhancements:
            order_component = InsuranceDecorator(order_component, enhancements['insurance'])

        if 'gift_package' in enhancements:
            order_component = GiftPackageDecorator(order_component, enhancements['gift_package'])

        return order_component


# ==============================
# PATTERN 6: ADAPTER для системы уведомлений
# ==============================
class NotificationSender(ABC):
    """Абстрактный интерфейс отправителя уведомлений (целевой интерфейс)"""

    @abstractmethod
    def send(self, recipient, message, subject=None):
        pass

    @abstractmethod
    def get_status(self, message_id):
        pass

    @abstractmethod
    def get_sender_type(self):
        pass


# Внешние сервисы уведомлений с несовместимыми интерфейсами
class SMTPEmailService:
    """Внешний класс Email сервиса с несовместимым интерфейсом"""

    def send_email(self, to_address, from_address, email_subject, body, cc_list=None, bcc_list=None):
        """SMTP сервис требует много специфических параметров"""
        print(f"SMTP: Отправка email на {to_address}")
        # Имитация отправки email
        return {
            "message_id": f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "delivered",
            "service": "smtp",
            "recipient": to_address
        }

    def check_email_status(self, message_id):
        """SMTP проверка статуса"""
        return {
            "message_id": message_id,
            "status": "delivered",
            "opened": True,
            "clicks": 0
        }


class TwilioSMSService:
    """Внешний класс SMS сервиса (Twilio-like API)"""

    def send_sms_message(self, phone_number, text_content, from_number=None, media_url=None):
        """Twilio работает с phone numbers и имеет другие параметры"""
        print(f"Twilio: Отправка SMS на {phone_number}")
        return {
            "sid": f"SM{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "status": "sent",
            "to": phone_number,
            "body": text_content
        }

    def get_message_status(self, message_sid):
        """Twilio проверка статуса"""
        return {
            "sid": message_sid,
            "status": "delivered",
            "error_code": None
        }


class TelegramBotAPI:
    """Внешний класс Telegram Bot API"""

    def send_telegram_message(self, chat_id, text, parse_mode=None, reply_markup=None):
        """Telegram Bot API работает с chat_id и имеет свои параметры"""
        print(f"Telegram: Отправка сообщения в chat {chat_id}")
        return {
            "message_id": datetime.now().timestamp(),
            "chat": {"id": chat_id},
            "text": text,
            "date": datetime.now().timestamp()
        }

    def get_chat_member(self, chat_id, user_id):
        """Telegram метод для получения информации о пользователе"""
        return {
            "user": {
                "id": user_id,
                "first_name": "User",
                "username": "username"
            },
            "status": "member"
        }


# Адаптеры для приведения интерфейсов к единому стандарту
class EmailNotificationAdapter(NotificationSender):
    """Адаптер для Email уведомлений"""

    def __init__(self, email_service):
        self.email_service = email_service
        self.default_from = "jewelry-shop@almaz.ru"

    def send(self, recipient, message, subject=None):
        # Преобразуем параметры для SMTP сервиса
        email_subject = subject or "Уведомление от ювелирной мастерской"

        # Вызываем метод SMTP сервиса с преобразованными параметрами
        result = self.email_service.send_email(
            to_address=recipient,
            from_address=self.default_from,
            email_subject=email_subject,
            body=message
        )

        # Преобразуем результат к нашему формату
        return {
            "message_id": result["message_id"],
            "status": "success" if result["status"] == "delivered" else "failed",
            "recipient": recipient,
            "service": "email"
        }

    def get_status(self, message_id):
        result = self.email_service.check_email_status(message_id)

        return {
            "message_id": message_id,
            "status": result["status"],
            "details": {
                "opened": result.get("opened", False),
                "clicks": result.get("clicks", 0)
            },
            "service": "email"
        }

    def get_sender_type(self):
        return "email"


class SMSNotificationAdapter(NotificationSender):
    """Адаптер для SMS уведомлений"""

    def __init__(self, sms_service):
        self.sms_service = sms_service
        self.default_from = "+79990001122"  # Наш номер Twilio

    def send(self, recipient, message, subject=None):
        # Преобразуем параметры для Twilio API
        # Убираем возможные символы из номера телефона
        phone_number = recipient.replace('+', '').replace(' ', '').replace('-', '')

        # Добавляем subject к сообщению если есть
        full_message = message
        if subject:
            full_message = f"{subject}: {message}"

        # Вызываем метод Twilio с преобразованными параметрами
        result = self.sms_service.send_sms_message(
            phone_number=phone_number,
            text_content=full_message,
            from_number=self.default_from
        )

        # Преобразуем результат к нашему формату
        return {
            "message_id": result["sid"],
            "status": "success" if result["status"] == "sent" else "failed",
            "recipient": recipient,
            "service": "sms"
        }

    def get_status(self, message_id):
        result = self.sms_service.get_message_status(message_id)

        return {
            "message_id": message_id,
            "status": result["status"],
            "details": {
                "error_code": result.get("error_code")
            },
            "service": "sms"
        }

    def get_sender_type(self):
        return "sms"


class TelegramNotificationAdapter(NotificationSender):
    """Адаптер для Telegram уведомлений"""

    def __init__(self, telegram_bot):
        self.telegram_bot = telegram_bot

    def send(self, recipient, message, subject=None):
        # Преобразуем параметры для Telegram API
        # recipient должен быть chat_id для Telegram
        try:
            chat_id = int(recipient)
        except ValueError:
            # Если передан username, получаем chat_id (в реальной системе)
            chat_id = self._get_chat_id_by_username(recipient)

        # Форматируем сообщение
        full_message = message
        if subject:
            full_message = f"**{subject}**\n\n{message}"

        # Вызываем метод Telegram Bot API
        result = self.telegram_bot.send_telegram_message(
            chat_id=chat_id,
            text=full_message,
            parse_mode="Markdown"
        )

        # Преобразуем результат к нашему формату
        return {
            "message_id": str(result["message_id"]),
            "status": "success",
            "recipient": recipient,
            "service": "telegram"
        }

    def get_status(self, message_id):
        # В Telegram сообщения доставляются мгновенно
        return {
            "message_id": message_id,
            "status": "delivered",
            "service": "telegram"
        }

    def get_sender_type(self):
        return "telegram"

    def _get_chat_id_by_username(self, username):
        """Вспомогательный метод для получения chat_id по username"""
        # В реальной системе здесь был бы запрос к Telegram API
        # Для демонстрации возвращаем фиктивный ID
        return 123456789


class NotificationService:
    """Сервис для работы с уведомлениями через адаптеры"""

    def __init__(self):
        self.adapters = {
            'email': EmailNotificationAdapter(SMTPEmailService()),
            'sms': SMSNotificationAdapter(TwilioSMSService()),
            'telegram': TelegramNotificationAdapter(TelegramBotAPI())
        }

        # Настройки по умолчанию для разных типов событий
        self.notification_rules = {
            'order_created': ['email', 'sms'],
            'order_ready': ['sms', 'telegram'],
            'master_assigned': ['email'],
            'status_changed': ['email', 'sms'],
            'urgent': ['sms', 'telegram']
        }

    def send_notification(self, recipient, message, notification_type='info', channels=None, subject=None):
        """Отправка уведомления через выбранные каналы"""
        print(f"\n🔔 Отправка уведомления типа '{notification_type}'")
        print(f"📨 Получатель: {recipient}")
        print(f"📝 Сообщение: {message}")

        # Определяем каналы для отправки
        if channels is None:
            channels = self.notification_rules.get(notification_type, ['email'])

        results = []
        for channel in channels:
            if channel in self.adapters:
                try:
                    adapter = self.adapters[channel]
                    result = adapter.send(recipient, message, subject)
                    results.append(result)

                    status_icon = "✅" if result['status'] == 'success' else "❌"
                    print(f"   {status_icon} {channel.upper()}: {result['status']}")

                except Exception as e:
                    error_result = {
                        'service': channel,
                        'status': 'error',
                        'error': str(e)
                    }
                    results.append(error_result)
                    print(f"   ❌ {channel.upper()}: ошибка - {e}")
            else:
                print(f"   ⚠️  Канал '{channel}' не поддерживается")

        return results

    def send_order_created_notification(self, order, client):
        """Специализированный метод для уведомления о создании заказа"""
        message = f"""
        🎉 Ваш заказ #{order.id} успешно создан!

        📦 Детали заказа:
        • Номер: #{order.id}
        • Дата: {order.data}
        • Статус: {order.status}

        Мы свяжемся с вами для уточнения деталей.
        Спасибо, что выбрали нашу мастерскую! ✨
        """

        subject = f"Заказ #{order.id} создан"

        return self.send_notification(
            recipient=client.phone_number,  # Для SMS
            message=message,
            notification_type='order_created',
            subject=subject
        )

    def send_master_assigned_notification(self, order, master, client):
        """Уведомление о назначении мастера"""
        client_message = f"""
        👨‍🔧 Мастер назначен на ваш заказ #{order.id}

        Вашим заказом будет заниматься:
        • Мастер: {master.surname} {master.name} {master.patronymic or ''}
        • Телефон: {master.phone_number}

        Мы приложим все усилия для качественного выполнения работы!
        """

        master_message = f"""
        📋 Вам назначен новый заказ #{order.id}

        Детали заказа:
        • Клиент: {client.name} {client.surname}
        • Телефон: {client.phone_number}
        • Дата создания: {order.data}

        Пожалуйста, свяжитесь с клиентом для уточнения деталей.
        """

        # Уведомление клиенту
        client_results = self.send_notification(
            recipient=client.phone_number,
            message=client_message,
            notification_type='master_assigned',
            subject=f"Мастер назначен для заказа #{order.id}"
        )

        # Уведомление мастеру
        master_results = self.send_notification(
            recipient=master.phone_number,
            message=master_message,
            notification_type='master_assigned',
            subject=f"Новый заказ #{order.id}"
        )

        return {
            'client': client_results,
            'master': master_results
        }

    def send_order_ready_notification(self, order, client):
        """Уведомление о готовности заказа"""
        message = f"""
        ✅ Ваш заказ #{order.id} готов!

        Заказ ожидает вас в нашей мастерской.
        Часы работы: пн-пт с 10:00 до 19:00

        При себе иметь документ, удостоверяющий личность.
        """

        return self.send_notification(
            recipient=client.phone_number,
            message=message,
            notification_type='order_ready',
            subject=f"Заказ #{order.id} готов!"
        )

    def get_adapter_status(self, service):
        """Получение статуса адаптера"""
        if service in self.adapters:
            adapter = self.adapters[service]
            return {
                'service': service,
                'type': adapter.get_sender_type(),
                'status': 'available'
            }
        return {'service': service, 'status': 'not_available'}


# ==============================
# БАЗОВЫЕ КЛАССЫ МОДЕЛЕЙ
# ==============================
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


# ==============================
# ОСНОВНОЙ КЛАСС СИСТЕМЫ
# ==============================
class JewelrySystem:
    """Основной класс системы ювелирной мастерской"""

    def __init__(self):
        self.db = DatabaseSingleton().get_db()
        self.order_facade = None
        self.notification_service = NotificationService()
        self.init_database()

    def init_database(self):
        """Инициализация всех таблиц через класс Database"""
        if not self.db.create_tables():
            print("❌ Ошибка создания таблиц")
            return False

        # Инициализируем фасад после создания таблиц
        self.order_facade = OrderManagementFacade(self)

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

    # ==================================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С ДОБАВЛЕННЫМИ СТРУКТУРНЫМИ ПАТТЕРНАМИ
    # ==================================================================

    def get_order_facade(self):
        """Получение фасада для управления заказами"""
        return self.order_facade

    def get_notification_service(self):
        """Получение сервиса уведомлений"""
        return self.notification_service

    def create_order_with_notifications(self, client_data, products_data):
        """Создание заказа с автоматическими уведомлениями"""
        print(f"\n🎯 Создание заказа с уведомлениями для {client_data['name']}")

        try:
            # Создаем заказ через фасад
            order_result = self.order_facade.create_simple_order(
                client_name=client_data['name'],
                client_surname=client_data['surname'],
                client_phone=client_data['phone_number'],
                product_type=products_data[0]['product_type'],
                material=products_data[0]['material'],
                sample=products_data[0]['sample']
            )

            if order_result:
                # Отправляем уведомления
                order = order_result['order']
                client = order_result['client']

                # Уведомление о создании заказа
                self.notification_service.send_order_created_notification(order, client)

                # Если есть мастер, отправляем уведомление о назначении
                work_order = order_result.get('work_order')
                if work_order:
                    master = work_order.get_master()
                    if master:
                        self.notification_service.send_master_assigned_notification(order, master, client)

                return order_result

        except Exception as e:
            print(f"❌ Ошибка создания заказа с уведомлениями: {e}")
            return None

    def demonstrate_enhanced_order(self, base_order, enhancements):
        """Демонстрация работы с улучшенным заказом через декораторы"""
        print(f"\n🎁 Создание улучшенного заказа с дополнительными услугами")

        enhanced_order = OrderEnhancementService.create_enhanced_order(
            base_order, enhancements
        )

        print(f"📝 Описание: {enhanced_order.get_description()}")
        print(f"💰 Итоговая стоимость: {enhanced_order.get_total_cost()} руб.")
        print(f"📋 Дополнительная информация: {enhanced_order.get_additional_info()}")

        return enhanced_order

    def send_custom_notification(self, recipient, message, channels=None, subject=None):
        """Отправка кастомного уведомления"""
        return self.notification_service.send_notification(
            recipient=recipient,
            message=message,
            channels=channels,
            subject=subject
        )

    def get_system_statistics(self):
        """Получение расширенной статистики системы"""
        print("\n📊 РАСШИРЕННАЯ СТАТИСТИКА СИСТЕМЫ")
        print("-" * 40)

        stats = {}

        # Базовая статистика
        stats['total_clients'] = len(Client.get_all())
        stats['total_masters'] = len(Master.get_all())
        stats['total_products'] = len(Product.get_all())
        stats['total_orders'] = len(Order.get_all())

        # Статистика по статусам заказов
        stats['new_orders'] = len(Order.get_by_status('new'))
        stats['in_progress_orders'] = len(Order.get_by_status('in_progress'))
        stats['completed_orders'] = len(Order.get_by_status('completed'))

        # Статистика по мастерам
        available_masters = Master.get_available_masters()
        busy_masters = [m for m in Master.get_all() if not m.is_available]
        stats['available_masters'] = len(available_masters)
        stats['busy_masters'] = len(busy_masters)

        # Вывод статистики
        for key, value in stats.items():
            readable_key = key.replace('_', ' ').title()
            print(f"• {readable_key}: {value}")

        return stats

