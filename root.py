import cv2
import numpy as np


class ColorObjectDetector:
    def __init__(self):
        # HSV:
        self.color_ranges = {
            "red": [(np.array([0, 120, 70]), np.array([10, 255, 255]))],
            "green": [(np.array([35, 50, 50]), np.array([85, 255, 255]))],
            "blue": [(np.array([100, 150, 50]), np.array([124, 255, 255]))],
            "yellow": [(np.array([20, 100, 100]), np.array([30, 255, 255]))],
            "purple": [(np.array([125, 40, 40]), np.array([145, 255, 255]))],
            "pink": [(np.array([146, 40, 40]), np.array([165, 255, 255]))],
        }

    def process_image(self, image_path, target_colors):
        originalImg = cv2.imread(image_path)
        if originalImg is None:
            print(f"Помилка: Не вдалося завантажити {image_path}")
            return

        # розмиття для точніших контурів

        img = cv2.GaussianBlur(originalImg, (5, 5), 0)

        # конвертування BGR в HSV

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        outputImg = originalImg.copy()

        for colorName in target_colors:
            if colorName not in self.color_ranges:
                continue

            # Створення маски для обраного кольору
            mask = None
            for lower, upper in self.color_ranges[colorName]:
                if mask is None:
                    mask = cv2.inRange(hsv, lower, upper)
                else:
                    mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lower, upper))

            # Пошук контурів
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            colorCount = 0
            for contour in contours:
                # Ігнорування маленьких фігур
                if cv2.contourArea(contour) < 500:
                    continue

                colorCount += 1

                # Визначення центру об'єкта (Moments)
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])

                    # Малюємо контур та точку центру
                    cv2.drawContours(outputImg, [contour], -1, (0, 255, 0), 2)
                    cv2.circle(outputImg, (cx, cy), 5, (176, 255, 146), -1)

            print(f"Detected {colorCount} {colorName} objects")

        # Візуалізація
        cv2.imshow("Original", originalImg)
        cv2.imshow("Detected Objects", outputImg)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


# Використання
if __name__ == "__main__":
    detector = ColorObjectDetector()

    colors = ""
    for colorName in detector.color_ranges.keys():
        colors += colorName + " "

    print(f"Available colors: {colors}")
    selected_colors = input("Choose an available color: ")
    actualSelected = []

    for colorName in selected_colors.split():
        actualSelected.append(colorName)

    detector.process_image("origImg.tiff", target_colors=actualSelected)
