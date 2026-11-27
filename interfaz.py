import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog
import pandas as pd
import os
import json
import sys
import re
import traceback
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import openpyxl
from openpyxl.styles import Font, PatternFill
import threading
from dotenv import load_dotenv
from google import genai

# Importar el motor matemático
from optimizacion import (
    resolver_modelo,
    ZONAS_DEFAULT, UBICACIONES_DEFAULT, DEMANDA_DEFAULT,
    COSTOS_FIJOS_DEFAULT, CAPACIDADES_DEFAULT,
    MAX_CENTROS_DEFAULT, COSTOS_ENVIO_DEFAULT, COSTO_BASELINE_DEFAULT
)

APP_DIR = os.path.dirname(
    sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
)
load_dotenv(os.path.join(APP_DIR, ".env"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = "gemini-3.5-flash-lite"
GEMINI_FALLBACK_MODEL = "gemini-3.8-flash"


def _is_gemini_model_not_found(error):
    for attribute in ("code", "status", "status_code"):
        value = getattr(error, attribute, None)
        if value == 404 or str(value).upper() in {"404", "NOT_FOUND"}:
            return True
    response = getattr(error, "response", None)
    if getattr(response, "status_code", None) == 404:
        return True
    message = str(error).upper()
    return "404" in message and ("NOT_FOUND" in message or "NOT FOUND" in message)
AI_SYSTEM_INSTRUCTION = """
Eres el asistente de MIP Retail Optimizer, una herramienta de apoyo a decisiones
logísticas. Responde en español, con claridad y rigor; distingue los resultados
oficiales del informe de los escenarios dinámicos que el usuario comparta. Usa
solo datos del proyecto y del escenario actual; no inventes cifras ni resultados.

Responde en español claro, directo y conversacional, en máximo 2 o 3 párrafos
cortos. PROHIBIDO usar sintaxis Markdown como asteriscos (**), almohadillas (#)
o bloques de código. No agregues notas de validación ni advertencias genéricas;
cíñete exclusivamente a los datos del proyecto y al escenario actual del usuario.

CONTEXTO COMPLETO DEL INFORME TÉCNICO
Objetivo: minimizar el costo mensual fijo de apertura más el costo variable de
transporte para abastecer toda la demanda de seis zonas urbanas desde cuatro
centros candidatos, sujetos a capacidades y a un máximo estratégico de centros.
La operación empírica de referencia cuesta USD 243,000 al mes (USD 125,000
fijos y USD 118,000 variables). El problema es un CFLP (Capacitated Facility
Location Problem), formulado como Programación Entera Mixta lineal.

Datos oficiales: centros L1, L2, L3 y L4; costos fijos respectivamente
USD 45,000, 50,000, 38,000 y 42,000; capacidades 15,000, 20,000, 12,000 y
16,000 unidades/mes. Zonas Z1–Z6 demandan 3,000, 4,000, 5,000, 3,500, 2,500
y 4,000 unidades/mes (22,000 total). Costos unitarios de envío por zona
(Z1–Z6): L1=[3,5,8,6,10,12], L2=[6,3,4,7,8,9],
L3=[9,7,5,3,4,6], L4=[11,8,6,5,3,4] USD/unidad. La interfaz actual no
permite editar tarifas de envío; indica esto si preguntan por ellas.

Formulación: y_i binaria vale 1 si se abre centro i; x_ij >= 0 es el flujo
desde centro i a zona j. Minimizar sum_i(f_i*y_i)+sum_i,sum_j(c_ij*x_ij),
sujeto a sum_i(x_ij)=d_j para cada zona, sum_j(x_ij)<=K_i*y_i para cada
centro, sum_i(y_i)<=P (P=2 en el caso base), además de los dominios de las
variables. La demanda total supera la mayor capacidad individual, por lo que
se necesitan al menos dos centros. PuLP formula el modelo y CBC lo resuelve
con Branch-and-Bound (relajaciones y ramificación sobre binarias) con garantía
de optimalidad global; el caso tiene 4 variables binarias, 24 continuas,
6 restricciones de demanda, 4 de capacidad y 1 de límite de centros.

Resultado oficial validado: abrir L2 y L3; L1 y L4 quedan cerrados. L2 atiende
Z1–Z3, 12,000/20,000 unidades (60.0%); L3 atiende Z4–Z6,
10,000/12,000 (83.3%). Costo fijo óptimo USD 88,000, transporte USD 94,500,
total USD 182,500; ahorro USD 60,500/mes (24.90%) o USD 726,000/año. El
ahorro frente al baseline reduce USD 37,000 fijos y USD 23,500 variables.
La mejor alternativa siguiente es L2+L4 a USD 183,000, solo USD 500 más.
La comprobación de las seis parejas dio: L2+L3 182,500; L2+L4 183,000;
L1+L4 187,000; L1+L3 190,500; L3+L4 197,500; L1+L2 213,000 USD.

Sensibilidad documentada: con fletes globales +10%, L2+L3 cuesta USD 191,950
y ahorra 21.01%; con +15% y +20% conviene L2+L4 (USD 196,650 y 201,200).
Un aumento de 10% solo en rutas desde L3 cambia a L2+L4. Si el fijo de L3
supera USD 38,500, L4 gana; capacidad L3 de 9,000 también cambia a L2+L4.
Con capacidad L3 de 15,000 se reporta L1+L3 por USD 181,500. La frontera de
decisión L3/L4 es sensible porque la diferencia base es de USD 500. Los
escenarios probados mantuvieron ahorros superiores al 17%; con máximo dos
centros la capacidad combinada máxima es 36,000.

Metodología y alcance: se eligió MIP frente al transporte/PL (no modela el
costo fijo) y a enumerar manualmente (no escala). Se comprobó el resultado
contra las seis parejas. El informe también describe un prototipo previo de
pronóstico lineal con 12 meses simulados (22,206 unidades pronosticadas y
2.75% de error retrospectivo en esa simulación); no son datos reales ni una
función implementada en esta interfaz. No prometas precisión de pronóstico.
Limitaciones/reglas: el modelo solo incluye costos fijos, tarifas y
capacidades definidos; no modela contratos vigentes, costos de cierre/traslado,
estacionalidad ni factores externos. Las decisiones deben revisarse con
criterio gerencial y datos reales, especialmente L3 vs L4.

MANUAL DEL SOFTWARE
El Dashboard muestra escenario, parámetros, KPIs, comparativa de costos y
utilización de capacidad. Los campos inician en modo protegido. Para simular,
habilita edición, cambia costos fijos/capacidades/demandas/máximo de centros/
baseline, guarda los cambios y ejecuta la optimización; Restaurar Base vuelve al caso
oficial. La matriz presenta las asignaciones y permite exportar CSV/Excel.
Los costos de envío permanecen en la matriz oficial y no tienen controles de
edición en la versión actual. La navegación lateral abre Dashboard, Matriz,
Manual, Licencia y este asistente. Este chat envía la pregunta junto con los
valores visibles al momento de enviarla; se conecta a Gemini por internet y
no impide usar el optimizador local si Gemini no está disponible.
"""

# ============================================================
# PALETA DE COLOR LIGHT ENTERPRISE SAAS (Stripe/Linear Style)
# ============================================================
COLORS = {
    # Fondos
    "BG_MAIN": "#EEF2F6",       # Gris azulado para separar las tarjetas blancas
    "BG_CARD": "#FFFFFF",       # Blanco puro - tarjetas
    "BG_SIDEBAR": "#0F172A",    # Azul pizarra profundo - sidebar
    "BG_SIDEBAR_HOVER": "#1E293B",
    "BG_HOVER": "#F1F5F9",
    
    # Textos
    "TEXT_PRIMARY": "#0F172A",   # Azul pizarra - texto principal
    "TEXT_SECONDARY": "#64748B", # Gris pizarra - texto secundario
    "TEXT_MUTED": "#94A3B8",     # Gris claro - placeholders
    "TEXT_WHITE": "#FFFFFF",
    
    # Acciones
    "PRIMARY": "#2563EB",       # Azul corporativo - acción principal
    "PRIMARY_HOVER": "#1D4ED8",
    "SUCCESS": "#059669",       # Verde esmeralda - éxito/ahorro
    "SUCCESS_HOVER": "#047857",
    "WARNING": "#D97706",       # Ámbar - alerta/edición
    "WARNING_HOVER": "#B45309",
    "DANGER": "#DC2626",        # Rojo - peligro/borrar
    
    # Bordes y divisores
    "BORDER": "#CBD5E1",        # Borde marcado para dar relieve a las tarjetas
    "BORDER_FOCUS": "#2563EB",
    
    # Gráficos
    "CHART_BG": "#FFFFFF",
    "CHART_BAR_BASELINE": "#EF4444",
    "CHART_BAR_OPTIMAL": "#059669",
    "CHART_BAR_CAPACITY": "#2563EB",
    "CHART_GRID": "#E2E8F0",
    "CHART_TEXT": "#0F172A",
    "CHART_TEXT_SECONDARY": "#64748B",
}

# Configurar customtkinter para tema claro
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


def _record_exception(exception_type, exception, traceback_object):
    log_directory = os.path.join(
        os.getenv("LOCALAPPDATA") or APP_DIR,
        "MIP_Retail_Optimizer"
    )
    try:
        os.makedirs(log_directory, exist_ok=True)
        with open(
            os.path.join(log_directory, "errores.log"),
            "a",
            encoding="utf-8"
        ) as log_file:
            traceback.print_exception(
                exception_type,
                exception,
                traceback_object,
                file=log_file
            )
    except OSError:
        traceback.print_exception(exception_type, exception, traceback_object)


class MIPRetailOptimizerApp:
    def __init__(self, root):
        self.root = root
        self.root.report_callback_exception = self.report_callback_exception
        self.root.title("MIP Retail Optimizer™ Enterprise")
        self.root.geometry("1400x900")
        self.root.minsize(1366, 768)
        
        # Pantalla completa
        if sys.platform.startswith("win"):
            self.root.state("zoomed")
            self.root.after(0, self.root.state, "zoomed")
        else:
            self.root.attributes('-zoomed', True)
        
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.root.bind('<Escape>', self.end_fullscreen)
        self.root.bind_all("<MouseWheel>", self._scroll_active_view, add="+")
        self._wheel_accum = 0
        
        # Estado
        self.current_view = "dashboard"
        self.active_scroll_frame = None
        self.modo_edicion = False
        self.costo_actual = COSTO_BASELINE_DEFAULT
        self.costo_optimo = None
        self.ultimo_resultado = None
        self.ultimo_parametros = None
        self.entry_vars = {}
        self.execution_step = 0
        self.is_executing = False
        self.chat_busy = False
        self.chat_conversation = []
        self.chat_messages = []
        self.chat_surfaces = []
        self.chat_label_histories: dict[ctk.CTkLabel, ctk.CTkScrollableFrame] = {}
        self.chat_typing_job = None
        self.chat_thinking_job = None
        self.quick_questions_hidden = False
        self.saved_parameters = None
        self.optimization_busy = False
        self.optimization_request_id = 0
        self.solver_thread = None
        self.toast_frame = None
        self.toast_shadow = None
        self.toast_after_id = None
        self.chart_canvases = []
        self.scroll_frames = {}
        self.floating_chat_animation_job = None
        self.floating_chat_open = False
        self.manual_page_index = 0
        self.manual_animation_job = None
        self.manual_animation_token = 0
        
        # Variables Entry
        self.setup_styles()
        self.build_layout()
        self.cargar_valores_iniciales()
        self.saved_parameters = self.leer_parametros_ui()
        self.bloquear_campos()
        self.build_floating_chat()
        self.root.after(0, self.load_csv_data)

    def _create_button(self, master, **kwargs):
        kwargs["height"] = max(38, kwargs.get("height", 38))
        kwargs.setdefault("corner_radius", 10)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLORS["BORDER"])
        button = ctk.CTkButton(master, **kwargs)
        base_border = kwargs["border_color"]
        hover_border = kwargs.get("hover_color", COLORS["BORDER_FOCUS"])
        button.bind(
            "<Enter>",
            lambda _: button.configure(border_color=hover_border),
            add=True
        )
        button.bind(
            "<Leave>",
            lambda _: button.configure(border_color=base_border),
            add=True
        )
        return button

    def report_callback_exception(self, exception_type, exception, traceback_object):
        _record_exception(exception_type, exception, traceback_object)
        self.mostrar_toast(
            "Ocurrió un error inesperado. La aplicación sigue activa; consulta errores.log.",
            "error",
            duration=5000
        )

    def mostrar_toast(self, message, kind="success", duration=2800):
        palette = {
            "success": (COLORS["SUCCESS"], "#FFFFFF"),
            "error": (COLORS["DANGER"], "#FFFFFF"),
            "info": (COLORS["PRIMARY"], "#FFFFFF"),
            "warning": (COLORS["WARNING"], "#FFFFFF"),
        }
        background, foreground = palette.get(kind, palette["info"])
        if self.toast_after_id:
            self.root.after_cancel(self.toast_after_id)
            self.toast_after_id = None
        if self.toast_frame and self.toast_frame.winfo_exists():
            self.toast_frame.destroy()
        if self.toast_shadow and self.toast_shadow.winfo_exists():
            self.toast_shadow.destroy()

        self.toast_frame = ctk.CTkFrame(
            self.root,
            fg_color=background,
            bg_color=COLORS["BG_MAIN"],
            corner_radius=14,
            border_width=1,
            border_color=background
        )
        ctk.CTkLabel(
            self.toast_frame,
            text=message,
            font=self.fonts["body"],
            text_color=foreground,
            justify="left",
            wraplength=420
        ).pack(padx=18, pady=12)
        self.toast_frame.update_idletasks()
        self.toast_shadow = ctk.CTkFrame(
            self.root,
            width=self.toast_frame.winfo_reqwidth(),
            height=self.toast_frame.winfo_reqheight(),
            fg_color=COLORS["BORDER"],
            corner_radius=14
        )
        self.toast_shadow.place(relx=1, rely=1, x=-22, y=-76, anchor="se")
        self.toast_frame.place(relx=1, rely=1, x=-24, y=-78, anchor="se")
        self.toast_frame.lift()
        self.toast_after_id = self.root.after(duration, self._dismiss_toast)

    def _dismiss_toast(self):
        self.toast_after_id = None
        if self.toast_frame and self.toast_frame.winfo_exists():
            self.toast_frame.destroy()
        self.toast_frame = None
        if self.toast_shadow and self.toast_shadow.winfo_exists():
            self.toast_shadow.destroy()
        self.toast_shadow = None

    def confirmar_accion(self, title, message, confirm_text="Confirmar"):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.configure(fg_color=COLORS["BG_MAIN"])
        dialog.update_idletasks()
        width, height = 440, 230
        x = self.root.winfo_rootx() + (self.root.winfo_width() - width) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - height) // 2
        dialog.geometry(f"{width}x{height}+{x}+{y}")

        result = {"confirmed": False}
        card = ctk.CTkFrame(
            dialog,
            fg_color=COLORS["BG_CARD"],
            corner_radius=14,
            border_width=2,
            border_color=COLORS["BORDER"]
        )
        card.pack(fill="both", expand=True, padx=14, pady=14)
        ctk.CTkLabel(
            card,
            text=title,
            font=self.fonts["section"],
            text_color=COLORS["TEXT_PRIMARY"]
        ).pack(anchor="w", padx=22, pady=(20, 8))
        ctk.CTkLabel(
            card,
            text=message,
            font=self.fonts["body"],
            text_color=COLORS["TEXT_SECONDARY"],
            justify="left",
            wraplength=370
        ).pack(anchor="w", padx=22, pady=(0, 14))
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(fill="x", padx=18, pady=(0, 14))
        self._create_button(
            actions,
            text="Cancelar",
            font=self.fonts["button"],
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color=COLORS["TEXT_SECONDARY"],
            command=dialog.destroy
        ).pack(side="right", padx=(8, 0))

        def confirm():
            result["confirmed"] = True
            dialog.destroy()

        self._create_button(
            actions,
            text=confirm_text,
            font=self.fonts["button"],
            fg_color=COLORS["PRIMARY"],
            hover_color=COLORS["PRIMARY_HOVER"],
            command=confirm
        ).pack(side="right")
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.grab_set()
        dialog.focus_force()
        self.root.wait_window(dialog)
        return result["confirmed"]

    def _scroll_active_view(self, event):
        scroll_frame = self.active_scroll_frame or self.scroll_frames.get(self.current_view)
        if scroll_frame is None or not scroll_frame.winfo_exists():
            return

        if self.floating_chat_panel.winfo_manager():
            widget = event.widget
            while widget is not None:
                if widget == self.floating_chat_panel:
                    scroll_frame = self.floating_chat_history
                    break
                widget = getattr(widget, "master", None)

        if not event.delta:
            return

        if sys.platform.startswith("win"):
            self._wheel_accum += event.delta
            if abs(self._wheel_accum) < 40:
                return "break"
            units = -1 if self._wheel_accum > 0 else 1
            self._wheel_accum = 0
        else:
            units = -1 if event.delta > 0 else 1
        scroll_frame._parent_canvas.yview_scroll(units, "units")
        return "break"
        
    def setup_styles(self):
        """Configura estilos globales"""
        # Fuentes
        self.fonts = {
            "logo": ("Bahnschrift", 20, "bold"),
            "title": ("Bahnschrift", 22, "bold"),
            "section": ("Bahnschrift", 16, "bold"),
            "subsection": ("Bahnschrift", 13, "bold"),
            "body": ("Segoe UI", 12),
            "body_small": ("Segoe UI", 11),
            "kpi_label": ("Bahnschrift", 12, "bold"),
            "kpi_value": ("Bahnschrift", 20, "bold"),
            "button": ("Segoe UI", 12, "bold"),
            "button_small": ("Segoe UI", 11),
            "sidebar_nav": ("Segoe UI", 12),
            "chart_title": ("Bahnschrift", 13, "bold"),
            "chart_subtitle": ("Segoe UI", 11),
            "code": ("Consolas", 10),
        }
        
        # Estilo ttk para Treeview
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Enterprise.Treeview",
            background="#FFFFFF",
            foreground="#0F172A",
            fieldbackground="#FFFFFF",
            font=("Segoe UI", 11),
            rowheight=32,
            borderwidth=0
        )
        style.configure(
            "Enterprise.Treeview.Heading",
            background="#F8FAFC",
            foreground="#0F172A",
            font=("Segoe UI", 11, "bold"),
            relief="flat"
        )
        style.map(
            "Enterprise.Treeview",
            background=[("selected", "#DBEAFE")],
            foreground=[("selected", "#1E40AF")]
        )
        style.configure(
            "Enterprise.Vertical.TScrollbar",
            background="#F1F5F9",
            troughcolor="#F8FAFC",
            bordercolor="#E2E8F0",
            arrowcolor="#64748B"
        )
        
    def build_layout(self):
        """Construye el layout principal con Sidebar + Content Area"""
        # Grid principal
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # ========== SIDEBAR IZQUIERDO (220px fijo) ==========
        self.sidebar = ctk.CTkFrame(
            self.root,
            width=220,
            corner_radius=0,
            fg_color=COLORS["BG_SIDEBAR"]
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(5, weight=1)
        
        # Logo en sidebar
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=(24, 16))

        logo_mark = tk.Canvas(
            logo_frame,
            width=38,
            height=38,
            bg=COLORS["BG_SIDEBAR"],
            highlightthickness=0
        )
        logo_mark.pack(side="left", padx=(0, 9))
        logo_mark.create_line(7, 19, 18, 7, fill="#3B82F6", width=2)
        logo_mark.create_line(18, 7, 29, 19, fill="#3B82F6", width=2)
        logo_mark.create_line(29, 19, 18, 31, fill="#3B82F6", width=2)
        logo_mark.create_line(18, 31, 7, 19, fill="#3B82F6", width=2)
        logo_mark.create_line(7, 19, 29, 19, fill="#34D399", width=1.5)
        for x, y, color in (
            (7, 19, "#34D399"),
            (18, 7, "#60A5FA"),
            (29, 19, "#34D399"),
            (18, 31, "#60A5FA"),
            (18, 19, "#FFFFFF"),
        ):
            radius = 4 if (x, y) == (18, 19) else 3
            logo_mark.create_oval(
                x - radius, y - radius, x + radius, y + radius,
                fill=color, outline=COLORS["BG_SIDEBAR"]
            )

        logo_text = ctk.CTkFrame(logo_frame, fg_color="transparent")
        logo_text.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            logo_text,
            text="MIP Retail\nOptimizer™",
            font=("Bahnschrift", 15, "bold"),
            text_color=COLORS["TEXT_WHITE"],
            justify="left"
        ).pack(anchor="w")
        ctk.CTkLabel(
            logo_text,
            text="Enterprise",
            font=("Segoe UI", 10, "bold"),
            text_color=COLORS["SUCCESS"]
        ).pack(anchor="w")
        
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["BG_SIDEBAR_HOVER"]).pack(fill="x", padx=16, pady=8)
        
        # Navegación
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊  Dashboard y Simulación"),
            ("matrix", "📋  Matriz de Rutas y Reportes"),
            ("manual", "📖  Manual de Uso y Modelo"),
            ("assistant", "🤖 Asistente IA (Gemini)"),
            ("license", "💼  Licencia y ROI Comercial"),
        ]
        
        for view_id, label in nav_items:
            btn = self._create_button(
                self.sidebar,
                text=label,
                font=self.fonts["sidebar_nav"],
                height=44,
                corner_radius=10,
                fg_color="transparent",
                text_color=COLORS["TEXT_WHITE"],
                hover_color=COLORS["BG_SIDEBAR_HOVER"],
                anchor="w",
                command=lambda v=view_id: self.switch_view(v)
            )
            btn.configure(border_color=COLORS["BG_SIDEBAR"])
            btn.pack(fill="x", padx=12, pady=4)
            self.nav_buttons[view_id] = btn
        
        # Version info al final
        ctk.CTkLabel(
            self.sidebar,
            text="v1.0.0 Enterprise",
            font=("Segoe UI", 10),
            text_color=COLORS["TEXT_MUTED"]
        ).pack(side="bottom", pady=20)
        
        # ========== ÁREA DE CONTENIDO PRINCIPAL ==========
        self.content_area = ctk.CTkFrame(
            self.root,
            corner_radius=0,
            fg_color=COLORS["BG_MAIN"]
        )
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)
        
        # Frames por vista (solo uno visible a la vez)
        self.views = {}
        for view_id, _ in nav_items:
            frame = ctk.CTkFrame(self.content_area, fg_color=COLORS["BG_MAIN"], corner_radius=0)
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)
            self.views[view_id] = frame
        
        # Construir cada vista
        self.build_dashboard_view()
        self.build_matrix_view()
        self.build_manual_view()
        self.build_assistant_view()
        self.build_license_view()
        
        # Mostrar vista inicial
        self.switch_view("dashboard")
        
    def switch_view(self, view_id):
        """Cambia la vista activa"""
        self.current_view = view_id
        self.active_scroll_frame = self.scroll_frames.get(view_id)
        for vid, frame in self.views.items():
            if vid == view_id:
                frame.tkraise()
            else:
                frame.lower()
        
        # Actualizar botones de navegación
        for vid, btn in self.nav_buttons.items():
            if vid == view_id:
                btn.configure(fg_color=COLORS["BG_SIDEBAR_HOVER"], text_color=COLORS["TEXT_WHITE"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["TEXT_WHITE"])
        if hasattr(self, "floating_chat_button"):
            self._sync_floating_chat_visibility()

    def build_floating_chat(self):
        self.floating_chat_panel = ctk.CTkFrame(
            self.root,
            width=460,
            fg_color="#EEF2F6",
            bg_color="#EEF2F6",
            corner_radius=16,
            border_width=2,
            border_color=COLORS["BORDER"]
        )
        self.floating_chat_panel.pack_propagate(False)

        header = ctk.CTkFrame(
            self.floating_chat_panel,
            fg_color=COLORS["BG_SIDEBAR"],
            corner_radius=10
        )
        header.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(
            header,
            text="💬 Asistente Rápido",
            font=self.fonts["subsection"],
            text_color=COLORS["TEXT_WHITE"]
        ).pack(side="left", padx=12, pady=10)
        self._create_button(
            header,
            text="×",
            width=34,
            height=34,
            font=self.fonts["section"],
            fg_color="transparent",
            hover_color=COLORS["BG_SIDEBAR_HOVER"],
            text_color=COLORS["TEXT_WHITE"],
            command=self._toggle_floating_chat
        ).pack(side="right", padx=6, pady=4)

        self.floating_chat_history = ctk.CTkScrollableFrame(
            self.floating_chat_panel,
            fg_color="#F8FAFC",
            corner_radius=8
        )
        self.floating_chat_history.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self.floating_chat_history.grid_columnconfigure(0, weight=1)
        input_frame = ctk.CTkFrame(self.floating_chat_panel, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=(0, 10))
        input_frame.grid_columnconfigure(0, weight=1)
        self.floating_chat_input = ctk.CTkEntry(
            input_frame,
            height=40,
            font=self.fonts["body_small"],
            placeholder_text="Pregunta sobre este escenario..."
        )
        self.floating_chat_input.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.floating_chat_send_button = self._create_button(
            input_frame,
            text="Enviar",
            width=74,
            height=40,
            font=self.fonts["button_small"],
            command=lambda: self.enviar_mensaje_asistente(source="floating")
        )
        self.floating_chat_send_button.grid(row=0, column=1)
        self.floating_chat_input.bind(
            "<Return>",
            lambda _: self.enviar_mensaje_asistente(source="floating")
        )
        self._register_chat_surface(
            self.floating_chat_history,
            self.floating_chat_send_button,
            wrap_limit=350
        )

        self.floating_chat_button_container = ctk.CTkFrame(
            self.root,
            width=202,
            height=50,
            fg_color="transparent",
            bg_color=COLORS["BG_MAIN"]
        )
        self.floating_chat_button_container.grid_propagate(False)
        self.floating_chat_button_container.grid_columnconfigure(0, weight=1)
        self.floating_chat_button_container.grid_rowconfigure(0, weight=1)
        ctk.CTkFrame(
            self.floating_chat_button_container,
            fg_color="#1D4ED8",
            corner_radius=10
        ).place(relx=0, rely=0, relwidth=1, relheight=1)
        self.floating_chat_button = self._create_button(
            self.floating_chat_button_container,
            text="💬 Asistente Rápido",
            font=self.fonts["button"],
            height=48,
            fg_color=COLORS["PRIMARY"],
            hover_color=COLORS["PRIMARY_HOVER"],
            border_width=0,
            command=self._toggle_floating_chat
        )
        self.floating_chat_button.grid(
            row=0,
            column=0,
            sticky="nsew",
            pady=(0, 2)
        )
        self.floating_chat_open = False
        self._sync_floating_chat_visibility()

    def _sync_floating_chat_visibility(self):
        if self.current_view in {"dashboard", "matrix", "manual"}:
            if not self.floating_chat_button_container.winfo_manager():
                self.floating_chat_button_container.place(
                    relx=1, rely=1, x=-24, y=-18, anchor="se"
                )
        else:
            self.floating_chat_button_container.place_forget()
            self.floating_chat_panel.place_forget()
            self.floating_chat_open = False
            if self.floating_chat_animation_job:
                self.root.after_cancel(self.floating_chat_animation_job)
                self.floating_chat_animation_job = None

    def _toggle_floating_chat(self):
        if self.floating_chat_animation_job:
            self.root.after_cancel(self.floating_chat_animation_job)
            self.floating_chat_animation_job = None

        opening = not self.floating_chat_open
        self.floating_chat_open = opening
        if opening:
            self.floating_chat_panel.place(
                relx=1,
                rely=0.1,
                x=-500,
                relheight=0.8,
                anchor="ne"
            )
            self.floating_chat_panel.lift()
            self.floating_chat_input.focus_set()
        self._animate_floating_chat(opening, 0)

    def _animate_floating_chat(self, opening, step):
        steps = 10
        start_x, end_x = (-500, -16) if opening else (-16, -500)
        x = round(start_x + (end_x - start_x) * step / steps)
        self.floating_chat_panel.place(
            relx=1,
            rely=0.1,
            x=x,
            relheight=0.8,
            anchor="ne"
        )
        if step >= steps:
            self.floating_chat_animation_job = None
            if not opening:
                self.floating_chat_panel.place_forget()
            return
        self.floating_chat_animation_job = self.root.after(
            16,
            lambda: self._animate_floating_chat(opening, step + 1)
        )
        
    # ========================================================
    # VISTA 1: DASHBOARD Y SIMULACIÓN
    # ========================================================
    def build_dashboard_view(self):
        frame = self.views["dashboard"]
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Scroll principal
        main_scroll = ctk.CTkScrollableFrame(
            frame,
            fg_color=COLORS["BG_MAIN"],
            corner_radius=0
        )
        self.scroll_frames["dashboard"] = main_scroll
        main_scroll.grid(row=0, column=0, sticky="nsew", padx=24, pady=12)
        main_scroll.grid_columnconfigure(0, weight=1)
        
        # ===== HEADER DE LA VISTA =====
        header = ctk.CTkFrame(main_scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 24))
        
        ctk.CTkLabel(
            header,
            text="Dashboard y Simulación",
            font=self.fonts["title"],
            text_color=COLORS["TEXT_PRIMARY"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header,
            text="Configura, ejecuta y analiza la optimización de tu red de distribución",
            font=self.fonts["body"],
            text_color=COLORS["TEXT_SECONDARY"]
        ).pack(anchor="w", pady=(4, 0))

        self._create_button(
            header,
            text="🤖 Consultar al Asistente IA",
            font=self.fonts["button"],
            height=40,
            fg_color=COLORS["PRIMARY"],
            hover_color=COLORS["PRIMARY_HOVER"],
            command=lambda: self.switch_view("assistant")
        ).pack(side="right", padx=4)
        
        # ===== TARJETA: ESCENARIO ACTUAL =====
        scenario_shadow = ctk.CTkFrame(
            main_scroll,
            fg_color=COLORS["BORDER"],
            corner_radius=12
        )
        scenario_shadow.pack(fill="x", pady=(0, 12))
        scenario_card = ctk.CTkFrame(
            scenario_shadow,
            fg_color=COLORS["BG_CARD"],
            bg_color=COLORS["BORDER"],
            corner_radius=12,
            border_width=2,
            border_color=COLORS["BORDER"]
        )
        scenario_card.pack(fill="x", pady=(0, 2))
        scenario_card.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            scenario_card,
            text="📋  Escenario Actual",
            font=self.fonts["section"],
            text_color=COLORS["TEXT_PRIMARY"]
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=24, pady=(20, 12))
        
        # KPIs del escenario
        scenario_kpis = [
            ("Centros Candidatos", "4 (L1–L4)", COLORS["TEXT_SECONDARY"]),
            ("Zonas de Demanda", "6 (Z1–Z6)", COLORS["TEXT_SECONDARY"]),
            ("Demanda Total", "22,000 unidades/mes", COLORS["TEXT_PRIMARY"]),
            ("Máx. CDs a Abrir", "2", COLORS["WARNING"]),
            ("Costo Baseline", "$243,000 USD/mes", COLORS["DANGER"]),
        ]
        
        for i, (label, value, color) in enumerate(scenario_kpis):
            ctk.CTkLabel(
                scenario_card,
                text=label,
                font=self.fonts["body_small"],
                text_color=COLORS["TEXT_MUTED"]
            ).grid(row=1, column=i, sticky="w", padx=(24, 8), pady=(0, 4))
            ctk.CTkLabel(
                scenario_card,
                text=value,
                font=("Segoe UI", 13, "bold"),
                text_color=color
            ).grid(row=2, column=i, sticky="w", padx=(24, 8), pady=(0, 20))
        
        # ===== PARÁMETROS DE ENTRADA =====
        params_shadow = ctk.CTkFrame(
            main_scroll,
            fg_color=COLORS["BORDER"],
            corner_radius=12
        )
        params_shadow.pack(fill="x", pady=(0, 12))
        params_card = ctk.CTkFrame(
            params_shadow,
            fg_color=COLORS["BG_CARD"],
            bg_color=COLORS["BORDER"],
            corner_radius=12,
            border_width=2,
            border_color=COLORS["BORDER"]
        )
        params_card.pack(fill="x", pady=(0, 2))
        
        # Header con título + barra de herramientas
        params_header = ctk.CTkFrame(params_card, fg_color="transparent")
        params_header.pack(fill="x", padx=24, pady=(8, 6))
        params_header.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            params_header,
            text="⚙️  Parámetros de Entrada",
            font=self.fonts["section"],
            text_color=COLORS["TEXT_PRIMARY"]
        ).grid(row=0, column=0, sticky="w")
        
        # Toolbar
        toolbar = ctk.CTkFrame(params_header, fg_color="transparent")
        toolbar.grid(row=0, column=1, sticky="e")
        
        self.btn_edit = self._create_button(
            toolbar,
            text="🔓  Editar Parámetros",
            font=self.fonts["button"],
            height=40,
            width=170,
            fg_color=COLORS["WARNING"],
            hover_color=COLORS["WARNING_HOVER"],
            command=self.habilitar_edicion
        )
        self.btn_edit.pack(side="left", padx=4)

        self.btn_save = self._create_button(
            toolbar,
            text="💾 Guardar Cambios",
            font=self.fonts["button"],
            height=40,
            width=165,
            fg_color=COLORS["SUCCESS"],
            hover_color=COLORS["SUCCESS_HOVER"],
            command=self.guardar_cambios
        )
        self.btn_cancel_edit = self._create_button(
            toolbar,
            text="✖ Cancelar Edición",
            font=self.fonts["button"],
            height=40,
            width=150,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color=COLORS["TEXT_SECONDARY"],
            command=self.cancelar_edicion
        )
        
        self.btn_restore = self._create_button(
            toolbar,
            text="↩ Restaurar Base",
            font=self.fonts["button"],
            height=40,
            width=160,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color=COLORS["TEXT_SECONDARY"],
            command=self.restaurar_valores_base
        )
        self.btn_restore.pack(side="left", padx=4)
        
        self.btn_import = self._create_button(
            toolbar,
            text="📂  Cargar CSV/Excel",
            font=self.fonts["button"],
            height=40,
            width=170,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color=COLORS["TEXT_SECONDARY"],
            command=self.importar_escenario
        )
        self.btn_import.pack(side="left", padx=4)
        
        # Estado del modo
        self.mode_indicator = ctk.CTkLabel(
            toolbar,
            text="🔒  Modo Protegido",
            font=("Segoe UI", 11, "bold"),
            text_color="#DC2626"
        )
        self.mode_indicator.pack(side="left", padx=16)
        
        # Notebook con pestañas de parámetros
        self.params_notebook = ctk.CTkTabview(
            params_card,
            fg_color=COLORS["BG_MAIN"],
            segmented_button_fg_color="#FFFFFF",
            segmented_button_selected_color=COLORS["PRIMARY"],
            segmented_button_selected_hover_color=COLORS["PRIMARY_HOVER"],
            segmented_button_unselected_color="#F1F5F9",
            segmented_button_unselected_hover_color="#E2E8F0",
            text_color=COLORS["TEXT_PRIMARY"],
            corner_radius=8
        )
        self.params_notebook.pack(fill="x", padx=24, pady=(0, 8))
        
        # ---- Pestaña: Centros de Distribución ----
        self.tab_cds = self.params_notebook.add("🏢 Centros de Distribución")
        self.tab_cds.grid_columnconfigure(1, weight=1)
        self.tab_cds.grid_columnconfigure(2, weight=1)
        
        headers_cds = ["Centro", "Costo Fijo (USD/mes)", "Capacidad (u/mes)"]
        for col, h in enumerate(headers_cds):
            ctk.CTkLabel(
                self.tab_cds, text=h,
                font=("Segoe UI", 12, "bold"),
                text_color=COLORS["TEXT_SECONDARY"]
            ).grid(row=0, column=col, padx=20, pady=6, sticky="ew")
        
        for i, ubicacion in enumerate(UBICACIONES_DEFAULT):
            row = i + 1
            ctk.CTkLabel(
                self.tab_cds,
                text=f"  {ubicacion}",
                font=("Segoe UI", 12, "bold"),
                text_color=COLORS["TEXT_PRIMARY"],
                anchor="w"
            ).grid(row=row, column=0, padx=20, pady=10, sticky="w")
            
            entry_costo = ctk.CTkEntry(
                self.tab_cds, width=200, height=38,
                font=("Segoe UI", 12),
                fg_color="#FFFFFF", border_color=COLORS["BORDER"],
                text_color=COLORS["TEXT_PRIMARY"]
            )
            entry_costo.grid(row=row, column=1, padx=20, pady=2, sticky="ew")
            self.entry_vars[f'costo_fijo_{i}'] = entry_costo
            
            entry_cap = ctk.CTkEntry(
                self.tab_cds, width=200, height=38,
                font=("Segoe UI", 12),
                fg_color="#FFFFFF", border_color=COLORS["BORDER"],
                text_color=COLORS["TEXT_PRIMARY"]
            )
            entry_cap.grid(row=row, column=2, padx=20, pady=2, sticky="ew")
            self.entry_vars[f'capacidad_{i}'] = entry_cap
        
        # ---- Pestaña: Demandas por Zona ----
        self.tab_demandas = self.params_notebook.add("📍 Demandas por Zona")
        self.tab_demandas.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            self.tab_demandas, text="Zona",
            font=("Segoe UI", 12, "bold"), text_color=COLORS["TEXT_SECONDARY"]
        ).grid(row=0, column=0, padx=20, pady=6, sticky="w")
        ctk.CTkLabel(
            self.tab_demandas, text="Demanda (u/mes)",
            font=("Segoe UI", 12, "bold"), text_color=COLORS["TEXT_SECONDARY"]
        ).grid(row=0, column=1, padx=20, pady=6, sticky="ew")
        
        for j, zona in enumerate(ZONAS_DEFAULT):
            row = j + 1
            ctk.CTkLabel(
                self.tab_demandas, text=f"  {zona}",
                font=("Segoe UI", 12), text_color=COLORS["TEXT_PRIMARY"], anchor="w"
            ).grid(row=row, column=0, padx=20, pady=2, sticky="w")
            
            entry_dem = ctk.CTkEntry(
                self.tab_demandas, width=250, height=38,
                font=("Segoe UI", 12),
                fg_color="#FFFFFF", border_color=COLORS["BORDER"],
                text_color=COLORS["TEXT_PRIMARY"]
            )
            entry_dem.grid(row=row, column=1, padx=20, pady=2, sticky="ew")
            self.entry_vars[f'demanda_{j}'] = entry_dem
        
        # ---- Pestaña: Reglas y Baseline ----
        self.tab_config = self.params_notebook.add("📏 Reglas y Baseline")
        self.tab_config.grid_columnconfigure(1, weight=1)
        
        config_items = [
            ("max_centros", "Máximo de CDs a abrir:", str(MAX_CENTROS_DEFAULT)),
            ("baseline", "Costo Baseline (USD/mes):", f"{COSTO_BASELINE_DEFAULT:,}"),
        ]
        
        for idx, (key, label, default) in enumerate(config_items):
            ctk.CTkLabel(
                self.tab_config, text=label,
                font=("Segoe UI", 12), text_color=COLORS["TEXT_PRIMARY"]
            ).grid(row=idx, column=0, padx=24, pady=8, sticky="w")
            
            entry = ctk.CTkEntry(
                self.tab_config, width=250, height=40,
                font=("Segoe UI", 12),
                fg_color="#FFFFFF", border_color=COLORS["BORDER"],
                text_color=COLORS["TEXT_PRIMARY"]
            )
            entry.grid(row=idx, column=1, padx=24, pady=8, sticky="ew")
            entry.insert(0, default)
            self.entry_vars[key] = entry
            
            if key == "max_centros":
                ctk.CTkLabel(
                    self.tab_config, text="(1-4)",
                    font=("Segoe UI", 10), text_color=COLORS["TEXT_MUTED"]
                ).grid(row=idx, column=2, padx=10, sticky="w")
        
        # ===== BOTÓN PRINCIPAL DE EJECUCIÓN =====
        exec_card = ctk.CTkFrame(main_scroll, fg_color="transparent")
        exec_card.pack(fill="x", pady=(0, 16))
        exec_card.grid_columnconfigure(0, weight=1)
        execute_shadow = ctk.CTkFrame(
            exec_card,
            fg_color="#1D4ED8",
            corner_radius=10,
            height=50
        )
        execute_shadow.grid(row=0, column=0, sticky="ew", padx=4, pady=(2, 0))
        execute_shadow.grid_propagate(False)
        
        self.btn_execute = self._create_button(
            exec_card,
            text="▶  Ejecutar Optimización Matemática",
            font=("Bahnschrift", 15, "bold"),
            height=48,
            fg_color=COLORS["PRIMARY"],
            hover_color=COLORS["PRIMARY_HOVER"],
            command=self.iniciar_ejecucion_progresiva
        )
        self.btn_execute.grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 2))
        
        # ===== ÁREA DE EJECUCIÓN PROGRESIVA =====
        self.execution_card = ctk.CTkFrame(
            main_scroll,
            fg_color=COLORS["BG_CARD"],
            corner_radius=12,
            border_width=2,
            border_color=COLORS["BORDER"]
        )
        self.execution_card.pack(fill="x", pady=(0, 16))
        self.execution_card.grid_columnconfigure(0, weight=1)
        
        exec_header = ctk.CTkFrame(self.execution_card, fg_color="transparent")
        exec_header.pack(fill="x", padx=24, pady=(20, 8))
        
        ctk.CTkLabel(
            exec_header,
            text="🔄  Ejecución Progresiva",
            font=self.fonts["section"],
            text_color=COLORS["TEXT_PRIMARY"]
        ).pack(side="left")
        
        self.execution_status = ctk.CTkLabel(
            exec_header,
            text="● Listo para ejecutar",
            font=("Segoe UI", 11),
            text_color=COLORS["TEXT_MUTED"]
        )
        self.execution_status.pack(side="right", padx=24)
        
        self.progress_bar = ctk.CTkProgressBar(
            self.execution_card, height=8, corner_radius=4,
            fg_color="#E2E8F0", progress_color=COLORS["PRIMARY"]
        )
        self.progress_bar.pack(fill="x", padx=24, pady=(0, 8))
        self.progress_bar.set(0)
        
        # Log de ejecución
        self.execution_log = ctk.CTkTextbox(
            self.execution_card,
            height=85,
            font=("Consolas", 10),
            fg_color="#0F172A",
            text_color="#E2E8F0",
            corner_radius=8,
            border_width=0,
            wrap="word"
        )
        self.execution_log.pack(fill="x", padx=24, pady=(0, 20))
        self.execution_log.insert("0.0", "Configura o verifica los parámetros y presiona 'Ejecutar Optimización Matemática' para calcular la red óptima.")
        self.execution_log.configure(state="disabled")
        self.execution_card.pack_forget()
        
        # ===== KPIs EJECUTIVOS (inicialmente ocultos) =====
        self.kpi_card = ctk.CTkFrame(main_scroll, fg_color="transparent")
        self.kpi_card.pack(fill="x", pady=(0, 16))
        self.kpi_card.grid_columnconfigure((0,1,2,3), weight=1)
        
        self.kpi_widgets = {}
        kpi_defs = [
            ("💰 Costo Total Óptimo", "$—", COLORS["TEXT_PRIMARY"]),
            ("💵 Ahorro Mensual", "$— / —%", COLORS["SUCCESS"]),
            ("🏢 Centros Activos", "—", COLORS["WARNING"]),
            ("✅ Demanda Cubierta", "—", COLORS["SUCCESS"]),
        ]
        
        for i, (label, value, color) in enumerate(kpi_defs):
            card = ctk.CTkFrame(
                self.kpi_card,
                fg_color=COLORS["BG_CARD"],
                corner_radius=12,
                border_width=2,
                border_color=COLORS["BORDER"]
            )
            card.grid(row=0, column=i, sticky="ew", padx=4)
            card.grid_columnconfigure(0, weight=1)
            
            ctk.CTkLabel(
                card, text=label,
                font=self.fonts["kpi_label"],
                text_color=COLORS["TEXT_SECONDARY"]
            ).pack(anchor="w", padx=20, pady=(16, 4))
            
            val_label = ctk.CTkLabel(
                card, text=value,
                font=self.fonts["kpi_value"],
                text_color=color
            )
            val_label.pack(anchor="w", padx=20, pady=(0, 16))
            self.kpi_widgets[label] = val_label
        
        # Inicialmente ocultar KPIs
        self.kpi_card.pack_forget()
        
        # ===== GRÁFICOS =====
        self.charts_card = ctk.CTkFrame(main_scroll, fg_color="transparent")
        self.charts_card.pack(fill="x", pady=(0, 0))
        self.charts_card.grid_columnconfigure(0, weight=1)
        self.charts_card.grid_columnconfigure(1, weight=1)
        self.charts_card.grid_rowconfigure(0, weight=1, minsize=280)
        
        # Gráfico 1
        self.chart1_frame = ctk.CTkFrame(
            self.charts_card,
            fg_color=COLORS["BG_CARD"],
            corner_radius=12,
            border_width=2,
            border_color=COLORS["BORDER"]
        )
        self.chart1_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.chart1_frame.grid_rowconfigure(1, weight=1, minsize=240)
        self.chart1_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            self.chart1_frame,
            text="📊  Comparativa: Costo Baseline vs. Optimizado",
            font=self.fonts["chart_title"],
            text_color=COLORS["TEXT_PRIMARY"]
        ).grid(row=0, column=0, padx=20, pady=(16, 8), sticky="w")
        
        self.chart1_canvas_frame = ctk.CTkFrame(self.chart1_frame, fg_color="transparent")
        self.chart1_canvas_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.chart1_canvas_frame.grid_rowconfigure(0, weight=1, minsize=220)
        self.chart1_canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Gráfico 2
        self.chart2_frame = ctk.CTkFrame(
            self.charts_card,
            fg_color=COLORS["BG_CARD"],
            corner_radius=12,
            border_width=2,
            border_color=COLORS["BORDER"]
        )
        self.chart2_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.chart2_frame.grid_rowconfigure(1, weight=1, minsize=240)
        self.chart2_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            self.chart2_frame,
            text="📈  Utilización de Capacidad por Centro",
            font=self.fonts["chart_title"],
            text_color=COLORS["TEXT_PRIMARY"]
        ).grid(row=0, column=0, padx=20, pady=(16, 8), sticky="w")
        
        self.chart2_canvas_frame = ctk.CTkFrame(self.chart2_frame, fg_color="transparent")
        self.chart2_canvas_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.chart2_canvas_frame.grid_rowconfigure(0, weight=1, minsize=220)
        self.chart2_canvas_frame.grid_columnconfigure(0, weight=1)
        
    # ========================================================
    # VISTA 2: MATRIZ DE RUTAS Y REPORTES
    # ========================================================
    def build_matrix_view(self):
        frame = self.views["matrix"]
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=24)
        header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header, text="📋 Matriz de Rutas y Reportes",
                    font=self.fonts["title"], text_color=COLORS["TEXT_PRIMARY"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="Tabla completa de asignaciones óptimas con filtros y exportación",
                    font=self.fonts["body"], text_color=COLORS["TEXT_SECONDARY"]).grid(row=1, column=0, sticky="w", pady=(4,0))
        
        # Toolbar
        toolbar = ctk.CTkFrame(header, fg_color="transparent")
        toolbar.grid(row=0, column=1, rowspan=2, sticky="e")
        
        self._create_button(toolbar, text="📊 Exportar a Excel",
                     font=self.fonts["button"], height=40, width=160,
                     fg_color=COLORS["PRIMARY"], hover_color=COLORS["PRIMARY_HOVER"],
                     command=self.exportar_excel_matriz).pack(side="left", padx=4)
        self._create_button(toolbar, text="📄 Exportar CSV",
                     font=self.fonts["button"], height=40, width=130,
                     fg_color="#F1F5F9", hover_color="#E2E8F0", text_color=COLORS["TEXT_SECONDARY"],
                     command=self.exportar_csv_matriz).pack(side="left", padx=4)
        
        # Tabla principal
        table_card = ctk.CTkFrame(frame, fg_color=COLORS["BG_CARD"], corner_radius=12,
                                  border_width=2, border_color=COLORS["BORDER"])
        table_card.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))
        table_card.grid_rowconfigure(0, weight=1)
        table_card.grid_columnconfigure(0, weight=1)
        
        # Treeview con columnas extendidas
        columns = ("Centro", "Zona", "Unidades", "Costo_Unit", "Costo_Ruta", "Pct_Demanda")
        self.tree_matrix = ttk.Treeview(
            table_card,
            columns=columns,
            show="headings",
            style="Enterprise.Treeview",
            height=12
        )
        
        headings = ["Centro Origen", "Zona Destino", "Unidades Asignadas",
                    "Costo Unitario (USD)", "Costo Total Ruta (USD)", "% Demanda Zona"]
        widths = [180, 180, 160, 200, 200, 160]
        
        for col, (h, w) in enumerate(zip(headings, widths)):
            self.tree_matrix.heading(col, text=h, anchor="center")
            self.tree_matrix.column(col, width=w, anchor="center", minwidth=120)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(table_card, orient="vertical", command=self.tree_matrix.yview,
                                style="Enterprise.Vertical.TScrollbar")
        h_scroll = ttk.Scrollbar(table_card, orient="horizontal", command=self.tree_matrix.xview)
        self.tree_matrix.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.tree_matrix.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        v_scroll.grid(row=0, column=1, sticky="ns", pady=8)
        h_scroll.grid(row=1, column=0, sticky="ew", padx=8)
        
        table_card.grid_rowconfigure(0, weight=1)
        table_card.grid_columnconfigure(0, weight=1)
        
        # Fila de totales
        self.total_label = ctk.CTkLabel(
            frame,
            text="TOTAL GENERAL: 22,000 unidades | $94,500 USD costo variable",
            font=("Segoe UI", 13, "bold"),
            text_color=COLORS["SUCCESS"]
        )
        self.total_label.grid(row=2, column=0, sticky="w", padx=24, pady=(0, 24))
        
    # ========================================================
    # VISTA 3: MANUAL DE USO Y MODELO
    # ========================================================
    def build_manual_view(self):
        frame = self.views["manual"]
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(frame, fg_color=COLORS["BG_MAIN"], corner_radius=0)
        self.scroll_frames["manual"] = scroll
        scroll.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        scroll.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            scroll,
            text="Manual de Uso y Modelo",
            font=self.fonts["title"],
            text_color=COLORS["TEXT_PRIMARY"]
        ).pack(anchor="w", padx=4, pady=(0, 6))
        ctk.CTkLabel(
            scroll,
            text="Libro interactivo · cinco capítulos para entender y operar el optimizador.",
            font=self.fonts["body"],
            text_color=COLORS["TEXT_SECONDARY"]
        ).pack(anchor="w", padx=4, pady=(0, 16))

        self.manual_chapters = [
            {
                "title": "Portada y Propósito del Sistema (CFLP)",
                "subtitle": "Optimizar la red logística equilibrando aperturas y transporte.",
                "left_heading": "Propósito del sistema",
                "left_text": (
                    "MIP Retail Optimizer ayuda a decidir qué centros abrir y cómo "
                    "abastecer seis zonas urbanas al menor costo mensual. El problema "
                    "es un CFLP: localización de instalaciones con capacidad limitada."
                ),
                "right_heading": "Resultado de referencia",
                "right_text": (
                    "El caso oficial reduce el costo de USD 243,000 a USD 182,500 "
                    "al mes. La red óptima ahorra USD 60,500, equivalente al 24.90%, "
                    "y opera con los centros L2 y L3."
                ),
            },
            {
                "title": "Anatomía de Centros y Demandas (L1–L4 y Z1–Z6)",
                "subtitle": "Cuatro ubicaciones candidatas abastecen seis zonas de demanda.",
                "left_heading": "Centros candidatos",
                "left_text": (
                    "L1: costo fijo USD 45,000 y capacidad 15,000 unidades. "
                    "L2: USD 50,000 y capacidad 20,000. L3: USD 38,000 y capacidad "
                    "12,000. L4: USD 42,000 y capacidad 16,000 unidades al mes."
                ),
                "right_heading": "Demanda de las zonas",
                "right_text": (
                    "Z1–Z6 requieren 3,000, 4,000, 5,000, 3,500, 2,500 y 4,000 "
                    "unidades mensuales, respectivamente: 22,000 en total. Las tarifas "
                    "de transporte permanecen fijas en esta versión."
                ),
            },
            {
                "title": "El Motor Matemático MIP y Branch-and-Bound",
                "subtitle": "Variables binarias deciden aperturas; flujos continuos asignan rutas.",
                "left_heading": "Formulación MIP",
                "left_text": (
                    "La variable binaria y_i indica si abre el centro i; x_ij representa "
                    "el flujo de i a la zona j. Se minimizan costos fijos más transporte, "
                    "cubriendo exactamente cada demanda y respetando capacidades y el "
                    "máximo de centros abiertos."
                ),
                "right_heading": "Resolución",
                "right_text": (
                    "PuLP construye el modelo y CBC ejecuta Branch-and-Bound. El algoritmo "
                    "relaja el modelo, ramifica sobre decisiones enteras y compara cotas "
                    "hasta certificar una solución óptima global."
                ),
            },
            {
                "title": "Guía Paso a Paso de Simulación en Vivo",
                "subtitle": "Edita parámetros, guarda explícitamente y ejecuta el escenario.",
                "left_heading": "Configurar y calcular",
                "left_text": (
                    "En Dashboard, elige Editar Parámetros. Cambia costos fijos, "
                    "capacidades, demandas, límite de centros o baseline; pulsa Guardar "
                    "Cambios para validar. Después selecciona Ejecutar Optimización "
                    "Matemática para resolver en segundo plano."
                ),
                "right_heading": "Revisar y exportar",
                "right_text": (
                    "Analiza KPIs, gráficas y asignaciones en Matriz de Rutas. Usa "
                    "Exportar para guardar CSV o Excel. Restaurar Base recupera los "
                    "valores oficiales; Cancelar Edición descarta modificaciones sin "
                    "recalcular el modelo."
                ),
            },
            {
                "title": "Interpretación de KPIs y Toma de Decisiones",
                "subtitle": "Interpreta el resultado junto con la sensibilidad y el contexto operativo.",
                "left_heading": "Indicadores del caso base",
                "left_text": (
                    "L2 atiende 12,000 de 20,000 unidades: 60%. L3 atiende 10,000 "
                    "de 12,000: 83.3%. El costo óptimo suma USD 88,000 fijos y "
                    "USD 94,500 de transporte."
                ),
                "right_heading": "Criterio gerencial",
                "right_text": (
                    "L2+L4 cuesta solo USD 500 más, por lo que la decisión es sensible "
                    "a costos, tarifas y capacidad. Revisa datos reales y restricciones "
                    "no modeladas —como contratos, traslados o estacionalidad— antes de "
                    "aplicar cambios operativos."
                ),
            },
        ]

        book = ctk.CTkFrame(
            scroll,
            fg_color=COLORS["BG_CARD"],
            corner_radius=16,
            border_width=2,
            border_color=COLORS["BORDER"]
        )
        book.pack(fill="both", expand=True, padx=4, pady=(0, 16))
        book.grid_columnconfigure(0, weight=1)

        self.manual_marker = ctk.CTkLabel(
            book,
            text="CAPÍTULO 1 / 5",
            font=self.fonts["button_small"],
            text_color=COLORS["PRIMARY"],
            fg_color="#DBEAFE",
            corner_radius=10
        )
        self.manual_marker.pack(anchor="e", padx=18, pady=(16, 8))

        self.manual_pages = ctk.CTkFrame(book, fg_color="transparent", height=430)
        self.manual_pages.pack(fill="both", expand=True, padx=10)
        self.manual_pages.grid_propagate(False)
        self.manual_pages.grid_columnconfigure((0, 2), weight=1, uniform="manual_page")
        self.manual_pages.grid_columnconfigure(1, minsize=4)
        self.manual_pages.grid_rowconfigure(0, weight=1)

        self.manual_left_shadow = ctk.CTkFrame(
            self.manual_pages,
            fg_color=COLORS["BORDER"],
            corner_radius=12
        )
        self.manual_left_shadow.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 2),
            pady=(10, 6)
        )
        self.manual_left_page = ctk.CTkFrame(
            self.manual_pages,
            fg_color="#FFFFFF",
            corner_radius=12,
            border_width=1,
            border_color=COLORS["BORDER"]
        )
        self.manual_left_page.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=8)
        self.manual_spine = ctk.CTkFrame(
            self.manual_pages,
            fg_color="#CBD5E1",
            corner_radius=2,
            width=4
        )
        self.manual_spine.grid(row=0, column=1, sticky="ns", pady=16)
        self.manual_right_shadow = ctk.CTkFrame(
            self.manual_pages,
            fg_color=COLORS["BORDER"],
            corner_radius=12
        )
        self.manual_right_shadow.grid(
            row=0,
            column=2,
            sticky="nsew",
            padx=(2, 0),
            pady=(10, 6)
        )
        self.manual_right_page = ctk.CTkFrame(
            self.manual_pages,
            fg_color="#FFFFFF",
            corner_radius=12,
            border_width=1,
            border_color=COLORS["BORDER"]
        )
        self.manual_right_page.grid(row=0, column=2, sticky="nsew", padx=(2, 0), pady=8)

        self.manual_title = ctk.CTkLabel(
            self.manual_left_page,
            text="",
            font=self.fonts["section"],
            text_color=COLORS["PRIMARY"],
            justify="left",
            anchor="nw",
            wraplength=460
        )
        self.manual_title.pack(anchor="w", padx=24, pady=(28, 12))
        self.manual_subtitle = ctk.CTkLabel(
            self.manual_left_page,
            text="",
            font=self.fonts["body"],
            text_color=COLORS["TEXT_SECONDARY"],
            justify="left",
            anchor="nw",
            wraplength=460
        )
        self.manual_subtitle.pack(anchor="w", padx=24, pady=(0, 28))
        self.manual_left_heading = ctk.CTkLabel(
            self.manual_left_page,
            text="",
            font=self.fonts["subsection"],
            text_color=COLORS["TEXT_PRIMARY"],
            anchor="w"
        )
        self.manual_left_heading.pack(anchor="w", padx=24, pady=(0, 10))
        self.manual_left_body = ctk.CTkLabel(
            self.manual_left_page,
            text="",
            font=self.fonts["body"],
            text_color=COLORS["TEXT_SECONDARY"],
            justify="left",
            anchor="nw",
            wraplength=460
        )
        self.manual_left_body.pack(anchor="w", fill="x", padx=24)

        self.manual_right_heading = ctk.CTkLabel(
            self.manual_right_page,
            text="",
            font=self.fonts["subsection"],
            text_color=COLORS["SUCCESS"],
            anchor="w"
        )
        self.manual_right_heading.pack(anchor="w", padx=24, pady=(28, 10))
        self.manual_right_body = ctk.CTkLabel(
            self.manual_right_page,
            text="",
            font=self.fonts["body"],
            text_color=COLORS["TEXT_SECONDARY"],
            justify="left",
            anchor="nw",
            wraplength=460
        )
        self.manual_right_body.pack(anchor="w", fill="x", padx=24)
        self.manual_left_page.bind(
            "<Configure>",
            lambda event: self._update_manual_wrap(self.manual_left_page, event),
            add=True
        )
        self.manual_right_page.bind(
            "<Configure>",
            lambda event: self._update_manual_wrap(self.manual_right_page, event),
            add=True
        )

        footer = ctk.CTkFrame(book, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=(12, 18))
        footer.grid_columnconfigure(1, weight=1)
        self.manual_previous_button = self._create_button(
            footer,
            text="◀ Página Anterior",
            width=170,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color=COLORS["TEXT_SECONDARY"],
            command=lambda: self._change_manual_page(-1)
        )
        self.manual_previous_button.grid(row=0, column=0, padx=(0, 12))
        self.manual_progress = ctk.CTkProgressBar(
            footer,
            height=8,
            corner_radius=4,
            fg_color="#E2E8F0",
            progress_color=COLORS["PRIMARY"]
        )
        self.manual_progress.grid(row=0, column=1, sticky="ew")
        self.manual_next_button = self._create_button(
            footer,
            text="Página Siguiente ▶",
            width=170,
            fg_color=COLORS["PRIMARY"],
            hover_color=COLORS["PRIMARY_HOVER"],
            command=lambda: self._change_manual_page(1)
        )
        self.manual_next_button.grid(row=0, column=2, padx=(12, 0))
        self._show_manual_page(0)

    def _update_manual_wrap(self, page, event):
        wraplength = max(180, event.width - 64)
        page_labels = (
            (self.manual_title, self.manual_subtitle, self.manual_left_body)
            if page is self.manual_left_page
            else (self.manual_right_body,)
        )
        for label in page_labels:
            label.configure(wraplength=wraplength)

    def _change_manual_page(self, direction):
        next_page = self.manual_page_index + direction
        if 0 <= next_page < len(self.manual_chapters):
            self._show_manual_page(next_page)

    def _show_manual_page(self, page_index):
        if self.manual_animation_job:
            self.root.after_cancel(self.manual_animation_job)
            self.manual_animation_job = None
        self.manual_animation_token += 1
        token = self.manual_animation_token
        self.manual_page_index = page_index
        chapter = self.manual_chapters[page_index]
        self.manual_marker.configure(text=f"CAPÍTULO {page_index + 1} / {len(self.manual_chapters)}")
        self.manual_title.configure(text=chapter["title"])
        self.manual_subtitle.configure(text=chapter["subtitle"])
        self.manual_left_heading.configure(text=chapter["left_heading"])
        self.manual_right_heading.configure(text=chapter["right_heading"])
        self.manual_left_body.configure(text="")
        self.manual_right_body.configure(text="")
        self.manual_progress.set((page_index + 1) / len(self.manual_chapters))
        self.manual_previous_button.configure(
            state="normal" if page_index > 0 else "disabled"
        )
        self.manual_next_button.configure(
            state="normal" if page_index < len(self.manual_chapters) - 1 else "disabled"
        )
        self._reveal_manual_page(token, chapter, 0, 0)

    def _reveal_manual_page(self, token, chapter, column, word_index):
        if token != self.manual_animation_token:
            return
        body = self.manual_left_body if column == 0 else self.manual_right_body
        text_key = "left_text" if column == 0 else "right_text"
        words = chapter[text_key].split()
        if word_index >= len(words):
            if column == 0:
                self._reveal_manual_page(token, chapter, 1, 0)
            else:
                self.manual_animation_job = None
            return
        chunk = " ".join(words[word_index:word_index + 5])
        prefix = body.cget("text")
        body.configure(text=f"{prefix} {chunk}".strip())
        self.manual_animation_job = self.root.after(
            32,
            lambda: self._reveal_manual_page(
                token,
                chapter,
                column,
                word_index + 5
            )
        )

    # ========================================================
    # VISTA 4: ASISTENTE IA
    # ========================================================
    def build_assistant_view(self):
        frame = self.views["assistant"]
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 12))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="🤖 Asistente IA (Gemini)",
            font=self.fonts["title"],
            text_color=COLORS["TEXT_PRIMARY"]
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text="Respuestas basadas en el informe y en el escenario visible actualmente",
            font=self.fonts["body"],
            text_color=COLORS["TEXT_SECONDARY"]
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        card = ctk.CTkFrame(
            frame,
            fg_color=COLORS["BG_CARD"],
            corner_radius=12,
            border_width=2,
            border_color=COLORS["BORDER"]
        )
        card.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 28))
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        self.chat_status = ctk.CTkLabel(
            card,
            text="",
            font=self.fonts["body_small"],
            text_color=COLORS["TEXT_SECONDARY"],
            anchor="w"
        )
        self.chat_status.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))

        self.chat_history = ctk.CTkScrollableFrame(
            card,
            fg_color="#F8FAFC",
            corner_radius=8
        )
        self.scroll_frames["assistant"] = self.chat_history
        self.chat_history.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 12))
        self.chat_history.grid_columnconfigure(0, weight=1)

        quick_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.quick_questions_frame = quick_frame
        quick_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 12))
        quick_questions = [
            "¿Por qué el modelo eligió L2 y L3?",
            "Explícame el ahorro del 24.90%",
            "¿Cómo simulo un aumento de demanda?",
            "Resume el modelo matemático MIP",
        ]
        for index, question in enumerate(quick_questions):
            self._create_button(
                quick_frame,
                text=question,
                font=self.fonts["button_small"],
                fg_color="#EFF6FF",
                hover_color="#DBEAFE",
                text_color=COLORS["PRIMARY"],
                command=lambda q=question: self.enviar_mensaje_asistente(q)
            ).grid(row=index // 2, column=index % 2, sticky="ew", padx=4, pady=4)
        quick_frame.grid_columnconfigure((0, 1), weight=1)

        input_frame = ctk.CTkFrame(card, fg_color="transparent")
        input_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        input_frame.grid_columnconfigure(0, weight=1)
        self.chat_input = ctk.CTkEntry(
            input_frame,
            height=44,
            font=self.fonts["body"],
            placeholder_text="Escribe una pregunta sobre resultados o uso del software…"
        )
        self.chat_input.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.chat_input.bind("<Return>", lambda _: self.enviar_mensaje_asistente())
        self.chat_send_button = self._create_button(
            input_frame,
            text="Enviar",
            width=100,
            height=44,
            font=self.fonts["button"],
            command=self.enviar_mensaje_asistente
        )
        self.chat_send_button.grid(row=0, column=1)
        self._register_chat_surface(self.chat_history, self.chat_send_button)

        self.chat_status.configure(
            text=(
                "Gemini está habilitado mediante GEMINI_API_KEY."
                if GEMINI_API_KEY
                else (
                    "Gemini no está configurado. Añade GEMINI_API_KEY al .env junto "
                    "al ejecutable; la optimización local funciona sin internet."
                )
            )
        )
        self._append_chat(
            "Asistente: Hola. Puedo explicar el modelo, comparar el escenario actual "
            "y guiarte por las pestañas. Al enviar una pregunta adjunto los parámetros "
            "visibles y el último resultado calculado."
        )

    def _register_chat_surface(self, history, send_button, wrap_limit=None):
        surface = {
            "history": history,
            "body_labels": [],
            "send_button": send_button,
            "wrap_limit": wrap_limit,
        }
        history.bind(
            "<Configure>",
            lambda event, target=surface: self._update_chat_wrap(target, event),
            add=True
        )
        self.chat_surfaces.append(surface)
        for message in self.chat_messages:
            self._render_chat_bubble(surface, message)
        return surface

    def _render_chat_bubble(self, surface, message):
        is_user = message.startswith("Tú:")
        is_assistant = message.startswith("Asistente:")
        if is_user:
            label, body = "Tú", message[len("Tú:"):].strip()
            bubble_color, border_color, text_color = "#DBEAFE", "#93C5FD", COLORS["TEXT_PRIMARY"]
        elif is_assistant:
            label, body = "Gemini", message[len("Asistente:"):].strip()
            bubble_color, border_color, text_color = "#FFFFFF", COLORS["BORDER"], COLORS["TEXT_PRIMARY"]
        else:
            label, body = "Sistema", message.split(":", 1)[-1].strip()
            bubble_color, border_color, text_color = "#F1F5F9", COLORS["BORDER"], COLORS["TEXT_SECONDARY"]

        history = surface["history"]
        row = ctk.CTkFrame(history, fg_color="transparent")
        row.grid_columnconfigure(0, weight=1)
        opposing_pad = (
            20 if surface["wrap_limit"]
            else max(32, min(88, int(max(history.winfo_width(), 380) * 0.16)))
        )
        bubble = ctk.CTkFrame(
            row,
            fg_color=bubble_color,
            corner_radius=12,
            border_width=2,
            border_color=border_color
        )
        bubble.grid(
            row=0,
            column=0,
            sticky="e" if is_user else "w",
            padx=(opposing_pad, 8) if is_user else (8, opposing_pad),
            pady=2
        )
        ctk.CTkLabel(
            bubble,
            text=label,
            font=("Bahnschrift", 11, "bold"),
            text_color=COLORS["PRIMARY"] if is_user else COLORS["TEXT_SECONDARY"],
            anchor="w"
        ).pack(anchor="w", padx=12, pady=(8, 0))
        body_label = ctk.CTkLabel(
            bubble,
            text=body,
            font=self.fonts["body"],
            text_color=text_color,
            justify="left",
            anchor="w",
            wraplength=self._chat_wraplength(surface, history.winfo_width())
        )
        body_label.pack(anchor="w", padx=12, pady=(2, 8))
        self.chat_label_histories[body_label] = history
        surface["body_labels"].append(body_label)
        row.pack(fill="x", padx=8, pady=4)
        self._scroll_chat_to_bottom(history)
        return body_label

    def _update_chat_wrap(self, surface, event):
        wraplength = self._chat_wraplength(surface, event.width)
        for label in surface["body_labels"]:
            if label.winfo_exists():
                label.configure(wraplength=wraplength)

    @staticmethod
    def _chat_wraplength(surface, width):
        inset = 60 if surface["wrap_limit"] else 144
        available_width = max(120, width - inset)
        if surface["wrap_limit"]:
            return min(surface["wrap_limit"], available_width)
        return available_width

    def _scroll_chat_to_bottom(self, history):
        if history.winfo_exists():
            history._parent_canvas.yview_moveto(1.0)

    def _append_chat(self, message):
        self.chat_messages.append(message)
        for surface in self.chat_surfaces:
            self._render_chat_bubble(surface, message)

    def _start_thinking_bubbles(self):
        self._thinking_labels = [
            self._render_chat_bubble(surface, "Asistente: ● ○ ○ Analizando escenario...")
            for surface in self.chat_surfaces
        ]
        self._thinking_phase = 0
        self._animate_thinking_bubbles()

    def _animate_thinking_bubbles(self):
        phases = (
            "● ○ ○ Analizando escenario...",
            "○ ● ○ Analizando escenario...",
            "○ ○ ● Analizando escenario...",
        )
        text = phases[self._thinking_phase % len(phases)]
        for label in getattr(self, "_thinking_labels", []):
            if label.winfo_exists():
                label.configure(text=text)
        self._thinking_phase += 1
        self.chat_thinking_job = self.root.after(280, self._animate_thinking_bubbles)

    def _stop_thinking_animation(self):
        if self.chat_thinking_job:
            self.root.after_cancel(self.chat_thinking_job)
            self.chat_thinking_job = None

    def _begin_typewriter(self, answer):
        self._stop_thinking_animation()
        self._typing_labels = getattr(self, "_thinking_labels", [])
        self._thinking_labels = []
        for label in self._typing_labels:
            if label.winfo_exists():
                label.configure(text="")
        self._typing_chunks = re.findall(r"\S+\s*", answer)
        self._typing_index = 0
        self._typewrite_next()

    def _typewrite_next(self):
        if self._typing_index >= len(self._typing_chunks):
            self.chat_busy = False
            self.chat_typing_job = None
            for surface in self.chat_surfaces:
                surface["send_button"].configure(state="normal", text="Enviar")
            self._typing_labels = []
            return

        chunk = self._typing_chunks[self._typing_index]
        self._typing_index += 1
        for label in self._typing_labels:
            if label.winfo_exists():
                label.configure(text=label.cget("text") + chunk)
                self._scroll_chat_to_bottom(self.chat_label_histories[label])
        self.chat_typing_job = self.root.after(18, self._typewrite_next)

    def _assistant_context(self):
        try:
            costos_fijos, capacidades, demandas, max_centros, baseline = self.leer_parametros_ui()
            parameter_state = {
                "costos_fijos_usd_mes": dict(zip(UBICACIONES_DEFAULT, costos_fijos)),
                "capacidades_unidades_mes": dict(zip(UBICACIONES_DEFAULT, capacidades)),
                "demandas_unidades_mes": dict(zip(ZONAS_DEFAULT, demandas)),
                "max_centros": max_centros,
                "baseline_usd_mes": baseline,
                "total_demanda_unidades_mes": sum(demandas),
            }
        except ValueError as error:
            parameter_state = {
                "valores_visibles_sin_validar": {
                    key: entry.get() for key, entry in self.entry_vars.items()
                },
                "error_validacion": str(error),
            }

        result = self.ultimo_resultado
        if result:
            result_state = {
                "estado": result.get("estado"),
                "centros_abiertos_ultimo_calculo": result.get("centros_abiertos", []),
                "costo_fijo_usd_mes": result.get("costo_fijo"),
                "costo_transporte_usd_mes": result.get("costo_variable"),
                "costo_total_usd_mes": result.get("costo_total"),
                "ahorro_usd_mes": result.get("ahorro"),
                "ahorro_porcentaje": result.get("porcentaje_ahorro"),
                "asignaciones": result.get("asignaciones", []),
            }
        else:
            result_state = "Todavía no hay un resultado calculado."

        return (
            "ESTADO DINÁMICO CAPTURADO AL ENVIAR ESTA PREGUNTA "
            "(los parámetros pueden ser distintos de los del informe):\n"
            f"Parámetros visibles: {json.dumps(parameter_state, ensure_ascii=False)}\n"
            f"Último resultado calculado: {json.dumps(result_state, ensure_ascii=False)}\n"
            "Tarifas de envío visibles: matriz oficial fija "
            f"{json.dumps(COSTOS_ENVIO_DEFAULT, ensure_ascii=False)}; la pantalla no tiene "
            "campos editables para tarifas. Si los parámetros visibles fueron modificados "
            "después del último cálculo, indícalo y no presentes el resultado anterior "
            "como si correspondiera a esos parámetros."
        )

    def enviar_mensaje_asistente(self, prompt=None, source="main"):
        if self.chat_busy:
            return

        input_widget = (
            self.floating_chat_input if source == "floating" else self.chat_input
        )
        question = prompt if prompt is not None else input_widget.get().strip()
        if not question:
            return
        if prompt is None:
            input_widget.delete(0, "end")
        if not self.quick_questions_hidden:
            self.quick_questions_hidden = True
            self.quick_questions_frame.grid_remove()
        self._append_chat("Tú: " + question)

        if not GEMINI_API_KEY:
            self._append_chat(
                "Asistente: Gemini no está configurado. Añade GEMINI_API_KEY al archivo "
                ".env junto al ejecutable y reinicia la aplicación. La optimización local "
                "y las demás vistas siguen disponibles sin conexión."
            )
            self.mostrar_toast("Gemini requiere GEMINI_API_KEY en el .env local.", "info")
            return

        context = self._assistant_context()
        self.chat_busy = True
        for surface in self.chat_surfaces:
            surface["send_button"].configure(state="disabled", text="Consultando…")
        self.chat_status.configure(text="Gemini está preparando una respuesta…")
        self._start_thinking_bubbles()
        threading.Thread(
            target=self._request_gemini,
            args=(question, context, GEMINI_API_KEY, list(self.chat_conversation[-12:])),
            daemon=True
        ).start()

    def _request_gemini(self, question, context, api_key, prior_turns):
        try:
            client = genai.Client(api_key=api_key)
            contents = [
                genai.types.Content(
                    role=turn["role"],
                    parts=[genai.types.Part(text=turn["text"])]
                )
                for turn in prior_turns
            ]
            contents.append(
                genai.types.Content(
                    role="user",
                    parts=[genai.types.Part(text=f"{question}\n\n{context}")]
                )
            )
            used_model = GEMINI_MODEL
            try:
                config = genai.types.GenerateContentConfig(
                    system_instruction=AI_SYSTEM_INSTRUCTION
                )
                try:
                    response = client.models.generate_content(
                        model=GEMINI_MODEL,
                        contents=contents,
                        config=config,
                    )
                except Exception as error:
                    if not _is_gemini_model_not_found(error):
                        raise
                    used_model = GEMINI_FALLBACK_MODEL
                    response = client.models.generate_content(
                        model=GEMINI_FALLBACK_MODEL,
                        contents=contents,
                        config=config,
                    )
                answer = response.text
            finally:
                client.close()
            if not answer:
                raise RuntimeError("Gemini returned an empty response.")
            self.root.after(0, self._finish_gemini_request, answer, None, question, used_model)
        except Exception as error:
            message = str(error).replace(api_key, "[clave oculta]")
            try:
                self.root.after(0, self._finish_gemini_request, None, message, question, GEMINI_MODEL)
            except (RuntimeError, tk.TclError):
                return

    def _finish_gemini_request(self, answer, error, question, model=GEMINI_MODEL):
        if error:
            self.chat_status.configure(text="No se pudo completar la consulta.")
            answer = f"No fue posible consultar Gemini: {error}"
            self.mostrar_toast("No se pudo completar la consulta a Gemini.", "error")
        else:
            answer = self._sanitize_assistant_response(answer)
            self.chat_conversation.extend([
                {"role": "user", "text": question},
                {"role": "model", "text": answer},
            ])
            self.chat_conversation = self.chat_conversation[-12:]
            self.chat_status.configure(text=f"Respuesta recibida de {model}.")

        answer = self._sanitize_assistant_response(answer)
        assistant_message = "Asistente: " + answer
        self.chat_messages.append(assistant_message)
        self._begin_typewriter(answer)

    @staticmethod
    def _sanitize_assistant_response(answer):
        answer = re.sub(r"\*{1,2}|#+", "", answer)
        answer = answer.replace("```", "").replace("`", "")
        return answer.strip()
        
    # ========================================================
    # VISTA 5: LICENCIA Y ROI COMERCIAL
    # ========================================================
    def build_license_view(self):
        frame = self.views["license"]
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        scroll = ctk.CTkScrollableFrame(frame, fg_color=COLORS["BG_MAIN"], corner_radius=0)
        self.scroll_frames["license"] = scroll
        scroll.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        scroll.grid_columnconfigure(0, weight=1)
        
        # Hero
        hero = ctk.CTkFrame(scroll, fg_color=COLORS["PRIMARY"], corner_radius=16)
        hero.pack(fill="x", pady=(0, 24))
        hero.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(hero, text="💼 MIP Retail Optimizer™ Enterprise",
                    font=self.fonts["title"], text_color=COLORS["TEXT_WHITE"]).grid(row=0, column=0, pady=(32, 8))
        ctk.CTkLabel(hero, text="Sistema de Optimización Logística y Diseño de Redes de Distribución",
                    font=self.fonts["body"], text_color="#DBEAFE").grid(row=1, column=0, pady=(0, 8))
        
        # ROI Box
        roi_card = ctk.CTkFrame(scroll, fg_color=COLORS["BG_CARD"], corner_radius=12,
                               border_width=2, border_color=COLORS["BORDER"])
        roi_card.pack(fill="x", pady=(0, 24))
        roi_card.grid_columnconfigure((0,1,2), weight=1)
        
        ctk.CTkLabel(roi_card, text="💰 RETORNO DE INVERSIÓN (ROI) ESTIMADO",
                    font=self.fonts["section"], text_color=COLORS["PRIMARY"]).grid(row=0, column=0, columnspan=3, sticky="w", padx=24, pady=(20, 16))
        
        roi_metrics = [
            ("Ahorro Mensual", "$60,500 USD"),
            ("Ahorro Anual", "$726,000 USD"),
            ("Reducción Costos", "24.90%"),
            ("ROI Primer Año", "> 300%"),
            ("Payback Estimado", "< 3 meses"),
        ]
        
        for i, (label, value) in enumerate(roi_metrics):
            cell = ctk.CTkFrame(roi_card, fg_color="#F8FAFC", corner_radius=8)
            cell.grid(row=1, column=i, padx=12, pady=(0, 20), sticky="ew")
            cell.grid_columnconfigure(0, weight=1)
            
            ctk.CTkLabel(cell, text=label, font=("Segoe UI", 11), text_color=COLORS["TEXT_SECONDARY"]).pack(pady=(12, 2))
            ctk.CTkLabel(cell, text=value,             font=("Bahnschrift", 18, "bold"), text_color=COLORS["SUCCESS"]).pack(pady=(0, 12))
        
        ctk.CTkLabel(roi_card, text="*Baseline $243,000/mes → Optimizado $182,500/mes (caso real)",
                    font=("Segoe UI", 10), text_color=COLORS["TEXT_MUTED"]).grid(row=2, column=0, columnspan=3, pady=(0, 20))
        
        # Beneficios
        ctk.CTkLabel(scroll, text="✨ BENEFICIOS CLAVE", font=self.fonts["section"],
                    text_color=COLORS["PRIMARY"]).pack(anchor="w", pady=(24, 12))
        
        beneficios = [
            "Optimización matemática rigurosa (MIP) con optimalidad global garantizada",
            "Análisis de sensibilidad en tiempo real (what-if scenarios interactivos)",
            "Interfaz ejecutiva con dashboard KPIs, gráficos duales y reportes listos para gerencia",
            "Importación/Exportación de escenarios (CSV/Excel multi-hoja profesional)",
            "Pantalla completa nativa, modo protegido por defecto, listo para demo en vivo",
            "Ejecutable standalone Windows (.exe) sin dependencias de Python",
        ]
        
        for b in beneficios:
            ctk.CTkLabel(scroll, text=f"  ✓  {b}",
                        font=("Segoe UI", 12), text_color=COLORS["TEXT_SECONDARY"],
                        anchor="w").pack(anchor="w", pady=4)
        
        # Modelo de negocio
        ctk.CTkLabel(scroll, text="💼 MODELO DE NEGOCIO",
                    font=self.fonts["section"], text_color=COLORS["PRIMARY"]).pack(anchor="w", pady=(24, 12))
        
        modelo_items = [
            ("Fase 1 - Diagnóstico", "Levantamiento de datos, validación, configuración del modelo"),
            ("Fase 2 - Ejecución", "Corridas base, análisis de sensibilidad, comparación de escenarios"),
            ("Fase 3 - Entrega", "Script ejecutable, documentación técnica, dashboard, capacitación"),
            ("Fee Implementación", "Según alcance y número de SKUs/ubicaciones"),
            ("Fee por Optimización", "Por corrida de escenario productivo o re-optimización mensual"),
            ("Suscripción Anual", "Actualizaciones, nuevos módulos (inventario, routing, estacionalidad), soporte"),
        ]
        
        for label, desc in modelo_items:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=f"  {label}:", font=("Segoe UI", 11, "bold"),
                        text_color=COLORS["WARNING"], width=200).pack(side="left")
            ctk.CTkLabel(row, text=desc, font=("Segoe UI", 11),
                        text_color=COLORS["TEXT_SECONDARY"]).pack(side="left")
    
    # ========================================================
    # LÓGICA DE NEGOCIO
    # ========================================================
    def cargar_valores_iniciales(self):
        self._set_parameter_fields((
            COSTOS_FIJOS_DEFAULT,
            CAPACIDADES_DEFAULT,
            DEMANDA_DEFAULT,
            MAX_CENTROS_DEFAULT,
            COSTO_BASELINE_DEFAULT,
        ))

    def _set_parameter_fields(self, params):
        costos_fijos, capacidades, demandas, max_centros, baseline = params
        values = {
            **{f"costo_fijo_{i}": value for i, value in enumerate(costos_fijos)},
            **{f"capacidad_{i}": value for i, value in enumerate(capacidades)},
            **{f"demanda_{i}": value for i, value in enumerate(demandas)},
            "max_centros": max_centros,
            "baseline": baseline,
        }
        for key, value in values.items():
            entry = self.entry_vars[key]
            entry.configure(state="normal")
            entry.delete(0, "end")
            entry.insert(0, f"{value:,}" if key != "max_centros" else str(value))

    def bloquear_campos(self):
        for entry in self.entry_vars.values():
            entry.configure(state="disabled")
        self.modo_edicion = False
        self.mode_indicator.configure(text="🔒  Modo Protegido", text_color="#DC2626")
        self.btn_save.pack_forget()
        self.btn_cancel_edit.pack_forget()
        if not self.btn_edit.winfo_manager():
            self.btn_edit.pack(side="left", before=self.btn_restore, padx=4)

    def desbloquear_campos(self):
        if self.optimization_busy:
            self.mostrar_toast("Espera a que termine el cálculo para editar.", "warning")
            return
        for entry in self.entry_vars.values():
            entry.configure(state="normal")
        self.modo_edicion = True
        self.mode_indicator.configure(text="✏️  Modo Edición Activo", text_color=COLORS["SUCCESS"])
        self.btn_edit.pack_forget()
        self.btn_save.pack(side="left", before=self.btn_restore, padx=4)
        self.btn_cancel_edit.pack(side="left", before=self.btn_restore, padx=4)

    def habilitar_edicion(self):
        if self.confirmar_accion(
            "Editar parámetros",
            "Podrás modificar los valores del escenario. Guarda los cambios antes de ejecutar la optimización.",
            confirm_text="Editar"
        ):
            self.desbloquear_campos()

    def guardar_cambios(self):
        try:
            params = self.leer_parametros_ui()
        except ValueError as error:
            self.mostrar_toast(str(error), "error", duration=4000)
            return

        self.saved_parameters = params
        self._set_parameter_fields(params)
        self.bloquear_campos()
        self.mostrar_toast("Parámetros guardados correctamente", "success")

    def cancelar_edicion(self):
        if self.saved_parameters is not None:
            self._set_parameter_fields(self.saved_parameters)
        self.bloquear_campos()
        self.mostrar_toast("Edición cancelada.", "info")

    def restaurar_valores_base(self):
        if not self.confirmar_accion(
            "Restaurar valores base",
            "Se reemplazarán los parámetros guardados por los valores oficiales del estudio.",
            confirm_text="Restaurar"
        ):
            return
        self.cargar_valores_iniciales()
        self.saved_parameters = self.leer_parametros_ui()
        self.bloquear_campos()
        self.mostrar_toast("Parámetros oficiales restaurados; recalculando el escenario.", "info")
        self.run_optimization_silencioso()

    def importar_escenario(self):
        file_path = filedialog.askopenfilename(
            title="Importar Escenario",
            filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx"), ("Todos", "*.*")]
        )
        if not file_path:
            return
        
        try:
            df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
            if not all(c in df.columns for c in ['parametro', 'valor']):
                raise ValueError("Columnas requeridas: 'parametro', 'valor'")
            
            params = dict(zip(df['parametro'], df['valor']))
            mapping = {**{f'costo_fijo_{i}': f'costo_fijo_{i}' for i in range(4)},
                      **{f'capacidad_{i}': f'capacidad_{i}' for i in range(4)},
                      **{f'demanda_{j}': f'demanda_{j}' for j in range(6)},
                      'max_centros': 'max_centros', 'baseline': 'baseline'}
            
            self.desbloquear_campos()
            imported = 0
            for pk, ek in mapping.items():
                if pk in params and ek in self.entry_vars:
                    self.entry_vars[ek].delete(0, "end")
                    self.entry_vars[ek].insert(0, str(params[pk]))
                    imported += 1
            self.leer_parametros_ui()
            self.mostrar_toast(
                f"{imported} parámetros importados. Revisa y guarda los cambios.",
                "success"
            )
        except Exception as error:
            self.mostrar_toast(f"No se pudo importar el escenario: {error}", "error", duration=4500)

    def leer_parametros_ui(self):
        try:
            costos_fijos = [int(self.entry_vars[f"costo_fijo_{i}"].get().replace(",", "")) for i in range(4)]
            capacidades = [int(self.entry_vars[f"capacidad_{i}"].get().replace(",", "")) for i in range(4)]
            demandas = [int(self.entry_vars[f"demanda_{j}"].get().replace(",", "")) for j in range(6)]
            max_centros = int(self.entry_vars["max_centros"].get())
            baseline = int(self.entry_vars["baseline"].get().replace(",", ""))
        except (ValueError, KeyError) as error:
            raise ValueError(f"Parámetro inválido: {error}") from error

        if max_centros < 1 or max_centros > len(UBICACIONES_DEFAULT):
            raise ValueError("Máximo de centros: elige un valor entre 1 y 4.")
        if any(costo < 0 for costo in costos_fijos):
            raise ValueError("Los costos fijos no pueden ser negativos.")
        if any(capacidad <= 0 for capacidad in capacidades):
            raise ValueError("Las capacidades deben ser mayores que cero.")
        if any(demanda < 0 for demanda in demandas):
            raise ValueError("Las demandas no pueden ser negativas.")
        if baseline <= 0:
            raise ValueError("El costo baseline debe ser mayor que cero.")
        return costos_fijos, capacidades, demandas, max_centros, baseline

    def iniciar_ejecucion_progresiva(self):
        """Inicia la animación paso a paso"""
        if self.is_executing or self.optimization_busy:
            return
        if self.modo_edicion:
            self.mostrar_toast("Guarda o cancela la edición antes de ejecutar.", "warning")
            return

        try:
            params = self.leer_parametros_ui()
        except ValueError as error:
            self.mostrar_toast(str(error), "error", duration=4000)
            return

        if not self.execution_card.winfo_manager():
            self.execution_card.pack(fill="x", pady=(0, 16), before=self.kpi_card)

        self.is_executing = True
        self.btn_execute.configure(state="disabled", text="⏳ Ejecutando...")
        for button in (self.btn_edit, self.btn_restore, self.btn_import):
            button.configure(state="disabled")
        self.execution_status.configure(text="● Iniciando...", text_color=COLORS["PRIMARY"])
        self.progress_bar.set(0)
        self.execution_log.configure(state="normal")
        self.execution_log.delete("0.0", "end")
        self.execution_log.insert("0.0", "[0.0s] Iniciando optimización...\n")
        self.execution_log.see("end")
        self.execution_log.configure(state="disabled")
        
        self.execution_step = 0
        self.execution_params = params
        _, capacidades, demandas, max_centros, _ = params
        max_capacity = sum(sorted(capacidades, reverse=True)[:max_centros])
        total_demand = sum(demandas)
        self.execution_steps = [
            f"[1/4] Validando capacidad máxima disponible ({max_capacity:,} u) "
            f"frente a demanda ({total_demand:,} u)...",
            "[2/4] Construyendo el modelo MIP con los parámetros guardados...",
            "[3/4] Resolviendo el modelo con CBC (Branch-and-Bound)...",
            "[4/4] Finalizando la solución óptima del escenario...",
        ]
        self._run_execution_step(0)

    def _run_execution_step(self, step):
        """Ejecuta animación paso a paso usando after()"""
        if step >= len(self.execution_steps):
            self._finalize_execution()
            return

        progress = (step + 1) / (len(self.execution_steps) + 1)
        msg = self.execution_steps[step]
        self.progress_bar.set(progress)
        self.execution_status.configure(text=f"● Paso {step+1}/4", text_color=COLORS["PRIMARY"])
        
        self.execution_log.configure(state="normal")
        self.execution_log.insert("end", f"\n{msg}")
        self.execution_log.see("end")
        self.execution_log.configure(state="disabled")
        
        delays = [400, 500, 600, 300]
        self.root.after(delays[step], lambda: self._run_execution_step(step + 1))

    def _finalize_execution(self):
        """Resuelve el modelo fuera del hilo de interfaz."""
        self.execution_log.configure(state="normal")
        self.execution_log.insert("end", "\n✓ Ejecutando CBC en segundo plano...\n")
        self.execution_log.see("end")
        self.execution_log.configure(state="disabled")
        if not self._solve_model_async(self.execution_params, self._finish_execution):
            self._finish_execution(None, RuntimeError("Ya hay un cálculo en curso."), self.execution_params)

    def _solve_model_async(self, params, callback):
        if self.optimization_busy:
            return False

        self.optimization_busy = True
        for button in (self.btn_edit, self.btn_restore, self.btn_import):
            button.configure(state="disabled")
        self.optimization_request_id += 1
        request_id = self.optimization_request_id
        costos_fijos, capacidades, demandas, max_centros, baseline = params

        def solve():
            try:
                result = resolver_modelo(
                    costos_fijos=costos_fijos,
                    capacidades=capacidades,
                    demandas=demandas,
                    costos_envio=COSTOS_ENVIO_DEFAULT,
                    max_centros=max_centros,
                    zonas=ZONAS_DEFAULT,
                    ubicaciones=UBICACIONES_DEFAULT,
                    costo_baseline=baseline
                )
                error = None
            except Exception as solver_error:
                result = None
                error = solver_error
            try:
                self.root.after(
                    0, self._deliver_model_result, request_id, callback,
                    result, error, params
                )
            except (RuntimeError, tk.TclError):
                return

        self.solver_thread = threading.Thread(target=solve, name="mip-solver", daemon=True)
        self.solver_thread.start()
        return True

    def _deliver_model_result(self, request_id, callback, result, error, params):
        if request_id != self.optimization_request_id:
            return
        self.optimization_busy = False
        for button in (self.btn_edit, self.btn_restore, self.btn_import):
            button.configure(state="normal")
        callback(result, error, params)

    def _finish_execution(self, resultado, error, params):
        self.is_executing = False
        self.btn_execute.configure(state="normal", text="▶  Ejecutar Optimización Matemática")
        for button in (self.btn_edit, self.btn_restore, self.btn_import):
            button.configure(state="normal")

        if error or not resultado or resultado.get("estado") != "Optimal":
            detail = str(error) if error else (
                f"{resultado.get('estado')}: {resultado.get('mensaje', 'No se encontró solución óptima.')}"
            )
            self._append_execution_log(f"\nError de optimización: {detail}")
            self.execution_status.configure(text="● Error", text_color=COLORS["DANGER"])
            self.mostrar_toast(f"No se pudo resolver el escenario: {detail}", "error", duration=5000)
            return

        try:
            self.ultimo_resultado = resultado
            self.actualizar_kpis_y_resultados(resultado, params)
        except Exception as ui_error:
            self.execution_status.configure(text="● Error al actualizar", text_color=COLORS["DANGER"])
            self.mostrar_toast(f"El cálculo terminó, pero no se pudo actualizar la vista: {ui_error}", "error")
            return

        self.progress_bar.set(1.0)
        self.execution_status.configure(text="● Completado ✓", text_color=COLORS["SUCCESS"])
        self._append_execution_log(
            f"\nOPTIMAL: ${resultado['costo_total']:,.0f} | "
            f"Ahorro: ${resultado['ahorro']:,.0f} ({resultado['porcentaje_ahorro']:.2f}%)"
        )
        self.mostrar_toast(
            f"Optimización lista: {', '.join(resultado['centros_abiertos'])}, "
            f"${resultado['costo_total']:,.0f}/mes.",
            "success"
        )

    def _append_execution_log(self, message):
        self.execution_log.configure(state="normal")
        self.execution_log.insert("end", message + "\n")
        self.execution_log.see("end")
        self.execution_log.configure(state="disabled")

    def actualizar_kpis_y_resultados(self, resultado, params=None):
        """Actualiza KPIs, gráficos y tabla"""
        params = params or self.leer_parametros_ui()
        costos_fijos, capacidades, demandas, max_centros, baseline = params
        self.ultimo_parametros = {
            "costos_fijos": costos_fijos,
            "capacidades": capacidades,
            "demandas": demandas,
            "max_centros": max_centros,
            "baseline": baseline,
        }
        self.costo_actual = baseline
        self.costo_optimo = resultado["costo_total"]

        # KPIs
        self.kpi_widgets["💰 Costo Total Óptimo"].configure(text=f"${resultado['costo_total']:,.0f}")
        self.kpi_widgets["💵 Ahorro Mensual"].configure(text=f"${resultado['ahorro']:,.0f} / {resultado['porcentaje_ahorro']:.2f}%")
        self.kpi_widgets["🏢 Centros Activos"].configure(
            text=f"{', '.join(resultado['centros_abiertos'])} "
                 f"({len(resultado['centros_abiertos'])}/{max_centros})"
        )
        self.kpi_widgets["✅ Demanda Cubierta"].configure(
            text=f"{sum(demandas):,} unidades (100%)"
        )
        
        self.kpi_card.pack(fill="x", pady=(0, 16))
        self.charts_card.pack(fill="x", pady=(0, 0))
        
        self.crear_graficos()
        self.load_csv_data_from_result(resultado['asignaciones'])
        self.load_matrix_table(resultado['asignaciones'])

    def load_csv_data(self):
        self.run_optimization_silencioso()

    def run_optimization_silencioso(self):
        if self.optimization_busy:
            self.mostrar_toast("Ya hay un cálculo en curso.", "warning")
            return
        try:
            params = self.leer_parametros_ui()
        except ValueError as error:
            self.mostrar_toast(str(error), "error", duration=4000)
            return

        self.btn_execute.configure(state="disabled", text="Calculando escenario...")
        if not self._solve_model_async(params, self._finish_silent_optimization):
            self.btn_execute.configure(state="normal", text="▶  Ejecutar Optimización Matemática")

    def _finish_silent_optimization(self, resultado, error, params):
        self.btn_execute.configure(state="normal", text="▶  Ejecutar Optimización Matemática")
        if error or not resultado or resultado.get("estado") != "Optimal":
            detail = str(error) if error else (
                f"{resultado.get('estado')}: {resultado.get('mensaje', 'No se encontró solución óptima.')}"
            )
            self.mostrar_toast(f"No se pudo calcular el escenario: {detail}", "error", duration=5000)
            return
        try:
            self.ultimo_resultado = resultado
            self.actualizar_kpis_y_resultados(resultado, params)
        except Exception as ui_error:
            self.mostrar_toast(f"No se pudo actualizar el escenario: {ui_error}", "error", duration=5000)

    def load_csv_data_from_result(self, asignaciones):
        for item in self.tree_matrix.get_children():
            self.tree_matrix.delete(item)
        for a in asignaciones:
            self.tree_matrix.insert("", "end", values=(
                a['Ubicacion'], a['Zona'],
                f"{a['Cantidad_Enviada']:,.0f}",
                "—", "—", "—"
            ))
    
    def load_matrix_table(self, asignaciones):
        """Carga tabla completa con costos calculados"""
        if self.ultimo_parametros is None:
            return
        for item in self.tree_matrix.get_children():
            self.tree_matrix.delete(item)
        
        demands = self.ultimo_parametros["demandas"]
        total_var = 0
        for a in asignaciones:
            i = UBICACIONES_DEFAULT.index(a['Ubicacion'])
            j = ZONAS_DEFAULT.index(a['Zona'])
            costo_u = COSTOS_ENVIO_DEFAULT[i][j]
            costo_r = a['Cantidad_Enviada'] * costo_u
            pct = (a['Cantidad_Enviada'] / demands[j] * 100) if demands[j] else 0
            total_var += costo_r
            
            self.tree_matrix.insert("", "end", values=(
                a['Ubicacion'], a['Zona'],
                f"{a['Cantidad_Enviada']:,.0f}",
                f"{costo_u:.2f}",
                f"{costo_r:,.2f}",
                f"{pct:.1f}%"
            ))
        
        self.total_label.configure(
            text=f"TOTAL GENERAL: {sum(demands):,} unidades | ${total_var:,.0f} USD costo variable"
        )
    
    def crear_graficos(self):
        self.root.update_idletasks()
        for chart_canvas in self.chart_canvases:
            plt.close(chart_canvas.figure)
        self.chart_canvases.clear()
        for widget in self.chart1_canvas_frame.winfo_children():
            widget.destroy()
        for widget in self.chart2_canvas_frame.winfo_children():
            widget.destroy()
        
        if not self.ultimo_resultado or not self.ultimo_parametros:
            return
        
        TEXT = COLORS["CHART_TEXT"]
        plt.style.use('default')
        
        # ---- GRÁFICO 1: Comparativa Baseline vs Óptimo ----
        chart1_width = max(4.5, self.chart1_canvas_frame.winfo_width() / 100)
        fig1, ax1 = plt.subplots(figsize=(chart1_width, 3.2), dpi=100)
        fig1.patch.set_facecolor(COLORS["CHART_BG"])
        ax1.set_facecolor(COLORS["CHART_BG"])
        
        labels = ['Baseline\n(Actual)', 'Optimizado\n(Nuevo)']
        values = [self.costo_actual, self.costo_optimo]
        colors = [COLORS["CHART_BAR_BASELINE"], COLORS["CHART_BAR_OPTIMAL"]]
        
        bars = ax1.bar(labels, values, color=colors, edgecolor='white', linewidth=1.5, width=0.65)
        
        for bar, val in zip(bars, values):
            ax1.annotate(f'${val:,.0f}',
                       xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                       xytext=(0, 10), textcoords="offset points",
                       ha='center', va='bottom',
                       fontweight='bold', fontsize=10, color=COLORS["CHART_TEXT"])
        
        ax1.set_ylabel('USD / mes', fontsize=10, fontweight='bold', color=TEXT)
        ax1.set_title('Costo mensual: baseline vs. óptimo',
                     fontsize=12, fontweight='bold', pad=12, color=TEXT)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['left'].set_color(COLORS["BORDER"])
        ax1.spines['bottom'].set_color(COLORS["BORDER"])
        ax1.tick_params(axis='x', colors=TEXT, labelsize=9)
        ax1.tick_params(axis='y', colors=TEXT, labelsize=8)
        ax1.grid(axis='y', alpha=0.2, color=COLORS["BORDER"])
        ax1.set_ylim(0, max(values) * 1.28)
        
        plt.tight_layout(pad=1.2)
        
        canvas1 = FigureCanvasTkAgg(fig1, master=self.chart1_canvas_frame)
        canvas1.get_tk_widget().pack(fill="both", expand=True)
        canvas1.get_tk_widget().bind(
            "<MouseWheel>",
            self._scroll_active_view,
            add=True
        )
        canvas1.draw()
        canvas1.get_tk_widget().update_idletasks()
        self.chart_canvases.append(canvas1)
        
        # ---- GRÁFICO 2: Utilización de Capacidad ----
        chart2_width = max(4.5, self.chart2_canvas_frame.winfo_width() / 100)
        fig2, ax2 = plt.subplots(figsize=(chart2_width, 3.2), dpi=100)
        fig2.patch.set_facecolor(COLORS["CHART_BG"])
        ax2.set_facecolor(COLORS["CHART_BG"])

        util_vals = []
        vol_vals = []
        capacidades = self.ultimo_parametros["capacidades"]
        for idx, c in enumerate(UBICACIONES_DEFAULT):
            cap = capacidades[idx]
            vol = sum(
                a['Cantidad_Enviada']
                for a in self.ultimo_resultado['asignaciones']
                if a['Ubicacion'] == c
            )
            util = (vol / cap * 100) if cap > 0 else 0
            
            util_vals.append(util)
            vol_vals.append(vol)

        y_pos = range(len(UBICACIONES_DEFAULT))
        colors_bar = []
        for u in util_vals:
            if u == 0:
                colors_bar.append("#E2E8F0")
            elif u > 80:
                colors_bar.append(COLORS["DANGER"])
            elif u > 60:
                colors_bar.append(COLORS["WARNING"])
            else:
                colors_bar.append(COLORS["SUCCESS"])
        
        bars = ax2.barh(y_pos, util_vals, color=colors_bar, edgecolor='white', height=0.65)
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(UBICACIONES_DEFAULT, fontsize=9, color=COLORS["CHART_TEXT"])
        ax2.set_xlim(0, 118)
        ax2.set_xlabel('Utilización de capacidad (%)', fontsize=9, fontweight='bold', color=COLORS["CHART_TEXT"])
        ax2.set_title('Utilización por centro',
                     fontsize=12, fontweight='bold', pad=12, color=COLORS["CHART_TEXT"])
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_color(COLORS["BORDER"])
        ax2.spines['bottom'].set_color(COLORS["BORDER"])
        ax2.tick_params(axis='x', colors=COLORS["CHART_TEXT"], labelsize=8)
        ax2.tick_params(axis='y', colors=COLORS["CHART_TEXT"], labelsize=9)
        ax2.grid(axis='x', alpha=0.2, color=COLORS["BORDER"])
        
        for bar, val, centro in zip(bars, util_vals, UBICACIONES_DEFAULT):
            etiqueta = f"{val:.1f}%"
            if centro not in self.ultimo_resultado['centros_abiertos']:
                etiqueta += " · Cerrado"
            ax2.annotate(
                etiqueta,
                xy=(bar.get_width(), bar.get_y() + bar.get_height() / 2),
                xytext=(6, 0),
                textcoords="offset points",
                ha='left',
                va='center',
                fontweight='bold',
                fontsize=9,
                color=COLORS["CHART_TEXT"]
            )
        
        plt.tight_layout(pad=1.2)
        
        canvas2 = FigureCanvasTkAgg(fig2, master=self.chart2_canvas_frame)
        canvas2.get_tk_widget().pack(fill="both", expand=True)
        canvas2.get_tk_widget().bind(
            "<MouseWheel>",
            self._scroll_active_view,
            add=True
        )
        canvas2.draw()
        canvas2.get_tk_widget().update_idletasks()
        self.chart_canvases.append(canvas2)
    
    def exportar_excel_matriz(self):
        if not self.ultimo_resultado or not self.ultimo_parametros:
            self.mostrar_toast("Ejecuta una optimización antes de exportar.", "warning")
            return
        
        path = filedialog.asksaveasfilename(
            title="Exportar a Excel", defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="Reporte_Ejecutivo_MIP_Retail_Optimizer.xlsx"
        )
        if not path: return
        
        try:
            self.crear_excel_ejecutivo(path)
            self.mostrar_toast(f"Reporte exportado: {os.path.basename(path)}", "success")
        except Exception as error:
            self.mostrar_toast(f"No se pudo exportar el reporte: {error}", "error", duration=4500)
    
    def exportar_csv_matriz(self):
        if not self.ultimo_resultado or not self.ultimo_parametros:
            self.mostrar_toast("Ejecuta una optimización antes de exportar.", "warning")
            return
        
        path = filedialog.asksaveasfilename(
            title="Exportar CSV", defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="Matriz_Asignacion_Logistica.csv"
        )
        if not path: return
        
        try:
            r = self.ultimo_resultado
            rows = []
            demands = self.ultimo_parametros["demandas"]
            for a in r['asignaciones']:
                i = UBICACIONES_DEFAULT.index(a['Ubicacion'])
                j = ZONAS_DEFAULT.index(a['Zona'])
                costo_u = COSTOS_ENVIO_DEFAULT[i][j]
                costo_r = a['Cantidad_Enviada'] * costo_u
                pct = (a['Cantidad_Enviada'] / demands[j] * 100) if demands[j] else 0
                rows.append([a['Ubicacion'], a['Zona'], a['Cantidad_Enviada'],
                            costo_u, costo_r, pct])
            
            df = pd.DataFrame(rows, columns=['Centro', 'Zona', 'Unidades',
                                            'Costo_Unit', 'Costo_Ruta', 'Pct_Demanda'])
            df.to_csv(path, index=False)
            self.mostrar_toast(f"CSV exportado: {os.path.basename(path)}", "success")
        except Exception as error:
            self.mostrar_toast(f"No se pudo exportar el CSV: {error}", "error", duration=4500)
    
    def crear_excel_ejecutivo(self, file_path):
        if not self.ultimo_resultado or not self.ultimo_parametros:
            raise ValueError("No hay un resultado calculado para exportar.")

        result = self.ultimo_resultado
        params = self.ultimo_parametros
        wb = openpyxl.Workbook()
        summary = wb.active
        if summary is None:
            raise RuntimeError("No se pudo crear la hoja de resumen.")
        summary.title = "Resumen"
        summary.append(["MIP Retail Optimizer"])
        summary.append(["Indicador", "Resultado"])
        summary.append(["Estado", result["estado"]])
        summary.append(["Centros abiertos", ", ".join(result["centros_abiertos"])])
        summary.append(["Costo baseline (USD/mes)", params["costo_baseline"]])
        summary.append(["Costo fijo (USD/mes)", result["costo_fijo"]])
        summary.append(["Costo de transporte (USD/mes)", result["costo_variable"]])
        summary.append(["Costo total (USD/mes)", result["costo_total"]])
        summary.append(["Ahorro (USD/mes)", result["ahorro"]])
        summary.append(["Ahorro (%)", result["porcentaje_ahorro"]])
        summary["A1"].font = Font(
            name="Bahnschrift",
            size=16,
            bold=True,
            color="0F172A"
        )
        for cell in summary[2]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(
                fill_type="solid",
                fgColor="1D4ED8"
            )
        summary.column_dimensions["A"].width = 34
        summary.column_dimensions["B"].width = 28
        summary.freeze_panes = "A3"

        routes = wb.create_sheet("Asignaciones")
        routes.append([
            "Centro",
            "Zona",
            "Unidades",
            "Costo unitario (USD)",
            "Costo de ruta (USD)",
            "Demanda atendida (%)"
        ])
        for assignment in result["asignaciones"]:
            center_index = UBICACIONES_DEFAULT.index(assignment["Ubicacion"])
            zone_index = ZONAS_DEFAULT.index(assignment["Zona"])
            units = assignment["Cantidad_Enviada"]
            unit_cost = COSTOS_ENVIO_DEFAULT[center_index][zone_index]
            demand = params["demandas"][zone_index]
            routes.append([
                assignment["Ubicacion"],
                assignment["Zona"],
                units,
                unit_cost,
                units * unit_cost,
                units / demand * 100 if demand else 0
            ])
        for cell in routes[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(
                fill_type="solid",
                fgColor="1D4ED8"
            )
        routes.freeze_panes = "A2"
        routes.auto_filter.ref = routes.dimensions
        for column, width in zip("ABCDEF", (16, 14, 16, 24, 22, 24)):
            routes.column_dimensions[column].width = width
        wb.save(file_path)
    
    def toggle_fullscreen(self, event=None):
        del event
        if sys.platform.startswith("win"):
            self.root.state("normal" if self.root.state() == "zoomed" else "zoomed")
            return
        self.root.attributes("-zoomed", not self.root.attributes("-zoomed"))
    
    def end_fullscreen(self, event=None):
        del event
        try:
            self.root.state('normal')
        except tk.TclError:
            self.root.attributes('-zoomed', False)


def _show_startup_error(root, error):
    for widget in root.winfo_children():
        widget.destroy()
    root.title("MIP Retail Optimizer — error de inicio")
    root.geometry("700x300")
    root.configure(fg_color=COLORS["BG_MAIN"])

    card = ctk.CTkFrame(
        root,
        fg_color=COLORS["BG_CARD"],
        corner_radius=14,
        border_width=2,
        border_color=COLORS["BORDER"]
    )
    card.pack(fill="both", expand=True, padx=24, pady=24)
    ctk.CTkLabel(
        card,
        text="La aplicación no pudo completar el inicio.",
        font=("Bahnschrift", 20, "bold"),
        text_color=COLORS["DANGER"]
    ).pack(anchor="w", padx=24, pady=(24, 8))
    ctk.CTkLabel(
        card,
        text=f"El error quedó registrado en errores.log.\n{error}",
        font=("Segoe UI", 13),
        text_color=COLORS["TEXT_SECONDARY"],
        justify="left",
        wraplength=600
    ).pack(anchor="w", padx=24, pady=(0, 20))
    ctk.CTkButton(
        card,
        text="Cerrar",
        height=38,
        corner_radius=10,
        fg_color=COLORS["PRIMARY"],
        hover_color=COLORS["PRIMARY_HOVER"],
        command=root.destroy
    ).pack(anchor="e", padx=24, pady=(0, 20))


def main():
    root = None
    try:
        root = ctk.CTk()
        MIPRetailOptimizerApp(root)
        root.mainloop()
    except Exception as error:
        _record_exception(type(error), error, error.__traceback__)
        if root is None:
            return
        try:
            root.winfo_exists()
        except tk.TclError:
            return
        _show_startup_error(root, error)
        root.mainloop()


if __name__ == "__main__":
    main()
