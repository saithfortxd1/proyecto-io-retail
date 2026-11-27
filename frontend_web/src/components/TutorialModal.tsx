import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Compass,
  Sparkles,
  X,
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import type { TutorialStep, ViewId } from '../types.ts';

interface TutorialModalProps {
  open: boolean;
  steps: TutorialStep[];
  loadingGemini: boolean;
  geminiError: string | null;
  geminiEnhanced: boolean;
  onSkip: () => void;
  onComplete: () => void;
  onNavigateView?: (view: ViewId) => void;
}

const TOUR_SELECTORS = [
  '[data-tour="scenario-params"]',
  '[data-tour="run-optimize"]',
  '[data-tour="charts-ai"]',
  '[data-tour="export-pdf"]',
  '[data-tour="assistant-trigger"]',
];

interface TargetBox {
  top: number;
  left: number;
  width: number;
  height: number;
}

export function TutorialModal({
  open,
  steps,
  loadingGemini,
  geminiError,
  geminiEnhanced,
  onSkip,
  onComplete,
  onNavigateView,
}: TutorialModalProps) {
  const [stepIndex, setStepIndex] = useState(0);
  const [targetBox, setTargetBox] = useState<TargetBox | null>(null);
  const navigateRef = useRef(onNavigateView);
  navigateRef.current = onNavigateView;

  const measureTarget = useCallback((idx: number, shouldScroll: boolean) => {
    const selector = TOUR_SELECTORS[idx];
    if (!selector) {
      setTargetBox(null);
      return;
    }
    const el = document.querySelector(selector);
    if (!el) {
      setTargetBox(null);
      return;
    }

    if (shouldScroll) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
    }

    const rect = el.getBoundingClientRect();
    const pad = 8;
    setTargetBox({
      top: Math.max(8, rect.top - pad),
      left: Math.max(8, rect.left - pad),
      width: Math.min(window.innerWidth - 16, rect.width + pad * 2),
      height: Math.min(window.innerHeight - 16, rect.height + pad * 2),
    });
  }, []);

  useEffect(() => {
    if (!open) {
      setTargetBox(null);
      return;
    }
    setStepIndex(0);
    navigateRef.current?.('dashboard');
  }, [open]);

  useEffect(() => {
    if (!open) return;

    const rafId = window.requestAnimationFrame(() => {
      measureTarget(stepIndex, true);
    });
    const settleTimer = window.setTimeout(() => {
      measureTarget(stepIndex, false);
    }, 360);

    const handleSync = () => measureTarget(stepIndex, false);
    window.addEventListener('resize', handleSync);
    window.addEventListener('scroll', handleSync, true);

    return () => {
      window.cancelAnimationFrame(rafId);
      window.clearTimeout(settleTimer);
      window.removeEventListener('resize', handleSync);
      window.removeEventListener('scroll', handleSync, true);
    };
  }, [open, stepIndex, measureTarget]);

  if (!open || steps.length === 0) return null;

  const safeIndex = Math.min(stepIndex, steps.length - 1);
  const current = steps[safeIndex];
  const isFirst = safeIndex === 0;
  const isLast = safeIndex === steps.length - 1;
  const progressPct = ((safeIndex + 1) / steps.length) * 100;

  const goToStep = (nextIdx: number) => {
    const bounded = Math.max(0, Math.min(steps.length - 1, nextIdx));
    onNavigateView?.('dashboard');
    setStepIndex(bounded);
  };

  // Compute floating card placement anchored smoothly near the highlighted element
  const cardWidth = Math.min(390, window.innerWidth - 32);
  const estimatedCardHeight = 250;
  let cardStyle: React.CSSProperties;

  if (targetBox) {
    const spaceBelow = window.innerHeight - (targetBox.top + targetBox.height);
    const spaceAbove = targetBox.top;

    let topPos: number;
    if (spaceBelow >= estimatedCardHeight + 20) {
      topPos = targetBox.top + targetBox.height + 14;
    } else if (spaceAbove >= estimatedCardHeight + 20) {
      topPos = Math.max(16, targetBox.top - estimatedCardHeight - 14);
    } else {
      topPos = Math.max(
        16,
        Math.min(
          window.innerHeight - estimatedCardHeight - 16,
          targetBox.top + 16
        )
      );
    }

    const desiredLeft =
      targetBox.left + targetBox.width / 2 - cardWidth / 2;
    const clampedLeft = Math.max(
      16,
      Math.min(window.innerWidth - cardWidth - 16, desiredLeft)
    );

    cardStyle = {
      top: `${topPos}px`,
      left: `${clampedLeft}px`,
      width: `${cardWidth}px`,
    };
  } else {
    cardStyle = {
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      width: `${cardWidth}px`,
    };
  }

  return (
    <div
      className="fixed inset-0 z-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="tutorial-modal-title"
    >
      {/* Dimmer fallback if no target rect yet */}
      {!targetBox && (
        <div
          className="fixed inset-0 bg-slate-900/60 backdrop-blur-[1px] transition-opacity duration-300"
          onClick={onSkip}
        />
      )}

      {/* Animated Spotlight Cutout Window */}
      {targetBox && (
        <>
          <div className="fixed inset-0" onClick={onSkip} />
          <div
            className="pointer-events-none fixed rounded-2xl transition-all duration-300 ease-out animate-spotlight-ring"
            style={{
              top: targetBox.top,
              left: targetBox.left,
              width: targetBox.width,
              height: targetBox.height,
            }}
          />
        </>
      )}

      {/* Compact Animated Coachmark Card */}
      <div
        className="fixed z-50 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl transition-all duration-300 ease-out animate-panel-in"
        style={cardStyle}
      >
        {/* Top Progress Strip */}
        <div className="h-1 w-full bg-slate-100">
          <div
            className="h-full bg-gradient-to-r from-blue-600 to-indigo-600 transition-all duration-300"
            style={{ width: `${progressPct}%` }}
          />
        </div>

        <div className="p-5">
          {/* Header Row */}
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
                <Compass className="h-3.5 w-3.5" />
              </div>
              <span className="font-mono-num text-[11.5px] font-bold text-blue-600">
                {current.section}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <span className="font-mono-num text-[11px] font-semibold text-slate-400">
                {safeIndex + 1} / {steps.length}
              </span>
              <button
                type="button"
                onClick={onSkip}
                aria-label="Cerrar tutorial"
                className="rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Concise Step Content */}
          <div key={current.id} className="mt-3 animate-chapter-in">
            <h3
              id="tutorial-modal-title"
              className="text-[16px] font-bold tracking-tight text-slate-900"
            >
              {current.title}
            </h3>
            <p className="mt-1.5 text-[13px] leading-relaxed text-slate-600">
              {current.summary}
            </p>
            <div className="mt-3 flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-[12px] font-medium text-slate-700">
              <Sparkles className="h-3.5 w-3.5 shrink-0 text-blue-600" />
              <span>{current.tip}</span>
            </div>
          </div>

          {loadingGemini && (
            <div className="mt-2.5 flex items-center gap-1.5 text-[11px] text-slate-400">
              <span>Gemini IA</span>
              <span className="inline-flex gap-0.5 text-blue-600">
                <span className="animate-dot-1">●</span>
                <span className="animate-dot-2">●</span>
                <span className="animate-dot-3">●</span>
              </span>
            </div>
          )}

          {!loadingGemini && geminiEnhanced && (
            <div className="mt-2.5 flex items-center gap-1 text-[11px] font-medium text-blue-600">
              <Sparkles className="h-3 w-3" />
              <span>Resumido por Gemini IA</span>
            </div>
          )}

          {!loadingGemini && geminiError && (
            <div className="mt-2 text-[11px] text-slate-400">
              Guía interactiva activa
            </div>
          )}

          {/* Progress Dots + Actions */}
          <div className="mt-4 flex items-center justify-between gap-2 border-t border-slate-100 pt-3.5">
            <button
              type="button"
              onClick={onSkip}
              className="rounded-lg px-2.5 py-1.5 text-[12px] font-semibold text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800 cursor-pointer"
            >
              Omitir
            </button>

            <div className="flex items-center gap-1.5">
              {steps.map((s, idx) => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => goToStep(idx)}
                  aria-label={`Paso ${idx + 1}`}
                  className={`h-1.5 rounded-full transition-all duration-300 cursor-pointer ${
                    idx === safeIndex
                      ? 'w-5 bg-blue-600'
                      : 'w-1.5 bg-slate-200 hover:bg-slate-300'
                  }`}
                />
              ))}
            </div>

            <div className="flex items-center gap-1.5">
              {!isFirst && (
                <button
                  type="button"
                  onClick={() => goToStep(safeIndex - 1)}
                  className="inline-flex h-8 items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 text-[12px] font-semibold text-slate-700 transition-all hover:bg-slate-50 active:scale-95 cursor-pointer"
                >
                  <ArrowLeft className="h-3.5 w-3.5" />
                  <span>Atrás</span>
                </button>
              )}

              {!isLast ? (
                <button
                  type="button"
                  onClick={() => goToStep(safeIndex + 1)}
                  className="inline-flex h-8 items-center gap-1 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 px-3 text-[12px] font-semibold text-white shadow-xs transition-all hover:from-blue-700 hover:to-indigo-700 active:scale-95 cursor-pointer"
                >
                  <span>Siguiente</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={onComplete}
                  className="inline-flex h-8 items-center gap-1 rounded-lg bg-emerald-600 px-3 text-[12px] font-semibold text-white shadow-xs transition-all hover:bg-emerald-700 active:scale-95 cursor-pointer"
                >
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>Listo</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
