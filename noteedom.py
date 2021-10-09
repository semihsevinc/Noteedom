import htr.main
import pytesseract
import cv2
import sys
import os
import numpy as np
# Word Segmentation
import glob
from PIL import Image
import segmentation.page
import segmentation.words
# HTR
import argparse
import json
from typing import Tuple, List
import editdistance
from path import Path
from htr.dataloader_iam import DataLoaderIAM, Batch
from htr.model import Model, DecoderType
from htr.preprocessor import Preprocessor
from htr.main import *
# GUI
import platform
from modules import *
from widgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
import multiprocessing

os.environ["QT_FONT_DPI"] = "96" # FIX Problem for High DPI and Scale above 100%
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
language_path = r"C:\\Program Files\\Tesseract-OCR\\tessdata\\"
language_path_list = glob.glob(language_path + "*.traineddata")

language_names_list = []

for path in language_path_list:
    base_name = os.path.basename(path)
    base_name = os.path.splitext(base_name)[0]
    language_names_list.append(base_name)

font_list = []
for font in range(41):
    font += 10
    font_list.append(str(font))

widgets = None

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Settings.ENABLE_CUSTOM_TITLE_BAR = True
        AppFunctions.setThemeHack(self)
        global widgets
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        widgets = self.ui
        self.setWindowIcon(QIcon("icon/icon.ico"))
        self.title = "NOTEEDOM - For Everyone"
        self.description = "NOTEEDOM APP - Optical Character and Handwritten Text Recognition"
        self.language = "eng"
        self.font_size = "26"
        self.text = 'NOTEEDOM APP - Optical Character and Handwritten Text Recognition'
        self.image = None
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        widgets.textEdit_htr.setFontPointSize(int(self.font_size))
        widgets.textEdit_ocr.setFontPointSize(int(self.font_size))
        self.setWindowTitle(self.title)
        widgets.titleRightInfo.setText(self.description)

        widgets.comboBox_lang.addItems(language_names_list)
        widgets.comboBox_lang.currentTextChanged["QString"].connect(self.update_lang)
        widgets.comboBox_lang.setCurrentIndex(language_names_list.index(self.language))

        widgets.combo_font_ocr.addItems(font_list)
        widgets.combo_font_ocr.currentTextChanged["QString"].connect(self.update_font_size_ocr)
        widgets.combo_font_ocr.setCurrentIndex(font_list.index(self.font_size))

        widgets.combo_font_htr.addItems(font_list)
        widgets.combo_font_htr.currentTextChanged["QString"].connect(self.update_font_size_htr)
        widgets.combo_font_htr.setCurrentIndex(font_list.index(self.font_size))
        self.setAcceptDrops(True)

        widgets.toggleButton.clicked.connect(lambda: UIFunctions.toggleMenu(self, True))
        widgets.btn_bottom_htr.clicked.connect(lambda: UIFunctions.toggleBottom_htr(self, True))
        widgets.btn_bottom_ocr.clicked.connect(lambda: UIFunctions.toggleBottom_ocr(self, True))

        widgets.label_htr.setMouseTracking(True)
        widgets.label_ocr.setMouseTracking(True)
        widgets.label_pdf.setMouseTracking(True)
        widgets.label_htr.installEventFilter(self)
        widgets.label_ocr.installEventFilter(self)
        widgets.label_pdf.installEventFilter(self)
        UIFunctions.uiDefinitions(self)

        # LEFT MENUS
        widgets.btn_htr.clicked.connect(self.buttonClick)
        widgets.btn_ocr.clicked.connect(self.buttonClick)
        widgets.btn_pdf.clicked.connect(self.buttonClick)
        widgets.btn_open.clicked.connect(self.open)
        widgets.btn_bottom_htr.clicked.connect(self.buttonClick)
        widgets.btn_bottom_ocr.clicked.connect(self.buttonClick)

        # SET HOME PAGE AND SELECT MENU
        widgets.stackedWidget.setCurrentWidget(widgets.page_htr)
        widgets.btn_htr.setStyleSheet(UIFunctions.selectMenu(widgets.btn_htr.styleSheet()))

        # EXTRA LEFT BOX
        def openCloseLeftBox():
            UIFunctions.toggleLeftBox(self, True)
        widgets.toggleLeftBox.clicked.connect(openCloseLeftBox)#
        widgets.extraCloseColumnBtn.clicked.connect(openCloseLeftBox)#

        # EXTRA RIGHT BOX
        def openCloseRightBox():
            UIFunctions.toggleRightBox(self, True)
        widgets.settingsTopBtn.clicked.connect(openCloseRightBox)#

    def update_lang(self, val):
        self.language = val

    def update_font_size_ocr(self, val):
        self.font_size = val
        self.ui.textEdit_ocr.setFontPointSize(int(self.font_size))
        self.ui.textEdit_ocr.setText(str(self.text))

    def update_font_size_htr(self, val):
        self.font_size = val
        self.ui.textEdit_htr.setFontPointSize(int(self.font_size))
        self.ui.textEdit_htr.setText(str(self.text))

    def buttonClick(self):
        # GET BUTTON CLICKED
        btn = self.sender()
        btnName = btn.objectName()

        # SHOW HTR PAGE
        if btnName == "btn_htr":
            widgets.stackedWidget.setCurrentWidget(widgets.page_htr)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # SHOW OCR PAGE
        if btnName == "btn_ocr":
            widgets.stackedWidget.setCurrentWidget(widgets.page_ocr)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # SHOW PDF SCANNER PAGE
        if btnName == "btn_pdf":
            widgets.stackedWidget.setCurrentWidget(widgets.page_pdf)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        if btnName == "btn_bottom_htr":
            widgets.stackedWidget.setCurrentWidget(widgets.page_htr)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # SHOW PDF SCANNER PAGE
        if btnName == "btn_bottom_ocr":
            widgets.stackedWidget.setCurrentWidget(widgets.page_ocr)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))


    def open(self):
        filename = QFileDialog.getOpenFileName(self, 'Open a file', '',
                                               'Image Files (*.png;*.jpg;*.jpeg;*.jpe;*.jfif)')
        self.image = cv2.imread(str(filename[0]))
        if self.image is None:
            return QMainWindow
        frame = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        image = QImage(frame, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888)
        if widgets.stackedWidget.currentIndex() == 0:
            widgets.label_htr.setPixmap(QPixmap.fromImage(image))
        elif widgets.stackedWidget.currentIndex() == 1:
            widgets.label_ocr.setPixmap(QPixmap.fromImage(image))
        elif widgets.stackedWidget.currentIndex() == 2:
            widgets.label_pdf.setPixmap(QPixmap.fromImage(image))
        else:
            return 0

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
            norm_img = cv2.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX,
                                     dtype=cv2.CV_8UC1)
            result_planes.append(diff_img)
            result_norm_planes.append(norm_img)
        cv2.merge(result_planes)
        shadows_out_image = cv2.merge(result_norm_planes)

        """shadow removed from image"""
        cv2.imwrite('image/preprocessed.png', shadows_out_image)

        # Crop image and get limiting lines of boxes
        crop = segmentation.page.detection(shadows_out_image)
        boxes = segmentation.words.detection(crop)
        lines = segmentation.words.sort_words(boxes)

        i = 0
        for line in lines:
            text = crop.copy()
            for (x1, y1, x2, y2) in line:
                save = Image.fromarray(text[y1:y2, x1:x2])
                save.save("segmented/" + str(i + 100) + ".png")
                i += 1

    def get_text(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--mode', choices=['train', 'validate', 'infer'], default='infer')
        parser.add_argument('--decoder', choices=['bestpath', 'beamsearch', 'wordbeamsearch'], default='bestpath')
        parser.add_argument('--batch_size', help='Batch size.', type=int, default=100)
        parser.add_argument('--data_dir', help='Directory containing IAM dataset.', type=Path, required=False)
        parser.add_argument('--fast', help='Load samples from LMDB.', action='store_true')
        parser.add_argument('--line_mode', help='Train to read text lines instead of single words.',
                            action='store_true')
        parser.add_argument('--early_stopping', help='Early stopping epochs.', type=int, default=10)
        parser.add_argument('--dump', help='Dump output of NN to CSV file(s).', action='store_true')
        args = parser.parse_args()
        # set chosen CTC decoder
        decoder_mapping = {'bestpath': DecoderType.BestPath,
                           'beamsearch': DecoderType.BeamSearch,
                           'wordbeamsearch': DecoderType.WordBeamSearch}
        decoder_type = decoder_mapping[args.decoder]
        model = Model(open(FilePaths.fn_char_list).read(), decoder_type, must_restore=False, dump=args.dump)

        pp = FilePaths()
        pp.paths = Path(r'segmented').glob('*.png')
        for path in pp.paths:
            infer(model, path)


    def eventFilter(self, source, event):
        width = 0
        height = 0
        if event.type() == QEvent.MouseButtonPress and source is widgets.label_ocr:
            self.org = self.mapFromGlobal(event.globalPos())
            self.left_top = event.pos()
            self.rubberBand.setGeometry(QRect(self.org, QSize()))
            self.rubberBand.show()
        elif event.type() == QEvent.MouseMove and source is widgets.label_ocr:
            if self.rubberBand.isVisible():
                self.rubberBand.setGeometry(QRect(self.org, self.mapFromGlobal(event.globalPos())).normalized())
        elif event.type() == QEvent.MouseButtonRelease and source is widgets.label_ocr:
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
                self.ui.textEdit_ocr.setText(str(self.text))
            else:
                self.rubberBand.hide()
        elif event.type() == QEvent.MouseButtonPress and source is widgets.label_htr:
            self.org = self.mapFromGlobal(event.globalPos())
            self.left_top = event.pos()
            self.rubberBand.setGeometry(QRect(self.org, QSize()))
            self.rubberBand.show()
        elif event.type() == QEvent.MouseMove and source is widgets.label_htr:
            if self.rubberBand.isVisible():
                self.rubberBand.setGeometry(QRect(self.org, self.mapFromGlobal(event.globalPos())).normalized())
        elif event.type() == QEvent.MouseButtonRelease and source is widgets.label_htr:
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
                # p = multiprocessing.Process(target=self.get_text())
                # p.start()
                # p.join()
                # os.system("python htr/main.py --mode infer --decoder bestpath")
                htr.main.main()
                self.text = open("HTR_text.txt", "r").readlines()
                self.ui.textEdit_htr.setText(str(self.text))
                f = open("HTR_text.txt", "w")
                f.write("")
            else:
                self.rubberBand.hide()
        else:
            return 0
        return QWidget.eventFilter(self, source, event)

    def resizeEvent(self, event):
        # Update Size Grips
        UIFunctions.resize_grips(self)

    def mousePressEvent(self, event):
        # SET DRAG POS WINDOW
        self.dragPos = event.globalPos()

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        import time
        splash = QSplashScreen()
        splash.setPixmap(QPixmap('icon/splash.ico'))
        splash.show()
        time.sleep(3)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    Window = MainWindow()
    Window.showMaximized()
    sys.exit(app.exec())
