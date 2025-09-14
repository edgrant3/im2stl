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
        self.mask  = None # boolean numpy array of same H, W as self.image

        self.img_w_mm   = None # width of resulting image panel in mm
        self.img_h_mm   = None # height of resulting image panel in mm

        self.thk_min    = None # minimum thickness of the lithophane image panel in mm
        self.thk_max    = None # maximum thickness of the lithophane image panel in mm

        self.add_border = False
        self.border_width_mm = 6.0 # mm
        self.border_depth_mm = 2.5 # mm
        self.border_corner_radius_mm = 1.5 # mm



    def load_config(self, config_json_file):
        with open(config_json_file, 'r') as file:
            self.args = json.load(file)

    def load_image_from_file(self, img_path):
        self.set_image(cv2.imread(img_path))

    def set_image(self, bgr_image):
        self.image = bgr_image
        if self.mask is None:
            self.mask = np.ones((self.image.shape[:2]))

    def compute_px_size_mm(self):
        self.px_size_mm = min((self.img_w_mm / float(self.image.shape[1])), 
                              (self.img_h_mm / float(self.image.shape[0])))

    def get_pixels_per_mm(self):
        # TODO: get from lithophane GUI after it runs
        return 1.0 / self.compute_px_size_mm()

    def generate_preview_image(self):
        # TODO: use 
        pass

    def create_thickness_image(self):
        # Convert existing image to grayscale
        image_gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        # Map value to thickness
        return self.thk_min + (1.0 - image_gray / 255.0) * (self.thk_max - self.thk_min)

    def create_border_kernel(self):        
        px_per_mm = self.get_pixels_per_mm()

        bw_px  = int(self.border_width_mm * px_per_mm)
        bcr_px = int(min(self.border_corner_radius_mm, self.border_width_mm / 2.0) * px_per_mm)

        k = np.zeros((bw_px, bw_px), dtype=np.uint8)

        if len(k) == 0:
            return k

        k[:, bcr_px:(bw_px - bcr_px)] = 1
        k[bcr_px:(bw_px - bcr_px), :] = 1

        X, Y = np.meshgrid(np.arange(0, bw_px), np.arange(0, bw_px))
        coords = np.stack([X,Y], dtype=np.double)

        inner_corners = [bcr_px-0.5, (-bcr_px % bw_px)-0.5]
        for i in inner_corners:
            for j in inner_corners:
                diff = coords - np.array([i,j]).reshape((2,1,1))
                k[np.where(np.linalg.norm(diff, axis=0) < bcr_px)] = 1
        
        return k


    def create_masked_lithophane_image(self, image_thick):
        # Create border convolution kernel
        border_kernel = self.create_border_kernel()

        # Expand thickness image dimensions to support convolution, padding with zeros
        image_thick = np.pad(image_thick, pad_width=self.border_kernel.shape[0], mode='constant')
        mask = np.pad(self.mask, pad_width=border_kernel.shape[0], mode='constant')

        # Compute border mask via convolution of border kernel on self.mask
        negative_space_indices = np.stack(np.where(mask == 0))
        for i in range(negative_space_indices.shape[1]):
            y, x = negative_space_indices[:,i]
            conv = border_kernel * mask[]

        # Where border mask = True in expanded image = border height

        # Where original mask = True in expanded image = thickness image

        # Return border mask (so gradient can be computed later) and new lithophane image

    def create(self):
        
        image_thick = self.create_thickness_image

        img_h_px, img_w_px = image_thick.shape[:2]
        X, Y = np.meshgrid(np.arange(0, img_w_px), np.arange(0, img_h_px))
        X = X.ravel() / ()


if __name__ == "__main__":

    # TODO: implement convolution-based border generation technique

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