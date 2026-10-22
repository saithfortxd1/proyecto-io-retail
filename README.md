# MIP Retail Optimizer - Optimización Logística de Centros de Distribución

## Descripción del Proyecto

Este repositorio contiene una solución completa de optimización logística basada en **Programación Entera Mixta (MIP)** para el diseño de redes de centros de distribución en el sector retail. El modelo determina la configuración óptima de apertura de centros y asignación de flujos a zonas de demanda, minimizando el costo logístico total sujeto a restricciones operativas reales.

---

## Problema Abordado

Dado un conjunto de:
- **4 ubicaciones candidatas** (L1, L2, L3, L4) con costos fijos y capacidades diferenciadas
- **6 zonas urbanas de demanda** (Z1–Z6) con requerimientos conocidos
- **Matriz de costos de transporte** entre cada par ubicación-zona
- **Restricción estratégica**: máximo 2 centros operativos simultáneamente

El modelo decide **qué centros abrir** y **cómo asignar la demanda** para minimizar costos totales.

---

## Estructura del Repositorio

| Archivo | Descripción |
|---------|-------------|
| `optimizacion.py` | Script principal: modelo MIP, resolución con CBC, exportación de resultados |
| `interfaz.py` | Interfaz gráfica (Tkinter) para ejecución visual y análisis de resultados |
| `asignacion_logistica.csv` | Plan de asignación óptima (Centro → Zona, unidades) |
| `documentacion_tecnica.md` | Sección 5.2 (Modelo Matemático) y Sección 13 (Resultados) |
| `pitch_comercial.md` | Sección 12: Justificación comercial, público objetivo, modelo de negocio |

---

## Modelo Matemático (Resumen)

### Variables de Decisión
- $y_i \in \{0,1\}$: Apertura del centro $i$
- $x_{ij} \geq 0$: Flujo del centro $i$ a la zona $j$

### Función Objetivo
$$\min \sum_i C_i^{\text{fijo}} y_i + \sum_i \sum_j C_{ij}^{\text{transporte}} x_{ij}$$

### Restricciones
1. **Demanda**: $\sum_i x_{ij} = D_j \quad \forall j$
2. **Capacidad**: $\sum_j x_{ij} \leq K_i y_i \quad \forall i$
3. **Infraestructura**: $\sum_i y_i \leq 2$

---

## Resultados Principales

| Métrica | Valor |
|---------|-------|
| **Centros seleccionados** | L2, L3 |
| **Costo Fijo Óptimo** | 88,000 USD |
| **Costo Variable Óptimo** | 94,500 USD |
| **Costo Total Óptimo** | **182,500 USD** |
| **Costo Actual (Baseline)** | 243,000 USD |
| **Ahorro Mensual** | **60,500 USD** |
| **Reducción Porcentual** | **24.90%** |

### Plan de Asignación Óptima
| Centro | Zonas Asignadas | Volumen |
|--------|-----------------|---------|
| L2 | Z1, Z2, Z3 | 12,000 |
| L3 | Z4, Z5, Z6 | 10,000 |

---

## Requisitos

- Python 3.8+
- `pulp` (PuLP 2.9+ compatible)
- `pandas`
- `tkinter` (incluido en Python estándar)

```bash
pip install pulp pandas
```

---

## Ejecución

### Línea de comandos
```bash
python optimizacion.py
```
Genera `asignacion_logistica.csv` e imprime resultados en consola.

### Interfaz gráfica
```bash
python interfaz.py
```
Ventana con botón de ejecución, panel de KPIs y tabla interactiva de asignaciones.

---

## Solucionador

Utiliza **CBC (Coin-or Branch and Cut)** vía PuLP. Tiempo de resolución típico: < 0.1 segundos. Optimalidad garantizada (gap = 0%).

---

## Aplicaciones

- **Network Design** para retail, e-commerce, distribución mayorista
- **Análisis de escenarios** (crecimiento de demanda, variación de costos, nuevas ubicaciones)
- **Due diligence** de inversiones en infraestructura logística
- **Herramienta didáctica** para MIP aplicado a supply chain

---

## Licencia

Proyecto académico / demostrativo. Uso libre para fines educativos y de evaluación.

---

## Autor

Desarrollado como parte de proyecto final de investigación en optimización logística.