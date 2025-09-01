import tkinter as tk
import cv2
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

class LithGUI:
    ALL_PADDING = 10
    CONTROL_PANEL_WIDTH = 0.2
    CANVAS_COLOR = (127, 127, 127)

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

        self._canvas_tag_image = "canvas_image"
        self._canvas_items = {}

        self.create_widgets()
        self.bind_events()

        self.root.mainloop()

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
        self.root.bind(   '<Up>', lambda event: self.move_canvas_image( 0, -10))
        self.root.bind( '<Down>', lambda event: self.move_canvas_image( 0,  10))
        self.root.bind( '<Left>', lambda event: self.move_canvas_image(-10,  0))
        self.root.bind('<Right>', lambda event: self.move_canvas_image( 10,  0))

        # Bind canvas image move to click and drag
        self.canvas.tag_bind(self._canvas_tag_image, '<ButtonPress-1>', self.start_drag)
        self.canvas.tag_bind(self._canvas_tag_image, '<B1-Motion>', lambda event: self.canvas_drag(event, id=self._canvas_tag_image))

        # Bind canvas image scaling to mouse scroll wheel
        self.root.bind('<MouseWheel>', lambda event: self.scale_canvas_image_from_scroll(event))

    def start_drag(self, event):
        global start_x, start_y
        # Record starting position of mouse click
        start_x = event.x
        start_y = event.y

    def canvas_drag(self, event, id):
        global start_x, start_y
        # Calculate displacement
        dx = event.x - start_x
        dy = event.y - start_y
        # Move the image on canvas
        self.canvas.move(id, dx, dy)
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
                                bg=RGB2HEX(self.CANVAS_COLOR), borderwidth=0, highlightthickness=0)

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

    def create_canvas_image(self, centered=True):
        self.canvas.delete(self._canvas_tag_image)

        pos = [0, 0]
        anchor = tk.NW
        if centered:
            w, h = self.get_canvas_dims()
            pos = [float(w) / 2.0, float(h) / 2.0]
            anchor = tk.CENTER

        self._canvas_items[self._canvas_tag_image] = {}
        self._canvas_items[self._canvas_tag_image]["pos"] = pos
        self._canvas_items[self._canvas_tag_image]["scale"] = 1.0
        self._canvas_items[self._canvas_tag_image]["item"] = self.canvas.create_image(pos[0], pos[1], anchor=anchor, image=self.tk_image, 
                                                                                      tags=self._canvas_tag_image)
        
    def move_canvas_image(self, dx, dy):
        self.canvas.move(self._canvas_tag_image, dx, dy)

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
        self.tk_image = cv2_to_tk(cv2.resize(self.intermediate_image, new_dims, interpolation=cv2.INTER_CUBIC))
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