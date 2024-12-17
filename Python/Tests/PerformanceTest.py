import socket
import threading
import time
from PIL import Image
import io
import random
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk  # Импортируем ttk для стилизации
import matplotlib.pyplot as plt

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
def generate_test_data(num_bw_images, output_callback):
    message = f"Генерация {num_bw_images} ЧБ изображений..."
    print(message)  # Выводим в консоль
    output_callback(message)  # Выводим в окно

    # Цветное изображение (например, красное)
    color_image = generate_image((255, 0, 0))
    message = "Цветное изображение сгенерировано."
    print(message)
    output_callback(message)

    # ЧБ изображения (разные случайные оттенки с шумом)
    bw_images = []
    for i in range(num_bw_images):
        bw_images.append(generate_random_bw_image())
        if (i + 1) % 200 == 0:
            message = f"Сгенерировано {i + 1}/{num_bw_images} ЧБ изображений..."
            print(message)
            output_callback(message)

    message = "Все ЧБ изображения сгенерированы."
    print(message)
    output_callback(message)
    
    return color_image, bw_images


# Функция для эмуляции клиента
def client_simulation(color_image, bw_images, server_ip, server_port, output_callback):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((server_ip, server_port))
            client_socket.sendall(len(color_image).to_bytes(4, 'big'))
            client_socket.sendall(color_image)

            for bw_image in bw_images:
                client_socket.sendall(len(bw_image).to_bytes(4, 'big'))
                client_socket.sendall(bw_image)

            client_socket.sendall((0).to_bytes(4, 'big'))
            result = int.from_bytes(client_socket.recv(4), 'big')
            return result
    except Exception as e:
        output_callback(f"Ошибка в клиенте: {e}")
        return None

# Функция для построения графика
def plot_results(results, output_callback):
    clients = [res[0] for res in results]
    times = [res[1] for res in results]

    plt.figure(figsize=(10, 6))
    plt.plot(clients, times, marker='o', linestyle='-', color='b', label='Время обработки')
    plt.title("Зависимость времени обработки от количества обработанных клиентов")
    plt.xlabel("Количество клиентов")
    plt.ylabel("Время обработки (сек.)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    output_callback("График построен.")

# Тестирование нескольких клиентов в многопоточном режиме
def test_multiple_clients_multithread(total_clients, batch_size, server_ip, server_port, output_callback, enable_button_callback):
    output_callback("Запуск многопоточного теста...")
    color_image, bw_images = generate_test_data(100, output_callback)  # 100 ЧБ изображений на клиента

    results = []
    lock = threading.Lock()

    def client_task(client_id):
        start_time = time.time()
        result = client_simulation(color_image, bw_images, server_ip, server_port, output_callback)
        end_time = time.time()
        with lock:
            results.append((client_id, end_time - start_time))
        output_callback(f"Клиент {client_id} получил результат: {result}")

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

    output_callback(f"Обработано {total_clients} клиентов в многопоточном режиме за {end_time - start_time:.2f} секунд")

    # Построение графика после теста
    plot_results(results, output_callback)

    # Включаем кнопку после завершения теста
    enable_button_callback()


# Тест с 10000 ЧБ изображениями для одного клиента
def test_large_single_client(server_ip, server_port, output_callback, enable_button_callback):
    output_callback("Запуск теста одного клиента с 10,000 ЧБ изображений...")
    output_callback("Генерация изображений началась...")
    color_image, bw_images = generate_test_data(10000, output_callback)  # 10000 изображений
    output_callback("Генерация завершена. Начало подключения к серверу...")
    
    start_time = time.time()
    result = client_simulation(color_image, bw_images, server_ip, server_port, output_callback)
    end_time = time.time()
    
    output_callback(f"Результат: {result}, Время обработки: {end_time - start_time:.2f} секунд")

    # Включаем кнопку после завершения теста
    enable_button_callback()

class TestApp:
    def __init__(self, root, server_ip, server_port):
        self.root = root
        self.root.title("Сетевой тест")

        self.server_ip = server_ip
        self.server_port = server_port

        # Настроим стили
        style = ttk.Style()
        style.configure("TButton", font=("Arial", 12), padding=10)
        style.configure("TLabel", font=("Arial", 12), padding=5)
        style.configure("TEntry", font=("Arial", 12), padding=5)
        style.configure("TScrolledText", font=("Arial", 10), padding=5)

        # Ввод и кнопки
        self.output_console = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Arial", 10))
        self.output_console.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.test_button_1 = ttk.Button(root, text="Тест одного клиента (10k ЧБ)", command=self.run_test_large_single_client)
        self.test_button_1.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.test_button_2 = ttk.Button(root, text="Тест нескольких клиентов", command=self.run_test_multiple_clients)
        self.test_button_2.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        # Ввод для настройки количества клиентов и размера пачки
        self.clients_label = ttk.Label(root, text="Количество клиентов:")
        self.clients_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.clients_entry = ttk.Entry(root)
        self.clients_entry.insert(0, "10")
        self.clients_entry.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        self.batch_label = ttk.Label(root, text="Размер пачки:")
        self.batch_label.grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.batch_entry = ttk.Entry(root)
        self.batch_entry.insert(0, "20")
        self.batch_entry.grid(row=6, column=0, padx=10, pady=5, sticky="ew")

        # Адаптивная настройка
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Стилизация окна
        self.root.configure(bg="#f5f5f5")
        self.output_console.configure(bg="#ffffff", fg="#000000", insertbackground="black")

    def output_callback(self, message):
        self.output_console.insert(tk.END, message + "\n")
        self.output_console.yview(tk.END)

    def enable_button_callback(self):
        # Включаем все кнопки после теста
        self.test_button_1.config(state=tk.NORMAL)
        self.test_button_2.config(state=tk.NORMAL)

    def run_test_large_single_client(self):
        # Запуск теста в отдельном потоке
        self.test_button_1.config(state=tk.DISABLED)
        threading.Thread(target=test_large_single_client, args=(self.server_ip, self.server_port, self.output_callback, self.enable_button_callback)).start()

    def run_test_multiple_clients(self):
        self.test_button_2.config(state=tk.DISABLED)
        total_clients = int(self.clients_entry.get())
        batch_size = int(self.batch_entry.get())

        threading.Thread(target=test_multiple_clients_multithread, args=(total_clients, batch_size, self.server_ip, self.server_port, self.output_callback, self.enable_button_callback)).start()

# Настроим IP и порт сервера
server_ip = "192.168.159.12"
server_port = 5000

# Создаем и запускаем приложение
root = tk.Tk()
app = TestApp(root, server_ip, server_port)
root.mainloop()
