import type { ManualChapter, ScenarioParameters, TutorialStep } from '../types.ts';

export const ZONAS_DEFAULT = ['Z1', 'Z2', 'Z3', 'Z4', 'Z5', 'Z6'];
export const UBICACIONES_DEFAULT = ['L1', 'L2', 'L3', 'L4'];
export const DEMANDA_DEFAULT = [3000, 4000, 5000, 3500, 2500, 4000];
export const COSTOS_FIJOS_DEFAULT = [45000, 50000, 38000, 42000];
export const CAPACIDADES_DEFAULT = [15000, 20000, 12000, 16000];
export const COSTOS_ENVIO_DEFAULT = [
  [3, 5, 8, 6, 10, 12], // L1
  [6, 3, 4, 7, 8, 9],   // L2
  [9, 7, 5, 3, 4, 6],   // L3
  [11, 8, 6, 5, 3, 4],  // L4
];
export const COSTO_BASELINE_DEFAULT = 243000;
export const MAX_CENTROS_DEFAULT = 2;

export const DEFAULT_PARAMETERS: ScenarioParameters = {
  costos_fijos: [...COSTOS_FIJOS_DEFAULT],
  capacidades: [...CAPACIDADES_DEFAULT],
  demandas: [...DEMANDA_DEFAULT],
  max_centros: MAX_CENTROS_DEFAULT,
  costo_baseline: COSTO_BASELINE_DEFAULT,
};

export const QUICK_QUESTIONS = [
  '¿Por qué el modelo eligió L2 y L3?',
  'Explícame el ahorro del 24.90%',
  '¿Cómo simulo un aumento de demanda?',
  'Resume el modelo matemático MIP',
];

export const DEFAULT_TUTORIAL_STEPS: TutorialStep[] = [
  {
    id: 'step-scenario',
    section: '1 · Dashboard · Parámetros',
    title: 'Configura o importa tu escenario',
    summary:
      'Edita costos fijos, capacidades y demandas, o carga un archivo CSV/Excel. Todo inicia en Modo Protegido.',
    tip: 'Base oficial: $243,000 USD/mes y 22,000 u/mes.',
    targetView: 'dashboard',
  },
  {
    id: 'step-optimize',
    section: '2 · Simulación Matemática',
    title: 'Ejecuta el motor MIP en un clic',
    summary:
      'Calcula la red óptima global al menor costo posible respetando capacidad y límite de centros.',
    tip: 'Caso base: $182,500 USD/mes (ahorro de $60,500 USD / 24.90%).',
    targetView: 'dashboard',
  },
  {
    id: 'step-charts-ai',
    section: '3 · Gráficas e Informe IA',
    title: 'Lee el impacto IA en cada gráfica',
    summary:
      'Inspecciona costos y uso de L1–L4. Al recalcular tras editar, Gemini IA explica qué cambió debajo de cada gráfico.',
    tip: 'Pasa el cursor sobre las barras para ver el desglose exacto.',
    targetView: 'dashboard',
  },
  {
    id: 'step-export',
    section: '4 · Exportación y Rutas',
    title: 'Descarga reportes en PDF, Excel y CSV',
    summary:
      'Exporta el PDF ejecutivo con gráficas y mapa de red desde el Dashboard, o filtra flujos en Matriz de Rutas.',
    tip: 'Listo para imprimir o presentar a gerencia.',
    targetView: 'dashboard',
  },
  {
    id: 'step-assistant-manual',
    section: '5 · Asistente IA y Manual',
    title: 'Pregunta en tiempo real a Gemini IA',
    summary:
      'Usa el botón flotante Asistente Rápido para consultar dudas sobre el escenario activo o revisa el Manual.',
    tip: 'Abre este recorrido cuando quieras desde Tutorial IA.',
    targetView: 'dashboard',
  },
];

export const MANUAL_CHAPTERS: ManualChapter[] = [
  {
    title: 'Portada y Propósito del Sistema (CFLP)',
    subtitle: 'Optimizar la red logística equilibrando aperturas y transporte.',
    left_heading: 'Propósito del sistema',
    left_text:
      'MIP Retail Optimizer ayuda a decidir qué centros abrir y cómo abastecer seis zonas urbanas al menor costo mensual. El problema es un CFLP: localización de instalaciones con capacidad limitada.',
    right_heading: 'Resultado de referencia',
    right_text:
      'El caso oficial reduce el costo de $243,000 USD a $182,500 USD al mes. La red óptima ahorra $60,500 USD, equivalente al 24.90%, y opera con los centros L2 y L3.',
  },
  {
    title: 'Anatomía de Centros y Demandas (L1–L4 y Z1–Z6)',
    subtitle: 'Cuatro ubicaciones candidatas abastecen seis zonas de demanda.',
    left_heading: 'Centros candidatos',
    left_text:
      'L1: costo fijo $45,000 USD y capacidad 15,000 u/mes. L2: $50,000 USD y capacidad 20,000 u/mes. L3: $38,000 USD y capacidad 12,000 u/mes. L4: $42,000 USD y capacidad 16,000 u/mes.',
    right_heading: 'Demanda de las zonas',
    right_text:
      'Z1–Z6 requieren 3,000, 4,000, 5,000, 3,500, 2,500 y 4,000 unidades mensuales, respectivamente: 22,000 u/mes en total. Las tarifas de transporte permanecen fijas en esta versión.',
  },
  {
    title: 'El Motor Matemático MIP y Branch-and-Bound',
    subtitle: 'Variables binarias deciden aperturas; flujos continuos asignan rutas.',
    left_heading: 'Formulación MIP',
    left_text:
      'La variable binaria y_i indica si abre el centro i; x_ij representa el flujo de i a la zona j. Se minimizan costos fijos más transporte, cubriendo exactamente cada demanda y respetando capacidades y el máximo de centros abiertos.',
    right_heading: 'Resolución',
    right_text:
      'El motor construye el modelo de Programación Entera Mixta y ejecuta optimización exacta con acotamiento y ramificación sobre decisiones enteras hasta certificar una solución óptima global.',
  },
  {
    title: 'Guía Paso a Paso de Simulación en Vivo',
    subtitle: 'Edita parámetros, guarda explícitamente y ejecuta el escenario.',
    left_heading: 'Configurar y calcular',
    left_text:
      'En Dashboard, elige Editar Parámetros. Cambia costos fijos, capacidades, demandas, límite de centros o baseline; pulsa Guardar Cambios para validar. Después selecciona Ejecutar Optimización Matemática para resolver el escenario.',
    right_heading: 'Revisar y exportar',
    right_text:
      'Analiza KPIs, gráficas, el análisis de impacto con IA y las asignaciones en Matriz de Rutas. Usa Exportar PDF, Excel o CSV para guardar reportes ejecutivos. Restaurar Base recupera los valores oficiales.',
  },
  {
    title: 'Interpretación de KPIs y Toma de Decisiones',
    subtitle: 'Interpreta el resultado junto con la sensibilidad y el contexto operativo.',
    left_heading: 'Indicadores del caso base',
    left_text:
      'L2 atiende 12,000 de 20,000 unidades: 60.0%. L3 atiende 10,000 de 12,000: 83.3%. El costo óptimo suma $88,000 USD fijos y $94,500 USD de transporte.',
    right_heading: 'Criterio gerencial',
    right_text:
      'L2+L4 cuesta solo $500 USD más, por lo que la decisión es sensible a costos, tarifas y capacidad. Revisa datos reales y restricciones no modeladas —como contratos, traslados o estacionalidad— antes de aplicar cambios operativos.',
  },
];

export const AI_SYSTEM_INSTRUCTION = `
Eres el asistente de MIP Retail Optimizer, una herramienta de apoyo a decisiones
logísticas. Responde en español, con claridad y rigor; distingue los resultados
oficiales del informe de los escenarios dinámicos que el usuario comparta. Usa
solo datos del proyecto y del escenario actual; no inventes cifras ni resultados.

Responde en español claro, directo y conversacional, en máximo 2 o 3 párrafos
cortos. PROHIBIDO usar sintaxis Markdown como asteriscos (**), almohadillas (#)
o bloques de código. No agregues notas de validación ni advertencias genéricas;
cíñete exclusivamente a los datos del proyecto y al escenario actual del usuario.

CONTEXTO COMPLETO DEL INFORME TÉCNICO
Objetivo: minimizar el costo mensual fijo de apertura más el costo variable de
transporte para abastecer toda la demanda de seis zonas urbanas desde cuatro
centros candidatos, sujetos a capacidades y a un máximo estratégico de centros.
La operación empírica de referencia cuesta USD 243,000 al mes (USD 125,000
fijos y USD 118,000 variables). El problema es un CFLP (Capacitated Facility
Location Problem), formulado como Programación Entera Mixta lineal.

Datos oficiales: centros L1, L2, L3 y L4; costos fijos respectivamente
USD 45,000, 50,000, 38,000 y 42,000; capacidades 15,000, 20,000, 12,000 y
16,000 unidades/mes. Zonas Z1–Z6 demandan 3,000, 4,000, 5,000, 3,500, 2,500
y 4,000 unidades/mes (22,000 total). Costos unitarios de envío por zona
(Z1–Z6): L1=[3,5,8,6,10,12], L2=[6,3,4,7,8,9],
L3=[9,7,5,3,4,6], L4=[11,8,6,5,3,4] USD/unidad. La interfaz actual no
permite editar tarifas de envío; indica esto si preguntan por ellas.

Formulación: y_i binaria vale 1 si se abre centro i; x_ij >= 0 es el flujo
desde centro i a zona j. Minimizar sum_i(f_i*y_i)+sum_i,sum_j(c_ij*x_ij),
sujeto a sum_i(x_ij)=d_j para cada zona, sum_j(x_ij)<=K_i*y_i para cada
centro, sum_i(y_i)<=P (P=2 en el caso base), además de los dominios de las
variables. La demanda total supera la mayor capacidad individual, por lo que
se necesitan al menos dos centros. El motor MIP resuelve el modelo con
garantía de optimalidad global; el caso tiene 4 variables binarias, 24 continuas,
6 restricciones de demanda, 4 de capacidad y 1 de límite de centros.

Resultado oficial validado: abrir L2 y L3; L1 y L4 quedan cerrados. L2 atiende
Z1–Z3, 12,000/20,000 unidades (60.0%); L3 atiende Z4–Z6,
10,000/12,000 (83.3%). Costo fijo óptimo USD 88,000, transporte USD 94,500,
total USD 182,500; ahorro USD 60,500/mes (24.90%) o USD 726,000/año. El
ahorro frente al baseline reduce USD 37,000 fijos y USD 23,500 variables.
La mejor alternativa siguiente es L2+L4 a USD 183,000, solo USD 500 más.
La comprobación de las seis parejas dio: L2+L3 182,500; L2+L4 183,000;
L1+L4 187,000; L1+L3 190,500; L3+L4 197,500; L1+L2 213,000 USD.

Sensibilidad documentada: con fletes globales +10%, L2+L3 cuesta USD 191,950
y ahorra 21.01%; con +15% y +20% conviene L2+L4 (USD 196,650 y 201,200).
Un aumento de 10% solo en rutas desde L3 cambia a L2+L4. Si el fijo de L3
supera USD 38,500, L4 gana; capacidad L3 de 9,000 también cambia a L2+L4.
Con capacidad L3 de 15,000 se reporta L1+L3 por USD 181,500. La frontera de
decisión L3/L4 es sensible porque la diferencia base es de USD 500. Los
escenarios probados mantuvieron ahorros superiores al 17%; con máximo dos
centros la capacidad combinada máxima es 36,000.

Metodología y alcance: se eligió MIP frente al transporte/PL (no modela el
costo fijo) y a enumerar manualmente (no escala). Se comprobó el resultado
contra las seis parejas. El informe también describe un prototipo previo de
pronóstico lineal con 12 meses simulados (22,206 unidades pronosticadas y
2.75% de error retrospectivo en esa simulación); no son datos reales ni una
función implementada en esta interfaz. No prometas precisión de pronóstico.
Limitaciones/reglas: el modelo solo incluye costos fijos, tarifas y
capacidades definidos; no modela contratos vigentes, costos de cierre/traslado,
estacionalidad ni factores externos. Las decisiones deben revisarse con
criterio gerencial y datos reales, especialmente L3 vs L4.

MANUAL DEL SOFTWARE
El Dashboard muestra escenario, parámetros, KPIs, comparativa de costos,
utilización de capacidad y exportación a PDF. Los campos inician en modo protegido.
Para simular, habilita edición, cambia costos fijos/capacidades/demandas/máximo de
centros/baseline (o carga CSV/Excel), guarda los cambios y ejecuta la optimización;
Restaurar Base vuelve al caso oficial. La matriz presenta las asignaciones y permite
exportar CSV/Excel. Los costos de envío permanecen en la matriz oficial y no tienen
controles de edición en la versión actual. La navegación lateral abre Dashboard, Matriz,
Manual, Licencia y este asistente.
`;
