import os
import pulp
import pandas as pd
import subprocess
import sys
import threading
from unittest.mock import patch

# Parámetros por defecto del caso de estudio original
ZONAS_DEFAULT = ['Z1', 'Z2', 'Z3', 'Z4', 'Z5', 'Z6']
UBICACIONES_DEFAULT = ['L1', 'L2', 'L3', 'L4']
DEMANDA_DEFAULT = [3000, 4000, 5000, 3500, 2500, 4000]
COSTOS_FIJOS_DEFAULT = [45000, 50000, 38000, 42000]
CAPACIDADES_DEFAULT = [15000, 20000, 12000, 16000]
COSTOS_ENVIO_DEFAULT = [
    [3, 5, 8, 6, 10, 12],  # L1
    [6, 3, 4, 7, 8, 9],    # L2
    [9, 7, 5, 3, 4, 6],    # L3
    [11, 8, 6, 5, 3, 4]    # L4
]
COSTO_BASELINE_DEFAULT = 243000
MAX_CENTROS_DEFAULT = 2

_CBC_LAUNCH_LOCK = threading.Lock()


def _is_cbc_command(command):
    executable = command[0] if isinstance(command, (list, tuple)) and command else command
    if not isinstance(executable, (str, bytes, os.PathLike)):
        return False
    executable_name = os.path.basename(os.fsdecode(os.fspath(executable))).lower()
    return executable_name in {"cbc", "cbc.exe"}


def _solve_with_cbc(model):
    solver = pulp.PULP_CBC_CMD(msg=False)
    if not sys.platform.startswith("win"):
        return model.solve(solver)

    with _CBC_LAUNCH_LOCK:
        original_popen = subprocess.Popen

        def popen_without_console(*args, **kwargs):
            command = args[0] if args else kwargs.get("args")
            if _is_cbc_command(command):
                kwargs["creationflags"] = (
                    kwargs.get("creationflags") or 0
                ) | subprocess.CREATE_NO_WINDOW
                kwargs["shell"] = False
            return original_popen(*args, **kwargs)

        with patch.object(subprocess, "Popen", popen_without_console):
            return model.solve(solver)


def resolver_modelo(
    costos_fijos=None,
    capacidades=None,
    demandas=None,
    costos_envio=None,
    max_centros=None,
    zonas=None,
    ubicaciones=None,
    costo_baseline=None
):
    """
    Resuelve el modelo MIP de localización de centros de distribución.
    
    Args:
        costos_fijos: Lista de costos fijos por ubicación (len = n_ubicaciones)
        capacidades: Lista de capacidades máximas por ubicación (len = n_ubicaciones)
        demandas: Lista de demandas por zona (len = n_zonas)
        costos_envio: Matriz n_ubicaciones x n_zonas de costos unitarios
        max_centros: Número máximo de centros a abrir (default 2)
        zonas: Lista de nombres de zonas
        ubicaciones: Lista de nombres de ubicaciones
        costo_baseline: Costo baseline para cálculo de ahorro (default 243,000)
    
    Returns:
        dict con:
            - 'estado': 'Optimal' | 'Infeasible' | 'Error'
            - 'centros_abiertos': lista de nombres de ubicaciones abiertas
            - 'costo_fijo': float
            - 'costo_variable': float
            - 'costo_total': float
            - 'ahorro': float
            - 'porcentaje_ahorro': float
            - 'asignaciones': lista de dicts con Ubicacion, Zona, Cantidad_Enviada
            - 'mensaje': str (detalle de error si aplica)
    """
    # Usar valores por defecto si no se proporcionan
    if zonas is None:
        zonas = ZONAS_DEFAULT
    if ubicaciones is None:
        ubicaciones = UBICACIONES_DEFAULT
    if costos_fijos is None:
        costos_fijos = COSTOS_FIJOS_DEFAULT
    if capacidades is None:
        capacidades = CAPACIDADES_DEFAULT
    if demandas is None:
        demandas = DEMANDA_DEFAULT
    if costos_envio is None:
        costos_envio = COSTOS_ENVIO_DEFAULT
    if max_centros is None:
        max_centros = MAX_CENTROS_DEFAULT
    if costo_baseline is None:
        costo_baseline = COSTO_BASELINE_DEFAULT
    
    n_ubicaciones = len(ubicaciones)
    n_zonas = len(zonas)
    
    # Validaciones básicas
    if len(costos_fijos) != n_ubicaciones:
        return {'estado': 'Error', 'mensaje': f'costos_fijos debe tener {n_ubicaciones} elementos'}
    if len(capacidades) != n_ubicaciones:
        return {'estado': 'Error', 'mensaje': f'capacidades debe tener {n_ubicaciones} elementos'}
    if len(demandas) != n_zonas:
        return {'estado': 'Error', 'mensaje': f'demandas debe tener {n_zonas} elementos'}
    if len(costos_envio) != n_ubicaciones:
        return {'estado': 'Error', 'mensaje': f'costos_envio debe tener {n_ubicaciones} filas'}
    for i, fila in enumerate(costos_envio):
        if len(fila) != n_zonas:
            return {'estado': 'Error', 'mensaje': f'costos_envio fila {i} debe tener {n_zonas} columnas'}
    if max_centros > n_ubicaciones or max_centros < 1:
        return {'estado': 'Error', 'mensaje': f'max_centros debe estar entre 1 y {n_ubicaciones}'}
    
    # Verificar factibilidad básica: capacidad total >= demanda total
    # (considerando que solo se pueden abrir max_centros centros)
    capacidades_ordenadas = sorted(capacidades, reverse=True)
    capacidad_max_disponible = sum(capacidades_ordenadas[:max_centros])
    if sum(demandas) > capacidad_max_disponible:
        return {
            'estado': 'Infeasible',
            'mensaje': f'Demanda total ({sum(demandas):,}) excede capacidad máxima posible con {max_centros} centros ({capacidad_max_disponible:,})',
            'centros_abiertos': [],
            'costo_fijo': 0,
            'costo_variable': 0,
            'costo_total': 0,
            'ahorro': 0,
            'porcentaje_ahorro': 0,
            'asignaciones': []
        }
    
    try:
        # Inicialización del modelo
        model = pulp.LpProblem("Optimizacion_Ubicacion", pulp.LpMinimize)
        
        # Variables de decisión
        y = pulp.LpVariable.dicts("y", range(n_ubicaciones), cat=pulp.LpBinary)
        x = pulp.LpVariable.dicts("x", (range(n_ubicaciones), range(n_zonas)), lowBound=0, cat=pulp.LpContinuous)
        
        # Función Objetivo
        costo_apertura = pulp.lpSum(costos_fijos[i] * y[i] for i in range(n_ubicaciones))
        costo_transporte = pulp.lpSum(costos_envio[i][j] * x[i][j] for i in range(n_ubicaciones) for j in range(n_zonas))
        model += costo_apertura + costo_transporte
        
        # Restricción 1: Demanda
        for j in range(n_zonas):
            model += pulp.lpSum(x[i][j] for i in range(n_ubicaciones)) == demandas[j]
        
        # Restricción 2: Capacidad ligada a apertura
        for i in range(n_ubicaciones):
            model += pulp.lpSum(x[i][j] for j in range(n_zonas)) <= capacidades[i] * y[i]
        
        # Restricción 3: Límite de centros
        model += pulp.lpSum(y[i] for i in range(n_ubicaciones)) <= max_centros
        
        # Resolver
        _solve_with_cbc(model)
        
        # Verificar estado
        status = pulp.LpStatus[model.status]
        if status != 'Optimal':
            return {
                'estado': status,
                'mensaje': f'Solver terminó con estado: {status}',
                'centros_abiertos': [],
                'costo_fijo': 0,
                'costo_variable': 0,
                'costo_total': 0,
                'ahorro': 0,
                'porcentaje_ahorro': 0,
                'asignaciones': []
            }
        
        # Extraer resultados
        centros_abiertos = [ubicaciones[i] for i in range(n_ubicaciones) if y[i].varValue == 1]
        
        costo_fijo_optimo = sum(costos_fijos[i] * y[i].varValue for i in range(n_ubicaciones))
        costo_variable_optimo = sum(costos_envio[i][j] * x[i][j].varValue for i in range(n_ubicaciones) for j in range(n_zonas))
        costo_total_optimo = costo_fijo_optimo + costo_variable_optimo
        
        ahorro_mensual = costo_baseline - costo_total_optimo
        porcentaje_ahorro = (ahorro_mensual / costo_baseline) * 100 if costo_baseline > 0 else 0
        
        # Asignaciones
        asignaciones = []
        for i in range(n_ubicaciones):
            for j in range(n_zonas):
                cantidad = x[i][j].varValue
                if cantidad and cantidad > 0:
                    asignaciones.append({
                        'Ubicacion': ubicaciones[i],
                        'Zona': zonas[j],
                        'Cantidad_Enviada': cantidad
                    })
        
        return {
            'estado': 'Optimal',
            'centros_abiertos': centros_abiertos,
            'costo_fijo': costo_fijo_optimo,
            'costo_variable': costo_variable_optimo,
            'costo_total': costo_total_optimo,
            'ahorro': ahorro_mensual,
            'porcentaje_ahorro': porcentaje_ahorro,
            'asignaciones': asignaciones,
            'mensaje': 'Optimización completada exitosamente'
        }
        
    except Exception as e:
        return {
            'estado': 'Error',
            'mensaje': f'Error al resolver el modelo: {str(e)}',
            'centros_abiertos': [],
            'costo_fijo': 0,
            'costo_variable': 0,
            'costo_total': 0,
            'ahorro': 0,
            'porcentaje_ahorro': 0,
            'asignaciones': []
        }


if __name__ == "__main__":
    # Ejecución directa con parámetros por defecto
    resultado = resolver_modelo()
    
    if resultado['estado'] == 'Optimal':
        print(f"Estado: {resultado['estado']}")
        print(f"Centros abiertos: {', '.join(resultado['centros_abiertos'])}")
        print(f"Costo Fijo Óptimo: {resultado['costo_fijo']:.2f}")
        print(f"Costo Variable Óptimo: {resultado['costo_variable']:.2f}")
        print(f"Costo Total Óptimo: {resultado['costo_total']:.2f}")
        print(f"Ahorro Mensual: {resultado['ahorro']:.2f}")
        print(f"Porcentaje de Ahorro: {resultado['porcentaje_ahorro']:.2f}%")
        
        # Exportar CSV
        df = pd.DataFrame(resultado['asignaciones'])
        df.to_csv('asignacion_logistica.csv', index=False)
        print("Archivo asignacion_logistica.csv creado correctamente")
    else:
        print(f"Estado: {resultado['estado']}")
        print(f"Mensaje: {resultado['mensaje']}")