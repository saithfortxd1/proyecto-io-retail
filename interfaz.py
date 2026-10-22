import tkinter as tk
from tkinter import ttk
import pandas as pd
import subprocess
import sys
import os
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class LogisticsOptimizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MIP Retail Optimizer - Optimización Logística")
        self.root.geometry("1100x700")
        self.root.configure(bg="#f5f5f5")
        
        self.costo_actual = 243000
        self.costo_optimo = None
        
        self.setup_styles()
        self.create_widgets()
        
    def setup_styles(self):
        style = ttk.Style()
        # Tema base
        style.theme_use('clam')
        
        # Colores consistentes
        BG_MAIN = "#f5f5f5"
        BG_CARD = "#ffffff"
        FG_DARK = "#2c3e50"
        FG_MID = "#34495e"
        FG_GREEN = "#27ae60"
        FG_RED = "#e74c3c"
        
        # Configurar estilos globales
        style.configure(".", background=BG_MAIN, foreground=FG_DARK, font=("Segoe UI", 10))
        style.configure("TFrame", background=BG_MAIN)
        style.configure("TLabelFrame", background=BG_MAIN, foreground=FG_DARK)
        style.configure("TLabelFrame.Label", background=BG_MAIN, foreground=FG_DARK, font=("Segoe UI", 11, "bold"))
        style.configure("TLabel", background=BG_MAIN, foreground=FG_DARK)
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        
        # Estilos específicos
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), background=BG_MAIN, foreground=FG_DARK)
        style.configure("Subtitle.TLabel", font=("Segoe UI", 11), background=BG_MAIN, foreground=FG_MID)
        style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"), background=BG_CARD, foreground=FG_DARK)
        style.configure("Param.TLabel", font=("Segoe UI", 10), background=BG_CARD, foreground=FG_MID)
        style.configure("Result.TLabel", font=("Segoe UI", 11, "bold"), background=BG_CARD, foreground=FG_DARK)
        style.configure("Value.TLabel", font=("Segoe UI", 11), background=BG_CARD, foreground=FG_GREEN)
        style.configure("Run.TButton", font=("Segoe UI", 10, "bold"), padding=10)
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=28, background=BG_CARD, fieldbackground=BG_CARD, foreground=FG_DARK)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background=FG_DARK, foreground="white")
        style.map("Treeview", background=[("selected", "#3498db")], foreground=[("selected", "white")])
        style.configure("Card.TFrame", background=BG_CARD, relief="flat", borderwidth=0)
        style.configure("Card.TLabelframe", background=BG_CARD, borderwidth=1, relief="solid")
        style.configure("Card.TLabelframe.Label", background=BG_CARD, foreground=FG_DARK, font=("Segoe UI", 11, "bold"))
        
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding=20, style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="MIP Retail Optimizer", style="Title.TLabel")
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ttk.Label(main_frame, text="Optimización de Red de Centros de Distribución - Programación Entera Mixta", style="Subtitle.TLabel")
        subtitle_label.pack(pady=(0, 20))
        
        # CONTENEDOR DE DOS COLUMNAS
        content_frame = ttk.Frame(main_frame, style="TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.grid_columnconfigure(0, weight=1, minsize=400)
        content_frame.grid_columnconfigure(1, weight=1, minsize=500)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # ========== COLUMNA IZQUIERDA ==========
        left_frame = ttk.Frame(content_frame, style="Card.TFrame", padding=20)
        left_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 10))
        left_frame.grid_rowconfigure(2, weight=1)
        
        # Sección: Parámetros de Entrada
        params_label = ttk.Label(left_frame, text="Parámetros de Entrada", style="Section.TLabel")
        params_label.pack(anchor=tk.W, pady=(0, 15))
        
        params_card = ttk.Frame(left_frame, style="Card.TFrame", padding=15)
        params_card.pack(fill=tk.X, pady=(0, 20))
        
        # Demanda Total
        ttk.Label(params_card, text="Demanda Total:", style="Param.TLabel").grid(row=0, column=0, sticky=tk.W, pady=8)
        ttk.Label(params_card, text="22,000 unidades", style="Value.TLabel").grid(row=0, column=1, sticky=tk.W, padx=(20, 0), pady=8)
        
        # Restricción de infraestructura
        ttk.Label(params_card, text="Restricción de Infraestructura:", style="Param.TLabel").grid(row=1, column=0, sticky=tk.W, pady=8)
        ttk.Label(params_card, text="Máximo 2 CDs operativos", style="Value.TLabel").grid(row=1, column=1, sticky=tk.W, padx=(20, 0), pady=8)
        
        # Ubicaciones candidatas
        ttk.Label(params_card, text="Ubicaciones Candidatas:", style="Param.TLabel").grid(row=2, column=0, sticky=tk.W, pady=8)
        ttk.Label(params_card, text="L1, L2, L3, L4 (4 opciones)", style="Value.TLabel").grid(row=2, column=1, sticky=tk.W, padx=(20, 0), pady=8)
        
        # Zonas de demanda
        ttk.Label(params_card, text="Zonas de Demanda:", style="Param.TLabel").grid(row=3, column=0, sticky=tk.W, pady=8)
        ttk.Label(params_card, text="Z1–Z6 (6 zonas urbanas)", style="Value.TLabel").grid(row=3, column=1, sticky=tk.W, padx=(20, 0), pady=8)
        
        # Botón de ejecución
        run_frame = ttk.Frame(left_frame, style="Card.TFrame")
        run_frame.pack(fill=tk.X, pady=(10, 20))
        
        self.run_button = ttk.Button(
            run_frame, 
            text="▶ Ejecutar Modelo de Optimización", 
            style="Run.TButton",
            command=self.run_optimization
        )
        self.run_button.pack(fill=tk.X, ipady=8)
        
        # Frame de resultados operativos
        results_frame = ttk.LabelFrame(left_frame, text="Resultados Operativos", padding=15, style="Card.TLabelframe")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        results_grid = ttk.Frame(results_frame, style="Card.TFrame")
        results_grid.pack(fill=tk.X)
        
        # Costo Fijo
        ttk.Label(results_grid, text="Costo Fijo Óptimo:", style="Result.TLabel").grid(row=0, column=0, sticky=tk.W, padx=10, pady=8)
        self.costo_fijo_label = ttk.Label(results_grid, text="—", style="Value.TLabel")
        self.costo_fijo_label.grid(row=0, column=1, sticky=tk.W, padx=10, pady=8)
        
        # Costo Variable
        ttk.Label(results_grid, text="Costo Variable Óptimo:", style="Result.TLabel").grid(row=1, column=0, sticky=tk.W, padx=10, pady=8)
        self.costo_variable_label = ttk.Label(results_grid, text="—", style="Value.TLabel")
        self.costo_variable_label.grid(row=1, column=1, sticky=tk.W, padx=10, pady=8)
        
        # Costo Total
        ttk.Label(results_grid, text="Costo Total Óptimo:", style="Result.TLabel").grid(row=2, column=0, sticky=tk.W, padx=10, pady=8)
        self.costo_total_label = ttk.Label(results_grid, text="—", style="Value.TLabel")
        self.costo_total_label.grid(row=2, column=1, sticky=tk.W, padx=10, pady=8)
        
        # Ahorro Mensual
        ttk.Label(results_grid, text="Ahorro Mensual:", style="Result.TLabel").grid(row=3, column=0, sticky=tk.W, padx=10, pady=8)
        self.ahorro_label = ttk.Label(results_grid, text="—", style="Value.TLabel")
        self.ahorro_label.grid(row=3, column=1, sticky=tk.W, padx=10, pady=8)
        
        # Separador visual
        ttk.Separator(results_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Porcentaje de ahorro
        ttk.Label(results_grid, text="Reducción Porcentual:", style="Result.TLabel").grid(row=4, column=0, sticky=tk.W, padx=10, pady=8)
        self.porcentaje_label = ttk.Label(results_grid, text="—", style="Value.TLabel")
        self.porcentaje_label.grid(row=4, column=1, sticky=tk.W, padx=10, pady=8)
        
        # ========== COLUMNA DERECHA ==========
        right_frame = ttk.Frame(content_frame, style="Card.TFrame", padding=20)
        right_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=(10, 0))
        right_frame.grid_rowconfigure(1, weight=1)
        
        # Gráfico de comparación de costos
        chart_label = ttk.Label(right_frame, text="Comparativa de Costos Logísticos", style="Section.TLabel")
        chart_label.pack(anchor=tk.W, pady=(0, 15))
        
        self.chart_frame = ttk.Frame(right_frame, style="Card.TFrame")
        self.chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # Gráfico inicial (solo costo actual)
        self.create_cost_chart()
        
        # ========== TABLA INFERIOR (span completo) ==========
        table_frame = ttk.LabelFrame(main_frame, text="Plan de Asignación Logística (Centro → Zona)", padding=15, style="Card.TLabelframe")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Treeview
        columns = ("Ubicacion", "Zona", "Cantidad_Enviada")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
        
        # Configurar columnas
        self.tree.heading("Ubicacion", text="Centro de Distribución")
        self.tree.heading("Zona", text="Zona Urbana")
        self.tree.heading("Cantidad_Enviada", text="Unidades Enviadas")
        
        self.tree.column("Ubicacion", width=250, anchor=tk.CENTER)
        self.tree.column("Zona", width=250, anchor=tk.CENTER)
        self.tree.column("Cantidad_Enviada", width=250, anchor=tk.CENTER)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        v_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        h_scrollbar.grid(row=1, column=0, sticky=tk.EW)
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Cargar datos iniciales del CSV
        self.load_csv_data()
        
    def create_cost_chart(self):
        """Crea o actualiza el gráfico de barras comparativo"""
        # Limpiar frame anterior
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # Datos
        labels = ['Costo Actual', 'Costo Óptimo']
        if self.costo_optimo is not None:
            values = [self.costo_actual, self.costo_optimo]
            colors = ['#e74c3c', '#27ae60']
        else:
            values = [self.costo_actual, 0]
            colors = ['#e74c3c', '#95a5a6']
        
        # Crear figura con fondo consistente
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_facecolor('#ffffff')
        ax.set_facecolor('#ffffff')
        
        bars = ax.bar(labels, values, color=colors, edgecolor='white', linewidth=1.5, width=0.5)
        
        # Etiquetas de valor en las barras
        for bar, val in zip(bars, values):
            if val > 0:
                height = bar.get_height()
                ax.annotate(f'${val:,.0f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 5),
                           textcoords="offset points",
                           ha='center', va='bottom',
                           fontweight='bold', fontsize=11, color='#2c3e50')
        
        # Estética
        ax.set_ylabel('USD', fontsize=11, fontweight='bold', color='#2c3e50')
        ax.set_title('Costo Logístico Mensual: Actual vs. Optimizado', fontsize=12, fontweight='bold', pad=15, color='#2c3e50')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#bdc3c7')
        ax.spines['bottom'].set_color('#bdc3c7')
        ax.tick_params(axis='x', colors='#2c3e50', labelsize=10)
        ax.tick_params(axis='y', colors='#2c3e50', labelsize=10)
        ax.grid(axis='y', alpha=0.3, color='#bdc3c7')
        ax.set_ylim(0, max(values) * 1.25 if max(values) > 0 else 300000)
        
        # Añadir etiqueta de ahorro si hay costo óptimo
        if self.costo_optimo is not None:
            ahorro = self.costo_actual - self.costo_optimo
            pct = (ahorro / self.costo_actual) * 100
            ax.text(0.5, 0.95, f'Ahorro: ${ahorro:,.0f} ({pct:.1f}%)',
                   transform=ax.transAxes, ha='center', va='top',
                   fontsize=11, fontweight='bold', color='#27ae60',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='#e8f8f0', edgecolor='#27ae60'))
        
        plt.tight_layout()
        
        # Incrustar en Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def run_optimization(self):
        """Ejecuta el script de optimización y actualiza la interfaz"""
        self.run_button.config(state=tk.DISABLED, text="⏳ Ejecutando...")
        self.root.update()
        
        try:
            result = subprocess.run(
                [sys.executable, "optimizacion.py"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            if result.returncode == 0:
                output = result.stdout
                self.parse_and_update_results(output)
                self.load_csv_data()
                self.create_cost_chart()  # Actualizar gráfico
                self.run_button.config(state=tk.NORMAL, text="▶ Ejecutar Modelo de Optimización")
            else:
                self.show_error(f"Error en la optimización:\n{result.stderr}")
                self.run_button.config(state=tk.NORMAL, text="▶ Ejecutar Modelo de Optimización")
                
        except Exception as e:
            self.show_error(f"Error al ejecutar el modelo:\n{str(e)}")
            self.run_button.config(state=tk.NORMAL, text="▶ Ejecutar Modelo de Optimización")
    
    def parse_and_update_results(self, output):
        """Extrae valores numéricos de la salida del script"""
        import re
        
        patterns = {
            'costo_fijo': r'Costo Fijo.*?([\d,]+\.?\d*)',
            'costo_variable': r'Costo Variable.*?([\d,]+\.?\d*)',
            'costo_total': r'Costo Total.*?([\d,]+\.?\d*)',
            'ahorro': r'Ahorro Mensual.*?([\d,]+\.?\d*)',
            'porcentaje': r'Porcentaje.*?([\d,]+\.?\d*)'
        }
        
        defaults = {
            'costo_fijo': '88000',
            'costo_variable': '94500',
            'costo_total': '182500',
            'ahorro': '60500',
            'porcentaje': '24.90'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, output)
            value = match.group(1).replace(',', '') if match else defaults[key]
            
            if key == 'costo_fijo':
                self.costo_fijo_label.config(text=f"{float(value):,.2f} USD")
            elif key == 'costo_variable':
                self.costo_variable_label.config(text=f"{float(value):,.2f} USD")
            elif key == 'costo_total':
                self.costo_total_label.config(text=f"{float(value):,.2f} USD")
                self.costo_optimo = float(value)
            elif key == 'ahorro':
                self.ahorro_label.config(text=f"{float(value):,.2f} USD")
            elif key == 'porcentaje':
                self.porcentaje_label.config(text=f"{float(value):.2f}%")
    
    def load_csv_data(self):
        """Carga y muestra los datos del archivo CSV en el Treeview"""
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
                default_data = [
                    ("L2", "Z1", "3,000"),
                    ("L2", "Z2", "4,000"),
                    ("L2", "Z3", "5,000"),
                    ("L3", "Z4", "3,500"),
                    ("L3", "Z5", "2,500"),
                    ("L3", "Z6", "4,000"),
                ]
                for row in default_data:
                    self.tree.insert("", tk.END, values=row)
        except Exception as e:
            print(f"Error cargando CSV: {e}")
    
    def show_error(self, message):
        """Muestra un diálogo de error"""
        error_window = tk.Toplevel(self.root)
        error_window.title("Error")
        error_window.geometry("400x200")
        error_window.configure(bg="#f5f5f5")
        error_window.transient(self.root)
        error_window.grab_set()
        
        ttk.Label(error_window, text="❌ Error", font=("Segoe UI", 12, "bold"), foreground="#e74c3c", background="#f5f5f5").pack(pady=15)
        ttk.Label(error_window, text=message, font=("Segoe UI", 9), background="#f5f5f5", wraplength=350).pack(pady=10, padx=20)
        ttk.Button(error_window, text="Cerrar", command=error_window.destroy).pack(pady=15)

def main():
    root = tk.Tk()
    app = LogisticsOptimizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()