import tkinter as tk
import cv2
import numpy as np
from tkinter import N, S, E, W
from tkinter import filedialog
from PIL import Image, ImageTk

def RGB2HEX(rgbcol):
    return '#%02x%02x%02x' % rgbcol

def cv2_to_tk(bgr_img):
    # 1) Convert from BGR to RGB color
    # 2) Convert from RGB np.ndarray to PIL Image
    # 3) Convert PIL Image to ImageTk PhtoImage
    return ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)))

rectangle_location_flip_ids = \
{
    # Top Left Corner
    0: {'x'  : 1,
        'y'  : 2},
        
    # Top Right Corner
    1: {'x'  : 0,
        'y'  : 3},

    # Bottom Left Corner
    2: {'x'  : 3,
        'y'  : 0},

    # Bottom Right Corner
    3: {'x'  : 2,
        'y'  : 1},

    # Top Edge
    4: {'x'  : 4,
        'y'  : 6},

    # Right Edge
    5: {'x'  : 7,
        'y'  : 5},

    # Bottom Edge
    6: {'x'  : 6,
        'y'  : 4},
    
    # Left Edge
    7: {'x'  : 5,
        'y'  : 7}
}

class LithGUI:
    ALL_PADDING = 10
    CONTROL_PANEL_WIDTH = 0.2
    CANVAS_COLOR = RGB2HEX((127, 127, 127))
    CROP_COLOR = RGB2HEX((255, 0, 0))
    LARGE_PX_INCREMENT = 10
    SMALL_PX_INCREMENT = 1
    DEFAULT_CANVAS_CURSOR = "fleur"

    def __init__(self, fullscreen=False):
        self.root = tk.Tk()
        self.root.title("Crop Image")
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

    def mark_setup_complete(self):
        self.setup_is_complete = True

    def get_screen_dims(self):
        return (self.root.winfo_screenwidth(), self.root.winfo_screenheight())
    
    def get_window_dims(self):
        return (self.root.winfo_width(), self.root.winfo_height())
    
    def get_canvas_dims(self):
        return (self.canvas.winfo_width(), self.canvas.winfo_height())
    
    def create_widgets(self):
        self.create_canvas()
        self.create_control_panel()
        self.arrange_widgets()

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
        # self.canvas.tag_bind(self._canvas_tag_image, '<ButtonPress-1>', self.start_drag)
        # self.canvas.tag_bind(self._canvas_tag_image, '<B1-Motion>', lambda event: self.canvas_drag(event, id=self._canvas_tag_image))
        self.canvas.bind('<ButtonPress-1>', self.handle_canvas_click)
        self.canvas.bind('<B1-Motion>', lambda event: self.handle_canvas_drag(event))
        self.canvas.bind('<ButtonRelease-1>', self.handle_canvas_click_release)

        # Bind un-clicked mouse motion
        self.canvas.bind('<Motion>', lambda event: self.handle_canvas_motion(event))

        # Bind canvas image scaling to mouse scroll wheel
        self.root.bind('<MouseWheel>', lambda event: self.scale_canvas_image_from_scroll(event))

        # Bind root window resizing
        self.root.bind("<Configure>", self.handle_resize)


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
        if loc == 0:
            # Top left corner
            self.canvas.config(cursor="top_left_corner")            
        elif loc == 1:
            # Top right corner
            self.canvas.config(cursor="top_right_corner")
        elif loc == 2:
            # Bottom left corner
            self.canvas.config(cursor="bottom_left_corner")
        elif loc == 3:
            # Bottom right corner
            self.canvas.config(cursor="bottom_right_corner")
        elif loc == 4:
            # Top edge
            self.canvas.config(cursor="bottom_side")
        elif loc == 5:
            # Right edge
            self.canvas.config(cursor="left_side")
        elif loc == 6:
            # Bottom edge
            self.canvas.config(cursor="top_side")
        elif loc == 7:
            # Left edge
            self.canvas.config(cursor="right_side")
        else:
            # Not interacting with crop window, revert to normal arrow
            self.canvas.config(cursor=self.DEFAULT_CANVAS_CURSOR)


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

        if self.active_item_loc >= 0:
            id = self._canvas_tag_rect

        if self.active_item_tag is None:
            self.active_item_tag = id

        # Move the image on canvas
        if self.active_item_tag == self._canvas_tag_image:
            self.move_canvas_image(dx, dy)
        elif self.active_item_tag == self._canvas_tag_rect:
            delta_coords = self.get_crop_bounding_box_update(start_x, start_y, dx, dy, location=self.active_item_loc)    
            self.update_crop_rectangle(delta_coords)
        else:
            self.canvas.move(self.active_item_tag, dx, dy)
        # Update start position for the next motion event
        start_x, start_y = event.x, event.y

    def create_control_panel(self):
        if self.control_panel is not None:
            self.control_panel.destroy()

        # Panel Frame
        # self.control_panel = tk.Frame(self.root, background="white")
        self.control_panel = tk.LabelFrame(self.root, background="white", text="Settings")
        # self.control_panel.grid_rowconfigure(0, weight=1)
        self.control_panel.grid_columnconfigure(0, weight=1)
        control_panel_cols = 2

        # Add + Pack entry fields for crop W and H in mm and corresponding labels
        self.mm_W_entry = tk.Entry(self.control_panel, borderwidth=3)
        self.mm_H_entry = tk.Entry(self.control_panel, borderwidth=3)
        mm_W_entry_label = tk.Label(self.control_panel, text="Width (mm)")
        mm_H_entry_label = tk.Label(self.control_panel, text="Height (mm)")

        mm_W_entry_label.grid(row=0, column=0, sticky=W, padx=self.ALL_PADDING)
        mm_H_entry_label.grid(row=0, column=1, sticky=W, padx=self.ALL_PADDING)
        self.mm_W_entry.grid(row=1, column=0)
        self.mm_H_entry.grid(row=1, column=1)

        # Add + Pack CheckBox for aspect ratio lock
        self.ar_lock_val = tk.IntVar(value=1)
        self.ar_lock_checkbox = tk.Checkbutton(self.control_panel, 
                                               text="Lock Aspect Ratio", 
                                               variable=self.ar_lock_val, 
                                               background=RGB2HEX((255,255,255)),
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

    def create_canvas(self):
        if self.canvas is not None:
            self.canvas.delete('all')
            self.canvas.destroy()

        self.canvas_w = int(round((1.0 - self.CONTROL_PANEL_WIDTH) * self.root_w))
        self.canvas_h = self.root_h

        self.canvas = tk.Canvas(self.root, width=self.canvas_w, height=self.canvas_h, 
                                bg=self.CANVAS_COLOR, borderwidth=0, highlightthickness=0)
        

    def create_crop_rectangle(self):

        pos = [10, 10]
        dims = [10, 10]

        self._canvas_items[self._canvas_tag_rect] = {}
        # self._canvas_items[self._canvas_tag_rect]["pos"] = pos
        # self._canvas_items[self._canvas_tag_rect]["dims"] = dims

        x1, y1, x2, y2 = pos[0], pos[1], pos[0] + dims[0] - 1, pos[1] + dims[1] - 1

        self._canvas_items[self._canvas_tag_rect]["item"] = self.canvas.create_rectangle(x1, y1, x2, y2, outline=self.CROP_COLOR, width=1, 
                                                                                         tags=self._canvas_tag_rect)                

        self._canvas_items[self._canvas_tag_rect]["corners"] = []
        self.draw_crop_corner_dots([x1, y1, x2, y2])
            
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

            
    def get_crop_bounding_box_update(self, start_x, start_y, dx, dy, location=None):

        if location is None:
            location = self.crop_box_location(start_x, start_y)

        if location == -1:
            return [0, 0, 0, 0]        
        elif location == 0:
            # Top left corner
            return [dx, dy, 0, 0]
        elif location == 1:
            # Top right corner
            return [0, dy, dx, 0]
        elif location == 2:
            # Bottom left corner
            return [dx, 0, 0, dy]
        elif location == 3:
            # Bottom right corner
            return [0, 0, dx, dy]
        elif location == 4:
            # Top edge
            return [0, dy, 0, 0]
        elif location == 5:
            # Right edge
            return [0, 0, dx, 0]
        elif location == 6:
            # Bottom edge
            return [0, 0, 0, dy]
        elif location == 7:
            # Left edge
            return [dx, 0, 0, 0]


    def update_crop_rectangle(self, delta_coords):
        x1, y1, x2, y2 = self.canvas.coords(self._canvas_tag_rect)
        dx1, dy1, dx2, dy2 = delta_coords

        # Handle out-of-canvas-bounds move
        x_res = [x1+dx1, x2+dx2]
        if (x_res[0] < 0) or (x_res[1] >= self.get_canvas_dims()[0]):
            dx1, dx2 = 0, 0

        y_res = [y1+dy1, y2+dy2]
        if (y_res[0] < 0) or (y_res[1] >= self.get_canvas_dims()[1]):
            dy1, dy2 = 0, 0

        x1 += dx1
        x2 += dx2
        y1 += dy1
        y2 += dy2

        if x1 > x2:
            x1, x2 = x2, x1
            self.active_item_loc = rectangle_location_flip_ids[self.active_item_loc]['x']
        
        if y1 > y2:
            y1, y2 = y2, y1
            self.active_item_loc = rectangle_location_flip_ids[self.active_item_loc]['y']

        # Alter the rectangle itself
        self.canvas.coords(self._canvas_tag_rect, [x1, y1, x2, y2])
        self.draw_crop_corner_dots([x1, y1, x2, y2])



    def crop_box_location(self, x, y, radius=10):
        coords = self.canvas.coords(self._canvas_tag_rect)
        if not coords:
            return -1
        
        x1, y1, x2, y2 = coords
        corners = np.array([[x1, x2, x1, x2], 
                            [y1, y1, y2, y2]])
        
        diff = np.array([[x],[y]]) - corners
        diff_abs = np.abs(diff)
        dist = np.max(diff_abs, axis=0)
        
        corner = np.argmin(dist)

        if dist[corner] <= radius:
            return corner
        
        between_x = (diff[0,0] >= 0) and (diff[0,1] <= 0)
        between_y = (diff[1,0] >= 0) and (diff[1,2] <= 0)

        # y1, x2, y2, x1
        edge_diff_abs = np.array([diff_abs[1,0], 
                                  diff_abs[0,1], 
                                  diff_abs[1,2], 
                                  diff_abs[0,0]])
        
        side = np.argmin(edge_diff_abs)
        
        condition = (between_x or between_y) and edge_diff_abs[side] <= radius
        
        return side + 4 if condition else -1

    def load_image(self):
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
        
        # print(f'putting {self._canvas_tag_image} behind {self._canvas_tag_rect}')
        # self.canvas.tag_lower(self._canvas_tag_image, self._canvas_tag_rect)
        
    def move_canvas_image(self, dx, dy):
        w_c, h_c = self.get_canvas_dims()
        w, h = self.tk_image.width(), self.tk_image.height()
        curr_pos = self._canvas_items[self._canvas_tag_image]["pos"]

        if np.floor(curr_pos[0] + dx) < - w // 2 or np.ceil(curr_pos[0] + dx) > w_c + w // 2:
            dx = 0
        if np.floor(curr_pos[1] + dy) < - h // 2 or np.ceil(curr_pos[1] + dy) > h_c + h // 2:
            dy = 0

        # if curr_pos[0] + dx < 0 or curr_pos[0] + dx >= w_c:
        #     dx = 0

        # if curr_pos[1] + dy < 0 or curr_pos[1] + dy >= h_c:
        #     dy = 0

        self.canvas.move(self._canvas_tag_image, dx, dy)
        self._canvas_items[self._canvas_tag_image]["pos"][0] += dx
        self._canvas_items[self._canvas_tag_image]["pos"][1] += dy

    def scale_canvas_image_from_scroll(self, event):
        try:
            current_scale = self._canvas_items[self._canvas_tag_image]["scale"]
            if event.delta > 0:
                self.scale_canvas_image(current_scale * 1.1)
            else:
                self.scale_canvas_image(current_scale * 0.9)
        except:
            pass
    
    def scale_canvas_image(self, scale):
        new_dims = (int(scale * self.intermediate_image.shape[1]), 
                    int(scale * self.intermediate_image.shape[0]))
        
        interp_method = cv2.INTER_CUBIC if scale < 1.0 else cv2.INTER_NEAREST

        self.tk_image = cv2_to_tk(cv2.resize(self.intermediate_image, new_dims, interpolation=cv2.INTER_CUBIC))

        # print(f'scale: {self._canvas_items[self._canvas_tag_image]["scale"]} --> {scale}')
        self._canvas_items[self._canvas_tag_image]["scale"] = scale

        self.canvas.itemconfig(self._canvas_tag_image, image=self.tk_image)
        self.canvas.image = self.tk_image


    def fit_image_to_canvas(self):
        w_c, h_c = self.get_canvas_dims()
        w_c, h_c = float(w_c), float(h_c)
        w, h = float(self.intermediate_image.shape[1]), float(self.intermediate_image.shape[0])

        if not ((w > w_c) or (h > h_c)):
            return
                
        sf = min((w_c / w), (h_c / h))
        self.tk_image = cv2_to_tk(cv2.resize(self.intermediate_image, (int(w * sf), int(h * sf)), interpolation=cv2.INTER_CUBIC))
        return sf

        

if __name__ == "__main__":
    app = LithGUI()