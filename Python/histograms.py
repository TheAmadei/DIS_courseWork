import cv2
import numpy as np
import matplotlib.pyplot as plt

def calculate_and_plot_histograms(color_image_path, bw_image_paths):
    # Загрузка цветного изображения
    color_image = cv2.imread(color_image_path)
    color_image_gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

    # Вычисление гистограммы цветного изображения
    hist_color = cv2.calcHist([color_image_gray], [0], None, [256], [0, 256])
    hist_color = hist_color / hist_color.sum()  # Нормализация

    # Хранение результатов
    correlations = []
    histograms_bw = []

    for bw_image_path in bw_image_paths:
        # Загрузка черно-белого изображения
        bw_image = cv2.imread(bw_image_path, cv2.IMREAD_GRAYSCALE)

        # Вычисление гистограммы черно-белого изображения
        hist_bw = cv2.calcHist([bw_image], [0], None, [256], [0, 256])
        hist_bw = hist_bw / hist_bw.sum()  # Нормализация
        histograms_bw.append(hist_bw)

        # Сравнение гистограмм
        correlation = cv2.compareHist(hist_color, hist_bw, cv2.HISTCMP_CORREL)
        correlations.append(correlation)

    # Построение графиков гистограмм
    plt.figure(figsize=(12, 8))

    # Гистограмма цветного изображения
    plt.subplot(2, 2, 1)
    plt.plot(hist_color, color='blue', label='Цветное изображение (градации серого)')
    plt.title('Гистограмма цветного изображения (градации серого)', fontsize=12)
    plt.xlabel('Интенсивность пикселя', fontsize=10)
    plt.ylabel('Нормированная частота', fontsize=10)
    plt.legend()

    # Гистограммы черно-белых изображений
    for i, hist_bw in enumerate(histograms_bw):
        plt.subplot(2, 2, i + 2)
        plt.plot(hist_bw, color='black', label=f'Чёрно-белое изображение {i + 1}')
        plt.title(f'Гистограмма чёрно-белого изображения {i + 1}', fontsize=12)
        plt.xlabel('Интенсивность пикселя', fontsize=10)
        plt.ylabel('Нормированная частота', fontsize=10)
        plt.legend()

    plt.tight_layout()
    plt.show()

    # Визуализация корреляции
    plt.figure(figsize=(6, 4))
    bars = plt.bar(range(len(correlations)), correlations, color=['red' if c < 0.9 else 'green' for c in correlations])
    plt.xticks(range(len(correlations)), [f'ЧБ изображение {i + 1}' for i in range(len(correlations))])
    plt.ylim(0, 1)
    plt.title('Коэффициент корреляции', fontsize=14)
    plt.ylabel('Корреляция', fontsize=12)
    plt.xlabel('Изображения', fontsize=12)
    for bar, correlation in zip(bars, correlations):
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval, f'{correlation:.2f}', ha='center', va='bottom', fontsize=10)
    plt.show()

# Укажите пути к вашим изображениям
color_image_path = "images/Color/test.png"
bw_image_paths = ["images/BW/bwimage1.jpg", "images/BW/good.jpg"]

calculate_and_plot_histograms(color_image_path, bw_image_paths)
