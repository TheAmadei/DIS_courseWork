import unittest
from unittest.mock import patch, MagicMock
import image_service_pb2_grpc
import image_service_pb2

# Пример теста для метода обработки изображений
class TestImageProcessing(unittest.TestCase):
    @patch.object(image_service_pb2_grpc.ImageServiceStub, 'CompareImages')
    def test_process_images(self, mock_compare_images):
        # Подготовка мока для CompareImages
        mock_compare_images.return_value = image_service_pb2.CompareResponse(matching_index=1)

        # Эмулируем данные изображения и кластеры
        color_image_data = b"color_image_data"  # Это будет байтовая строка изображения
        bw_images = [b"bw_image_1", b"bw_image_2"]  # Список черно-белых изображений
        clusters = ['192.168.56.1:50051', '192.168.56.2:50052']  # Список кластеров

        # Функция для обработки изображений
        def process_images(color_image_data, bw_images, clusters):
            # Эмулируем взаимодействие с кластером
            for cluster in clusters:
                # Используем мокированный метод CompareImages
                response = mock_compare_images(image_service_pb2.CompareRequest(
                    color_image=color_image_data, bw_images=bw_images))
                if response.matching_index != -1:
                    return response.matching_index
            return -1

        # Тестируем
        result = process_images(color_image_data, bw_images, clusters)

        # Проверяем, что результат верный
        self.assertEqual(result, 1)
        mock_compare_images.assert_called_once()  # Проверяем, что метод был вызван

if __name__ == '__main__':
    unittest.main()
