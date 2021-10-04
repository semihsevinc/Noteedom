# -*- coding: utf-8 -*-

import pytesseract
import cv2
import sys
import os
# Word Segmentation
import glob
from PIL import Image
import page
import words
import numpy as np
# HTR
import argparse
import json
from typing import Tuple, List
import editdistance
from path import Path
from dataloader_iam import DataLoaderIAM, Batch
from model import Model, DecoderType
from preprocessor import Preprocessor
from main import *
# App Gui
import PyQt5
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5 import QtCore, QtGui, QtWidgets

# Tesseract(Google) setup for Optic Character Recognition
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
language_path = r"C:\\Program Files\\Tesseract-OCR\\tessdata\\"
language_path_list = glob.glob(language_path + "*.traineddata")

language_names_list = []

for path in language_path_list:
    base_name = os.path.basename(path)
    base_name = os.path.splitext(base_name)[0]
    language_names_list.append(base_name)

font_list = []
font = 20

for font in range(53):
    font += 2
    font_list.append(str(font))


# Gui setup
class NOTEEDOM(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = uic.loadUi("main.ui", self)

        self.image = None
        self.ui.pushButton_open.clicked.connect(self.open)
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.setWindowIcon(QIcon("icon/icon.ico"))
        self.language = "tur"
        self.font_size = "26"
        self.text = 'Noteedom OCR & HTR Application'
        self.ui.textEdit.setFontPointSize(int(self.font_size))

        self.ui.label_ocr.setMouseTracking(True)
        self.ui.label_ocr.installEventFilter(self)
        self.ui.label_ocr.setAlignment(PyQt5.QtCore.Qt.AlignTop)
        self.ui.label_ocr.setStyleSheet("background-image : url(icon/layer_icon.png)")#ÖZELLEŞTİR

        self.ui.label_htr.setMouseTracking(True)
        self.ui.label_htr.installEventFilter(self)
        self.ui.label_htr.setAlignment(PyQt5.QtCore.Qt.AlignTop)
        self.ui.label_htr.setStyleSheet("background-image : url(icon/layer_icon.png)")#ÖZELLEŞTİR

        self.comboBox_lang.addItems(language_names_list)
        self.comboBox_lang.currentIndexChanged['QString'].connect(self.update_lang)
        self.comboBox_lang.setCurrentIndex(language_names_list.index(self.language))

        self.comboBox_font.addItems(font_list)
        self.comboBox_font.currentIndexChanged["QString"].connect(self.update_font_size)
        self.comboBox_font.setCurrentIndex(font_list.index(self.font_size))
        self.setAcceptDrops(True)

        self.ui.scrollArea = QScrollArea()
        self.ui.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.ui.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.ui.scrollArea.setWidgetResizable(True)

    def update_lang(self, val):
        self.language = val

    def update_font_size(self, val):
        self.font_size = val
        self.ui.textEdit.setFontPointSize(int(self.font_size))
        self.ui.textEdit.setText(str(self.text))

    def open(self):
        filename = QFileDialog.getOpenFileName(self, 'Open a file', '',
                                               'Image Files (*.png;*.jpg;*.jpeg;*.jpe;*.jfif)')
        self.image = cv2.imread(str(filename[0]))
        if self.image is None:
            return QMainWindow
        frame = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        image = QImage(frame, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888)
        if self.ui.tabWidget.currentIndex() == 0:
            self.ui.label_ocr.setPixmap(QPixmap.fromImage(image))
        elif self.ui.tabWidget.currentIndex() == 1:
            self.ui.label_htr.setPixmap(QPixmap.fromImage(image))
        else:
            return 0

    # OCR
    def get_ocr(self, img):
        image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        image = cv2.medianBlur(image, 1)
        crop = Image.fromarray(image)
        text = pytesseract.image_to_string(crop, lang=self.language)
        print('Text:', text)
        return text

    # Word Segmentation from full page for HTR
    @staticmethod
    def get_htr(image):
        folder_path = 'segmented'
        folder = os.listdir(folder_path)
        for images in folder:
            if images.endswith(".png"):
                os.remove(os.path.join(folder_path, images))
        image = cv2.imread("image/cropped.png")
        # image = cv2.resize(image, (int(image.shape[1]), 1000))
        rgb_planes = cv2.split(image)
        result_planes = []
        result_norm_planes = []
        for plane in rgb_planes:
            dilated_img = cv2.dilate(plane, np.ones((5, 5), np.uint8))
            bg_img = cv2.medianBlur(dilated_img, 21)
            diff_img = 255 - (cv2.absdiff(plane, bg_img))
            norm_img = cv2.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
            result_planes.append(diff_img)
            result_norm_planes.append(norm_img)
        cv2.merge(result_planes)
        shadows_out_image = cv2.merge(result_norm_planes)

        """shadow removed from image"""
        cv2.imwrite('image/preprocessed.png', shadows_out_image)

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

    def eventFilter(self, source, event):
        width = 0
        height = 0
        if event.type() == QEvent.MouseButtonPress and source is self.ui.label_ocr:
            self.org = self.mapFromGlobal(event.globalPos())
            self.left_top = event.pos()
            self.rubberBand.setGeometry(QRect(self.org, QSize()))
            self.rubberBand.show()
        elif event.type() == QEvent.MouseMove and source is self.ui.label_ocr:
            if self.rubberBand.isVisible():
                self.rubberBand.setGeometry(QRect(self.org, self.mapFromGlobal(event.globalPos())).normalized())
        elif event.type() == QEvent.MouseButtonRelease and source is self.ui.label_ocr:
            if self.rubberBand.isVisible():
                self.rubberBand.hide()
                rect = self.rubberBand.geometry()
                width = rect.width()
                height = rect.height()
            if width >= 5 and height >= 5 and self.image is not None:
                crop = self.image[self.left_top.y():self.left_top.y() + height,
                                  self.left_top.x():self.left_top.x() + width]
                cv2.imwrite("image/cropped.png", crop)
                self.text = self.get_ocr(crop)
                self.ui.textEdit.setText(str(self.text))
            else:
                self.rubberBand.hide()
        elif event.type() == QEvent.MouseButtonPress and source is self.ui.label_htr:
            self.org = self.mapFromGlobal(event.globalPos())
            self.left_top = event.pos()
            self.rubberBand.setGeometry(QRect(self.org, QSize()))
            self.rubberBand.show()
        elif event.type() == QEvent.MouseMove and source is self.ui.label_htr:
            if self.rubberBand.isVisible():
                self.rubberBand.setGeometry(QRect(self.org, self.mapFromGlobal(event.globalPos())).normalized())
        elif event.type() == QEvent.MouseButtonRelease and source is self.ui.label_htr:
            if self.rubberBand.isVisible():
                self.rubberBand.hide()
                rect = self.rubberBand.geometry()
                width = rect.width()
                height = rect.height()
            if width >= 5 and height >= 5 and self.image is not None:
                crop = self.image[self.left_top.y():self.left_top.y() + height,
                       self.left_top.x():self.left_top.x() + width]

                cv2.imwrite("image/cropped.png", crop)
                self.get_htr(self.image)
                os.system("python main.py --mode infer --decoder bestpath")
                self.text = open("HTR_text.txt", "r").readlines()
                self.ui.textEdit.setText(str(self.text))
                f = open("HTR_text.txt", "w")
                f.write("")
            else:
                self.rubberBand.hide()
        else:
            return 0
        return QWidget.eventFilter(self, source, event)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        import time
        splash = QSplashScreen()
        splash.setPixmap(QPixmap('icon/splash.ico'))
        splash.show()
        time.sleep(1)


app = QtWidgets.QApplication(sys.argv)
mainWindow = NOTEEDOM()
window = Window()
mainWindow.showMaximized()
sys.exit(app.exec_())
