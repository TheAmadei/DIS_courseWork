import socket
import grpc
import threading
import logging

import image_service_pb2
import image_service_pb2_grpc

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def start_tcp_server():
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
                    logging.error(f"Error receiving color image: {e}")
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
                        logging.debug("Received black-and-white image")
                    except Exception as e:
                        logging.error(f"Error receiving black-and-white images: {e}")
                        break

                # Отправляем изображения на кластер через gRPC для обработки
                logging.debug("Connecting to gRPC cluster to process images")
                try:
                    with grpc.insecure_channel('localhost:50051') as channel:
                        stub = image_service_pb2_grpc.ImageServiceStub(channel)
                        request = image_service_pb2.CompareRequest(color_image=color_image_data, bw_images=bw_images)
                        logging.debug("Sending CompareImages request to gRPC cluster")
                        response = stub.CompareImages(request)
                        logging.debug(f"Received response from gRPC cluster: {response.matching_index}")

                    # Отправляем индекс соответствующего черно-белого изображения обратно клиенту
                    matching_index_to_send = response.matching_index + 1 if response.matching_index >= 0 else 0  # Если -1, отправим 0
                    conn.sendall(matching_index_to_send.to_bytes(4, 'big'))
                    logging.info(f"Sent matching index back to client: {matching_index_to_send}")
                except Exception as e:
                    logging.error(f"Error communicating with gRPC cluster: {e}")

if __name__ == '__main__':
    # Запускаем TCP сервер
    start_tcp_server()
