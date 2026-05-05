import cv2

img = cv2.imread("testImg.jpg") #3D

res_y = len(img)
res_x = len(img[0])

class shape():
    def __init__(self):
        self.x_max = res_x
        self.x_min = 0
        self.y_max = res_y
        self.y_min = 0
        self.rgb = [256, 256, 256]

r, g, b = int(input("r: ")), int(input("g: ")), int(input("b: "))


