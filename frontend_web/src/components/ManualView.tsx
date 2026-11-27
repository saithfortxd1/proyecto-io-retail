import { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { MANUAL_CHAPTERS } from '../data/defaults.ts';

export function ManualView() {
  const [pageIndex, setPageIndex] = useState(0);
  const chapter = MANUAL_CHAPTERS[pageIndex];
  const progressPct = ((pageIndex + 1) / MANUAL_CHAPTERS.length) * 100;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-[24px] font-bold tracking-tight text-slate-900">
          Manual de Uso y Modelo
        </h1>
        <p className="mt-1 text-[13.5px] text-slate-500">
          Guía interactiva paso a paso · Cinco capítulos para operar y comprender el modelo MIP.
        </p>
      </div>

      {/* Interactive Chapter Stepper */}
      <div className="flex flex-wrap items-center gap-1.5 rounded-xl bg-slate-200/70 p-1.5">
        {MANUAL_CHAPTERS.map((item, idx) => {
          const active = idx === pageIndex;
          return (
            <button
              key={item.title}
              type="button"
              onClick={() => setPageIndex(idx)}
              className={`flex-1 min-w-[140px] rounded-lg px-3 py-2 text-left text-[12px] font-semibold transition-all duration-150 whitespace-nowrap truncate cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 ${
                active
                  ? 'bg-white text-blue-600 shadow-xs'
                  : 'text-slate-600 hover:bg-white/60 hover:text-slate-900'
              }`}
            >
              0{idx + 1}. {item.title.split('(')[0].trim()}
            </button>
          );
        })}
      </div>

      {/* Book Container */}
      <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="font-mono-num text-[12px] font-semibold text-blue-600">
            Capítulo {pageIndex + 1} de {MANUAL_CHAPTERS.length}
          </div>
          <div className="text-[12px] text-slate-400">
            Documentación operativa · CFLP
          </div>
        </div>

        <div
          key={pageIndex}
          className="mt-6 grid grid-cols-1 gap-8 lg:grid-cols-2 animate-chapter-in"
        >
          {/* Left Column */}
          <div className="space-y-5 lg:border-r lg:border-slate-100 lg:pr-8">
            <div>
              <h2 className="text-[20px] font-bold leading-snug tracking-tight text-slate-900">
                {chapter.title}
              </h2>
              <p className="mt-2 text-[14px] leading-relaxed text-slate-500">
                {chapter.subtitle}
              </p>
            </div>

            <div className="border-t border-slate-100 pt-5">
              <h3 className="text-[14px] font-bold text-slate-900">
                {chapter.left_heading}
              </h3>
              <p className="mt-2 text-[14px] leading-relaxed text-slate-600">
                {chapter.left_text}
              </p>
            </div>
          </div>

          {/* Right Column */}
          <div className="flex flex-col justify-between space-y-5 rounded-xl bg-slate-50/80 p-6">
            <div>
              <h3 className="text-[14px] font-bold text-emerald-700">
                {chapter.right_heading}
              </h3>
              <p className="mt-2.5 text-[14px] leading-relaxed text-slate-600">
                {chapter.right_text}
              </p>
            </div>

            <div className="border-t border-slate-200/70 pt-4 text-[12px] text-slate-400">
              MIP Retail Optimizer™ Enterprise · Referencia técnica oficial
            </div>
          </div>
        </div>

        {/* Footer Controls */}
        <div className="mt-7 flex items-center gap-4 border-t border-slate-100 pt-5">
          <button
            type="button"
            disabled={pageIndex === 0}
            onClick={() => setPageIndex((p) => Math.max(0, p - 1))}
            className="inline-flex h-10 w-[168px] shrink-0 items-center justify-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 text-[13px] font-semibold text-slate-600 transition-all hover:bg-slate-100 active:scale-[0.99] disabled:opacity-40 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
          >
            <ChevronLeft className="h-4 w-4" />
            <span>Página Anterior</span>
          </button>

          <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 transition-all duration-300"
              style={{ width: `${progressPct}%` }}
            />
          </div>

          <button
            type="button"
            disabled={pageIndex === MANUAL_CHAPTERS.length - 1}
            onClick={() =>
              setPageIndex((p) => Math.min(MANUAL_CHAPTERS.length - 1, p + 1))
            }
            className="inline-flex h-10 w-[168px] shrink-0 items-center justify-center gap-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-[13px] font-semibold text-white shadow-sm transition-all hover:from-blue-700 hover:to-indigo-700 active:scale-[0.99] disabled:opacity-40 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          >
            <span>Página Siguiente</span>
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
