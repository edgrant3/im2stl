import json
import cv2
import os

import tkinter as tk
from tkinter import filedialog
import numpy as np
import matplotlib.pyplot as plt

from utils import STL_Tri, \
    crop_to_aspect_ratio, \
    show_img, \
    write_binary_stl, \
    convert_stl_to_3mf

class LithophaneGenerator():

    def __init__(self):

        self.image = None # BGR image from opencv
        self.mask  = None

        self.px_size_mm = None # inverse of pixel density (mm per dot instead of DPI)
        self.img_w_mm   = None # width of resulting image panel in mm
        self.img_h_mm   = None # height of resulting image panel in mm
        self.thk_min    = None # minimum thickness of the lithophane image panel in mm
        self.thk_max    = None # maximum thickness of the lithophane image panel in mm

    def load_config(self, config_json_file):
        with open(config_json_file, 'r') as file:
            self.args = json.load(file)

    def load_image_from_file(self, img_path):
        self.set_image(cv2.imread(img_path))

    def set_image(self, bgr_image):
        self.image = bgr_image
        self.mask = np.ones((self.image.shape[:2]))

    def compute_px_size_mm(self):
        self.px_size_mm = min((self.img_w_mm / float(self.image.shape[1])), 
                              (self.img_h_mm / float(self.image.shape[0])))

    def create(self):
        
        # TODO: Compute strech values for each axis to make the result exactly match desired dimensions
        # NOTE: one of the 2 values will always be 1.0

        pass


if __name__ == "__main__":

    lithgen = LithophaneGenerator()

    img_path = filedialog.askopenfilename(
        title="Select Image File",
        filetypes=[
            ("Image Files", "*.jpg;*.jpeg;*.png;*.gif;*.bmp"),
            ("All Files", "*.*")
        ]
    )

    if img_path:
        print(f"Selected file: {img_path}")

    lithgen.load_image_from_file(img_path)
    lithgen.load_config('config.json')
    lithgen.create()