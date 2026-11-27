import type {
  ChatTurn,
  OptimizationResult,
  ScenarioParameters,
  TutorialStep,
  ViewId,
} from '../types.ts';

export interface AssistantStatusResult {
  configured: boolean;
  model: string;
  source?: 'pywebview' | 'server';
}

export interface AssistantQueryResult {
  answer: string;
  model: string;
}

function desktopApi() {
  return typeof window !== 'undefined' ? window.pywebview?.api : undefined;
}

function isDesktopShell(): boolean {
  return typeof window !== 'undefined' &&
    (Boolean(window.pywebview) || window.location.protocol === 'file:');
}

async function desktopApiWhenReady() {
  if (typeof window === 'undefined') return undefined;
  const initialApi = desktopApi();
  if (initialApi) return initialApi;
  if (!isDesktopShell()) return undefined;

  await new Promise<void>((resolve) => {
    let settled = false;
    const finish = () => {
      if (settled) return;
      settled = true;
      window.clearTimeout(timeoutId);
      window.removeEventListener('pywebviewready', finish);
      resolve();
    };
    const timeoutId = window.setTimeout(finish, 5000);
    window.addEventListener('pywebviewready', finish, { once: true });
  });
  return desktopApi();
}

async function desktopChatApiWhenReady() {
  const readyApi = await desktopApiWhenReady();
  return typeof readyApi?.consultar_asistente === 'function' ? readyApi : undefined;
}

export function sanitizeAssistantResponse(answer: string): string {
  return answer
    .replace(/\*{1,2}|#+/g, '')
    .replace(/```/g, '')
    .replace(/`/g, '')
    .trim();
}

export async function checkAssistantStatus(): Promise<AssistantStatusResult> {
  const api = await desktopApiWhenReady();
  if (api?.estado_asistente) {
    try {
      return { ...(await api.estado_asistente()), source: 'pywebview' };
    } catch {
      if (isDesktopShell()) return { configured: false, model: 'gemini-2.5-flash', source: 'pywebview' };
    }
  }
  if (isDesktopShell()) {
    return { configured: false, model: 'gemini-2.5-flash', source: 'pywebview' };
  }
  try {
    const res = await fetch('/api/assistant/status');
    const contentType = res.headers.get('content-type') || '';
    if (res.ok && contentType.includes('application/json')) {
      const data = (await res.json()) as { configured?: boolean; model?: string };
      return {
        configured: Boolean(data.configured),
        model: data.model ?? 'gemini-4-hydrogen',
        source: 'server',
      };
    }
  } catch {
    // Server status unavailable
  }

  return {
    configured: false,
    model: 'gemini-4-hydrogen',
    source: 'server',
  };
}

export async function sendAssistantQuestion(
  question: string,
  context: string,
  priorTurns: ChatTurn[]
): Promise<AssistantQueryResult> {
  const api = await desktopChatApiWhenReady();
  if (api?.consultar_asistente) {
    const result = await api.consultar_asistente({
      question,
      context,
      priorTurns: priorTurns.slice(-12),
    });
    if (!result?.answer) throw new Error('No se pudo completar la consulta.');
    return { answer: sanitizeAssistantResponse(result.answer), model: result.model };
  }

  if (isDesktopShell()) {
    throw new Error('El puente nativo del asistente no está disponible. Reinicia la aplicación de escritorio.');
  }

  const res = await fetch('/api/assistant', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      context,
      priorTurns: priorTurns.slice(-12),
    }),
  });

  const contentType = res.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(
      'El servicio del asistente requiere el servidor backend activo (/api/assistant).'
    );
  }

  const data = (await res.json()) as {
    answer?: string;
    model?: string;
    error?: string;
  };

  if (!res.ok || !data.answer) {
    throw new Error(data.error ?? 'No se pudo completar la consulta.');
  }

  return {
    answer: sanitizeAssistantResponse(data.answer),
    model: data.model ?? 'gemini-4-hydrogen',
  };
}

const TARGET_VIEWS: ViewId[] = [
  'dashboard',
  'dashboard',
  'dashboard',
  'matrix',
  'assistant',
];

export async function fetchGeminiTutorialSteps(): Promise<TutorialStep[]> {
  const api = desktopApi();
  if (api?.generar_tutorial) {
    const result = await api.generar_tutorial();
    if (!Array.isArray(result?.steps) || result.steps.length === 0) {
      throw new Error('No se pudo generar el tutorial con Gemini.');
    }
    return result.steps.map((step, idx) => ({
      ...step,
      targetView: TARGET_VIEWS[idx] ?? 'dashboard',
    }));
  }

  const res = await fetch('/api/assistant/tutorial', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });

  const contentType = res.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error('El servidor del asistente no está disponible.');
  }

  const data = (await res.json()) as {
    steps?: Array<{
      id: string;
      section: string;
      title: string;
      summary: string;
      tip: string;
    }>;
    error?: string;
  };

  if (!res.ok || !Array.isArray(data.steps) || data.steps.length === 0) {
    throw new Error(data.error ?? 'No se pudo generar el tutorial con Gemini.');
  }

  return data.steps.map((step, idx) => ({
    ...step,
    targetView: TARGET_VIEWS[idx] ?? 'dashboard',
  }));
}

export async function fetchChartImpactReport(
  previousParams: ScenarioParameters,
  previousResult: OptimizationResult | null,
  currentParams: ScenarioParameters,
  currentResult: OptimizationResult
): Promise<{ costImpactReport: string; capacityImpactReport: string }> {
  const api = desktopApi();
  if (api?.analizar_impacto_graficos) {
    const result = await api.analizar_impacto_graficos({
      previousParams,
      previousResult,
      currentParams,
      currentResult,
    });
    if (!result?.costImpactReport || !result.capacityImpactReport) {
      throw new Error('No se pudo generar el análisis de impacto con Gemini.');
    }
    return {
      costImpactReport: sanitizeAssistantResponse(result.costImpactReport),
      capacityImpactReport: sanitizeAssistantResponse(result.capacityImpactReport),
    };
  }

  const res = await fetch('/api/assistant/chart-impact', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      previousParams,
      previousResult,
      currentParams,
      currentResult,
    }),
  });

  const contentType = res.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error('El servidor del asistente no está disponible.');
  }

  const data = (await res.json()) as {
    costImpactReport?: string;
    capacityImpactReport?: string;
    error?: string;
  };

  if (!res.ok || !data.costImpactReport || !data.capacityImpactReport) {
    throw new Error(
      data.error ?? 'No se pudo generar el análisis de impacto con Gemini.'
    );
  }

  return {
    costImpactReport: sanitizeAssistantResponse(data.costImpactReport),
    capacityImpactReport: sanitizeAssistantResponse(data.capacityImpactReport),
  };
}
