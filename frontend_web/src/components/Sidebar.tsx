import {
  BarChart3,
  BookOpen,
  Bot,
  Briefcase,
  ClipboardList,
  Compass,
} from 'lucide-react';
import type { ViewId } from '../types.ts';

interface SidebarProps {
  currentView: ViewId;
  onSelectView: (view: ViewId) => void;
  onOpenTutorial: () => void;
}

const NAV_ITEMS: { id: ViewId; label: string; icon: typeof BarChart3 }[] = [
  { id: 'dashboard', label: 'Dashboard y Simulación', icon: BarChart3 },
  { id: 'matrix', label: 'Matriz de Rutas y Reportes', icon: ClipboardList },
  { id: 'manual', label: 'Manual de Uso y Modelo', icon: BookOpen },
  { id: 'assistant', label: 'Asistente IA (Gemini)', icon: Bot },
  { id: 'license', label: 'Licencia y ROI Comercial', icon: Briefcase },
];

export function Sidebar({ currentView, onSelectView, onOpenTutorial }: SidebarProps) {
  return (
    <aside className="flex w-[256px] shrink-0 flex-col border-r border-slate-800 bg-[#0F172A] text-white select-none">
      {/* Brand Lockup */}
      <div className="flex items-center gap-3 px-5 pt-6 pb-5">
        <svg
          width="38"
          height="38"
          viewBox="0 0 38 38"
          fill="none"
          aria-hidden="true"
          className="shrink-0"
        >
          <line x1="7" y1="19" x2="18" y2="7" stroke="#3B82F6" strokeWidth="2" />
          <line x1="18" y1="7" x2="29" y2="19" stroke="#3B82F6" strokeWidth="2" />
          <line x1="29" y1="19" x2="18" y2="31" stroke="#3B82F6" strokeWidth="2" />
          <line x1="18" y1="31" x2="7" y2="19" stroke="#3B82F6" strokeWidth="2" />
          <line x1="7" y1="19" x2="29" y2="19" stroke="#34D399" strokeWidth="1.5" />
          <circle cx="7" cy="19" r="3" fill="#34D399" stroke="#0F172A" />
          <circle cx="18" cy="7" r="3" fill="#60A5FA" stroke="#0F172A" />
          <circle cx="29" cy="19" r="3" fill="#34D399" stroke="#0F172A" />
          <circle cx="18" cy="31" r="3" fill="#60A5FA" stroke="#0F172A" />
          <circle cx="18" cy="19" r="4" fill="#FFFFFF" stroke="#0F172A" />
        </svg>
        <div className="min-w-0">
          <div className="text-[15px] font-bold leading-tight tracking-tight text-white">
            MIP Retail
            <br />
            Optimizer™
          </div>
          <div className="mt-0.5 text-[11px] font-semibold tracking-wide text-emerald-400">
            Enterprise Edition
          </div>
        </div>
      </div>

      <div className="mx-4 h-px bg-slate-800/90" />

      {/* Primary Navigation */}
      <nav
        className="flex-1 space-y-1 px-3 py-4"
        aria-label="Navegación principal"
      >
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = currentView === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelectView(item.id)}
              className={`group flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-left text-[13px] font-medium transition-all duration-150 whitespace-nowrap cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 ${
                active
                  ? 'bg-white/10 text-white shadow-sm ring-1 ring-white/15'
                  : 'text-slate-300 hover:bg-white/5 hover:text-white'
              }`}
            >
              <Icon
                className={`h-4 w-4 shrink-0 transition-colors ${
                  active
                    ? 'text-blue-400'
                    : 'text-slate-400 group-hover:text-slate-200'
                }`}
              />
              <span className="truncate">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Tutorial Trigger + Quiet Footer Info */}
      <div className="border-t border-slate-800/80 px-4 py-3.5 space-y-3">
        <button
          type="button"
          onClick={onOpenTutorial}
          className="flex w-full items-center gap-2.5 rounded-xl bg-white/5 px-3 py-2 text-[12.5px] font-semibold text-blue-200 transition-colors hover:bg-white/10 hover:text-white cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
        >
          <Compass className="h-4 w-4 text-blue-400 shrink-0" />
          <span>Tutorial Guiado (IA)</span>
        </button>

        <div className="px-1 text-[11px] text-slate-400">
          <div>v1.0.0 Enterprise</div>
          <div className="mt-0.5 text-slate-500">Motor MIP · Optimalidad Global</div>
        </div>
      </div>
    </aside>
  );
}
