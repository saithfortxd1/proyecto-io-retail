import {
  CAPACIDADES_DEFAULT,
  COSTOS_ENVIO_DEFAULT,
  COSTOS_FIJOS_DEFAULT,
  COSTO_BASELINE_DEFAULT,
  DEMANDA_DEFAULT,
  MAX_CENTROS_DEFAULT,
  UBICACIONES_DEFAULT,
  ZONAS_DEFAULT,
} from '../data/defaults.ts';
import type {
  AssignmentRow,
  OptimizationResult,
  ScenarioParameters,
} from '../types.ts';

export interface SolverInput {
  costos_fijos?: number[];
  capacidades?: number[];
  demandas?: number[];
  costos_envio?: number[][];
  max_centros?: number;
  zonas?: string[];
  ubicaciones?: string[];
  costo_baseline?: number;
}

interface Edge {
  to: number;
  rev: number;
  cap: number;
  cost: number;
  origCap: number;
}

const EPS = 1e-9;

function solveMinCostFlow(
  selectedFacilities: number[],
  capacidades: number[],
  demandas: number[],
  costosEnvio: number[][]
): { totalTransportCost: number; flows: number[][] } | null {
  const kCount = selectedFacilities.length;
  const zCount = demandas.length;
  const totalDemand = demandas.reduce((acc, v) => acc + v, 0);

  if (totalDemand <= EPS) {
    return {
      totalTransportCost: 0,
      flows: selectedFacilities.map(() => new Array<number>(zCount).fill(0)),
    };
  }

  const SRC = 0;
  const FAC_OFFSET = 1;
  const ZONE_OFFSET = 1 + kCount;
  const SNK = 1 + kCount + zCount;
  const nodeCount = SNK + 1;

  const graph: Edge[][] = Array.from({ length: nodeCount }, () => []);

  const addEdge = (from: number, to: number, cap: number, cost: number): number => {
    const fwdIdx = graph[from].length;
    const revIdx = graph[to].length;
    graph[from].push({ to, rev: revIdx, cap, cost, origCap: cap });
    graph[to].push({ to: from, rev: fwdIdx, cap: 0, cost: -cost, origCap: 0 });
    return fwdIdx;
  };

  for (let fi = 0; fi < kCount; fi++) {
    const origFacIdx = selectedFacilities[fi];
    addEdge(SRC, FAC_OFFSET + fi, capacidades[origFacIdx], 0);
  }

  const facZoneEdgeIndices: number[][] = Array.from({ length: kCount }, () => []);
  for (let fi = 0; fi < kCount; fi++) {
    const origFacIdx = selectedFacilities[fi];
    for (let zj = 0; zj < zCount; zj++) {
      const idx = addEdge(
        FAC_OFFSET + fi,
        ZONE_OFFSET + zj,
        totalDemand,
        costosEnvio[origFacIdx][zj]
      );
      facZoneEdgeIndices[fi].push(idx);
    }
  }

  for (let zj = 0; zj < zCount; zj++) {
    if (demandas[zj] > 0) {
      addEdge(ZONE_OFFSET + zj, SNK, demandas[zj], 0);
    }
  }

  let flow = 0;
  let totalCost = 0;

  while (flow < totalDemand - EPS) {
    const dist = new Array<number>(nodeCount).fill(Infinity);
    const parentNode = new Array<number>(nodeCount).fill(-1);
    const parentEdge = new Array<number>(nodeCount).fill(-1);
    const inQueue = new Array<boolean>(nodeCount).fill(false);
    const queue: number[] = [];

    dist[SRC] = 0;
    queue.push(SRC);
    inQueue[SRC] = true;

    for (let head = 0; head < queue.length; head++) {
      const u = queue[head];
      inQueue[u] = false;

      for (let ei = 0; ei < graph[u].length; ei++) {
        const edge = graph[u][ei];
        if (edge.cap > EPS && dist[u] + edge.cost < dist[edge.to] - EPS) {
          dist[edge.to] = dist[u] + edge.cost;
          parentNode[edge.to] = u;
          parentEdge[edge.to] = ei;
          if (!inQueue[edge.to]) {
            queue.push(edge.to);
            inQueue[edge.to] = true;
          }
        }
      }
    }

    if (!Number.isFinite(dist[SNK])) {
      return null;
    }

    let push = totalDemand - flow;
    for (let v = SNK; v !== SRC; v = parentNode[v]) {
      const u = parentNode[v];
      const ei = parentEdge[v];
      push = Math.min(push, graph[u][ei].cap);
    }

    for (let v = SNK; v !== SRC; v = parentNode[v]) {
      const u = parentNode[v];
      const ei = parentEdge[v];
      const edge = graph[u][ei];
      edge.cap -= push;
      graph[v][edge.rev].cap += push;
    }

    flow += push;
    totalCost += push * dist[SNK];
  }

  const flows = facZoneEdgeIndices.map((row, fi) =>
    row.map((edgeIdx) => {
      const edge = graph[FAC_OFFSET + fi][edgeIdx];
      return Math.max(0, edge.origCap - edge.cap);
    })
  );

  return { totalTransportCost: totalCost, flows };
}

export function resolverModelo(input: SolverInput = {}): OptimizationResult {
  const zonas = input.zonas ?? ZONAS_DEFAULT;
  const ubicaciones = input.ubicaciones ?? UBICACIONES_DEFAULT;
  const costos_fijos = input.costos_fijos ?? COSTOS_FIJOS_DEFAULT;
  const capacidades = input.capacidades ?? CAPACIDADES_DEFAULT;
  const demandas = input.demandas ?? DEMANDA_DEFAULT;
  const costos_envio = input.costos_envio ?? COSTOS_ENVIO_DEFAULT;
  const max_centros = input.max_centros ?? MAX_CENTROS_DEFAULT;
  const costo_baseline = input.costo_baseline ?? COSTO_BASELINE_DEFAULT;

  const nUbicaciones = ubicaciones.length;
  const nZonas = zonas.length;

  const emptyError = (estado: 'Error' | 'Infeasible', mensaje: string): OptimizationResult => ({
    estado,
    mensaje,
    centros_abiertos: [],
    costo_fijo: 0,
    costo_variable: 0,
    costo_total: 0,
    ahorro: 0,
    porcentaje_ahorro: 0,
    asignaciones: [],
  });

  if (costos_fijos.length !== nUbicaciones) {
    return emptyError('Error', `costos_fijos debe tener ${nUbicaciones} elementos`);
  }
  if (capacidades.length !== nUbicaciones) {
    return emptyError('Error', `capacidades debe tener ${nUbicaciones} elementos`);
  }
  if (demandas.length !== nZonas) {
    return emptyError('Error', `demandas debe tener ${nZonas} elementos`);
  }
  if (costos_envio.length !== nUbicaciones) {
    return emptyError('Error', `costos_envio debe tener ${nUbicaciones} filas`);
  }
  for (let i = 0; i < costos_envio.length; i++) {
    if (costos_envio[i].length !== nZonas) {
      return emptyError('Error', `costos_envio fila ${i} debe tener ${nZonas} columnas`);
    }
  }
  if (max_centros > nUbicaciones || max_centros < 1) {
    return emptyError('Error', `max_centros debe estar entre 1 y ${nUbicaciones}`);
  }
  if (costos_fijos.some((c) => !Number.isFinite(c) || c < 0)) {
    return emptyError('Error', 'Los costos fijos no pueden ser negativos');
  }
  if (capacidades.some((c) => !Number.isFinite(c) || c <= 0)) {
    return emptyError('Error', 'Las capacidades deben ser mayores que cero');
  }
  if (demandas.some((d) => !Number.isFinite(d) || d < 0)) {
    return emptyError('Error', 'Las demandas no pueden ser negativas');
  }
  if (!Number.isFinite(costo_baseline) || costo_baseline <= 0) {
    return emptyError('Error', 'El costo baseline debe ser mayor que cero');
  }

  const totalDemand = demandas.reduce((acc, d) => acc + d, 0);
  const capacidadesOrdenadas = [...capacidades].sort((a, b) => b - a);
  const capacidadMaxDisponible = capacidadesOrdenadas
    .slice(0, max_centros)
    .reduce((acc, c) => acc + c, 0);

  if (totalDemand > capacidadMaxDisponible + EPS) {
    return emptyError(
      'Infeasible',
      `Demanda total (${totalDemand.toLocaleString('en-US')}) excede capacidad máxima posible con ${max_centros} centros (${capacidadMaxDisponible.toLocaleString('en-US')})`
    );
  }

  let bestTotalCost = Infinity;
  let bestFixedCost = 0;
  let bestVarCost = 0;
  let bestSubset: number[] | null = null;
  let bestFlows: number[][] | null = null;

  const currentSubset: number[] = [];

  const search = (startIdx: number, currentFixed: number, currentCap: number) => {
    if (currentSubset.length > 0) {
      if (currentFixed < bestTotalCost - EPS && currentCap + EPS >= totalDemand) {
        const res = solveMinCostFlow(currentSubset, capacidades, demandas, costos_envio);
        if (res) {
          const total = currentFixed + res.totalTransportCost;
          if (total < bestTotalCost - EPS) {
            bestTotalCost = total;
            bestFixedCost = currentFixed;
            bestVarCost = res.totalTransportCost;
            bestSubset = [...currentSubset];
            bestFlows = res.flows;
          }
        }
      }
    }

    if (currentSubset.length >= max_centros) {
      return;
    }

    for (let i = startIdx; i < nUbicaciones; i++) {
      const nextFixed = currentFixed + costos_fijos[i];
      if (nextFixed >= bestTotalCost - EPS) {
        continue;
      }
      currentSubset.push(i);
      search(i + 1, nextFixed, currentCap + capacidades[i]);
      currentSubset.pop();
    }
  };

  search(0, 0, 0);

  if (!bestSubset || !bestFlows) {
    return emptyError('Infeasible', 'No se encontró una asignación factible para los parámetros actuales.');
  }

  const subset = bestSubset as number[];
  const flows = bestFlows as number[][];
  const centros_abiertos = subset.map((idx) => ubicaciones[idx]);
  const asignaciones: AssignmentRow[] = [];

  for (let fi = 0; fi < subset.length; fi++) {
    const uIdx = subset[fi];
    for (let zj = 0; zj < nZonas; zj++) {
      const qty = Math.round(flows[fi][zj] * 1e6) / 1e6;
      if (qty > EPS) {
        asignaciones.push({
          Ubicacion: ubicaciones[uIdx],
          Zona: zonas[zj],
          Cantidad_Enviada: qty,
        });
      }
    }
  }

  const ahorro = costo_baseline - bestTotalCost;
  const porcentaje_ahorro = costo_baseline > 0 ? (ahorro / costo_baseline) * 100 : 0;

  return {
    estado: 'Optimal',
    centros_abiertos,
    costo_fijo: bestFixedCost,
    costo_variable: bestVarCost,
    costo_total: bestTotalCost,
    ahorro,
    porcentaje_ahorro,
    asignaciones,
    mensaje: 'Optimización completada exitosamente',
  };
}

export function isPyWebViewAvailable(): boolean {
  return (
    typeof window !== 'undefined' &&
    typeof window.pywebview?.api?.resolver_escenario === 'function'
  );
}

export async function resolverEscenarioConPuente(
  params: ScenarioParameters
): Promise<{ result: OptimizationResult; engine: 'pywebview' | 'typescript' }> {
  const payload = {
    costos_fijos: [...params.costos_fijos],
    capacidades: [...params.capacidades],
    demandas: [...params.demandas],
    costos_envio: COSTOS_ENVIO_DEFAULT.map((row) => [...row]),
    tarifas: COSTOS_ENVIO_DEFAULT.map((row) => [...row]),
    max_centros: params.max_centros,
    costo_baseline: params.costo_baseline,
    zonas: [...ZONAS_DEFAULT],
    ubicaciones: [...UBICACIONES_DEFAULT],
  };

  if (isPyWebViewAvailable()) {
    const pyResolver = window.pywebview!.api!.resolver_escenario!;
    const raw = await pyResolver(payload);
    const parsed = (typeof raw === 'string' ? JSON.parse(raw) : raw) as OptimizationResult;
    if (!parsed || typeof parsed.estado !== 'string') {
      throw new Error('Respuesta inválida del solver Python/PuLP.');
    }
    return {
      result: {
        ...parsed,
        centros_abiertos: Array.isArray(parsed.centros_abiertos)
          ? parsed.centros_abiertos
          : [],
        asignaciones: Array.isArray(parsed.asignaciones) ? parsed.asignaciones : [],
        costo_fijo: Number(parsed.costo_fijo ?? 0),
        costo_variable: Number(parsed.costo_variable ?? 0),
        costo_total: Number(parsed.costo_total ?? 0),
        ahorro: Number(parsed.ahorro ?? 0),
        porcentaje_ahorro: Number(parsed.porcentaje_ahorro ?? 0),
        mensaje: parsed.mensaje ?? '',
      },
      engine: 'pywebview',
    };
  }

  return {
    result: resolverModelo(payload),
    engine: 'typescript',
  };
}
