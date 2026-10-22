# 5.2 Modelo Matemático

## Variables de Decisión

El problema se formula como un modelo de Programación Entera Mixta (MIP) para la optimización de la red logística de distribución. Se definen las siguientes variables de decisión:

**Variable binaria de apertura de Centro de Distribución (CD):**

$$y_i \in \{0, 1\} \quad \forall i \in I$$

Donde:
- $i \in I = \{L1, L2, L3, L4\}$ representa el conjunto de ubicaciones candidatas para los centros de distribución.
- $y_i = 1$ si el centro de distribución $i$ se abre; $y_i = 0$ en caso contrario.

**Variable continua de flujo de envío:**

$$x_{ij} \geq 0 \quad \forall i \in I, \; \forall j \in J$$

Donde:
- $j \in J = \{Z1, Z2, Z3, Z4, Z5, Z6\}$ representa el conjunto de zonas urbanas de demanda.
- $x_{ij}$ denota el volumen de unidades enviadas desde el centro de distribución $i$ hacia la zona $j$.

## Función Objetivo

La función objetivo minimiza el costo logístico total, compuesto por la suma de los costos fijos de apertura de los centros de distribución y los costos variables de transporte:

$$\min \; Z = \sum_{i \in I} C_i^{\text{fijo}} \cdot y_i + \sum_{i \in I} \sum_{j \in J} C_{ij}^{\text{transporte}} \cdot x_{ij}$$

Donde:
- $C_i^{\text{fijo}}$ es el costo fijo anual de apertura del centro $i$.
- $C_{ij}^{\text{transporte}}$ es el costo unitario de transporte desde el centro $i$ a la zona $j$.

## Restricciones

El modelo está sujeto a las siguientes restricciones operativas:

**1. Cumplimiento estricto de la demanda por zona:**

$$\sum_{i \in I} x_{ij} = D_j \quad \forall j \in J$$

Donde $D_j$ es la demanda de la zona $j$. Esta restricción garantiza que la totalidad de la demanda de cada zona sea satisfecha exactamente.

**2. Límite de capacidad por ubicación sujeto a la variable de apertura:**

$$\sum_{j \in J} x_{ij} \leq K_i \cdot y_i \quad \forall i \in I$$

Donde $K_i$ es la capacidad máxima del centro $i$. Si $y_i = 0$ (centro cerrado), la restricción fuerza $x_{ij} = 0 \; \forall j$; si $y_i = 1$, el flujo total no puede exceder la capacidad instalada $K_i$.

**3. Restricción de infraestructura - máximo número de centros abiertos:**

$$\sum_{i \in I} y_i \leq 2$$

Esta restricción cardinal impone un límite superior de dos centros de distribución operativos simultáneamente, reflejando la limitación estratégica de infraestructura.

---

# 13 Resultados Obtenidos

## Solución Óptima del Modelo

La resolución del modelo MIP mediante el solucionador CBC (Coin-or Branch and Cut) convergió a una solución óptima global en 0.03 segundos (111 iteraciones, 0 nodos enumerados), confirmando la optimalidad del resultado.

**Configuración óptima de la red:**

El modelo seleccionó la apertura de dos centros de distribución:
- **L2** (costo fijo: 50,000 USD; capacidad: 20,000 unidades)
- **L3** (costo fijo: 38,000 USD; capacidad: 12,000 unidades)

Los centros L1 y L4 permanecen cerrados ($y_{L1} = y_{L4} = 0$).

**Asignación óptima de flujos:**

| Centro | Zonas Asignadas | Volumen Total |
|--------|-----------------|---------------|
| L2     | Z1, Z2, Z3      | 12,000        |
| L3     | Z4, Z5, Z6      | 10,000        |

Ambas ubicaciones operan dentro de sus límites de capacidad (L2: 60% de utilización; L3: 83% de utilización).

## Análisis de Costos

| Componente | Valor (USD) |
|------------|-------------|
| Costo Fijo Óptimo ($\sum C_i^{\text{fijo}} y_i$) | 88,000 |
| Costo Variable Óptimo ($\sum C_{ij}^{\text{transporte}} x_{ij}$) | 94,500 |
| **Costo Logístico Total Óptimo** | **182,500** |

## Impacto Financiero

El escenario actual (sin optimización) presenta un costo logístico de **243,000 USD**. La implementación de la configuración óptima genera:

- **Ahorro mensual:** 60,500 USD
- **Reducción porcentual:** 24.90%

$$\text{Ahorro} = 243,000 - 182,500 = 60,500 \text{ USD}$$
$$\text{Reducción \%} = \frac{60,500}{243,000} \times 100 = 24.90\%$$

Este resultado representa una disminución sustancial en la estructura de costos logísticos, liberando capital operativo y mejorando la eficiencia de la cadena de suministro sin comprometer el nivel de servicio a las zonas de demanda.

---

# 7 Integración con Inteligencia Artificial

El desarrollo de este proyecto se apoyó extensivamente en **Inteligencia Artificial Generativa** como asistente de desarrollo, acelerando la transición desde la formulación matemática hasta la implementación computacional completa. Los roles específicos incluyen:

**Asistente de Programación y Sintaxis:**
- Estructuración de la sintaxis en Python para el modelo MIP usando PuLP, incluyendo la declaración correcta de variables de decisión (`LpVariable.dicts`), construcción de la función objetivo con `lpSum`, y codificación de restricciones lineales.
- Implementación de la interfaz gráfica con Tkinter: diseño de layouts con `grid`/`pack`, integración de `ttk.Treeview` para tablas de datos, y embebido de gráficos `matplotlib` mediante `FigureCanvasTkAgg`.
- Manejo de subprocess para desacoplar la ejecución del solucionador de la GUI principal, parsing de salida stdout para actualización dinámica de KPIs.

**Gestión de Control de Versiones:**
- Generación de comandos Git secuenciales: inicialización del repositorio (`git init`), staging selectivo (`git add`), commits semánticos con mensajes descriptivos, renombrado de rama principal (`git branch -M main`), vinculación a remoto (`git remote add origin`) y push (`git push -u origin main`).
- Organización del historial en commits atómicos que separan la definición del modelo, la ejecución de optimización, y la entrega de interfaz y documentación.

**Redacción de Documentación Técnica:**
- Formalización de la Sección 5.2 (Modelo Matemático) con notación LaTeX para variables, función objetivo y restricciones.
- Estructuración de la Sección 13 (Resultados) con tablas Markdown, análisis de costos desglosado y fórmulas de impacto financiero.
- Redacción de la Sección 12 (Pitch Comercial) con justificación cuantitativa, segmentación de público objetivo y definición de modelo de negocio recurrente.

La IA generativa actuó como **co-piloto técnico**, reduciendo el tiempo de desarrollo de días a horas, asegurando consistencia entre formulación matemática, código ejecutable y documentación, y permitiendo al equipo enfocarse en la validación del modelo y la interpretación de resultados en lugar de la sintaxis boilerplate.

---

# 8 Ventajas de la Propuesta

| Categoría | Ventaja |
|-----------|---------|
| **Técnicas** | Resolución rápida con PuLP y escalabilidad del script; arquitectura modular que permite extender el modelo (nuevas ubicaciones, SKUs, restricciones de inventario) sin reescritura; desacoplamiento entre motor de optimización e interfaz de usuario. |
| **Económicas** | Reducción comprobada de costos operativos (24.90% ahorro mensual = 60,500 USD) y optimización de fletes logísticos mediante asignación matemáticamente óptima de flujos a centros de menor costo unitario de transporte. |
| **Estratégicas** | Soporte cuantitativo a la toma de decisiones para apertura de instalaciones; capacidad de análisis de escenarios (what-if) ante variaciones de demanda, costos de combustible o expansión de red; trazabilidad completa desde datos de entrada hasta plan de asignación ejecutable (CSV). |