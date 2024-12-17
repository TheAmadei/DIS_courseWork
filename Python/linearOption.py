from tkinter import Tk, filedialog, Label, Button, messagebox, Frame, Listbox, Scrollbar
import tkinter as tk
from PIL import Image, ImageTk
import numpy as np
import cv2
import logging
import time

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
            self.bw_images = []
            self.bw_listbox.delete(0, tk.END)  # Очистить список перед загрузкой новых изображений
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

        start_time = time.time()
        
        # Преобразование цветного изображения в черно-белое
        color_image_bw = self.convert_to_grayscale(self.color_image)

        best_match_index, best_match_image = self.find_best_match(color_image_bw)

        if best_match_index != -1:
            # Замер времени окончания
            end_time = time.time()
            # Рассчитываем время выполнения в миллисекундах
            execution_time_ms = (end_time - start_time) * 1000
            self.show_image(self.matched_bw_label, best_match_image)
            messagebox.showinfo("Результат", f"Совпадение найдено с изображением под индексом: {best_match_index}. Время выполнения сравнения изображений: {execution_time_ms:.2f} мс")
        else:
            self.matched_bw_label.config(image='', text='')  # Убираем изображение, если совпадений нет
            messagebox.showinfo("Результат", "Совпадений изображения в черно-белом варианте не найдено.")

    def convert_to_grayscale(self, image):
        """Преобразовать изображение в градации серого, если оно не в таком формате."""
        # Преобразуем изображение PIL в массив NumPy
        image_np = np.array(image)

        # Если изображение уже в градациях серого, возвращаем его без изменений
        if len(image_np.shape) == 2:  # Уже одноканальное изображение (черно-белое)
            return image_np
        else:
            # Если изображение цветное, конвертируем его в градации серого
            return cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

    def compare_images_hist(self, bw_image, bw_image_to_compare):
        """Сравнить два изображения с помощью гистограммы."""
        if len(bw_image.shape) == 2:
            bw_image = cv2.cvtColor(bw_image, cv2.COLOR_GRAY2BGR)

        if bw_image.shape[:2] != bw_image_to_compare.shape[:2]:
            logging.warning(f"Размеры изображений не совпадают: bw {bw_image.shape}, bw_compare {bw_image_to_compare.shape}")
            return False

        hist_bw = cv2.calcHist([bw_image], [0], None, [256], [0, 256])
        hist_bw_compare = cv2.calcHist([bw_image_to_compare], [0], None, [256], [0, 256])

        cv2.normalize(hist_bw, hist_bw, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        cv2.normalize(hist_bw_compare, hist_bw_compare, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

        score = cv2.compareHist(hist_bw, hist_bw_compare, cv2.HISTCMP_CORREL)

        threshold = 0.9  # Порог для совпадения

        return score > threshold

    def find_best_match(self, color_image_bw):
        """Найти лучшее совпадение среди черно-белых изображений."""
        best_diff = float('inf')
        matching_index = -1
        best_match_image = None
        
        for index, bw_image in enumerate(self.bw_images):
            bw_image_resized = self.convert_to_grayscale(bw_image)
            if self.compare_images_hist(color_image_bw, bw_image_resized):
                best_match_index = index
                best_match_image = bw_image
                break

        return best_match_index, best_match_image

    def show_image(self, label, image):
        """Отобразить изображение в метке."""
        image_tk = ImageTk.PhotoImage(image)
        label.config(image=image_tk, text='')
        label.image = image_tk  # Сохраняем ссылку на изображение

# Создаем и запускаем приложение
if __name__ == "__main__":
    root = Tk()
    app = ImageComparisonApp(root)
    root.mainloop()
