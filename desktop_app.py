"""Aplicación de escritorio PyWebView para MIP Retail Optimizer."""

from __future__ import annotations

import json
import os
import base64
import ntpath
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import webview
from dotenv import load_dotenv
from fpdf import FPDF

from optimizacion import (
    CAPACIDADES_DEFAULT,
    COSTOS_ENVIO_DEFAULT,
    UBICACIONES_DEFAULT,
    ZONAS_DEFAULT,
    resolver_modelo,
)


MODEL_NAME = "gemini-2.5-flash"


def resource_path(*parts: str) -> Path:
    """Resuelve recursos tanto en desarrollo como dentro del bundle onefile."""
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return bundle_root.joinpath(*parts)


def _clean_api_key(value: str | None) -> str | None:
    cleaned = (value or "").strip().strip('"').strip("'").strip()
    return cleaned if len(cleaned) > 20 else None


def _parse_bundled_api_key(env_path: Path) -> str | None:
    try:
        raw = env_path.read_bytes()
    except OSError:
        return None

    contents = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            contents = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if contents is None:
        return None

    for line in contents.splitlines():
        line = line.lstrip("\ufeff").strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        name, separator, value = line.partition("=")
        if separator and name.strip() == "GEMINI_API_KEY":
            return _clean_api_key(value)
    return None


def _load_api_key() -> str | None:
    meipass = getattr(sys, "_MEIPASS", None)
    env_paths: list[Path] = []
    if getattr(sys, "frozen", False):
        executable_dir = Path(sys.executable).resolve().parent
        env_paths.extend((executable_dir / ".env", executable_dir.parent / ".env"))
    else:
        env_paths.append(Path(__file__).resolve().parent / ".env")
    bundled_env = Path(meipass) / ".env" if meipass else None
    if bundled_env:
        # The onefile copy should override any stale .env next to the executable.
        env_paths.append(bundled_env)

    seen: set[Path] = set()
    for env_path in env_paths:
        try:
            resolved_path = env_path.resolve()
            if resolved_path in seen:
                continue
            seen.add(resolved_path)
            load_dotenv(os.fspath(resolved_path), override=True)
        except (OSError, UnicodeError, ValueError):
            continue

    api_key = _clean_api_key(os.getenv("GEMINI_API_KEY", ""))
    if api_key is None and bundled_env is not None:
        api_key = _parse_bundled_api_key(bundled_env)
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key
    return api_key


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
        """Guarda un informe ejecutivo de una página mediante el diálogo nativo."""
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
            centers = list(params.get("ubicaciones") or UBICACIONES_DEFAULT)
            zones = list(params.get("zonas") or ZONAS_DEFAULT)
            demands = params.get("demandas") or [0] * len(zones)
            capacities = params.get("capacidades") or CAPACIDADES_DEFAULT
            tariffs = params.get("costos_envio") or params.get("tarifas") or COSTOS_ENVIO_DEFAULT

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
            saving_pct = float(
                result.get("porcentaje_ahorro", saving / baseline * 100 if baseline else 0) or 0
            )

            class ExecutivePdf(FPDF):
                def header(self):
                    self.set_fill_color(15, 23, 42)
                    self.rect(0, 0, self.w, 27, style="F")
                    self.set_text_color(255, 255, 255)
                    self.set_font("Helvetica", "B", 15)
                    self.set_xy(12, 4)
                    self.cell(0, 7, "MIP RETAIL OPTIMIZER | ENTERPRISE")
                    self.set_font("Helvetica", "", 8)
                    self.set_xy(12, 13)
                    self.cell(0, 5, "Reporte ejecutivo de optimización de red logística")
                    self.set_xy(12, 19)
                    self.cell(0, 4, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

                def footer(self):
                    self.set_y(-9)
                    self.set_text_color(71, 85, 105)
                    self.set_font("Helvetica", "", 8)
                    self.cell(0, 4, "MIP Retail Optimizer Enterprise  |  Confidencial  |  Página 1 de 1", align="C")

            pdf = ExecutivePdf(orientation="L", unit="mm", format="A4")
            pdf.set_margins(12, 32, 12)
            pdf.set_auto_page_break(auto=False)
            pdf.set_title("Reporte Ejecutivo MIP Retail Optimizer")
            pdf.set_author("MIP Retail Optimizer Enterprise")
            pdf.add_page()

            margin, gap = 12.0, 3.0
            card_y, card_h = 32.0, 22.0
            card_width = (pdf.w - 2 * margin - gap * 3) / 4
            kpis = [
                ("Costo Óptimo", f"${total_cost:,.0f} USD"),
                ("Ahorro vs. Baseline", f"${saving:,.0f} USD / {saving_pct:.2f}%"),
                ("Centros Activos", ", ".join(map(str, opened)) or "Ninguno"),
                ("Nivel de Servicio", f"{service_level:.1f}%"),
            ]
            for index, (label, value) in enumerate(kpis):
                x = margin + index * (card_width + gap)
                pdf.set_fill_color(241, 245, 249)
                pdf.set_draw_color(203, 213, 225)
                pdf.rect(x, card_y, card_width, card_h, style="DF")
                pdf.set_xy(x + 2, card_y + 3)
                pdf.set_text_color(71, 85, 105)
                pdf.set_font("Helvetica", "", 7)
                pdf.cell(card_width - 4, 5, label, align="C")
                pdf.set_xy(x + 2, card_y + 11)
                pdf.set_text_color(15, 23, 42)
                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(card_width - 4, 7, value, align="C")

            def section_title(text: str, x: float, y: float) -> None:
                pdf.set_xy(x, y)
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(15, 23, 42)
                pdf.cell(0, 5, text)

            def draw_grid(
                headers: list[str],
                rows: list[list[str]],
                widths: list[float],
                x: float,
                y: float,
                row_height: float,
                right_columns: set[int],
                highlighted_rows: set[int] | None = None,
                font_size: float = 7,
            ) -> float:
                highlighted_rows = highlighted_rows or set()
                for row_index, values in enumerate([headers, *rows]):
                    row_y = y + row_index * row_height
                    is_header = row_index == 0
                    if is_header:
                        fill = (37, 99, 235)
                        text_color = (255, 255, 255)
                        style = "B"
                    else:
                        fill = (219, 234, 254) if row_index - 1 in highlighted_rows else (255, 255, 255)
                        text_color = (15, 23, 42)
                        style = ""
                    current_x = x
                    for column, (value, width) in enumerate(zip(values, widths)):
                        pdf.set_fill_color(*fill)
                        pdf.set_draw_color(203, 213, 225)
                        pdf.rect(current_x, row_y, width, row_height, style="DF")
                        pdf.set_xy(current_x + 1.5, row_y + 0.7)
                        pdf.set_text_color(*text_color)
                        pdf.set_font("Helvetica", style, font_size)
                        pdf.cell(
                            width - 3,
                            row_height - 1.4,
                            str(value),
                            align="R" if column in right_columns else "L",
                        )
                        current_x += width
                return y + (len(rows) + 1) * row_height

            table_width = pdf.w - 2 * margin
            section_title("MATRIZ COMPLETA DE ASIGNACIÓN LOGÍSTICA | L1-L4 × Z1-Z6", margin, 57)
            matrix_rows: list[list[str]] = []
            for center in centers:
                quantities = [flows.get((str(center), str(zone)), 0.0) for zone in zones]
                matrix_rows.append([str(center), *[f"{value:,.0f}" for value in quantities], f"{sum(quantities):,.0f}"])
            matrix_headers = ["Centro", *[str(zone) for zone in zones], "Total"]
            matrix_widths = [27.0] + [(table_width - 54.0) / max(len(zones), 1)] * len(zones) + [27.0]
            draw_grid(
                matrix_headers,
                matrix_rows,
                matrix_widths,
                margin,
                63,
                6.3,
                set(range(1, len(matrix_headers))),
                {index for index, center in enumerate(centers) if center in opened},
            )

            section_title("DETALLE DE RUTAS ACTIVAS Y UTILIZACIÓN DE CAPACIDAD", margin, 98)
            utilization_parts = []
            for center in opened:
                if center in centers:
                    center_idx = centers.index(center)
                    used = sum(flows.get((str(center), str(zone)), 0.0) for zone in zones)
                    capacity = float(capacities[center_idx] or 0) if center_idx < len(capacities) else 0.0
                    utilization = used / capacity * 100 if capacity else 0.0
                    utilization_parts.append(f"{center}: {utilization:.1f}%")
            utilization_text = "Utilización: " + ("  |  ".join(utilization_parts) if utilization_parts else "Sin centros activos")
            pdf.set_xy(margin, 103)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(table_width, 4, utilization_text)

            route_rows: list[list[str]] = []
            for item in assignments:
                center = str(item.get("Ubicacion", ""))
                zone = str(item.get("Zona", ""))
                quantity = float(item.get("Cantidad_Enviada", 0) or 0)
                route_cost = 0.0
                if center in centers and zone in zones:
                    center_idx, zone_idx = centers.index(center), zones.index(zone)
                    try:
                        route_cost = quantity * float(tariffs[center_idx][zone_idx])
                    except (IndexError, TypeError, ValueError):
                        pass
                route_rows.append([center, zone, f"{quantity:,.0f}", f"${route_cost:,.2f}"])

            route_headers = ["Centro Origen", "Zona Destino", "Unidades Asignadas", "Costo de Ruta USD"]
            route_widths = [table_width * 0.20, table_width * 0.19, table_width * 0.30, table_width * 0.31]
            route_row_height = 6.5
            if len(route_rows) > 6:
                route_row_height = max(3.2, min(6.5, (194 - 108 - 6.5) / (len(route_rows) + 1)))
            draw_grid(
                route_headers,
                route_rows,
                route_widths,
                margin,
                108,
                route_row_height,
                {2, 3},
                font_size=7 if route_row_height >= 5 else 6,
            )
            pdf.output(path)
            if len(pdf.pages) != 1:
                raise RuntimeError("El reporte ejecutivo debe ocupar exactamente una página.")
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
        try:
            answer = self._generate_text(prompt)
            return {"answer": answer, "model": MODEL_NAME}
        except Exception as exc:
            message = str(exc).strip() or exc.__class__.__name__
            if self._api_key:
                message = message.replace(self._api_key, "[clave oculta]")
            return {"answer": f"Error al consultar Gemini: {message}", "model": MODEL_NAME}

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
