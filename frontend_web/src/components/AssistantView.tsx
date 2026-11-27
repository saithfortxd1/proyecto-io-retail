import { useEffect, useRef, useState } from 'react';
import { Send } from 'lucide-react';
import { QUICK_QUESTIONS } from '../data/defaults.ts';
import type { ChatMessage } from '../types.ts';

interface AssistantViewProps {
  messages: ChatMessage[];
  chatBusy: boolean;
  quickQuestionsHidden: boolean;
  statusText: string;
  onSendMessage: (question: string) => void;
}

export function AssistantView({
  messages,
  chatBusy,
  quickQuestionsHidden,
  statusText,
  onSendMessage,
}: AssistantViewProps) {
  const [input, setInput] = useState('');
  const listRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages, chatBusy]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || chatBusy) return;
    setInput('');
    onSendMessage(trimmed);
  };

  return (
    <div className="flex h-full flex-col gap-4 pb-4">
      <div>
        <h1 className="text-[24px] font-bold tracking-tight text-slate-900">
          Asistente IA (Gemini)
        </h1>
        <p className="mt-1 text-[13.5px] text-slate-500">
          Respuestas basadas en el informe técnico y en el escenario visible actualmente
        </p>
      </div>

      <div className="flex min-h-[520px] flex-1 flex-col rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm">
        <div className="mb-3 text-[12px] text-slate-500">{statusText}</div>

        {/* Chat History */}
        <div
          ref={listRef}
          className="flex-1 space-y-3 overflow-y-auto rounded-xl bg-slate-50/80 p-4"
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
                  className={`max-w-[82%] rounded-2xl px-4 py-3 shadow-xs ${
                    isUser
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white'
                      : isAssistant
                        ? 'border border-slate-200 bg-white text-slate-800'
                        : 'border border-slate-200 bg-slate-100 text-slate-600'
                  }`}
                >
                  <div
                    className={`text-[11px] font-semibold ${
                      isUser ? 'text-blue-100' : 'text-slate-400'
                    }`}
                  >
                    {label}
                  </div>
                  <div className="mt-1 whitespace-pre-wrap text-[13.5px] leading-relaxed">
                    {msg.text}
                  </div>
                </div>
              </div>
            );
          })}

          {chatBusy && (
            <div className="flex justify-start">
              <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-xs">
                <div className="text-[11px] font-semibold text-slate-400">
                  Gemini
                </div>
                <div className="mt-1 flex items-center gap-2 text-[13px] text-slate-500">
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

        {/* Quick Questions */}
        {!quickQuestionsHidden && (
          <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
            {QUICK_QUESTIONS.map((q) => (
              <button
                key={q}
                type="button"
                disabled={chatBusy}
                onClick={() => onSendMessage(q)}
                className="h-10 rounded-xl border border-blue-200/80 bg-blue-50/70 px-3.5 text-left text-[12.5px] font-semibold text-blue-700 transition-colors hover:bg-blue-100/80 disabled:opacity-50 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <form onSubmit={handleSubmit} className="mt-3 flex gap-2.5">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Escribe una pregunta sobre resultados o uso del software…"
            className="h-11 flex-1 rounded-xl border border-slate-200 bg-slate-50 px-4 text-[13.5px] text-slate-900 placeholder:text-slate-400 transition-colors focus:border-blue-500 focus:bg-white focus:outline-none"
          />
          <button
            type="submit"
            disabled={chatBusy || !input.trim()}
            className="inline-flex h-11 items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-5 text-[13px] font-semibold text-white shadow-sm transition-all hover:from-blue-700 hover:to-indigo-700 active:scale-[0.98] disabled:opacity-45 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          >
            <Send className="h-4 w-4" />
            <span>{chatBusy ? 'Consultando…' : 'Enviar'}</span>
          </button>
        </form>
      </div>
    </div>
  );
}
