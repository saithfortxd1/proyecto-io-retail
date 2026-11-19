import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Importar la función refactorizada
from optimizacion import resolver_modelo, ZONAS_DEFAULT, UBICACIONES_DEFAULT, DEMANDA_DEFAULT, COSTOS_FIJOS_DEFAULT, CAPACIDADES_DEFAULT, MAX_CENTROS_DEFAULT, COSTOS_ENVIO_DEFAULT, COSTO_BASELINE_DEFAULT


class LogisticsOptimizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MIP Retail Optimizer - Optimización Logística")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f5f5f5")
        
        # Pantalla completa en Windows
        try:
            self.root.state('zoomed')
        except:
            # Fallback multiplataforma
            self.root.attributes('-zoomed', True)
        
        # Toggle fullscreen con F11 y salir con Esc
        self.fullscreen = True
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.root.bind('<Escape>', self.end_fullscreen)
        
        self.costo_actual = COSTO_BASELINE_DEFAULT
        self.costo_optimo = None
        
        # Variables para almacenar referencias a los Entry
        self.entry_vars = {}
        
        self.setup_styles()
        self.create_widgets()
        self.cargar_valores_iniciales()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        BG_MAIN = "#f5f5f5"
        BG_CARD = "#ffffff"
        FG_DARK = "#2c3e50"
        FG_MID = "#34495e"
        FG_GREEN = "#27ae60"
        FG_RED = "#e74c3c"
        
        style.configure(".", background=BG_MAIN, foreground=FG_DARK, font=("Segoe UI", 10))
        style.configure("TFrame", background=BG_MAIN)
        style.configure("TLabelFrame", background=BG_MAIN, foreground=FG_DARK)
        style.configure("TLabelFrame.Label", background=BG_MAIN, foreground=FG_DARK, font=("Segoe UI", 11, "bold"))
        style.configure("TLabel", background=BG_MAIN, foreground=FG_DARK)
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), background=BG_MAIN, foreground=FG_DARK)
        style.configure("Subtitle.TLabel", font=("Segoe UI", 11), background=BG_MAIN, foreground=FG_MID)
        style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"), background=BG_CARD, foreground=FG_DARK)
        style.configure("Param.TLabel", font=("Segoe UI", 10), background=BG_CARD, foreground=FG_MID)
        style.configure("Result.TLabel", font=("Segoe UI", 11, "bold"), background=BG_CARD, foreground=FG_DARK)
        style.configure("Value.TLabel", font=("Segoe UI", 11), background=BG_CARD, foreground=FG_GREEN)
        style.configure("Run.TButton", font=("Segoe UI", 10, "bold"), padding=10)
        style.configure("Restore.TButton", font=("Segoe UI", 9), padding=6)
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=28, background=BG_CARD, fieldbackground=BG_CARD, foreground=FG_DARK)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background=FG_DARK, foreground="white")
        style.map("Treeview", background=[("selected", "#3498db")], foreground=[("selected", "white")])
        style.configure("Card.TFrame", background=BG_CARD, relief="flat", borderwidth=0)
        style.configure("Card.TLabelframe", background=BG_CARD, borderwidth=1, relief="solid")
        style.configure("Card.TLabelframe.Label", background=BG_CARD, foreground=FG_DARK, font=("Segoe UI", 11, "bold"))
        
    def create_widgets(self):
        # === SCROLL GLOBAL ===
        canvas = tk.Canvas(self.root, background="#f5f5f5", highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=v_scrollbar.set)
        
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        main_frame = ttk.Frame(canvas, padding=20, style="TFrame")
        canvas_window = canvas.create_window((0, 0), window=main_frame, anchor=tk.NW)
        
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        main_frame.bind("<Configure>", on_frame_configure)
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Título
        title_label = ttk.Label(main_frame, text="MIP Retail Optimizer", style="Title.TLabel")
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ttk.Label(main_frame, text="Optimización de Red de Centros de Distribución - Programación Entera Mixta", style="Subtitle.TLabel")
        subtitle_label.pack(pady=(0, 15))
        
        # CONTENEDOR DE DOS COLUMNAS
        content_frame = ttk.Frame(main_frame, style="TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.grid_columnconfigure(0, weight=1, minsize=450)
        content_frame.grid_columnconfigure(1, weight=1, minsize=550)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # ========== COLUMNA IZQUIERDA ==========
        left_frame = ttk.Frame(content_frame, style="Card.TFrame", padding=20)
        left_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 10))
        left_frame.grid_rowconfigure(2, weight=1)
        
        # Sección: Parámetros de Entrada EDITABLES
        params_header_frame = ttk.Frame(left_frame, style="Card.TFrame")
        params_header_frame.pack(fill=tk.X, pady=(0, 10))
        
        params_label = ttk.Label(params_header_frame, text="Parámetros de Entrada (Editables)", style="Section.TLabel")
        params_label.pack(side=tk.LEFT, anchor=tk.W)
        
        # Botón Restaurar Valores Base
        self.restore_button = ttk.Button(
            params_header_frame,
            text="↩ Restaurar Valores Base",
            style="Restore.TButton",
            command=self.restaurar_valores_base
        )
        self.restore_button.pack(side=tk.RIGHT)
        
        # Notebook para organizar parámetros en pestañas
        self.notebook = ttk.Notebook(left_frame)
        self.notebook.pack(fill=tk.X, pady=(0, 12))
        
        # --- Pestaña 1: Centros de Distribución ---
        self.tab_cds = ttk.Frame(self.notebook, style="Card.TFrame", padding=10)
        self.notebook.add(self.tab_cds, text="🏢 Centros (Costos Fijos y Capacidades)")
        
        # Headers
        ttk.Label(self.tab_cds, text="Centro", style="Section.TLabel").grid(row=0, column=0, padx=10, pady=6)
        ttk.Label(self.tab_cds, text="Costo Fijo (USD/mes)", style="Section.TLabel").grid(row=0, column=1, padx=10, pady=6)
        ttk.Label(self.tab_cds, text="Capacidad (unidades/mes)", style="Section.TLabel").grid(row=0, column=2, padx=10, pady=6)
        
        for i, ubicacion in enumerate(UBICACIONES_DEFAULT):
            row = i + 1
            ttk.Label(self.tab_cds, text=ubicacion, style="Param.TLabel").grid(row=row, column=0, padx=10, pady=4, sticky=tk.W)
            
            entry_costo = ttk.Entry(self.tab_cds, width=18, font=("Segoe UI", 10))
            entry_costo.grid(row=row, column=1, padx=10, pady=4)
            self.entry_vars[f'costo_fijo_{i}'] = entry_costo
            
            entry_cap = ttk.Entry(self.tab_cds, width=18, font=("Segoe UI", 10))
            entry_cap.grid(row=row, column=2, padx=10, pady=4)
            self.entry_vars[f'capacidad_{i}'] = entry_cap
        
        # --- Pestaña 2: Demandas ---
        self.tab_demandas = ttk.Frame(self.notebook, style="Card.TFrame", padding=10)
        self.notebook.add(self.tab_demandas, text="📍 Demandas por Zona")
        
        ttk.Label(self.tab_demandas, text="Zona", style="Section.TLabel").grid(row=0, column=0, padx=10, pady=6)
        ttk.Label(self.tab_demandas, text="Demanda (unidades/mes)", style="Section.TLabel").grid(row=0, column=1, padx=10, pady=6)
        
        for j, zona in enumerate(ZONAS_DEFAULT):
            row = j + 1
            ttk.Label(self.tab_demandas, text=zona, style="Param.TLabel").grid(row=row, column=0, padx=10, pady=4, sticky=tk.W)
            entry_dem = ttk.Entry(self.tab_demandas, width=18, font=("Segoe UI", 10))
            entry_dem.grid(row=row, column=1, padx=10, pady=4)
            self.entry_vars[f'demanda_{j}'] = entry_dem
        
        # --- Pestaña 3: Configuración General ---
        self.tab_config = ttk.Frame(self.notebook, style="Card.TFrame", padding=10)
        self.notebook.add(self.tab_config, text="⚙️ Configuración")
        
        ttk.Label(self.tab_config, text="Máximo de CDs a abrir:", style="Param.TLabel").grid(row=0, column=0, padx=10, pady=8, sticky=tk.W)
        self.entry_max_centros = ttk.Entry(self.tab_config, width=10, font=("Segoe UI", 10))
        self.entry_max_centros.grid(row=0, column=1, padx=10, pady=8, sticky=tk.W)
        self.entry_vars['max_centros'] = self.entry_max_centros
        
        ttk.Label(self.tab_config, text="Costo Baseline (USD/mes):", style="Param.TLabel").grid(row=1, column=0, padx=10, pady=8, sticky=tk.W)
        self.entry_baseline = ttk.Entry(self.tab_config, width=18, font=("Segoe UI", 10))
        self.entry_baseline.grid(row=1, column=1, padx=10, pady=8, sticky=tk.W)
        self.entry_vars['baseline'] = self.entry_baseline
        
        # Botón de ejecución
        run_frame = ttk.Frame(left_frame, style="Card.TFrame")
        run_frame.pack(fill=tk.X, pady=(6, 12))
        
        self.run_button = ttk.Button(
            run_frame, 
            text="▶ Ejecutar Modelo de Optimización", 
            style="Run.TButton",
            command=self.run_optimization
        )
        self.run_button.pack(fill=tk.X, ipady=8)
        
        # Frame de resultados operativos
        results_frame = ttk.LabelFrame(left_frame, text="Resultados Operativos", padding=12, style="Card.TLabelframe")
        results_frame.pack(fill=tk.X, pady=(0, 0))
        
        results_grid = ttk.Frame(results_frame, style="Card.TFrame")
        results_grid.pack(fill=tk.X)
        
        # 5 filas de métricas
        ttk.Label(results_grid, text="Costo Fijo Óptimo:", style="Result.TLabel").grid(row=0, column=0, sticky=tk.W, padx=10, pady=4)
        self.costo_fijo_label = ttk.Label(results_grid, text="—", style="Value.TLabel")
        self.costo_fijo_label.grid(row=0, column=1, sticky=tk.W, padx=10, pady=4)
        
        ttk.Label(results_grid, text="Costo Variable Óptimo:", style="Result.TLabel").grid(row=1, column=0, sticky=tk.W, padx=10, pady=4)
        self.costo_variable_label = ttk.Label(results_grid, text="—", style="Value.TLabel")
        self.costo_variable_label.grid(row=1, column=1, sticky=tk.W, padx=10, pady=4)
        
        ttk.Label(results_grid, text="Costo Total Óptimo:", style="Result.TLabel").grid(row=2, column=0, sticky=tk.W, padx=10, pady=4)
        self.costo_total_label = ttk.Label(results_grid, text="—", style="Value.TLabel")
        self.costo_total_label.grid(row=2, column=1, sticky=tk.W, padx=10, pady=4)
        
        ttk.Label(results_grid, text="Ahorro Mensual:", style="Result.TLabel").grid(row=3, column=0, sticky=tk.W, padx=10, pady=4)
        self.ahorro_label = ttk.Label(results_grid, text="—", style="Value.TLabel")
        self.ahorro_label.grid(row=3, column=1, sticky=tk.W, padx=10, pady=4)
        
        ttk.Separator(results_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)
        
        ttk.Label(results_grid, text="Reducción Porcentual:", style="Result.TLabel").grid(row=4, column=0, sticky=tk.W, padx=10, pady=4)
        self.porcentaje_label = ttk.Label(results_grid, text="—", style="Value.TLabel")
        self.porcentaje_label.grid(row=4, column=1, sticky=tk.W, padx=10, pady=4)
        
        # ========== COLUMNA DERECHA ==========
        right_frame = ttk.Frame(content_frame, style="Card.TFrame", padding=20)
        right_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=(10, 0))
        right_frame.grid_rowconfigure(1, weight=1)
        
        chart_label = ttk.Label(right_frame, text="Comparativa de Costos Logísticos", style="Section.TLabel")
        chart_label.pack(anchor=tk.W, pady=(0, 10))
        
        self.chart_frame = ttk.Frame(right_frame, style="Card.TFrame")
        self.chart_frame.pack(fill=tk.BOTH, expand=True)
        
        self.create_cost_chart()
        
        # ========== TABLA INFERIOR ==========
        table_frame = ttk.LabelFrame(main_frame, text="Plan de Asignación Logística (Centro → Zona)", padding=12, style="Card.TLabelframe")
        table_frame.pack(fill=tk.BOTH, expand=False, pady=(15, 0))
        
        columns = ("Ubicacion", "Zona", "Cantidad_Enviada")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=6)
        
        self.tree.heading("Ubicacion", text="Centro de Distribución")
        self.tree.heading("Zona", text="Zona Urbana")
        self.tree.heading("Cantidad_Enviada", text="Unidades Enviadas")
        
        self.tree.column("Ubicacion", width=280, anchor=tk.CENTER)
        self.tree.column("Zona", width=280, anchor=tk.CENTER)
        self.tree.column("Cantidad_Enviada", width=280, anchor=tk.CENTER)
        
        v_scrollbar_tree = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar_tree = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar_tree.set, xscrollcommand=h_scrollbar_tree.set)
        
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        v_scrollbar_tree.grid(row=0, column=1, sticky=tk.NS)
        h_scrollbar_tree.grid(row=1, column=0, sticky=tk.EW)
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        self.load_csv_data()
        
    def cargar_valores_iniciales(self):
        """Carga los valores por defecto en todos los campos Entry"""
        for i, costo in enumerate(COSTOS_FIJOS_DEFAULT):
            self.entry_vars[f'costo_fijo_{i}'].delete(0, tk.END)
            self.entry_vars[f'costo_fijo_{i}'].insert(0, f"{costo:,}")
        
        for i, cap in enumerate(CAPACIDADES_DEFAULT):
            self.entry_vars[f'capacidad_{i}'].delete(0, tk.END)
            self.entry_vars[f'capacidad_{i}'].insert(0, f"{cap:,}")
        
        for j, dem in enumerate(DEMANDA_DEFAULT):
            self.entry_vars[f'demanda_{j}'].delete(0, tk.END)
            self.entry_vars[f'demanda_{j}'].insert(0, f"{dem:,}")
        
        self.entry_max_centros.delete(0, tk.END)
        self.entry_max_centros.insert(0, str(MAX_CENTROS_DEFAULT))
        
        self.entry_baseline.delete(0, tk.END)
        self.entry_baseline.insert(0, f"{COSTO_BASELINE_DEFAULT:,}")
        
    def restaurar_valores_base(self):
        """Restaura todos los campos a los valores originales del estudio"""
        self.cargar_valores_iniciales()
        messagebox.showinfo("Valores Restaurados", "Todos los parámetros han sido restablecidos a los valores base del caso de estudio.")
        
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
            
            max_centros = int(self.entry_max_centros.get())
            baseline = int(self.entry_baseline.get().replace(',', '').replace('.', ''))
            
            # Validaciones adicionales
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
    
    def create_cost_chart(self):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        labels = ['Costo Baseline', 'Costo Óptimo']
        if self.costo_optimo is not None:
            values = [self.costo_actual, self.costo_optimo]
            colors = ['#e74c3c', '#27ae60']
        else:
            values = [self.costo_actual, 0]
            colors = ['#e74c3c', '#95a5a6']
        
        fig, ax = plt.subplots(figsize=(6, 3.5), dpi=100)
        fig.patch.set_facecolor('#ffffff')
        ax.set_facecolor('#ffffff')
        
        bars = ax.bar(labels, values, color=colors, edgecolor='white', linewidth=1.5, width=0.5)
        
        for bar, val in zip(bars, values):
            if val > 0:
                height = bar.get_height()
                ax.annotate(f'${val:,.0f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 5),
                           textcoords="offset points",
                           ha='center', va='bottom',
                           fontweight='bold', fontsize=11, color='#2c3e50')
        
        ax.set_ylabel('USD', fontsize=11, fontweight='bold', color='#2c3e50')
        ax.set_title('Costo Logístico Mensual: Baseline vs. Optimizado', fontsize=12, fontweight='bold', pad=12, color='#2c3e50')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#bdc3c7')
        ax.spines['bottom'].set_color('#bdc3c7')
        ax.tick_params(axis='x', colors='#2c3e50', labelsize=10)
        ax.tick_params(axis='y', colors='#2c3e50', labelsize=10)
        ax.grid(axis='y', alpha=0.3, color='#bdc3c7')
        ax.set_ylim(0, max(values) * 1.25 if max(values) > 0 else 300000)
        
        if self.costo_optimo is not None:
            ahorro = self.costo_actual - self.costo_optimo
            pct = (ahorro / self.costo_actual) * 100
            ax.text(0.5, 0.93, f'Ahorro: ${ahorro:,.0f} ({pct:.1f}%)',
                   transform=ax.transAxes, ha='center', va='top',
                   fontsize=10, fontweight='bold', color='#27ae60',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='#e8f8f0', edgecolor='#27ae60'))
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def run_optimization(self):
        """Ejecuta la optimización con los parámetros personalizados"""
        # Leer y validar parámetros
        try:
            costos_fijos, capacidades, demandas, max_centros, baseline = self.leer_parametros_ui()
        except ValueError as e:
            messagebox.showerror("Error de Validación", str(e))
            return
        
        self.run_button.config(state=tk.DISABLED, text="⏳ Ejecutando...")
        self.costo_actual = baseline
        self.root.update()
        
        try:
            # Llamar a la función refactorizada
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
                self.actualizar_resultados(resultado)
                self.load_csv_data_from_result(resultado['asignaciones'])
                self.create_cost_chart()
                self.run_button.config(state=tk.NORMAL, text="▶ Ejecutar Modelo de Optimización")
            else:
                messagebox.showerror("Error en Optimización", 
                    f"Estado: {resultado['estado']}\n{resultado['mensaje']}")
                self.run_button.config(state=tk.NORMAL, text="▶ Ejecutar Modelo de Optimización")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")
            self.run_button.config(state=tk.NORMAL, text="▶ Ejecutar Modelo de Optimización")
    
    def actualizar_resultados(self, resultado):
        self.costo_fijo_label.config(text=f"{resultado['costo_fijo']:,.2f} USD")
        self.costo_variable_label.config(text=f"{resultado['costo_variable']:,.2f} USD")
        self.costo_total_label.config(text=f"{resultado['costo_total']:,.2f} USD")
        self.ahorro_label.config(text=f"{resultado['ahorro']:,.2f} USD")
        self.porcentaje_label.config(text=f"{resultado['porcentaje_ahorro']:.2f}%")
        self.costo_optimo = resultado['costo_total']
        
    def load_csv_data_from_result(self, asignaciones):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for asignacion in asignaciones:
            self.tree.insert("", tk.END, values=(
                asignacion['Ubicacion'],
                asignacion['Zona'],
                f"{asignacion['Cantidad_Enviada']:,.0f}"
            ))
        
        # También guardar CSV
        df = pd.DataFrame(asignaciones)
        df.to_csv('asignacion_logistica.csv', index=False)
    
    def load_csv_data(self):
        """Carga inicial desde archivo CSV si existe"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "asignacion_logistica.csv")
        
        try:
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                for _, row in df.iterrows():
                    self.tree.insert("", tk.END, values=(
                        row['Ubicacion'],
                        row['Zona'],
                        f"{row['Cantidad_Enviada']:,.0f}"
                    ))
            else:
                # Cargar resultado por defecto
                self.run_optimization()
        except Exception as e:
            print(f"Error cargando CSV: {e}")
    
    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        try:
            self.root.state('zoomed' if self.fullscreen else 'normal')
        except:
            self.root.attributes('-zoomed', self.fullscreen)
    
    def end_fullscreen(self, event=None):
        self.fullscreen = False
        try:
            self.root.state('normal')
        except:
            self.root.attributes('-zoomed', False)

def main():
    root = tk.Tk()
    app = LogisticsOptimizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()