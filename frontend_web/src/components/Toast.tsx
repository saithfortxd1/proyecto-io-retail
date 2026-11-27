import { X } from 'lucide-react';
import type { ToastState } from '../types.ts';

interface ToastProps {
  toast: ToastState | null;
  onDismiss: () => void;
}

const PALETTE = {
  success: 'bg-emerald-600 border-emerald-700 text-white',
  error: 'bg-red-600 border-red-700 text-white',
  info: 'bg-blue-600 border-blue-700 text-white',
  warning: 'bg-amber-600 border-amber-700 text-white',
};

export function Toast({ toast, onDismiss }: ToastProps) {
  if (!toast) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className={`fixed bottom-24 left-1/2 z-50 flex -translate-x-1/2 max-w-md items-center gap-3 rounded-xl border px-4 py-3 shadow-xl transition-all duration-200 ${PALETTE[toast.kind]}`}
    >
      <p className="text-[13px] font-medium leading-snug">{toast.message}</p>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Cerrar notificación"
        className="ml-1 shrink-0 rounded-lg p-1 text-white/80 transition-colors hover:bg-white/15 hover:text-white cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
