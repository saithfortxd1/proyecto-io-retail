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
| `interfaz.py` | **Interfaz gráfica Enterprise** (customtkinter) con pantalla completa, **modo protegido por defecto** con valores oficiales, **simulador interactivo desbloqueable** (pestañas editables, candado de solo lectura, botón restauración), **KPIs ejecutivos**, **gráficos duales**, **importación/exportación de escenarios (CSV/Excel)**, **reporte ejecutivo multi-hoja**, **modal ROI** y **modal Licencia** |
| `asignacion_logistica.csv` | Plan de asignación óptima (Centro → Zona, unidades) |
| `documentacion_tecnica.md` | Informe técnico completo (secciones 1-5, 7-8, 13-15, referencias APA, Anexo A) |
| `pitch_comercial.md` | Modelo de negocio, justificación financiera, ROI y propuesta de valor |
| `requirements.txt` | Dependencias Python para desarrollo |
| `MIP_Retail_Optimizer.exe` | **Ejecutable standalone Windows** (ver sección Releases) |

---

## Arquitectura de Ramas (Git Workflow)

| Rama | Propósito | Estado |
|------|-----------|--------|
| **`main`** | **Producto comercial completo** — Incluye versión base oficial ($182,500 USD / 24.90% ahorro) **y** simulador interactivo desbloqueable. Al iniciar, la interfaz muestra los valores oficiales en **modo protegido (solo lectura)**. Un clic en **"🔓 Habilitar Edición"** + confirmación activa el simulador completo (pestañas editables, recálculo en vivo, botón **✅ Confirmar y Recalcular**, y **↩ Restaurar Valores Base** que vuelve al caso oficial). Incluye **KPIs ejecutivos**, **gráficos duales**, **importación/exportación de escenarios**, **reporte ejecutivo multi-hoja (.xlsx/.csv)**, **modal ROI/Licencia** y **ejecutable standalone Windows**. | 🟢 Oficial / Completa |

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

- Python 3.8+
- `pip install -r requirements.txt`

```bash
pip install -r requirements.txt
```

**Nota:** Para uso comercial directo **no se requiere Python**. Descargue `MIP_Retail_Optimizer.exe` desde [Releases](https://github.com/saithfortxd1/proyecto-io-retail/releases) y ejecútelo directamente en Windows 10/11.

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
- KPIs tarjetas, gráficos duales, tabla asignación, exportación reporte multi-hoja.

---

## Compilación del Ejecutable (Solo Desarrolladores)

```bash
pip install -r requirements.txt
pyinstaller --noconfirm --onefile --windowed \
  --name "MIP_Retail_Optimizer" \
  --collect-all pulp \
  --collect-all customtkinter \
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