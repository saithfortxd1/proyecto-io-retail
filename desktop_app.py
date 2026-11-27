"""Aplicación de escritorio PyWebView para MIP Retail Optimizer."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import webview
from dotenv import load_dotenv

from optimizacion import resolver_modelo


MODEL_NAME = "gemini-2.5-flash"


def resource_path(*parts: str) -> Path:
    """Resuelve recursos tanto en desarrollo como dentro del bundle onefile."""
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return bundle_root.joinpath(*parts)


def _load_api_key() -> str | None:
    candidates = [resource_path(".env"), Path(__file__).resolve().parent / ".env"]
    for env_path in candidates:
        if env_path.is_file():
            load_dotenv(env_path, override=False)
    return os.getenv("GEMINI_API_KEY") or None


class Api:
    """Métodos JavaScript expuestos a la interfaz React por PyWebView."""

    def __init__(self) -> None:
        self._api_key = _load_api_key()
        self._gemini_client = None

    def resolver_escenario(self, params: dict[str, Any]) -> dict[str, Any]:
        """Resuelve un escenario y devuelve el contrato OptimizationResult."""
        if not isinstance(params, dict):
            return resolver_modelo()

        costos_envio = params.get("costos_envio") or params.get("tarifas")
        return resolver_modelo(
            costos_fijos=params.get("costos_fijos"),
            capacidades=params.get("capacidades"),
            demandas=params.get("demandas"),
            costos_envio=costos_envio,
            max_centros=params.get("max_centros"),
            zonas=params.get("zonas"),
            ubicaciones=params.get("ubicaciones"),
            costo_baseline=params.get("costo_baseline"),
        )

    def estado_asistente(self) -> dict[str, Any]:
        return {"configured": bool(self._api_key), "model": MODEL_NAME}

    def _client(self):
        if not self._api_key:
            raise RuntimeError(
                "Gemini no está configurado. Define GEMINI_API_KEY en .env o en el entorno."
            )
        if self._gemini_client is None:
            from google import genai

            self._gemini_client = genai.Client(api_key=self._api_key)
        return self._gemini_client

    def _generate_text(self, prompt: str, *, json_response: bool = False) -> str:
        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=0.3,
            response_mime_type="application/json" if json_response else "text/plain",
        )
        response = self._client().models.generate_content(
            model=MODEL_NAME, contents=prompt, config=config
        )
        answer = (response.text or "").strip()
        if not answer:
            raise RuntimeError("Gemini devolvió una respuesta vacía.")
        return answer

    def consultar_asistente(self, payload: dict[str, Any]) -> dict[str, str]:
        question = str(payload.get("question", "")).strip()
        if not question:
            raise ValueError("La pregunta no puede estar vacía.")
        turns = payload.get("priorTurns") or []
        history = "\n".join(
            f"{str(turn.get('role', 'user')).upper()}: {turn.get('text', '')}"
            for turn in turns[-12:]
            if isinstance(turn, dict)
        )
        prompt = (
            "Eres el asistente integrado de MIP Retail Optimizer Enterprise. "
            "Responde en español, con claridad y basándote en el contexto proporcionado. "
            "No inventes resultados ni afirmes que una simulación se ejecutó.\n\n"
            f"CONTEXTO ACTUAL:\n{payload.get('context', '')}\n\n"
            f"CONVERSACIÓN RECIENTE:\n{history}\n\nPREGUNTA:\n{question}"
        )
        return {"answer": self._generate_text(prompt), "model": MODEL_NAME}

    def generar_tutorial(self) -> dict[str, Any]:
        prompt = (
            "Crea un tutorial breve de cinco pasos en español para una aplicación de "
            "optimización logística. Devuelve exclusivamente JSON con la forma "
            '{"steps":[{"id":"...","section":"...","title":"...",'
            '"summary":"...","tip":"..."}]}. Explica dashboard, parámetros, '
            "ejecución PuLP, matriz y asistente."
        )
        return self._parse_json_object(self._generate_text(prompt, json_response=True))

    def analizar_impacto_graficos(self, payload: dict[str, Any]) -> dict[str, str]:
        prompt = (
            "Analiza en español el cambio entre el escenario previo y el actual de "
            "una red de distribución. Usa solo los datos incluidos y redacta dos "
            "resúmenes breves: impacto en costos e impacto en capacidad. Devuelve "
            'exclusivamente JSON con claves "costImpactReport" y "capacityImpactReport".\n'
            + json.dumps(payload, ensure_ascii=False, allow_nan=False)
        )
        result = self._parse_json_object(
            self._generate_text(prompt, json_response=True)
        )
        if not result.get("costImpactReport") or not result.get("capacityImpactReport"):
            raise RuntimeError("Gemini no devolvió los dos informes de impacto esperados.")
        return {
            "costImpactReport": str(result["costImpactReport"]),
            "capacityImpactReport": str(result["capacityImpactReport"]),
        }

    @staticmethod
    def _parse_json_object(text: str) -> dict[str, Any]:
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            start, end = text.find("{"), text.rfind("}")
            if start < 0 or end < start:
                raise RuntimeError("Gemini devolvió JSON inválido.")
            result = json.loads(text[start : end + 1])
        if not isinstance(result, dict):
            raise RuntimeError("Gemini devolvió una respuesta JSON inesperada.")
        return result


def main() -> None:
    index_path = resource_path("frontend_web", "dist", "index.html")
    if not index_path.is_file():
        raise FileNotFoundError(f"No se encontró la interfaz web: {index_path}")
    api = Api()
    webview.create_window(
        "MIP Retail Optimizer™ Enterprise",
        url=index_path.as_uri(),
        js_api=api,
        maximized=True,
    )
    webview.start()


if __name__ == "__main__":
    main()
