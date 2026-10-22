import pulp
import pandas as pd

# Zonas urbanas y ubicaciones candidatas
zonas = ['Z1', 'Z2', 'Z3', 'Z4', 'Z5', 'Z6']
ubicaciones = ['L1', 'L2', 'L3', 'L4']

# Datos de entrada
demanda = [3000, 4000, 5000, 3500, 2500, 4000]
costos_fijos = [45000, 50000, 38000, 42000]
capacidades = [15000, 20000, 12000, 16000]

# Costos de envío desde cada ubicación a cada zona
costos_envio = [
    [3, 5, 8, 6, 10, 12],  # L1
    [6, 3, 4, 7, 8, 9],    # L2
    [9, 7, 5, 3, 4, 6],    # L3
    [11, 8, 6, 5, 3, 4]    # L4
]

# Inicialización del modelo de minimización
model = pulp.LpProblem("Optimizacion_Ubicacion", pulp.LpMinimize)

# Variables de decisión
# y: variable binaria de apertura por ubicación
y = pulp.LpVariable.dicts("y", range(len(ubicaciones)), cat=pulp.LpBinary)

# x: variable continua del volumen de envío desde cada ubicación a cada zona
x = pulp.LpVariable.dicts("x", (range(len(ubicaciones)), range(len(zonas))), lowBound=0, cat=pulp.LpContinuous)

# Función Objetivo: Minimizar costo de apertura + costo de transporte
costo_apertura = pulp.lpSum(costos_fijos[i] * y[i] for i in range(len(ubicaciones)))
costo_transporte = pulp.lpSum(costos_envio[i][j] * x[i][j] for i in range(len(ubicaciones)) for j in range(len(zonas)))
model += costo_apertura + costo_transporte

# Restricción 1: La suma de envíos a cada zona es igual a su demanda
for j in range(len(zonas)):
    model += pulp.lpSum(x[i][j] for i in range(len(ubicaciones))) == demanda[j]

# Restricción 2: El total enviado desde cada ubicación es menor o igual a su capacidad * y[i]
for i in range(len(ubicaciones)):
    model += pulp.lpSum(x[i][j] for j in range(len(zonas))) <= capacidades[i] * y[i]

# Restricción 3: La suma total de variables 'y' es menor o igual a 2
model += pulp.lpSum(y[i] for i in range(len(ubicaciones))) <= 2

# Resolver el modelo
model.solve()

# Extraer valores de las variables
costo_fijo_optimo = sum(costos_fijos[i] * y[i].varValue for i in range(len(ubicaciones)))
costo_variable_optimo = sum(costos_envio[i][j] * x[i][j].varValue for i in range(len(ubicaciones)) for j in range(len(zonas)))
costo_total_optimo = costo_fijo_optimo + costo_variable_optimo

# Cálculo de ahorro
costo_actual = 243000
ahorro_mensual = costo_actual - costo_total_optimo
porcentaje_ahorro = (ahorro_mensual / costo_actual) * 100

# Crear DataFrame de asignaciones
asignaciones = []
for i in range(len(ubicaciones)):
    for j in range(len(zonas)):
        cantidad = x[i][j].varValue
        if cantidad > 0:
            asignaciones.append({
                'Ubicacion': ubicaciones[i],
                'Zona': zonas[j],
                'Cantidad_Enviada': cantidad
            })

df_asignaciones = pd.DataFrame(asignaciones)
df_asignaciones.to_csv('asignacion_logistica.csv', index=False)

# Imprimir resultados
print(f"Costo Fijo Óptimo: {costo_fijo_optimo:.2f}")
print(f"Costo Variable Óptimo: {costo_variable_optimo:.2f}")
print(f"Costo Total Óptimo: {costo_total_optimo:.2f}")
print(f"Ahorro Mensual: {ahorro_mensual:.2f}")
print(f"Porcentaje de Ahorro: {porcentaje_ahorro:.2f}%")
print("Archivo asignacion_logistica.csv creado correctamente")