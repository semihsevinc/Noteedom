from PIL import Image
import cv2
import page

import words
from utils import *
import utils
import numpy as np
import os


folder_path = r'C:\Users\semih\Noteedom\segmented'
#using listdir() method to list the files of the folder
test = os.listdir(folder_path)
#taking a loop to remove all the images
#using ".png" extension to remove only png images
#using os.remove() method to remove the files
for images in test:
    if images.endswith(".png"):
        os.remove(os.path.join(folder_path, images))

    ##### Shadow removing from image #####

image = cv2.cvtColor(cv2.imread("test1.jpg"), cv2.COLOR_BGR2RGB)

#image = cv2.resize(image, (1000,1000))
rgb_planes = cv2.split(image)
result_planes = []
result_norm_planes = []
for plane in rgb_planes:
    dilated_img = cv2.dilate(plane, np.ones((5,5), np.uint8))
    bg_img = cv2.medianBlur(dilated_img, 21)
    diff_img = 255 - (cv2.absdiff(plane, bg_img) )
    norm_img = cv2.normalize(diff_img,None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
    result_planes.append(diff_img)
    result_norm_planes.append(norm_img)
result = cv2.merge(result_planes)
shadows_out_image = cv2.merge(result_norm_planes)
print(shadows_out_image.shape[0])

    ##### shadow removed from image #####

# shadows out image saved JUST IN CASE #
cv2.imwrite('shadows.png', shadows_out_image)

# Crop image and get limiting lines of boxes

crop = page.detection(shadows_out_image)
boxes = words.detection(crop)
lines = words.sort_words(boxes)


i = 0
for line in lines:
    text = crop.copy()
    for (x1, y1, x2, y2) in line:

        save = Image.fromarray(text[y1:y2, x1:x2])
        save.save("segmented/" + str(i + 100) + ".png")
        i += 1
