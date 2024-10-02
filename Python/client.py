import tkinter as tk
from tkinter import filedialog, messagebox, Label, Button, Frame, Listbox, Scrollbar
import grpc
import io
import image_service_pb2
import image_service_pb2_grpc
from PIL import Image, ImageTk
import socket

class ImageComparisonApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Инструмент Сравнения Изображений")
        self.master.geometry("1000x700")  # Увеличен размер окна
        self.master.configure(bg="#f8f9fa")  # Светлый фон

        # Панель для кнопок
        self.button_frame = Frame(master, bg="#f8f9fa", bd=2, relief="groove")
        self.button_frame.pack(pady=20, padx=20)

        # Кнопка загрузки цветного изображения
        self.load_color_button = Button(self.button_frame, text="Загрузить Цветное Изображение", command=self.load_color_image, bg="#28a745", fg="white", font=("Helvetica", 12, "bold"), relief="flat")
        self.load_color_button.pack(side="left", padx=10, pady=10)

        # Кнопка загрузки черно-белых изображений
        self.load_bw_button = Button(self.button_frame, text="Загрузить Черно-Белые Изображения", command=self.load_bw_images, bg="#007bff", fg="white", font=("Helvetica", 12, "bold"), relief="flat")
        self.load_bw_button.pack(side="left", padx=10, pady=10)

        # Кнопка сравнения изображений
        self.compare_button = Button(self.button_frame, text="Сравнить Изображения", command=self.compare_images, bg="#ffc107", fg="white", font=("Helvetica", 12, "bold"), relief="flat")
        self.compare_button.pack(side="left", padx=10, pady=10)

        # Панель для оригинального и совпадающего изображений
        self.images_frame = Frame(master, bg="#f8f9fa")
        self.images_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # Панель для оригинального изображения
        self.original_frame = Frame(self.images_frame, bg="#f8f9fa", bd=2, relief="groove")
        self.original_frame.pack(side="left", padx=10, fill="both", expand=True)

        self.original_label = Label(self.original_frame, bg="#f8f9fa")
        self.original_label.pack(pady=10)

        # Панель для совпадающего черно-белого изображения
        self.match_frame = Frame(self.images_frame, bg="#f8f9fa", bd=2, relief="groove")
        self.match_frame.pack(side="left", padx=10, fill="both", expand=True)

        self.matched_bw_label = Label(self.match_frame, bg="#f8f9fa")
        self.matched_bw_label.pack(pady=10)

        # Панель для списка черно-белых изображений
        self.list_frame = Frame(master, bg="#f8f9fa", bd=2, relief="groove")
        self.list_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # Кнопка для показа/скрытия списка черно-белых изображений
        self.toggle_button = Button(master, text="Показать/Скрыть ЧБ Изображения", command=self.toggle_bw_image_list, bg="#6c757d", fg="white", font=("Helvetica", 12, "bold"), relief="flat")
        self.toggle_button.pack(pady=10)

        # Список для черно-белых изображений
        self.bw_listbox = Listbox(self.list_frame, bg="#f8f9fa", font=("Helvetica", 10))
        self.bw_listbox.pack(side="left", fill="both", expand=True)

        # Полоса прокрутки для списка
        self.scrollbar = Scrollbar(self.list_frame)
        self.scrollbar.pack(side="right", fill="y")
        self.bw_listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.bw_listbox.yview)

        # Статусная метка
        self.status_label = Label(master, text="", bg="#f8f9fa", font=("Helvetica", 10))
        self.status_label.pack(pady=10)

        self.color_image = None
        self.bw_images = []
        self.bw_list_visible = False  # Отслеживание видимости списка

    def load_color_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Файлы изображений", "*.jpg;*.jpeg;*.png")])
        if file_path:
            self.color_image = Image.open(file_path)
            self.color_image.thumbnail((400, 400))  # Уменьшаем изображение для отображения
            self.show_image(self.original_label, self.color_image)

    def load_bw_images(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Файлы изображений", "*.jpg;*.jpeg;*.png")])
        if file_paths:
            for path in file_paths:
                bw_image = Image.open(path)
                bw_image.thumbnail((400, 400))  # Уменьшаем изображение для отображения
                self.bw_images.append(bw_image)
                self.bw_listbox.insert(tk.END, f"Index: {len(self.bw_images) - 1}: {path}")  # Добавляем в список с индексом

    def toggle_bw_image_list(self):
        """Переключить видимость списка черно-белых изображений."""
        if self.bw_list_visible:
            self.bw_listbox.pack_forget()  # Скрыть список
            self.toggle_button.config(text="Показать ЧБ Изображения")  # Изменить текст кнопки
        else:
            self.bw_listbox.pack(side="left", fill="both", expand=True)  # Показать список
            self.toggle_button.config(text="Скрыть ЧБ Изображения")  # Изменить текст кнопки
        self.bw_list_visible = not self.bw_list_visible  # Изменить состояние видимости

    def compare_images(self):
        if self.color_image is None or not self.bw_images:
            messagebox.showwarning("Предупреждение", "Пожалуйста, загрузите цветное и черно-белые изображения!")
            return

        # Подготовка изображений для TCP
        try:
            # Сериализация цветного изображения
            color_image_bytes = io.BytesIO()
            self.color_image.save(color_image_bytes, format='PNG')
            color_image_data = color_image_bytes.getvalue()

            # Сериализация черно-белых изображений
            bw_images_data = []
            for bw_image in self.bw_images:
                bw_image_bytes = io.BytesIO()
                bw_image.save(bw_image_bytes, format='PNG')
                bw_images_data.append(bw_image_bytes.getvalue())

            # Подключение к TCP серверу и отправка запросов
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', 5000))
                # Отправляем размер цветного изображения
                s.sendall(len(color_image_data).to_bytes(4, 'big'))
                # Отправляем цветное изображение
                s.sendall(color_image_data)

                # Отправляем черно-белые изображения
                for bw_image_data in bw_images_data:
                    s.sendall(len(bw_image_data).to_bytes(4, 'big'))
                    s.sendall(bw_image_data)

                # Отправляем сигнал окончания передачи черно-белых изображений
                s.sendall((0).to_bytes(4, 'big'))

                # Получаем индекс соответствующего черно-белого изображения
                matching_index_bytes = s.recv(4)
                matching_index = int.from_bytes(matching_index_bytes, 'big') - 1  # Корректируем индекс

            # Отображение результатов
            if matching_index >= 0:
                matching_bw_image = self.bw_images[matching_index]
                self.show_image(self.matched_bw_label, matching_bw_image)
                messagebox.showinfo("Результат", f"Совпадение найдено с изображением под индексом: {matching_index}")
            else:
                self.matched_bw_label.config(image='', text='')  # Убираем изображение, если совпадений нет
                messagebox.showinfo("Результат", "Совпадений изображения в черно-белом варианте не найдено.")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")


    def show_image(self, label, image):
        """Отобразить изображение в указанной метке."""
        image_tk = ImageTk.PhotoImage(image)
        label.config(image=image_tk)
        label.image = image_tk  # Сохранить ссылку для предотвращения сборки мусора

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageComparisonApp(root)
    root.mainloop()
