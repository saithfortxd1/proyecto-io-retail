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
| `optimizacion.py` | Motor matemático desacoplado: función `resolver_modelo(...)` reutilizable + ejecución CLI |
| `interfaz.py` | Interfaz gráfica (Tkinter) con pantalla completa (`F11`/`Esc`), **modo protegido por defecto** con valores oficiales, **simulador interactivo desbloqueable** (pestañas editables, candado de solo lectura, botón restauración), KPIs, gráfico Matplotlib y tabla |
| `asignacion_logistica.csv` | Plan de asignación óptima (Centro → Zona, unidades) |
| `documentacion_tecnica.md` | Informe técnico completo (secciones 1-5, 7-8, 13-15, referencias APA, Anexo A) |
| `pitch_comercial.md` | Solo en rama `feature/pitch-comercial`: modelo de negocio y propuesta de valor |

---

## Arquitectura de Ramas (Git Workflow)

Este repositorio mantiene una arquitectura simplificada con dos ramas:

| Rama | Propósito | Estado |
|------|-----------|--------|
| **`main`** | **Aplicación completa lista para usar** — Incluye la versión base oficial ($182,500 USD / 24.90% ahorro) **y** el simulador interactivo desbloqueable. Al iniciar, la interfaz muestra los valores oficiales en **modo protegido (solo lectura)**. Un clic en **"🔓 Habilitar Edición"** + confirmación activa el simulador completo (pestañas editables, recálculo en vivo, botón **✅ Confirmar y Recalcular**, y **↩ Restaurar Valores Base** que vuelve al caso oficial). Recomendada para evaluación, auditoría, despliegue y análisis de sensibilidad. | 🟢 Oficial / Completa |
| **`feature/pitch-comercial`** | **Documentación comercial aislada** — Archivo `pitch_comercial.md` con definición de producto, justificación financiera ($60,500 USD/mes ahorro), público objetivo y modelo de negocio (consultoría + licenciamiento). No afecta código técnico. | 🔵 Documental |

> **Nota:** La rama `feature/simulacion-parametrizable` fue integrada a `main` y eliminada. La funcionalidad completa está disponible directamente en `main`.

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

## Resultados Principales (Caso Base Oficial)

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
- `matplotlib`

```bash
pip install pulp pandas matplotlib
```

---

## Ejecución

### Línea de comandos (motor matemático)
```bash
python optimizacion.py
```
Genera `asignacion_logistica.csv` e imprime resultados en consola (caso base oficial).

### Interfaz gráfica completa (en `main`)
```bash
python interfaz.py
```
- **Al iniciar**: Ventana maximizada, **modo protegido** con valores oficiales ($182,500 USD / 24.90%), etiqueta `🔒 Modo Protegido (Valores Oficiales)`.
- **Simulador interactivo**: Clic en **"🔓 Habilitar Edición"** → confirmación → pestañas editables (Centros, Demandas, Configuración) → **"✅ Confirmar y Recalcular en Tiempo Real"** → recálculo instantáneo → **vuelve a modo protegido** automáticamente.
- **Restauración**: Botón **"↩ Restaurar Valores Base"** → confirmación → valores oficiales + recálculo automático + modo protegido.
- **Pantalla completa**: `F11` alterna, `Esc` sale.
- Panel KPIs, gráfico Matplotlib (Baseline vs Óptimo), tabla `Treeview` de asignación.

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