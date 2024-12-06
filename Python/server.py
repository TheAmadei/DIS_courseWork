import socket
import grpc
import threading
import logging
import json  # Для работы с конфигурационным файлом

import image_service_pb2
import image_service_pb2_grpc

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Функция для загрузки конфигурации кластеров
def load_config():
    with open('config.json', 'r') as file:
        return json.load(file)

# Функция для поиска свободного кластера
def find_available_cluster(clusters):
    for cluster in clusters:
        ip = cluster["ip"]
        port = cluster["port"]
        try:
            # Возвращаем открытый канал и stub, не закрываем его сразу
            channel = grpc.insecure_channel(f'{ip}:{port}')
            stub = image_service_pb2_grpc.ImageServiceStub(channel)
            return channel, stub, ip, port
        except Exception as e:
            logging.error(f"Кластер {ip}:{port} недоступен: {e}")
    return None, None, None, None

# Функция для разбиения черно-белых изображений между кластерами
def distribute_bw_images(bw_images, num_clusters):
    """
    Разделяет массив черно-белых изображений на части для кластеров.

    :param bw_images: Список черно-белых изображений.
    :param num_clusters: Количество кластеров.
    :return: Список списков, где каждый вложенный список - часть для одного кластера.
    """
    if num_clusters >= len(bw_images):
        return [[bw_image] for bw_image in bw_images]
    distributed = [[] for _ in range(num_clusters)]
    for i, bw_image in enumerate(bw_images):
        distributed[i % num_clusters].append(bw_image)
    return distributed

def process_images(color_image_data, bw_images, clusters):
    """
    Обрабатывает изображения, распределяя задачи между кластерами.

    :param color_image_data: Данные цветного изображения.
    :param bw_images: Список черно-белых изображений.
    :param clusters: Список кластеров (IP и порты).
    :return: Итоговый индекс совпадающего изображения.
    """
    num_clusters = len(clusters)
    parts = distribute_bw_images(bw_images, num_clusters)
    results = []

    for i, part in enumerate(parts):
        channel, stub, ip, port = find_available_cluster(clusters)
        if not stub:
            logging.error(f"Кластер {ip}:{port} недоступен для части {i}")
            continue

        try:
            # Формируем запрос с частью черно-белых изображений
            request = image_service_pb2.CompareRequest(color_image=color_image_data, bw_images=part)
            logging.debug(f"Отправка части {i} на кластер {ip}:{port}")
            response = stub.CompareImages(request)
            logging.debug(f"Ответ от кластера {ip}:{port}: {response.matching_index}")
            results.append((response.matching_index, i, len(part), ip, port))  # Храним результаты
        except Exception as e:
            logging.error(f"Ошибка при обработке части {i} на {ip}:{port}: {e}")
        finally:
            if channel:
                channel.close()

    # Сводим результаты
    final_index = -1
    for match_index, part_index, part_size, ip, port in results:
        if match_index >= 0:
            # Корректируем индекс с учетом смещения и добавляем 1
            final_index = match_index + part_index * part_size + 1
            break

    return final_index

def start_tcp_server():
    # Загрузка конфигурации кластеров
    clusters = load_config()["clusters"]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('192.168.56.1', 5000))
        s.listen()
        logging.info("TCP сервер запущен на порту 5000")
        
        while True:
            conn, addr = s.accept()
            with conn:
                logging.info(f'Подключено к {addr}')
                
                # Получаем цветное изображение
                try:
                    color_image_size = int.from_bytes(conn.recv(4), 'big')
                    color_image_data = conn.recv(color_image_size)
                    logging.debug("Color image received from client")
                except Exception as e:
                    logging.error(f"Ошибка при получении цветного изображения: {e}")
                    continue

                # Получаем черно-белые изображения
                bw_images = []
                while True:
                    try:
                        bw_image_size = int.from_bytes(conn.recv(4), 'big')
                        if not bw_image_size:
                            break
                        bw_image_data = conn.recv(bw_image_size)
                        bw_images.append(bw_image_data)
                        logging.debug("Получено черно-белое изображение")
                    except Exception as e:
                        logging.error(f"Ошибка при получении черно-белых изображений: {e}")
                        break

                # Распределяем задачи между кластерами и обрабатываем изображения
                logging.debug("Распределение задач между кластерами")
                final_index = process_images(color_image_data, bw_images, clusters)

                # Отправляем результат клиенту
                try:
                    matching_index_to_send = final_index if final_index >= 0 else 0
                    conn.sendall(matching_index_to_send.to_bytes(4, 'big'))
                    logging.info(f"Отправлен индекс совпадающего изображения клиенту: {matching_index_to_send}")
                except Exception as e:
                    logging.error(f"Ошибка при отправке результата клиенту: {e}")

if __name__ == '__main__':
    # Запускаем TCP сервер
    start_tcp_server()
