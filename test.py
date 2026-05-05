import cv2

r, g, b = int(input("r: ")), int(input("g: ")), int(input("b: "))

img = cv2.imread("testImg.jpg") #3D

print(len(img))
print(len(img[0]))
