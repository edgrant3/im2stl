import tkinter as tk
import cv2
import re
import numpy as np
from enum import Enum
from tkinter import N, S, E, W
from tkinter import filedialog
from PIL import Image, ImageTk

from utils import rgb2hex, cv2_to_tk, convert_numeric_string

class RectLoc(Enum):
    NULL = -1
    TOP_LEFT = 0
    TOP_RIGHT = 1
    BOTTOM_LEFT = 2
    BOTTOM_RIGHT = 3
    TOP = 4
    RIGHT = 5
    BOTTOM = 6
    LEFT = 7
    CENTER = 8

rect_location_props = \
{
    RectLoc.TOP_LEFT: {
        'flip_x': RectLoc.TOP_RIGHT,
        'flip_y': RectLoc.BOTTOM_LEFT,
        'cursor': "top_left_corner",
        'coord_idx': np.array([0,1])
    },

    RectLoc.TOP_RIGHT: {
        'flip_x': RectLoc.TOP_LEFT,
        'flip_y': RectLoc.BOTTOM_RIGHT,
        'cursor': "top_right_corner",
        'coord_idx': np.array([2,1])
    },

    RectLoc.BOTTOM_LEFT: {
        'flip_x': RectLoc.BOTTOM_RIGHT,
        'flip_y': RectLoc.TOP_LEFT,
        'cursor': "bottom_left_corner",
        'coord_idx': np.array([0,3])
    },

    RectLoc.BOTTOM_RIGHT: {
        'flip_x': RectLoc.BOTTOM_LEFT,
        'flip_y': RectLoc.TOP_RIGHT,
        'cursor': "bottom_right_corner",
        'coord_idx': np.array([2,3])
    },

    RectLoc.TOP: {
        'flip_x': RectLoc.TOP,
        'flip_y': RectLoc.BOTTOM,
        'cursor': "bottom_side",
        'coord_idx': np.array([1])
    },

    RectLoc.RIGHT: {
        'flip_x': RectLoc.LEFT,
        'flip_y': RectLoc.RIGHT,
        'cursor': "left_side",
        'coord_idx': np.array([2])
    },

    RectLoc.BOTTOM: {
        'flip_x': RectLoc.BOTTOM,
        'flip_y': RectLoc.TOP,
        'cursor': "top_side",
        'coord_idx': np.array([3])
    },

    RectLoc.LEFT: {
        'flip_x': RectLoc.RIGHT,
        'flip_y': RectLoc.LEFT,
        'cursor': "right_side",
        'coord_idx': np.array([0])
    },

    RectLoc.CENTER: {
        'flip_x': RectLoc.CENTER,
        'flip_y': RectLoc.CENTER,
        'cursor': "diamond_cross",
        'coord_idx': np.array([0,1,2,3])
    },

    RectLoc.NULL: {
        'flip_x': RectLoc.NULL,
        'flip_y': RectLoc.NULL,
        'cursor': None,
        'coord_idx': None
    }
}


class LithGUI:
    ALL_PADDING = 10
    CONTROL_PANEL_WIDTH = 0.2
    CANVAS_COLOR = rgb2hex((127, 127, 127))
    CROP_COLOR = rgb2hex((255, 0, 0))
    LARGE_PX_INCREMENT = 10
    SMALL_PX_INCREMENT = 1
    DEFAULT_CANVAS_CURSOR = "fleur"
    DPMM = 12 # default pixels per millimeter

    def __init__(self, fullscreen=False):
        self.root = tk.Tk()
        self.root.title("Lithophane Generator")
        self.root.focus_force()

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.fullscreen = fullscreen
        if fullscreen:
            self.root.attributes('-fullscreen', True)
        else:
            screen_w, screen_h = self.get_screen_dims()
            self.root_w = int(round(0.75 * screen_w))
            self.root_h = int(round(0.75 * screen_h))
            offset_x = int(round((screen_w - self.root_w) / 2))
            offset_y = int(round((screen_h - self.root_h) / 2))
            self.root.geometry(f"{self.root_w}x{self.root_h}+{offset_x}+{offset_y}")

        self.crop_width_mm = None
        self.crop_height_mm = None

        self.image_path = None
        self.original_image = None # numpy.ndarray in BGR from cv2
        self.intermediate_image = None # numpy.ndarray in BGR from cv2
        self.tk_image = None # image to render to GUI, converted from cv2-manipulated image
        
        self.canvas = None
        self.control_panel = None
        self.active_item_tag = None
        self.active_item_loc = None

        self._canvas_tag_image = "canvas_image"
        self._canvas_tag_rect = "cropping_rectangle"
        self._canvas_items = {}

        self.create_widgets()
        self.bind_events()

        self.setup_is_complete = False
        self.root.after(100, self.mark_setup_complete)

        self.root.mainloop()

    def create_widgets(self):
        self.create_canvas()
        self.create_control_panel()
        self.arrange_widgets()

    def create_canvas(self):
        if self.canvas is not None:
            self.canvas.delete('all')
            self.canvas.destroy()

        self.canvas_w = int(round((1.0 - self.CONTROL_PANEL_WIDTH) * self.root_w))
        self.canvas_h = self.root_h

        self.canvas = tk.Canvas(self.root, width=self.canvas_w, height=self.canvas_h, 
                                bg=self.CANVAS_COLOR, borderwidth=0, highlightthickness=0)
        
    def create_control_panel(self):
        if self.control_panel is not None:
            self.control_panel.destroy()

        # Panel Frame
        self.control_panel = tk.LabelFrame(self.root, background="white", text="Settings")
        # self.control_panel.grid_rowconfigure(0, weight=1)
        self.control_panel.grid_columnconfigure(0, weight=1)
        control_panel_cols = 2

        # Add + Pack entry fields for crop W and H in mm and corresponding labels
        self.mm_W_entry_str = tk.StringVar()
        self.mm_H_entry_str = tk.StringVar()
        self.mm_W_entry = tk.Entry(self.control_panel, borderwidth=3, textvariable=self.mm_W_entry_str)
        self.mm_H_entry = tk.Entry(self.control_panel, borderwidth=3, textvariable=self.mm_H_entry_str)
        mm_W_entry_label = tk.Label(self.control_panel, text="Width (mm)")
        mm_H_entry_label = tk.Label(self.control_panel, text="Height (mm)")

        mm_W_entry_label.grid(row=0, column=0, sticky=W, padx=self.ALL_PADDING)
        mm_H_entry_label.grid(row=0, column=1, sticky=W, padx=self.ALL_PADDING)
        self.mm_W_entry.grid(row=1, column=0)
        self.mm_H_entry.grid(row=1, column=1)

        # Add + Pack CheckBox for aspect ratio lock
        self.ar_lock = tk.IntVar(value=1)
        self.ar_lock_checkbox = tk.Checkbutton(self.control_panel, 
                                               text="Lock Aspect Ratio", 
                                               variable=self.ar_lock, 
                                               background=rgb2hex((255,255,255)),
                                               onvalue=1, offvalue=0)

        self.ar_lock_checkbox.grid(row=2, column=0, columnspan=control_panel_cols, sticky=W)

        # Add + Pack Entry, Label, and Text note for pixel_size in mm
        self.pixel_size_entry = tk.Entry(self.control_panel, borderwidth=3)
        pixel_size_entry_label = tk.Label(self.control_panel, text="Pixel Size (mm)")
        pixel_size_entry_label.grid(row=3, column=0, sticky=W)
        self.pixel_size_entry.grid(row=4, column=0)

        pixel_size_entry_text_note = tk.Text(self.control_panel)
        pixel_size_note = 'Setting "Pixel Size" will downsample the source image to save memory and expedite mesh generation.\n\n' + \
        'There is no need to have a finer pixel resolution than a 3D printer can achieve (i.e. pixel size should roughly match 3D printer nozzle diameter)'
        pixel_size_entry_text_note.insert(tk.END, pixel_size_note)
        self.control_panel.grid_rowconfigure(5, weight=1)
        pixel_size_entry_text_note.grid(row=5, column=0, sticky=N+S+E+W, columnspan=control_panel_cols)

        # Add + Pack image loading button
        self.load_img_button = tk.Button(self.control_panel, command=self.load_image, text="Load Image")
        self.load_img_button.grid(row=6, column=0, sticky=S)

    def arrange_widgets(self):
        self.control_panel.grid(row=0, column=0, padx=self.ALL_PADDING, pady=self.ALL_PADDING, sticky=N+S+E+W)
        self.canvas.grid(row=0, column=1, padx=self.ALL_PADDING, pady=self.ALL_PADDING)

    def bind_events(self):
        self.root.bind('<Escape>', lambda x: self.root.destroy())

        # Bind canvas image move to arrow keys
        inc = self.SMALL_PX_INCREMENT
        self.root.bind(   '<Up>', lambda event: self.move_canvas_image( 0, -inc))
        self.root.bind( '<Down>', lambda event: self.move_canvas_image( 0,  inc))
        self.root.bind( '<Left>', lambda event: self.move_canvas_image(-inc,  0))
        self.root.bind('<Right>', lambda event: self.move_canvas_image( inc,  0))

        # Bind canvas image move to click and drag
        self.canvas.bind('<ButtonPress-1>', self.handle_canvas_click)
        self.canvas.bind('<B1-Motion>', lambda event: self.handle_canvas_drag(event))
        self.canvas.bind('<ButtonRelease-1>', self.handle_canvas_click_release)

        # Bind un-clicked mouse motion
        self.canvas.bind('<Motion>', lambda event: self.handle_canvas_motion(event))

        # Bind canvas image scaling to mouse scroll wheel
        self.root.bind('<MouseWheel>', lambda event: self.scale_canvas_image_from_scroll(event))

        # Bind root window resizing
        self.root.bind("<Configure>", self.handle_resize)

        # Bind reset crop rectangle to canvas image corner coords
        self.root.bind("<r>", lambda event: self.fit_crop_to_image())

        # Bind update of entry field string variables
        self.mm_W_entry.bind("<Return>", lambda event: self.handle_sizing_entry_write('w'))
        self.mm_H_entry.bind("<Return>", lambda event: self.handle_sizing_entry_write('h'))
        # self.mm_W_entry_str.trace_add('write', lambda name, index, mode : self.handle_sizing_entry_write('w'))
        # self.mm_H_entry_str.trace_add('write', lambda name, index, mode : self.handle_sizing_entry_write('h'))

    def handle_sizing_entry_write(self, dim):
        idx = 0 + 1 * (dim == 'h')
        txt = [self.mm_W_entry_str.get(),
               self.mm_H_entry_str.get()]
        
        # numeric = re.findall(r"[-+]?\d*\.?\d+", txt[idx])
        numeric = convert_numeric_string(txt[idx])
        if numeric is None:
            return
        
        if idx == 0:
            self.crop_width_mm = float(numeric)
        else:
            self.crop_height_mm = float(numeric)

        self.update_crop_aspect_ratio(dim=dim)

    def mark_setup_complete(self):
        self.setup_is_complete = True

    def get_screen_dims(self):
        return (self.root.winfo_screenwidth(), self.root.winfo_screenheight())
    
    def get_window_dims(self):
        return (self.root.winfo_width(), self.root.winfo_height())
    
    def get_canvas_dims(self):
        return (self.canvas.winfo_width(), self.canvas.winfo_height())
    
    def get_aspect_ratio(self):        
        if self.crop_width_mm and self.crop_height_mm:
            return self.crop_width_mm / self.crop_height_mm

    def handle_resize(self, event):
        if self.setup_is_complete:
            return
            print(f'resizing to: {event.width}, {event.height}')
            # self.create_control_panel()
            # self.create_canvas_image()

    def handle_canvas_motion(self, event):
        # Cursor options found at:
        # https://tkdocs.com/shipman/cursors.html

        loc = self.crop_box_location(event.x, event.y)
        cursor = rect_location_props[loc]['cursor']
        if cursor is None:
            cursor = self.DEFAULT_CANVAS_CURSOR
        self.canvas.config(cursor=cursor)

    def handle_canvas_click(self, event):
        global start_x, start_y
        # Record starting position of mouse click
        start_x = event.x
        start_y = event.y

    def handle_canvas_click_release(self, event):
        self.active_item_tag = None
        self.active_item_loc = None

    def handle_canvas_drag(self, event):
        global start_x, start_y

        # Calculate displacement
        dx = event.x - start_x
        dy = event.y - start_y

        id = self._canvas_tag_image

        if self.active_item_loc is None:
            self.active_item_loc = self.crop_box_location(start_x, start_y)

        if self.active_item_loc.value >= 0:
            id = self._canvas_tag_rect

        if self.active_item_tag is None:
            self.active_item_tag = id

        # Move the image on canvas
        if self.active_item_tag == self._canvas_tag_image:
            self.move_canvas_image(dx, dy)
        elif self.active_item_tag == self._canvas_tag_rect:
            if self.ar_lock.get():
                delta_coords = self.get_crop_bounding_box_update_ar_locked(start_x, start_y, dx, dy, location=self.active_item_loc) 
            else:
                delta_coords = self.get_crop_bounding_box_update(start_x, start_y, dx, dy, location=self.active_item_loc)

            self.update_crop_rectangle_relative(delta_coords)
        else:
            self.canvas.move(self.active_item_tag, dx, dy)
        # Update start position for the next motion event
        start_x, start_y = event.x, event.y

    def clear_canvas(self):
        if self.canvas is not None:
            self.canvas.delete('all')
            self._canvas_items = {}

    def create_crop_rectangle(self, coords=None):

        self._canvas_items[self._canvas_tag_rect] = {}

        if coords is None:
            coords = [x for x in self.canvas.bbox(self._canvas_tag_image)]
            coords[2] -= 1
            coords[3] -= 1
            # print(coords, self.tk_image.width(), self.tk_image.height())

        if not coords:
            pos = [10, 10]
            dims = [10, 10]
            coords = pos[0], pos[1], pos[0] + dims[0] - 1, pos[1] + dims[1] - 1

        x1, y1, x2, y2 = coords

        self._canvas_items[self._canvas_tag_rect]["item"] = self.canvas.create_rectangle(x1, y1, x2, y2, outline=self.CROP_COLOR, width=1, 
                                                                                         tags=self._canvas_tag_rect)                

        self._canvas_items[self._canvas_tag_rect]["corners"] = []
        self.draw_crop_corner_dots([x1, y1, x2, y2])
        self._canvas_items[self._canvas_tag_rect]["crosshair"] = []
        self.draw_crop_center_crosshair([x1, y1, x2, y2])
            
    def draw_crop_corner_dots(self, coords, radius=3):
        x1, y1, x2, y2 = coords

        x1p, x1m = x1 + radius, x1 - radius
        y1p, y1m = y1 + radius, y1 - radius
        x2p, x2m = x2 + radius, x2 - radius
        y2p, y2m = y2 + radius, y2 - radius

        for i in range(4):
            if i == 0:
                xx1, yy1 = x1m, y1m
                xx2, yy2 = x1p, y1p
            elif i == 1:
                xx1, yy1 = x2m, y1m
                xx2, yy2 = x2p, y1p
            elif i == 2:
                xx1, yy1 = x1m, y2m
                xx2, yy2 = x1p, y2p
            elif i == 3:
                xx1, yy1 = x2m, y2m
                xx2, yy2 = x2p, y2p

            if len(self._canvas_items[self._canvas_tag_rect]["corners"]) != 4:
                self._canvas_items[self._canvas_tag_rect]["corners"].append(self.canvas.create_rectangle(xx1, yy1, xx2, yy2, 
                                                                                                         outline=self.CROP_COLOR,
                                                                                                         fill=self.CROP_COLOR, 
                                                                                                         width=1, 
                                                                                                         tags=f'c{i}'))
            else:
                self.canvas.coords(f'c{i}', xx1, yy1, xx2, yy2)

    def draw_crop_center_crosshair(self, coords, radius=10):
        x1, y1, x2, y2 = coords

        xc = int(x1 + float(x2 - x1 + 1) / 2.0)
        yc = int(y1 + float(y2 - y1 + 1) / 2.0)

        xcm, xcp = max(xc - radius, x1), min(xc + radius, x2)
        ycm, ycp = max(yc - radius, y1), min(yc + radius, y2)

        if len(self._canvas_items[self._canvas_tag_rect]["crosshair"]) == 0:
            self._canvas_items[self._canvas_tag_rect]["crosshair"].append(self.canvas.create_rectangle(xcm, ycm, xcp, ycp,
                                                                                                       outline=self.CROP_COLOR,
                                                                                                       fill=None,
                                                                                                       width=1,
                                                                                                       tags='crosshair'))
        else:
            self.canvas.coords('crosshair', xcm, ycm, xcp, ycp)

    def get_crop_bounding_box_update(self, start_x, start_y, dx, dy, location=None):

        if location is None:
            location = self.crop_box_location(start_x, start_y)

        coord_update = np.array([dx, dy, dx, dy])
        constrained = np.array([1,1,1,1])
        constrained[rect_location_props[location]['coord_idx']] = 0
        coord_update[np.where(constrained)] = 0
        
        return coord_update
        
    def get_crop_bounding_box_update_ar_locked(self, start_x, start_y, dx, dy, location=None):

        if location is None:
            location = self.crop_box_location(start_x, start_y)

        if location == RectLoc.NULL:
            return [0, 0, 0, 0]
        
        if location == RectLoc.CENTER:
            return [dx, dy, dx, dy]
        
        ar = self.get_aspect_ratio()
        coords = np.array(self.canvas.coords(self._canvas_tag_rect))
        mouse_ref_pt = np.array([start_x + dx, start_y + dy])

        # Create mask for constrained edges of the rectangle
        constrained = np.zeros(coords.shape, dtype=np.uint8)

        # In this case, constrained edges are only those immediately opposite the selected edge/corner
        location_opposite = rect_location_props[location]['flip_x']
        location_opposite = rect_location_props[location_opposite]['flip_y']
        opp_indices = rect_location_props[location_opposite]['coord_idx']
        constrained[opp_indices] = 1

        axis = np.array([0,1])
        axis = axis[np.logical_or(constrained[:2], constrained[2:])]

        dist = mouse_ref_pt[axis] - coords[opp_indices]
        sign = np.sign(dist)
        
        # Prevent divide-by-zero undefined condition
        if np.any(dist == 0):
            return np.zeros((4))

        if len(dist) > 1:
            bounds_ar = abs(dist[0] / dist[1])
            # If wider aspect ratio, constrain scaling by height - & vice versa
            axis = 1 * (bounds_ar >= ar)
            dist = dist[axis]
        else:
            axis = axis[0]
            dist = dist[0]

        # Dist is now scalar. Time to compute integer dimensions of resulting rectangle
        dims = np.zeros((2))
        dims[axis] = dist          
        dims[1-axis] = sign[min(len(sign)-1, 1-axis)] * (round(abs(dist * ar)) if axis == 1 else round(abs(dist / ar)))


        # Now calculate updated coords that adhere to the side or corner constraints
        coord_update = np.array([0,0,0,0])
        free_indices = rect_location_props[location]['coord_idx']
        if np.sum(constrained) > 1:
            # Corner pull            
            coord_update[free_indices] = coords[opp_indices] + dims - coords[free_indices]
        else:
            # Edge pull
            coord_update[free_indices] = coords[opp_indices] + dims[axis] - coords[free_indices]

            # Get coordinate indices of adjacent free edges
            adj_mask = np.isin(np.arange(4), np.concatenate((free_indices, opp_indices)), invert=True)
            adj_indices = np.where(adj_mask)
            adj_coords = coords[adj_indices]

            # Calc difference between adjacent axis dimension and existing axis size given from coords
            adj_diff = abs(dims[1-axis]) - abs(adj_coords[0] - adj_coords[1])
            coord_update[adj_indices] = [-round(adj_diff / 2), round(adj_diff / 2)]

        return coord_update

    def update_entry_text(self):
        self.mm_W_entry.delete(0, tk.END)  # Delete all existing text
        self.mm_H_entry.delete(0, tk.END)  # Delete all existing text
        self.mm_W_entry.insert(0, f'{self.crop_width_mm:.2f}mm')
        self.mm_H_entry.insert(0, f'{self.crop_height_mm:.2f}mm')

    def update_crop_aspect_ratio(self, ar=None, dim=None):
        if ar is None:
            ar = self.get_aspect_ratio()

        coords = self.canvas.coords(self._canvas_tag_rect)
        x1, y1, x2, y2 = coords
        w, h = (x2 - x1), (y2 - y1)
        curr_ar = w / h

        v = ar / curr_ar

        if dim is None:
            # Subtract and add equal magnitude from each edge
            delta = (h * w * (1 - v)) / (h + v * w)
            inc = round(delta / 2.0)
            new_coords = [inc, -inc, -inc, inc]

        elif dim == 'w':
            # Hold height constant and only adjust width
            new_w = h * ar
            inc = round((new_w - w) / 2.0)
            new_coords = [-inc, 0, inc, 0]

        elif dim == 'h':
            # Hold width constant and only adjust height
            new_h = w / ar
            inc = round((new_h - h) / 2.0)
            new_coords = [0, -inc, 0, inc]


        # If, for any dim, the size of the resulting rectangle exceeds canvas bounds,
        # then scale uniformly down until within bounds
        self.update_crop_rectangle_relative(new_coords)

    def update_crop_rectangle_absolute(self, coords):
        coords = self.constrain_coords_to_canvas(coords)
        self.canvas.coords(self._canvas_tag_rect, coords)
        self.draw_crop_corner_dots(coords)
        self.draw_crop_center_crosshair(coords)

    def update_crop_rectangle_relative(self, delta_coords):
        x1, y1, x2, y2 = self.canvas.coords(self._canvas_tag_rect)
        dx1, dy1, dx2, dy2 = delta_coords

        # Handle out-of-canvas-bounds move
        x_res = [x1+dx1, x2+dx2]
        if (x_res[0] < 0) or (x_res[1] >= self.get_canvas_dims()[0]):
            if self.ar_lock.get():
                return
            dx1, dx2 = 0, 0

        y_res = [y1+dy1, y2+dy2]
        if (y_res[0] < 0) or (y_res[1] >= self.get_canvas_dims()[1]):
            if self.ar_lock.get():
                return
            dy1, dy2 = 0, 0

        x1 += dx1
        x2 += dx2
        y1 += dy1
        y2 += dy2

        if x1 > x2:
            x1, x2 = x2, x1
            self.active_item_loc = rect_location_props[self.active_item_loc]['flip_x']
        
        if y1 > y2:
            y1, y2 = y2, y1
            self.active_item_loc = rect_location_props[self.active_item_loc]['flip_y']

        # Alter the rectangle itself
        coords = [x1, y1, x2, y2]
        self.canvas.coords(self._canvas_tag_rect, coords)
        self.draw_crop_corner_dots(coords)
        self.draw_crop_center_crosshair(coords)

    def crop_box_location(self, x, y, radius=10):
        coords = self.canvas.coords(self._canvas_tag_rect)
        if not coords:
            return RectLoc.NULL
        
        x1, y1, x2, y2 = coords
        corners = np.array([[x1, x2, x1, x2], 
                            [y1, y1, y2, y2]])
        
        diff = np.array([[x],[y]]) - corners
        diff_abs = np.abs(diff)
        dist = np.max(diff_abs, axis=0)
        
        corner = np.argmin(dist)

        if dist[corner] <= radius:
            return RectLoc(corner)
        
        between_x = (diff[0,0] >= -radius) and (diff[0,1] <= radius)
        between_y = (diff[1,0] >= -radius) and (diff[1,2] <= radius)

        # y1, x2, y2, x1
        edge_diff_abs = np.array([diff_abs[1,0], 
                                  diff_abs[0,1], 
                                  diff_abs[1,2], 
                                  diff_abs[0,0]])
        
        side = np.argmin(edge_diff_abs)
        
        if (between_x and between_y) and edge_diff_abs[side] <= radius:
            return RectLoc(side + 4)
        

        center = [x1 + float(x2 - x1 + 1) / 2.0, y1 + float(y2 - y1 + 1) / 2.0]
        dist = max(abs(x - center[0]), abs(y - center[1]))

        if dist <= radius:
            return RectLoc.CENTER

        return RectLoc.NULL

    def load_image(self):
        self.clear_canvas()
        self.image_path = filedialog.askopenfilename(
        title="Select Image File",
        filetypes=[
            ("Image Files", "*.jpg;*.jpeg;*.png;*.gif;*.bmp"),
            ("All Files", "*.*")
        ])
        self.original_image = cv2.imread(self.image_path)
        self.intermediate_image = cv2.imread(self.image_path)
        self.tk_image = cv2_to_tk(self.original_image)        

        scale = self.fit_image_to_canvas()
        self.create_canvas_image()
        self._canvas_items[self._canvas_tag_image]["scale"] = scale

        self.create_crop_rectangle()

        self.crop_height_mm, self.crop_width_mm = self.original_image.shape[:2]
        self.crop_height_mm /= self.DPMM
        self.crop_width_mm  /= self.DPMM
        self.update_entry_text()

    def create_canvas_image(self, centered=True):
        self.canvas.delete(self._canvas_tag_image)

        pos = [self.tk_image.width() / 2, 
               self.tk_image.height() / 2]
        
        if centered:
            w, h = self.get_canvas_dims()
            pos = [float(w) / 2.0, float(h) / 2.0]

        self._canvas_items[self._canvas_tag_image] = {}
        self._canvas_items[self._canvas_tag_image]["pos"] = pos
        self._canvas_items[self._canvas_tag_image]["scale"] = 1.0
        self._canvas_items[self._canvas_tag_image]["item"] = self.canvas.create_image(pos[0], pos[1], anchor=tk.CENTER, image=self.tk_image, 
                                                                                      tags=self._canvas_tag_image)

        # self.canvas.tag_lower(self._canvas_tag_image, self._canvas_tag_rect)
        
    def move_canvas_image(self, dx, dy):
        w_c, h_c = self.get_canvas_dims()
        w, h = self.tk_image.width(), self.tk_image.height()
        curr_pos = self._canvas_items[self._canvas_tag_image]["pos"]

        if np.floor(curr_pos[0] + dx) < - w // 2 or np.ceil(curr_pos[0] + dx) > w_c + w // 2:
            dx = 0
        if np.floor(curr_pos[1] + dy) < - h // 2 or np.ceil(curr_pos[1] + dy) > h_c + h // 2:
            dy = 0

        self.canvas.move(self._canvas_tag_image, dx, dy)
        self._canvas_items[self._canvas_tag_image]["pos"][0] += dx
        self._canvas_items[self._canvas_tag_image]["pos"][1] += dy

    def scale_canvas_image_from_scroll(self, event):
        if len(self._canvas_items) == 0:
            return
        
        current_scale = self._canvas_items[self._canvas_tag_image]["scale"]
        if event.delta > 0:
            self.scale_canvas_image(current_scale * 1.1)
        else:
            self.scale_canvas_image(current_scale * 0.9)
    
    def scale_canvas_image(self, scale):
        new_dims = (int(scale * self.intermediate_image.shape[1]), 
                    int(scale * self.intermediate_image.shape[0]))
        
        interp_method = cv2.INTER_LINEAR if scale < 1.0 else cv2.INTER_NEAREST

        self.tk_image = cv2_to_tk(cv2.resize(self.intermediate_image, new_dims, interpolation=interp_method))

        self._canvas_items[self._canvas_tag_image]["scale"] = scale

        self.canvas.itemconfig(self._canvas_tag_image, image=self.tk_image)
        self.canvas.image = self.tk_image

    def constrain_coords_to_canvas(self, coords):

        w_c, h_c = self.get_canvas_dims()

        coords[0] = max(0, coords[0])
        coords[1] = max(0, coords[1])
        coords[2] = min(w_c-1, coords[2])
        coords[3] = min(h_c-1, coords[3])

        return coords

    def fit_crop_to_image(self):
        coords = [x for x in self.canvas.bbox(self._canvas_tag_image)]
        coords[2] -= 1
        coords[3] -= 1
        coords = self.constrain_coords_to_canvas(coords)

        old_coords = self.canvas.coords(self._canvas_tag_rect)
        self.update_entries_from_new_crop(old_coords, coords)
        self.update_crop_rectangle_absolute(coords)

    def update_entries_from_new_crop(self, old_coords, new_coords):
        entry_w = convert_numeric_string(self.mm_W_entry_str.get())
        entry_h = convert_numeric_string(self.mm_H_entry_str.get())        

        old_w, old_h = (old_coords[2]- old_coords[0] + 1), (old_coords[3]- old_coords[1] + 1)
        new_w, new_h = (new_coords[2]- new_coords[0] + 1), (new_coords[3]- new_coords[1] + 1)
        scale = [new_w / old_w, new_h / old_h]

        self.crop_width_mm  = entry_w * scale[0]
        self.crop_height_mm = entry_h * scale[1]

        self.update_entry_text()

    def fit_image_to_canvas(self):
        w_c, h_c = self.get_canvas_dims()
        w_c, h_c = float(w_c), float(h_c)
        w, h = float(self.intermediate_image.shape[1]), float(self.intermediate_image.shape[0])

        if not ((w > w_c) or (h > h_c)):
            return 1.0
                
        sf = min((w_c / w), (h_c / h))
        self.tk_image = cv2_to_tk(cv2.resize(self.intermediate_image, (int(w * sf), int(h * sf)), interpolation=cv2.INTER_CUBIC))
        return sf

        

if __name__ == "__main__":
    app = LithGUI()