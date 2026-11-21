import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import os
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

# Importar el motor matemático
from optimizacion import (
    resolver_modelo,
    ZONAS_DEFAULT, UBICACIONES_DEFAULT, DEMANDA_DEFAULT,
    COSTOS_FIJOS_DEFAULT, CAPACIDADES_DEFAULT,
    MAX_CENTROS_DEFAULT, COSTOS_ENVIO_DEFAULT, COSTO_BASELINE_DEFAULT
)

# Configuración de colores corporativos
COLORS = {
    "NAVY": "#0F172A",      # Azul marino oscuro - fondo principal
    "SLATE": "#1E293B",     # Pizarra - tarjetas/paneles
    "SLATE_LIGHT": "#334155",
    "TEAL": "#10B981",      # Esmeralda - acentos principales
    "TEAL_HOVER": "#059669",
    "TEAL_LIGHT": "#D1FAE5",
    "WHITE": "#FFFFFF",
    "GRAY": "#94A3B8",
    "GRAY_LIGHT": "#F1F5F9",
    "RED": "#EF4444",
    "RED_HOVER": "#DC2626",
    "AMBER": "#F59E0B",
}

# Configurar customtkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MIPRetailOptimizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MIP Retail Optimizer™ Enterprise - Sistema de Optimización Logística")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Pantalla completa en Windows
        try:
            self.root.state('zoomed')
        except:
            self.root.attributes('-zoomed', True)
        
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.root.bind('<Escape>', self.end_fullscreen)
        
        # Estado de la aplicación
        self.costo_actual = COSTO_BASELINE_DEFAULT
        self.costo_optimo = None
        self.modo_edicion = False
        self.ultimo_resultado = None
        
        # Variables para almacenar referencias a los Entry
        self.entry_vars = {}
        
        self.setup_fonts()
        self.create_widgets()
        self.cargar_valores_iniciales()
        self.bloquear_campos()
        
    def setup_fonts(self):
        """Configura fuentes para customtkinter y matplotlib"""
        self.font_title = ("Segoe UI", 24, "bold")
        self.font_subtitle = ("Segoe UI", 13)
        self.font_section = ("Segoe UI", 14, "bold")
        self.font_kpi_label = ("Segoe UI", 13, "bold")
        self.font_kpi_value = ("Segoe UI", 18, "bold")
        self.font_kpi_small = ("Segoe UI", 12)
        self.font_button = ("Segoe UI", 12, "bold")
        self.font_button_small = ("Segoe UI", 11)
        self.font_entry = ("Segoe UI", 12)
        self.font_tab = ("Segoe UI", 12, "bold")
        
        # Configurar matplotlib
        plt.rcParams['font.family'] = 'Segoe UI'
        plt.rcParams['font.size'] = 10
        
    def create_widgets(self):
        # Configurar grid principal
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # ========== BARRA SUPERIOR CORPORATIVA ==========
        self.header_frame = ctk.CTkFrame(
            self.root, 
            height=100, 
            corner_radius=0,
            fg_color=COLORS["NAVY"]
        )
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        # Logo + Título
        title_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w", padx=30, pady=15)
        
        ctk.CTkLabel(
            title_frame,
            text="MIP Retail Optimizer™ Enterprise",
            font=self.font_title,
            text_color=COLORS["WHITE"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_frame,
            text="Sistema de Optimización Logística y Diseño de Redes de Distribución",
            font=self.font_subtitle,
            text_color=COLORS["GRAY"]
        ).pack(anchor="w")
        
        # Estado central
        self.estado_label = ctk.CTkLabel(
            self.header_frame,
            text="🔒 Modo Protegido",
            font=("Segoe UI", 14, "bold"),
            text_color=COLORS["RED"],
            fg_color=COLORS["SLATE"],
            corner_radius=8,
            padx=20,
            pady=8
        )
        self.estado_label.grid(row=0, column=1, pady=15)
        
        # Botones derechos
        right_buttons = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        right_buttons.grid(row=0, column=2, sticky="e", padx=30, pady=15)
        
        self.licencia_btn = ctk.CTkButton(
            right_buttons,
            text="💼 Licencia y ROI",
            font=self.font_button,
            width=160,
            height=40,
            fg_color=COLORS["TEAL"],
            hover_color=COLORS["TEAL_HOVER"],
            command=self.mostrar_modal_roi
        )
        self.licencia_btn.pack(side="left", padx=5)
        
        # ========== CONTENEDOR PRINCIPAL DOS COLUMNAS ==========
        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_columnconfigure(0, weight=1, minsize=500)
        self.main_container.grid_columnconfigure(1, weight=2, minsize=800)
        self.main_container.grid_rowconfigure(0, weight=1)
        
        # ========== PANEL IZQUIERDO ==========
        self.left_panel = ctk.CTkFrame(self.main_container, fg_color=COLORS["SLATE"], corner_radius=12)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.left_panel.grid_rowconfigure(1, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)
        
        # Header panel izquierdo
        left_header = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        left_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        left_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            left_header,
            text="🎛️ Parámetros de Entrada",
            font=self.font_section,
            text_color=COLORS["WHITE"]
        ).grid(row=0, column=0, sticky="w")
        
        # Botones de control
        btn_frame = ctk.CTkFrame(left_header, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")
        
        self.edit_btn = ctk.CTkButton(
            btn_frame,
            text="🔓 Habilitar Edición",
            font=self.font_button,
            width=160,
            height=36,
            fg_color=COLORS["AMBER"],
            hover_color="#D97706",
            command=self.habilitar_edicion
        )
        self.edit_btn.pack(side="left", padx=5)
        
        self.confirm_btn = ctk.CTkButton(
            btn_frame,
            text="✅ Confirmar y Recalcular",
            font=self.font_button,
            width=180,
            height=36,
            fg_color=COLORS["TEAL"],
            hover_color=COLORS["TEAL_HOVER"],
            command=self.confirmar_y_recalcular
        )
        self.confirm_btn.pack(side="left", padx=5)
        self.confirm_btn.pack_forget()  # Oculto por defecto
        
        self.restore_btn = ctk.CTkButton(
            btn_frame,
            text="↩ Restaurar Valores Base",
            font=self.font_button,
            width=170,
            height=36,
            fg_color=COLORS["SLATE_LIGHT"],
            hover_color=COLORS["GRAY"],
            command=self.restaurar_valores_base
        )
        self.restore_btn.pack(side="left", padx=5)
        
        self.import_btn = ctk.CTkButton(
            btn_frame,
            text="📂 Importar Escenario",
            font=self.font_button,
            width=160,
            height=36,
            fg_color=COLORS["GRAY"],
            hover_color=COLORS["GRAY_LIGHT"],
            command=self.importar_escenario
        )
        self.import_btn.pack(side="left", padx=5)
        
        # Notebook con pestañas
        self.notebook = ctk.CTkTabview(
            self.left_panel,
            width=460,
            corner_radius=10,
            fg_color=COLORS["NAVY"],
            segmented_button_fg_color=COLORS["SLATE"],
            segmented_button_selected_color=COLORS["TEAL"],
            segmented_button_selected_hover_color=COLORS["TEAL_HOVER"],
            segmented_button_unselected_color=COLORS["SLATE_LIGHT"],
            segmented_button_unselected_hover_color=COLORS["SLATE"],
            text_color=COLORS["WHITE"],
            text_color_disabled=COLORS["GRAY"]
        )
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # --- Pestaña 1: Centros ---
        self.tab_cds = self.notebook.add("🏢 Centros")
        self.tab_cds.grid_columnconfigure(1, weight=1)
        self.tab_cds.grid_columnconfigure(2, weight=1)
        
        # Headers
        headers = ["Centro", "Costo Fijo (USD/mes)", "Capacidad (u/mes)"]
        for col, header in enumerate(headers):
            ctk.CTkLabel(
                self.tab_cds,
                text=header,
                font=("Segoe UI", 12, "bold"),
                text_color=COLORS["TEAL"]
            ).grid(row=0, column=col, padx=15, pady=12, sticky="ew")
        
        for i, ubicacion in enumerate(UBICACIONES_DEFAULT):
            row = i + 1
            ctk.CTkLabel(
                self.tab_cds,
                text=f"  {ubicacion}",
                font=("Segoe UI", 12, "bold"),
                text_color=COLORS["WHITE"],
                anchor="w"
            ).grid(row=row, column=0, padx=15, pady=8, sticky="w")
            
            entry_costo = ctk.CTkEntry(
                self.tab_cds,
                width=160,
                height=32,
                font=self.font_entry,
                fg_color=COLORS["SLATE"],
                border_color=COLORS["SLATE_LIGHT"],
                text_color=COLORS["WHITE"]
            )
            entry_costo.grid(row=row, column=1, padx=15, pady=8, sticky="ew")
            self.entry_vars[f'costo_fijo_{i}'] = entry_costo
            
            entry_cap = ctk.CTkEntry(
                self.tab_cds,
                width=160,
                height=32,
                font=self.font_entry,
                fg_color=COLORS["SLATE"],
                border_color=COLORS["SLATE_LIGHT"],
                text_color=COLORS["WHITE"]
            )
            entry_cap.grid(row=row, column=2, padx=15, pady=8, sticky="ew")
            self.entry_vars[f'capacidad_{i}'] = entry_cap
        
        # --- Pestaña 2: Demandas ---
        self.tab_demandas = self.notebook.add("📍 Demandas")
        self.tab_demandas.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            self.tab_demandas,
            text="Zona",
            font=("Segoe UI", 12, "bold"),
            text_color=COLORS["TEAL"]
        ).grid(row=0, column=0, padx=15, pady=12, sticky="w")
        ctk.CTkLabel(
            self.tab_demandas,
            text="Demanda (u/mes)",
            font=("Segoe UI", 12, "bold"),
            text_color=COLORS["TEAL"]
        ).grid(row=0, column=1, padx=15, pady=12, sticky="ew")
        
        for j, zona in enumerate(ZONAS_DEFAULT):
            row = j + 1
            ctk.CTkLabel(
                self.tab_demandas,
                text=f"  {zona}",
                font=("Segoe UI", 12),
                text_color=COLORS["WHITE"],
                anchor="w"
            ).grid(row=row, column=0, padx=15, pady=8, sticky="w")
            
            entry_dem = ctk.CTkEntry(
                self.tab_demandas,
                width=200,
                height=32,
                font=self.font_entry,
                fg_color=COLORS["SLATE"],
                border_color=COLORS["SLATE_LIGHT"],
                text_color=COLORS["WHITE"]
            )
            entry_dem.grid(row=row, column=1, padx=15, pady=8, sticky="ew")
            self.entry_vars[f'demanda_{j}'] = entry_dem
        
        # --- Pestaña 3: Configuración ---
        self.tab_config = self.notebook.add("⚙️ Configuración")
        self.tab_config.grid_columnconfigure(1, weight=1)
        
        config_items = [
            ("max_centros", "Máximo de CDs a abrir:", str(MAX_CENTROS_DEFAULT), "1-4"),
            ("baseline", "Costo Baseline (USD/mes):", f"{COSTO_BASELINE_DEFAULT:,}", "")
        ]
        
        for idx, (key, label, default, hint) in enumerate(config_items):
            ctk.CTkLabel(
                self.tab_config,
                text=label,
                font=("Segoe UI", 12),
                text_color=COLORS["WHITE"]
            ).grid(row=idx, column=0, padx=20, pady=20, sticky="w")
            
            entry = ctk.CTkEntry(
                self.tab_config,
                width=200,
                height=36,
                font=self.font_entry,
                fg_color=COLORS["SLATE"],
                border_color=COLORS["SLATE_LIGHT"],
                text_color=COLORS["WHITE"]
            )
            entry.grid(row=idx, column=1, padx=20, pady=20, sticky="ew")
            entry.insert(0, default)
            self.entry_vars[key] = entry
            
            if hint:
                ctk.CTkLabel(
                    self.tab_config,
                    text=hint,
                    font=("Segoe UI", 10),
                    text_color=COLORS["GRAY"]
                ).grid(row=idx, column=2, padx=10, sticky="w")
        
        # ========== PANEL DERECHO ==========
        self.right_panel = ctk.CTkFrame(self.main_container, fg_color=COLORS["SLATE"], corner_radius=12)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_rowconfigure(2, weight=1)
        
        # --- KPIs Superiores ---
        self.kpi_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.kpi_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.kpi_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        self.kpi_widgets = {}
        kpi_data = [
            ("💰 Costo Total Óptimo", "$182,500", COLORS["TEAL"]),
            ("💵 Ahorro Mensual", "$60,500 / 24.90%", COLORS["TEAL"]),
            ("🏢 Centros Activos", "L2, L3 (2/2)", COLORS["AMBER"]),
            ("✅ Nivel de Servicio", "100% Demanda", COLORS["TEAL"]),
        ]
        
        for i, (label, value, color) in enumerate(kpi_data):
            card = ctk.CTkFrame(self.kpi_frame, fg_color=COLORS["NAVY"], corner_radius=10)
            card.grid(row=0, column=i, sticky="ew", padx=5)
            card.grid_columnconfigure(0, weight=1)
            
            ctk.CTkLabel(
                card,
                text=label,
                font=("Segoe UI", 11),
                text_color=COLORS["GRAY"]
            ).pack(anchor="w", padx=15, pady=(12, 2))
            
            value_label = ctk.CTkLabel(
                card,
                text=value,
                font=("Segoe UI", 18, "bold"),
                text_color=color
            )
            value_label.pack(anchor="w", padx=15, pady=(0, 12))
            self.kpi_widgets[label] = value_label
        
        # --- Gráficos Duales ---
        self.charts_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.charts_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.charts_frame.grid_columnconfigure(0, weight=1)
        self.charts_frame.grid_columnconfigure(1, weight=1)
        self.charts_frame.grid_rowconfigure(0, weight=1)
        
        # Gráfico 1: Comparativa Baseline vs Óptimo
        self.chart1_frame = ctk.CTkFrame(self.charts_frame, fg_color=COLORS["NAVY"], corner_radius=10)
        self.chart1_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.chart1_frame.grid_rowconfigure(0, weight=1)
        self.chart1_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            self.chart1_frame,
            text="📊 Comparativa: Baseline vs. Optimizado",
            font=("Segoe UI", 12, "bold"),
            text_color=COLORS["TEAL"]
        ).grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")
        
        self.chart1_canvas_frame = ctk.CTkFrame(self.chart1_frame, fg_color="transparent")
        self.chart1_canvas_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.chart1_canvas_frame.grid_rowconfigure(0, weight=1)
        self.chart1_canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Gráfico 2: Desglose Costos + Utilización
        self.chart2_frame = ctk.CTkFrame(self.charts_frame, fg_color=COLORS["NAVY"], corner_radius=10)
        self.chart2_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.chart2_frame.grid_rowconfigure(0, weight=1)
        self.chart2_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            self.chart2_frame,
            text="📈 Desglose de Costos y Utilización",
            font=("Segoe UI", 12, "bold"),
            text_color=COLORS["TEAL"]
        ).grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")
        
        self.chart2_canvas_frame = ctk.CTkFrame(self.chart2_frame, fg_color="transparent")
        self.chart2_canvas_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.chart2_canvas_frame.grid_rowconfigure(0, weight=1)
        self.chart2_canvas_frame.grid_columnconfigure(0, weight=1)
        
        # --- Tabla de Asignación + Exportación ---
        self.table_frame = ctk.CTkFrame(self.right_panel, fg_color=COLORS["NAVY"], corner_radius=10)
        self.table_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 20))
        self.table_frame.grid_columnconfigure(0, weight=1)
        self.table_frame.grid_rowconfigure(1, weight=1)
        
        table_header = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        table_header.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        table_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            table_header,
            text="📋 Plan de Asignación Logística (Centro → Zona)",
            font=("Segoe UI", 13, "bold"),
            text_color=COLORS["WHITE"]
        ).grid(row=0, column=0, sticky="w")
        
        self.export_btn = ctk.CTkButton(
            table_header,
            text="📊 Exportar Reporte Ejecutivo",
            font=self.font_button,
            width=200,
            height=36,
            fg_color=COLORS["TEAL"],
            hover_color=COLORS["TEAL_HOVER"],
            command=self.exportar_reporte_ejecutivo
        )
        self.export_btn.grid(row=0, column=1, sticky="e")
        
        # Treeview estilizado
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Custom.Treeview",
            background=COLORS["NAVY"],
            foreground=COLORS["WHITE"],
            fieldbackground=COLORS["NAVY"],
            font=("Segoe UI", 11),
            rowheight=36,
            borderwidth=0
        )
        style.configure(
            "Custom.Treeview.Heading",
            background=COLORS["TEAL"],
            foreground=COLORS["WHITE"],
            font=("Segoe UI", 11, "bold"),
            relief="flat"
        )
        style.map(
            "Custom.Treeview",
            background=[("selected", COLORS["TEAL"])],
            foreground=[("selected", COLORS["WHITE"])]
        )
        
        tree_container = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        tree_container.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        tree_container.grid_columnconfigure(0, weight=1)
        tree_container.grid_rowconfigure(0, weight=1)
        
        columns = ("Ubicacion", "Zona", "Cantidad_Enviada")
        self.tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show="headings",
            style="Custom.Treeview"
        )
        
        self.tree.heading("Ubicacion", text="Centro de Distribución", anchor="center")
        self.tree.heading("Zona", text="Zona Urbana", anchor="center")
        self.tree.heading("Cantidad_Enviada", text="Unidades Enviadas", anchor="center")
        
        self.tree.column("Ubicacion", width=250, anchor="center")
        self.tree.column("Zona", width=250, anchor="center")
        self.tree.column("Cantidad_Enviada", width=250, anchor="center")
        
        v_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        # Cargar datos iniciales
        self.load_csv_data()
        self.crear_graficos()
        
    def cargar_valores_iniciales(self):
        """Carga los valores por defecto en todos los campos Entry"""
        for i, costo in enumerate(COSTOS_FIJOS_DEFAULT):
            self.entry_vars[f'costo_fijo_{i}'].delete(0, "end")
            self.entry_vars[f'costo_fijo_{i}'].insert(0, f"{costo:,}")
        
        for i, cap in enumerate(CAPACIDADES_DEFAULT):
            self.entry_vars[f'capacidad_{i}'].delete(0, "end")
            self.entry_vars[f'capacidad_{i}'].insert(0, f"{cap:,}")
        
        for j, dem in enumerate(DEMANDA_DEFAULT):
            self.entry_vars[f'demanda_{j}'].delete(0, "end")
            self.entry_vars[f'demanda_{j}'].insert(0, f"{dem:,}")
        
        self.entry_vars['max_centros'].delete(0, "end")
        self.entry_vars['max_centros'].insert(0, str(MAX_CENTROS_DEFAULT))
        
        self.entry_vars['baseline'].delete(0, "end")
        self.entry_vars['baseline'].insert(0, f"{COSTO_BASELINE_DEFAULT:,}")
        
    def bloquear_campos(self):
        """Bloquea todos los campos Entry en modo solo lectura"""
        for entry in self.entry_vars.values():
            entry.configure(state="disabled")
        self.modo_edicion = False
        self.estado_label.configure(text="🔒 Modo Protegido", text_color=COLORS["RED"])
        self.edit_btn.pack(side="left", padx=5)
        self.confirm_btn.pack_forget()
        
    def desbloquear_campos(self):
        """Desbloquea todos los campos Entry para edición"""
        for entry in self.entry_vars.values():
            entry.configure(state="normal")
        self.modo_edicion = True
        self.estado_label.configure(text="✏️ Modo Edición Activo", text_color=COLORS["TEAL"])
        self.edit_btn.pack_forget()
        self.confirm_btn.pack(side="left", padx=5)
        
    def habilitar_edicion(self):
        """Muestra confirmación y habilita modo edición"""
        if messagebox.askyesno(
            "Confirmar Edición",
            "¿Deseas desbloquear los parámetros del modelo para realizar una simulación personalizada?",
            icon="question"
        ):
            self.desbloquear_campos()
        
    def confirmar_y_recalcular(self):
        """Valida, confirma y recalcula con nuevos parámetros"""
        try:
            costos_fijos, capacidades, demandas, max_centros, baseline = self.leer_parametros_ui()
        except ValueError as e:
            messagebox.showerror("Error de Validación", str(e))
            return
        
        if not messagebox.askyesno(
            "Confirmar Simulación",
            "¿Confirmas recalcular el modelo con los nuevos parámetros personalizados?\n\n"
            "Esto actualizará los KPIs, gráficos y tabla de asignación.",
            icon="question"
        ):
            return
        
        self.ejecutar_optimizacion(costos_fijos, capacidades, demandas, max_centros, baseline)
        
        # Bloquear nuevamente tras confirmación exitosa
        self.bloquear_campos()
        
    def restaurar_valores_base(self):
        """Restaura todos los campos a los valores originales con confirmación"""
        if messagebox.askyesno(
            "Confirmar Restauración",
            "¿Estás seguro de restaurar todos los parámetros a los valores oficiales del estudio?",
            icon="question"
        ):
            self.cargar_valores_iniciales()
            self.bloquear_campos()
            # Recalcular automáticamente el óptimo oficial
            self.run_optimization_silencioso()
            messagebox.showinfo(
                "Valores Restaurados", 
                "Todos los parámetros han sido restablecidos a los valores base del caso de estudio.\n"
                "El modelo se ha recalculado automáticamente ($182,500 USD / 24.90% ahorro)."
            )
    
    def importar_escenario(self):
        """Importa parámetros desde archivo CSV o Excel"""
        file_path = filedialog.askopenfilename(
            title="Importar Escenario",
            filetypes=[
                ("Archivos CSV", "*.csv"),
                ("Archivos Excel", "*.xlsx"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Validar columnas requeridas
            required_cols = ['parametro', 'valor']
            if not all(col in df.columns for col in required_cols):
                raise ValueError("El archivo debe contener columnas 'parametro' y 'valor'")
            
            # Aplicar parámetros
            params_dict = dict(zip(df['parametro'], df['valor']))
            
            # Mapear parámetros a campos
            mapping = {
                **{f'costo_fijo_{i}': f'costo_fijo_{i}' for i in range(len(UBICACIONES_DEFAULT))},
                **{f'capacidad_{i}': f'capacidad_{i}' for i in range(len(UBICACIONES_DEFAULT))},
                **{f'demanda_{j}': f'demanda_{j}' for j in range(len(ZONAS_DEFAULT))},
                'max_centros': 'max_centros',
                'baseline': 'baseline'
            }
            
            for param_key, entry_key in mapping.items():
                if param_key in params_dict and entry_key in self.entry_vars:
                    val = params_dict[param_key]
                    if entry_key in self.entry_vars:
                        self.entry_vars[entry_key].configure(state="normal")
                        self.entry_vars[entry_key].delete(0, "end")
                        self.entry_vars[entry_key].insert(0, str(val))
                        self.entry_vars[entry_key].configure(state="disabled" if not self.modo_edicion else "normal")
            
            messagebox.showinfo("Importación Exitosa", 
                f"Se importaron {len(params_dict)} parámetros correctamente.\n"
                "Habilita edición para modificarlos si es necesario.")
            
        except Exception as e:
            messagebox.showerror("Error al Importar", f"No se pudo importar el escenario:\n{str(e)}")
    
    def run_optimization_silencioso(self):
        """Ejecuta optimización sin interacción para restaurar valores base"""
        try:
            resultado = resolver_modelo()
            if resultado['estado'] == 'Optimal':
                self.actualizar_kpis_y_resultados(resultado)
        except Exception as e:
            print(f"Error en recálculo silencioso: {e}")
    
    def leer_parametros_ui(self):
        """Lee y valida los parámetros desde los campos Entry"""
        try:
            costos_fijos = []
            for i in range(len(UBICACIONES_DEFAULT)):
                val = self.entry_vars[f'costo_fijo_{i}'].get().replace(',', '').replace('.', '')
                if not val:
                    raise ValueError(f"Costo fijo {UBICACIONES_DEFAULT[i]} está vacío")
                costos_fijos.append(int(val))
            
            capacidades = []
            for i in range(len(UBICACIONES_DEFAULT)):
                val = self.entry_vars[f'capacidad_{i}'].get().replace(',', '').replace('.', '')
                if not val:
                    raise ValueError(f"Capacidad {UBICACIONES_DEFAULT[i]} está vacía")
                capacidades.append(int(val))
            
            demandas = []
            for j in range(len(ZONAS_DEFAULT)):
                val = self.entry_vars[f'demanda_{j}'].get().replace(',', '').replace('.', '')
                if not val:
                    raise ValueError(f"Demanda {ZONAS_DEFAULT[j]} está vacía")
                demandas.append(int(val))
            
            max_centros = int(self.entry_vars['max_centros'].get())
            baseline = int(self.entry_vars['baseline'].get().replace(',', '').replace('.', ''))
            
            # Validaciones
            if max_centros < 1 or max_centros > len(UBICACIONES_DEFAULT):
                raise ValueError(f"Máximo de CDs debe estar entre 1 y {len(UBICACIONES_DEFAULT)}")
            
            if any(c < 0 for c in costos_fijos):
                raise ValueError("Los costos fijos no pueden ser negativos")
            if any(c <= 0 for c in capacidades):
                raise ValueError("Las capacidades deben ser positivas")
            if any(d < 0 for d in demandas):
                raise ValueError("Las demandas no pueden ser negativas")
            if baseline <= 0:
                raise ValueError("El costo baseline debe ser positivo")
            
            return costos_fijos, capacidades, demandas, max_centros, baseline
            
        except ValueError as e:
            raise ValueError(f"Parámetro inválido: {str(e)}")
    
    def ejecutar_optimizacion(self, costos_fijos, capacidades, demandas, max_centros, baseline):
        """Ejecuta la optimización y actualiza la UI"""
        self.costo_actual = baseline
        self.root.configure(cursor="watch")
        self.root.update()
        
        try:
            resultado = resolver_modelo(
                costos_fijos=costos_fijos,
                capacidades=capacidades,
                demandas=demandas,
                costos_envio=COSTOS_ENVIO_DEFAULT,
                max_centros=max_centros,
                zonas=ZONAS_DEFAULT,
                ubicaciones=UBICACIONES_DEFAULT,
                costo_baseline=baseline
            )
            
            if resultado['estado'] == 'Optimal':
                self.actualizar_kpis_y_resultados(resultado)
                messagebox.showinfo(
                    "Simulación Completada",
                    f"Simulación actualizada y bloqueada correctamente.\n\n"
                    f"Nuevo Costo Total Óptimo: ${resultado['costo_total']:,.0f}\n"
                    f"Ahorro: ${resultado['ahorro']:,.0f} ({resultado['porcentaje_ahorro']:.2f}%)\n"
                    f"Centros: {', '.join(resultado['centros_abiertos'])}"
                )
            else:
                messagebox.showerror("Error en Optimización", 
                    f"Estado: {resultado['estado']}\n{resultado['mensaje']}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")
        finally:
            self.root.configure(cursor="")
        
    def actualizar_kpis_y_resultados(self, resultado):
        """Actualiza KPIs, gráficos y tabla con resultados"""
        self.ultimo_resultado = resultado
        self.costo_optimo = resultado['costo_total']
        self.costo_actual = resultado.get('costo_baseline', COSTO_BASELINE_DEFAULT)
        
        # Actualizar KPIs
        self.kpi_widgets["💰 Costo Total Óptimo"].configure(text=f"${resultado['costo_total']:,.0f}")
        self.kpi_widgets["💵 Ahorro Mensual"].configure(text=f"${resultado['ahorro']:,.0f} / {resultado['porcentaje_ahorro']:.2f}%")
        self.kpi_widgets["🏢 Centros Activos"].configure(text=f"{', '.join(resultado['centros_abiertos'])} ({len(resultado['centros_abiertos'])}/2)")
        
        # Actualizar gráficos
        self.crear_graficos()
        
        # Actualizar tabla
        self.load_csv_data_from_result(resultado['asignaciones'])
        
        # Guardar CSV
        df = pd.DataFrame(resultado['asignaciones'])
        df.to_csv('asignacion_logistica.csv', index=False)
    
    def crear_graficos(self):
        """Crea ambos gráficos con estilo corporativo"""
        # Limpiar frames
        for widget in self.chart1_canvas_frame.winfo_children():
            widget.destroy()
        for widget in self.chart2_canvas_frame.winfo_children():
            widget.destroy()
        
        # Estilo matplotlib corporativo
        plt.style.use('dark_background')
        BG_COLOR = '#0F172A'
        CARD_COLOR = '#1E293B'
        TEAL = '#10B981'
        RED = '#EF4444'
        AMBER = '#F59E0B'
        GRAY = '#64748B'
        
        # --- GRÁFICO 1: Comparativa Baseline vs Óptimo ---
        fig1, ax1 = plt.subplots(figsize=(5.5, 3.8), dpi=100)
        fig1.patch.set_facecolor(BG_COLOR)
        ax1.set_facecolor(CARD_COLOR)
        
        labels = ['Baseline\n(Actual)', 'Optimizado\n(Nuevo)']
        values = [self.costo_actual, self.costo_optimo or 0]
        colors = [RED, TEAL]
        
        bars = ax1.bar(labels, values, color=colors, edgecolor='white', linewidth=1.5, width=0.6)
        
        for bar, val in zip(bars, values):
            if val > 0:
                ax1.annotate(f'${val:,.0f}',
                           xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                           xytext=(0, 8),
                           textcoords="offset points",
                           ha='center', va='bottom',
                           fontweight='bold', fontsize=12, color='white')
        
        ax1.set_ylabel('USD', fontsize=11, fontweight='bold', color='white')
        ax1.set_title('Costo Logístico Mensual: Baseline vs. Optimizado', 
                     fontsize=12, fontweight='bold', pad=15, color='white')
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['left'].set_color(GRAY)
        ax1.spines['bottom'].set_color(GRAY)
        ax1.tick_params(axis='x', colors='white', labelsize=10)
        ax1.tick_params(axis='y', colors='white', labelsize=10)
        ax1.grid(axis='y', alpha=0.2, color=GRAY)
        ax1.set_ylim(0, max(values) * 1.25 if max(values) > 0 else 300000)
        
        if self.costo_optimo:
            ahorro = self.costo_actual - self.costo_optimo
            pct = (ahorro / self.costo_actual) * 100
            ax1.text(0.5, 0.92, f'Ahorro: ${ahorro:,.0f} ({pct:.1f}%)',
                   transform=ax1.transAxes, ha='center', va='top',
                   fontsize=11, fontweight='bold', color=TEAL,
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='#064E3B', edgecolor=TEAL))
        
        plt.tight_layout()
        
        canvas1 = FigureCanvasTkAgg(fig1, master=self.chart1_canvas_frame)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill="both", expand=True)
        
        # --- GRÁFICO 2: Desglose Costos + Utilización ---
        fig2, (ax2a, ax2b) = plt.subplots(2, 1, figsize=(5.5, 5.2), dpi=100)
        fig2.patch.set_facecolor(BG_COLOR)
        
        # Subplot 2a: Desglose Fijo vs Variable (Donut)
        ax2a.set_facecolor(CARD_COLOR)
        if self.ultimo_resultado:
            fijo = self.ultimo_resultado['costo_fijo']
            variable = self.ultimo_resultado['costo_variable']
            labels2 = ['Costo Fijo', 'Costo Variable']
            values2 = [fijo, variable]
            colors2 = [TEAL, AMBER]
            
            wedges, texts, autotexts = ax2a.pie(
                values2, labels=labels2, colors=colors2,
                autopct='%1.1f%%', startangle=90,
                textprops={'fontsize': 10, 'color': 'white', 'fontweight': 'bold'},
                wedgeprops=dict(width=0.5, edgecolor='white', linewidth=1.5)
            )
            for autotext in autotexts:
                autotext.set_fontsize(11)
                autotext.set_fontweight('bold')
            ax2a.set_title('Desglose: Costo Fijo vs. Variable', 
                          fontsize=12, fontweight='bold', pad=10, color='white')
        else:
            ax2a.text(0.5, 0.5, 'Ejecute una optimización', ha='center', va='center', color='white', fontsize=12)
            ax2a.set_title('Desglose: Costo Fijo vs. Variable', fontsize=12, fontweight='bold', pad=10, color='white')
        
        # Subplot 2b: Utilización de Capacidad por Centro
        ax2b.set_facecolor(CARD_COLOR)
        if self.ultimo_resultado:
            centros_abiertos = self.ultimo_resultado['centros_abiertos']
            asignaciones = self.ultimo_resultado['asignaciones']
            
            # Calcular volumen por centro
            vol_por_centro = {}
            for a in asignaciones:
                c = a['Ubicacion']
                vol_por_centro[c] = vol_por_centro.get(c, 0) + a['Cantidad_Enviada']
            
            centros_labels = []
            util_labels = []
            util_values = []
            cap_values = []
            
            for c in UBICACIONES_DEFAULT:
                if c in centros_abiertos:
                    idx = UBICACIONES_DEFAULT.index(c)
                    vol = vol_por_centro.get(c, 0)
                    cap = CAPACIDADES_DEFAULT[idx]
                    util = (vol / cap) * 100 if cap > 0 else 0
                    centros_labels.append(c)
                    util_labels.append(f"{util:.0f}%")
                    util_values.append(util)
                    cap_values.append(cap)
            
            y_pos = range(len(centros_labels))
            bars = ax2b.barh(y_pos, util_values, color=TEAL, edgecolor='white', height=0.6)
            ax2b.set_yticks(y_pos)
            ax2b.set_yticklabels([f"{c} ({v:,.0f}/{c_cap:,.0f})" for c, v, c_cap in zip(centros_labels, [vol_por_centro.get(c,0) for c in centros_labels], cap_values)], 
                                fontsize=10, color='white')
            ax2b.set_xlim(0, 100)
            ax2b.set_xlabel('Utilización (%)', fontsize=10, color='white')
            ax2b.set_title('Utilización de Capacidad por Centro', fontsize=12, fontweight='bold', pad=10, color='white')
            
            # Colorear barras según utilización
            for bar, val in zip(bars, util_values):
                if val > 85:
                    bar.set_color(RED)
                elif val > 70:
                    bar.set_color(AMBER)
                else:
                    bar.set_color(TEAL)
                
                ax2b.annotate(f'{val:.0f}%',
                            xy=(bar.get_width(), bar.get_y() + bar.get_height()/2),
                            xytext=(5, 0),
                            textcoords="offset points",
                            ha='left', va='center',
                            fontweight='bold', fontsize=10, color='white')
        else:
            ax2b.text(0.5, 0.5, 'Ejecute una optimización', ha='center', va='center', color='white', fontsize=12)
            ax2b.set_title('Utilización de Capacidad por Centro', fontsize=12, fontweight='bold', pad=10, color='white')
        
        for ax in [ax2a, ax2b]:
            ax.set_facecolor(CARD_COLOR)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color(GRAY)
            ax.spines['bottom'].set_color(GRAY)
            ax.tick_params(colors='white')
        
        plt.tight_layout()
        
        canvas2 = FigureCanvasTkAgg(fig2, master=self.chart2_canvas_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill="both", expand=True)
    
    def load_csv_data(self):
        """Carga inicial desde archivo CSV si existe"""
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "asignacion_logistica.csv")
        
        try:
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                self.load_csv_data_from_result(df.to_dict('records'))
            else:
                self.run_optimization_silencioso()
        except Exception as e:
            print(f"Error cargando CSV: {e}")
            self.run_optimization_silencioso()
    
    def load_csv_data_from_result(self, asignaciones):
        """Carga datos en Treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for a in asignaciones:
            self.tree.insert("", "end", values=(
                a['Ubicacion'],
                a['Zona'],
                f"{a['Cantidad_Enviada']:,.0f}"
            ))
    
    def exportar_reporte_ejecutivo(self):
        """Exporta reporte ejecutivo completo a Excel y CSV"""
        if not self.ultimo_resultado:
            messagebox.showwarning("Sin Datos", "No hay resultados para exportar. Ejecute una optimización primero.")
            return
        
        # Diálogo para guardar
        file_path = filedialog.asksaveasfilename(
            title="Guardar Reporte Ejecutivo",
            defaultextension=".xlsx",
            filetypes=[
                ("Excel Workbook", "*.xlsx"),
                ("CSV", "*.csv"),
                ("Todos", "*.*")
            ],
            initialfile="Reporte_Ejecutivo_MIP_Retail_Optimizer.xlsx"
        )
        
        if not file_path:
            return
        
        try:
            if file_path.endswith('.xlsx'):
                self.crear_excel_ejecutivo(file_path)
            else:
                self.crear_csv_ejecutivo(file_path)
            
            messagebox.showinfo("Exportación Exitosa", 
                f"Reporte ejecutivo generado correctamente:\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("Error al Exportar", f"No se pudo generar el reporte:\n{str(e)}")
    
    def crear_excel_ejecutivo(self, file_path):
        """Crea reporte Excel multi-hoja profesional"""
        wb = openpyxl.Workbook()
        
        # Estilos
        header_font = Font(name='Calibri', bold=True, size=12, color='FFFFFF')
        header_fill = PatternFill(start_color='0F172A', end_color='0F172A', fill_type='solid')
        header_alignment = Alignment(horizontal='center', vertical='center')
        title_font = Font(name='Calibri', bold=True, size=16, color='0F172A')
        subtitle_font = Font(name='Calibri', bold=True, size=12, color='1E293B')
        normal_font = Font(name='Calibri', size=11)
        money_font = Font(name='Calibri', bold=True, size=11, color='10B981')
        thin_border = Border(
            left=Side(style='thin', color='CCCCCC'),
            right=Side(style='thin', color='CCCCCC'),
            top=Side(style='thin', color='CCCCCC'),
            bottom=Side(style='thin', color='CCCCCC')
        )
        
        # ========== HOJA 1: RESUMEN EJECUTIVO ==========
        ws1 = wb.active
        ws1.title = "Resumen Ejecutivo"
        
        # Título
        ws1.merge_cells('A1:D1')
        ws1['A1'] = "MIP Retail Optimizer™ Enterprise - Reporte de Optimización"
        ws1['A1'].font = title_font
        ws1['A1'].alignment = Alignment(horizontal='center')
        
        ws1.merge_cells('A2:D2')
        ws1['A2'] = "Sistema de Optimización Logística y Diseño de Redes de Distribución"
        ws1['A2'].font = subtitle_font
        ws1['A2'].alignment = Alignment(horizontal='center')
        
        # KPIs principales
        r = self.ultimo_resultado
        kpis = [
            ("Costo Total Óptimo", f"${r['costo_total']:,.0f} USD", '10B981'),
            ("Costo Fijo Óptimo", f"${r['costo_fijo']:,.0f} USD", '10B981'),
            ("Costo Variable Óptimo", f"${r['costo_variable']:,.0f} USD", '10B981'),
            ("Ahorro Mensual vs Baseline", f"${r['ahorro']:,.0f} USD ({r['porcentaje_ahorro']:.2f}%)", '10B981'),
            ("Costo Baseline (Actual)", f"${self.costo_actual:,.0f} USD", 'EF4444'),
            ("Centros Activos", f"{', '.join(r['centros_abiertos'])} ({len(r['centros_abiertos'])}/2)", 'F59E0B'),
            ("Nivel de Servicio", "100% Demanda Cubierta", '10B981'),
        ]
        
        row = 4
        for label, value, color in kpis:
            ws1[f'A{row}'] = label
            ws1[f'A{row}'].font = Font(name='Calibri', bold=True, size=12, color=color)
            ws1[f'B{row}'] = value
            ws1[f'B{row}'].font = Font(name='Calibri', bold=True, size=12, color=color)
            ws1[f'A{row}'].border = thin_border
            ws1[f'B{row}'].border = thin_border
            ws1.merge_cells(f'C{row}:D{row}')
            row += 1
        
        # Detalle de centros
        row += 1
        ws1[f'A{row}'] = "DETALLE DE CENTROS ACTIVOS"
        ws1[f'A{row}'].font = Font(name='Calibri', bold=True, size=13, color='0F172A')
        
        row += 1
        for col, header in enumerate(['Centro', 'Costo Fijo (USD)', 'Capacidad (u)', 'Volumen Asignado (u)', 'Utilización (%)'], 1):
            cell = ws1.cell(row=row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
        
        for c in r['centros_abiertos']:
            idx = UBICACIONES_DEFAULT.index(c)
            cap = CAPACIDADES_DEFAULT[idx]
            costo_f = COSTOS_FIJOS_DEFAULT[idx]
            vol = sum(a['Cantidad_Enviada'] for a in r['asignaciones'] if a['Ubicacion'] == c)
            util = (vol / cap * 100) if cap > 0 else 0
            
            row += 1
            for col, val in enumerate([c, f"${costo_f:,.0f}", f"{cap:,}", f"{vol:,.0f}", f"{util:.1f}%"], 1):
                cell = ws1.cell(row=row, column=col, value=val)
                cell.font = normal_font
                cell.alignment = Alignment(horizontal='center')
                cell.border = thin_border
        
        # Ajustar anchos
        for col in range(1, 5):
            ws1.column_dimensions[get_column_letter(col)].width = 25
        
        # ========== HOJA 2: KPIs DETALLADOS ==========
        ws2 = wb.create_sheet("KPIs Detallados")
        
        # Matriz de costos
        headers = ['Métrica', 'Valor', 'Unidad']
        for col, h in enumerate(headers, 1):
            cell = ws2.cell(row=1, column=col, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
        
        kpi_detalle = [
            ("Costo Fijo Óptimo", r['costo_fijo'], "USD"),
            ("Costo Variable Óptimo", r['costo_variable'], "USD"),
            ("Costo Total Óptimo", r['costo_total'], "USD"),
            ("Baseline (Costo Actual)", self.costo_actual, "USD"),
            ("Ahorro Mensual", r['ahorro'], "USD"),
            ("Reducción Porcentual", r['porcentaje_ahorro'], "%"),
            ("Número de Centros Activos", len(r['centros_abiertos']), "Unidades"),
            ("Máximo Centros Permitidos", MAX_CENTROS_DEFAULT, "Unidades"),
            ("Demanda Total", sum(DEMANDA_DEFAULT), "Unidades/mes"),
            ("Capacidad Total Activa", sum(CAPACIDADES_DEFAULT[i] for i, c in enumerate(UBICACIONES_DEFAULT) if c in r['centros_abiertos']), "Unidades/mes"),
        ]
        
        for i, (metrica, valor, unidad) in enumerate(kpi_detalle, 2):
            ws2.cell(row=i, column=1, value=metrica).font = normal_font
            ws2.cell(row=i, column=2, value=valor).font = normal_font
            ws2.cell(row=i, column=3, value=unidad).font = normal_font
            for c in range(1, 4):
                ws2.cell(row=i, column=c).border = thin_border
                ws2.cell(row=i, column=c).alignment = Alignment(horizontal='center')
        
        for col in range(1, 4):
            ws2.column_dimensions[get_column_letter(col)].width = 35
        
        # ========== HOJA 3: MATRIZ DE ASIGNACIÓN LOGÍSTICA ==========
        ws3 = wb.create_sheet("Matriz Asignación")
        
        # Crear matriz pivote
        centros_ordenados = [c for c in UBICACIONES_DEFAULT if c in r['centros_abiertos']]
        
        headers = ['Zona'] + centros_ordenados + ['Total']
        for col, h in enumerate(headers, 1):
            cell = ws3.cell(row=1, column=col, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
        
        # Llenar matriz
        for j, zona in enumerate(ZONAS_DEFAULT, 2):
            ws3.cell(row=j, column=1, value=zona).font = normal_font
            ws3.cell(row=j, column=1).border = thin_border
            ws3.cell(row=j, column=1).alignment = Alignment(horizontal='center')
            
            total_zona = 0
            for i, centro in enumerate(centros_ordenados):
                val = sum(a['Cantidad_Enviada'] for a in r['asignaciones'] 
                         if a['Zona'] == zona and a['Ubicacion'] == centro)
                cell = ws3.cell(row=j, column=i+2, value=val if val > 0 else 0)
                cell.font = normal_font
                cell.alignment = Alignment(horizontal='center')
                cell.border = thin_border
                total_zona += val
            
            # Total zona
            cell = ws3.cell(row=j, column=len(headers), value=total_zona)
            cell.font = Font(name='Calibri', bold=True, size=11, color='10B981')
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border
        
        # Fila totales por centro
        row_total = len(ZONAS_DEFAULT) + 2
        ws3.cell(row=row_total, column=1, value="TOTAL CENTRO").font = Font(name='Calibri', bold=True, size=11, color='0F172A')
        ws3.cell(row=row_total, column=1).border = thin_border
        
        for i, centro in enumerate(centros_ordenados):
            total_c = sum(a['Cantidad_Enviada'] for a in r['asignaciones'] if a['Ubicacion'] == centro)
            cell = ws3.cell(row=row_total, column=i+2, value=total_c)
            cell.font = Font(name='Calibri', bold=True, size=11, color='10B981')
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border
        
        # Gran total
        gran_total = sum(a['Cantidad_Enviada'] for a in r['asignaciones'])
        cell = ws3.cell(row=row_total, column=len(headers), value=gran_total)
        cell.font = Font(name='Calibri', bold=True, size=12, color='10B981')
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border
        
        for col in range(1, len(headers)+1):
            ws3.column_dimensions[get_column_letter(col)].width = 18
        
        # ========== HOJA 4: PARÁMETROS DEL ESCENARIO ==========
        ws4 = wb.create_sheet("Parámetros Escenario")
        
        headers = ['Parámetro', 'Valor']
        for col, h in enumerate(headers, 1):
            cell = ws4.cell(row=1, column=col, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
        
        params = []
        for i, c in enumerate(UBICACIONES_DEFAULT):
            params.append((f"Costo Fijo {c} (USD/mes)", COSTOS_FIJOS_DEFAULT[i]))
            params.append((f"Capacidad {c} (u/mes)", CAPACIDADES_DEFAULT[i]))
        for j, z in enumerate(ZONAS_DEFAULT):
            params.append((f"Demanda {z} (u/mes)", DEMANDA_DEFAULT[j]))
        params.append(("Máximo CDs a abrir", MAX_CENTROS_DEFAULT))
        params.append(("Costo Baseline (USD/mes)", self.costo_actual))
        params.append(("Matriz Costos Envío", "Ver Anexo Técnico"))
        
        for i, (param, val) in enumerate(params, 2):
            ws4.cell(row=i, column=1, value=param).font = normal_font
            ws4.cell(row=i, column=2, value=val).font = normal_font
            for c in range(1, 3):
                ws4.cell(row=i, column=c).border = thin_border
                ws4.cell(row=i, column=c).alignment = Alignment(horizontal='center')
        
        ws4.column_dimensions['A'].width = 40
        ws4.column_dimensions['B'].width = 25
        
        # Guardar
        wb.save(file_path)
    
    def crear_csv_ejecutivo(self, file_path):
        """Crea CSV simplificado con datos principales"""
        r = self.ultimo_resultado
        
        # Crear DataFrame con KPIs
        kpi_df = pd.DataFrame([
            ['Métrica', 'Valor', 'Unidad'],
            ['Costo Total Óptimo', r['costo_total'], 'USD'],
            ['Costo Fijo Óptimo', r['costo_fijo'], 'USD'],
            ['Costo Variable Óptimo', r['costo_variable'], 'USD'],
            ['Ahorro Mensual', r['ahorro'], 'USD'],
            ['Reducción Porcentual', r['porcentaje_ahorro'], '%'],
            ['Centros Activos', ', '.join(r['centros_abiertos']), ''],
            ['Nivel de Servicio', '100%', ''],
        ])
        
        kpi_df.to_csv(file_path, index=False, header=False)
    
    def mostrar_modal_roi(self):
        """Muestra modal ejecutivo con propuesta de valor y ROI"""
        modal = ctk.CTkToplevel(self.root)
        modal.title("💼 Licencia y ROI - MIP Retail Optimizer™ Enterprise")
        modal.geometry("700x650")
        modal.resizable(False, False)
        modal.transient(self.root)
        modal.grab_set()
        modal.configure(fg_color=COLORS["NAVY"])
        
        # Centrar modal
        modal.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 700) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 650) // 2
        modal.geometry(f"+{x}+{y}")
        
        # Scrollable frame
        scroll = ctk.CTkScrollableFrame(modal, fg_color=COLORS["NAVY"], corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Título
        ctk.CTkLabel(
            scroll,
            text="MIP Retail Optimizer™ Enterprise",
            font=("Segoe UI", 24, "bold"),
            text_color=COLORS["TEAL"]
        ).pack(anchor="w", pady=(0, 5))
        
        ctk.CTkLabel(
            scroll,
            text="Sistema de Optimización Logística y Diseño de Redes de Distribución",
            font=("Segoe UI", 13),
            text_color=COLORS["GRAY"]
        ).pack(anchor="w", pady=(0, 20))
        
        # ROI Box
        roi_frame = ctk.CTkFrame(scroll, fg_color=COLORS["SLATE"], corner_radius=12)
        roi_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            roi_frame,
            text="💰 RETORNO DE INVERSIÓN (ROI) ESTIMADO",
            font=("Segoe UI", 16, "bold"),
            text_color=COLORS["TEAL"]
        ).pack(anchor="w", padx=20, pady=(20, 15))
        
        roi_metrics = [
            ("Ahorro Mensual", "$60,500 USD"),
            ("Ahorro Anual", "$726,000 USD"),
            ("Reducción de Costos", "24.90%"),
            ("ROI Primer Año", "> 300%"),
            ("Payback Estimado", "< 3 meses"),
        ]
        
        for label, value in roi_metrics:
            row = ctk.CTkFrame(roi_frame, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(row, text=label, font=("Segoe UI", 12), text_color=COLORS["GRAY"]).pack(side="left", padx=20)
            ctk.CTkLabel(row, text=value, font=("Segoe UI", 13, "bold"), text_color=COLORS["TEAL"]).pack(side="right", padx=20)
        
        ctk.CTkLabel(
            roi_frame,
            text="*Basado en caso de estudio real: Baseline $243,000/mes → Optimizado $182,500/mes",
            font=("Segoe UI", 10),
            text_color=COLORS["GRAY"]
        ).pack(anchor="w", padx=20, pady=(10, 20))
        
        # Beneficios
        ctk.CTkLabel(
            scroll,
            text="✨ BENEFICIOS CLAVE",
            font=("Segoe UI", 16, "bold"),
            text_color=COLORS["TEAL"]
        ).pack(anchor="w", pady=(20, 10))
        
        beneficios = [
            "Optimización matemática rigurosa (MIP) con optimalidad garantizada",
            "Análisis de sensibilidad en tiempo real (what-if scenarios)",
            "Interfaz ejecutiva con dashboard KPIs y reportes listos para gerencia",
            "Importación/Exportación de escenarios (CSV/Excel)",
            "Pantalla completa, modo protegido por defecto, listo para demo en vivo",
            "Ejecutable standalone Windows (.exe) sin dependencias de Python",
        ]
        
        for b in beneficios:
            ctk.CTkLabel(
                scroll,
                text=f"  ✓  {b}",
                font=("Segoe UI", 11),
                text_color=COLORS["WHITE"],
                anchor="w"
            ).pack(anchor="w", pady=3)
        
        # Modelo de negocio
        ctk.CTkLabel(
            scroll,
            text="💼 MODELO DE NEGOCIO",
            font=("Segoe UI", 16, "bold"),
            text_color=COLORS["TEAL"]
        ).pack(anchor="w", pady=(20, 10))
        
        modelo_items = [
            ("Fase 1 - Diagnóstico", "Levantamiento de datos, validación, configuración"),
            ("Fase 2 - Ejecución", "Corridas base, análisis de sensibilidad, comparación"),
            ("Fase 3 - Entrega", "Script ejecutable, docs técnicas, dashboard, capacitación"),
            ("Fee Implementación", "Según alcance y número de SKUs/ubicaciones"),
            ("Fee por Optimización", "Por corrida de escenario productivo"),
            ("Suscripción Anual", "Actualizaciones, nuevos módulos, soporte"),
        ]
        
        for label, desc in modelo_items:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=f"  {label}:", font=("Segoe UI", 11, "bold"), text_color=COLORS["AMBER"], width=180).pack(side="left")
            ctk.CTkLabel(row, text=desc, font=("Segoe UI", 11), text_color=COLORS["GRAY"]).pack(side="left")
        
        # Botón cerrar
        ctk.CTkButton(
            modal,
            text="Cerrar",
            font=("Segoe UI", 12, "bold"),
            width=120,
            height=40,
            fg_color=COLORS["TEAL"],
            hover_color=COLORS["TEAL_HOVER"],
            command=modal.destroy
        ).pack(pady=30)
        
    def toggle_fullscreen(self, event=None):
        try:
            self.root.state('zoomed' if not self.root.attributes('-zoomed') else 'normal')
        except:
            self.root.attributes('-zoomed', not self.root.attributes('-zoomed'))
    
    def end_fullscreen(self, event=None):
        try:
            self.root.state('normal')
        except:
            self.root.attributes('-zoomed', False)


def main():
    root = ctk.CTk()
    app = MIPRetailOptimizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()