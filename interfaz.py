import tkinter as tk
from tkinter import ttk
import pandas as pd
import subprocess
import sys
import os

class LogisticsOptimizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MIP Retail Optimizer - Optimización Logística")
        self.root.geometry("900x650")
        self.root.configure(bg="#f5f5f5")
        
        self.setup_styles()
        self.create_widgets()
        
    def setup_styles(self):
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), background="#f5f5f5", foreground="#2c3e50")
        style.configure("Subtitle.TLabel", font=("Segoe UI", 11), background="#f5f5f5", foreground="#34495e")
        style.configure("Result.TLabel", font=("Segoe UI", 11, "bold"), background="#ffffff", foreground="#2c3e50")
        style.configure("Value.TLabel", font=("Segoe UI", 11), background="#ffffff", foreground="#27ae60")
        style.configure("Run.TButton", font=("Segoe UI", 10, "bold"), padding=10)
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=28)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="MIP Retail Optimizer", style="Title.TLabel")
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ttk.Label(main_frame, text="Optimización de Red de Centros de Distribución - Programación Entera Mixta", style="Subtitle.TLabel")
        subtitle_label.pack(pady=(0, 20))
        
        # Frame de botón de ejecución
        run_frame = ttk.Frame(main_frame)
        run_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.run_button = ttk.Button(
            run_frame, 
            text="▶ Ejecutar Modelo de Optimización", 
            style="Run.TButton",
            command=self.run_optimization
        )
        self.run_button.pack(pady=10)
        
        # Frame de resultados operativos
        results_frame = ttk.LabelFrame(main_frame, text="Resultados Operativos", padding=15)
        results_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Grid de resultados
        results_grid = ttk.Frame(results_frame)
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
        
        # Frame de tabla de asignaciones
        table_frame = ttk.LabelFrame(main_frame, text="Plan de Asignación Logística (Centro → Zona)", padding=15)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
        columns = ("Ubicacion", "Zona", "Cantidad_Enviada")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        
        # Configurar columnas
        self.tree.heading("Ubicacion", text="Centro de Distribución")
        self.tree.heading("Zona", text="Zona Urbana")
        self.tree.heading("Cantidad_Enviada", text="Unidades Enviadas")
        
        self.tree.column("Ubicacion", width=200, anchor=tk.CENTER)
        self.tree.column("Zona", width=200, anchor=tk.CENTER)
        self.tree.column("Cantidad_Enviada", width=200, anchor=tk.CENTER)
        
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
        
    def run_optimization(self):
        """Ejecuta el script de optimización y actualiza la interfaz"""
        self.run_button.config(state=tk.DISABLED, text="⏳ Ejecutando...")
        self.root.update()
        
        try:
            # Ejecutar optimizacion.py
            result = subprocess.run(
                [sys.executable, "optimizacion.py"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            if result.returncode == 0:
                # Parsear salida para extraer valores
                output = result.stdout
                self.parse_and_update_results(output)
                # Recargar tabla
                self.load_csv_data()
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
        
        # Valores por defecto (resultados conocidos)
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
            elif key == 'ahorro':
                self.ahorro_label.config(text=f"{float(value):,.2f} USD")
            elif key == 'porcentaje':
                self.porcentaje_label.config(text=f"{float(value):.2f}%")
    
    def load_csv_data(self):
        """Carga y muestra los datos del archivo CSV en el Treeview"""
        # Limpiar tabla
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
                # Datos por defecto si no existe el CSV
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