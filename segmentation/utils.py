# -*- coding: utf-8 -*-


import numpy as np
import cv2


min_height = 400


def implt(img, cmp=None, t=''):
    """Show image using plt."""
    cv2.namedWindow('Bounding Box', cv2.WINDOW_AUTOSIZE)
    cv2.imshow('Bounding Box', img)
    cv2.waitKey(0)


def resize(img, height=min_height, allways=False):
    """Resize image to given height."""
    min_height = img.shape[0]
    # print(img.shape[1], img.shape[0])
    if (img.shape[0] > height or allways):
        rat = height / img.shape[0]
        return cv2.resize(img, (int(rat * img.shape[1]), height))

    return img


def ratio(img, height=min_height):
    """Getting scale ratio."""
    return img.shape[0] /height


def img_extend(img, shape):
    """Extend 2D image (numpy array) in vertical and horizontal direction.
    Shape of result image will match 'shape'
    Args:
        img: image to be extended
        shape: shape of result image
    Returns:
        Extended image
    """
    x = np.zeros(shape, np.uint8)
    x[:img.shape[0], :img.shape[1]] = img
    return x