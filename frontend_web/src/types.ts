export type ViewId = 'dashboard' | 'matrix' | 'manual' | 'assistant' | 'license';

export interface ScenarioParameters {
  costos_fijos: number[];
  capacidades: number[];
  demandas: number[];
  max_centros: number;
  costo_baseline: number;
}

export interface AssignmentRow {
  Ubicacion: string;
  Zona: string;
  Cantidad_Enviada: number;
}

export type OptimizationStatus = 'Optimal' | 'Infeasible' | 'Error';

export interface OptimizationResult {
  estado: OptimizationStatus;
  centros_abiertos: string[];
  costo_fijo: number;
  costo_variable: number;
  costo_total: number;
  ahorro: number;
  porcentaje_ahorro: number;
  asignaciones: AssignmentRow[];
  mensaje: string;
}

export interface ManualChapter {
  title: string;
  subtitle: string;
  left_heading: string;
  left_text: string;
  right_heading: string;
  right_text: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  text: string;
}

export interface ChatTurn {
  role: 'user' | 'model';
  text: string;
}

export type ToastKind = 'success' | 'error' | 'info' | 'warning';

export interface ToastState {
  id: number;
  message: string;
  kind: ToastKind;
}

export interface TutorialStep {
  id: string;
  title: string;
  section: string;
  summary: string;
  tip: string;
  targetView?: ViewId;
}

export interface ChartImpactReport {
  costImpactReport: string;
  capacityImpactReport: string;
  loading: boolean;
  error: string | null;
  source: 'gemini' | 'none';
}

export interface NativeSaveResult {
  ok: boolean;
  ruta?: string | null;
  cancelado?: boolean;
  error?: string;
}

export interface PyWebViewPayload extends ScenarioParameters {
  costos_envio: number[][];
  tarifas: number[][];
  zonas: string[];
  ubicaciones: string[];
}

export interface PyWebViewApi {
  resolver_escenario?: (
    params: PyWebViewPayload
  ) => Promise<OptimizationResult | string> | OptimizationResult | string;
  estado_asistente?: () => Promise<{
    configured: boolean;
    model: string;
  }>;
  consultar_asistente?: (payload: {
    question: string;
    context: string;
    priorTurns: ChatTurn[];
  }) => Promise<{ answer: string; model: string }>;
  generar_tutorial?: () => Promise<{ steps: Array<Omit<TutorialStep, 'targetView'>> }>;
  analizar_impacto_graficos?: (payload: {
    previousParams: ScenarioParameters;
    previousResult: OptimizationResult | null;
    currentParams: ScenarioParameters;
    currentResult: OptimizationResult;
  }) => Promise<{ costImpactReport: string; capacityImpactReport: string }>;
  guardar_archivo_base64?: (
    filename: string,
    base64Data: string,
    fileTypes: string[]
  ) => Promise<NativeSaveResult>;
  guardar_pdf_ejecutivo?: (payload: {
    resultado: OptimizationResult;
    parametros: ScenarioParameters;
    impacto?: ChartImpactReport;
  }) => Promise<NativeSaveResult>;
}

declare global {
  interface Window {
    pywebview?: {
      api?: PyWebViewApi;
    };
  }
}
