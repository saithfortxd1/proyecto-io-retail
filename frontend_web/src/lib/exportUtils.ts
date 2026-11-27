import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import * as XLSX from 'xlsx';
import {
  COSTOS_ENVIO_DEFAULT,
  UBICACIONES_DEFAULT,
  ZONAS_DEFAULT,
} from '../data/defaults.ts';
import type {
  ChartImpactReport,
  OptimizationResult,
  ScenarioParameters,
} from '../types.ts';

export function validateParameters(params: ScenarioParameters): ScenarioParameters {
  if (params.max_centros < 1 || params.max_centros > UBICACIONES_DEFAULT.length) {
    throw new Error('Máximo de centros: elige un valor entre 1 y 4.');
  }
  if (params.costos_fijos.some((c) => !Number.isFinite(c) || c < 0)) {
    throw new Error('Los costos fijos no pueden ser negativos.');
  }
  if (params.capacidades.some((c) => !Number.isFinite(c) || c <= 0)) {
    throw new Error('Las capacidades deben ser mayores que cero.');
  }
  if (params.demandas.some((d) => !Number.isFinite(d) || d < 0)) {
    throw new Error('Las demandas no pueden ser negativas.');
  }
  if (!Number.isFinite(params.costo_baseline) || params.costo_baseline <= 0) {
    throw new Error('El costo baseline debe ser mayor que cero.');
  }
  return params;
}

function normalizeHeader(h: string): string {
  return h
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase();
}

function normalizeParamKey(rawKey: string): string {
  const k = normalizeHeader(rawKey).replace(/[\s-]+/g, '_');
  const centerAlias: Record<string, number> = { l1: 0, l2: 1, l3: 2, l4: 3 };
  const zoneAlias: Record<string, number> = {
    z1: 0,
    z2: 1,
    z3: 2,
    z4: 3,
    z5: 4,
    z6: 5,
  };

  for (const [label, idx] of Object.entries(centerAlias)) {
    if (k === `costo_fijo_${label}` || k === `${label}_costo_fijo`) {
      return `costo_fijo_${idx}`;
    }
    if (k === `capacidad_${label}` || k === `${label}_capacidad`) {
      return `capacidad_${idx}`;
    }
  }
  for (const [label, idx] of Object.entries(zoneAlias)) {
    if (k === `demanda_${label}` || k === `${label}_demanda` || k === label) {
      return `demanda_${idx}`;
    }
  }
  if (k === 'max_cds' || k === 'maximo_centros' || k === 'p') {
    return 'max_centros';
  }
  if (k === 'costo_baseline' || k === 'baseline_usd') {
    return 'baseline';
  }
  return k;
}

function parseNumericCell(raw: unknown, key: string): number {
  const str = String(raw ?? '')
    .replace(/\u00A0/g, '')
    .replace(/[$€]/g, '')
    .replace(/usd|u\/mes|unidades/gi, '')
    .replace(/,/g, '')
    .trim();

  if (!str) {
    throw new Error(`Valor vacío para '${key}'.`);
  }
  const parsed = Number(str);
  if (!Number.isFinite(parsed)) {
    throw new Error(`Valor numérico inválido para '${key}': "${String(raw)}"`);
  }
  return Math.round(parsed);
}

export async function parseImportedScenarioFile(
  file: File,
  currentParams: ScenarioParameters
): Promise<{ params: ScenarioParameters; importedCount: number }> {
  const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
  let workbook: XLSX.WorkBook;

  if (ext === 'csv' || file.type === 'text/csv') {
    const rawText = await file.text();
    const cleanedText = rawText.replace(/^\uFEFF/, '');
    const firstLine = cleanedText.split(/\r?\n/)[0] ?? '';
    const fs = firstLine.includes(';') && !firstLine.includes(',') ? ';' : ',';
    workbook = XLSX.read(cleanedText, { type: 'string', FS: fs });
  } else {
    const buffer = await file.arrayBuffer();
    workbook = XLSX.read(buffer, { type: 'array' });
  }

  const firstSheetName = workbook.SheetNames[0];
  if (!firstSheetName) {
    throw new Error('El archivo no contiene hojas válidas.');
  }
  const sheet = workbook.Sheets[firstSheetName];
  const rows = XLSX.utils.sheet_to_json<Record<string, unknown>>(sheet, { defval: '' });

  if (rows.length === 0) {
    throw new Error(
      "El archivo está vacío. Columnas requeridas: 'parametro' y 'valor'."
    );
  }

  const firstKeys = Object.keys(rows[0]).map(normalizeHeader);
  if (!firstKeys.includes('parametro') || !firstKeys.includes('valor')) {
    throw new Error("Columnas requeridas: 'parametro' y 'valor'");
  }

  const rawMap = new Map<string, number>();
  for (const row of rows) {
    const normalizedRow: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(row)) {
      normalizedRow[normalizeHeader(k)] = v;
    }
    const rawKey = String(normalizedRow['parametro'] ?? '').trim();
    const rawVal = normalizedRow['valor'];
    if (rawKey && String(rawVal ?? '').trim() !== '') {
      const canonicalKey = normalizeParamKey(rawKey);
      rawMap.set(canonicalKey, parseNumericCell(rawVal, rawKey));
    }
  }

  const next: ScenarioParameters = {
    costos_fijos: [...currentParams.costos_fijos],
    capacidades: [...currentParams.capacidades],
    demandas: [...currentParams.demandas],
    max_centros: currentParams.max_centros,
    costo_baseline: currentParams.costo_baseline,
  };

  let importedCount = 0;

  for (let i = 0; i < 4; i++) {
    const cf = rawMap.get(`costo_fijo_${i}`);
    if (cf !== undefined) {
      next.costos_fijos[i] = cf;
      importedCount++;
    }
    const cap = rawMap.get(`capacidad_${i}`);
    if (cap !== undefined) {
      next.capacidades[i] = cap;
      importedCount++;
    }
  }

  for (let j = 0; j < 6; j++) {
    const dem = rawMap.get(`demanda_${j}`);
    if (dem !== undefined) {
      next.demandas[j] = dem;
      importedCount++;
    }
  }

  const maxCentros = rawMap.get('max_centros');
  if (maxCentros !== undefined) {
    next.max_centros = maxCentros;
    importedCount++;
  }

  const baseline = rawMap.get('baseline');
  if (baseline !== undefined) {
    next.costo_baseline = baseline;
    importedCount++;
  }

  if (importedCount === 0) {
    throw new Error(
      'No se reconocieron claves válidas (ej. costo_fijo_0, capacidad_0, demanda_0, max_centros, baseline).'
    );
  }

  validateParameters(next);
  return { params: next, importedCount };
}

export function exportScenarioTemplateCsv(params: ScenarioParameters): void {
  const lines = ['parametro,valor'];
  params.costos_fijos.forEach((v, i) => lines.push(`costo_fijo_${i},${v}`));
  params.capacidades.forEach((v, i) => lines.push(`capacidad_${i},${v}`));
  params.demandas.forEach((v, j) => lines.push(`demanda_${j},${v}`));
  lines.push(`max_centros,${params.max_centros}`);
  lines.push(`baseline,${params.costo_baseline}`);

  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'Plantilla_Escenario_MIP.csv';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function exportMatrixCsv(
  result: OptimizationResult,
  params: ScenarioParameters
): void {
  const headers = ['Centro', 'Zona', 'Unidades', 'Costo_Unit', 'Costo_Ruta', 'Pct_Demanda'];
  const lines = [headers.join(',')];

  for (const a of result.asignaciones) {
    const i = UBICACIONES_DEFAULT.indexOf(a.Ubicacion);
    const j = ZONAS_DEFAULT.indexOf(a.Zona);
    const costoU = COSTOS_ENVIO_DEFAULT[i]?.[j] ?? 0;
    const costoR = a.Cantidad_Enviada * costoU;
    const demand = params.demandas[j] ?? 0;
    const pct = demand > 0 ? (a.Cantidad_Enviada / demand) * 100 : 0;

    lines.push(
      [
        a.Ubicacion,
        a.Zona,
        a.Cantidad_Enviada,
        costoU.toFixed(2),
        costoR.toFixed(2),
        pct.toFixed(2),
      ].join(',')
    );
  }

  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'Matriz_Asignacion_Logistica.csv';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function exportExecutiveExcel(
  result: OptimizationResult,
  params: ScenarioParameters
): void {
  const wb = XLSX.utils.book_new();

  const summaryRows = [
    ['MIP Retail Optimizer™ Enterprise'],
    ['Indicador', 'Resultado'],
    ['Estado', result.estado],
    ['Centros abiertos', result.centros_abiertos.join(', ')],
    ['Costo baseline (USD/mes)', params.costo_baseline],
    ['Costo fijo (USD/mes)', result.costo_fijo],
    ['Costo de transporte (USD/mes)', result.costo_variable],
    ['Costo total óptimo (USD/mes)', result.costo_total],
    ['Ahorro mensual (USD/mes)', result.ahorro],
    ['Ahorro anual (USD/año)', result.ahorro * 12],
    ['Ahorro (%)', Number(result.porcentaje_ahorro.toFixed(2))],
  ];
  const summarySheet = XLSX.utils.aoa_to_sheet(summaryRows);
  summarySheet['!cols'] = [{ wch: 34 }, { wch: 28 }];
  XLSX.utils.book_append_sheet(wb, summarySheet, 'Resumen');

  const routeRows: (string | number)[][] = [
    [
      'Centro',
      'Zona',
      'Unidades',
      'Costo unitario (USD)',
      'Costo de ruta (USD)',
      'Demanda atendida (%)',
    ],
  ];

  for (const a of result.asignaciones) {
    const i = UBICACIONES_DEFAULT.indexOf(a.Ubicacion);
    const j = ZONAS_DEFAULT.indexOf(a.Zona);
    const unitCost = COSTOS_ENVIO_DEFAULT[i]?.[j] ?? 0;
    const demand = params.demandas[j] ?? 0;
    const pct = demand > 0 ? (a.Cantidad_Enviada / demand) * 100 : 0;

    routeRows.push([
      a.Ubicacion,
      a.Zona,
      a.Cantidad_Enviada,
      unitCost,
      a.Cantidad_Enviada * unitCost,
      Number(pct.toFixed(2)),
    ]);
  }

  const routesSheet = XLSX.utils.aoa_to_sheet(routeRows);
  routesSheet['!cols'] = [
    { wch: 16 },
    { wch: 14 },
    { wch: 16 },
    { wch: 24 },
    { wch: 22 },
    { wch: 24 },
  ];
  XLSX.utils.book_append_sheet(wb, routesSheet, 'Asignaciones');

  XLSX.writeFile(wb, 'Reporte_Ejecutivo_MIP_Retail_Optimizer.xlsx');
}

function fmtUsd(value: number, decimals = 0): string {
  return `$${value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })} USD`;
}

function fmtUnits(value: number): string {
  return `${value.toLocaleString('en-US', { maximumFractionDigits: 0 })} u/mes`;
}

export function exportDashboardPdf(
  result: OptimizationResult,
  params: ScenarioParameters,
  impact?: ChartImpactReport
): void {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const totalDemand = params.demandas.reduce((a, b) => a + b, 0);
  const nowStr = new Date().toLocaleString('es-MX', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });

  // 1. Header Banner
  doc.setFillColor(15, 23, 42);
  doc.rect(0, 0, pageWidth, 28, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(16);
  doc.text('MIP Retail Optimizer™ Enterprise', 14, 12);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9.5);
  doc.setTextColor(203, 213, 225);
  doc.text(
    'Reporte Ejecutivo de Optimización Logística (Modelo CFLP)',
    14,
    19
  );
  doc.text(`Generado: ${nowStr}`, pageWidth - 14, 12, { align: 'right' });
  doc.text(
    `Máx. CDs: ${params.max_centros} · Demanda: ${fmtUnits(totalDemand)}`,
    pageWidth - 14,
    19,
    { align: 'right' }
  );

  // 2. KPI Cards Row
  const kpis = [
    {
      label: 'Costo Total Óptimo',
      value: fmtUsd(result.costo_total),
      sub: `Baseline: ${fmtUsd(params.costo_baseline)}`,
      color: [37, 99, 235] as [number, number, number],
    },
    {
      label: 'Ahorro Mensual',
      value: `${fmtUsd(result.ahorro)} (${result.porcentaje_ahorro.toFixed(2)}%)`,
      sub: `Anual: ${fmtUsd(result.ahorro * 12)}`,
      color: [5, 150, 105] as [number, number, number],
    },
    {
      label: 'Centros Abiertos',
      value: result.centros_abiertos.join(', '),
      sub: `${result.centros_abiertos.length} de ${params.max_centros} permitidos`,
      color: [217, 119, 6] as [number, number, number],
    },
    {
      label: 'Demanda Cubierta',
      value: fmtUnits(totalDemand),
      sub: 'Nivel de servicio: 100.0%',
      color: [5, 150, 105] as [number, number, number],
    },
  ];

  const cardW = (pageWidth - 28 - 9) / 4;
  kpis.forEach((kpi, idx) => {
    const x = 14 + idx * (cardW + 3);
    const y = 33;
    doc.setFillColor(248, 250, 252);
    doc.setDrawColor(203, 213, 225);
    doc.roundedRect(x, y, cardW, 21, 2.5, 2.5, 'FD');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(7.5);
    doc.setTextColor(100, 116, 139);
    doc.text(kpi.label, x + 3, y + 6);

    doc.setFontSize(9);
    doc.setTextColor(kpi.color[0], kpi.color[1], kpi.color[2]);
    doc.text(kpi.value, x + 3, y + 12.5);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(6.8);
    doc.setTextColor(71, 85, 105);
    doc.text(kpi.sub, x + 3, y + 18);
  });

  // 3. Vector Charts Side by Side (Baseline vs Optimal + Capacity Utilization L1-L4)
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10.5);
  doc.setTextColor(15, 23, 42);
  doc.text('1. Gráficas de Desempeño y Utilización de Capacidad', 14, 62);

  const chartY = 65;
  const chartW = (pageWidth - 28 - 4) / 2;
  const chartH = 48;

  // Left Chart Box: Baseline vs Optimal
  doc.setFillColor(255, 255, 255);
  doc.setDrawColor(203, 213, 225);
  doc.roundedRect(14, chartY, chartW, chartH, 2.5, 2.5, 'FD');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8.5);
  doc.setTextColor(15, 23, 42);
  doc.text('Comparativa: Baseline vs. Optimizado (USD/mes)', 18, chartY + 6.5);

  const maxBarVal = Math.max(params.costo_baseline, result.costo_total, 1) * 1.18;
  const plotBottom = chartY + chartH - 9;
  const plotMaxH = 26;
  const baseH = (params.costo_baseline / maxBarVal) * plotMaxH;
  const optH = (result.costo_total / maxBarVal) * plotMaxH;

  doc.setDrawColor(226, 232, 240);
  doc.line(18, plotBottom, 14 + chartW - 4, plotBottom);

  const barW = 20;
  const baseBarX = 14 + chartW * 0.25 - barW / 2;
  const optBarX = 14 + chartW * 0.72 - barW / 2;

  doc.setFillColor(220, 38, 38);
  doc.rect(baseBarX, plotBottom - baseH, barW, baseH, 'F');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(7.5);
  doc.setTextColor(15, 23, 42);
  doc.text(
    `$${params.costo_baseline.toLocaleString('en-US')}`,
    baseBarX + barW / 2,
    plotBottom - baseH - 2,
    { align: 'center' }
  );
  doc.setFontSize(7);
  doc.setTextColor(71, 85, 105);
  doc.text('Baseline', baseBarX + barW / 2, plotBottom + 5, { align: 'center' });

  doc.setFillColor(5, 150, 105);
  doc.rect(optBarX, plotBottom - optH, barW, optH, 'F');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(7.5);
  doc.setTextColor(5, 150, 105);
  doc.text(
    `$${result.costo_total.toLocaleString('en-US')}`,
    optBarX + barW / 2,
    plotBottom - optH - 2,
    { align: 'center' }
  );
  doc.setFontSize(7);
  doc.setTextColor(71, 85, 105);
  doc.text('Óptimo MIP', optBarX + barW / 2, plotBottom + 5, { align: 'center' });

  // Right Chart Box: Capacity L1-L4
  const rightChartX = 14 + chartW + 4;
  doc.setFillColor(255, 255, 255);
  doc.setDrawColor(203, 213, 225);
  doc.roundedRect(rightChartX, chartY, chartW, chartH, 2.5, 2.5, 'FD');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8.5);
  doc.setTextColor(15, 23, 42);
  doc.text('Utilización de Capacidad por Centro (L1–L4)', rightChartX + 4, chartY + 6.5);

  UBICACIONES_DEFAULT.forEach((center, idx) => {
    const rowY = chartY + 13 + idx * 8.5;
    const cap = params.capacidades[idx] || 1;
    const vol = result.asignaciones
      .filter((a) => a.Ubicacion === center)
      .reduce((acc, a) => acc + a.Cantidad_Enviada, 0);
    const pct = Math.min(100, (vol / cap) * 100);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(7.5);
    doc.setTextColor(15, 23, 42);
    doc.text(center, rightChartX + 5, rowY + 3.5);

    const trackX = rightChartX + 13;
    const trackW = chartW - 36;
    doc.setFillColor(241, 245, 249);
    doc.roundedRect(trackX, rowY, trackW, 4.5, 1, 1, 'F');

    if (pct > 0) {
      if (pct > 80) doc.setFillColor(220, 38, 38);
      else if (pct > 60) doc.setFillColor(217, 119, 6);
      else doc.setFillColor(5, 150, 105);
      doc.roundedRect(trackX, rowY, Math.max(1.5, (trackW * pct) / 100), 4.5, 1, 1, 'F');
    }

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7);
    doc.setTextColor(51, 65, 85);
    doc.text(
      `${pct.toFixed(1)}%${pct === 0 ? ' · Cerr.' : ''}`,
      trackX + trackW + 2,
      rowY + 3.4
    );
  });

  // 4. Visual Network Map: Open Centers -> Zones
  let currentY = chartY + chartH + 7;
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10.5);
  doc.setTextColor(15, 23, 42);
  doc.text('2. Mapa de Red Logística: Centros Abiertos y Asignación a Zonas', 14, currentY);

  const mapTop = currentY + 3.5;
  const mapHeight = 58;
  doc.setFillColor(248, 250, 252);
  doc.setDrawColor(203, 213, 225);
  doc.roundedRect(14, mapTop, pageWidth - 28, mapHeight, 3, 3, 'FD');

  const leftX = 30;
  const rightX = pageWidth - 46;
  const centerPositions: Record<string, { x: number; y: number }> = {};
  const zonePositions: Record<string, { x: number; y: number }> = {};

  UBICACIONES_DEFAULT.forEach((center, idx) => {
    const cy = mapTop + 9.5 + idx * 13;
    centerPositions[center] = { x: leftX + 22, y: cy };
  });

  ZONAS_DEFAULT.forEach((zone, idx) => {
    const zy = mapTop + 6.8 + idx * 8.8;
    zonePositions[zone] = { x: rightX, y: zy };
  });

  result.asignaciones.forEach((a) => {
    const from = centerPositions[a.Ubicacion];
    const to = zonePositions[a.Zona];
    if (!from || !to) return;
    doc.setDrawColor(37, 99, 235);
    doc.setLineWidth(0.5);
    doc.line(from.x, from.y, to.x, to.y);

    const midX = (from.x + to.x) / 2;
    const midY = (from.y + to.y) / 2;
    doc.setFillColor(255, 255, 255);
    doc.rect(midX - 9, midY - 2.2, 18, 4.2, 'F');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(6.5);
    doc.setTextColor(37, 99, 235);
    doc.text(`${a.Cantidad_Enviada.toLocaleString('en-US')} u`, midX, midY + 0.8, {
      align: 'center',
    });
  });

  UBICACIONES_DEFAULT.forEach((center, idx) => {
    const pos = centerPositions[center];
    const isOpen = result.centros_abiertos.includes(center);
    const cy = pos.y;
    const cap = params.capacidades[idx];
    const vol = result.asignaciones
      .filter((a) => a.Ubicacion === center)
      .reduce((acc, a) => acc + a.Cantidad_Enviada, 0);
    const utilPct = cap > 0 ? (vol / cap) * 100 : 0;

    if (isOpen) {
      doc.setFillColor(5, 150, 105);
      doc.setDrawColor(4, 120, 87);
    } else {
      doc.setFillColor(226, 232, 240);
      doc.setDrawColor(148, 163, 184);
    }
    doc.roundedRect(leftX - 10, cy - 4.3, 32, 8.6, 2, 2, 'FD');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(7.5);
    doc.setTextColor(isOpen ? 255 : 71, isOpen ? 255 : 85, isOpen ? 255 : 105);
    doc.text(
      `${center} · ${isOpen ? `${utilPct.toFixed(0)}%` : 'Cerrado'}`,
      leftX + 6,
      cy + 1,
      { align: 'center' }
    );
  });

  ZONAS_DEFAULT.forEach((zone, idx) => {
    const pos = zonePositions[zone];
    const demand = params.demandas[idx];
    doc.setFillColor(239, 246, 255);
    doc.setDrawColor(147, 197, 253);
    doc.roundedRect(pos.x, pos.y - 3.4, 28, 6.8, 1.5, 1.5, 'FD');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(7);
    doc.setTextColor(30, 64, 175);
    doc.text(
      `${zone}: ${demand.toLocaleString('en-US')} u`,
      pos.x + 14,
      pos.y + 0.8,
      { align: 'center' }
    );
  });

  // 5. Financial Summary Table (Bottom of Page 1)
  currentY = mapTop + mapHeight + 7;
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10.5);
  doc.setTextColor(15, 23, 42);
  doc.text('3. Resumen Financiero y Comparativa de Costos', 14, currentY);

  autoTable(doc, {
    startY: currentY + 3,
    margin: { left: 14, right: 14 },
    head: [['Concepto Financiero', 'Valor Mensual', 'Detalle / Impacto Anual']],
    body: [
      [
        'Costo Baseline (Operación Actual)',
        fmtUsd(params.costo_baseline),
        `${fmtUsd(params.costo_baseline * 12)} / año`,
      ],
      [
        'Costo Fijo de Apertura (CDs Activos)',
        fmtUsd(result.costo_fijo),
        `Centros abiertos: ${result.centros_abiertos.join(', ')}`,
      ],
      [
        'Costo Variable de Transporte',
        fmtUsd(result.costo_variable),
        `${result.asignaciones.length} rutas activas`,
      ],
      [
        'Costo Total Óptimo (Modelo MIP)',
        fmtUsd(result.costo_total),
        `${fmtUsd(result.costo_total * 12)} / año`,
      ],
      [
        'Ahorro Neto Logrado',
        `${fmtUsd(result.ahorro)} (${result.porcentaje_ahorro.toFixed(2)}%)`,
        `${fmtUsd(result.ahorro * 12)} liberados / año`,
      ],
    ],
    headStyles: { fillColor: [37, 99, 235], textColor: 255, fontSize: 8 },
    bodyStyles: { fontSize: 8, textColor: [15, 23, 42] },
    alternateRowStyles: { fillColor: [248, 250, 252] },
  });

  // Page 2: Centers + Routes Matrix + Demands + Executive AI Impact Analysis
  doc.addPage();
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10.5);
  doc.setTextColor(15, 23, 42);
  doc.text('4. Capacidad, Costos Fijos y Utilización por Centro (L1–L4)', 14, 16);

  const centerRows = UBICACIONES_DEFAULT.map((center, idx) => {
    const isOpen = result.centros_abiertos.includes(center);
    const cap = params.capacidades[idx];
    const vol = result.asignaciones
      .filter((a) => a.Ubicacion === center)
      .reduce((acc, a) => acc + a.Cantidad_Enviada, 0);
    const pct = cap > 0 ? (vol / cap) * 100 : 0;

    return [
      center,
      isOpen ? 'Operativo' : 'Cerrado',
      fmtUsd(params.costos_fijos[idx]),
      fmtUnits(cap),
      fmtUnits(vol),
      `${pct.toFixed(1)}%`,
    ];
  });

  autoTable(doc, {
    startY: 19,
    margin: { left: 14, right: 14 },
    head: [['Centro', 'Estado', 'Costo Fijo', 'Capacidad', 'Volumen Asignado', 'Utilización']],
    body: centerRows,
    headStyles: { fillColor: [15, 23, 42], textColor: 255, fontSize: 8 },
    bodyStyles: { fontSize: 8, textColor: [15, 23, 42] },
    alternateRowStyles: { fillColor: [248, 250, 252] },
  });

  let nextY =
    (doc as jsPDF & { lastAutoTable?: { finalY: number } }).lastAutoTable?.finalY ?? 65;
  nextY += 8;

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10.5);
  doc.setTextColor(15, 23, 42);
  doc.text('5. Matriz de Rutas Óptimas (Centro Origen → Zona Destino)', 14, nextY);

  const routeRows = result.asignaciones.map((a) => {
    const i = UBICACIONES_DEFAULT.indexOf(a.Ubicacion);
    const j = ZONAS_DEFAULT.indexOf(a.Zona);
    const unitCost = COSTOS_ENVIO_DEFAULT[i]?.[j] ?? 0;
    const routeCost = a.Cantidad_Enviada * unitCost;
    const demand = params.demandas[j] ?? 0;
    const pct = demand > 0 ? (a.Cantidad_Enviada / demand) * 100 : 0;

    return [
      a.Ubicacion,
      a.Zona,
      fmtUnits(a.Cantidad_Enviada),
      fmtUsd(unitCost, 2),
      fmtUsd(routeCost, 2),
      `${pct.toFixed(1)}%`,
    ];
  });

  autoTable(doc, {
    startY: nextY + 3,
    margin: { left: 14, right: 14 },
    head: [
      [
        'Centro Origen',
        'Zona Destino',
        'Unidades',
        'Costo Unitario',
        'Costo Total Ruta',
        '% Demanda Zona',
      ],
    ],
    body: routeRows,
    headStyles: { fillColor: [5, 150, 105], textColor: 255, fontSize: 8 },
    bodyStyles: { fontSize: 8, textColor: [15, 23, 42] },
    alternateRowStyles: { fillColor: [248, 250, 252] },
  });

  nextY =
    (doc as jsPDF & { lastAutoTable?: { finalY: number } }).lastAutoTable?.finalY ?? 130;
  nextY += 8;

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10.5);
  doc.setTextColor(15, 23, 42);
  doc.text('6. Parámetros de Demanda por Zona (Z1–Z6)', 14, nextY);

  autoTable(doc, {
    startY: nextY + 3,
    margin: { left: 14, right: 14 },
    head: [['Zona', 'Demanda Mensual', 'Participación (%)']],
    body: ZONAS_DEFAULT.map((z, j) => {
      const d = params.demandas[j];
      const share = totalDemand > 0 ? (d / totalDemand) * 100 : 0;
      return [z, fmtUnits(d), `${share.toFixed(1)}%`];
    }),
    headStyles: { fillColor: [71, 85, 105], textColor: 255, fontSize: 8 },
    bodyStyles: { fontSize: 8, textColor: [15, 23, 42] },
    alternateRowStyles: { fillColor: [248, 250, 252] },
  });

  nextY =
    (doc as jsPDF & { lastAutoTable?: { finalY: number } }).lastAutoTable?.finalY ?? 185;
  nextY += 8;

  const hasGeminiNotes = Boolean(
    impact && (impact.costImpactReport || impact.capacityImpactReport)
  );
  const analysisHeading = hasGeminiNotes
    ? '7. Informe Ejecutivo de Impacto (Gemini IA)'
    : '7. Conclusiones Operativas del Escenario';

  const fallbackAnalysis = [
    `Impacto en Costos: El diseño óptimo reduce el costo mensual de ${fmtUsd(
      params.costo_baseline
    )} a ${fmtUsd(result.costo_total)}, logrando un ahorro de ${fmtUsd(
      result.ahorro
    )} (${result.porcentaje_ahorro.toFixed(2)}%) mensual o ${fmtUsd(
      result.ahorro * 12
    )} anual.`,
    `Red Activa: Operan ${result.centros_abiertos.join(
      ' y '
    )} cubriendo el 100.0% de las ${fmtUnits(
      totalDemand
    )} demandadas en Z1–Z6 con ${result.asignaciones.length} rutas asignadas.`,
  ].join('\n\n');

  const analysisText = hasGeminiNotes
    ? [
        impact?.costImpactReport ? `Impacto en Costos: ${impact.costImpactReport}` : '',
        impact?.capacityImpactReport
          ? `Impacto en Capacidad y Red: ${impact.capacityImpactReport}`
          : '',
      ]
        .filter(Boolean)
        .join('\n\n')
    : fallbackAnalysis;

  if (nextY > pageHeight - 36) {
    doc.addPage();
    nextY = 18;
  }

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10.5);
  doc.setTextColor(15, 23, 42);
  doc.text(analysisHeading, 14, nextY);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8.5);
  doc.setTextColor(51, 65, 85);
  const wrapped = doc.splitTextToSize(analysisText, pageWidth - 28);
  doc.text(wrapped, 14, nextY + 5.5);

  // Page Footers
  const totalPages = doc.getNumberOfPages();
  for (let p = 1; p <= totalPages; p++) {
    doc.setPage(p);
    doc.setDrawColor(226, 232, 240);
    doc.line(14, pageHeight - 11, pageWidth - 14, pageHeight - 11);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7.5);
    doc.setTextColor(100, 116, 139);
    doc.text('MIP Retail Optimizer™ Enterprise · Motor CFLP', 14, pageHeight - 6.5);
    doc.text(`Página ${p} de ${totalPages}`, pageWidth - 14, pageHeight - 6.5, {
      align: 'right',
    });
  }

  doc.save('Reporte_Ejecutivo_MIP_Retail_Optimizer.pdf');
}
