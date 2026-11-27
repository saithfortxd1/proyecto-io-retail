import 'dotenv/config';
import express from 'express';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { GoogleGenAI, Type, type Content } from '@google/genai';
import {
  AI_SYSTEM_INSTRUCTION,
  COSTOS_ENVIO_DEFAULT,
  DEFAULT_PARAMETERS,
  UBICACIONES_DEFAULT,
  ZONAS_DEFAULT,
} from './src/data/defaults.ts';
import { resolverModelo } from './src/lib/mipSolver.ts';
import type {
  ChatTurn,
  OptimizationResult,
  ScenarioParameters,
} from './src/types.ts';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = 3000;
const GEMINI_MODEL = 'gemini-3.5-flash-lite';
const GEMINI_FALLBACK_MODEL = 'gemini-3.8-flash';

function isModelNotFound(error: unknown): boolean {
  if (typeof error === 'object' && error !== null) {
    const details = error as {
      code?: unknown;
      status?: unknown;
      statusCode?: unknown;
      response?: { status?: unknown; statusCode?: unknown };
    };
    const statuses = [
      details.code,
      details.status,
      details.statusCode,
      details.response?.status,
      details.response?.statusCode,
    ];
    if (statuses.some((status) => status === 404 || String(status).toUpperCase() === 'NOT_FOUND')) {
      return true;
    }
  }
  const message = error instanceof Error ? error.message.toUpperCase() : String(error).toUpperCase();
  return message.includes('404') && (message.includes('NOT_FOUND') || message.includes('NOT FOUND'));
}

async function generateContentWithFallback<T>(
  generate: (model: string) => Promise<T>
): Promise<{ response: T; model: string }> {
  try {
    return { response: await generate(GEMINI_MODEL), model: GEMINI_MODEL };
  } catch (error) {
    if (!isModelNotFound(error)) throw error;
    return {
      response: await generate(GEMINI_FALLBACK_MODEL),
      model: GEMINI_FALLBACK_MODEL,
    };
  }
}

function sanitizeAssistantResponse(answer: string): string {
  return answer
    .replace(/\*{1,2}|#+/g, '')
    .replace(/```/g, '')
    .replace(/`/g, '')
    .trim();
}

function getGeminiApiKey(): string {
  return (process.env.GEMINI_API_KEY || process.env.API_KEY || '').trim();
}

function createGeminiClient(apiKey: string) {
  return new GoogleGenAI({
    apiKey,
    httpOptions: {
      headers: {
        'User-Agent': 'aistudio-build',
      },
    },
  });
}

async function startServer() {
  const app = express();
  app.use(express.json({ limit: '1mb' }));

  app.get('/api/health', (_req, res) => {
    res.json({ ok: true });
  });

  app.get('/api/assistant/status', (_req, res) => {
    const apiKey = getGeminiApiKey();
    res.json({
      configured: Boolean(apiKey),
      model: GEMINI_MODEL,
    });
  });

  app.post('/api/optimize', (req, res) => {
    try {
      const result = resolverModelo(req.body || {});
      res.json(result);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Error al resolver el modelo.';
      res.status(400).json({ estado: 'Error', mensaje: message });
    }
  });

  app.post('/api/assistant', async (req, res) => {
    const apiKey = getGeminiApiKey();
    if (!apiKey) {
      res.status(503).json({
        error:
          'Gemini no está configurado en el servidor. Agrega GEMINI_API_KEY en los Secretos/Variables de entorno de AI Studio (o en un archivo .env si lo ejecutas en tu PC); la optimización local sigue disponible.',
      });
      return;
    }

    const { question, context, priorTurns } = req.body as {
      question?: string;
      context?: string;
      priorTurns?: ChatTurn[];
    };

    if (!question || typeof question !== 'string' || !question.trim()) {
      res.status(400).json({ error: 'La pregunta es obligatoria.' });
      return;
    }

    try {
      const ai = createGeminiClient(apiKey);
      const history = Array.isArray(priorTurns) ? priorTurns.slice(-12) : [];
      const contents: Content[] = history
        .filter(
          (turn): turn is ChatTurn =>
            Boolean(turn) &&
            (turn.role === 'user' || turn.role === 'model') &&
            typeof turn.text === 'string'
        )
        .map((turn) => ({
          role: turn.role,
          parts: [{ text: turn.text }],
        }));

      const userPrompt = context
        ? `${question.trim()}\n\n${context}`
        : question.trim();
      contents.push({
        role: 'user',
        parts: [{ text: userPrompt }],
      });

      const { response, model } = await generateContentWithFallback((model) =>
        ai.models.generateContent({
          model,
          contents,
          config: {
            systemInstruction: AI_SYSTEM_INSTRUCTION,
          },
        })
      );

      const rawText = response.text;
      if (!rawText) {
        res.status(502).json({ error: 'Gemini devolvió una respuesta vacía.' });
        return;
      }

      res.json({
        answer: sanitizeAssistantResponse(rawText),
        model,
      });
    } catch (error) {
      const rawMessage =
        error instanceof Error ? error.message : 'Error consultando Gemini.';
      const safeMessage = rawMessage.replaceAll(apiKey, '[clave oculta]');
      res.status(502).json({ error: safeMessage });
    }
  });

  app.post('/api/assistant/tutorial', async (_req, res) => {
    const apiKey = getGeminiApiKey();
    if (!apiKey) {
      res.status(503).json({
        error:
          'Gemini no está configurado en el servidor. Agrega GEMINI_API_KEY en Secretos/Variables de entorno o en .env.',
      });
      return;
    }

    try {
      const ai = createGeminiClient(apiKey);
      const { response, model } = await generateContentWithFallback((model) =>
        ai.models.generateContent({
          model,
          contents:
          'Genera un recorrido guiado tipo spotlight en 5 pasos MUY breves y directos en español para MIP Retail Optimizer Enterprise. Cada "summary" debe tener máximo 18 palabras y cada "tip" máximo 12 palabras (sin texto largo). Cubre en orden: (1) Escenario y carga CSV/Excel en Dashboard, (2) Botón Ejecutar Optimización MIP ($243,000 USD vs $182,500 USD, ahorro $60,500 USD / 24.90%), (3) Gráficas e Informe IA debajo de cada gráfica, (4) Exportar PDF con mapa y Matriz de Rutas, (5) Asistente Rápido IA y Manual. Sin Markdown.',
          config: {
            systemInstruction: AI_SYSTEM_INSTRUCTION,
            responseMimeType: 'application/json',
            responseSchema: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  section: { type: Type.STRING },
                  title: { type: Type.STRING },
                  summary: { type: Type.STRING },
                  tip: { type: Type.STRING },
                },
                required: ['section', 'title', 'summary', 'tip'],
              },
            },
          },
        })
      );

      const parsed = JSON.parse((response.text ?? '[]').trim()) as Array<{
        section: string;
        title: string;
        summary: string;
        tip: string;
      }>;

      const cleanSteps = parsed.slice(0, 5).map((item, idx) => ({
        id: `gemini-step-${idx + 1}`,
        section: sanitizeAssistantResponse(item.section),
        title: sanitizeAssistantResponse(item.title),
        summary: sanitizeAssistantResponse(item.summary),
        tip: sanitizeAssistantResponse(item.tip),
      }));

      res.json({ steps: cleanSteps, model });
    } catch (error) {
      const rawMessage =
        error instanceof Error ? error.message : 'Error generando tutorial con Gemini.';
      const safeMessage = rawMessage.replaceAll(apiKey, '[clave oculta]');
      res.status(502).json({ error: safeMessage });
    }
  });

  app.post('/api/assistant/chart-impact', async (req, res) => {
    const apiKey = getGeminiApiKey();
    if (!apiKey) {
      res.status(503).json({
        error:
          'Gemini no está configurado en el servidor. Agrega GEMINI_API_KEY en Secretos/Variables de entorno o en .env para generar el informe automático.',
      });
      return;
    }

    const {
      previousParams,
      previousResult,
      currentParams,
      currentResult,
    } = req.body as {
      previousParams?: ScenarioParameters;
      previousResult?: OptimizationResult | null;
      currentParams?: ScenarioParameters;
      currentResult?: OptimizationResult;
    };

    if (!currentParams || !currentResult) {
      res.status(400).json({ error: 'Faltan parámetros o resultados del escenario.' });
      return;
    }

    const refParams = previousParams ?? DEFAULT_PARAMETERS;
    const refResult = previousResult ?? resolverModelo(DEFAULT_PARAMETERS);

    const payloadSummary = {
      centros: UBICACIONES_DEFAULT,
      zonas: ZONAS_DEFAULT,
      tarifas_fijas_envio: COSTOS_ENVIO_DEFAULT,
      escenario_anterior: {
        parametros: refParams,
        resultado: {
          centros_abiertos: refResult.centros_abiertos,
          costo_fijo: refResult.costo_fijo,
          costo_variable: refResult.costo_variable,
          costo_total: refResult.costo_total,
          ahorro: refResult.ahorro,
          porcentaje_ahorro: refResult.porcentaje_ahorro,
        },
      },
      escenario_nuevo: {
        parametros: currentParams,
        resultado: {
          centros_abiertos: currentResult.centros_abiertos,
          costo_fijo: currentResult.costo_fijo,
          costo_variable: currentResult.costo_variable,
          costo_total: currentResult.costo_total,
          ahorro: currentResult.ahorro,
          porcentaje_ahorro: currentResult.porcentaje_ahorro,
          asignaciones: currentResult.asignaciones,
        },
      },
    };

    try {
      const ai = createGeminiClient(apiKey);
      const { response, model } = await generateContentWithFallback((model) =>
        ai.models.generateContent({
          model,
          contents: `Analiza los cambios entre el escenario anterior y el nuevo escenario optimizado y genera dos informes claros y concisos para mostrar debajo de cada gráfica en el Dashboard.
1) costImpactReport (debajo de la gráfica Comparativa Baseline vs. Optimizado): explica en 2-3 oraciones cómo afectaron los cambios de parámetros al costo fijo, al costo de transporte, al costo total óptimo y al ahorro mensual/anual frente al baseline, citando las cifras exactas con signo $, comas, puntos decimales y %.
2) capacityImpactReport (debajo de la gráfica Utilización de Capacidad L1–L4): explica en 2-3 oraciones qué centros quedaron abiertos o cerrados, cómo cambió el porcentaje de utilización de L1–L4 y qué implicación operativa tiene para que cualquier usuario entienda qué está pasando.
PROHIBIDO usar Markdown (**, #, \`\`).

Datos exactos del escenario:
${JSON.stringify(payloadSummary)}`,
          config: {
            systemInstruction: AI_SYSTEM_INSTRUCTION,
            responseMimeType: 'application/json',
            responseSchema: {
              type: Type.OBJECT,
              properties: {
                costImpactReport: { type: Type.STRING },
                capacityImpactReport: { type: Type.STRING },
              },
              required: ['costImpactReport', 'capacityImpactReport'],
            },
          },
        })
      );

      const parsed = JSON.parse((response.text ?? '{}').trim()) as {
        costImpactReport?: string;
        capacityImpactReport?: string;
      };

      res.json({
        costImpactReport: sanitizeAssistantResponse(parsed.costImpactReport ?? ''),
        capacityImpactReport: sanitizeAssistantResponse(parsed.capacityImpactReport ?? ''),
        model,
      });
    } catch (error) {
      const rawMessage =
        error instanceof Error
          ? error.message
          : 'Error generando el informe de impacto con Gemini.';
      const safeMessage = rawMessage.replaceAll(apiKey, '[clave oculta]');
      res.status(502).json({ error: safeMessage });
    }
  });

  if (process.env.NODE_ENV === 'production') {
    const distDir = path.resolve(__dirname, 'dist');
    app.use(express.static(distDir));
    app.get('/{*splat}', (_req, res) => {
      res.sendFile(path.join(distDir, 'index.html'));
    });
  } else {
    app.get('/@vite/client', (_req, res) => {
      res.type('application/javascript').send(`
const sheetsMap = new Map();
export function updateStyle(id, content) {
  let style = sheetsMap.get(id);
  if (!style) {
    style = document.createElement('style');
    style.setAttribute('type', 'text/css');
    style.setAttribute('data-vite-dev-id', id);
    style.textContent = content;
    document.head.appendChild(style);
    sheetsMap.set(id, style);
  } else if (style.textContent !== content) {
    style.textContent = content;
  }
}
export function removeStyle(id) {
  const style = sheetsMap.get(id);
  if (style && style.parentNode) {
    style.parentNode.removeChild(style);
    sheetsMap.delete(id);
  }
}
export function createHotContext() {
  return {
    data: {},
    accept() {},
    dispose() {},
    prune() {},
    invalidate() {},
    on() {},
    off() {},
    send() {},
  };
}
export function injectQuery(url, queryToInject) {
  if (url[0] !== '.' && url[0] !== '/') return url;
  const pathname = url.replace(/[?#].*$/, '');
  const { search, hash } = new URL(url, 'http://vite.dev');
  return \`\${pathname}?\${queryToInject}\${search ? '&' + search.slice(1) : ''}\${hash || ''}\`;
}
export class ErrorOverlay extends HTMLElement {}
`);
    });
    const { createServer: createViteServer } = await import('vite');
    const vite = await createViteServer({
      server: { middlewareMode: true, hmr: false },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`MIP Retail Optimizer server running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
