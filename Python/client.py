import socket
import struct

# Настройки клиента
SERVER_IP = 'localhost'
TCP_PORT = 5000

def send_images(color_image_path, bw_image_paths):
    # Подключение к серверу
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_IP, TCP_PORT))

        # Отправка цветного изображения
        with open(color_image_path, 'rb') as f:
            color_image_data = f.read()
        color_image_size = len(color_image_data)
        s.sendall(color_image_size.to_bytes(4, 'big'))
        s.sendall(color_image_data)

        # Отправка черно-белых изображений
        for bw_image_path in bw_image_paths:
            with open(bw_image_path, 'rb') as f:
                bw_image_data = f.read()
            bw_image_size = len(bw_image_data)
            s.sendall(bw_image_size.to_bytes(4, 'big'))
            s.sendall(bw_image_data)

        # Завершение отправки
        s.sendall((0).to_bytes(4, 'big'))  # Отправка 0 для завершения

        # Получение индекса соответствующего изображения
        matching_index_data = s.recv(4)
        matching_index = int.from_bytes(matching_index_data, 'big')
        
        if matching_index == 0:
            print("No matching black-and-white image found.")
        else:
            print(f"Received matching index from server: {matching_index}")

# Пример использования
if __name__ == '__main__':
    color_image_path = 'images/colorImage.jpg'  # Замените на путь к вашему цветному изображению
    bw_image_paths = [ 'images/bwimage2.jpg', 'images/bwimage1.jpg']  # Замените на пути к вашим черно-белым изображениям
    send_images(color_image_path, bw_image_paths)
