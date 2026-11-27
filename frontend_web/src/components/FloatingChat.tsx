import { useEffect, useRef, useState } from 'react';
import { MessageSquare, Send, X } from 'lucide-react';
import type { ChatMessage } from '../types.ts';

interface FloatingChatProps {
  visible: boolean;
  messages: ChatMessage[];
  chatBusy: boolean;
  onSendMessage: (question: string) => void;
}

export function FloatingChat({
  visible,
  messages,
  chatBusy,
  onSendMessage,
}: FloatingChatProps) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const listRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!visible) {
      setOpen(false);
    }
  }, [visible]);

  useEffect(() => {
    if (open && listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [open, messages, chatBusy]);

  if (!visible) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || chatBusy) return;
    setInput('');
    onSendMessage(trimmed);
  };

  return (
    <>
      {/* Fixed Bottom-Right Floating Button — perfectly round, zero shifting or square edges */}
      <button
        type="button"
        data-tour="assistant-trigger"
        onClick={() => setOpen((prev) => !prev)}
        aria-label={open ? 'Cerrar Asistente Rápido' : 'Abrir Asistente Rápido'}
        aria-expanded={open}
        className="fixed bottom-6 right-6 z-50 flex items-center gap-2.5 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 px-5 py-3.5 text-sm font-semibold text-white shadow-xl transition-transform duration-200 hover:scale-105 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-offset-2 whitespace-nowrap cursor-pointer"
      >
        {open ? (
          <>
            <X className="h-4 w-4 shrink-0" />
            <span>Cerrar Asistente</span>
          </>
        ) : (
          <>
            <MessageSquare className="h-4 w-4 shrink-0" />
            <span>Asistente Rápido</span>
          </>
        )}
      </button>

      {/* Modern Floating Panel */}
      {open && (
        <div
          className="fixed bottom-24 right-6 z-50 flex h-[520px] max-h-[calc(100vh-8rem)] w-[400px] max-w-[calc(100vw-3rem)] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl animate-panel-in"
          role="dialog"
          aria-label="Asistente Rápido"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-800 bg-[#0F172A] px-4 py-3 text-white">
            <div className="flex items-center gap-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-r from-blue-600 to-indigo-600">
                <MessageSquare className="h-3.5 w-3.5 text-white" />
              </div>
              <div>
                <div className="text-[13px] font-semibold leading-tight">
                  Asistente Rápido
                </div>
                <div className="text-[11px] text-slate-400">
                  Contexto del escenario activo
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Cerrar asistente rápido"
              className="rounded-lg p-1.5 text-slate-300 transition-colors hover:bg-slate-800 hover:text-white cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Chat History */}
          <div
            ref={listRef}
            className="flex-1 space-y-3 overflow-y-auto bg-slate-50/70 p-4"
          >
            {messages.map((msg) => {
              const isUser = msg.role === 'user';
              const isAssistant = msg.role === 'assistant';
              const label = isUser ? 'Tú' : isAssistant ? 'Gemini' : 'Sistema';

              return (
                <div
                  key={msg.id}
                  className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 shadow-xs ${
                      isUser
                        ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white'
                        : isAssistant
                          ? 'border border-slate-200 bg-white text-slate-800'
                          : 'border border-slate-200 bg-slate-100 text-slate-600'
                    }`}
                  >
                    <div
                      className={`text-[10px] font-semibold tracking-wide ${
                        isUser ? 'text-blue-100' : 'text-slate-400'
                      }`}
                    >
                      {label}
                    </div>
                    <div className="mt-0.5 whitespace-pre-wrap text-[12.5px] leading-relaxed">
                      {msg.text}
                    </div>
                  </div>
                </div>
              );
            })}

            {chatBusy && (
              <div className="flex justify-start">
                <div className="rounded-2xl border border-slate-200 bg-white px-4 py-2.5 shadow-xs">
                  <div className="text-[10px] font-semibold text-slate-400">
                    Gemini
                  </div>
                  <div className="mt-1 flex items-center gap-1.5 text-[12px] text-slate-500">
                    <span className="inline-flex items-center gap-1 text-blue-600">
                      <span className="animate-dot-1">●</span>
                      <span className="animate-dot-2">●</span>
                      <span className="animate-dot-3">●</span>
                    </span>
                    <span>Analizando escenario</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input Bar */}
          <form
            onSubmit={handleSubmit}
            className="flex items-center gap-2 border-t border-slate-200 bg-white p-3"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Pregunta sobre este escenario..."
              className="h-10 flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3.5 text-[12.5px] text-slate-900 placeholder:text-slate-400 transition-colors focus:border-blue-500 focus:bg-white focus:outline-none"
            />
            <button
              type="submit"
              disabled={chatBusy || !input.trim()}
              className="inline-flex h-10 items-center gap-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-3.5 text-[12.5px] font-semibold text-white shadow-sm transition-all hover:from-blue-700 hover:to-indigo-700 active:scale-95 disabled:opacity-45 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            >
              <Send className="h-3.5 w-3.5" />
              <span>{chatBusy ? '…' : 'Enviar'}</span>
            </button>
          </form>
        </div>
      )}
    </>
  );
}
