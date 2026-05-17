import cv2 # Потрібна для читання зображення та алгоритму Сузукі (знаходження контурів)
import numpy as np # Потрібна для зручної роботи з масивами (списками) а також для деяких типів данних
import ctypes # Потрібна для підключення .so бібліотеки з кодом на ASM
import os # Потрібна для зручного склеювання шляху до .so бібліотеки 

# Налаштування .so бібліотеки (знаходження шляху до неї, задання типів данних її аргументів тощо)
lib_path = os.path.join(os.path.dirname(__file__), 'backend.so')
backend = ctypes.CDLL(lib_path)

# Вказуємо суворі типи аргументів, щоб уникнути SegFault
backend.process_single_pass.argtypes = [
    ctypes.POINTER(ctypes.c_uint8),  # bgr_pixels (вхідне зображення)
    ctypes.POINTER(ctypes.c_uint8),  # masks_out (вихідні маски)
    ctypes.c_int,                    # total_pixels (кількість пікселів)
    ctypes.POINTER(ctypes.c_uint8),  # flat_lower_bounds (нижні межі)
    ctypes.POINTER(ctypes.c_uint8),  # flat_upper_bounds (верхні межі)
    ctypes.c_int                     # num_targets (кількість кольорів)
]


# Контстати кольорів (діапазони)
# Всі значення мають тип uint8 (unsigned integer 8 bits long)
COLOR_RANGES = {
    "red": (np.array([0, 120, 70], dtype=np.uint8), np.array([10, 255, 255], dtype=np.uint8)),
    "green": (np.array([35, 50, 50], dtype=np.uint8), np.array([85, 255, 255], dtype=np.uint8)),
    "blue": (np.array([100, 150, 50], dtype=np.uint8), np.array([124, 255, 255], dtype=np.uint8)),
    "yellow": (np.array([20, 100, 100], dtype=np.uint8), np.array([30, 255, 255], dtype=np.uint8)),
    "purple": (np.array([125, 40, 40], dtype=np.uint8), np.array([145, 255, 255], dtype=np.uint8)),
    "pink": (np.array([146, 40, 40], dtype=np.uint8), np.array([165, 255, 255], dtype=np.uint8)),
}

# Основна функція, що викликає ASM код, передаючи йому аргументи, та повертаючи його результат
def call_backend_single_pass(bgr_img, target_colors):

    height, width, _ = bgr_img.shape
    num_targets = len(target_colors)
    
    # Готуємо пам'ять для результату: 3D масив масок (Колір, Висота, Ширина)
    # np.zeros гарантує C-contiguous блок пам'яті (заповнений нулями)
    masks_out = np.zeros((num_targets, height, width), dtype=np.uint8)
    
    # Готуємо плоскі масиви меж для ASM (щоб передати їх як прості uint8_t вказівники)
    flat_lower = np.concatenate([COLOR_RANGES[c][0] for c in target_colors])
    flat_upper = np.concatenate([COLOR_RANGES[c][1] for c in target_colors])
    total_pixels = height * width
    
    # Викликаємо ASM код
    backend.process_single_pass(
        bgr_img.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        masks_out.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        total_pixels,
        flat_lower.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        flat_upper.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        num_targets
    )

    return masks_out

# OpenCV фронтенд та знаходження контурів (занадто складно на ASM)
def draw_objects_and_count(mask, output_img, color_name):
    
    # Шукаємо контури чеерез findContours (алгоритм Сузукі-Абе, занадто складний щоб написати на ASM)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    count = 0
    for contour in contours:
        if cv2.contourArea(contour) < 500: # Ігноруємо шуми 
            continue
            
        count += 1
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            
            # Малюємо контури
            cv2.drawContours(output_img, [contour], -1, (0, 255, 0), 2)
            cv2.circle(output_img, (cx, cy), 5, (176, 255, 146), -1)
            
    print(f"Detected {count} {color_name} objects")

def process_image(image_path, target_colors):
    original_img = cv2.imread(image_path)
    if original_img is None:
        print(f"Помилка: Не вдалося завантажити {image_path}")
        return
        
    # Блюр залишаємо в Python (це попередня обробка)
    img_blurred = cv2.GaussianBlur(original_img, (5, 5), 0)
    
    # Гарантуємо, що зображення лежить суцільним шматком у пам'яті
    if not img_blurred.flags['C_CONTIGUOUS']:
        img_blurred = np.ascontiguousarray(img_blurred)
        
    output_img = original_img.copy()
    
    # Виклик ASM коду
    # Передаємо картинку 1 раз і отримуємо готові маски 
    masks = call_backend_single_pass(img_blurred, target_colors)
    
    # Фронтенд-відмальовка результатів
    for i, color_name in enumerate(target_colors):
        draw_objects_and_count(masks[i], output_img, color_name)
        
    cv2.imshow("Original", original_img)
    cv2.imshow("Detected Objects", output_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Точка фходу 
if __name__ == "__main__":
    available_colors = " ".join(COLOR_RANGES.keys())
    print(f"Available colors: {available_colors}")
    
    user_input = input("Choose available colors (space separated): ")
    selected_colors = [c for c in user_input.split() if c in COLOR_RANGES]
    
    if not selected_colors:
        print("No valid colors selected. Exiting.")
    else:
        process_image("origImg.jpg", target_colors=selected_colors)
