import { useMemo, useState } from 'react';
import { FileSpreadsheet, FileText } from 'lucide-react';
import {
  COSTOS_ENVIO_DEFAULT,
  UBICACIONES_DEFAULT,
  ZONAS_DEFAULT,
} from '../data/defaults.ts';
import { exportExecutiveExcel, exportMatrixCsv } from '../lib/exportUtils.ts';
import type {
  OptimizationResult,
  ScenarioParameters,
  ToastKind,
} from '../types.ts';

interface MatrixViewProps {
  result: OptimizationResult | null;
  params: ScenarioParameters;
  onNotify: (message: string, kind?: ToastKind) => void;
}

export function MatrixView({ result, params, onNotify }: MatrixViewProps) {
  const [filterCenter, setFilterCenter] = useState<string>('ALL');

  const rows = useMemo(() => {
    if (!result || result.estado !== 'Optimal') return [];
    return result.asignaciones
      .filter((a) => filterCenter === 'ALL' || a.Ubicacion === filterCenter)
      .map((a) => {
        const i = UBICACIONES_DEFAULT.indexOf(a.Ubicacion);
        const j = ZONAS_DEFAULT.indexOf(a.Zona);
        const unitCost = COSTOS_ENVIO_DEFAULT[i]?.[j] ?? 0;
        const routeCost = a.Cantidad_Enviada * unitCost;
        const demand = params.demandas[j] ?? 0;
        const pct = demand > 0 ? (a.Cantidad_Enviada / demand) * 100 : 0;

        return {
          centro: a.Ubicacion,
          zona: a.Zona,
          unidades: a.Cantidad_Enviada,
          unitCost,
          routeCost,
          pct,
        };
      });
  }, [result, params, filterCenter]);

  const totalUnits = rows.reduce((acc, r) => acc + r.unidades, 0);
  const totalVarCost = rows.reduce((acc, r) => acc + r.routeCost, 0);

  const handleExportExcel = () => {
    if (!result || result.estado !== 'Optimal') {
      onNotify('Ejecuta una optimización antes de exportar.', 'warning');
      return;
    }
    try {
      exportExecutiveExcel(result, params);
      onNotify(
        'Reporte exportado: Reporte_Ejecutivo_MIP_Retail_Optimizer.xlsx',
        'success'
      );
    } catch (err) {
      onNotify(
        `No se pudo exportar el reporte: ${err instanceof Error ? err.message : 'Error'}`,
        'error'
      );
    }
  };

  const handleExportCsv = () => {
    if (!result || result.estado !== 'Optimal') {
      onNotify('Ejecuta una optimización antes de exportar.', 'warning');
      return;
    }
    try {
      exportMatrixCsv(result, params);
      onNotify('CSV exportado: Matriz_Asignacion_Logistica.csv', 'success');
    } catch (err) {
      onNotify(
        `No se pudo exportar el CSV: ${err instanceof Error ? err.message : 'Error'}`,
        'error'
      );
    }
  };

  return (
    <div className="flex h-full flex-col gap-5 pb-12">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-[24px] font-bold tracking-tight text-slate-900">
            Matriz de Rutas y Reportes
          </h1>
          <p className="mt-1 text-[13.5px] text-slate-500">
            Asignaciones óptimas de flujo por centro de origen y zona de destino
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="inline-flex rounded-xl bg-slate-200/70 p-1">
            <button
              type="button"
              onClick={() => setFilterCenter('ALL')}
              className={`rounded-lg px-3 py-1.5 text-[12px] font-semibold transition-all cursor-pointer ${
                filterCenter === 'ALL'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Todos
            </button>
            {UBICACIONES_DEFAULT.map((u) => (
              <button
                key={u}
                type="button"
                onClick={() => setFilterCenter(u)}
                className={`rounded-lg px-3 py-1.5 text-[12px] font-semibold transition-all cursor-pointer ${
                  filterCenter === u
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {u}
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={handleExportExcel}
            className="inline-flex h-10 items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 text-[13px] font-semibold text-white shadow-sm transition-all hover:from-blue-700 hover:to-indigo-700 active:scale-[0.98] whitespace-nowrap cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          >
            <FileSpreadsheet className="h-4 w-4" />
            <span>Exportar a Excel</span>
          </button>

          <button
            type="button"
            onClick={handleExportCsv}
            className="inline-flex h-10 items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 text-[13px] font-semibold text-slate-700 shadow-xs transition-all hover:bg-slate-50 active:scale-[0.98] whitespace-nowrap cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
          >
            <FileText className="h-4 w-4" />
            <span>Exportar CSV</span>
          </button>
        </div>
      </div>

      {/* Table Card */}
      <div className="flex-1 overflow-hidden rounded-2xl border border-slate-200/90 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/80 text-[12px] font-semibold text-slate-600">
                <th className="px-5 py-3.5 text-left">Centro Origen</th>
                <th className="px-5 py-3.5 text-left">Zona Destino</th>
                <th className="px-5 py-3.5 text-right">Unidades Asignadas</th>
                <th className="px-5 py-3.5 text-right">Costo Unitario (USD)</th>
                <th className="px-5 py-3.5 text-right">Costo Total Ruta (USD)</th>
                <th className="px-5 py-3.5 text-right">% Demanda Zona</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-[13.5px] text-slate-800">
              {rows.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-5 py-12 text-center text-slate-500"
                  >
                    No hay rutas asignadas para el filtro seleccionado.
                  </td>
                </tr>
              ) : (
                rows.map((row) => (
                  <tr
                    key={`${row.centro}-${row.zona}`}
                    className="h-11 transition-colors hover:bg-blue-50/50"
                  >
                    <td className="font-mono-num px-5 py-3 text-left font-bold text-blue-600">
                      {row.centro}
                    </td>
                    <td className="font-mono-num px-5 py-3 text-left font-medium text-slate-800">
                      {row.zona}
                    </td>
                    <td className="font-mono-num px-5 py-3 text-right">
                      {row.unidades.toLocaleString('en-US', {
                        maximumFractionDigits: 0,
                      })}{' '}
                      u
                    </td>
                    <td className="font-mono-num px-5 py-3 text-right text-slate-600">
                      ${row.unitCost.toFixed(2)} USD
                    </td>
                    <td className="font-mono-num px-5 py-3 text-right font-semibold text-slate-900">
                      ${row.routeCost.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}{' '}
                      USD
                    </td>
                    <td className="font-mono-num px-5 py-3 text-right font-semibold text-emerald-600">
                      {row.pct.toFixed(1)}%
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer Totals */}
      <div className="font-mono-num flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-slate-200/90 bg-white px-5 py-4 text-[13.5px] font-bold text-slate-900 shadow-sm">
        <span className="text-slate-500 font-sans">Resumen de Flujo Activo</span>
        <span className="text-emerald-700">
          {totalUnits.toLocaleString('en-US', { maximumFractionDigits: 0 })} unidades · $
          {totalVarCost.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}{' '}
          USD costo variable
        </span>
      </div>
    </div>
  );
}
