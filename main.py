from models import JewelrySystem, Client, Order, Product, OrderItem, WorkOrder, Master


def print_menu():
    """Вывод главного меню"""
    print("\n" + "=" * 50)
    print("🎯 СИСТЕМА ЗАКАЗОВ ЮВЕЛИРНОЙ МАСТЕРСКОЙ")
    print("=" * 50)
    print("1. 📋 Создать новый заказ")
    print("2. 🔍 Проверить статус заказа")
    print("3. 👨‍🏭 Панель мастера")
    print("4. 📊 Просмотр всех заказов")
    print("5. ℹ️  Информация о мастерах")
    print("6. 👥 Просмотр всех клиентов")
    print("0. 🚪 Выход")
    print("=" * 50)


def create_order_menu(system):
    """Меню создания заказа"""
    print("\n📋 СОЗДАНИЕ НОВОГО ЗАКАЗА")
    print("-" * 30)

    # Данные клиента
    print("\n👤 Данные клиента:")
    name = input("Имя: ").strip()
    surname = input("Фамилия: ").strip()
    phone = input("Телефон: ").strip()
    email = input("Email (необязательно): ").strip()

    # Проверяем, есть ли клиент с таким телефоном
    existing_client = Client.get_by_phone(phone)
    if existing_client:
        client = existing_client
        print(f"✅ Найден существующий клиент: {client.name} {client.surname}")
    else:
        # Создаем нового клиента
        client = Client(name=name, surname=surname, phone_number=phone, email=email)
        if client.save():
            print("✅ Новый клиент создан")
        else:
            print("❌ Ошибка создания клиента")
            return

    # Информация о заказе
    print("\n💎 Информация о изделии:")
    product_type = input("Тип изделия (кольцо, серьги, подвеска и т.д.): ").strip()
    material = input("Материал (золото, серебро и т.д.): ").strip()
    sample = input("Проба (585, 925 и т.д.): ").strip()
    description = input("Подробное описание заказа: ").strip()

    # Создаем заказ
    order = Order(client_id=client.id)
    if not order.save():
        print("❌ Ошибка создания заказа")
        return

    # Находим или создаем продукт
    product = Product.get_by_params(product_type, material, sample)
    if not product:
        product = Product(type=product_type, material=material, sample=sample)
        if not product.save():
            print("❌ Ошибка создания продукта")
            return

    # Создаем позицию заказа
    order_item = OrderItem(order_id=order.id, product_id=product.id, inform=description)
    if not order_item.save():
        print("❌ Ошибка создания позиции заказа")
        return

    # Пытаемся назначить заказ мастеру
    assign_order_to_master(order.id)

    print(f"\n✅ Заказ успешно создан!")
    print(f"📦 Номер вашего заказа: {order.id}")
    print("💡 Сохраните этот номер для отслеживания статуса")


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
            client = order.get_client()
            order_items = OrderItem.get_by_order_id(order.id)
            work_order = WorkOrder.get_by_order_id(order.id)

            print(f"\n📦 Заказ №{order.id}")
            print(f"👤 Клиент: {client.name} {client.surname}")
            print(f"📞 Телефон: {client.phone_number}")
            print(f"📅 Дата: {order.data}")
            print(f"📊 Статус: {order.status}")

            if work_order:
                master = work_order.get_master()
                print(f"👨‍🏭 Мастер: {master.name} {master.surname}")

            for item in order_items:
                product = item.get_product()
                if product:
                    print(f"💎 Изделие: {product.type} из {product.material} (проба {product.sample})")
                if item.inform:
                    print(f"📝 Описание: {item.inform}")
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
            print("3. ↩️ Назад")

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

    while True:
        print_menu()
        choice = input("Выберите действие: ").strip()

        if choice == "1":
            create_order_menu(system)
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
        elif choice == "0":
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор, попробуйте снова")


if __name__ == "__main__":
    main()