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

"""
args:
- pixel_size: inverse of pixel density (mm per dot instead of DPI)
- image_width_mm: width of resulting image panel in mm
- image_height_mm: height of resulting image panel in mm
- min_thickness: minimum thickness of the lithophane image panel in mm
- max_thickness: maximum thickness of the lithophane image panel in mm
"""

def create_lithophane(args, img_path):
    
    # Get image name without extension so we can save result under the same
    name = os.path.splitext(os.path.basename(img_path))[0]

    # Load in image using openCV
    img_bgr = cv2.imread(img_path)

    # Calculate aspect ratio from desired output dimensions
    ar = args.image_width_mm / args.image_height_mm

    # Crop image as close to the proper aspect ratio as possible
    offset
    img_bgr = crop_to_aspect_ratio(img_bgr, ar, True, offset)

    # Compute strech values for each axis to make the result exactly match desired dimensions
    # NOTE: one of the 2 values will always be 1.0

    pass



if __name__ == "__main__":

    img_path = filedialog.askopenfilename(
        title="Select Image File",
        filetypes=[
            ("Image Files", "*.jpg;*.jpeg;*.png;*.gif;*.bmp"),
            ("All Files", "*.*")
        ]
    )

    if img_path:
        print(f"Selected file: {img_path}")

    with open('config.json', 'r') as file:
        args = json.load(file)
    
    create_lithophane(args, img_path)