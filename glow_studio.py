import cv2
import numpy as np
from PIL import Image
import customtkinter as ctk
from tkinter import filedialog, colorchooser
import threading
import queue

# Theme Configuration
ctk.set_appearance_mode("dark")  
ctk.set_default_color_theme("blue")

class GlowGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Glow Outline Maker")
        self.geometry("1150x820")
        
        # --- State Variables ---
        self.image_path = None
        self.original_img = None
        self.preview_img_base = None
        self.preview_scale = 0.5 # 50% by default
        
        # UI Variables
        self.effect_mode = ctk.StringVar(value="classic")
        self.color_source_var = ctk.StringVar(value="custom") # 'custom' or 'auto_edge'
        
        self.thickness_var = ctk.IntVar(value=8)
        self.glow_var = ctk.IntVar(value=20)
        
        # Classic Mode Colors
        self.classic_color_bgr = [0, 255, 0] # Green
        self.classic_color_hex = "#00ff00"
        
        # Neon Mode Options
        self.neon_tube_var = ctk.IntVar(value=4)
        self.neon_spread_var = ctk.IntVar(value=25)
        self.neon_tube_color_bgr = [255, 255, 255] # White
        self.neon_tube_color_hex = "#ffffff"
        self.neon_glow_color_bgr = [255, 0, 255] # Magenta
        self.neon_glow_color_hex = "#ff00ff"
        
        # --- Multithreading Engine ---
        self.task_queue = queue.Queue(maxsize=1)
        self.result_queue = queue.Queue(maxsize=1)
        
        # Start Background Worker
        self.worker_thread = threading.Thread(target=self.image_worker, daemon=True)
        self.worker_thread.start()

        self.setup_ui()
        self.check_queues()

    def setup_ui(self):
        # === SIDEBAR (Controls) ===
        self.sidebar = ctk.CTkFrame(self, width=350, corner_radius=15, fg_color="#23272d")
        self.sidebar.pack(side="left", fill="y", padx=20, pady=20)
        self.sidebar.pack_propagate(False)
        
        ctk.CTkLabel(self.sidebar, text="Glow Studio", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(20, 15))

        # --- Loading and Resolution ---
        ctk.CTkButton(self.sidebar, text="Load Image (PNG)", command=self.load_image, height=45).pack(fill="x", padx=20, pady=(0, 15))
        
        scale_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        scale_frame.pack(fill="x", padx=20, pady=(0, 15))
        ctk.CTkLabel(scale_frame, text="Preview Quality:").pack(side="left")
        
        self.scale_var = ctk.StringVar(value="50%")
        self.scale_menu = ctk.CTkOptionMenu(scale_frame, values=["25%", "50%", "100%"], variable=self.scale_var, command=self.change_preview_scale, width=100)
        self.scale_menu.pack(side="right")

        # --- Mode Selector ---
        self.mode_tabs = ctk.CTkSegmentedButton(self.sidebar, values=["Classic", "Neon"], command=self.switch_mode)
        self.mode_tabs.set("Classic")
        self.mode_tabs.pack(fill="x", padx=20, pady=(0, 15))

        # --- Color Source Selector ---
        ctk.CTkLabel(self.sidebar, text="Glow Color Source:", anchor="w").pack(fill="x", padx=20, pady=(5, 5))
        self.color_source_tabs = ctk.CTkSegmentedButton(self.sidebar, values=["Custom Color", "Auto Edge"], command=self.change_color_source)
        self.color_source_tabs.set("Custom Color")
        self.color_source_tabs.pack(fill="x", padx=20, pady=(0, 15))

        # --- Dynamic Params Container ---
        self.params_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.params_frame.pack(fill="x", expand=True)

        self.build_classic_ui()
        self.build_neon_ui()
        self.switch_mode("Classic")

        # --- Bottom Area (Status & Export) ---
        self.status_label = ctk.CTkLabel(self.sidebar, text="", text_color="#00ff00")
        self.status_label.pack(side="bottom", pady=(0, 10))

        ctk.CTkButton(self.sidebar, text="Export HD Image", command=self.save_image, height=50, fg_color="#1f538d", font=ctk.CTkFont(weight="bold")).pack(side="bottom", fill="x", padx=20, pady=(0, 10))

        # === PREVIEW AREA ===
        self.preview_area = ctk.CTkFrame(self, corner_radius=15, fg_color="#1e1e1e")
        self.preview_area.pack(side="right", fill="both", expand=True, padx=(0, 20), pady=20)

        self.image_label = ctk.CTkLabel(self.preview_area, text="No Image Loaded", text_color="#555555", font=ctk.CTkFont(size=20))
        self.image_label.place(relx=0.5, rely=0.5, anchor="center")
        
        self.loading_label = ctk.CTkLabel(self.preview_area, text="Processing...", text_color="#ffaa00", bg_color="#1e1e1e")
        self.preview_area.bind("<Configure>", lambda e: self.trigger_update())

    def build_classic_ui(self):
        self.frame_classic = ctk.CTkFrame(self.params_frame, fg_color="transparent")
        
        ctk.CTkLabel(self.frame_classic, text="Outline Thickness:", anchor="w").pack(fill="x", padx=20)
        ctk.CTkSlider(self.frame_classic, from_=0, to=100, variable=self.thickness_var, command=self.trigger_update).pack(fill="x", padx=20, pady=(5, 15))

        ctk.CTkLabel(self.frame_classic, text="Glow Amount:", anchor="w").pack(fill="x", padx=20)
        ctk.CTkSlider(self.frame_classic, from_=0, to=100, variable=self.glow_var, command=self.trigger_update).pack(fill="x", padx=20, pady=(5, 15))

        self.btn_color_classic = ctk.CTkButton(self.frame_classic, text="Effect Color", fg_color=self.classic_color_hex, text_color="black", hover_color="#cccccc", command=lambda: self.choose_color('classic'))
        self.btn_color_classic.pack(fill="x", padx=20, pady=10)

    def build_neon_ui(self):
        self.frame_neon = ctk.CTkFrame(self.params_frame, fg_color="transparent")
        
        ctk.CTkLabel(self.frame_neon, text="Tube Thickness:", anchor="w").pack(fill="x", padx=20)
        ctk.CTkSlider(self.frame_neon, from_=0, to=50, variable=self.neon_tube_var, command=self.trigger_update).pack(fill="x", padx=20, pady=(5, 15))

        ctk.CTkLabel(self.frame_neon, text="Light Spread (Glow):", anchor="w").pack(fill="x", padx=20)
        ctk.CTkSlider(self.frame_neon, from_=0, to=150, variable=self.neon_spread_var, command=self.trigger_update).pack(fill="x", padx=20, pady=(5, 15))

        # Grid for the two color buttons
        color_grid = ctk.CTkFrame(self.frame_neon, fg_color="transparent")
        color_grid.pack(fill="x", padx=20, pady=10)
        
        self.btn_color_neon_tube = ctk.CTkButton(color_grid, text="Tube Color", fg_color=self.neon_tube_color_hex, text_color="black", hover_color="#cccccc", command=lambda: self.choose_color('neon_tube'), width=140)
        self.btn_color_neon_tube.pack(side="left", expand=True, padx=(0, 5))
        
        self.btn_color_neon_glow = ctk.CTkButton(color_grid, text="Glow Color", fg_color=self.neon_glow_color_hex, text_color="black", hover_color="#cccccc", command=lambda: self.choose_color('neon_glow'), width=140)
        self.btn_color_neon_glow.pack(side="right", expand=True, padx=(5, 0))

    def switch_mode(self, mode_name):
        self.frame_classic.pack_forget()
        self.frame_neon.pack_forget()
        
        if mode_name == "Classic":
            self.effect_mode.set("classic")
            self.frame_classic.pack(fill="both", expand=True)
        else:
            self.effect_mode.set("neon")
            self.frame_neon.pack(fill="both", expand=True)
            
        self.trigger_update()

    def change_color_source(self, choice):
        if choice == "Custom Color":
            self.color_source_var.set("custom")
            self.btn_color_classic.configure(state="normal")
            self.btn_color_neon_glow.configure(state="normal")
        else:
            self.color_source_var.set("auto_edge")
            # Disable specific color buttons if auto edge is used
            self.btn_color_classic.configure(state="disabled")
            self.btn_color_neon_glow.configure(state="disabled")
            # Note: Tube color remains active as it usually stays solid white/colored even with edge glow
        self.trigger_update()

    def choose_color(self, target):
        color_code = colorchooser.askcolor(title="Choose Color")
        if color_code[1]:
            hex_val = color_code[1]
            rgb = color_code[0]
            bgr = [int(rgb[2]), int(rgb[1]), int(rgb[0])]
            
            brightness = (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000
            txt_color = "black" if brightness > 125 else "white"
            
            if target == 'classic':
                self.classic_color_hex = hex_val
                self.classic_color_bgr = bgr
                self.btn_color_classic.configure(fg_color=hex_val, text_color=txt_color)
            elif target == 'neon_tube':
                self.neon_tube_color_hex = hex_val
                self.neon_tube_color_bgr = bgr
                self.btn_color_neon_tube.configure(fg_color=hex_val, text_color=txt_color)
            elif target == 'neon_glow':
                self.neon_glow_color_hex = hex_val
                self.neon_glow_color_bgr = bgr
                self.btn_color_neon_glow.configure(fg_color=hex_val, text_color=txt_color)
                
            self.trigger_update()

    def change_preview_scale(self, choice):
        if self.original_img is None: return
        
        if choice == "25%": self.preview_scale = 0.25
        elif choice == "50%": self.preview_scale = 0.5
        else: self.preview_scale = 1.0
        
        # Regenerate base preview proxy
        h, w = self.original_img.shape[:2]
        new_w, new_h = max(1, int(w * self.preview_scale)), max(1, int(h * self.preview_scale))
        self.preview_img_base = cv2.resize(self.original_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        self.trigger_update()

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("PNG Images", "*.png")])
        if not file_path: return
        
        img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
        if img is None or len(img.shape) < 3 or img.shape[2] != 4:
            self.show_status("Error: Alpha Channel required", is_error=True)
            return

        self.original_img = img
        self.change_preview_scale(self.scale_var.get())
        self.show_status("Image loaded successfully.")

    def show_status(self, message, is_error=False, persist=False):
        color = "#ff4444" if is_error else ( "#ffaa00" if persist else "#00ff00" )
        self.status_label.configure(text=message, text_color=color)
        if not persist:
            if hasattr(self, '_status_timer') and self._status_timer:
                self.after_cancel(self._status_timer)
            self._status_timer = self.after(3000, lambda: self.status_label.configure(text=""))
        self.update_idletasks()

    # ==========================================
    # MULTITHREADING LOGIC
    # ==========================================
    
    def trigger_update(self, event=None):
        if self.original_img is None: return
        self.loading_label.place(relx=0.05, rely=0.05)
        
        params = {
            'mode': self.effect_mode.get(),
            'color_source': self.color_source_var.get(),
            't_classic': self.thickness_var.get(),
            'g_classic': self.glow_var.get(),
            'c_classic': self.classic_color_bgr,
            't_neon': self.neon_tube_var.get(),
            'g_neon': self.neon_spread_var.get(),
            'c_neon_tube': self.neon_tube_color_bgr,
            'c_neon_glow': self.neon_glow_color_bgr,
            'scale': self.preview_scale
        }
        
        while not self.task_queue.empty():
            try: self.task_queue.get_nowait()
            except queue.Empty: break
            
        self.task_queue.put(params)

    def image_worker(self):
        while True:
            params = self.task_queue.get()
            if params is None: break
            
            try:
                processed = self.core_algorithm(self.preview_img_base, params, is_preview=True)
                while not self.result_queue.empty():
                    try: self.result_queue.get_nowait()
                    except queue.Empty: break
                self.result_queue.put(processed)
            except Exception as e:
                print(f"Render Error: {e}")
            finally:
                self.task_queue.task_done()

    def check_queues(self):
        try:
            result_img = self.result_queue.get_nowait()
            self.render_to_canvas(result_img)
            self.loading_label.place_forget()
        except queue.Empty:
            pass
        self.after(50, self.check_queues)

    # ==========================================
    # OPENCV RENDER ENGINE
    # ==========================================

    def core_algorithm(self, source_img, params, is_preview=True):
        scale = params['scale'] if is_preview else 1.0
        mode = params['mode']
        color_source = params['color_source']

        if mode == 'classic':
            t_val = max(1, int(params['t_classic'] * scale)) if params['t_classic'] > 0 else 0
            g_val = max(1, int(params['g_classic'] * scale)) if params['g_classic'] > 0 else 0
            color = np.array(params['c_classic'], dtype=np.float32)
            pad = t_val + g_val + 10
        else:
            t_val = max(1, int(params['t_neon'] * scale)) if params['t_neon'] > 0 else 0
            g_val = max(1, int(params['g_neon'] * scale)) if params['g_neon'] > 0 else 0
            c_tube = np.array(params['c_neon_tube'], dtype=np.float32)
            c_glow = np.array(params['c_neon_glow'], dtype=np.float32)
            pad = t_val + (g_val * 3) + 10

        img = cv2.copyMakeBorder(source_img, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=[0, 0, 0, 0])

        bgr = img[:, :, :3]
        alpha = img[:, :, 3].astype(np.float32) / 255.0

        if mode == 'classic':
            if t_val > 0:
                k_thick = t_val * 2 + 1 
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_thick, k_thick))
                outline_alpha = cv2.dilate(img[:, :, 3], kernel)
            else:
                outline_alpha = img[:, :, 3].copy()
                
            # Apply color source logic
            if color_source == 'auto_edge':
                if t_val > 0:
                    base_color_bgr = cv2.dilate(bgr, kernel).astype(np.float32)
                else:
                    base_color_bgr = bgr.astype(np.float32)
            else:
                base_color_bgr = np.full_like(bgr, color, dtype=np.float32)

            if g_val > 0:
                k_glow = g_val * 2 + 1 
                bg_bgr = cv2.GaussianBlur(base_color_bgr.astype(np.uint8), (k_glow, k_glow), 0).astype(np.float32)
                bg_alpha = cv2.GaussianBlur(outline_alpha, (k_glow, k_glow), 0).astype(np.float32) / 255.0
            else:
                bg_bgr = base_color_bgr
                bg_alpha = outline_alpha.astype(np.float32) / 255.0
                
        else:
            if t_val > 0:
                k_thick = t_val * 2 + 1 
                kernel_tube = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_thick, k_thick))
                tube_alpha_raw = cv2.dilate(img[:, :, 3], kernel_tube)
            else:
                tube_alpha_raw = img[:, :, 3].copy()
                
            tube_alpha = cv2.GaussianBlur(tube_alpha_raw, (3, 3), 0).astype(np.float32) / 255.0
            
            # Tube color is usually solid/custom even in auto_edge mode
            tube_bgr = np.full_like(bgr, c_tube, dtype=np.float32) 
            
            if g_val > 0:
                k1 = g_val * 2 + 1
                k2 = g_val * 4 + 1
                
                g1 = cv2.GaussianBlur(tube_alpha_raw, (k1, k1), 0).astype(np.float32) / 255.0
                g2 = cv2.GaussianBlur(tube_alpha_raw, (k2, k2), 0).astype(np.float32) / 255.0
                halo_alpha = 1.0 - (1.0 - g1) * (1.0 - g2)
            else:
                halo_alpha = np.zeros_like(tube_alpha)
                
            # Halo color depends on source
            if color_source == 'auto_edge':
                if t_val > 0:
                    halo_bgr = cv2.dilate(bgr, kernel_tube).astype(np.float32)
                else:
                    halo_bgr = bgr.astype(np.float32)
            else:
                halo_bgr = np.full_like(bgr, c_glow, dtype=np.float32)
            
            bg_alpha = tube_alpha + halo_alpha * (1.0 - tube_alpha)
            bg_alpha_safe = np.where(bg_alpha == 0, 1.0, bg_alpha)
            bg_bgr = (tube_bgr * tube_alpha[..., None] + halo_bgr * halo_alpha[..., None] * (1.0 - tube_alpha[..., None])) / bg_alpha_safe[..., None]

        out_alpha = alpha + bg_alpha * (1.0 - alpha)
        out_alpha_safe = np.where(out_alpha == 0, 1.0, out_alpha)
        out_bgr = (bgr.astype(np.float32) * alpha[..., None] + bg_bgr * bg_alpha[..., None] * (1.0 - alpha[..., None])) / out_alpha_safe[..., None]

        return np.dstack((out_bgr, out_alpha * 255)).astype(np.uint8)

    # ==========================================
    # DISPLAY & EXPORT
    # ==========================================

    def render_to_canvas(self, processed_img):
        rgba_img = cv2.cvtColor(processed_img, cv2.COLOR_BGRA2RGBA)
        pil_img = Image.fromarray(rgba_img)

        frame_w = self.preview_area.winfo_width()
        frame_h = self.preview_area.winfo_height()
        
        if frame_w > 40 and frame_h > 40:
            target_w_max = frame_w - 40
            target_h_max = frame_h - 40
            
            # Keep visual size consistent across resolutions
            img_w, img_h = pil_img.size
            ratio = min(target_w_max / img_w, target_h_max / img_h)
            
            target_w = int(img_w * ratio)
            target_h = int(img_h * ratio)
            
            # Use NEAREST to show accurate low-res pixelation if scale is 25%
            pil_img = pil_img.resize((target_w, target_h), Image.Resampling.NEAREST)
            
            checker = Image.fromarray(self.create_checkerboard(target_w, target_h))
            checker.paste(pil_img, (0, 0), pil_img)
            
            ctk_img = ctk.CTkImage(light_image=checker, dark_image=checker, size=(target_w, target_h))
            
            self.image_label.configure(image=ctk_img, text="")
            self.image_label.image = ctk_img 

    def create_checkerboard(self, width, height, tile_size=20):
        tiles_x = width // tile_size + 1
        tiles_y = height // tile_size + 1
        grid = np.indices((tiles_y, tiles_x)).sum(axis=0) % 2
        board = np.kron(grid, np.ones((tile_size, tile_size))) * 15 + 30 
        board = board[:height, :width].astype(np.uint8)
        return cv2.cvtColor(board, cv2.COLOR_GRAY2BGR)

    def save_image(self):
        if self.original_img is None: return
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Images", "*.png")],
            title="Save Modified Image"
        )
        
        if save_path:
            self.show_status("Processing HD Image... Please wait.", persist=True)
            self.update_idletasks()
            
            params = {
                'mode': self.effect_mode.get(),
                'color_source': self.color_source_var.get(),
                't_classic': self.thickness_var.get(),
                'g_classic': self.glow_var.get(),
                'c_classic': self.classic_color_bgr,
                't_neon': self.neon_tube_var.get(),
                'g_neon': self.neon_spread_var.get(),
                'c_neon_tube': self.neon_tube_color_bgr,
                'c_neon_glow': self.neon_glow_color_bgr,
                'scale': 1.0 # 100% Scale for HD export
            }
            
            final_img = self.core_algorithm(self.original_img, params, is_preview=False)
            cv2.imwrite(save_path, final_img)
            self.show_status(f"Success! Image saved as {final_img.shape[1]}x{final_img.shape[0]}")

if __name__ == "__main__":
    app = GlowGeneratorApp()
    app.mainloop()