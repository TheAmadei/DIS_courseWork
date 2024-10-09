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
            # Можно проверить доступность с помощью health-check или ping
            return channel, stub, ip, port
        except Exception as e:
            logging.error(f"Кластер {ip}:{port} недоступен: {e}")
    return None, None, None, None

def start_tcp_server():
    # Загрузка конфигурации кластеров
    clusters = load_config()["clusters"]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 5000))
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

                # Поиск доступного кластера
                logging.debug("Поиск доступного кластера через gRPC")
                channel, stub, ip, port = find_available_cluster(clusters)
                if not stub:
                    logging.error("Нет доступных кластеров")
                    continue

                # Отправляем изображения на кластер через gRPC для обработки
                logging.debug(f"Подключение к кластеру {ip}:{port} для обработки изображений")
                try:
                    request = image_service_pb2.CompareRequest(color_image=color_image_data, bw_images=bw_images)
                    logging.debug("Отправка запроса CompareImages на кластер")
                    response = stub.CompareImages(request)
                    logging.debug(f"Ответ от кластера: {response.matching_index}")

                    # Отправляем индекс соответствующего черно-белого изображения обратно клиенту
                    matching_index_to_send = response.matching_index + 1 if response.matching_index >= 0 else 0  # Если -1, отправим 0
                    conn.sendall(matching_index_to_send.to_bytes(4, 'big'))
                    logging.info(f"Отправлен индекс совпадающего изображения клиенту: {matching_index_to_send}")
                except Exception as e:
                    logging.error(f"Ошибка при работе с кластером {ip}:{port}: {e}")
                finally:
                    # Закрываем канал, когда работа с ним завершена
                    if channel:
                        channel.close()

if __name__ == '__main__':
    # Запускаем TCP сервер
    start_tcp_server()
