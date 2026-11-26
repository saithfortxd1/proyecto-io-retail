# MIP Retail Optimizer™ Enterprise - Optimización Logística de Centros de Distribución

## Descripción del Proyecto

**MIP Retail Optimizer™ Enterprise** es una solución de software comercial lista para producción, basada en **Programación Entera Mixta (MIP)**, para el diseño óptimo de redes de centros de distribución en el sector retail. El modelo determina la configuración óptima de apertura de centros y asignación de flujos a zonas de demanda, minimizando el costo logístico total sujeto a restricciones operativas reales.

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
| `interfaz.py` | **Interfaz gráfica Enterprise** (customtkinter) con pantalla completa, modo protegido, simulador de escenarios, KPIs, gráficas de costos y capacidad visibles desde el inicio, exportación CSV/Excel y Asistente IA Gemini con contexto dinámico |
| `asignacion_logistica.csv` | Plan de asignación óptima (Centro → Zona, unidades) |
| `documentacion_tecnica.md` | Informe técnico completo (secciones 1-5, 7-8, 13-15, referencias APA, Anexo A) |
| `pitch_comercial.md` | Modelo de negocio, justificación financiera, ROI y propuesta de valor |
| `requirements.txt` | Dependencias Python para desarrollo |
| `MIP_Retail_Optimizer.exe` | **Ejecutable standalone Windows** (ver sección Releases) |

---

## Arquitectura de Ramas (Git Workflow)

| Rama | Propósito | Estado |
|------|-----------|--------|
| **`main`** | **Producto comercial completo** — Caso base oficial ($182,500 USD / 24.90% ahorro), simulador interactivo, gráficas desde el inicio, exportación de escenarios y Asistente IA con Gemini. Los campos inician protegidos y la API Key se configura localmente. | 🟢 Oficial / Completa |

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

## Características Comerciales (Enterprise)

| Capacidad | Descripción |
|-----------|-------------|
| **🔒 Modo Protegido por Defecto** | Arranca con valores oficiales bloqueados (`readonly`), etiqueta `🔒 Modo Protegido`. Evita modificaciones accidentales en demos en vivo. |
| **🔓 Simulador Interactivo Desbloqueable** | Botón `🔓 Habilitar Edición` → confirmación → pestañas editables (Centros, Demandas, Configuración) → `✅ Confirmar y Recalcular` → recálculo instantáneo → **vuelve a modo protegido automáticamente**. |
| **↩ Restauración Segura** | Botón `↩ Restaurar Valores Base` → confirmación → valores oficiales + recálculo automático + modo protegido. |
| **📂 Importar Escenarios** | Carga parámetros desde archivos `.csv` o `.xlsx` con columnas `parametro` / `valor`. |
| **📊 Exportar Reporte Ejecutivo** | Genera **Excel multi-hoja** (Resumen Ejecutivo, KPIs Detallados, Matriz de Asignación, Parámetros Escenario) y **CSV** listos para gerencia. |
| **💼 Modal Licencia y ROI** | Botón `💼 Licencia y ROI` en header abre modal ejecutivo con propuesta de valor, ROI (>300%), payback (<3 meses), modelo de negocio 3 fases y beneficios clave. |
| **📈 Dashboard Analítico Dual** | KPIs tarjetas (Total, Ahorro, Centros, Nivel Servicio) + 2 gráficos: (1) Baseline vs Optimizado, (2) Desglose Fijo/Variable + Utilización capacidad por centro. |
| **🖥️ Ejecutable Standalone Windows** | `MIP_Retail_Optimizer.exe` compilado con PyInstaller (`--collect-all pulp --collect-all customtkinter`). **Sin dependencias de Python**. Incluye solver CBC embebido. Ideal para clientes, demos en vivo y distribución comercial. |
| **🌐 Pantalla Completa Nativa** | `F11` alterna, `Esc` sale. Optimizado para presentaciones ejecutivas. |

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

## Requisitos (Solo para Desarrollo)

- Python 3.10+
- `pip install -r requirements.txt`

```bash
pip install -r requirements.txt
```

**Nota:** Para uso comercial directo **no se requiere Python**. Descargue `MIP_Retail_Optimizer.exe` desde [Releases](https://github.com/saithfortxd1/proyecto-io-retail/releases) y ejecútelo directamente en Windows 10/11.

### Configurar Gemini (opcional)

La optimización PuLP/CBC funciona sin internet. El Asistente IA requiere conexión y una API Key de Google AI Studio:

1. Copia `.env.example` como `.env` junto a `interfaz.py` y configura `GEMINI_API_KEY=tu_clave`.
2. Alternativamente, en la aplicación pulsa **🔑 Configurar API Key** para guardarla en `config_ia.json` junto al programa (en el `.exe`, junto al ejecutable).
3. `.env` y `config_ia.json` están excluidos de Git. No compartas ni subas claves; `.env.example` solo contiene un valor de muestra.

Al enviar una pregunta, el asistente incluye los costos fijos, capacidades, demandas, baseline, centros abiertos, último resultado y matriz de tarifas vigente. La matriz de tarifas actualmente no es editable desde la interfaz. Las consultas corren en un hilo secundario; si Gemini no está disponible, las demás funciones continúan operando.

---

## Ejecución (Modo Desarrollo)

### Motor matemático (CLI)
```bash
python optimizacion.py
```
Genera `asignacion_logistica.csv` e imprime resultados en consola (caso base oficial).

### Interfaz Gráfica Enterprise (Modo Completo)
```bash
python interfaz.py
```
- **Al iniciar**: Ventana maximizada, **modo protegido** con valores oficiales ($182,500 USD / 24.90%), etiqueta `🔒 Modo Protegido`, botón `🔓 Habilitar Edición`.
- **Simulador interactivo**: Clic en `🔓 Habilitar Edición` → confirmación → pestañas editables (Centros, Demandas, Configuración) → `✅ Confirmar y Recalcular` → recálculo instantáneo → **vuelve a modo protegido** automáticamente.
- **Restauración**: Botón `↩ Restaurar Valores Base` → confirmación → valores oficiales + recálculo automático + modo protegido.
- **Importar/Exportar**: `📂 Importar Escenario` (.csv/.xlsx) | `📊 Exportar Reporte Ejecutivo` (.xlsx/.csv).
- **ROI/Licencia**: Botón `💼 Licencia y ROI` en header → modal ejecutivo con propuesta de valor, ROI >300%, payback <3 meses, modelo 3 fases.
- **Pantalla completa**: `F11` alterna, `Esc` sale.
- Gráficas de costo baseline/óptimo y capacidad por centro visibles desde el arranque y actualizadas tras cada cálculo.
- **Asistente IA** desde el sidebar o el Dashboard: explicación del modelo, resultados actuales y guía de uso; incluye preguntas rápidas.
- KPIs tarjetas, tabla de asignación y exportación de reportes.

---

## Compilación del Ejecutable (Solo Desarrolladores)

```bash
pip install -r requirements.txt
pyinstaller --noconfirm --onefile --windowed \
  --name "MIP_Retail_Optimizer" \
  --collect-all pulp \
  --collect-all customtkinter \
  --collect-all google.genai \
  interfaz.py
```

**Resultado:** `dist/MIP_Retail_Optimizer.exe` (standalone, incluye solver CBC embebido, ~150-200 MB).

**Archivos generados ignorados por Git:**
- `build/` - archivos temporales de compilación
- `dist/` - ejecutable final
- `*.spec` - archivo de especificación PyInstaller

---

## Solucionador

Utiliza **CBC (Coin-or Branch and Cut)** vía PuLP. Tiempo de resolución típico: < 0.1 segundos. Optimalidad garantizada (gap = 0%). El ejecutable incluye el solver CBC embebido (`pulp.solverdir`), funcionando **sin instalación externa**.

---

## Aplicaciones Comerciales

- **Network Design** para retail, e-commerce, distribución mayorista
- **Análisis de escenarios** (crecimiento de demanda, variación de costos, nuevas ubicaciones)
- **Due diligence** de inversiones en infraestructura logística
- **Herramienta didáctica ejecutiva** para MIP aplicado a supply chain
- **Demo en vivo** para clientes: modo protegido → desbloquear → simular → restaurar

---

## Licencia

Producto comercial / demostrativo. Licencia propietaria. Contactar para términos de uso comercial.

---

## Autor y Contacto

Desarrollado como parte de proyecto final de investigación en optimización logística.
**MIP Retail Optimizer™ Enterprise** - Sistema de Optimización Logística y Diseño de Redes de Distribución.