from models import JewelrySystem, Client, Order, Product, OrderItem, WorkOrder, Master


def print_menu():
    """Вывод главного меню"""
    print("\n" + "=" * 50)
    print("🎯 СИСТЕМА ЗАКАЗОВ ЮВЕЛИРНОЙ МАСТЕРСКОЙ")
    print("=" * 50)
    print("1. 📋 Создать улучшенный заказ")
    print("2. 🔍 Проверить статус заказа")
    print("3. 👨‍🏭 Панель мастера")
    print("4. 📊 Просмотр всех заказов")
    print("5. ℹ️  Информация о мастерах")
    print("6. 👥 Просмотр всех клиентов")
    print("7. 🔔 Тест уведомлений")
    print("8. 📈 Статистика системы")
    print("0. 🚪 Выход")
    print("=" * 50)


def create_enhanced_order_menu(system):
    """Меню создания улучшенного заказа с дополнительными услугами"""
    print("\n🎁 СОЗДАНИЕ УЛУЧШЕННОГО ЗАКАЗА")
    print("-" * 30)

    # Данные клиента
    print("\n👤 ДАННЫЕ КЛИЕНТА:")
    name = input("Имя: ").strip()
    surname = input("Фамилия: ").strip()
    phone = input("Телефон: ").strip()
    email = input("Email (необязательно): ").strip()

    # Проверяем, есть ли клиент с таким телефоном
    existing_client = Client.get_by_phone(phone)
    if existing_client:
        client = existing_client
        print(f"✅ Найден существующий клиент: {client.name} {client.surname}")
        use_existing = input("Использовать существующие данные? (y/n): ").strip().lower()
        if use_existing != 'y':
            # Обновляем данные клиента
            client.name = name
            client.surname = surname
            client.email = email
            client.save()
            print("✅ Данные клиента обновлены")
    else:
        # Создаем нового клиента
        client = Client(name=name, surname=surname, phone_number=phone, email=email)
        if client.save():
            print("✅ Новый клиент создан")
        else:
            print("❌ Ошибка создания клиента")
            return

    # Информация о заказе
    print("\n💎 ИНФОРМАЦИЯ ОБ ИЗДЕЛИИ:")
    product_type = input("Тип изделия (кольцо, серьги, подвеска и т.д.): ").strip()
    material = input("Материал (золото, серебро и т.д.): ").strip()
    sample = input("Проба (585, 925 и т.д.): ").strip()
    description = input("Подробное описание заказа: ").strip()

    # Дополнительные услуги
    print("\n🌟 ДОПОЛНИТЕЛЬНЫЕ УСЛУГИ:")

    enhancements = {}

    # Срочность
    print("\n⚡ СРОЧНОСТЬ ВЫПОЛНЕНИЯ:")
    print("1. Стандартный срок (5-7 дней) - без доплаты")
    print("2. Срочный заказ (3-4 дня) +500 руб.")
    print("3. Экспресс (1-2 дня) +1000 руб.")
    print("4. Супер-экспресс (до 24 часов) +2000 руб.")

    while True:
        urgency_choice = input("Выберите вариант срочности (1-4): ").strip()
        urgency_map = {"1": None, "2": "standard", "3": "express", "4": "super_express"}
        if urgency_choice in urgency_map:
            if urgency_map[urgency_choice]:
                enhancements['urgent'] = urgency_map[urgency_choice]
                urgency_names = {"standard": "Срочный", "express": "Экспресс", "super_express": "Супер-экспресс"}
                print(f"✅ Выбрано: {urgency_names[urgency_map[urgency_choice]]}")
            else:
                print("✅ Выбрано: Стандартный срок")
            break
        else:
            print("❌ Неверный выбор, попробуйте снова")

    # Страхование
    print("\n🛡️ СТРАХОВАНИЕ ИЗДЕЛИЯ:")
    print("1. Без страхования")
    print("2. Стандартная страховка (10,000 руб.) +100 руб.")
    print("3. Премиум страховка (20,000 руб.) +200 руб.")

    while True:
        insurance_choice = input("Выберите вариант страхования (1-3): ").strip()
        insurance_map = {"1": None, "2": 10000, "3": 20000}
        if insurance_choice in insurance_map:
            if insurance_map[insurance_choice]:
                enhancements['insurance'] = insurance_map[insurance_choice]
                insurance_amounts = {10000: "10,000 руб.", 20000: "20,000 руб."}
                print(f"✅ Выбрано: Страхование на {insurance_amounts[insurance_map[insurance_choice]]}")
            else:
                print("✅ Выбрано: Без страхования")
            break
        else:
            print("❌ Неверный выбор, попробуйте снова")

    # Подарочная упаковка
    print("\n🎀 ПОДАРОЧНАЯ УПАКОВКА:")
    print("1. Без упаковки")
    print("2. Стандартная упаковка +300 руб.")
    print("3. Премиум упаковка +800 руб.")
    print("4. Элитная упаковка +1500 руб.")

    while True:
        package_choice = input("Выберите вариант упаковки (1-4): ").strip()
        package_map = {"1": None, "2": "standard", "3": "premium", "4": "luxury"}
        if package_choice in package_map:
            if package_map[package_choice]:
                enhancements['gift_package'] = package_map[package_choice]
                package_names = {"standard": "Стандартная", "premium": "Премиум", "luxury": "Элитная"}
                print(f"✅ Выбрано: {package_names[package_map[package_choice]]} упаковка")
            else:
                print("✅ Выбрано: Без упаковки")
            break
        else:
            print("❌ Неверный выбор, попробуйте снова")

    # Подтверждение заказа
    print("\n" + "=" * 40)
    print("📋 ПОДТВЕРЖДЕНИЕ ЗАКАЗА")
    print("=" * 40)

    try:
        # Создаем базовый заказ через фасад
        client_data = {
            'name': client.name,
            'surname': client.surname,
            'phone_number': client.phone_number,
            'email': client.email
        }

        # ИСПРАВЛЕНИЕ: используем правильные параметры для add_product
        products_data = [{
            'product_type': product_type,
            'material': material,
            'sample': sample,
            'inform': description  # ИСПРАВЛЕНО: было 'product_info', должно быть 'inform'
        }]

        # Используем фасад для создания заказа
        facade = system.get_order_facade()
        order_result = facade.create_advanced_order(client_data, products_data)

        if order_result:
            # Применяем декораторы для улучшенного заказа
            enhanced_order = system.demonstrate_enhanced_order(
                order_result['order'],
                enhancements
            )

            print(f"\n🎉 УЛУЧШЕННЫЙ ЗАКАЗ УСПЕШНО СОЗДАН!")
            print("=" * 50)
            print(f"📦 Номер заказа: #{order_result['order'].id}")
            print(f"👤 Клиент: {client.name} {client.surname}")
            print(f"📞 Телефон: {client.phone_number}")
            print(f"💎 Изделие: {product_type} из {material} (проба {sample})")
            print(f"📝 Услуги: {enhanced_order.get_description()}")
            print(f"💰 Итоговая стоимость: {enhanced_order.get_total_cost():.2f} руб.")
            print("=" * 50)

            # Показываем детализацию стоимости
            print("\n📊 ДЕТАЛИЗАЦИЯ СТОИМОСТИ:")
            additional_info = enhanced_order.get_additional_info()
            if additional_info.get('urgent'):
                print(f"   • Срочность ({additional_info['urgency_level']}): +{additional_info['urgency_cost']} руб.")
            if additional_info.get('insured'):
                print(f"   • Страхование: +{additional_info['insurance_cost']} руб.")
            if additional_info.get('gift_package'):
                print(f"   • Упаковка ({additional_info['package_type']}): +{additional_info['package_cost']} руб.")

            # Отправляем уведомление о премиум заказе
            notification_service = system.get_notification_service()

            # Уведомление клиенту
            notification_service.send_notification(
                recipient=client.phone_number,
                message=f"""
🎉 Ваш улучшенный заказ #{order_result['order'].id} создан!

💎 Детали заказа:
• Изделие: {product_type} из {material}
• Услуги: {enhanced_order.get_description()}
• Итоговая стоимость: {enhanced_order.get_total_cost():.2f} руб.

Мы свяжемся с вами в ближайшее время!
                """,
                notification_type='order_created',
                subject=f"Заказ #{order_result['order'].id} создан"
            )

            # Уведомление администратору о премиум заказе
            if enhancements:
                notification_service.send_notification(
                    recipient="admin@almaz.ru",  # Администратор системы
                    message=f"""
🚀 СОЗДАН ПРЕМИУМ ЗАКАЗ #{order_result['order'].id}

👤 Клиент: {client.name} {client.surname}
📞 Телефон: {client.phone_number}
💰 Стоимость: {enhanced_order.get_total_cost():.2f} руб.
🎁 Услуги: {enhanced_order.get_description()}

Требуется особое внимание!
                    """,
                    notification_type='urgent',
                    subject=f"ПРЕМИУМ ЗАКАЗ #{order_result['order'].id}"
                )

            print("\n💡 Сохраните номер заказа для отслеживания статуса")
            print("📞 С вами свяжутся для уточнения деталей")

    except Exception as e:
        print(f"❌ Ошибка при создании заказа: {e}")
        print("Пожалуйста, проверьте введенные данные и попробуйте снова")


def notification_test_menu(system):
    """Меню тестирования системы уведомлений (Adapter)"""
    print("\n🔔 ТЕСТИРОВАНИЕ СИСТЕМЫ УВЕДОМЛЕНИЙ")
    print("-" * 30)

    notification_service = system.get_notification_service()

    print("\n📧 Тестирование каналов уведомлений:")

    # Тестовые данные
    test_recipient = input("Введите телефон/email для теста: ").strip()
    test_message = input("Введите тестовое сообщение: ").strip()

    print("\n🌐 Выберите каналы отправки:")
    print("1. 📧 Только Email")
    print("2. 📱 Только SMS")
    print("3. ✈️ Только Telegram")
    print("4. 🔄 Все каналы")
    print("5. 🎯 Автоматический подбор")

    choice = input("Выберите вариант (1-5): ").strip()

    channels_map = {
        "1": ["email"],
        "2": ["sms"],
        "3": ["telegram"],
        "4": ["email", "sms", "telegram"],
        "5": None  # автоматический подбор
    }

    channels = channels_map.get(choice, None)

    results = notification_service.send_notification(
        recipient=test_recipient,
        message=test_message,
        channels=channels,
        subject="Тестовое уведомление"
    )

    print(f"\n📊 Результаты отправки:")
    for result in results:
        status_icon = "✅" if result['status'] == 'success' else "❌"
        print(f"   {status_icon} {result['service'].upper()}: {result['status']}")


def system_statistics_menu(system):
    """Меню статистики системы"""
    print("\n📈 СТАТИСТИКА СИСТЕМЫ")
    print("-" * 30)

    stats = system.get_system_statistics()

    # Дополнительная аналитика
    print("\n📊 АНАЛИТИКА:")

    # Загрузка мастеров
    masters = Master.get_all()
    if masters:
        total_capacity = len(masters) * 3  # Максимум 3 заказа на мастера
        current_orders = sum(master.current_orders for master in masters)
        load_percentage = (current_orders / total_capacity) * 100 if total_capacity > 0 else 0

        print(f"• Загрузка мастеров: {load_percentage:.1f}%")
        print(f"• Всего заказов в работе: {current_orders}")
        print(f"• Доступно слотов: {total_capacity - current_orders}")

    # Статусы заказов
    orders = Order.get_all()
    if orders:
        status_count = {}
        for order in orders:
            status_count[order.status] = status_count.get(order.status, 0) + 1

        print(f"• Распределение по статусам:")
        for status, count in status_count.items():
            percentage = (count / len(orders)) * 100
            print(f"  - {status}: {count} ({percentage:.1f}%)")


def assign_order_to_master(order_id):
    """Автоматическое назначение заказа мастеру"""
    available_masters = Master.get_available_masters()

    if available_masters:
        # Берем первого доступного мастера
        master = available_masters[0]

        # Создаем рабочее задание
        work_order = WorkOrder(order_id=order_id, master_id=master.id)
        if work_order.save():
            # Обновляем статус заказа
            order = Order.get_by_id(order_id)
            order.status = 'assigned'
            order.save()

            # Обновляем счетчик заказов мастера
            master.current_orders += 1
            master.update_availability()

            print(f"✅ Заказ назначен мастеру: {master.name} {master.surname}")

            # Отправляем уведомления через адаптер
            system = JewelrySystem()
            notification_service = system.get_notification_service()

            # Уведомление клиенту
            client = order.get_client()
            notification_service.send_master_assigned_notification(order, master, client)

            return True

    print("⏳ Все мастера заняты. Заказ ожидает назначения.")
    return False


def check_order_status_menu():
    """Меню проверки статуса заказа"""
    print("\n🔍 ПРОВЕРКА СТАТУСА ЗАКАЗА")
    print("-" * 30)

    try:
        order_id = int(input("Введите номер заказа: "))
        order = Order.get_by_id(order_id)

        if order:
            # Используем фасад для получения сводки
            system = JewelrySystem()
            facade = system.get_order_facade()
            summary = facade.get_order_summary(order_id)

            if summary:
                # Дополнительная информация о уведомлениях
                notification_service = system.get_notification_service()
                print(f"\n🔔 История уведомлений:")

                # Имитация проверки отправленных уведомлений
                notifications = [
                    f"Создание заказа - отправлено",
                    f"Назначение мастера - {'отправлено' if summary.get('master') else 'ожидание'}"
                ]

                for notification in notifications:
                    print(f"   • {notification}")
        else:
            print("❌ Заказ не найден")

    except ValueError:
        print("❌ Неверный формат номера заказа")


def master_panel_menu():
    """Панель мастера"""
    print("\n👨‍🏭 ПАНЕЛЬ МАСТЕРА")
    print("-" * 30)

    try:
        master_id = int(input("Введите ваш ID мастера: "))
        master = Master.get_by_id(master_id)

        if not master:
            print("❌ Мастер не найден")
            return

        while True:
            print(f"\n🎯 Мастер: {master.name} {master.surname}")
            print("1. 📋 Мои текущие заказы")
            print("2. ✅ Завершить заказ")
            print("3. 🔔 Уведомить клиента")
            print("4. 📊 Моя статистика")
            print("5. ↩️ Назад")

            choice = input("Выберите действие: ").strip()

            if choice == "1":
                work_orders = WorkOrder.get_by_master_id(master.id)
                if work_orders:
                    print("\n📋 Ваши текущие заказы:")
                    for wo in work_orders:
                        order = wo.get_order()
                        if order and order.status != 'completed':
                            client = order.get_client()
                            items = OrderItem.get_by_order_id(order.id)
                            product_info = ""
                            for item in items:
                                product = item.get_product()
                                if product:
                                    product_info = f" - {product.type}"
                                    break
                            print(
                                f"Заказ №{order.id}{product_info} - {order.status} - Клиент: {client.name} {client.surname}")
                else:
                    print("📭 У вас нет текущих заказов")

            elif choice == "2":
                try:
                    order_id = int(input("Введите номер заказа для завершения: "))
                    work_order = WorkOrder.get_by_order_id(order_id)

                    if work_order and work_order.master_id == master.id:
                        order = Order.get_by_id(order_id)
                        order.status = 'completed'
                        if order.save():
                            # Обновляем счетчик заказов мастера
                            master.current_orders -= 1
                            master.update_availability()

                            # Отправляем уведомление о готовности
                            system = JewelrySystem()
                            notification_service = system.get_notification_service()
                            client = order.get_client()
                            notification_service.send_order_ready_notification(order, client)

                            # Проверяем очередь
                            pending_orders = Order.get_by_status('new')
                            for pending_order in pending_orders:
                                if assign_order_to_master(pending_order.id):
                                    break

                            print("✅ Заказ завершен")
                        else:
                            print("❌ Ошибка завершения заказа")
                    else:
                        print("❌ Заказ не найден или не назначен вам")

                except ValueError:
                    print("❌ Неверный формат номера заказа")

            elif choice == "3":
                try:
                    order_id = int(input("Введите номер заказа: "))
                    work_order = WorkOrder.get_by_order_id(order_id)

                    if work_order and work_order.master_id == master.id:
                        order = Order.get_by_id(order_id)
                        client = order.get_client()

                        print("\n💬 Типы уведомлений:")
                        print("1. Запрос дополнительной информации")
                        print("2. Уточнение деталей")
                        print("3. Уведомление о ходе работы")
                        print("4. Кастомное сообщение")

                        msg_type = input("Выберите тип: ").strip()
                        custom_message = input("Введите сообщение: ").strip()

                        message_templates = {
                            "1": "Требуется дополнительная информация по вашему заказу",
                            "2": "Необходимо уточнить детали заказа",
                            "3": "Работа над вашим заказом активно ведется",
                            "4": custom_message
                        }

                        message = message_templates.get(msg_type, custom_message)

                        system = JewelrySystem()
                        notification_service = system.get_notification_service()
                        notification_service.send_notification(
                            recipient=client.phone_number,
                            message=message,
                            subject=f"Сообщение от мастера по заказу #{order_id}"
                        )

                        print("✅ Уведомление отправлено")
                    else:
                        print("❌ Заказ не найден или не назначен вам")

                except ValueError:
                    print("❌ Неверный формат номера заказа")

            elif choice == "4":
                print(f"\n📊 СТАТИСТИКА МАСТЕРА:")
                print(f"• Текущие заказы: {master.current_orders}")
                print(f"• Статус: {'✅ Свободен' if master.is_available else '⚠️ Занят'}")
                print(f"• Максимальная нагрузка: 3 заказа")

                work_orders = WorkOrder.get_by_master_id(master.id)
                completed_orders = [wo for wo in work_orders if wo.get_order().status == 'completed']
                print(f"• Завершено заказов: {len(completed_orders)}")

            elif choice == "5":
                break
            else:
                print("❌ Неверный выбор")

    except ValueError:
        print("❌ Неверный формат ID")


def view_all_orders_menu():
    """Просмотр всех заказов"""
    print("\n📊 ВСЕ ЗАКАЗЫ")
    print("-" * 30)

    orders = Order.get_all()
    if orders:
        for order in orders:
            client = order.get_client()
            work_order = WorkOrder.get_by_order_id(order.id)
            master_info = ""
            if work_order:
                master = work_order.get_master()
                master_info = f" - Мастер: {master.name} {master.surname}"

            print(f"Заказ №{order.id} - {order.status} - Клиент: {client.name} {client.surname}{master_info}")
    else:
        print("📭 Нет заказов в системе")


def masters_info_menu():
    """Информация о мастерах"""
    print("\nℹ️  ИНФОРМАЦИЯ О МАСТЕРАХ")
    print("-" * 30)

    masters = Master.get_all()
    if masters:
        for master in masters:
            print(master)
    else:
        print("📭 Нет мастеров в системе")


def view_all_clients_menu():
    """Просмотр всех клиентов"""
    print("\n👥 ВСЕ КЛИЕНТЫ")
    print("-" * 30)

    clients = Client.get_all()
    if clients:
        for client in clients:
            print(client)
    else:
        print("📭 Нет клиентов в системе")


def main():
    """Главная функция"""
    system = JewelrySystem()

    print("🚀 Система запущена успешно!")
    print("💡 Теперь все заказы создаются как улучшенные с дополнительными услугами!")
    print("   • ⚡ Настройка срочности выполнения")
    print("   • 🛡️ Страхование изделий")
    print("   • 🎀 Подарочная упаковка")
    print("   • 🔔 Автоматические уведомления")

    while True:
        print_menu()
        choice = input("Выберите действие: ").strip()

        if choice == "1":
            create_enhanced_order_menu(system)
        elif choice == "2":
            check_order_status_menu()
        elif choice == "3":
            master_panel_menu()
        elif choice == "4":
            view_all_orders_menu()
        elif choice == "5":
            masters_info_menu()
        elif choice == "6":
            view_all_clients_menu()
        elif choice == "7":
            notification_test_menu(system)
        elif choice == "8":
            system_statistics_menu(system)
        elif choice == "0":
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор, попробуйте снова")


if __name__ == "__main__":
    main()