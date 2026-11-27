const ROI_METRICS = [
  { label: 'Ahorro Mensual', value: '$60,500 USD' },
  { label: 'Ahorro Anual', value: '$726,000 USD' },
  { label: 'Reducción Costos', value: '24.90%' },
  { label: 'ROI Primer Año', value: '> 300%' },
  { label: 'Payback Estimado', value: '< 3 meses' },
];

const BENEFICIOS = [
  'Optimización matemática rigurosa (MIP) con optimalidad global garantizada',
  'Análisis de sensibilidad en tiempo real (what-if scenarios interactivos)',
  'Interfaz ejecutiva con dashboard KPIs, gráficos interactivos y reportes listos para gerencia',
  'Importación y exportación de escenarios (CSV y Excel multi-hoja profesional)',
  'Modo protegido por defecto, listo para presentaciones y demos en vivo',
  'Arquitectura lista para empaquetado standalone en Windows (.exe) con motor PuLP y PyWebView',
];

const MODELO_NEGOCIO = [
  {
    label: 'Fase 1 - Diagnóstico',
    desc: 'Levantamiento de datos, validación, configuración del modelo',
  },
  {
    label: 'Fase 2 - Ejecución',
    desc: 'Corridas base, análisis de sensibilidad, comparación de escenarios',
  },
  {
    label: 'Fase 3 - Entrega',
    desc: 'Ejecutable standalone, documentación técnica, dashboard, capacitación',
  },
  {
    label: 'Fee Implementación',
    desc: 'Según alcance y número de SKUs/ubicaciones',
  },
  {
    label: 'Fee por Optimización',
    desc: 'Por corrida de escenario productivo o re-optimización mensual',
  },
  {
    label: 'Suscripción Anual',
    desc: 'Actualizaciones, nuevos módulos (inventario, routing, estacionalidad), soporte',
  },
];

export function LicenseView() {
  return (
    <div className="space-y-6 pb-8">
      {/* Hero Banner */}
      <section className="rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 px-8 py-9 text-center text-white shadow-md">
        <h1 className="text-[26px] font-bold tracking-tight">
          MIP Retail Optimizer™ Enterprise
        </h1>
        <p className="mt-2 text-[14.5px] text-blue-100">
          Sistema de Optimización Logística y Diseño de Redes de Distribución
        </p>
      </section>

      {/* ROI Box */}
      <section className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-slate-100 pb-3.5">
          <h2 className="text-[16px] font-bold tracking-tight text-slate-900">
            Retorno de Inversión (ROI) Estimado
          </h2>
          <span className="font-mono-num text-[12px] text-slate-400">
            Baseline $243,000 USD/mes → Optimizado $182,500 USD/mes
          </span>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-5">
          {ROI_METRICS.map((m) => (
            <div
              key={m.label}
              className="rounded-xl bg-slate-50/90 px-4 py-4 text-center"
            >
              <div className="text-[12px] font-medium text-slate-500">
                {m.label}
              </div>
              <div className="font-mono-num mt-1.5 text-[20px] font-bold text-emerald-600">
                {m.value}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Beneficios */}
      <section className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <h2 className="text-[16px] font-bold tracking-tight text-slate-900">
          Beneficios Clave
        </h2>
        <ul className="mt-4 space-y-2.5">
          {BENEFICIOS.map((item) => (
            <li
              key={item}
              className="flex items-start gap-2.5 text-[13.5px] text-slate-600"
            >
              <span className="font-bold text-emerald-600">✓</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </section>

      {/* Modelo de Negocio */}
      <section className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <h2 className="text-[16px] font-bold tracking-tight text-slate-900">
          Modelo de Negocio
        </h2>
        <div className="mt-4 divide-y divide-slate-100">
          {MODELO_NEGOCIO.map((item) => (
            <div
              key={item.label}
              className="flex flex-col gap-1 py-2.5 sm:flex-row sm:items-baseline sm:gap-6"
            >
              <span className="w-52 shrink-0 text-[13px] font-bold text-amber-700">
                {item.label}
              </span>
              <span className="text-[13.5px] text-slate-600">{item.desc}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
