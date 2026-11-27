import { useState } from 'react';
import { Sparkles } from 'lucide-react';
import { UBICACIONES_DEFAULT } from '../data/defaults.ts';
import type {
  ChartImpactReport,
  OptimizationResult,
  ScenarioParameters,
} from '../types.ts';

interface ChartsProps {
  result: OptimizationResult;
  params: ScenarioParameters;
  impactReport?: ChartImpactReport;
}

export function Charts({ result, params, impactReport }: ChartsProps) {
  const [hoveredCostBar, setHoveredCostBar] = useState<'baseline' | 'optimal' | null>(
    null
  );
  const [hoveredCenter, setHoveredCenter] = useState<string | null>(null);

  const baseline = params.costo_baseline;
  const optimal = result.costo_total;
  const maxCost = Math.max(baseline, optimal, 1) * 1.25;

  const baselineHeightPct = Math.min(100, (baseline / maxCost) * 100);
  const optimalHeightPct = Math.min(100, (optimal / maxCost) * 100);

  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((f) => Math.round(maxCost * f));

  const centerUtils = UBICACIONES_DEFAULT.map((center, idx) => {
    const cap = params.capacidades[idx] || 1;
    const fixedCost = params.costos_fijos[idx] || 0;
    const vol = result.asignaciones
      .filter((a) => a.Ubicacion === center)
      .reduce((acc, a) => acc + a.Cantidad_Enviada, 0);
    const pct = (vol / cap) * 100;
    const isOpen = result.centros_abiertos.includes(center);

    let barColor = '#059669';
    if (pct === 0) barColor = '#CBD5E1';
    else if (pct > 80) barColor = '#DC2626';
    else if (pct > 60) barColor = '#D97706';

    return {
      center,
      pct,
      vol,
      cap,
      fixedCost,
      isOpen,
      barColor,
    };
  });

  const openSummaries = centerUtils
    .filter((c) => c.isOpen)
    .map((c) => `${c.center} (${c.pct.toFixed(1)}%)`)
    .join(' y ');

  const defaultCostSummary = `Comparativa actual: la red óptima cuesta $${optimal.toLocaleString(
    'en-US',
    { maximumFractionDigits: 0 }
  )} USD/mes ($${result.costo_fijo.toLocaleString('en-US', {
    maximumFractionDigits: 0,
  })} USD fijos + $${result.costo_variable.toLocaleString('en-US', {
    maximumFractionDigits: 0,
  })} USD de transporte), generando un ahorro de $${result.ahorro.toLocaleString(
    'en-US',
    { maximumFractionDigits: 0 }
  )} USD/mes (${result.porcentaje_ahorro.toFixed(2)}%) frente al baseline de $${baseline.toLocaleString(
    'en-US',
    { maximumFractionDigits: 0 }
  )} USD/mes. Modifica parámetros y ejecuta la optimización para obtener el informe comparativo de Gemini IA.`;

  const defaultCapacitySummary = `Operan ${
    result.centros_abiertos.length
  } centros activos: ${openSummaries}. El resto de ubicaciones permanecen cerradas (0.0%). Al actualizar capacidades, costos o demandas y ejecutar el cálculo, Gemini IA explicará aquí cómo se reequilibró la red.`;

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
      {/* Gráfico 1: Comparativa Baseline vs Optimizado */}
      <div className="flex flex-col rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <div className="flex items-baseline justify-between gap-2">
          <h3 className="text-[15px] font-bold tracking-tight text-slate-900">
            Comparativa: Costo Baseline vs. Optimizado
          </h3>
          <span className="text-[12px] text-slate-500">USD / mes</span>
        </div>

        <div className="mt-5 flex items-stretch gap-3">
          <div className="font-mono-num flex flex-col justify-between py-2 text-right text-[11px] font-medium text-slate-400">
            {[...yTicks].reverse().map((t, i) => (
              <span key={i}>${t.toLocaleString('en-US')}</span>
            ))}
          </div>

          <div className="relative flex-1 border-b border-l border-slate-200 px-8 pt-6 pb-0 h-[230px]">
            {/* Gridlines */}
            <div className="pointer-events-none absolute inset-x-0 top-6 bottom-0 flex flex-col justify-between">
              {yTicks.map((_, idx) => (
                <div
                  key={idx}
                  className="w-full border-t border-dashed border-slate-100"
                />
              ))}
            </div>

            <div className="relative z-10 flex h-full items-end justify-around gap-8">
              {/* Baseline Bar */}
              <div
                className="relative flex h-full w-28 flex-col items-center justify-end"
                onMouseEnter={() => setHoveredCostBar('baseline')}
                onMouseLeave={() => setHoveredCostBar(null)}
              >
                {hoveredCostBar === 'baseline' && (
                  <div className="pointer-events-none absolute -top-2 left-1/2 z-30 w-56 -translate-x-1/2 -translate-y-full rounded-xl border border-slate-200 bg-slate-900 px-3.5 py-2.5 text-left text-white shadow-xl">
                    <div className="text-[11px] font-semibold text-red-300">
                      Operación Baseline (Actual)
                    </div>
                    <div className="font-mono-num mt-0.5 text-[14px] font-bold">
                      ${baseline.toLocaleString('en-US', { maximumFractionDigits: 0 })} USD / mes
                    </div>
                    <div className="font-mono-num mt-0.5 text-[11px] text-slate-300">
                      Anual: ${(baseline * 12).toLocaleString('en-US', { maximumFractionDigits: 0 })} USD
                    </div>
                  </div>
                )}

                <span className="font-mono-num mb-1.5 text-[12px] font-bold text-slate-900">
                  ${baseline.toLocaleString('en-US', { maximumFractionDigits: 0 })} USD
                </span>
                <div
                  tabIndex={0}
                  onFocus={() => setHoveredCostBar('baseline')}
                  onBlur={() => setHoveredCostBar(null)}
                  className="w-full cursor-pointer rounded-t-lg bg-gradient-to-t from-red-600 to-rose-400 transition-all duration-300 hover:brightness-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
                  style={{ height: `${baselineHeightPct}%` }}
                  aria-label={`Costo Baseline: $${baseline.toLocaleString('en-US')} USD por mes`}
                />
              </div>

              {/* Optimal Bar */}
              <div
                className="relative flex h-full w-28 flex-col items-center justify-end"
                onMouseEnter={() => setHoveredCostBar('optimal')}
                onMouseLeave={() => setHoveredCostBar(null)}
              >
                {hoveredCostBar === 'optimal' && (
                  <div className="pointer-events-none absolute -top-2 left-1/2 z-30 w-60 -translate-x-1/2 -translate-y-full rounded-xl border border-slate-200 bg-slate-900 px-3.5 py-2.5 text-left text-white shadow-xl">
                    <div className="text-[11px] font-semibold text-emerald-300">
                      Red Óptima ({result.centros_abiertos.join(' + ')})
                    </div>
                    <div className="font-mono-num mt-0.5 text-[14px] font-bold">
                      ${optimal.toLocaleString('en-US', { maximumFractionDigits: 0 })} USD / mes
                    </div>
                    <div className="font-mono-num mt-1 space-y-0.5 text-[11px] text-slate-300">
                      <div>
                        Fijo: ${result.costo_fijo.toLocaleString('en-US', { maximumFractionDigits: 0 })} USD
                      </div>
                      <div>
                        Transporte: ${result.costo_variable.toLocaleString('en-US', { maximumFractionDigits: 0 })} USD
                      </div>
                      <div className="font-semibold text-emerald-300">
                        Ahorro: ${result.ahorro.toLocaleString('en-US', { maximumFractionDigits: 0 })} USD ({result.porcentaje_ahorro.toFixed(2)}%)
                      </div>
                    </div>
                  </div>
                )}

                <span className="font-mono-num mb-1.5 text-[12px] font-bold text-emerald-700">
                  ${optimal.toLocaleString('en-US', { maximumFractionDigits: 0 })} USD
                </span>
                <div
                  tabIndex={0}
                  onFocus={() => setHoveredCostBar('optimal')}
                  onBlur={() => setHoveredCostBar(null)}
                  className="w-full cursor-pointer rounded-t-lg bg-gradient-to-t from-emerald-600 to-teal-400 transition-all duration-300 hover:brightness-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                  style={{ height: `${optimalHeightPct}%` }}
                  aria-label={`Costo Optimizado: $${optimal.toLocaleString('en-US')} USD por mes`}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="mt-3 ml-16 flex justify-around text-center text-[12px] font-semibold text-slate-700">
          <span>Baseline (Actual)</span>
          <span>Optimizado (MIP)</span>
        </div>

        {/* Informe IA debajo de Gráfico 1 */}
        <div className="mt-5 flex-1 border-t border-slate-100 pt-4">
          <div className="flex items-center justify-between gap-2">
            <span className="inline-flex items-center gap-1.5 text-[12px] font-bold text-slate-800">
              <Sparkles className="h-3.5 w-3.5 text-blue-600" />
              <span>Informe IA · Impacto en Costos y Ahorros</span>
            </span>
            <span className="text-[11px] font-medium text-slate-400">
              {impactReport?.loading
                ? 'Analizando…'
                : impactReport?.source === 'gemini'
                  ? 'Gemini IA'
                  : 'Resumen del escenario'}
            </span>
          </div>

          {impactReport?.loading ? (
            <div className="mt-2 flex items-center gap-2 text-[12.5px] text-slate-500">
              <span className="inline-flex gap-1 text-blue-600">
                <span className="animate-dot-1">●</span>
                <span className="animate-dot-2">●</span>
                <span className="animate-dot-3">●</span>
              </span>
              <span>Gemini IA está evaluando el impacto en costos y ahorros…</span>
            </div>
          ) : impactReport?.error ? (
            <div className="mt-2 space-y-1 text-[12.5px] leading-relaxed text-slate-600">
              <p className="text-amber-700">{impactReport.error}</p>
              <p>{defaultCostSummary}</p>
            </div>
          ) : (
            <p className="mt-2 text-[12.5px] leading-relaxed text-slate-600">
              {impactReport?.costImpactReport || defaultCostSummary}
            </p>
          )}
        </div>
      </div>

      {/* Gráfico 2: Utilización de Capacidad L1–L4 */}
      <div className="flex flex-col rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <div className="flex items-baseline justify-between gap-2">
          <h3 className="text-[15px] font-bold tracking-tight text-slate-900">
            Utilización de Capacidad por Centro (L1–L4)
          </h3>
          <span className="text-[12px] text-slate-500">% ocupado</span>
        </div>

        <div className="mt-5 flex flex-col justify-center gap-4 border-b border-l border-slate-200 py-4 pl-3 pr-4 h-[230px]">
          {centerUtils.map((item) => (
            <div
              key={item.center}
              className="relative flex items-center gap-3"
              onMouseEnter={() => setHoveredCenter(item.center)}
              onMouseLeave={() => setHoveredCenter(null)}
            >
              {hoveredCenter === item.center && (
                <div className="pointer-events-none absolute -top-2 left-1/2 z-30 w-60 -translate-x-1/2 -translate-y-full rounded-xl border border-slate-200 bg-slate-900 px-3.5 py-2.5 text-left text-white shadow-xl">
                  <div className="flex items-center justify-between text-[11px] font-semibold">
                    <span className="text-blue-300">Centro {item.center}</span>
                    <span className={item.isOpen ? 'text-emerald-300' : 'text-slate-400'}>
                      {item.isOpen ? 'Operativo' : 'Cerrado'}
                    </span>
                  </div>
                  <div className="font-mono-num mt-1 space-y-0.5 text-[11px] text-slate-200">
                    <div>
                      Volumen: {item.vol.toLocaleString('en-US', { maximumFractionDigits: 0 })} /{' '}
                      {item.cap.toLocaleString('en-US', { maximumFractionDigits: 0 })} u/mes
                    </div>
                    <div>Utilización: {item.pct.toFixed(1)}%</div>
                    <div>
                      Costo fijo: ${item.fixedCost.toLocaleString('en-US', { maximumFractionDigits: 0 })} USD / mes
                    </div>
                  </div>
                </div>
              )}

              <span className="font-mono-num w-8 text-right text-[12px] font-bold text-slate-900">
                {item.center}
              </span>

              <div
                tabIndex={0}
                onFocus={() => setHoveredCenter(item.center)}
                onBlur={() => setHoveredCenter(null)}
                className="relative h-7 flex-1 cursor-pointer overflow-hidden rounded-lg bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                aria-label={`${item.center}: ${item.pct.toFixed(1)}% de capacidad`}
              >
                <div
                  className="h-full rounded-lg transition-all duration-500 hover:brightness-105"
                  style={{
                    width: `${Math.min(100, item.pct)}%`,
                    backgroundColor: item.barColor,
                  }}
                />
              </div>

              <span className="font-mono-num w-28 text-left text-[12px] font-semibold text-slate-700">
                {item.pct.toFixed(1)}%
                {!item.isOpen ? (
                  <span className="ml-1 font-sans text-[11px] font-normal text-slate-400">
                    · Cerrado
                  </span>
                ) : null}
              </span>
            </div>
          ))}
        </div>

        <div className="font-mono-num mt-3 flex justify-between pl-11 pr-28 text-[11px] text-slate-400">
          <span>0.0%</span>
          <span>25.0%</span>
          <span>50.0%</span>
          <span>75.0%</span>
          <span>100.0%</span>
        </div>

        {/* Informe IA debajo de Gráfico 2 */}
        <div className="mt-5 flex-1 border-t border-slate-100 pt-4">
          <div className="flex items-center justify-between gap-2">
            <span className="inline-flex items-center gap-1.5 text-[12px] font-bold text-slate-800">
              <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
              <span>Informe IA · Capacidad y Centros Activos</span>
            </span>
            <span className="text-[11px] font-medium text-slate-400">
              {impactReport?.loading
                ? 'Analizando…'
                : impactReport?.source === 'gemini'
                  ? 'Gemini IA'
                  : 'Resumen operativo'}
            </span>
          </div>

          {impactReport?.loading ? (
            <div className="mt-2 flex items-center gap-2 text-[12.5px] text-slate-500">
              <span className="inline-flex gap-1 text-emerald-600">
                <span className="animate-dot-1">●</span>
                <span className="animate-dot-2">●</span>
                <span className="animate-dot-3">●</span>
              </span>
              <span>Gemini IA está analizando la asignación y capacidad de L1–L4…</span>
            </div>
          ) : impactReport?.error ? (
            <div className="mt-2 space-y-1 text-[12.5px] leading-relaxed text-slate-600">
              <p className="text-amber-700">{impactReport.error}</p>
              <p>{defaultCapacitySummary}</p>
            </div>
          ) : (
            <p className="mt-2 text-[12.5px] leading-relaxed text-slate-600">
              {impactReport?.capacityImpactReport || defaultCapacitySummary}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
