import { useEffect, useRef, useState } from 'react';
import {
  Bot,
  Compass,
  Download,
  FileDown,
  FolderOpen,
  Lock,
  Play,
  RotateCcw,
  Save,
  Unlock,
  X,
} from 'lucide-react';
import { UBICACIONES_DEFAULT, ZONAS_DEFAULT } from '../data/defaults.ts';
import {
  exportDashboardPdf,
  exportScenarioTemplateCsv,
  parseImportedScenarioFile,
  validateParameters,
} from '../lib/exportUtils.ts';
import type {
  ChartImpactReport,
  OptimizationResult,
  ScenarioParameters,
  ToastKind,
} from '../types.ts';
import { Charts } from './Charts.tsx';

interface DashboardViewProps {
  savedParams: ScenarioParameters;
  lastResult: OptimizationResult | null;
  lastResultParams: ScenarioParameters | null;
  chartImpactReport: ChartImpactReport;
  isExecuting: boolean;
  executionVisible: boolean;
  executionProgress: number;
  executionStatusText: string;
  executionStatusTone: 'primary' | 'success' | 'danger' | 'muted';
  executionLogs: string[];
  onSwitchToAssistant: () => void;
  onOpenTutorial: () => void;
  onRequestConfirm: (
    title: string,
    message: string,
    confirmText: string,
    onConfirm: () => void
  ) => void;
  onSaveParams: (nextParams: ScenarioParameters) => void;
  onRestoreBase: () => void;
  onExecuteOptimization: () => void;
  onNotify: (message: string, kind?: ToastKind) => void;
  onDraftChange: (draft: ScenarioParameters, isEditing: boolean) => void;
}

type ParamTab = 'cds' | 'demandas' | 'config';

function toDraftStrings(params: ScenarioParameters) {
  return {
    costos_fijos: params.costos_fijos.map((v) => v.toLocaleString('en-US')),
    capacidades: params.capacidades.map((v) => v.toLocaleString('en-US')),
    demandas: params.demandas.map((v) => v.toLocaleString('en-US')),
    max_centros: String(params.max_centros),
    costo_baseline: params.costo_baseline.toLocaleString('en-US'),
  };
}

function parseIntField(raw: string, label: string): number {
  const cleaned = raw.replace(/[$,\s]/g, '').trim();
  if (!cleaned || !/^-?\d+$/.test(cleaned)) {
    throw new Error(`Parámetro inválido en ${label}: "${raw}"`);
  }
  return Number.parseInt(cleaned, 10);
}

export function DashboardView({
  savedParams,
  lastResult,
  lastResultParams,
  chartImpactReport,
  isExecuting,
  executionVisible,
  executionProgress,
  executionStatusText,
  executionStatusTone,
  executionLogs,
  onSwitchToAssistant,
  onOpenTutorial,
  onRequestConfirm,
  onSaveParams,
  onRestoreBase,
  onExecuteOptimization,
  onNotify,
  onDraftChange,
}: DashboardViewProps) {
  const [activeTab, setActiveTab] = useState<ParamTab>('cds');
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(() => toDraftStrings(savedParams));
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (!isEditing) {
      setDraft(toDraftStrings(savedParams));
    }
  }, [savedParams, isEditing]);

  const syncDraftFromParams = (params: ScenarioParameters, editingState: boolean) => {
    setDraft(toDraftStrings(params));
    onDraftChange(params, editingState);
  };

  const parseDraft = (): ScenarioParameters => {
    const costos_fijos = draft.costos_fijos.map((v, i) =>
      parseIntField(v, `Costo fijo ${UBICACIONES_DEFAULT[i]}`)
    );
    const capacidades = draft.capacidades.map((v, i) =>
      parseIntField(v, `Capacidad ${UBICACIONES_DEFAULT[i]}`)
    );
    const demandas = draft.demandas.map((v, j) =>
      parseIntField(v, `Demanda ${ZONAS_DEFAULT[j]}`)
    );
    const max_centros = parseIntField(draft.max_centros, 'Máximo de CDs');
    const costo_baseline = parseIntField(draft.costo_baseline, 'Costo Baseline');

    return validateParameters({
      costos_fijos,
      capacidades,
      demandas,
      max_centros,
      costo_baseline,
    });
  };

  const tryPushDraft = (nextDraft: typeof draft) => {
    try {
      const costos_fijos = nextDraft.costos_fijos.map((v) =>
        Number.parseInt(v.replace(/[$,\s]/g, '').trim(), 10)
      );
      const capacidades = nextDraft.capacidades.map((v) =>
        Number.parseInt(v.replace(/[$,\s]/g, '').trim(), 10)
      );
      const demandas = nextDraft.demandas.map((v) =>
        Number.parseInt(v.replace(/[$,\s]/g, '').trim(), 10)
      );
      const max_centros = Number.parseInt(
        nextDraft.max_centros.replace(/[$,\s]/g, '').trim(),
        10
      );
      const costo_baseline = Number.parseInt(
        nextDraft.costo_baseline.replace(/[$,\s]/g, '').trim(),
        10
      );
      if (
        costos_fijos.every(Number.isFinite) &&
        capacidades.every(Number.isFinite) &&
        demandas.every(Number.isFinite) &&
        Number.isFinite(max_centros) &&
        Number.isFinite(costo_baseline)
      ) {
        onDraftChange(
          { costos_fijos, capacidades, demandas, max_centros, costo_baseline },
          true
        );
      }
    } catch {
      // Ignore partial intermediate typing
    }
  };

  const handleEnableEdit = () => {
    if (isExecuting) {
      onNotify('Espera a que termine el cálculo para editar.', 'warning');
      return;
    }
    onRequestConfirm(
      'Editar parámetros',
      'Podrás modificar los valores del escenario. Guarda los cambios antes de ejecutar la optimización.',
      'Editar',
      () => {
        setIsEditing(true);
        setDraft({
          costos_fijos: savedParams.costos_fijos.map(String),
          capacidades: savedParams.capacidades.map(String),
          demandas: savedParams.demandas.map(String),
          max_centros: String(savedParams.max_centros),
          costo_baseline: String(savedParams.costo_baseline),
        });
        onDraftChange(savedParams, true);
      }
    );
  };

  const handleSave = () => {
    try {
      const parsed = parseDraft();
      onSaveParams(parsed);
      setIsEditing(false);
      syncDraftFromParams(parsed, false);
      onNotify('Parámetros guardados correctamente.', 'success');
    } catch (err) {
      onNotify(err instanceof Error ? err.message : 'Parámetros inválidos.', 'error');
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    syncDraftFromParams(savedParams, false);
    onNotify('Edición cancelada.', 'info');
  };

  const handleRestore = () => {
    onRequestConfirm(
      'Restaurar valores base',
      'Se reemplazarán los parámetros guardados por los valores oficiales del estudio.',
      'Restaurar',
      () => {
        setIsEditing(false);
        onRestoreBase();
      }
    );
  };

  const handleFileImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;

    try {
      const { params, importedCount } = await parseImportedScenarioFile(
        file,
        savedParams
      );
      setIsEditing(true);
      setDraft({
        costos_fijos: params.costos_fijos.map(String),
        capacidades: params.capacidades.map(String),
        demandas: params.demandas.map(String),
        max_centros: String(params.max_centros),
        costo_baseline: String(params.costo_baseline),
      });
      onDraftChange(params, true);
      onNotify(
        `${importedCount} parámetros importados desde "${file.name}". Pulsa "Guardar Cambios" y luego "Ejecutar Optimización Matemática".`,
        'success'
      );
    } catch (err) {
      onNotify(
        `No se pudo importar el escenario: ${err instanceof Error ? err.message : 'Error de lectura'}`,
        'error'
      );
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const saved = await exportScenarioTemplateCsv(savedParams);
      if (!saved.ok) {
        if (saved.cancelado) return;
        throw new Error(saved.error ?? 'No se pudo guardar la plantilla.');
      }
      onNotify(
        saved.ruta
          ? `Archivo guardado en: ${saved.ruta}`
          : 'Plantilla CSV descargada: Plantilla_Escenario_MIP.csv',
        'success'
      );
    } catch (err) {
      onNotify(
        `No se pudo generar la plantilla: ${err instanceof Error ? err.message : 'Error'}`,
        'error'
      );
    }
  };

  const handleExportPdf = async () => {
    if (!lastResult || lastResult.estado !== 'Optimal') {
      onNotify('Ejecuta una optimización óptima antes de exportar el PDF.', 'warning');
      return;
    }
    try {
      const saved = await exportDashboardPdf(lastResult, displayParams, chartImpactReport);
      if (!saved.ok) {
        if (saved.cancelado) return;
        throw new Error(saved.error ?? 'No se pudo guardar el reporte PDF.');
      }
      onNotify(
        saved.ruta
          ? `Archivo guardado en: ${saved.ruta}`
          : 'Reporte PDF descargado: Reporte_Ejecutivo_MIP_Retail_Optimizer.pdf',
        'success'
      );
    } catch (err) {
      onNotify(
        `No se pudo exportar el PDF: ${err instanceof Error ? err.message : 'Error'}`,
        'error'
      );
    }
  };

  const handleExecuteClick = () => {
    if (isExecuting) return;
    if (isEditing) {
      onNotify('Guarda o cancela la edición antes de ejecutar.', 'warning');
      return;
    }
    onExecuteOptimization();
  };

  const displayParams = lastResultParams ?? savedParams;
  const totalDemandScenario = savedParams.demandas.reduce((a, b) => a + b, 0);
  const totalDemandResult = displayParams.demandas.reduce((a, b) => a + b, 0);

  const statusToneClass =
    executionStatusTone === 'success'
      ? 'text-emerald-600'
      : executionStatusTone === 'danger'
        ? 'text-red-600'
        : executionStatusTone === 'primary'
          ? 'text-blue-600'
          : 'text-slate-400';

  return (
    <div className="space-y-5 pb-12">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-[24px] font-bold tracking-tight text-slate-900">
            Dashboard y Simulación
          </h1>
          <p className="mt-1 text-[13.5px] text-slate-500">
            Configura, ejecuta y analiza la optimización matemática de tu red de distribución
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            onClick={onOpenTutorial}
            className="inline-flex h-10 items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 text-[13px] font-semibold text-slate-700 shadow-xs transition-all hover:bg-slate-50 active:scale-[0.98] whitespace-nowrap cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
          >
            <Compass className="h-4 w-4 text-blue-600" />
            <span>Tutorial IA</span>
          </button>

          <button
            type="button"
            data-tour="export-pdf"
            onClick={handleExportPdf}
            disabled={!lastResult || lastResult.estado !== 'Optimal'}
            className="inline-flex h-10 items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 text-[13px] font-semibold text-white shadow-sm transition-all hover:from-blue-700 hover:to-indigo-700 active:scale-[0.98] disabled:opacity-50 whitespace-nowrap cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          >
            <FileDown className="h-4 w-4" />
            <span>Exportar PDF</span>
          </button>

          <button
            type="button"
            onClick={onSwitchToAssistant}
            className="inline-flex h-10 items-center gap-2 rounded-xl bg-slate-900 px-4 text-[13px] font-semibold text-white shadow-sm transition-all hover:bg-slate-800 active:scale-[0.98] whitespace-nowrap cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500"
          >
            <Bot className="h-4 w-4 text-blue-400" />
            <span>Consultar al Asistente IA</span>
          </button>
        </div>
      </div>

      {/* Escenario Actual Card */}
      <section className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3.5">
          <h2 className="text-[15px] font-bold tracking-tight text-slate-900">
            Escenario Actual
          </h2>
          <span className="text-[12px] text-slate-400">
            Modelo CFLP · Red Retail
          </span>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-5">
          <div>
            <div className="text-[12px] font-medium text-slate-400">
              Centros Candidatos
            </div>
            <div className="font-mono-num mt-1 text-[15px] font-bold text-slate-700">
              4 centros (L1–L4)
            </div>
          </div>
          <div>
            <div className="text-[12px] font-medium text-slate-400">
              Zonas de Demanda
            </div>
            <div className="font-mono-num mt-1 text-[15px] font-bold text-slate-700">
              6 zonas (Z1–Z6)
            </div>
          </div>
          <div>
            <div className="text-[12px] font-medium text-slate-400">
              Demanda Total
            </div>
            <div className="font-mono-num mt-1 text-[15px] font-bold text-slate-900">
              {totalDemandScenario.toLocaleString('en-US')} u/mes
            </div>
          </div>
          <div>
            <div className="text-[12px] font-medium text-slate-400">
              Máx. CDs a Abrir
            </div>
            <div className="font-mono-num mt-1 text-[15px] font-bold text-amber-600">
              {savedParams.max_centros} centros
            </div>
          </div>
          <div>
            <div className="text-[12px] font-medium text-slate-400">
              Costo Baseline
            </div>
            <div className="font-mono-num mt-1 text-[15px] font-bold text-red-600">
              ${savedParams.costo_baseline.toLocaleString('en-US')} USD / mes
            </div>
          </div>
        </div>
      </section>

      {/* Parámetros de Entrada Card */}
      <section
        data-tour="scenario-params"
        className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm"
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <h2 className="text-[15px] font-bold tracking-tight text-slate-900">
              Parámetros de Entrada
            </h2>
            <span className="text-slate-300" aria-hidden="true">
              ·
            </span>
            <span
              className={`inline-flex items-center gap-1.5 text-[12px] font-semibold ${
                isEditing ? 'text-emerald-600' : 'text-slate-500'
              }`}
            >
              {isEditing ? (
                <>Edición activa</>
              ) : (
                <>
                  <Lock className="h-3.5 w-3.5 text-slate-400" /> Modo Protegido
                </>
              )}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {!isEditing ? (
              <button
                type="button"
                onClick={handleEnableEdit}
                disabled={isExecuting}
                className="inline-flex h-10 items-center gap-2 rounded-xl bg-amber-600 px-4 text-[13px] font-semibold text-white shadow-xs transition-all hover:bg-amber-700 active:scale-[0.98] disabled:opacity-50 whitespace-nowrap cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500"
              >
                <Unlock className="h-4 w-4" />
                <span>Editar Parámetros</span>
              </button>
            ) : (
              <>
                <button
                  type="button"
                  onClick={handleSave}
                  className="inline-flex h-10 items-center gap-2 rounded-xl bg-emerald-600 px-4 text-[13px] font-semibold text-white shadow-xs transition-all hover:bg-emerald-700 active:scale-[0.98] whitespace-nowrap cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
                >
                  <Save className="h-4 w-4" />
                  <span>Guardar Cambios</span>
                </button>
                <button
                  type="button"
                  onClick={handleCancelEdit}
                  className="inline-flex h-10 items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 text-[13px] font-semibold text-slate-600 transition-all hover:bg-slate-100 active:scale-[0.98] whitespace-nowrap cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
                >
                  <X className="h-4 w-4" />
                  <span>Cancelar Edición</span>
                </button>
              </>
            )}

            <button
              type="button"
              onClick={handleRestore}
              disabled={isExecuting}
              className="inline-flex h-10 items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 text-[13px] font-semibold text-slate-600 transition-all hover:bg-slate-100 active:scale-[0.98] disabled:opacity-50 whitespace-nowrap cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
            >
              <RotateCcw className="h-4 w-4" />
              <span>Restaurar Base</span>
            </button>

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isExecuting}
              className="inline-flex h-10 items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 text-[13px] font-semibold text-slate-600 transition-all hover:bg-slate-100 active:scale-[0.98] disabled:opacity-50 whitespace-nowrap cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
            >
              <FolderOpen className="h-4 w-4" />
              <span>Cargar CSV/Excel</span>
            </button>

            <button
              type="button"
              onClick={handleDownloadTemplate}
              disabled={isExecuting}
              title="Descargar archivo CSV de ejemplo con el formato requerido"
              className="inline-flex h-10 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 text-[12.5px] font-semibold text-slate-600 transition-all hover:bg-slate-50 active:scale-[0.98] disabled:opacity-50 whitespace-nowrap cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Plantilla CSV</span>
            </button>

            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.xls"
              className="hidden"
              onChange={handleFileImport}
            />
          </div>
        </div>

        {/* Segmented Tabs + Inputs */}
        <div className="mt-5 rounded-xl bg-slate-50/90 p-4">
          <div className="mb-4 inline-flex flex-wrap gap-1 rounded-xl bg-slate-200/70 p-1">
            <button
              type="button"
              onClick={() => setActiveTab('cds')}
              className={`rounded-lg px-3.5 py-2 text-[12.5px] font-semibold transition-all whitespace-nowrap cursor-pointer ${
                activeTab === 'cds'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Centros de Distribución
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('demandas')}
              className={`rounded-lg px-3.5 py-2 text-[12.5px] font-semibold transition-all whitespace-nowrap cursor-pointer ${
                activeTab === 'demandas'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Demandas por Zona
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('config')}
              className={`rounded-lg px-3.5 py-2 text-[12.5px] font-semibold transition-all whitespace-nowrap cursor-pointer ${
                activeTab === 'config'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Reglas y Baseline
            </button>
          </div>

          {activeTab === 'cds' && (
            <div className="grid grid-cols-1 items-center gap-3 sm:grid-cols-[110px_1fr_1fr]">
              <div className="px-2 text-[12px] font-semibold text-slate-500">
                Centro
              </div>
              <div className="px-2 text-[12px] font-semibold text-slate-500">
                Costo Fijo (USD/mes)
              </div>
              <div className="px-2 text-[12px] font-semibold text-slate-500">
                Capacidad (u/mes)
              </div>

              {UBICACIONES_DEFAULT.map((ubicacion, i) => (
                <div key={ubicacion} className="contents">
                  <div className="font-mono-num px-2 text-[13px] font-bold text-slate-900">
                    {ubicacion}
                  </div>
                  <div
                    className={`flex h-10 items-center rounded-xl border border-slate-200 px-3 transition-colors focus-within:border-blue-500 ${
                      isEditing ? 'bg-white' : 'bg-slate-100/70'
                    }`}
                  >
                    <span className="font-mono-num mr-1.5 text-[13px] font-semibold text-slate-400">
                      $
                    </span>
                    <input
                      type="text"
                      aria-label={`Costo Fijo ${ubicacion}`}
                      disabled={!isEditing}
                      value={draft.costos_fijos[i]}
                      onChange={(e) => {
                        const next = {
                          ...draft,
                          costos_fijos: draft.costos_fijos.map((v, idx) =>
                            idx === i ? e.target.value : v
                          ),
                        };
                        setDraft(next);
                        tryPushDraft(next);
                      }}
                      className="font-mono-num w-full bg-transparent text-[13px] text-slate-900 focus:outline-none disabled:text-slate-500"
                    />
                    <span className="font-mono-num ml-1.5 shrink-0 text-[11px] font-medium text-slate-400">
                      USD
                    </span>
                  </div>

                  <div
                    className={`flex h-10 items-center rounded-xl border border-slate-200 px-3 transition-colors focus-within:border-blue-500 ${
                      isEditing ? 'bg-white' : 'bg-slate-100/70'
                    }`}
                  >
                    <input
                      type="text"
                      aria-label={`Capacidad ${ubicacion}`}
                      disabled={!isEditing}
                      value={draft.capacidades[i]}
                      onChange={(e) => {
                        const next = {
                          ...draft,
                          capacidades: draft.capacidades.map((v, idx) =>
                            idx === i ? e.target.value : v
                          ),
                        };
                        setDraft(next);
                        tryPushDraft(next);
                      }}
                      className="font-mono-num w-full bg-transparent text-[13px] text-slate-900 focus:outline-none disabled:text-slate-500"
                    />
                    <span className="font-mono-num ml-1.5 shrink-0 text-[11px] font-medium text-slate-400">
                      u/mes
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'demandas' && (
            <div className="grid grid-cols-1 items-center gap-3 sm:grid-cols-[110px_1fr]">
              <div className="px-2 text-[12px] font-semibold text-slate-500">
                Zona
              </div>
              <div className="px-2 text-[12px] font-semibold text-slate-500">
                Demanda (u/mes)
              </div>

              {ZONAS_DEFAULT.map((zona, j) => (
                <div key={zona} className="contents">
                  <div className="font-mono-num px-2 text-[13px] font-bold text-slate-900">
                    {zona}
                  </div>
                  <div
                    className={`flex h-10 items-center rounded-xl border border-slate-200 px-3 transition-colors focus-within:border-blue-500 ${
                      isEditing ? 'bg-white' : 'bg-slate-100/70'
                    }`}
                  >
                    <input
                      type="text"
                      aria-label={`Demanda ${zona}`}
                      disabled={!isEditing}
                      value={draft.demandas[j]}
                      onChange={(e) => {
                        const next = {
                          ...draft,
                          demandas: draft.demandas.map((v, idx) =>
                            idx === j ? e.target.value : v
                          ),
                        };
                        setDraft(next);
                        tryPushDraft(next);
                      }}
                      className="font-mono-num w-full bg-transparent text-[13px] text-slate-900 focus:outline-none disabled:text-slate-500"
                    />
                    <span className="font-mono-num ml-1.5 shrink-0 text-[11px] font-medium text-slate-400">
                      u/mes
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'config' && (
            <div className="space-y-3 py-1">
              <div className="grid grid-cols-1 items-center gap-3 sm:grid-cols-[230px_1fr_90px]">
                <label
                  htmlFor="input-max-centros"
                  className="px-2 text-[13px] font-medium text-slate-700"
                >
                  Máximo de CDs a abrir:
                </label>
                <div
                  className={`flex h-10 items-center rounded-xl border border-slate-200 px-3 transition-colors focus-within:border-blue-500 ${
                    isEditing ? 'bg-white' : 'bg-slate-100/70'
                  }`}
                >
                  <input
                    id="input-max-centros"
                    type="text"
                    disabled={!isEditing}
                    value={draft.max_centros}
                    onChange={(e) => {
                      const next = { ...draft, max_centros: e.target.value };
                      setDraft(next);
                      tryPushDraft(next);
                    }}
                    className="font-mono-num w-full bg-transparent text-[13px] text-slate-900 focus:outline-none disabled:text-slate-500"
                  />
                  <span className="font-mono-num ml-1.5 shrink-0 text-[11px] font-medium text-slate-400">
                    centros
                  </span>
                </div>
                <span className="text-[12px] text-slate-400">1 a 4</span>
              </div>

              <div className="grid grid-cols-1 items-center gap-3 sm:grid-cols-[230px_1fr_90px]">
                <label
                  htmlFor="input-baseline"
                  className="px-2 text-[13px] font-medium text-slate-700"
                >
                  Costo Baseline (USD/mes):
                </label>
                <div
                  className={`flex h-10 items-center rounded-xl border border-slate-200 px-3 transition-colors focus-within:border-blue-500 ${
                    isEditing ? 'bg-white' : 'bg-slate-100/70'
                  }`}
                >
                  <span className="font-mono-num mr-1.5 text-[13px] font-semibold text-slate-400">
                    $
                  </span>
                  <input
                    id="input-baseline"
                    type="text"
                    disabled={!isEditing}
                    value={draft.costo_baseline}
                    onChange={(e) => {
                      const next = { ...draft, costo_baseline: e.target.value };
                      setDraft(next);
                      tryPushDraft(next);
                    }}
                    className="font-mono-num w-full bg-transparent text-[13px] text-slate-900 focus:outline-none disabled:text-slate-500"
                  />
                </div>
                <span className="text-[12px] text-slate-400">USD / mes</span>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Main CTA */}
      <button
        type="button"
        data-tour="run-optimize"
        onClick={handleExecuteClick}
        disabled={isExecuting}
        className="flex h-12 w-full items-center justify-center gap-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-[15px] font-semibold text-white shadow-md transition-all duration-150 hover:from-blue-700 hover:to-indigo-700 hover:shadow-lg active:scale-[0.99] disabled:opacity-60 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
      >
        <Play className="h-4 w-4 fill-current" />
        <span>
          {isExecuting ? 'Ejecutando optimización…' : 'Ejecutar Optimización Matemática'}
        </span>
      </button>

      {/* Progressive Execution Card */}
      {executionVisible && (
        <section className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-[15px] font-bold tracking-tight text-slate-900">
              Ejecución Progresiva del Modelo
            </h2>
            <span className={`text-[12px] font-semibold ${statusToneClass}`}>
              {executionStatusText}
            </span>
          </div>

          <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 transition-all duration-300"
              style={{ width: `${Math.round(executionProgress * 100)}%` }}
            />
          </div>

          <pre className="font-mono-num mt-3 max-h-32 overflow-y-auto rounded-xl bg-slate-900 p-3.5 text-[11.5px] leading-relaxed text-slate-200 whitespace-pre-wrap">
            {executionLogs.join('\n')}
          </pre>
        </section>
      )}

      {/* Executive KPIs + Interactive Charts */}
      {lastResult && lastResult.estado === 'Optimal' && (
        <>
          <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm">
              <div className="text-[12px] font-semibold text-slate-500">
                Costo Total Óptimo
              </div>
              <div className="font-mono-num mt-2 text-[23px] font-bold tracking-tight text-slate-900">
                ${lastResult.costo_total.toLocaleString('en-US', { maximumFractionDigits: 0 })} USD
              </div>
              <div className="font-mono-num mt-1 text-[11.5px] text-slate-400">
                Fijo: ${lastResult.costo_fijo.toLocaleString('en-US', { maximumFractionDigits: 0 })} USD · Transp.: ${lastResult.costo_variable.toLocaleString('en-US', { maximumFractionDigits: 0 })} USD
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm">
              <div className="text-[12px] font-semibold text-slate-500">
                Ahorro Mensual
              </div>
              <div className="font-mono-num mt-2 text-[23px] font-bold tracking-tight text-emerald-600">
                ${lastResult.ahorro.toLocaleString('en-US', { maximumFractionDigits: 0 })} USD
                <span className="ml-1.5 text-[14px] font-semibold">
                  ({lastResult.porcentaje_ahorro.toFixed(2)}%)
                </span>
              </div>
              <div className="font-mono-num mt-1 text-[11.5px] text-slate-400">
                ${(lastResult.ahorro * 12).toLocaleString('en-US', { maximumFractionDigits: 0 })} USD / año
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm">
              <div className="text-[12px] font-semibold text-slate-500">
                Centros Activos
              </div>
              <div className="font-mono-num mt-2 text-[23px] font-bold tracking-tight text-amber-600">
                {lastResult.centros_abiertos.join(', ')}
              </div>
              <div className="font-mono-num mt-1 text-[11.5px] text-slate-400">
                {lastResult.centros_abiertos.length} de {displayParams.max_centros} permitidos
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm">
              <div className="text-[12px] font-semibold text-slate-500">
                Demanda Cubierta
              </div>
              <div className="font-mono-num mt-2 text-[23px] font-bold tracking-tight text-emerald-600">
                {totalDemandResult.toLocaleString('en-US')}
                <span className="ml-1.5 text-[14px] font-semibold">u/mes</span>
              </div>
              <div className="font-mono-num mt-1 text-[11.5px] text-slate-400">
                Nivel de servicio: 100.0%
              </div>
            </div>
          </section>

          <div data-tour="charts-ai">
            <Charts
              result={lastResult}
              params={displayParams}
              impactReport={chartImpactReport}
            />
          </div>
        </>
      )}
    </div>
  );
}
