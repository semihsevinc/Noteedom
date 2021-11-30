"""     Purpose of Using: Word Segmentation from Image Including Handwritten Text
#       Input: Image Including Lines of Handwritten Words
#       Output: Sorted and Cropped Handwritten Word Images (Located: folder_path = "path/to/images")
"""
from PIL import Image
import cv2
import numpy as np
import os
import segmentation_words
import segmentation_page

def get_segmented():
    """Cleaning Segmentation Folder"""
    folder_path = 'segment'
    folder = os.listdir(folder_path)
    for images in folder:
        if images.endswith(".png"):
            os.remove(os.path.join(folder_path, images))

    """Image Preprocessing (getting binary image for text recognition)"""
    image = cv2.imread("image/cropped.png")
    rgb_planes = cv2.split(image)
    result_planes = []
    result_norm_planes = []
    for plane in rgb_planes:
        dilated_img = cv2.dilate(plane, np.ones((5, 5), np.uint8))
        diff_img = 255 - (cv2.absdiff(plane, dilated_img))
        norm_img = cv2.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
        result_planes.append(diff_img)
        result_norm_planes.append(norm_img)
    cv2.merge(result_planes)
    shadows_out_image = cv2.merge(result_norm_planes)
    T, thresholded_image = cv2.threshold(shadows_out_image, 221, 255, cv2.THRESH_BINARY)

    cv2.imwrite("image/thresholded.png", thresholded_image)

    """shadow removed from image"""
    cv2.imwrite('image/preprocessed.png', shadows_out_image)

    # Crop image and get limiting lines of boxes
    crop = segmentation_page.detection(thresholded_image)
    boxes = segmentation_words.detection(crop)
    lines = segmentation_words.sort_words(boxes)

    """Saving sorted words to dedicated folder"""
    i = 0
    for line in lines:
        text = crop.copy()
        for (x1, y1, x2, y2) in line:
            save = Image.fromarray(text[y1:y2, x1:x2])
            save.save("segment/" + str(i + 100) + ".png")
            i += 1