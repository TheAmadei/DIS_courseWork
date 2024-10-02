import socket
import grpc
from concurrent import futures
from PIL import Image
import numpy as np
import io
import cv2  # Импортируем OpenCV
import logging  # Импортируем модуль логирования

import image_service_pb2
import image_service_pb2_grpc

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ImageService(image_service_pb2_grpc.ImageServiceServicer):
    def CompareImages(self, request, context):
        logging.debug("Received CompareImages request")

        # Получаем цветное изображение
        try:
            color_image = Image.open(io.BytesIO(request.color_image)).convert('RGB')
            color_array = np.array(color_image)
            logging.debug("Color image received and converted to array")
        except Exception as e:
            logging.error(f"Error processing color image: {e}")
            return image_service_pb2.CompareResponse(matching_index=-1)

        # Преобразуем цветное изображение в черно-белое
        try:
            bw_image = cv2.cvtColor(color_array, cv2.COLOR_RGB2GRAY)
            logging.debug("Converted color image to black-and-white")
        except Exception as e:
            logging.error(f"Error converting color image to black-and-white: {e}")
            return image_service_pb2.CompareResponse(matching_index=-1)

        # Сравнение с черно-белыми изображениями из запроса
        matching_index = -1
        for index, bw_image_bytes in enumerate(request.bw_images):
            try:
                logging.debug(f"Comparing with black-and-white image at index {index}")
                bw_array = Image.open(io.BytesIO(bw_image_bytes)).convert('L')
                bw_array_resized = np.array(bw_array)

                # Изменение размера черно-белого изображения до размеров цветного изображения
                bw_array_resized = cv2.resize(bw_array_resized, (color_array.shape[1], color_array.shape[0]))

                # Проверяем размеры
                logging.debug(f"Color image size: {color_array.shape}, BW image size: {bw_array_resized.shape}")
                if color_array.shape[0] != bw_array_resized.shape[0] or color_array.shape[1] != bw_array_resized.shape[1]:
                    logging.warning(f"Image sizes do not match: color {color_array.shape}, bw {bw_array_resized.shape}")
                    continue  # Пропускаем это изображение, если размеры не совпадают

                # Сравнение изображений
                if self.compare_images(bw_image, bw_array_resized):
                    matching_index = index
                    logging.debug(f"Match found with black-and-white image at index {matching_index}")
                    break
            except Exception as e:
                logging.error(f"Error processing black-and-white image at index {index}: {e}")

        logging.debug("Finished processing images, returning response")
        return image_service_pb2.CompareResponse(matching_index=matching_index)

    def compare_images(self, bw_image, bw_image_to_compare):
        # Убедимся, что черно-белое изображение в правильном формате
        if len(bw_image.shape) == 2:
            bw_image = cv2.cvtColor(bw_image, cv2.COLOR_GRAY2BGR)

        # Проверяем, что размеры изображений совпадают
        if bw_image.shape[:2] != bw_image_to_compare.shape[:2]:
            logging.warning(f"Image sizes do not match: bw {bw_image.shape}, bw_compare {bw_image_to_compare.shape}")
            return False

        # Вычисление гистограмм
        hist_bw = cv2.calcHist([bw_image], [0], None, [256], [0, 256])
        hist_bw_compare = cv2.calcHist([bw_image_to_compare], [0], None, [256], [0, 256])

        # Нормализация гистограмм
        cv2.normalize(hist_bw, hist_bw, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        cv2.normalize(hist_bw_compare, hist_bw_compare, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

        # Сравнение гистограмм
        score = cv2.compareHist(hist_bw, hist_bw_compare, cv2.HISTCMP_CORREL)

        # Установка порога для соответствия
        threshold = 0.5  # Этот порог может быть настроен в зависимости от требований

        if score > threshold:
            logging.info(f"Images match with a score of {score}")
            return True
        else:
            logging.info(f"No match. Score: {score}")
            return False

def start_grpc_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    image_service_pb2_grpc.add_ImageServiceServicer_to_server(ImageService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logging.info("gRPC сервер запущен на порту 50051")
    server.wait_for_termination()

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

                # Отправляем изображения на gRPC сервер для обработки
                logging.debug("Connecting to gRPC server to process images")
                try:
                    with grpc.insecure_channel('localhost:50051') as channel:
                        stub = image_service_pb2_grpc.ImageServiceStub(channel)
                        request = image_service_pb2.CompareRequest(color_image=color_image_data, bw_images=bw_images)
                        logging.debug("Sending CompareImages request to gRPC server")
                        response = stub.CompareImages(request)
                        logging.debug(f"Received response from gRPC server: {response.matching_index}")

                    # Отправляем индекс соответствующего черно-белого изображения обратно клиенту
                    # Убедимся, что индекс -1 не отправляется, чтобы избежать недоразумений
                    matching_index_to_send = response.matching_index + 1 if response.matching_index >= 0 else 0  # Если -1, отправим 0
                    conn.sendall(matching_index_to_send.to_bytes(4, 'big'))
                    logging.info(f"Sent matching index back to client: {matching_index_to_send}")
                except Exception as e:
                    logging.error(f"Error communicating with gRPC server: {e}")

if __name__ == '__main__':
    # Запускаем gRPC сервер в отдельном потоке
    import threading
    grpc_thread = threading.Thread(target=start_grpc_server)
    grpc_thread.start()
    
    # Запускаем TCP сервер
    start_tcp_server()
