import cv2
import pytesseract
import numpy as np


class Ocr(object):

    def __init__(self, path_image):
        self.path = path_image
        self.start_ocr()

    def start_ocr(self):
        img = cv2.imread(self.path)  # Alternatively: can be skipped if you have a Blackwhite image
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        gray, img_bin = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        gray = cv2.bitwise_not(img_bin)
        kernel = np.ones((2, 1), np.uint8)
        img = cv2.erode(gray, kernel, iterations=1)
        img = cv2.dilate(img, kernel, iterations=1)
        out_below = pytesseract.image_to_string(img)
        return out_below
