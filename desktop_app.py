"""Aplicación de escritorio PyWebView para MIP Retail Optimizer."""

from __future__ import annotations

import json
import os
import base64
import ntpath
import sys
from pathlib import Path
from typing import Any

import webview
from dotenv import load_dotenv
from fpdf import FPDF

from optimizacion import resolver_modelo


MODEL_NAME = "gemini-2.5-flash"


def resource_path(*parts: str) -> Path:
    """Resuelve recursos tanto en desarrollo como dentro del bundle onefile."""
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return bundle_root.joinpath(*parts)


def _load_api_key() -> str | None:
    env_paths: list[Path] = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        env_paths.append(Path(os.path.join(meipass, ".env")))

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        env_paths.extend((exe_dir / ".env", exe_dir.parent / ".env"))
    else:
        env_paths.append(Path(__file__).resolve().parent / ".env")

    for env_path in env_paths:
        load_dotenv(os.fspath(env_path), override=False)
    return os.getenv("GEMINI_API_KEY") or None


class Api:
    """Métodos JavaScript expuestos a la interfaz React por PyWebView."""

    def __init__(self) -> None:
        self._api_key = _load_api_key()
        self._gemini_client = None
        self._window = None

    def _save_dialog(self, filename: str, file_types: list[str] | tuple[str, ...]) -> str | None:
        window = self._window
        if window is None and webview.windows:
            window = webview.windows[0]
        if window is None:
            raise RuntimeError("La ventana de PyWebView todavía no está disponible.")

        selected = window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=filename,
            file_types=tuple(file_types) or ("All files (*.*)",),
        )
        if isinstance(selected, (tuple, list)):
            selected = selected[0] if selected else None
        if not selected:
            return None
        return os.path.abspath(os.fspath(selected))

    @staticmethod
    def _ensure_extension(path: str, filename: str) -> str:
        extension = Path(filename).suffix
        if extension and not Path(path).suffix:
            return path + extension
        return path

    def guardar_archivo_base64(
        self, filename: str, base64_data: str, file_types: list[str] | None = None
    ) -> dict[str, Any]:
        """Abre el diálogo nativo y escribe un archivo enviado desde React."""
        safe_filename = ntpath.basename(str(filename).replace("/", "\\")).strip()
        if not safe_filename or safe_filename in {".", ".."}:
            return {"ok": False, "error": "Nombre de archivo no válido."}
        try:
            data = base64.b64decode(base64_data, validate=True)
        except (ValueError, TypeError):
            return {"ok": False, "error": "El contenido Base64 no es válido."}

        try:
            path = self._save_dialog(safe_filename, file_types or [])
            if path is None:
                return {"ok": False, "cancelado": True}
            path = self._ensure_extension(path, safe_filename)
            Path(path).write_bytes(data)
            return {"ok": True, "ruta": path}
        except Exception as exc:
            return {"ok": False, "error": f"No se pudo guardar el archivo: {exc}"}

    def guardar_pdf_ejecutivo(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Genera un PDF ejecutivo y lo guarda con el diálogo nativo."""
        try:
            path = self._save_dialog(
                "Reporte_Ejecutivo_MIP.pdf", ("Documento PDF (*.pdf)",)
            )
            if path is None:
                return {"ok": False, "cancelado": True}
            path = self._ensure_extension(path, "Reporte_Ejecutivo_MIP.pdf")

            result = payload.get("resultado") or payload.get("result") or {}
            params = payload.get("parametros") or payload.get("params") or {}
            assignments = result.get("asignaciones") or []
            centers = params.get("ubicaciones") or ["L1", "L2", "L3", "L4"]
            zones = params.get("zonas") or ["Z1", "Z2", "Z3", "Z4", "Z5", "Z6"]
            demands = params.get("demandas") or [0] * len(zones)

            flows: dict[tuple[str, str], float] = {}
            served_units = 0.0
            for item in assignments:
                center = str(item.get("Ubicacion", ""))
                zone = str(item.get("Zona", ""))
                quantity = float(item.get("Cantidad_Enviada", 0) or 0)
                flows[(center, zone)] = flows.get((center, zone), 0.0) + quantity
                if zone in zones:
                    served_units += quantity

            total_demand = sum(float(value or 0) for value in demands)
            service_level = served_units / total_demand * 100 if total_demand else 0.0
            opened = result.get("centros_abiertos") or []
            baseline = float(params.get("costo_baseline", 0) or 0)
            total_cost = float(result.get("costo_total", 0) or 0)
            saving = float(result.get("ahorro", baseline - total_cost) or 0)
            saving_pct = float(result.get("porcentaje_ahorro", 0) or 0)

            class ExecutivePdf(FPDF):
                def header(self):
                    self.set_fill_color(15, 23, 42)
                    self.rect(0, 0, self.w, 20, style="F")
                    self.set_text_color(255, 255, 255)
                    self.set_font("Helvetica", "B", 11)
                    self.set_xy(15, 7)
                    self.cell(0, 6, "MIP RETAIL OPTIMIZER  |  ENTERPRISE")

                def footer(self):
                    self.set_y(-12)
                    self.set_text_color(71, 85, 105)
                    self.set_font("Helvetica", "", 8)
                    self.cell(0, 5, f"Reporte ejecutivo de optimizacion logistica  |  Pagina {self.page_no()}", align="C")

            pdf = ExecutivePdf(orientation="L", unit="mm", format="A4")
            pdf.set_margins(15, 26, 15)
            pdf.set_auto_page_break(auto=True, margin=17)
            pdf.set_title("Reporte Ejecutivo MIP Retail Optimizer")
            pdf.set_author("MIP Retail Optimizer Enterprise")
            pdf.add_page()
            pdf.set_text_color(15, 23, 42)
            pdf.set_font("Helvetica", "B", 20)
            pdf.cell(0, 11, "Reporte Ejecutivo", ln=1)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(0, 7, "Resultados del modelo de localizacion y asignacion de centros de distribucion.", ln=1)
            pdf.ln(4)

            kpis = [
                ("Costo optimo", f"${total_cost:,.2f} USD"),
                ("Ahorro vs. baseline", f"${saving:,.2f} USD ({saving_pct:.2f}%)"),
                ("Centros activos", ", ".join(map(str, opened)) or "Ninguno"),
                ("Nivel de servicio", f"{service_level:.2f}%"),
            ]
            gap = 3
            card_width = (pdf.w - 30 - gap * 3) / 4
            card_y = pdf.get_y()
            for index, (label, value) in enumerate(kpis):
                x = 15 + index * (card_width + gap)
                pdf.set_fill_color(241, 245, 249)
                pdf.set_draw_color(203, 213, 225)
                pdf.rect(x, card_y, card_width, 25, style="DF")
                pdf.set_xy(x + 2, card_y + 4)
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(71, 85, 105)
                pdf.cell(card_width - 4, 6, label, align="C")
                pdf.set_xy(x + 2, card_y + 12)
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(15, 23, 42)
                pdf.cell(card_width - 4, 8, value, align="C")
            pdf.set_y(card_y + 30)

            def draw_table(title: str, headers: list[str], rows: list[list[str]], widths: list[float]):
                if pdf.get_y() + 17 > pdf.page_break_trigger:
                    pdf.add_page()
                pdf.set_font("Helvetica", "B", 12)
                pdf.set_text_color(15, 23, 42)
                pdf.cell(0, 8, title, ln=1)

                def draw_row(values: list[str], is_header: bool = False):
                    if pdf.get_y() + 8 > pdf.page_break_trigger:
                        pdf.add_page()
                    pdf.set_font("Helvetica", "B" if is_header else "", 8)
                    pdf.set_fill_color(*( (37, 99, 235) if is_header else (255, 255, 255) ))
                    pdf.set_text_color(*( (255, 255, 255) if is_header else (15, 23, 42) ))
                    for cell_value, width in zip(values, widths):
                        pdf.cell(width, 8, str(cell_value), border=1, align="C", fill=is_header)
                    pdf.ln(8)

                draw_row(headers, is_header=True)
                for row in rows:
                    draw_row(row)
                pdf.ln(4)

            content_width = pdf.w - 30
            first_width, total_width = 25.0, 30.0
            zone_width = (content_width - first_width - total_width) / max(1, len(zones))
            matrix_rows = []
            for center in centers:
                quantities = [flows.get((str(center), str(zone)), 0.0) for zone in zones]
                matrix_rows.append([
                    str(center),
                    *[f"{value:,.0f}" if value else "-" for value in quantities],
                    f"{sum(quantities):,.0f}",
                ])
            draw_table(
                "Matriz completa de asignacion logistica",
                ["Centro", *[str(zone) for zone in zones], "Total unidades"],
                matrix_rows,
                [first_width] + [zone_width] * len(zones) + [total_width],
            )

            route_rows = [
                [
                    str(item.get("Ubicacion", "")),
                    str(item.get("Zona", "")),
                    f"{float(item.get('Cantidad_Enviada', 0) or 0):,.2f}",
                ]
                for item in assignments
            ]
            draw_table(
                "Detalle de rutas activas",
                ["Centro origen", "Zona destino", "Unidades asignadas"],
                route_rows,
                [content_width * 0.34, content_width * 0.33, content_width * 0.33],
            )
            pdf.output(path)
            return {"ok": True, "ruta": path}
        except Exception as exc:
            return {"ok": False, "error": f"No se pudo generar el PDF: {exc}"}
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
    window = webview.create_window(
        "MIP Retail Optimizer™ Enterprise",
        url=index_path.as_uri(),
        js_api=api,
        maximized=True,
    )
    api._window = window
    webview.start()


if __name__ == "__main__":
    main()
