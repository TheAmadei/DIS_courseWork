import socket
import threading
import time
from PIL import Image
import io
import random

# Функция для генерации изображения
def generate_image(color, size=(100, 100)):
    img = Image.new("RGB", size, color)
    byte_stream = io.BytesIO()
    img.save(byte_stream, format="JPEG")
    return byte_stream.getvalue()

# Генерация случайного ЧБ изображения с шумом
def generate_random_bw_image(size=(100, 100)):
    noise_level = random.randint(5, 50)  # Уровень шума
    base_color = random.randint(0, 255)  # Основной оттенок серого
    img = Image.new("L", size, base_color)
    pixels = img.load()

    for i in range(size[0]):
        for j in range(size[1]):
            noise = random.randint(-noise_level, noise_level)
            pixels[i, j] = max(0, min(255, base_color + noise))

    byte_stream = io.BytesIO()
    img.convert("RGB").save(byte_stream, format="JPEG")
    return byte_stream.getvalue()

# Генерация тестовых данных для ЧБ изображений
def generate_test_data(num_bw_images):
    print(f"Генерация {num_bw_images} ЧБ изображений...")
    # Цветное изображение (например, красное)
    color_image = generate_image((255, 0, 0))
    print("Цветное изображение сгенерировано.")

    # ЧБ изображения (разные случайные оттенки с шумом)
    bw_images = []
    for i in range(num_bw_images):
        bw_images.append(generate_random_bw_image())
        if (i + 1) % 200 == 0:
            print(f"Сгенерировано {i + 1}/{num_bw_images} ЧБ изображений...")

    print("Все ЧБ изображения сгенерированы.")
    return color_image, bw_images


# Функция эмуляции клиента
def client_simulation(color_image, bw_images, server_ip, server_port):
    try:
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((server_ip, server_port))


            # Отправка цветного изображения
            client_socket.sendall(len(color_image).to_bytes(4, 'big'))
            client_socket.sendall(color_image)

            # Отправка черно-белых изображений
            for idx, bw_image in enumerate(bw_images):
                client_socket.sendall(len(bw_image).to_bytes(4, 'big'))
                client_socket.sendall(bw_image)

            # Завершение отправки
            client_socket.sendall((0).to_bytes(4, 'big'))

            # Получение результата
            result = int.from_bytes(client_socket.recv(4), 'big')
            print(f"Клиент получил результат: {result}")
            return result
    except Exception as e:
        print(f"Ошибка в клиенте: {e}")
        return None

# Тестирование одного клиента
def test_single_client(server_ip, server_port):
    print("Запуск теста одного клиента...")
    color_image, bw_images = generate_test_data(100)  # 100 ЧБ изображений
    start_time = time.time()
    result = client_simulation(color_image, bw_images, server_ip, server_port)
    end_time = time.time()
    print(f"Результат: {result}, Время обработки: {end_time - start_time:.2f} секунд")

# Тестирование одного клиента с 10,000 ЧБ изображений
def test_large_single_client(server_ip, server_port):
    print("Запуск теста одного клиента с 10,000 ЧБ изображений...")
    color_image, bw_images = generate_test_data(10000)  # 10,000 ЧБ изображений
    start_time = time.time()
    result = client_simulation(color_image, bw_images, server_ip, server_port)
    end_time = time.time()
    print(f"Результат: {result}, Время обработки: {end_time - start_time:.2f} секунд")

# Тестирование нескольких клиентов в однопоточном режиме
def test_multiple_clients_singlethread(total_clients, server_ip, server_port):
    print("Запуск однопоточного теста...")
    color_image, bw_images = generate_test_data(100)  # 100 ЧБ изображений на клиента
    start_time = time.time()
    results = []
    for i in range(total_clients):
        print(f"Запуск клиента {i + 1}...")
        result = client_simulation(color_image, bw_images, server_ip, server_port)
        results.append((i + 1, result))
    end_time = time.time()

    print("Результаты:")
    for client_id, result in results:
        print(f"Клиент {client_id}: результат {result}")
    print(f"Обработано {total_clients} клиентов в однопоточном режиме за {end_time - start_time:.2f} секунд")

# Тестирование нескольких клиентов в многопоточном режиме
def test_multiple_clients_multithread(total_clients, batch_size, server_ip, server_port):
    print("Запуск многопоточного теста...")
    color_image, bw_images = generate_test_data(100)  # 100 ЧБ изображений на клиента

    results = []
    lock = threading.Lock()

    def client_task(client_id):
        print(f"Запуск клиента {client_id} в отдельном потоке...")
        result = client_simulation(color_image, bw_images, server_ip, server_port)
        with lock:
            results.append((client_id, result))

    start_time = time.time()
    threads = []
    for i in range(total_clients):
        thread = threading.Thread(target=client_task, args=(i + 1,))
        threads.append(thread)
        thread.start()

        # Ограничение на одновременное количество потоков
        if len(threads) >= batch_size:
            for t in threads:
                t.join()
            threads = []

    # Завершаем оставшиеся потоки
    for t in threads:
        t.join()

    end_time = time.time()

    print("Результаты:")
    for client_id, result in sorted(results):
        print(f"Клиент {client_id}: результат {result}")
    print(f"Обработано {total_clients} клиентов в многопоточном режиме за {end_time - start_time:.2f} секунд")

# Тестирование масштабируемости
def test_scalability(server_ip, server_port):
    print("Запуск теста масштабируемости...")
    client_counts = [10, 50, 100, 500]  # Количество клиентов для теста

    for count in client_counts:
        print(f"\nТест с {count} клиентами в однопоточном режиме:")
        test_multiple_clients_singlethread(count, server_ip, server_port)

        print(f"\nТест с {count} клиентами в многопоточном режиме:")
        test_multiple_clients_multithread(count, batch_size=20, server_ip=server_ip, server_port=server_port)

if __name__ == "__main__":
    SERVER_IP = "192.168.100.6"  # Замените на IP вашего сервера
    SERVER_PORT = 5000           # Замените на порт вашего сервера

    mode = input("Выберите тест (1 - Один клиент, 2 - Несколько клиентов, 3 - Масштабируемость, 4 - Один клиент с 10,000 ЧБ изображений): ")

    if mode == "1":
        test_single_client(SERVER_IP, SERVER_PORT)
    elif mode == "2":
        TOTAL_CLIENTS = int(input("Введите количество клиентов: "))
        BATCH_SIZE = int(input("Введите количество клиентов в одной партии: "))

        mode_execution = input("Выберите режим работы (1 - Однопоточный, 2 - Многопоточный): ")

        if mode_execution == "1":
            test_multiple_clients_singlethread(TOTAL_CLIENTS, SERVER_IP, SERVER_PORT)
        elif mode_execution == "2":
            test_multiple_clients_multithread(TOTAL_CLIENTS, BATCH_SIZE, SERVER_IP, SERVER_PORT)
        else:
            print("Неверный выбор режима.")
    elif mode == "3":
        test_scalability(SERVER_IP, SERVER_PORT)
    elif mode == "4":
        test_large_single_client(SERVER_IP, SERVER_PORT)
    else:
        print("Неверный выбор теста.")