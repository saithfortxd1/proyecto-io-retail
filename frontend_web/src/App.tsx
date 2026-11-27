import { useCallback, useEffect, useRef, useState } from 'react';
import { AssistantView } from './components/AssistantView.tsx';
import { ConfirmModal } from './components/ConfirmModal.tsx';
import { DashboardView } from './components/DashboardView.tsx';
import { FloatingChat } from './components/FloatingChat.tsx';
import { LicenseView } from './components/LicenseView.tsx';
import { ManualView } from './components/ManualView.tsx';
import { MatrixView } from './components/MatrixView.tsx';
import { Sidebar } from './components/Sidebar.tsx';
import { Toast } from './components/Toast.tsx';
import { TutorialModal } from './components/TutorialModal.tsx';
import {
  COSTOS_ENVIO_DEFAULT,
  DEFAULT_PARAMETERS,
  DEFAULT_TUTORIAL_STEPS,
  UBICACIONES_DEFAULT,
  ZONAS_DEFAULT,
} from './data/defaults.ts';
import {
  checkAssistantStatus,
  fetchChartImpactReport,
  fetchGeminiTutorialSteps,
  sendAssistantQuestion,
} from './lib/assistantClient.ts';
import { resolverEscenarioConPuente, resolverModelo } from './lib/mipSolver.ts';
import type {
  ChartImpactReport,
  ChatMessage,
  ChatTurn,
  OptimizationResult,
  ScenarioParameters,
  ToastKind,
  ToastState,
  TutorialStep,
  ViewId,
} from './types.ts';

const TUTORIAL_STORAGE_KEY = 'mip_tutorial_seen_v1';

interface ConfirmDialogState {
  open: boolean;
  title: string;
  message: string;
  confirmText: string;
  onConfirm: () => void;
}

function buildAssistantContext(
  visibleParams: ScenarioParameters,
  isEditing: boolean,
  lastResult: OptimizationResult | null
): string {
  const parameterState = {
    costos_fijos_usd_mes: Object.fromEntries(
      UBICACIONES_DEFAULT.map((u, i) => [u, visibleParams.costos_fijos[i]])
    ),
    capacidades_unidades_mes: Object.fromEntries(
      UBICACIONES_DEFAULT.map((u, i) => [u, visibleParams.capacidades[i]])
    ),
    demandas_unidades_mes: Object.fromEntries(
      ZONAS_DEFAULT.map((z, j) => [z, visibleParams.demandas[j]])
    ),
    max_centros: visibleParams.max_centros,
    baseline_usd_mes: visibleParams.costo_baseline,
    total_demanda_unidades_mes: visibleParams.demandas.reduce((a, b) => a + b, 0),
    edicion_en_curso_sin_guardar: isEditing,
  };

  const resultState = lastResult
    ? {
        estado: lastResult.estado,
        centros_abiertos_ultimo_calculo: lastResult.centros_abiertos,
        costo_fijo_usd_mes: lastResult.costo_fijo,
        costo_transporte_usd_mes: lastResult.costo_variable,
        costo_total_usd_mes: lastResult.costo_total,
        ahorro_usd_mes: lastResult.ahorro,
        ahorro_porcentaje: lastResult.porcentaje_ahorro,
        asignaciones: lastResult.asignaciones,
      }
    : 'Todavía no hay un resultado calculado.';

  return (
    'ESTADO DINÁMICO CAPTURADO AL ENVIAR ESTA PREGUNTA ' +
    '(los parámetros pueden ser distintos de los del informe):\n' +
    `Parámetros visibles: ${JSON.stringify(parameterState)}\n` +
    `Último resultado calculado: ${JSON.stringify(resultState)}\n` +
    `Tarifas de envío visibles: matriz oficial fija ${JSON.stringify(COSTOS_ENVIO_DEFAULT)}; ` +
    'la pantalla no tiene campos editables para tarifas. Si los parámetros visibles fueron modificados ' +
    'después del último cálculo, indícalo y no presentes el resultado anterior como si correspondiera a esos parámetros.'
  );
}

export default function App() {
  const [currentView, setCurrentView] = useState<ViewId>('dashboard');
  const [savedParams, setSavedParams] = useState<ScenarioParameters>(DEFAULT_PARAMETERS);
  const [visibleDraftParams, setVisibleDraftParams] =
    useState<ScenarioParameters>(DEFAULT_PARAMETERS);
  const [isEditingDraft, setIsEditingDraft] = useState(false);

  const [lastResult, setLastResult] = useState<OptimizationResult | null>(() =>
    resolverModelo(DEFAULT_PARAMETERS)
  );
  const [lastResultParams, setLastResultParams] = useState<ScenarioParameters | null>(
    DEFAULT_PARAMETERS
  );

  // Chart AI Impact Report state
  const [chartImpactReport, setChartImpactReport] = useState<ChartImpactReport>({
    costImpactReport: '',
    capacityImpactReport: '',
    loading: false,
    error: null,
    source: 'none',
  });

  // Tutorial modal state
  const [tutorialOpen, setTutorialOpen] = useState<boolean>(() => {
    try {
      return window.localStorage.getItem(TUTORIAL_STORAGE_KEY) !== '1';
    } catch {
      return true;
    }
  });
  const [tutorialSteps, setTutorialSteps] = useState<TutorialStep[]>(
    DEFAULT_TUTORIAL_STEPS
  );
  const [tutorialLoading, setTutorialLoading] = useState(false);
  const [tutorialError, setTutorialError] = useState<string | null>(null);
  const [tutorialEnhanced, setTutorialEnhanced] = useState(false);

  // Progressive execution state
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionVisible, setExecutionVisible] = useState(false);
  const [executionProgress, setExecutionProgress] = useState(0);
  const [executionStatusText, setExecutionStatusText] = useState('Listo para ejecutar');
  const [executionStatusTone, setExecutionStatusTone] = useState<
    'primary' | 'success' | 'danger' | 'muted'
  >('muted');
  const [executionLogs, setExecutionLogs] = useState<string[]>([]);

  // Toast
  const [toast, setToast] = useState<ToastState | null>(null);
  const toastTimerRef = useRef<number | null>(null);

  const notify = useCallback((message: string, kind: ToastKind = 'success') => {
    if (toastTimerRef.current !== null) {
      window.clearTimeout(toastTimerRef.current);
    }
    const id = Date.now();
    setToast({ id, message, kind });
    toastTimerRef.current = window.setTimeout(() => {
      setToast((prev) => (prev?.id === id ? null : prev));
    }, 3600);
  }, []);

  // Confirmation modal
  const [confirmState, setConfirmState] = useState<ConfirmDialogState>({
    open: false,
    title: '',
    message: '',
    confirmText: 'Confirmar',
    onConfirm: () => {},
  });

  const requestConfirm = (
    title: string,
    message: string,
    confirmText: string,
    onConfirm: () => void
  ) => {
    setConfirmState({
      open: true,
      title,
      message,
      confirmText,
      onConfirm: () => {
        setConfirmState((prev) => ({ ...prev, open: false }));
        onConfirm();
      },
    });
  };

  // Assistant state
  const [assistantConfigured, setAssistantConfigured] = useState<boolean | null>(null);
  const [assistantStatusText, setAssistantStatusText] = useState(
    'Verificando disponibilidad de Gemini…'
  );
  const [chatBusy, setChatBusy] = useState(false);
  const [quickQuestionsHidden, setQuickQuestionsHidden] = useState(false);
  const [chatConversation, setChatConversation] = useState<ChatTurn[]>([]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      text:
        'Hola. Puedo explicar el modelo, comparar el escenario actual y guiarte por las pestañas. Al enviar una pregunta adjunto los parámetros visibles y el último resultado calculado.',
    },
  ]);

  useEffect(() => {
    let active = true;
    checkAssistantStatus().then((status) => {
      if (!active) return;
      setAssistantConfigured(status.configured);
      if (status.configured) {
        setAssistantStatusText(
          `Gemini está habilitado en el servidor (${status.model}).`
        );
      } else {
        setAssistantStatusText(
          'Gemini no está configurado en el servidor. Agrega GEMINI_API_KEY en Secretos / Variables de entorno (o en .env local); la optimización funciona sin conexión.'
        );
      }
    });
    return () => {
      active = false;
    };
  }, []);

  const loadGeminiTutorialIfNeeded = useCallback(async () => {
    if (tutorialEnhanced || tutorialLoading) return;
    if (assistantConfigured === false) {
      setTutorialError('Gemini no está configurado en el servidor (GEMINI_API_KEY).');
      return;
    }
    if (assistantConfigured !== true) return;

    setTutorialLoading(true);
    setTutorialError(null);
    try {
      const steps = await fetchGeminiTutorialSteps();
      setTutorialSteps(steps);
      setTutorialEnhanced(true);
    } catch (err) {
      setTutorialError(
        err instanceof Error ? err.message : 'No se pudo consultar a Gemini.'
      );
    } finally {
      setTutorialLoading(false);
    }
  }, [assistantConfigured, tutorialEnhanced, tutorialLoading]);

  useEffect(() => {
    if (tutorialOpen && assistantConfigured !== null) {
      void loadGeminiTutorialIfNeeded();
    }
  }, [tutorialOpen, assistantConfigured, loadGeminiTutorialIfNeeded]);

  const closeTutorial = () => {
    setTutorialOpen(false);
    setCurrentView('dashboard');
    try {
      window.localStorage.setItem(TUTORIAL_STORAGE_KEY, '1');
    } catch {
      // Ignore storage failures
    }
  };

  const handleOpenTutorial = () => {
    setTutorialOpen(true);
  };

  const handleRestoreBase = async () => {
    setSavedParams(DEFAULT_PARAMETERS);
    setVisibleDraftParams(DEFAULT_PARAMETERS);
    setIsEditingDraft(false);

    try {
      const { result: res } = await resolverEscenarioConPuente(DEFAULT_PARAMETERS);
      if (res.estado === 'Optimal') {
        setLastResult(res);
        setLastResultParams(DEFAULT_PARAMETERS);
        setChartImpactReport({
          costImpactReport: '',
          capacityImpactReport: '',
          loading: false,
          error: null,
          source: 'none',
        });
        notify('Parámetros oficiales restaurados; escenario recalculado.', 'info');
      } else {
        notify(`No se pudo calcular el escenario base: ${res.mensaje}`, 'error');
      }
    } catch (err) {
      notify(
        `No se pudo recalcular el escenario base: ${err instanceof Error ? err.message : 'Error'}`,
        'error'
      );
    }
  };

  const triggerChartImpactAnalysis = async (
    prevParams: ScenarioParameters,
    prevResult: OptimizationResult | null,
    nextParams: ScenarioParameters,
    nextResult: OptimizationResult
  ) => {
    if (assistantConfigured === false) {
      setChartImpactReport({
        costImpactReport: '',
        capacityImpactReport: '',
        loading: false,
        error:
          'Gemini no está configurado en el servidor (GEMINI_API_KEY). Se muestra el resumen numérico local.',
        source: 'none',
      });
      return;
    }

    setChartImpactReport({
      costImpactReport: '',
      capacityImpactReport: '',
      loading: true,
      error: null,
      source: 'none',
    });

    try {
      const report = await fetchChartImpactReport(
        prevParams,
        prevResult,
        nextParams,
        nextResult
      );
      setChartImpactReport({
        costImpactReport: report.costImpactReport,
        capacityImpactReport: report.capacityImpactReport,
        loading: false,
        error: null,
        source: 'gemini',
      });
    } catch (err) {
      setChartImpactReport({
        costImpactReport: '',
        capacityImpactReport: '',
        loading: false,
        error:
          err instanceof Error
            ? `No se pudo generar el informe con Gemini: ${err.message}`
            : 'No se pudo generar el informe con Gemini.',
        source: 'none',
      });
    }
  };

  const handleExecuteOptimization = () => {
    if (isExecuting) return;

    const paramsToSolve = savedParams;
    const prevParamsSnapshot = lastResultParams ?? DEFAULT_PARAMETERS;
    const prevResultSnapshot = lastResult;

    const maxCap = [...paramsToSolve.capacidades]
      .sort((a, b) => b - a)
      .slice(0, paramsToSolve.max_centros)
      .reduce((a, b) => a + b, 0);
    const totalDemand = paramsToSolve.demandas.reduce((a, b) => a + b, 0);

    const steps = [
      `[1/4] Validando capacidad máxima disponible (${maxCap.toLocaleString('en-US')} u) frente a demanda (${totalDemand.toLocaleString('en-US')} u)...`,
      '[2/4] Construyendo el modelo MIP con los parámetros guardados...',
      '[3/4] Resolviendo el modelo con Branch-and-Bound exacto...',
      '[4/4] Finalizando la solución óptima del escenario...',
    ];

    setIsExecuting(true);
    setExecutionVisible(true);
    setExecutionProgress(0);
    setExecutionStatusTone('primary');
    setExecutionStatusText('Iniciando…');
    setExecutionLogs(['[0.0s] Iniciando optimización...']);

    const delays = [240, 300, 340, 200];

    const runStep = async (idx: number) => {
      if (idx >= steps.length) {
        setExecutionLogs((prev) => [...prev, '✓ Ejecutando solver MIP...']);
        let resultado: OptimizationResult;
        let engineUsed: 'pywebview' | 'typescript' = 'typescript';

        try {
          const solved = await resolverEscenarioConPuente(paramsToSolve);
          resultado = solved.result;
          engineUsed = solved.engine;
        } catch (err) {
          setIsExecuting(false);
          setExecutionStatusTone('danger');
          setExecutionStatusText('Error');
          const msg =
            err instanceof Error ? err.message : 'Error al ejecutar el solver.';
          setExecutionLogs((prev) => [...prev, `Error de optimización: ${msg}`]);
          notify(`No se pudo resolver el escenario: ${msg}`, 'error');
          return;
        }

        setIsExecuting(false);
        if (resultado.estado !== 'Optimal') {
          setExecutionStatusTone('danger');
          setExecutionStatusText('Error');
          setExecutionLogs((prev) => [
            ...prev,
            `Error de optimización: ${resultado.estado}: ${resultado.mensaje}`,
          ]);
          notify(
            `No se pudo resolver el escenario: ${resultado.estado}: ${resultado.mensaje}`,
            'error'
          );
          return;
        }

        setLastResult(resultado);
        setLastResultParams(paramsToSolve);
        setExecutionProgress(1);
        setExecutionStatusTone('success');
        setExecutionStatusText('Completado ✓');
        setExecutionLogs((prev) => [
          ...prev,
          `[${engineUsed === 'pywebview' ? 'Python · PuLP' : 'Solver MIP Local'}] OPTIMAL: $${resultado.costo_total.toLocaleString('en-US', {
            maximumFractionDigits: 0,
          })} USD | Ahorro: $${resultado.ahorro.toLocaleString('en-US', {
            maximumFractionDigits: 0,
          })} USD (${resultado.porcentaje_ahorro.toFixed(2)}%)`,
        ]);
        notify(
          `Optimización lista: ${resultado.centros_abiertos.join(', ')}, $${resultado.costo_total.toLocaleString(
            'en-US',
            { maximumFractionDigits: 0 }
          )} USD/mes.`,
          'success'
        );

        void triggerChartImpactAnalysis(
          prevParamsSnapshot,
          prevResultSnapshot,
          paramsToSolve,
          resultado
        );
        return;
      }

      setExecutionProgress((idx + 1) / (steps.length + 1));
      setExecutionStatusText(`Paso ${idx + 1}/4`);
      setExecutionLogs((prev) => [...prev, steps[idx]]);

      window.setTimeout(() => runStep(idx + 1), delays[idx]);
    };

    window.setTimeout(() => runStep(0), 160);
  };

  const handleSendMessage = async (question: string) => {
    if (chatBusy) return;
    if (!quickQuestionsHidden) {
      setQuickQuestionsHidden(true);
    }

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: 'user',
      text: question,
    };
    setChatMessages((prev) => [...prev, userMsg]);

    if (assistantConfigured === false) {
      setChatMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: 'assistant',
          text:
            'Gemini no está configurado en el servidor. Agrega tu clave GEMINI_API_KEY en el panel de Secretos / Variables de entorno de AI Studio (o en un archivo .env si lo ejecutas en tu PC). La optimización matemática y las demás vistas siguen funcionando normalmente.',
        },
      ]);
      notify('Falta GEMINI_API_KEY en Secretos o .env.', 'info');
      return;
    }

    const context = buildAssistantContext(
      visibleDraftParams,
      isEditingDraft,
      lastResult
    );

    setChatBusy(true);
    setAssistantStatusText('Gemini está preparando una respuesta…');

    try {
      const result = await sendAssistantQuestion(
        question,
        context,
        chatConversation.slice(-12)
      );

      setAssistantStatusText(`Respuesta recibida de ${result.model}.`);
      setChatConversation((prev) =>
        [
          ...prev,
          { role: 'user' as const, text: question },
          { role: 'model' as const, text: result.answer },
        ].slice(-12)
      );
      setChatMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: 'assistant',
          text: result.answer,
        },
      ]);
    } catch (error) {
      const msg = error instanceof Error ? error.message : 'Error de red.';
      setAssistantStatusText('No se pudo completar la consulta.');
      setChatMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: 'assistant',
          text: `No fue posible consultar Gemini: ${msg}`,
        },
      ]);
      notify('No se pudo completar la consulta a Gemini.', 'error');
    } finally {
      setChatBusy(false);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#F4F7FB]">
      <Sidebar
        currentView={currentView}
        onSelectView={setCurrentView}
        onOpenTutorial={handleOpenTutorial}
      />

      <main className="flex-1 overflow-y-auto px-7 py-6">
        <div className="mx-auto max-w-[1260px]">
          {currentView === 'dashboard' && (
            <DashboardView
              savedParams={savedParams}
              lastResult={lastResult}
              lastResultParams={lastResultParams}
              chartImpactReport={chartImpactReport}
              isExecuting={isExecuting}
              executionVisible={executionVisible}
              executionProgress={executionProgress}
              executionStatusText={executionStatusText}
              executionStatusTone={executionStatusTone}
              executionLogs={executionLogs}
              onSwitchToAssistant={() => setCurrentView('assistant')}
              onOpenTutorial={handleOpenTutorial}
              onRequestConfirm={requestConfirm}
              onSaveParams={(next) => {
                setSavedParams(next);
                setVisibleDraftParams(next);
                setIsEditingDraft(false);
              }}
              onRestoreBase={handleRestoreBase}
              onExecuteOptimization={handleExecuteOptimization}
              onNotify={notify}
              onDraftChange={(draft, editing) => {
                setVisibleDraftParams(draft);
                setIsEditingDraft(editing);
              }}
            />
          )}

          {currentView === 'matrix' && (
            <MatrixView
              result={lastResult}
              params={lastResultParams ?? savedParams}
              onNotify={notify}
            />
          )}

          {currentView === 'manual' && <ManualView />}

          {currentView === 'assistant' && (
            <AssistantView
              messages={chatMessages}
              chatBusy={chatBusy}
              quickQuestionsHidden={quickQuestionsHidden}
              statusText={assistantStatusText}
              onSendMessage={handleSendMessage}
            />
          )}

          {currentView === 'license' && <LicenseView />}
        </div>
      </main>

      <FloatingChat
        visible={
          currentView === 'dashboard' ||
          currentView === 'matrix' ||
          currentView === 'manual'
        }
        messages={chatMessages}
        chatBusy={chatBusy}
        onSendMessage={handleSendMessage}
      />

      <TutorialModal
        open={tutorialOpen}
        steps={tutorialSteps}
        loadingGemini={tutorialLoading}
        geminiError={tutorialError}
        geminiEnhanced={tutorialEnhanced}
        onSkip={closeTutorial}
        onComplete={closeTutorial}
        onNavigateView={(view) => setCurrentView(view)}
      />

      <ConfirmModal
        open={confirmState.open}
        title={confirmState.title}
        message={confirmState.message}
        confirmText={confirmState.confirmText}
        onConfirm={confirmState.onConfirm}
        onCancel={() => setConfirmState((prev) => ({ ...prev, open: false }))}
      />

      <Toast toast={toast} onDismiss={() => setToast(null)} />
    </div>
  );
}
