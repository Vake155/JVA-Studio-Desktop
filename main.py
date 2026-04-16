<<<<<<< HEAD
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import requests
from PIL import Image, ImageSequence, ImageTk, ImageOps
from io import BytesIO
from rembg import remove
from pathlib import Path
from datetime import datetime
import pollinations
import sys

class JVAStudioApp:
    """JVA Studio: Eliminación de fondos, generación IA y edición básica."""

    def __init__(self, root):
        self.root = root
        try:
            # --- Splash screen inmediato ---
            splash = tk.Toplevel(root)
            splash.overrideredirect(True)
            splash.configure(bg='#4361EE')
            splash.geometry("400x200")
            # Centrar splash
            splash.update_idletasks()
            sw = splash.winfo_screenwidth()
            sh = splash.winfo_screenheight()
            x = (sw // 2) - 200
            y = (sh // 2) - 100
            splash.geometry(f"+{x}+{y}")
            ttk.Label(splash, text="JVA Studio", font=('Segoe UI', 24, 'bold'),
                      foreground='white', background='#4361EE').pack(pady=(50,10))
            ttk.Label(splash, text="Cargando...", font=('Segoe UI', 12),
                      foreground='white', background='#4361EE').pack()
            splash.update()

            # --- Inicialización normal ---
            self.root.title("JVA Studio")
            self.root.geometry("1024x760")
            self.root.resizable(False, False)
            self.root.configure(bg='#F5F7FA')
            # Variables de estado (sin cambios)
            self.local_image_path = None
            self.generated_image = None
            self.original_image = None
            self.edited_image = None
            self.preview_tk = None
            self.status_var = tk.StringVar(value="🟢 Listo para comenzar")
            self.progress = None
            self.ai_progress = None
            self.zoom_factor = 1.0
            self.zoom_step = 0.2
            self.base_preview_image = None

            self.root.withdraw()
            self.root.attributes('-alpha', 0.0)

            self.set_app_icon()
            self.setup_styles()
            self.create_notebook()
            self.setup_keyboard_shortcuts()
            self.setup_input_tracking()
            self.center_window()

            # Cerrar splash y mostrar ventana principal
            splash.destroy()
            self.root.deiconify()
            self.fade_in()

            # Precargar modelo de IA en segundo plano (evita bloqueo en el primer uso)
            threading.Thread(target=self._warmup_rembg, daemon=True).start()

        except Exception as e:
            log_path = Path.home() / "jva_studio_error.log"
            with open(log_path, "w", encoding="utf-8") as f:
                traceback.print_exc(file=f)
            messagebox.showerror("Error fatal", f"La aplicación falló al iniciar.\nRevisa el log en:\n{log_path}")
            raise

    # -------------------------------------------------------------------------
    # Estética y configuración
    # -------------------------------------------------------------------------
    def set_app_icon(self):
        try:
            # Determinar ruta base (desarrollo o ejecutable)
            if getattr(sys, 'frozen', False):
                base_path = Path(sys._MEIPASS)
            else:
                base_path = Path(__file__).parent
            icon_path = base_path / "Assets" / "logo.png"
            if icon_path.exists():
                icon = tk.PhotoImage(file=str(icon_path))
                self.root.iconphoto(True, icon)
        except Exception:
            pass

    def center_window(self):
        self.root.update_idletasks()
        w, h = 1024, 760
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')

    def fade_in(self):
        alpha = 0.0
        def increase():
            nonlocal alpha
            alpha += 0.05
            if alpha >= 1.0:
                self.root.attributes('-alpha', 1.0)
                return
            self.root.attributes('-alpha', alpha)
            self.root.after(20, increase)
        increase()
        
    def _warmup_rembg(self):
        """Precarga el modelo de rembg en segundo plano para evitar bloqueos."""
        try:
            dummy = Image.new("RGB", (10, 10), color="white")
            remove(dummy)  # Esto fuerza la descarga/carga del modelo
            self.update_status("Modelo de IA listo", "🧠")
        except Exception:
            pass  # Silencioso, ya se mostrará error cuando el usuario intente usarlo

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        PRIMARY = "#4361EE"
        SECONDARY = "#3A0CA3"
        ACCENT = "#F72585"
        BG = "#F5F7FA"
        CARD = "#FFFFFF"
        TEXT = "#2B2D42"
        MUTED = "#8D99AE"

        style.configure('TFrame', background=BG)
        style.configure('Card.TFrame', background=CARD, relief='solid', borderwidth=1, bordercolor='#E9ECEF')
        style.configure('TLabel', background=BG, foreground=TEXT, font=('Segoe UI', 10))
        style.configure('Header.TLabel', font=('Segoe UI', 20, 'bold'), foreground=PRIMARY)
        style.configure('Subtitle.TLabel', font=('Segoe UI', 11), foreground=MUTED)
        style.configure('Status.TLabel', font=('Segoe UI', 9), foreground=MUTED)
        style.configure('Primary.TButton', font=('Segoe UI', 11, 'bold'), background=PRIMARY,
                        foreground='white', borderwidth=0, relief='flat', padding=(15, 8))
        style.map('Primary.TButton', background=[('active', '#3650D5'), ('pressed', '#2A3FBF')],
                  foreground=[('active', 'white'), ('pressed', 'white')])
        style.configure('Secondary.TButton', font=('Segoe UI', 10), background=CARD,
                        foreground=PRIMARY, borderwidth=1, bordercolor=PRIMARY, relief='solid', padding=(10, 5))
        style.map('Secondary.TButton', background=[('active', '#E6EBFF'), ('pressed', '#D0DCFF')])
        style.configure('Danger.TButton', font=('Segoe UI', 9), background=CARD,
                        foreground='#E63946', borderwidth=1, bordercolor='#E63946', relief='solid', padding=(5, 3))
        style.map('Danger.TButton', background=[('active', '#FFEBEE'), ('pressed', '#FFCDD2')])
        style.configure('Generate.TButton', font=('Segoe UI', 12, 'bold'), background=SECONDARY,
                        foreground='white', borderwidth=0, relief='flat', padding=(20, 10))
        style.map('Generate.TButton', background=[('active', '#2D0A7A'), ('pressed', '#1F0560')])
        style.configure('TEntry', fieldbackground=CARD, borderwidth=1, bordercolor='#CED4DA',
                        relief='solid', padding=8)
        style.map('TEntry', bordercolor=[('focus', PRIMARY)], lightcolor=[('focus', PRIMARY)])
        style.configure('TCombobox', fieldbackground=CARD, borderwidth=1, bordercolor='#CED4DA',
                        relief='solid', padding=6, arrowcolor=PRIMARY)
        style.configure('TProgressbar', background=PRIMARY, troughcolor='#E9ECEF',
                        borderwidth=0, lightcolor=PRIMARY, darkcolor=PRIMARY)
        style.configure('Accent.Horizontal.TProgressbar', background=ACCENT, troughcolor='#E9ECEF')

    # -------------------------------------------------------------------------
    # Pestañas
    # -------------------------------------------------------------------------
    def create_notebook(self):
        self.notebook = ttk.Notebook(self.root, style='TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        style = ttk.Style()
        style.configure('TNotebook', background='#F5F7FA', borderwidth=0)
        style.configure('TNotebook.Tab', background='#E9ECEF', foreground='#2B2D42',
                        padding=[20, 8], font=('Segoe UI', 11, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', '#FFFFFF'), ('active', '#F0F2F5')],
                  foreground=[('selected', '#4361EE')], expand=[('selected', [1, 1, 1, 0])])

        self.tab_remove = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_remove, text=" 🖼️ Quitar Fondo ")
        self.create_remove_bg_tab()

        self.tab_generate = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_generate, text=" ✨ Generar con IA ")
        self.create_generate_ai_tab()

    # -------------------------------------------------------------------------
    # Pestaña: Quitar Fondo (con edición básica)
    # -------------------------------------------------------------------------
    def create_remove_bg_tab(self):
        main = ttk.Frame(self.tab_remove, style='Card.TFrame', padding=30)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Configurar grid de main
        main.columnconfigure(0, weight=0)      # Columna izquierda (ancho fijo)
        main.columnconfigure(1, weight=1)      # Columna derecha (ancho fijo también, pero con peso 1 para absorber espacio sobrante)
        main.rowconfigure(2, weight=1)         # Fila de contenido principal (expandible verticalmente)

        # Títulos (ocupan ambas columnas)
        ttk.Label(main, text="JVA Studio", style='Header.TLabel').grid(row=0, column=0, columnspan=2, pady=(0,5))
        ttk.Label(main, text="Elimina el fondo y edita tus imágenes", style='Subtitle.TLabel').grid(row=1, column=0, columnspan=2, pady=(0,20))

        # Panel izquierdo (ancho fijo 380 px)
        left_frame = ttk.Frame(main, width=380)
        left_frame.grid(row=2, column=0, sticky='nsew', padx=(0,15))
        left_frame.pack_propagate(False)       # Evita que el contenido cambie el ancho

        # Panel derecho (ancho fijo 680 px)
        right_frame = ttk.Frame(main, width=680)
        right_frame.grid(row=2, column=1, sticky='nsew')
        right_frame.pack_propagate(False)

        # --- Contenido del panel izquierdo (sin cambios internos, solo empaquetado) ---
        # URL
        card_url = ttk.Frame(left_frame, style='Card.TFrame', padding=15)
        card_url.pack(fill=tk.X, pady=5)
        ttk.Label(card_url, text="🌐 URL de la imagen", font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0, 8))
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(card_url, textvariable=self.url_var, font=('Segoe UI', 10))
        self.url_entry.pack(fill=tk.X)

        # Archivo Local
        card_local = ttk.Frame(left_frame, style='Card.TFrame', padding=15)
        card_local.pack(fill=tk.X, pady=10)
        ttk.Label(card_local, text="📁 O selecciona un archivo", font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0, 8))
        local_row = ttk.Frame(card_local)
        local_row.pack(fill=tk.X)
        self.local_file_btn = ttk.Button(local_row, text="📂 Examinar", command=self.select_local_image,
                                         style='Secondary.TButton')
        self.local_file_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.local_path_var = tk.StringVar(value="Ningún archivo seleccionado")
        ttk.Label(local_row, textvariable=self.local_path_var, foreground='#6C757D', anchor='w', width=30).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.clear_local_btn = ttk.Button(local_row, text="✕ Quitar", command=self.clear_local_image,
                                          style='Danger.TButton')
        self.clear_local_btn.pack(side=tk.RIGHT)
        self.clear_local_btn.config(state=tk.DISABLED)

        # Formato de salida
        format_frame = ttk.Frame(left_frame, style='Card.TFrame', padding=15)
        format_frame.pack(fill=tk.X, pady=10)
        ttk.Label(format_frame, text="⚙️ Formato de salida", font=('Segoe UI', 11, 'bold')).grid(row=0, column=0, sticky='w', pady=(0, 10))
        self.format_var = tk.StringVar(value="PNG")
        format_combo = ttk.Combobox(format_frame, textvariable=self.format_var,
                                    values=["PNG", "JPEG", "WebP"], state="readonly", width=12)
        format_combo.grid(row=0, column=1, padx=10)
        format_combo.current(0)
        ttk.Label(format_frame, text="⚠️ JPEG no conserva transparencia.", style='Status.TLabel').grid(row=1, column=0, columnspan=2, sticky='w')

        # Botón procesar
        self.process_btn = ttk.Button(left_frame, text="✨ Eliminar fondo", command=self.start_processing,
                                      style='Primary.TButton')
        self.process_btn.pack(pady=15)

        # --- Contenido del panel derecho (vista previa y herramientas) ---
        # Vista previa con tamaño fijo
        # Marco de vista previa con altura fija pero con scroll
                # Marco de vista previa con altura fija y controles de zoom
        preview_card = ttk.Frame(right_frame, style='Card.TFrame', padding=10, height=300, width=660)
        preview_card.pack(fill=tk.X, pady=(0,10))
        preview_card.pack_propagate(False)

        # Cabecera: título y botones de zoom
        header_frame = ttk.Frame(preview_card)
        header_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(header_frame, text="Vista previa", font=('Segoe UI', 11, 'bold')).pack(side=tk.LEFT)

        zoom_frame = ttk.Frame(header_frame)
        zoom_frame.pack(side=tk.RIGHT)

        ttk.Button(zoom_frame, text="🔍-", command=self.zoom_out, style='Secondary.TButton', width=3).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="🔍+", command=self.zoom_in, style='Secondary.TButton', width=3).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="↺", command=self.zoom_reset, style='Secondary.TButton', width=3).pack(side=tk.LEFT, padx=2)

        # Canvas + scrollbars
        canvas_frame = ttk.Frame(preview_card)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.preview_canvas = tk.Canvas(canvas_frame, bg='#F0F0F0', highlightthickness=0)
        h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.preview_canvas.xview)
        v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.preview_canvas.yview)
        self.preview_canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

        self.preview_canvas.grid(row=0, column=0, sticky='nsew')
        h_scroll.grid(row=1, column=0, sticky='ew')
        v_scroll.grid(row=0, column=1, sticky='ns')

        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # Label dentro del canvas
        self.preview_label = ttk.Label(self.preview_canvas, background='#F0F0F0')
        self.preview_canvas.create_window((0, 0), window=self.preview_label, anchor='nw')
        
        # Barra de herramientas de edición
        edit_container = ttk.Frame(right_frame, style='Card.TFrame', padding=5)
        edit_container.pack(fill=tk.X, pady=(0,10))

        ttk.Label(edit_container, text="🛠️ Herramientas de edición", font=('Segoe UI', 9, 'bold')).grid(
            row=0, column=0, columnspan=4, sticky='w', pady=(0, 3))

        # Botones (textos cortos)
        ttk.Button(edit_container, text="↻ Izq", command=lambda: self.apply_edit('rotate', -90),
                   style='Secondary.TButton', width=6).grid(row=1, column=0, padx=2, pady=2, sticky='ew')
        ttk.Button(edit_container, text="↺ Der", command=lambda: self.apply_edit('rotate', 90),
                   style='Secondary.TButton', width=6).grid(row=1, column=1, padx=2, pady=2, sticky='ew')
        ttk.Button(edit_container, text="⇄ Horiz", command=lambda: self.apply_edit('flip', 'horizontal'),
                   style='Secondary.TButton', width=6).grid(row=1, column=2, padx=2, pady=2, sticky='ew')
        ttk.Button(edit_container, text="⇅ Vert", command=lambda: self.apply_edit('flip', 'vertical'),
                   style='Secondary.TButton', width=6).grid(row=1, column=3, padx=2, pady=2, sticky='ew')

        ttk.Button(edit_container, text="✂ Recortar", command=self.start_crop,
                   style='Secondary.TButton', width=8).grid(row=2, column=0, padx=2, pady=2, sticky='ew')
        ttk.Button(edit_container, text="📏 Redim", command=self.resize_dialog,
                   style='Secondary.TButton', width=8).grid(row=2, column=1, padx=2, pady=2, sticky='ew')
        ttk.Button(edit_container, text="⟲ Restaurar", command=self.restore_original,
                   style='Danger.TButton', width=8).grid(row=2, column=2, padx=2, pady=2, sticky='ew')
        ttk.Label(edit_container, text="").grid(row=2, column=3)

        for col in range(4):
            edit_container.columnconfigure(col, weight=1)

        # --- Frame inferior para progreso y estado (anclado al fondo) ---
        bottom_frame = ttk.Frame(main)
        bottom_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(10,0))

        self.progress = ttk.Progressbar(bottom_frame, mode='indeterminate', length=500)
        self.progress.pack(pady=5)

        # Etiqueta de estado (ya inicializada en __init__, solo actualizamos texto)
        ttk.Label(bottom_frame, textvariable=self.status_var, style='Status.TLabel').pack(pady=(0,5))

        # Footer
        ttk.Label(main, text="JVA Studio © 2026 - v1.0", font=('Segoe UI', 8),
                  foreground='#ADB5BD').grid(row=4, column=0, columnspan=2, pady=(20,0))
    
    # -------------------------------------------------------------------------
    # Pestaña: Generar con IA (sin cambios)
    # -------------------------------------------------------------------------
    def create_generate_ai_tab(self):
        main = ttk.Frame(self.tab_generate, style='Card.TFrame', padding=30)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        ttk.Label(main, text="JVA Studio AI", style='Header.TLabel').pack(anchor='center')
        ttk.Label(main, text="Crea imágenes a partir de texto", style='Subtitle.TLabel').pack(pady=(5, 20))
        card_prompt = ttk.Frame(main, style='Card.TFrame', padding=15)
        card_prompt.pack(fill=tk.X, pady=5)
        ttk.Label(card_prompt, text="💬 Describe la imagen", font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0, 8))
        self.prompt_text = tk.Text(card_prompt, height=4, font=('Segoe UI', 11), wrap=tk.WORD,
                                   bg='#FFFFFF', fg='#2B2D42', relief='solid', borderwidth=1)
        self.prompt_text.pack(fill=tk.BOTH)
        self.prompt_text.insert('1.0', "Ej: Un gato astronauta en una galaxia colorida")
        options_frame = ttk.Frame(main, style='Card.TFrame', padding=15)
        options_frame.pack(fill=tk.X, pady=10)
        ttk.Label(options_frame, text="🎨 Formato:").pack(side=tk.LEFT)
        self.ai_format_var = tk.StringVar(value="PNG")
        format_combo = ttk.Combobox(options_frame, textvariable=self.ai_format_var,
                                    values=["PNG", "JPEG", "WebP"], state="readonly", width=8)
        format_combo.pack(side=tk.LEFT, padx=(5, 25))
        self.remove_bg_after_gen = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Quitar fondo automáticamente",
                        variable=self.remove_bg_after_gen).pack(side=tk.LEFT)
        self.generate_btn = ttk.Button(main, text="🎨 Generar imagen", command=self.start_generation,
                                       style='Generate.TButton')
        self.generate_btn.pack(pady=20)
        self.ai_progress = ttk.Progressbar(main, mode='indeterminate', length=500, style='Accent.Horizontal.TProgressbar')
        self.ai_progress.pack(pady=5)
        ttk.Label(main, text="JVA Studio © 2026", font=('Segoe UI', 8), foreground='#ADB5BD').pack(side=tk.BOTTOM, pady=(20, 0))

    # -------------------------------------------------------------------------
    # Edición de imagen
    # -------------------------------------------------------------------------
    def update_preview(self, image=None):
        """Actualiza la vista previa con la imagen editada (o la original)."""
        if image is None:
            image = self.edited_image if self.edited_image else self.original_image
        if image is None:
            self.preview_label.config(image='')
            self.preview_canvas.config(scrollregion=(0, 0, 0, 0))
            self.base_preview_image = None
            return

        # Guardamos la imagen base para poder reescalar después
        self.base_preview_image = image.copy()
        self.apply_zoom_to_preview()

    def apply_zoom_to_preview(self):
        """Aplica el factor de zoom actual a la imagen base y la muestra en el canvas."""
        if self.base_preview_image is None:
            return

        img = self.base_preview_image
        new_width = int(img.width * self.zoom_factor)
        new_height = int(img.height * self.zoom_factor)

        if new_width > 0 and new_height > 0:
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            resized = img

        self.preview_tk = ImageTk.PhotoImage(resized)
        self.preview_label.config(image=self.preview_tk)

        # Actualizar región de scroll al tamaño escalado
        self.preview_canvas.config(scrollregion=(0, 0, resized.width, resized.height))

    def zoom_in(self):
        """Aumenta el zoom un paso."""
        self.zoom_factor += self.zoom_step
        self.apply_zoom_to_preview()

    def zoom_out(self):
        """Reduce el zoom un paso (sin bajar de 0.1)."""
        self.zoom_factor = max(0.1, self.zoom_factor - self.zoom_step)
        self.apply_zoom_to_preview()

    def zoom_reset(self):
        """Restaura el zoom al 100%."""
        self.zoom_factor = 1.0
        self.apply_zoom_to_preview()

    def apply_edit(self, operation, *args):
        """Aplica una transformación a la imagen editada y refresca la preview."""
        if self.original_image is None:
            messagebox.showinfo("Sin imagen", "Primero carga una imagen.")
            return
        if self.edited_image is None:
            self.edited_image = self.original_image.copy()
        if operation == 'rotate':
            angle = args[0]
            self.edited_image = self.edited_image.rotate(angle, expand=True)
        elif operation == 'flip':
            direction = args[0]
            if direction == 'horizontal':
                self.edited_image = ImageOps.mirror(self.edited_image)
            elif direction == 'vertical':
                self.edited_image = ImageOps.flip(self.edited_image)
        elif operation == 'crop':
            box = args[0]
            self.edited_image = self.edited_image.crop(box)
        elif operation == 'resize':
            size = args[0]
            self.edited_image = self.edited_image.resize(size, Image.Resampling.LANCZOS)

        # Actualizar la imagen base y refrescar con el zoom actual
        self.base_preview_image = self.edited_image.copy()
        self.apply_zoom_to_preview()

    def start_crop(self):
        """Activa el modo de recorte mediante selección en la preview."""
        if self.original_image is None:
            messagebox.showinfo("Sin imagen", "Carga una imagen primero.")
            return
        # Implementación simple: solicitar coordenadas por diálogo
        # (Una versión más avanzada usaría eventos de ratón sobre el canvas)
        crop_str = simpledialog.askstring("Recortar",
                                          "Introduce las coordenadas (izquierda, superior, derecha, inferior):\n"
                                          "Ejemplo: 50,50,300,300")
        if crop_str:
            try:
                parts = [int(p.strip()) for p in crop_str.split(',')]
                if len(parts) == 4:
                    self.apply_edit('crop', tuple(parts))
                else:
                    messagebox.showerror("Error", "Debes introducir 4 números separados por comas.")
            except ValueError:
                messagebox.showerror("Error", "Coordenadas inválidas.")

    def resize_dialog(self):
        """Diálogo personalizado para redimensionar la imagen (ancho y alto)."""
        if self.original_image is None:
            messagebox.showinfo("Sin imagen", "Carga una imagen primero.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Redimensionar imagen")
        dialog.geometry("300x180")
        dialog.resizable(False, False)
        dialog.configure(bg='#F5F7FA')
        dialog.transient(self.root)        # Siempre encima de la ventana principal
        dialog.grab_set()                  # Modal: bloquea la ventana principal
        dialog.focus_force()               # Asegura que tome el foco

        # Centrar respecto a la ventana principal
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 90
        dialog.geometry(f"+{x}+{y}")

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Ancho (píxeles):", font=('Segoe UI', 10)).grid(row=0, column=0, sticky='w', pady=5)
        width_var = tk.StringVar()
        width_entry = ttk.Entry(main_frame, textvariable=width_var, font=('Segoe UI', 10), width=15)
        width_entry.grid(row=0, column=1, padx=10, pady=5)
        width_entry.focus()                # Foco inicial

        ttk.Label(main_frame, text="Alto (píxeles):", font=('Segoe UI', 10)).grid(row=1, column=0, sticky='w', pady=5)
        height_var = tk.StringVar()
        height_entry = ttk.Entry(main_frame, textvariable=height_var, font=('Segoe UI', 10), width=15)
        height_entry.grid(row=1, column=1, padx=10, pady=5)

        def confirm():
            try:
                w = int(width_var.get().strip())
                h = int(height_var.get().strip())
                if w < 1 or h < 1:
                    raise ValueError
                dialog.destroy()
                self.apply_edit('resize', (w, h))
            except ValueError:
                messagebox.showerror("Error", "Introduce valores numéricos positivos.", parent=dialog)

        def cancel():
            dialog.destroy()

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Aceptar", command=confirm, style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=cancel, style='Secondary.TButton').pack(side=tk.LEFT, padx=5)

        # Atajos de teclado
        dialog.bind('<Return>', lambda e: confirm())
        dialog.bind('<Escape>', lambda e: cancel())

    def restore_original(self):
        """Descarta todas las ediciones y vuelve a la imagen original."""
        if self.original_image:
            self.edited_image = None
            self.zoom_factor = 1.0
            self.base_preview_image = self.original_image.copy()
            self.apply_zoom_to_preview()
            self.update_status("Imagen restaurada", "🔄")
            
    def _truncate_path_display(self, full_path, max_length=40):
        """Devuelve el nombre del archivo truncado para mostrar sin deformar la interfaz."""
        name = Path(full_path).name
        if len(name) <= max_length:
            return name
        return name[:max_length-3] + "..."

    # -------------------------------------------------------------------------
    # Lógica de carga y actualización de imagen
    # -------------------------------------------------------------------------
    def load_image_from_path(self, path):
        """Carga una imagen desde disco y la establece como original."""
        try:
            img = Image.open(path)
            self.original_image = img.copy()
            self.edited_image = None
            self.update_preview()
            self.update_status("Imagen cargada", "✅")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen:\n{e}")

    def load_image_from_url(self, url):
        """Descarga una imagen desde URL y la establece como original."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            self.original_image = img.copy()
            self.edited_image = None
            self.update_preview()
            self.update_status("Imagen descargada", "✅")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo descargar la imagen:\n{e}")

    def select_local_image(self):
        filetypes = [("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("Todos", "*.*")]
        path = filedialog.askopenfilename(title="Seleccionar imagen", filetypes=filetypes)
        if path:
            self.local_image_path = path
            # Mostrar solo nombre de archivo truncado
            display_name = self._truncate_path_display(path)
            self.local_path_var.set(display_name)
            self.clear_local_btn.config(state=tk.NORMAL)
            self.url_entry.config(state=tk.DISABLED)
            self.local_file_btn.config(state=tk.NORMAL)
            self.load_image_from_path(path)

    # -------------------------------------------------------------------------
    # Procesamiento Quitar Fondo (utiliza la imagen editada)
    # -------------------------------------------------------------------------
    def start_processing(self):
        if self.original_image is None:
            messagebox.showwarning("Sin imagen", "Primero carga o selecciona una imagen.")
            return
        if self.format_var.get() == "JPEG":
            if not messagebox.askyesno("Confirmar formato JPEG",
                                       "JPEG no admite transparencia. Se guardará con fondo BLANCO.\n¿Continuar?"):
                return
        self.process_btn.config(state=tk.DISABLED)
        self.progress.start(10)
        self.update_status("Preparando...", "⏳")
        thread = threading.Thread(target=self.process_image, daemon=True)
        thread.start()

    def process_image(self):
        try:
            # Usar la imagen editada si existe, si no la original
            img_to_process = self.edited_image if self.edited_image else self.original_image
            if getattr(img_to_process, "is_animated", False):
                self.process_animated_gif(img_to_process)
            else:
                self.process_static_image(img_to_process)
        except Exception as e:
            self.root.after(0, self.on_error, str(e))

    def process_static_image(self, img):
        self.update_status("Procesando con IA...", "🧠")
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        output = remove(img)
        formato = self.format_var.get().lower()
        self.update_status(f"Guardando {formato.upper()}...", "💾")
        save_path = self.save_image(output, formato, destination="remove_bg")
        self.update_status("¡Completado!", "✅")
        self.root.after(0, self.on_success, save_path)

    def process_animated_gif(self, img):
        total = img.n_frames
        frames, durations = [], []
        for i, frame in enumerate(ImageSequence.Iterator(img), 1):
            self.update_status(f"Fotograma {i}/{total}", "🎞️")
            durations.append(frame.info.get('duration', 100))
            frame_rgba = frame.convert("RGBA")
            processed = remove(frame_rgba)
            frames.append(processed)
            self.root.update_idletasks()
        self.update_status("Ensamblando GIF...", "🎬")
        save_path = self.save_animated_gif(frames, durations, img.info.get('loop', 0))
        self.update_status("¡GIF listo!", "✅")
        self.root.after(0, self.on_success, save_path)

    # -------------------------------------------------------------------------
    # Resto de métodos (generación IA, guardado, utilidades) sin cambios...
    # -------------------------------------------------------------------------
    def setup_input_tracking(self):
        self.url_var.trace_add('write', self.on_input_change)

    def on_input_change(self, *args):
        url_present = bool(self.url_var.get().strip())
        local_present = bool(self.local_image_path)
        if url_present:
            self.local_file_btn.config(state=tk.DISABLED)
            self.clear_local_btn.config(state=tk.DISABLED)
            # Si se escribe URL, se podría descargar automáticamente al pulsar Enter
        elif local_present:
            self.url_entry.config(state=tk.DISABLED)
            self.clear_local_btn.config(state=tk.NORMAL)
        else:
            self.url_entry.config(state=tk.NORMAL)
            self.local_file_btn.config(state=tk.NORMAL)
            self.clear_local_btn.config(state=tk.DISABLED)

    def clear_local_image(self):
        self.local_image_path = None
        self.local_path_var.set("Ningún archivo seleccionado")
        self.clear_local_btn.config(state=tk.DISABLED)
        self.original_image = None
        self.edited_image = None
        self.update_preview()
        if not self.url_var.get().strip():
            self.url_entry.config(state=tk.NORMAL)
            self.local_file_btn.config(state=tk.NORMAL)

    def setup_keyboard_shortcuts(self):
        self.root.bind('<Control-v>', lambda e: self.paste_from_clipboard())
        self.url_entry.bind('<Return>', lambda e: self.load_url_and_preview())

    def load_url_and_preview(self):
        url = self.url_var.get().strip()
        if url:
            self.load_image_from_url(url)

    def paste_from_clipboard(self):
        try:
            widget = self.root.focus_get()
            if widget == self.url_entry:
                self.url_var.set(self.root.clipboard_get())
            elif widget == self.prompt_text:
                self.prompt_text.insert(tk.INSERT, self.root.clipboard_get())
        except tk.TclError:
            pass

    def update_status(self, message, emoji="🔄"):
        self.root.after(0, lambda: self.status_var.set(f"{emoji} {message}"))

    # -------------------------------------------------------------------------
    # Generación IA
    # -------------------------------------------------------------------------
    def start_generation(self):
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt or prompt == "Ej: Un gato astronauta en una galaxia colorida":
            messagebox.showwarning("Prompt vacío", "Escribe una descripción para generar la imagen.")
            return

        self.generate_btn.config(state=tk.DISABLED)
        self.ai_progress.start(10)
        self.update_status("Generando con IA...", "🎨")
        thread = threading.Thread(target=self.generate_ai_image, args=(prompt,), daemon=True)
        thread.start()

    def generate_ai_image(self, prompt):
        try:
            generator = pollinations.Image()
            generated_img = generator(prompt)
            self.generated_image = generated_img
            self.update_status("Imagen generada", "🖼️")

            if self.remove_bg_after_gen.get():
                self.update_status("Quitando fondo...", "🧽")
                if generated_img.mode not in ("RGB", "RGBA"):
                    generated_img = generated_img.convert("RGBA")
                output = remove(generated_img)
                formato = self.ai_format_var.get().lower()
                save_path = self.save_image(output, formato, destination="ai")
            else:
                formato = self.ai_format_var.get().lower()
                save_path = self.save_image(generated_img, formato, destination="ai")

            self.update_status("¡Imagen guardada!", "✅")
            self.root.after(0, self.on_ai_success, save_path)

        except Exception as e:
            self.root.after(0, self.on_error, f"Error IA: {e}")

    def on_ai_success(self, save_path):
        self.ai_progress.stop()
        self.generate_btn.config(state=tk.NORMAL)
        self.status_var.set(f"✅ Imagen guardada en JVA-Studio/IA")
        messagebox.showinfo("Éxito", f"Imagen generada y guardada en:\n{save_path}")
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", "Ej: Un gato astronauta en una galaxia colorida")

    # -------------------------------------------------------------------------
    # Guardado en carpetas
    # -------------------------------------------------------------------------
    def get_destination_folder(self, destination):
        pictures = Path.home() / "Pictures"
        if not pictures.exists():
            pictures = Path.home() / "Imágenes"
        studio = pictures / "JVA-Studio"
        folder = studio / ("QuitaFondos" if destination == "remove_bg" else "IA")
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def generate_filename(self, extension):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"jva_{timestamp}.{extension}"

    def save_image(self, image, formato, destination):
        folder = self.get_destination_folder(destination)
        ext = "jpg" if formato == "jpeg" else formato
        ruta = folder / self.generate_filename(ext)

        if formato in ("jpeg", "jpg"):
            if image.mode in ("RGBA", "LA", "P"):
                fondo = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                fondo.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                image = fondo
            image.save(str(ruta), "JPEG", quality=95)
        elif formato == "webp":
            image.save(str(ruta), "WEBP", quality=95)
        else:
            image.save(str(ruta), "PNG")
        return ruta

    def save_animated_gif(self, frames, durations, loop):
        folder = self.get_destination_folder("remove_bg")
        ruta = folder / self.generate_filename("gif")
        frames[0].save(
            str(ruta),
            save_all=True,
            append_images=frames[1:],
            loop=loop,
            duration=durations,
            disposal=2,
            transparency=0,
            optimize=False
        )
        return ruta

    # -------------------------------------------------------------------------
    # Manejo de éxito / error
    # -------------------------------------------------------------------------
    def on_success(self, save_path):
        self.progress.stop()
        self.process_btn.config(state=tk.NORMAL)
        self.status_var.set(f"✅ Guardado en JVA-Studio/QuitaFondos")
        self.url_var.set("")
        self.clear_local_image()
        self.url_entry.focus()
        messagebox.showinfo("Éxito", f"¡Fondo eliminado!\n\n{save_path}")

    def on_error(self, error_msg):
        self.progress.stop()
        self.ai_progress.stop()
        self.process_btn.config(state=tk.NORMAL)
        self.generate_btn.config(state=tk.NORMAL)
        self.status_var.set(f"❌ Error: {error_msg}")
        messagebox.showerror("Error", error_msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = JVAStudioApp(root)
=======
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import requests
from PIL import Image, ImageSequence, ImageTk, ImageOps
from io import BytesIO
from rembg import remove
from pathlib import Path
from datetime import datetime
import pollinations
import sys

class JVAStudioApp:
    """JVA Studio: Eliminación de fondos, generación IA y edición básica."""

    def __init__(self, root):
        self.root = root
        try:
            # --- Splash screen inmediato ---
            splash = tk.Toplevel(root)
            splash.overrideredirect(True)
            splash.configure(bg='#4361EE')
            splash.geometry("400x200")
            # Centrar splash
            splash.update_idletasks()
            sw = splash.winfo_screenwidth()
            sh = splash.winfo_screenheight()
            x = (sw // 2) - 200
            y = (sh // 2) - 100
            splash.geometry(f"+{x}+{y}")
            ttk.Label(splash, text="JVA Studio", font=('Segoe UI', 24, 'bold'),
                      foreground='white', background='#4361EE').pack(pady=(50,10))
            ttk.Label(splash, text="Cargando...", font=('Segoe UI', 12),
                      foreground='white', background='#4361EE').pack()
            splash.update()

            # --- Inicialización normal ---
            self.root.title("JVA Studio")
            self.root.geometry("1024x760")
            self.root.resizable(False, False)
            self.root.configure(bg='#F5F7FA')
            # Variables de estado (sin cambios)
            self.local_image_path = None
            self.generated_image = None
            self.original_image = None
            self.edited_image = None
            self.preview_tk = None
            self.status_var = tk.StringVar(value="🟢 Listo para comenzar")
            self.progress = None
            self.ai_progress = None
            self.zoom_factor = 1.0
            self.zoom_step = 0.2
            self.base_preview_image = None

            self.root.withdraw()
            self.root.attributes('-alpha', 0.0)

            self.set_app_icon()
            self.setup_styles()
            self.create_notebook()
            self.setup_keyboard_shortcuts()
            self.setup_input_tracking()
            self.center_window()

            # Cerrar splash y mostrar ventana principal
            splash.destroy()
            self.root.deiconify()
            self.fade_in()

            # Precargar modelo de IA en segundo plano (evita bloqueo en el primer uso)
            threading.Thread(target=self._warmup_rembg, daemon=True).start()

        except Exception as e:
            log_path = Path.home() / "jva_studio_error.log"
            with open(log_path, "w", encoding="utf-8") as f:
                traceback.print_exc(file=f)
            messagebox.showerror("Error fatal", f"La aplicación falló al iniciar.\nRevisa el log en:\n{log_path}")
            raise

    # -------------------------------------------------------------------------
    # Estética y configuración
    # -------------------------------------------------------------------------
    def set_app_icon(self):
        try:
            # Determinar ruta base (desarrollo o ejecutable)
            if getattr(sys, 'frozen', False):
                base_path = Path(sys._MEIPASS)
            else:
                base_path = Path(__file__).parent
            icon_path = base_path / "Assets" / "logo.png"
            if icon_path.exists():
                icon = tk.PhotoImage(file=str(icon_path))
                self.root.iconphoto(True, icon)
        except Exception:
            pass

    def center_window(self):
        self.root.update_idletasks()
        w, h = 1024, 760
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')

    def fade_in(self):
        alpha = 0.0
        def increase():
            nonlocal alpha
            alpha += 0.05
            if alpha >= 1.0:
                self.root.attributes('-alpha', 1.0)
                return
            self.root.attributes('-alpha', alpha)
            self.root.after(20, increase)
        increase()
        
    def _warmup_rembg(self):
        """Precarga el modelo de rembg en segundo plano para evitar bloqueos."""
        try:
            dummy = Image.new("RGB", (10, 10), color="white")
            remove(dummy)  # Esto fuerza la descarga/carga del modelo
            self.update_status("Modelo de IA listo", "🧠")
        except Exception:
            pass  # Silencioso, ya se mostrará error cuando el usuario intente usarlo

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        PRIMARY = "#4361EE"
        SECONDARY = "#3A0CA3"
        ACCENT = "#F72585"
        BG = "#F5F7FA"
        CARD = "#FFFFFF"
        TEXT = "#2B2D42"
        MUTED = "#8D99AE"

        style.configure('TFrame', background=BG)
        style.configure('Card.TFrame', background=CARD, relief='solid', borderwidth=1, bordercolor='#E9ECEF')
        style.configure('TLabel', background=BG, foreground=TEXT, font=('Segoe UI', 10))
        style.configure('Header.TLabel', font=('Segoe UI', 20, 'bold'), foreground=PRIMARY)
        style.configure('Subtitle.TLabel', font=('Segoe UI', 11), foreground=MUTED)
        style.configure('Status.TLabel', font=('Segoe UI', 9), foreground=MUTED)
        style.configure('Primary.TButton', font=('Segoe UI', 11, 'bold'), background=PRIMARY,
                        foreground='white', borderwidth=0, relief='flat', padding=(15, 8))
        style.map('Primary.TButton', background=[('active', '#3650D5'), ('pressed', '#2A3FBF')],
                  foreground=[('active', 'white'), ('pressed', 'white')])
        style.configure('Secondary.TButton', font=('Segoe UI', 10), background=CARD,
                        foreground=PRIMARY, borderwidth=1, bordercolor=PRIMARY, relief='solid', padding=(10, 5))
        style.map('Secondary.TButton', background=[('active', '#E6EBFF'), ('pressed', '#D0DCFF')])
        style.configure('Danger.TButton', font=('Segoe UI', 9), background=CARD,
                        foreground='#E63946', borderwidth=1, bordercolor='#E63946', relief='solid', padding=(5, 3))
        style.map('Danger.TButton', background=[('active', '#FFEBEE'), ('pressed', '#FFCDD2')])
        style.configure('Generate.TButton', font=('Segoe UI', 12, 'bold'), background=SECONDARY,
                        foreground='white', borderwidth=0, relief='flat', padding=(20, 10))
        style.map('Generate.TButton', background=[('active', '#2D0A7A'), ('pressed', '#1F0560')])
        style.configure('TEntry', fieldbackground=CARD, borderwidth=1, bordercolor='#CED4DA',
                        relief='solid', padding=8)
        style.map('TEntry', bordercolor=[('focus', PRIMARY)], lightcolor=[('focus', PRIMARY)])
        style.configure('TCombobox', fieldbackground=CARD, borderwidth=1, bordercolor='#CED4DA',
                        relief='solid', padding=6, arrowcolor=PRIMARY)
        style.configure('TProgressbar', background=PRIMARY, troughcolor='#E9ECEF',
                        borderwidth=0, lightcolor=PRIMARY, darkcolor=PRIMARY)
        style.configure('Accent.Horizontal.TProgressbar', background=ACCENT, troughcolor='#E9ECEF')

    # -------------------------------------------------------------------------
    # Pestañas
    # -------------------------------------------------------------------------
    def create_notebook(self):
        self.notebook = ttk.Notebook(self.root, style='TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        style = ttk.Style()
        style.configure('TNotebook', background='#F5F7FA', borderwidth=0)
        style.configure('TNotebook.Tab', background='#E9ECEF', foreground='#2B2D42',
                        padding=[20, 8], font=('Segoe UI', 11, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', '#FFFFFF'), ('active', '#F0F2F5')],
                  foreground=[('selected', '#4361EE')], expand=[('selected', [1, 1, 1, 0])])

        self.tab_remove = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_remove, text=" 🖼️ Quitar Fondo ")
        self.create_remove_bg_tab()

        self.tab_generate = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_generate, text=" ✨ Generar con IA ")
        self.create_generate_ai_tab()

    # -------------------------------------------------------------------------
    # Pestaña: Quitar Fondo (con edición básica)
    # -------------------------------------------------------------------------
    def create_remove_bg_tab(self):
        main = ttk.Frame(self.tab_remove, style='Card.TFrame', padding=30)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Configurar grid de main
        main.columnconfigure(0, weight=0)      # Columna izquierda (ancho fijo)
        main.columnconfigure(1, weight=1)      # Columna derecha (ancho fijo también, pero con peso 1 para absorber espacio sobrante)
        main.rowconfigure(2, weight=1)         # Fila de contenido principal (expandible verticalmente)

        # Títulos (ocupan ambas columnas)
        ttk.Label(main, text="JVA Studio", style='Header.TLabel').grid(row=0, column=0, columnspan=2, pady=(0,5))
        ttk.Label(main, text="Elimina el fondo y edita tus imágenes", style='Subtitle.TLabel').grid(row=1, column=0, columnspan=2, pady=(0,20))

        # Panel izquierdo (ancho fijo 380 px)
        left_frame = ttk.Frame(main, width=380)
        left_frame.grid(row=2, column=0, sticky='nsew', padx=(0,15))
        left_frame.pack_propagate(False)       # Evita que el contenido cambie el ancho

        # Panel derecho (ancho fijo 680 px)
        right_frame = ttk.Frame(main, width=680)
        right_frame.grid(row=2, column=1, sticky='nsew')
        right_frame.pack_propagate(False)

        # --- Contenido del panel izquierdo (sin cambios internos, solo empaquetado) ---
        # URL
        card_url = ttk.Frame(left_frame, style='Card.TFrame', padding=15)
        card_url.pack(fill=tk.X, pady=5)
        ttk.Label(card_url, text="🌐 URL de la imagen", font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0, 8))
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(card_url, textvariable=self.url_var, font=('Segoe UI', 10))
        self.url_entry.pack(fill=tk.X)

        # Archivo Local
        card_local = ttk.Frame(left_frame, style='Card.TFrame', padding=15)
        card_local.pack(fill=tk.X, pady=10)
        ttk.Label(card_local, text="📁 O selecciona un archivo", font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0, 8))
        local_row = ttk.Frame(card_local)
        local_row.pack(fill=tk.X)
        self.local_file_btn = ttk.Button(local_row, text="📂 Examinar", command=self.select_local_image,
                                         style='Secondary.TButton')
        self.local_file_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.local_path_var = tk.StringVar(value="Ningún archivo seleccionado")
        ttk.Label(local_row, textvariable=self.local_path_var, foreground='#6C757D', anchor='w', width=30).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.clear_local_btn = ttk.Button(local_row, text="✕ Quitar", command=self.clear_local_image,
                                          style='Danger.TButton')
        self.clear_local_btn.pack(side=tk.RIGHT)
        self.clear_local_btn.config(state=tk.DISABLED)

        # Formato de salida
        format_frame = ttk.Frame(left_frame, style='Card.TFrame', padding=15)
        format_frame.pack(fill=tk.X, pady=10)
        ttk.Label(format_frame, text="⚙️ Formato de salida", font=('Segoe UI', 11, 'bold')).grid(row=0, column=0, sticky='w', pady=(0, 10))
        self.format_var = tk.StringVar(value="PNG")
        format_combo = ttk.Combobox(format_frame, textvariable=self.format_var,
                                    values=["PNG", "JPEG", "WebP"], state="readonly", width=12)
        format_combo.grid(row=0, column=1, padx=10)
        format_combo.current(0)
        ttk.Label(format_frame, text="⚠️ JPEG no conserva transparencia.", style='Status.TLabel').grid(row=1, column=0, columnspan=2, sticky='w')

        # Botón procesar
        self.process_btn = ttk.Button(left_frame, text="✨ Eliminar fondo", command=self.start_processing,
                                      style='Primary.TButton')
        self.process_btn.pack(pady=15)

        # --- Contenido del panel derecho (vista previa y herramientas) ---
        # Vista previa con tamaño fijo
        # Marco de vista previa con altura fija pero con scroll
                # Marco de vista previa con altura fija y controles de zoom
        preview_card = ttk.Frame(right_frame, style='Card.TFrame', padding=10, height=300, width=660)
        preview_card.pack(fill=tk.X, pady=(0,10))
        preview_card.pack_propagate(False)

        # Cabecera: título y botones de zoom
        header_frame = ttk.Frame(preview_card)
        header_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(header_frame, text="Vista previa", font=('Segoe UI', 11, 'bold')).pack(side=tk.LEFT)

        zoom_frame = ttk.Frame(header_frame)
        zoom_frame.pack(side=tk.RIGHT)

        ttk.Button(zoom_frame, text="🔍-", command=self.zoom_out, style='Secondary.TButton', width=3).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="🔍+", command=self.zoom_in, style='Secondary.TButton', width=3).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="↺", command=self.zoom_reset, style='Secondary.TButton', width=3).pack(side=tk.LEFT, padx=2)

        # Canvas + scrollbars
        canvas_frame = ttk.Frame(preview_card)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.preview_canvas = tk.Canvas(canvas_frame, bg='#F0F0F0', highlightthickness=0)
        h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.preview_canvas.xview)
        v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.preview_canvas.yview)
        self.preview_canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

        self.preview_canvas.grid(row=0, column=0, sticky='nsew')
        h_scroll.grid(row=1, column=0, sticky='ew')
        v_scroll.grid(row=0, column=1, sticky='ns')

        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # Label dentro del canvas
        self.preview_label = ttk.Label(self.preview_canvas, background='#F0F0F0')
        self.preview_canvas.create_window((0, 0), window=self.preview_label, anchor='nw')
        
        # Barra de herramientas de edición
        edit_container = ttk.Frame(right_frame, style='Card.TFrame', padding=5)
        edit_container.pack(fill=tk.X, pady=(0,10))

        ttk.Label(edit_container, text="🛠️ Herramientas de edición", font=('Segoe UI', 9, 'bold')).grid(
            row=0, column=0, columnspan=4, sticky='w', pady=(0, 3))

        # Botones (textos cortos)
        ttk.Button(edit_container, text="↻ Izq", command=lambda: self.apply_edit('rotate', -90),
                   style='Secondary.TButton', width=6).grid(row=1, column=0, padx=2, pady=2, sticky='ew')
        ttk.Button(edit_container, text="↺ Der", command=lambda: self.apply_edit('rotate', 90),
                   style='Secondary.TButton', width=6).grid(row=1, column=1, padx=2, pady=2, sticky='ew')
        ttk.Button(edit_container, text="⇄ Horiz", command=lambda: self.apply_edit('flip', 'horizontal'),
                   style='Secondary.TButton', width=6).grid(row=1, column=2, padx=2, pady=2, sticky='ew')
        ttk.Button(edit_container, text="⇅ Vert", command=lambda: self.apply_edit('flip', 'vertical'),
                   style='Secondary.TButton', width=6).grid(row=1, column=3, padx=2, pady=2, sticky='ew')

        ttk.Button(edit_container, text="✂ Recortar", command=self.start_crop,
                   style='Secondary.TButton', width=8).grid(row=2, column=0, padx=2, pady=2, sticky='ew')
        ttk.Button(edit_container, text="📏 Redim", command=self.resize_dialog,
                   style='Secondary.TButton', width=8).grid(row=2, column=1, padx=2, pady=2, sticky='ew')
        ttk.Button(edit_container, text="⟲ Restaurar", command=self.restore_original,
                   style='Danger.TButton', width=8).grid(row=2, column=2, padx=2, pady=2, sticky='ew')
        ttk.Label(edit_container, text="").grid(row=2, column=3)

        for col in range(4):
            edit_container.columnconfigure(col, weight=1)

        # --- Frame inferior para progreso y estado (anclado al fondo) ---
        bottom_frame = ttk.Frame(main)
        bottom_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(10,0))

        self.progress = ttk.Progressbar(bottom_frame, mode='indeterminate', length=500)
        self.progress.pack(pady=5)

        # Etiqueta de estado (ya inicializada en __init__, solo actualizamos texto)
        ttk.Label(bottom_frame, textvariable=self.status_var, style='Status.TLabel').pack(pady=(0,5))

        # Footer
        ttk.Label(main, text="JVA Studio © 2026 - v1.0", font=('Segoe UI', 8),
                  foreground='#ADB5BD').grid(row=4, column=0, columnspan=2, pady=(20,0))
    
    # -------------------------------------------------------------------------
    # Pestaña: Generar con IA (sin cambios)
    # -------------------------------------------------------------------------
    def create_generate_ai_tab(self):
        main = ttk.Frame(self.tab_generate, style='Card.TFrame', padding=30)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        ttk.Label(main, text="JVA Studio AI", style='Header.TLabel').pack(anchor='center')
        ttk.Label(main, text="Crea imágenes a partir de texto", style='Subtitle.TLabel').pack(pady=(5, 20))
        card_prompt = ttk.Frame(main, style='Card.TFrame', padding=15)
        card_prompt.pack(fill=tk.X, pady=5)
        ttk.Label(card_prompt, text="💬 Describe la imagen", font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0, 8))
        self.prompt_text = tk.Text(card_prompt, height=4, font=('Segoe UI', 11), wrap=tk.WORD,
                                   bg='#FFFFFF', fg='#2B2D42', relief='solid', borderwidth=1)
        self.prompt_text.pack(fill=tk.BOTH)
        self.prompt_text.insert('1.0', "Ej: Un gato astronauta en una galaxia colorida")
        options_frame = ttk.Frame(main, style='Card.TFrame', padding=15)
        options_frame.pack(fill=tk.X, pady=10)
        ttk.Label(options_frame, text="🎨 Formato:").pack(side=tk.LEFT)
        self.ai_format_var = tk.StringVar(value="PNG")
        format_combo = ttk.Combobox(options_frame, textvariable=self.ai_format_var,
                                    values=["PNG", "JPEG", "WebP"], state="readonly", width=8)
        format_combo.pack(side=tk.LEFT, padx=(5, 25))
        self.remove_bg_after_gen = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Quitar fondo automáticamente",
                        variable=self.remove_bg_after_gen).pack(side=tk.LEFT)
        self.generate_btn = ttk.Button(main, text="🎨 Generar imagen", command=self.start_generation,
                                       style='Generate.TButton')
        self.generate_btn.pack(pady=20)
        self.ai_progress = ttk.Progressbar(main, mode='indeterminate', length=500, style='Accent.Horizontal.TProgressbar')
        self.ai_progress.pack(pady=5)
        ttk.Label(main, text="JVA Studio © 2026", font=('Segoe UI', 8), foreground='#ADB5BD').pack(side=tk.BOTTOM, pady=(20, 0))

    # -------------------------------------------------------------------------
    # Edición de imagen
    # -------------------------------------------------------------------------
    def update_preview(self, image=None):
        """Actualiza la vista previa con la imagen editada (o la original)."""
        if image is None:
            image = self.edited_image if self.edited_image else self.original_image
        if image is None:
            self.preview_label.config(image='')
            self.preview_canvas.config(scrollregion=(0, 0, 0, 0))
            self.base_preview_image = None
            return

        # Guardamos la imagen base para poder reescalar después
        self.base_preview_image = image.copy()
        self.apply_zoom_to_preview()

    def apply_zoom_to_preview(self):
        """Aplica el factor de zoom actual a la imagen base y la muestra en el canvas."""
        if self.base_preview_image is None:
            return

        img = self.base_preview_image
        new_width = int(img.width * self.zoom_factor)
        new_height = int(img.height * self.zoom_factor)

        if new_width > 0 and new_height > 0:
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            resized = img

        self.preview_tk = ImageTk.PhotoImage(resized)
        self.preview_label.config(image=self.preview_tk)

        # Actualizar región de scroll al tamaño escalado
        self.preview_canvas.config(scrollregion=(0, 0, resized.width, resized.height))

    def zoom_in(self):
        """Aumenta el zoom un paso."""
        self.zoom_factor += self.zoom_step
        self.apply_zoom_to_preview()

    def zoom_out(self):
        """Reduce el zoom un paso (sin bajar de 0.1)."""
        self.zoom_factor = max(0.1, self.zoom_factor - self.zoom_step)
        self.apply_zoom_to_preview()

    def zoom_reset(self):
        """Restaura el zoom al 100%."""
        self.zoom_factor = 1.0
        self.apply_zoom_to_preview()

    def apply_edit(self, operation, *args):
        """Aplica una transformación a la imagen editada y refresca la preview."""
        if self.original_image is None:
            messagebox.showinfo("Sin imagen", "Primero carga una imagen.")
            return
        if self.edited_image is None:
            self.edited_image = self.original_image.copy()
        if operation == 'rotate':
            angle = args[0]
            self.edited_image = self.edited_image.rotate(angle, expand=True)
        elif operation == 'flip':
            direction = args[0]
            if direction == 'horizontal':
                self.edited_image = ImageOps.mirror(self.edited_image)
            elif direction == 'vertical':
                self.edited_image = ImageOps.flip(self.edited_image)
        elif operation == 'crop':
            box = args[0]
            self.edited_image = self.edited_image.crop(box)
        elif operation == 'resize':
            size = args[0]
            self.edited_image = self.edited_image.resize(size, Image.Resampling.LANCZOS)

        # Actualizar la imagen base y refrescar con el zoom actual
        self.base_preview_image = self.edited_image.copy()
        self.apply_zoom_to_preview()

    def start_crop(self):
        """Activa el modo de recorte mediante selección en la preview."""
        if self.original_image is None:
            messagebox.showinfo("Sin imagen", "Carga una imagen primero.")
            return
        # Implementación simple: solicitar coordenadas por diálogo
        # (Una versión más avanzada usaría eventos de ratón sobre el canvas)
        crop_str = simpledialog.askstring("Recortar",
                                          "Introduce las coordenadas (izquierda, superior, derecha, inferior):\n"
                                          "Ejemplo: 50,50,300,300")
        if crop_str:
            try:
                parts = [int(p.strip()) for p in crop_str.split(',')]
                if len(parts) == 4:
                    self.apply_edit('crop', tuple(parts))
                else:
                    messagebox.showerror("Error", "Debes introducir 4 números separados por comas.")
            except ValueError:
                messagebox.showerror("Error", "Coordenadas inválidas.")

    def resize_dialog(self):
        """Diálogo personalizado para redimensionar la imagen (ancho y alto)."""
        if self.original_image is None:
            messagebox.showinfo("Sin imagen", "Carga una imagen primero.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Redimensionar imagen")
        dialog.geometry("300x180")
        dialog.resizable(False, False)
        dialog.configure(bg='#F5F7FA')
        dialog.transient(self.root)        # Siempre encima de la ventana principal
        dialog.grab_set()                  # Modal: bloquea la ventana principal
        dialog.focus_force()               # Asegura que tome el foco

        # Centrar respecto a la ventana principal
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 90
        dialog.geometry(f"+{x}+{y}")

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Ancho (píxeles):", font=('Segoe UI', 10)).grid(row=0, column=0, sticky='w', pady=5)
        width_var = tk.StringVar()
        width_entry = ttk.Entry(main_frame, textvariable=width_var, font=('Segoe UI', 10), width=15)
        width_entry.grid(row=0, column=1, padx=10, pady=5)
        width_entry.focus()                # Foco inicial

        ttk.Label(main_frame, text="Alto (píxeles):", font=('Segoe UI', 10)).grid(row=1, column=0, sticky='w', pady=5)
        height_var = tk.StringVar()
        height_entry = ttk.Entry(main_frame, textvariable=height_var, font=('Segoe UI', 10), width=15)
        height_entry.grid(row=1, column=1, padx=10, pady=5)

        def confirm():
            try:
                w = int(width_var.get().strip())
                h = int(height_var.get().strip())
                if w < 1 or h < 1:
                    raise ValueError
                dialog.destroy()
                self.apply_edit('resize', (w, h))
            except ValueError:
                messagebox.showerror("Error", "Introduce valores numéricos positivos.", parent=dialog)

        def cancel():
            dialog.destroy()

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Aceptar", command=confirm, style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=cancel, style='Secondary.TButton').pack(side=tk.LEFT, padx=5)

        # Atajos de teclado
        dialog.bind('<Return>', lambda e: confirm())
        dialog.bind('<Escape>', lambda e: cancel())

    def restore_original(self):
        """Descarta todas las ediciones y vuelve a la imagen original."""
        if self.original_image:
            self.edited_image = None
            self.zoom_factor = 1.0
            self.base_preview_image = self.original_image.copy()
            self.apply_zoom_to_preview()
            self.update_status("Imagen restaurada", "🔄")
            
    def _truncate_path_display(self, full_path, max_length=40):
        """Devuelve el nombre del archivo truncado para mostrar sin deformar la interfaz."""
        name = Path(full_path).name
        if len(name) <= max_length:
            return name
        return name[:max_length-3] + "..."

    # -------------------------------------------------------------------------
    # Lógica de carga y actualización de imagen
    # -------------------------------------------------------------------------
    def load_image_from_path(self, path):
        """Carga una imagen desde disco y la establece como original."""
        try:
            img = Image.open(path)
            self.original_image = img.copy()
            self.edited_image = None
            self.update_preview()
            self.update_status("Imagen cargada", "✅")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen:\n{e}")

    def load_image_from_url(self, url):
        """Descarga una imagen desde URL y la establece como original."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            self.original_image = img.copy()
            self.edited_image = None
            self.update_preview()
            self.update_status("Imagen descargada", "✅")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo descargar la imagen:\n{e}")

    def select_local_image(self):
        filetypes = [("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("Todos", "*.*")]
        path = filedialog.askopenfilename(title="Seleccionar imagen", filetypes=filetypes)
        if path:
            self.local_image_path = path
            # Mostrar solo nombre de archivo truncado
            display_name = self._truncate_path_display(path)
            self.local_path_var.set(display_name)
            self.clear_local_btn.config(state=tk.NORMAL)
            self.url_entry.config(state=tk.DISABLED)
            self.local_file_btn.config(state=tk.NORMAL)
            self.load_image_from_path(path)

    # -------------------------------------------------------------------------
    # Procesamiento Quitar Fondo (utiliza la imagen editada)
    # -------------------------------------------------------------------------
    def start_processing(self):
        if self.original_image is None:
            messagebox.showwarning("Sin imagen", "Primero carga o selecciona una imagen.")
            return
        if self.format_var.get() == "JPEG":
            if not messagebox.askyesno("Confirmar formato JPEG",
                                       "JPEG no admite transparencia. Se guardará con fondo BLANCO.\n¿Continuar?"):
                return
        self.process_btn.config(state=tk.DISABLED)
        self.progress.start(10)
        self.update_status("Preparando...", "⏳")
        thread = threading.Thread(target=self.process_image, daemon=True)
        thread.start()

    def process_image(self):
        try:
            # Usar la imagen editada si existe, si no la original
            img_to_process = self.edited_image if self.edited_image else self.original_image
            if getattr(img_to_process, "is_animated", False):
                self.process_animated_gif(img_to_process)
            else:
                self.process_static_image(img_to_process)
        except Exception as e:
            self.root.after(0, self.on_error, str(e))

    def process_static_image(self, img):
        self.update_status("Procesando con IA...", "🧠")
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        output = remove(img)
        formato = self.format_var.get().lower()
        self.update_status(f"Guardando {formato.upper()}...", "💾")
        save_path = self.save_image(output, formato, destination="remove_bg")
        self.update_status("¡Completado!", "✅")
        self.root.after(0, self.on_success, save_path)

    def process_animated_gif(self, img):
        total = img.n_frames
        frames, durations = [], []
        for i, frame in enumerate(ImageSequence.Iterator(img), 1):
            self.update_status(f"Fotograma {i}/{total}", "🎞️")
            durations.append(frame.info.get('duration', 100))
            frame_rgba = frame.convert("RGBA")
            processed = remove(frame_rgba)
            frames.append(processed)
            self.root.update_idletasks()
        self.update_status("Ensamblando GIF...", "🎬")
        save_path = self.save_animated_gif(frames, durations, img.info.get('loop', 0))
        self.update_status("¡GIF listo!", "✅")
        self.root.after(0, self.on_success, save_path)

    # -------------------------------------------------------------------------
    # Resto de métodos (generación IA, guardado, utilidades) sin cambios...
    # -------------------------------------------------------------------------
    def setup_input_tracking(self):
        self.url_var.trace_add('write', self.on_input_change)

    def on_input_change(self, *args):
        url_present = bool(self.url_var.get().strip())
        local_present = bool(self.local_image_path)
        if url_present:
            self.local_file_btn.config(state=tk.DISABLED)
            self.clear_local_btn.config(state=tk.DISABLED)
            # Si se escribe URL, se podría descargar automáticamente al pulsar Enter
        elif local_present:
            self.url_entry.config(state=tk.DISABLED)
            self.clear_local_btn.config(state=tk.NORMAL)
        else:
            self.url_entry.config(state=tk.NORMAL)
            self.local_file_btn.config(state=tk.NORMAL)
            self.clear_local_btn.config(state=tk.DISABLED)

    def clear_local_image(self):
        self.local_image_path = None
        self.local_path_var.set("Ningún archivo seleccionado")
        self.clear_local_btn.config(state=tk.DISABLED)
        self.original_image = None
        self.edited_image = None
        self.update_preview()
        if not self.url_var.get().strip():
            self.url_entry.config(state=tk.NORMAL)
            self.local_file_btn.config(state=tk.NORMAL)

    def setup_keyboard_shortcuts(self):
        self.root.bind('<Control-v>', lambda e: self.paste_from_clipboard())
        self.url_entry.bind('<Return>', lambda e: self.load_url_and_preview())

    def load_url_and_preview(self):
        url = self.url_var.get().strip()
        if url:
            self.load_image_from_url(url)

    def paste_from_clipboard(self):
        try:
            widget = self.root.focus_get()
            if widget == self.url_entry:
                self.url_var.set(self.root.clipboard_get())
            elif widget == self.prompt_text:
                self.prompt_text.insert(tk.INSERT, self.root.clipboard_get())
        except tk.TclError:
            pass

    def update_status(self, message, emoji="🔄"):
        self.root.after(0, lambda: self.status_var.set(f"{emoji} {message}"))

    # -------------------------------------------------------------------------
    # Generación IA
    # -------------------------------------------------------------------------
    def start_generation(self):
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt or prompt == "Ej: Un gato astronauta en una galaxia colorida":
            messagebox.showwarning("Prompt vacío", "Escribe una descripción para generar la imagen.")
            return

        self.generate_btn.config(state=tk.DISABLED)
        self.ai_progress.start(10)
        self.update_status("Generando con IA...", "🎨")
        thread = threading.Thread(target=self.generate_ai_image, args=(prompt,), daemon=True)
        thread.start()

    def generate_ai_image(self, prompt):
        try:
            generator = pollinations.Image()
            generated_img = generator(prompt)
            self.generated_image = generated_img
            self.update_status("Imagen generada", "🖼️")

            if self.remove_bg_after_gen.get():
                self.update_status("Quitando fondo...", "🧽")
                if generated_img.mode not in ("RGB", "RGBA"):
                    generated_img = generated_img.convert("RGBA")
                output = remove(generated_img)
                formato = self.ai_format_var.get().lower()
                save_path = self.save_image(output, formato, destination="ai")
            else:
                formato = self.ai_format_var.get().lower()
                save_path = self.save_image(generated_img, formato, destination="ai")

            self.update_status("¡Imagen guardada!", "✅")
            self.root.after(0, self.on_ai_success, save_path)

        except Exception as e:
            self.root.after(0, self.on_error, f"Error IA: {e}")

    def on_ai_success(self, save_path):
        self.ai_progress.stop()
        self.generate_btn.config(state=tk.NORMAL)
        self.status_var.set(f"✅ Imagen guardada en JVA-Studio/IA")
        messagebox.showinfo("Éxito", f"Imagen generada y guardada en:\n{save_path}")
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", "Ej: Un gato astronauta en una galaxia colorida")

    # -------------------------------------------------------------------------
    # Guardado en carpetas
    # -------------------------------------------------------------------------
    def get_destination_folder(self, destination):
        pictures = Path.home() / "Pictures"
        if not pictures.exists():
            pictures = Path.home() / "Imágenes"
        studio = pictures / "JVA-Studio"
        folder = studio / ("QuitaFondos" if destination == "remove_bg" else "IA")
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def generate_filename(self, extension):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"jva_{timestamp}.{extension}"

    def save_image(self, image, formato, destination):
        folder = self.get_destination_folder(destination)
        ext = "jpg" if formato == "jpeg" else formato
        ruta = folder / self.generate_filename(ext)

        if formato in ("jpeg", "jpg"):
            if image.mode in ("RGBA", "LA", "P"):
                fondo = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                fondo.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                image = fondo
            image.save(str(ruta), "JPEG", quality=95)
        elif formato == "webp":
            image.save(str(ruta), "WEBP", quality=95)
        else:
            image.save(str(ruta), "PNG")
        return ruta

    def save_animated_gif(self, frames, durations, loop):
        folder = self.get_destination_folder("remove_bg")
        ruta = folder / self.generate_filename("gif")
        frames[0].save(
            str(ruta),
            save_all=True,
            append_images=frames[1:],
            loop=loop,
            duration=durations,
            disposal=2,
            transparency=0,
            optimize=False
        )
        return ruta

    # -------------------------------------------------------------------------
    # Manejo de éxito / error
    # -------------------------------------------------------------------------
    def on_success(self, save_path):
        self.progress.stop()
        self.process_btn.config(state=tk.NORMAL)
        self.status_var.set(f"✅ Guardado en JVA-Studio/QuitaFondos")
        self.url_var.set("")
        self.clear_local_image()
        self.url_entry.focus()
        messagebox.showinfo("Éxito", f"¡Fondo eliminado!\n\n{save_path}")

    def on_error(self, error_msg):
        self.progress.stop()
        self.ai_progress.stop()
        self.process_btn.config(state=tk.NORMAL)
        self.generate_btn.config(state=tk.NORMAL)
        self.status_var.set(f"❌ Error: {error_msg}")
        messagebox.showerror("Error", error_msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = JVAStudioApp(root)
>>>>>>> 3519d64 (Primera versión JVA Studio)
    root.mainloop()