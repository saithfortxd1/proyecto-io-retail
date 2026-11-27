"""Aplicación de escritorio PyWebView para MIP Retail Optimizer."""

from __future__ import annotations

import json
import os
import base64
import ntpath
import sys
from html import escape
from pathlib import Path
from typing import Any

import webview
from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from optimizacion import resolver_modelo


MODEL_NAME = "gemini-2.5-flash"


def resource_path(*parts: str) -> Path:
    """Resuelve recursos tanto en desarrollo como dentro del bundle onefile."""
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return bundle_root.joinpath(*parts)


def _load_api_key() -> str | None:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        load_dotenv(os.path.join(sys._MEIPASS, ".env"), override=False)
    else:
        local_env = os.path.join(Path(__file__).resolve().parent, ".env")
        load_dotenv(local_env, override=False)
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
        """Genera el informe PDF en Python y lo guarda mediante el diálogo nativo."""
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
            service_level = (served_units / total_demand * 100) if total_demand > 0 else 0.0
            opened = result.get("centros_abiertos") or []
            baseline = float(params.get("costo_baseline", 0) or 0)
            total_cost = float(result.get("costo_total", 0) or 0)
            saving = float(result.get("ahorro", baseline - total_cost) or 0)
            saving_pct = float(result.get("porcentaje_ahorro", 0) or 0)

            navy = colors.HexColor("#0F172A")
            blue = colors.HexColor("#2563EB")
            pale = colors.HexColor("#F1F5F9")
            slate = colors.HexColor("#475569")
            green = colors.HexColor("#059669")
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                "ExecutiveTitle", parent=styles["Title"], fontName="Helvetica-Bold",
                fontSize=20, leading=24, textColor=navy, spaceAfter=3 * mm,
            )
            subtitle_style = ParagraphStyle(
                "ExecutiveSubtitle", parent=styles["Normal"], fontSize=9,
                leading=13, textColor=slate, spaceAfter=5 * mm,
            )
            kpi_label = ParagraphStyle(
                "KpiLabel", parent=styles["Normal"], fontSize=8,
                leading=10, textColor=slate, alignment=TA_CENTER,
            )
            heading = ParagraphStyle(
                "SectionHeading", parent=styles["Heading2"], fontName="Helvetica-Bold",
                fontSize=12, leading=15, textColor=navy, spaceBefore=4 * mm,
                spaceAfter=2 * mm,
            )

            def draw_page(canvas, doc):
                canvas.saveState()
                width, height = landscape(A4)
                canvas.setFillColor(navy)
                canvas.rect(0, height - 20 * mm, width, 20 * mm, fill=1, stroke=0)
                canvas.setFillColor(colors.white)
                canvas.setFont("Helvetica-Bold", 11)
                canvas.drawString(15 * mm, height - 12 * mm, "MIP RETAIL OPTIMIZER  |  ENTERPRISE")
                canvas.setFillColor(slate)
                canvas.setFont("Helvetica", 8)
                canvas.drawString(15 * mm, 10 * mm, "Reporte ejecutivo de optimización logística")
                canvas.drawRightString(width - 15 * mm, 10 * mm, f"Página {doc.page}")
                canvas.restoreState()

            doc = SimpleDocTemplate(
                path, pagesize=landscape(A4), rightMargin=15 * mm,
                leftMargin=15 * mm, topMargin=27 * mm, bottomMargin=17 * mm,
                title="Reporte Ejecutivo MIP Retail Optimizer",
                author="MIP Retail Optimizer Enterprise",
            )
            story = [
                Paragraph("Reporte Ejecutivo", title_style),
                Paragraph(
                    "Resultados del modelo de localización y asignación de centros de distribución.",
                    subtitle_style,
                ),
            ]

            kpis = [
                ("Costo óptimo", f"${total_cost:,.2f} USD"),
                ("Ahorro vs. baseline", f"${saving:,.2f} USD ({saving_pct:.2f}%)"),
                ("Centros activos", escape(", ".join(map(str, opened)) or "Ninguno")),
                ("Nivel de servicio", f"{service_level:.2f}%"),
            ]
            kpi_cells = [
                Paragraph(
                    f'<font size="8" color="#475569">{label}</font><br/>'
                    f'<font name="Helvetica-Bold" size="11" color="#0F172A">{value}</font>',
                    kpi_label,
                )
                for label, value in kpis
            ]
            kpi_table = Table(
                [kpi_cells],
                colWidths=[(landscape(A4)[0] - 30 * mm) / 4] * 4,
                rowHeights=[19 * mm],
            )
            kpi_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), pale),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.extend([kpi_table, Spacer(1, 5 * mm)])

            story.append(Paragraph("Matriz completa de asignación logística", heading))
            matrix_rows = [["Centro", *zones, "Total unidades"]]
            for center in centers:
                quantities = [flows.get((str(center), str(zone)), 0.0) for zone in zones]
                matrix_rows.append([
                    str(center),
                    *[f"{value:,.0f}" if value else "—" for value in quantities],
                    f"{sum(quantities):,.0f}",
                ])
            col_widths = [25 * mm] + [25 * mm] * len(zones) + [30 * mm]
            matrix = Table(matrix_rows, repeatRows=1, colWidths=col_widths, hAlign="LEFT")
            matrix.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), blue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, pale]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.extend([matrix, Spacer(1, 4 * mm)])
            story.append(Paragraph("Detalle de rutas activas", heading))
            route_rows = [["Centro origen", "Zona destino", "Unidades asignadas"]]
            route_rows.extend([
                [
                    escape(str(item.get("Ubicacion", ""))),
                    escape(str(item.get("Zona", ""))),
                    f"{float(item.get('Cantidad_Enviada', 0) or 0):,.2f}",
                ]
                for item in assignments
            ])
            routes = Table(route_rows, repeatRows=1, colWidths=[55 * mm, 55 * mm, 55 * mm])
            routes.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), navy),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, pale]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (2, 1), (2, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(routes)
            doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
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
