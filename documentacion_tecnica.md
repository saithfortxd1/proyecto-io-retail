# 1 Introducción

Este proyecto aborda el **problema de localización de centros de distribución (Facility Location Problem)** en el contexto de una cadena de retail con múltiples zonas de demanda y ubicaciones candidatas para centros de distribución (CDs). El objetivo es determinar qué instalaciones abrir y cómo asignar los flujos de producto para minimizar el costo logístico total, sujeto a restricciones de capacidad, demanda y límite de infraestructura.

La técnica empleada es la **Programación Entera Mixta (MIP - Mixed Integer Programming)**, una metodología de optimización matemática que combina variables continuas (flujos de envío) y variables binarias (decisiones de apertura/cerradura de instalaciones). Esta formulación permite modelar decisiones discretas de infraestructura junto con asignación continua de volúmenes, capturando la naturaleza combinatoria del problema.

La implementación computacional se realiza mediante **PuLP (Python Linear Programming)**, una librería de modelado de optimización lineal en Python que actúa como interfaz hacia solucionadores de alto rendimiento como CBC (Coin-or Branch and Cut), GLPK, Gurobi o CPLEX. PuLP permite declarar variables, funciones objetivo y restricciones con sintaxis pythonica, generando automáticamente los archivos de entrada para el solucionador y recuperando la solución óptima.

---

# 2 Objetivos

## Objetivo General

Desarrollar un modelo de optimización basado en Programación Entera Mixta que **minimice el costo logístico total** (costos fijos de apertura + costos variables de transporte) para la red de distribución de una cadena de retail, cumpliendo con la totalidad de la demanda zonal y respetando restricciones de capacidad e infraestructura.

## Objetivos Específicos

1. **Formulación del modelo matemático**: Definir variables de decisión ($y_i$ binaria, $x_{ij}$ continua), función objetivo de minimización y restricciones operativas (demanda, capacidad, cardinalidad de centros) con notación formal.

2. **Implementación computacional reproducible**: Codificar el modelo en Python usando PuLP, integrar la resolución con CBC, automatizar la exportación del plan de asignación óptima (CSV) y construir una interfaz gráfica (Tkinter + matplotlib) para visualización interactiva de resultados.

3. **Integración de Inteligencia Artificial Generativa**: Utilizar IA como asistente de desarrollo para acelerar la sintaxis de PuLP, la estructura de la interfaz gráfica, la gestión de control de versiones (Git) y la redacción de documentación técnica con notación LaTeX, validando la consistencia entre formulación matemática, código ejecutable y reporte final.

---

# 3 Justificación

La operación actual de la cadena de retail utiliza **asignación empírica de demanda a centros de distribución**, basada en reglas heurísticas (proximidad geográfica, antecedentes históricos, criterio de gerentes zonales) sin un respaldo cuantitativo riguroso. Esta aproximación presenta limitaciones críticas:

- **Suboptimalidad estructural**: La asignación por proximidad no considera la interacción entre costos fijos de apertura y costos variables de transporte, pudiendo abrir centros costosos cuando una consolidación en menos instalaciones de menor costo unitario sería superior.
- **Falta de escalabilidad**: Ante cambios en la demanda, costos de combustible o nuevas ubicaciones candidatas, la re-asignación manual requiere semanas de análisis y no garantiza optimalidad.
- **Opacidad en la toma de decisiones**: Sin un modelo matemático, no es posible realizar análisis de sensibilidad (what-if) ni cuantificar el costo de oportunidad de decisiones operativas.
- **Costo de oportunidad documentado**: El escenario actual incurre en **243,000 USD/mes**, mientras que la optimización matemática demuestra que una reconfiguración racional alcanza **182,500 USD/mes**, dejando **60,500 USD/mes (24.90%)** en ahorros no capturados.

La adopción de un enfoque MIP resuelve estas limitaciones al proporcionar optimalidad garantizada, trazabilidad completa, capacidad de escenario y velocidad de re-optimización (segundos vs. semanas).

---

# 4 Descripción del Problema

## Contexto Operativo

Una cadena de retail opera en un área metropolitana dividida en **seis zonas urbanas de demanda** ($Z1$–$Z6$) con requerimientos mensuales conocidos: 3,000; 4,000; 5,000; 3,500; 2,500 y 4,000 unidades respectivamente, totalizando **22,000 unidades/mes**.

Existen **cuatro ubicaciones candidatas** ($L1$–$L4$) para establecer centros de distribución, cada una con:
- **Costo fijo mensual de apertura**: 45,000; 50,000; 38,000 y 42,000 USD
- **Capacidad máxima de procesamiento**: 15,000; 20,000; 12,000 y 16,000 unidades
- **Matriz de costos unitarios de transporte** a cada zona (USD/unidad)

## Restricción Estratégica

Por directriz corporativa de racionalización de activos, se impone un **límite máximo de dos centros de distribución operativos simultáneamente** ($\sum y_i \leq 2$), obligando a una selección óptima del subconjunto de ubicaciones.

## Costo Actual (Baseline)

La configuración actual, heredada de decisiones históricas sin optimización formal, genera un **costo logístico total de 243,000 USD/mes**, compuesto por costos fijos de instalaciones activas y fletes de distribución a zonas. Este valor constituye el benchmark contra el cual se mide el impacto de la optimización.

---

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

# 14 Análisis de Sensibilidad

El análisis de sensibilidad evalúa la robustez de la solución óptima ante variaciones en parámetros clave, proporcionando información crítica para la toma de decisiones bajo incertidumbre.

## Variación en Costos de Flete (+10%)

Un incremento generalizado del 10% en la matriz de costos de transporte ($C_{ij}^{\text{transporte}} \times 1.10$) elevaría el **costo variable óptimo** de 94,500 USD a aproximadamente **103,950 USD** (asumiendo que la estructura de asignación óptima L2→Z1-3, L3→Z4-6 se mantiene). El **costo total óptimo** ascendería a ~191,950 USD, reduciendo el ahorro mensual a ~51,050 USD (21.0% vs. 243,000 USD baseline).

Sin embargo, si el aumento es **asimétrico** (ej. solo rutas desde L3), el modelo podría re-optimizar cambiando la asignación de zonas frontera (Z4, Z6) hacia L2 si su capacidad residual (8,000 unidades disponibles) lo permite, mitigando parcialmente el impacto. La **estructura binaria** ($y_{L2}=1, y_{L3}=1$) probablemente se mantendría dada la diferencia de costos fijos (L3: 38,000 USD vs L1: 45,000 USD, L4: 42,000 USD).

## Variación en Capacidad de Centros

- **Reducción de capacidad en L2** (ej. de 20,000 a 15,000): La asignación actual (12,000 en L2) dejaría margen de 3,000 unidades. Si la demanda crece o se reasignan zonas, L2 podría convertirse en cuello de botella, forzando apertura de un tercer centro (violando $\sum y_i \leq 2$) o redistribución subóptima. El **shadow price** de la capacidad de L2 indica el valor marginal de cada unidad adicional de capacidad.

- **Aumento de capacidad en L3** (ej. de 12,000 a 15,000): Permitiría absorber mayor volumen de Z4-Z6 y potencialmente atraer zonas de L2 si los costos de transporte lo justifican, mejorando la utilización del centro de menor costo fijo.

- **Nueva ubicación candidata**: La adición de L5 con costos/parámetros competitivos expandiría el espacio factible, pudiendo reducir el costo total si ofrece mejor trade-off fijo/variable.

La **dualidad del programa lineal relajado** proporciona precios sombra (valores duales) para cada restricción, cuantificando exactamente cuánto mejorarían el objetivo por unidad de relajación en capacidad o demanda.

---

# 15 Conclusiones

## 1. Eficiencia computacional de PuLP+CBC para Facility Location

La combinación **PuLP + CBC** resolvió el MIP (28 variables, 11 restricciones, 4 enteras) en **0.03 segundos** con optimalidad global garantizada (gap 0%). Esto demuestra que para problemas de localización de tamaño moderado (< 50 ubicaciones, < 100 zonas), el stack Python open-source es **suficiente para uso productivo**, eliminando la dependencia de solucionadores comerciales costosos. La arquitectura desacoplada (modelo → solver → resultados) permite migrar a Gurobi/CPLEX cambiando una línea de código si la escala lo requiere.

## 2. Ahorro del 24.90% valida la optimización matemática frente a heurísticas empíricas

La reducción de **243,000 USD a 182,500 USD/mes (60,500 USD de ahorro, 24.90%)** no es marginal: representa **726,000 USD anuales** liberados. Este resultado cuantifica el **costo de la no-optimización** —la brecha entre asignación por reglas de pulgar y asignación matemáticamente óptima—. En contextos retail con márgenes comprimidos, esta diferencia puede determinar la viabilidad de una operación. La solución óptima (L2+L3) consolidó volumen en el centro de menor costo fijo (L3: 38,000 USD) y aprovechó la capacidad del centro mejor posicionado para Z1-Z3 (L2), un trade-off que la heurística de proximidad no captura.

## 3. IA Generativa como multiplicador de productividad en proyectos de OR/Analytics

La integración de IA generativa redujo el ciclo de desarrollo de **formulación → código → interfaz → documentación → versionado** de días a horas. Roles clave: (a) **traducción fiel de notación matemática a sintaxis PuLP** sin errores de indexación; (b) **arquitectura Tkinter + matplotlib** con layout responsivo, threading implícito via subprocess, y binding de datos CSV; (c) **commits Git semánticos** y ramificación main; (d) **documentación técnica con LaTeX/Markdown** consistente con el código. La IA no reemplaza la validación del analista (verificación de factibilidad, interpretación de duales, prueba de escenarios), pero elimina la fricción sintáctica y estructural, permitiendo enfocar el tiempo experto en **modelado y decisión**, no en boilerplate.

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