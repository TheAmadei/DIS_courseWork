import cv2

# Загрузка цветного изображения
color_image = cv2.imread('images/test.png')

# Преобразование в черно-белое изображение
bw_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

# Сохранение черно-белого изображения
cv2.imwrite('images/bwimage2.jpg', bw_image)

# Отображение изображений (по желанию)
cv2.imshow('Color Image', color_image)
cv2.imshow('Black and White Image', bw_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
