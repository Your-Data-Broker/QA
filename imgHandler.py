import cv2
import numpy as np


class ColorObjectDetector:
    def init(self):
        # HSV
        self.color_ranges = {
            'red': [(np.array([0, 120, 70]), np.array([10, 255, 255]))],
            'green': [(np.array([35, 50, 50]), np.array([85, 255, 255]))],
            'blue': [(np.array([100, 150, 0]), np.array([140, 255, 255]))],
            'yellow': [(np.array([20, 100, 100]), np.array([30, 255, 255]))],
            'purple': [(np.array([125, 40, 40]), np.array([145, 255, 255]))],
            'pink': [(np.array([146, 40, 40]), np.array([165, 255, 255]))]
        }

    def process_image(self, image_path, target_colors=['red']):
        img = cv2.imread(image_path)
        if img is None:
            print(f"Помилка: Не вдалося завантажити {image_path}")
            return

        # Невелике розмиття щоб зменшити кількість звуку
        blurred = cv2.GaussianBlur(img, (5, 5), 0)

        # конвертування BGR в HSV
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        output_img = img.copy()
        total_count = 0

        for color_name in target_colors:
            if color_name not in self.color_ranges:
                continue

            # Створення маски для обраного кольору
            mask = None
            for (lower, upper) in self.color_ranges[color_name]:
                if mask is None:
                    mask = cv2.inRange(hsv, lower, upper)
                else:
                    mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lower, upper))

            # 5. Пошук контурів
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            color_count = 0
            for cnt in contours:
                # Фільтрація за площею (ігноруємо надто малі об'єкти)
                if cv2.contourArea(cnt) < 500:
                    continue

                color_count += 1
                total_count += 1

                # 6. Визначення центру об'єкта (Moments)
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])

                    # Малюємо контур та точку центру
                    cv2.drawContours(output_img, [cnt], -1, (0, 255, 0), 2)
                    cv2.drawCircle()

            print(f"Знайдено {color_name} об'єктів: {color_count}")

        # 7. Вивід фінального результату
        print("-" * 25)
        print(f"Detected objects: {total_count}")

        # Візуалізація
        cv2.imshow("Original", img)
        cv2.imshow("Detected Objects", output_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


# Використання
if name == "main":
    detector = ColorObjectDetector()
    detector.process_image('smth.JPG', target_colors=['purple'])
