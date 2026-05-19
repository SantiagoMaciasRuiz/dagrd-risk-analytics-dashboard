#!/usr/bin/env python3
"""
AutoVis Smart: Generador inteligente de visualizaciones Power BI.
Diagnostica automáticamente la estructura del modelo y crea visualizaciones profesionales.
"""
from __future__ import annotations

import argparse
import json
import re
import uuid
import urllib.request
from pathlib import Path
from typing import Any


NARRATIVE_TEMPLATES = {"auto", "kpi", "tendencia", "comparacion", "territorio"}
VISUAL_STRATEGIES = {"auto", "rule", "llm"}
HYBRID_VISUAL_TYPES = {"hybrid", "narrative", "html", "deneb", "textbox"}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_id() -> str:
    return uuid.uuid4().hex[:20]


def _sanitize_identifier(value: str) -> str:
    cleaned = re.sub(r"[\r\n\t]+", " ", str(value or ""))
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


def _clean_path_value(raw_value: str) -> str:
    return str(raw_value or "").strip().strip('"').strip("'")


def _resolve_report_definition(pbip_path: Path) -> Path:
    """Resuelve la carpeta definition del reporte PBIP."""
    if pbip_path.is_dir():
        if pbip_path.name.endswith(".Report"):
            definition = pbip_path / "definition"
            if definition.exists():
                return definition
        if pbip_path.name == "definition" and (pbip_path / "pages").exists():
            return pbip_path

    if pbip_path.suffix.lower() == ".pbip":
        stem = pbip_path.stem
        report_dir = pbip_path.parent / f"{stem}.Report"
        definition = report_dir / "definition"
        if definition.exists():
            return definition
        
        for sibling in pbip_path.parent.iterdir():
            if sibling.is_dir() and sibling.name.endswith(".Report"):
                fallback_def = sibling / "definition"
                if fallback_def.exists():
                    return fallback_def

    raise RuntimeError(f"No se pudo resolver carpeta definition desde: {pbip_path}")


def _resolve_semantic_tables_dir(pbip_path: Path) -> Path | None:
    """Resuelve la carpeta de tablas del modelo semántico."""
    if pbip_path.suffix.lower() != ".pbip":
        return None
    stem = pbip_path.stem
    tables_dir = pbip_path.parent / f"{stem}.SemanticModel" / "definition" / "tables"
    return tables_dir if tables_dir.exists() else None


def _summarize_model_for_llm(analyzer: "ModelAnalyzer") -> dict[str, Any]:
    """Resume el modelo para que Ollama decida estrategia de diseño."""
    table_summary = []
    for table_name, info in list(analyzer.tables.items())[:20]:
        table_summary.append(
            {
                "table": table_name,
                "columns": len(info.get("columns") or []),
                "measures": len(info.get("measures") or []),
            }
        )

    return {
        "tables": table_summary,
        "measure_count": len(analyzer.measures),
        "date_fields": analyzer.date_fields[:10],
        "categorical_fields": analyzer.categorical_fields[:15],
        "measure_samples": [f"{t}.{m}" for t, m in analyzer.measures[:40]],
        "column_samples": [f"{t}.{c}" for t, c in analyzer.columns[:40]],
        "top_measure_names": [m for _, m in analyzer.measures[:12]],
    }


def _storyline_for_page(template: str, page_name: str, visuals_info: list[dict[str, Any]]) -> str:
    """Genera un encabezado narrativo corto para la pagina."""
    template = str(template or "kpi").strip().lower()
    page_name = _sanitize_identifier(page_name) or "Dashboard"
    lead_metric = _sanitize_identifier(str((visuals_info[0] or {}).get("field") if visuals_info else ""))
    lead_label = _sanitize_identifier(str((visuals_info[0] or {}).get("label") if visuals_info else ""))

    template_map = {
        "kpi": "Resumen ejecutivo con foco en los indicadores clave.",
        "tendencia": "Lectura temporal para ver cambio, ritmo y desviaciones.",
        "comparacion": "Vista comparativa para contrastar resultados y brechas.",
        "territorio": "Vista territorial para ubicar concentracion y cobertura.",
    }
    base = template_map.get(template, "Vista ejecutiva para explorar el modelo.")
    if lead_metric:
        return f"{page_name}: {base} Enfoque inicial en {lead_metric}."
    if lead_label:
        return f"{page_name}: {base} Enfoque inicial en {lead_label}."
    return f"{page_name}: {base}"


def _normalize_visual_plan(plan: dict[str, Any], analyzer: "ModelAnalyzer") -> dict[str, Any]:
    """Valida y recorta un plan de diseño para evitar resultados vacios o inestables."""
    clean: dict[str, Any] = {
        "page_strategy": "rule",
        "page_count": 0,
        "reasoning": [],
        "pages": {},
    }

    if not isinstance(plan, dict):
        return clean

    page_strategy = str(plan.get("page_strategy") or plan.get("strategy") or "rule").strip().lower()
    if page_strategy not in {"simple", "date_focused", "categorical_focused", "multi_professional", "mixed", "llm", "rule"}:
        page_strategy = "rule"
    clean["page_strategy"] = page_strategy

    reasoning = plan.get("reasoning") or plan.get("rationale") or []
    if isinstance(reasoning, list):
        clean["reasoning"] = [str(x)[:220] for x in reasoning[:8]]
    elif isinstance(reasoning, str):
        clean["reasoning"] = [reasoning[:220]]

    pages = plan.get("pages") or {}
    if not isinstance(pages, dict):
        return clean

    def _template_from_name(page_name: str, current_template: str) -> str:
        name = _sanitize_identifier(page_name).lower()
        if "tend" in name or "trend" in name:
            return "tendencia"
        if "territ" in name or "zona" in name or "comuna" in name or "barrio" in name:
            return "territorio"
        if "compar" in name or "oper" in name:
            return "comparacion"
        if "ejecut" in name or "resum" in name or "kpi" in name:
            return "kpi"
        return current_template

    for key, raw_page in list(pages.items())[:3]:
        if not isinstance(raw_page, dict):
            continue
        page_name = str(raw_page.get("name") or key).strip() or key
        page_template = str(raw_page.get("template") or raw_page.get("narrative_template") or "kpi").strip().lower()
        if page_template not in NARRATIVE_TEMPLATES:
            page_template = "kpi"
        page_template = _template_from_name(page_name, page_template)

        visual_count = raw_page.get("visual_count")
        try:
            visual_count = int(visual_count)
        except Exception:
            visual_count = 4
        visual_count = max(2, min(6, visual_count))

        visual_types = raw_page.get("visual_types") or raw_page.get("visuals") or []
        if not isinstance(visual_types, list):
            visual_types = []
        visual_types = [str(v).strip().lower() for v in visual_types if str(v).strip()]
        if not visual_types:
            visual_types = analyzer._infer_page_visual_types(page_template, visual_count)
        visual_types = [v if v in HYBRID_VISUAL_TYPES or v in {"card", "line", "bar", "table"} else "card" for v in visual_types]

        hybrid_mode = bool(raw_page.get("hybrid_mode") or raw_page.get("hybrid") or any(v in HYBRID_VISUAL_TYPES for v in visual_types))
        page_story = raw_page.get("narrative") or raw_page.get("header") or raw_page.get("story")
        if not isinstance(page_story, str) or not page_story.strip():
            page_story = _storyline_for_page(page_template, page_name, [])
        else:
            page_story = _sanitize_identifier(page_story)

        fields = raw_page.get("fields") or {}
        if not isinstance(fields, dict):
            fields = {}
        date_field = fields.get("date_field")
        categorical_field = fields.get("categorical_field")

        # Fallbacks seguros a partir del propio analizador.
        if not date_field and analyzer.date_fields:
            date_field = analyzer.date_fields[0]
        if not categorical_field and analyzer.categorical_fields:
            categorical_field = analyzer.categorical_fields[0]

        clean["pages"][key] = {
            "name": page_name,
            "template": page_template,
            "visual_count": visual_count,
            "visual_types": visual_types,
            "hybrid_mode": hybrid_mode,
            "narrative": page_story,
            "date_field": tuple(date_field) if isinstance(date_field, (list, tuple)) and len(date_field) == 2 else date_field,
            "categorical_field": tuple(categorical_field) if isinstance(categorical_field, (list, tuple)) and len(categorical_field) == 2 else categorical_field,
        }

    clean["page_count"] = len(clean["pages"])

    if not clean["pages"]:
        return clean

    return clean


def _request_ollama_visual_plan(
    analyzer: "ModelAnalyzer",
    model: str = "qwen3:8b",
    base_url: str = "http://localhost:11434",
) -> dict[str, Any]:
    """Pide a Ollama un plan de visualización JSON y lo valida."""
    context = _summarize_model_for_llm(analyzer)
    system = (
        "Eres un arquitecto senior de Power BI. "
        "Debes decidir la mejor estructura visual para un dashboard. "
        "Responde SOLO JSON valido y sin markdown con esta forma: "
        "{\"page_strategy\":\"llm\",\"reasoning\":[...],\"pages\":{...}}. "
        "Reglas: maximo 3 paginas; cada pagina debe tener visual_count entre 2 y 6; "
        "mezcla cards, line, bar y table segun los datos; si hay fecha usa line; si hay categorias usa bar; "
        "maximo 2 cards por pagina; preferir paginas Ejecutiva, Tendencia, Territorial o Comparativa segun el caso; "
        "si conviene un encabezado narrativo, usa hybrid_mode=true y agrega narrative o header; "
        "tambien puedes sugerir tipos html, deneb o textbox cuando agreguen valor, con fallback seguro."
    )
    user = (
        "Analiza este modelo y propón un plan de visualizacion. "
        "Debes priorizar buena composicion visual, jerarquia, proporciones y variedad. "
        "Datos del modelo: " + json.dumps(context, ensure_ascii=True)
    )

    payload = {
        "model": model,
        "prompt": system + "\n\n" + user,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
            "num_predict": 700,
        },
    }
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    try:
        decoded = json.loads(raw)
        if isinstance(decoded, dict) and "response" in decoded:
            content = str(decoded.get("response") or "").strip()
        else:
            message = decoded.get("message", {}) if isinstance(decoded, dict) else {}
            content = str(message.get("content") or "").strip()
    except Exception:
        content = raw.strip()

    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {"ok": False, "error": "Ollama no devolvio JSON utilizable", "raw": content[:4000]}

    try:
        plan = json.loads(content[start : end + 1])
    except Exception as exc:
        return {"ok": False, "error": f"JSON invalido de Ollama: {exc}", "raw": content[:4000]}

    normalized = _normalize_visual_plan(plan, analyzer)
    if not normalized.get("pages"):
        return {"ok": False, "error": "Plan de Ollama vacio o invalido", "raw": content[:4000]}

    normalized["ok"] = True
    return normalized


def _sync_pages_metadata(report_def: Path, pages_meta: dict) -> dict:
    pages_meta.setdefault(
        "$schema",
        "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
    )
    pages_dir = report_def / "pages"
    ordered = list(pages_meta.get("pageOrder") or [])
    valid_order: list[str] = []
    for page_id in ordered:
        page_json_path = pages_dir / page_id / "page.json"
        if not page_json_path.exists():
            continue
        valid_order.append(page_id)
    pages_meta["pageOrder"] = valid_order
    active = str(pages_meta.get("activePageName") or "")
    if active not in valid_order:
        pages_meta["activePageName"] = valid_order[0] if valid_order else ""
    # El schema pagesMetadata/1.0.0 no permite la propiedad "pages".
    pages_meta.pop("pages", None)
    return pages_meta


class ModelAnalyzer:
    """Analiza automáticamente la estructura del modelo y detecta tablas, campos y medidas."""
    
    def __init__(self, tables_dir: Path | None):
        self.tables_dir = tables_dir
        self.tables: dict[str, dict[str, Any]] = {}
        self.measures: list[tuple[str, str]] = []
        self.columns: list[tuple[str, str]] = []
        self.date_fields: list[tuple[str, str]] = []  # (tabla, campo) de tipo fecha
        self.categorical_fields: list[tuple[str, str]] = []  # (tabla, campo) categórico
        self._analyze()

    @staticmethod
    def _normalize_tokens(value: str) -> str:
        text = _sanitize_identifier(value).lower()
        return re.sub(r"[^a-z0-9áéíóúñü]+", " ", text)

    def infer_narrative_template(self, forced_template: str) -> str:
        chosen = (forced_template or "auto").strip().lower()
        if chosen in NARRATIVE_TEMPLATES and chosen != "auto":
            return chosen

        haystack_parts = [
            " ".join(self.tables.keys()),
            " ".join([m for _, m in self.measures]),
            " ".join([c for _, c in self.columns]),
        ]
        haystack = self._normalize_tokens(" ".join(haystack_parts))

        scores = {
            "territorio": 0,
            "tendencia": 0,
            "comparacion": 0,
            "kpi": 0,
        }

        for kw in ("comuna", "barrio", "ciudad", "region", "zona", "territorio", "satc", "municipio", "departamento"):
            if kw in haystack:
                scores["territorio"] += 3

        for kw in ("fecha", "mes", "anio", "año", "dia", "hora", "time", "periodo", "period", "evolucion", "tendencia"):
            if kw in haystack:
                scores["tendencia"] += 3

        for kw in ("ratio", "porcentaje", "pct", "promedio", "avg", "max", "min", "vs", "delta", "variacion", "compar"):
            if kw in haystack:
                scores["comparacion"] += 2

        for kw in ("total", "count", "rows", "sum", "monto", "valor", "kpi", "indicador"):
            if kw in haystack:
                scores["kpi"] += 1

        best = max(scores.items(), key=lambda x: x[1])[0]
        if scores[best] <= 0:
            return "kpi"
        return best

    @staticmethod
    def _measure_score(template: str, table: str, measure: str) -> int:
        text = f"{table} {measure}".lower()
        score = 0

        if template == "kpi":
            for pat in ("rows", "count", "total", "sum", "ingreso", "monto", "valor", "kpi"):
                if pat in text:
                    score += 3
        elif template == "tendencia":
            for pat in ("fecha", "mes", "anio", "año", "hora", "trend", "evol", "growth", "period"):
                if pat in text:
                    score += 4
            for pat in ("avg", "promedio", "moving", "rolling"):
                if pat in text:
                    score += 2
        elif template == "comparacion":
            for pat in ("ratio", "pct", "porcentaje", "promedio", "avg", "max", "min", "distinct", "delta", "vs"):
                if pat in text:
                    score += 4
        elif template == "territorio":
            for pat in ("comuna", "barrio", "ciudad", "region", "zona", "satc", "territorio"):
                if pat in text:
                    score += 4
            for pat in ("count", "rows", "sum", "total"):
                if pat in text:
                    score += 1

        if measure.upper().startswith("AB_"):
            score += 1
        return score

    @staticmethod
    def _slot_titles(template: str, limit: int) -> list[str]:
        base_map = {
            "kpi": [
                "KPI Principal",
                "Volumen Total",
                "Cobertura",
                "Rendimiento",
                "Control de Calidad",
                "Resumen Ejecutivo",
            ],
            "tendencia": [
                "Tendencia Actual",
                "Variación del Periodo",
                "Promedio Móvil",
                "Pico Reciente",
                "Base de Comparación",
                "Ritmo de Cambio",
            ],
            "comparacion": [
                "Comparativo Principal",
                "Brecha",
                "Ratio Clave",
                "Máximo vs Mínimo",
                "Promedio vs Actual",
                "Diferencial",
            ],
            "territorio": [
                "Cobertura Territorial",
                "Concentración por Zona",
                "Desempeño por Comuna",
                "Comparativo Territorial",
                "Brecha Territorial",
                "Resumen Geográfico",
            ],
        }
        base = base_map.get(template, base_map["kpi"])
        out: list[str] = []
        idx = 0
        while len(out) < limit:
            out.append(base[idx % len(base)])
            idx += 1
        return out

    def get_narrative_visuals(self, template: str, limit: int = 6) -> list[dict[str, Any]]:
        visuals: list[dict[str, Any]] = []
        filtered_measures = [m for m in self.measures if not self._looks_like_datetime_metric(m[1])]
        candidate_measures = filtered_measures if filtered_measures else self.measures
        scored_measures = sorted(
            candidate_measures,
            key=lambda x: self._measure_score(template, x[0], x[1]),
            reverse=True,
        )

        titles = self._slot_titles(template, limit)
        used: set[tuple[str, str]] = set()

        for i in range(limit):
            metric: tuple[str, str] | None = None
            for candidate in scored_measures:
                if candidate not in used:
                    metric = candidate
                    used.add(candidate)
                    break

            if metric is None and self.columns:
                col_idx = i % len(self.columns)
                table, col = self.columns[col_idx]
                # Sin medidas disponibles, usar visuales de detalle seguros.
                suggested_type = "card" if i == 0 else "table"
                visuals.append(
                    {
                        "type": suggested_type,
                        "table": table,
                        "field": col,
                        "label": f"{titles[i]} · {col}",
                        "is_measure": False,
                    }
                )
                continue

            if metric is None:
                visuals.append(
                    {
                        "type": "blank",
                        "table": "",
                        "field": "",
                        "label": f"{titles[i]} · Sin dato",
                        "is_measure": False,
                    }
                )
                continue

            table, measure = metric
            suggested_type = self._infer_visual_type_for_measure(template=template, measure_name=measure)
            visuals.append(
                {
                    "type": suggested_type,
                    "table": table,
                    "field": measure,
                    "label": f"{titles[i]} · {measure}",
                    "is_measure": True,
                }
            )

        return visuals[:limit]

    @staticmethod
    def _looks_like_datetime_metric(measure_name: str) -> bool:
        text = _sanitize_identifier(measure_name).lower()
        bad_tokens = (
            "fecha", "hora", "date", "time", "timestamp", "inicio", "fin", "start", "end", "day", "month", "year"
        )
        return any(tok in text for tok in bad_tokens)

    def pick_best_date_field_for_table(self, table_name: str) -> tuple[str, str] | None:
        """Prioriza campo fecha de la misma tabla para evitar cruces sin relación."""
        for t, c in self.date_fields:
            if t == table_name:
                return (t, c)
        return self.date_fields[0] if self.date_fields else None

    def pick_best_category_field_for_table(self, table_name: str) -> tuple[str, str] | None:
        """Prioriza categoría de la misma tabla para evitar cruces sin relación."""
        preferred = ("comuna", "barrio", "zona", "region", "categoria", "category", "nombre", "name", "tipo")
        same_table = [(t, c) for (t, c) in self.categorical_fields if t == table_name]
        for t, c in same_table:
            cl = c.lower()
            if any(k in cl for k in preferred):
                return (t, c)
        if same_table:
            return same_table[0]
        return self.categorical_fields[0] if self.categorical_fields else None

    def get_table_detail_fields(
        self,
        table_name: str,
        max_cols: int = 2,
        exclude_field: str = "",
    ) -> list[tuple[str, str, bool]]:
        """Devuelve columnas de detalle de la misma tabla para evitar joins implícitos rotos."""
        out: list[tuple[str, str, bool]] = []
        info = self.tables.get(table_name) or {}
        cols = list(info.get("columns") or [])
        ex = _sanitize_identifier(exclude_field).lower()
        for col in cols:
            clean = _sanitize_identifier(col)
            if not clean:
                continue
            if ex and clean.lower() == ex:
                continue
            out.append((table_name, clean, False))
            if len(out) >= max_cols:
                break
        return out

    def _infer_visual_type_for_measure(self, template: str, measure_name: str) -> str:
        """Sugiere tipo visual por semántica de medida y señales del modelo."""
        text = self._normalize_tokens(f"{template} {measure_name}")

        ratio_tokens = ("ratio", "pct", "porcentaje", "promedio", "avg", "share", "participacion")
        trend_tokens = ("tendencia", "trend", "variacion", "delta", "growth", "periodo", "evol")
        dist_tokens = ("rank", "top", "bottom", "distrib", "comuna", "barrio", "region", "zona", "segmento")
        scalar_tokens = ("total", "count", "rows", "sum", "monto", "valor", "kpi", "indicador")

        has_date = len(self.date_fields) > 0
        has_cat = len(self.categorical_fields) > 0

        if any(tok in text for tok in trend_tokens) and has_date:
            return "line"
        if any(tok in text for tok in dist_tokens) and has_cat:
            return "bar"
        if any(tok in text for tok in ratio_tokens):
            if has_cat:
                return "bar"
            if has_date:
                return "line"
            return "table"
        if any(tok in text for tok in scalar_tokens):
            return "card"

        # Fallback contextual por plantilla.
        t = str(template or "").lower().strip()
        if t == "tendencia" and has_date:
            return "line"
        if t in {"territorio", "comparacion"} and has_cat:
            return "bar"
        if has_cat:
            return "bar"
        if has_date:
            return "line"
        return "table"
    
    def _analyze(self) -> None:
        """Analiza todas las tablas TMDL disponibles."""
        if not self.tables_dir or not self.tables_dir.exists():
            return
        
        for tmdl_file in sorted(self.tables_dir.glob("*.tmdl")):
            self._parse_tmdl(tmdl_file)
    
    def _parse_tmdl(self, tmdl_path: Path) -> None:
        """Parsea un archivo TMDL para extraer tabla, campos, medidas, fechas y categorías."""
        text = tmdl_path.read_text(encoding="utf-8", errors="ignore")
        
        table_name = tmdl_path.stem
        columns = []
        measures = []
        
        # Detectar nombre real de tabla
        table_match = re.search(r'^\s*table\s+[\'"]?([^\'":\r\n]+)[\'"]?\s*:', text, re.MULTILINE)
        if table_match:
            table_name = _sanitize_identifier(table_match.group(1))
        
        # Extraer columnas y detectar tipo de dato
        col_pattern = re.compile(
            r'^\s*column\s+[\'"]?([^\'"=]+)[\'"]?\s*=?\s*(?:\n.*?)?\s*(?:dataType:\s*[\'"]?([^\'",\n]+)[\'"]?)?',
            re.MULTILINE | re.DOTALL
        )
        
        # Parseo simple: buscar bloques de columna
        col_blocks = re.finditer(
            r'^\s*column\s+[\'"]([^\'"=]+)[\'"]?\s*(?:=.*?)?\s*(?:dataType:\s*[\'"]?([^\'"}\n,]+)[\'"]?)?',
            text,
            re.MULTILINE
        )
        
        for match in col_blocks:
            col_name = _sanitize_identifier(match.group(1))
            data_type = (match.group(2) or "").lower().strip()
            
            if col_name and not col_name.startswith("_"):
                columns.append(col_name)
                self.columns.append((table_name, col_name))
                
                # Detectar si es una fecha
                if any(dt in data_type for dt in ["datetime", "date", "time", "timestamp"]):
                    self.date_fields.append((table_name, col_name))
                # Detectar si es categórico (texto, nombre, categoría)
                elif any(dt in data_type for dt in ["string", "text", "varchar"]) or \
                     any(kw in col_name.lower() for kw in ["nombre", "name", "tipo", "type", "categoria", "category", "comuna", "zona", "region", "barrio"]):
                    self.categorical_fields.append((table_name, col_name))
        
        # Extraer medidas
        measure_pattern = re.compile(r'^\s*measure\s+[\'"]?([^\'"=]+)[\'"]?\s*=', re.MULTILINE)
        for match in measure_pattern.finditer(text):
            measure_name = _sanitize_identifier(match.group(1))
            if measure_name:
                measures.append((table_name, measure_name))
                self.measures.append((table_name, measure_name))
        
        self.tables[table_name] = {
            "columns": columns,
            "measures": measures,
            "count": len(columns),
        }
    
    def get_best_visuals(self, limit: int = 4) -> list[dict[str, str]]:
        """Selecciona las mejores visualizaciones disponibles basado en datos reales."""
        visuals = []
        
        # Prioridad 1: Medidas numéricas (VERIFICADAS)
        if self.measures:
            for table, measure in self.measures[:limit]:
                visuals.append({
                    "type": "card",
                    "table": table,
                    "field": measure,
                    "label": f"{measure} ({table})",
                    "is_measure": True,
                })
        
        # Prioridad 2: Columnas numéricas/fechas
        if len(visuals) < limit and self.columns:
            for table, col in self.columns[:limit - len(visuals)]:
                visuals.append({
                    "type": "card",
                    "table": table,
                    "field": col,
                    "label": f"{col}",
                    "is_measure": False,
                })
        
        # Si aún no hay suficientes, crear placeholders vacíos pero bien formados
        if len(visuals) < limit:
            for i in range(limit - len(visuals)):
                visuals.append({
                    "type": "blank",
                    "table": "",
                    "field": "",
                    "label": f"Visualización {len(visuals) + 1}",
                    "is_measure": False,
                })
        
        return visuals[:limit]

    def decide_page_strategy(self) -> dict[str, Any]:
        """
        Decide automáticamente la estrategia: 1, 2 o 3 páginas.
        Retorna dict con decisiones, razones, y visuals para cada página.
        """
        has_date_fields = len(self.date_fields) > 0
        has_categorical = len(self.categorical_fields) > 0
        measure_count = len(self.measures)
        
        decision = {
            "has_dates": has_date_fields,
            "has_categorical": has_categorical,
            "measure_count": measure_count,
            "date_fields": self.date_fields[:3],  # Top 3
            "categorical_fields": self.categorical_fields[:3],
            "page_count": 1,
            "page_strategy": "simple",
            "pages": {},
            "reasoning": [],
        }
        
        # Lógica de decisión
        if measure_count < 4:
            decision["page_count"] = 1
            decision["page_strategy"] = "simple"
            decision["reasoning"].append("Pocas medidas (<4), página única")
            decision["pages"]["simple"] = {
                "name": "Resumen",
                "template": "kpi",
                "visual_count": min(measure_count, 4),
                "visual_types": self._infer_page_visual_types("kpi", min(measure_count, 4)),
            }
        elif has_date_fields and has_categorical and measure_count >= 6:
            decision["page_count"] = 3
            decision["page_strategy"] = "multi_professional"
            decision["reasoning"] = [
                f"OK: {measure_count} medidas detectadas",
                f"OK: {len(self.date_fields)} campos fecha encontrados -> Tendencia",
                f"OK: {len(self.categorical_fields)} campos categoricos encontrados -> Territorial",
                "Estrategia: 3 paginas profesionales (Ejecutiva, Tendencia, Territorial)"
            ]
            decision["pages"]["executive"] = {
                "name": "Ejecutiva",
                "template": "kpi",
                "visual_count": 4,
                "visual_types": self._infer_page_visual_types("kpi", 4),
            }
            decision["pages"]["trending"] = {
                "name": "Tendencia",
                "template": "tendencia",
                "visual_count": 4,
                "visual_types": self._infer_page_visual_types("tendencia", 4),
                "date_field": self.date_fields[0] if self.date_fields else None,
            }
            decision["pages"]["territorial"] = {
                "name": "Territorial",
                "template": "territorio",
                "visual_count": 4,
                "visual_types": self._infer_page_visual_types("territorio", 4),
                "categorical_field": self.categorical_fields[0] if self.categorical_fields else None,
            }
        elif has_date_fields and measure_count >= 6:
            decision["page_count"] = 2
            decision["page_strategy"] = "date_focused"
            decision["reasoning"] = [
                f"OK: {measure_count} medidas detectadas",
                f"OK: {len(self.date_fields)} campos fecha encontrados",
                "INFO: No hay campos categoricos para territorial",
                "Estrategia: 2 paginas (Ejecutiva, Tendencia)"
            ]
            decision["pages"]["executive"] = {
                "name": "Ejecutiva",
                "template": "kpi",
                "visual_count": 3,
                "visual_types": self._infer_page_visual_types("kpi", 3),
            }
            decision["pages"]["trending"] = {
                "name": "Tendencia",
                "template": "tendencia",
                "visual_count": 4,
                "visual_types": self._infer_page_visual_types("tendencia", 4),
                "date_field": self.date_fields[0] if self.date_fields else None,
            }
        elif has_categorical and measure_count >= 6:
            decision["page_count"] = 2
            decision["page_strategy"] = "categorical_focused"
            decision["reasoning"] = [
                f"OK: {measure_count} medidas detectadas",
                f"OK: {len(self.categorical_fields)} campos categoricos encontrados",
                "INFO: No hay campos fecha para tendencia",
                "Estrategia: 2 paginas (Ejecutiva, Comparativo)"
            ]
            decision["pages"]["executive"] = {
                "name": "Ejecutiva",
                "template": "kpi",
                "visual_count": 3,
                "visual_types": self._infer_page_visual_types("kpi", 3),
            }
            decision["pages"]["comparative"] = {
                "name": "Comparativo",
                "template": "territorio",
                "visual_count": 4,
                "visual_types": self._infer_page_visual_types("territorio", 4),
                "categorical_field": self.categorical_fields[0] if self.categorical_fields else None,
            }
        else:
            decision["page_count"] = 1
            decision["page_strategy"] = "mixed"
            decision["reasoning"].append(f"Página mixta con {measure_count} medidas")
            decision["pages"]["mixed"] = {
                "name": "Dashboard",
                "template": "comparacion",
                "visual_count": min(measure_count, 6),
                "visual_types": self._infer_page_visual_types("comparacion", min(measure_count, 6)),
            }
        
        return decision

    def _infer_page_visual_types(self, template: str, count: int) -> list[str]:
        """Decide tipos visuales por plantilla, evitando páginas de solo KPI."""
        if count <= 0:
            return []

        has_date = len(self.date_fields) > 0
        has_cat = len(self.categorical_fields) > 0
        t = str(template or "kpi").lower().strip()

        # Prioridades por plantilla.
        if t == "tendencia":
            pool = ["line", "line", "bar", "table", "card"]
        elif t in {"territorio", "comparacion"}:
            pool = ["bar", "bar", "table", "line", "card"]
        else:
            # Ejecutivo/KPI: máximo 1 tarjeta al inicio, luego análisis.
            pool = ["card", "line", "bar", "table", "bar", "line"]

        out: list[str] = []
        for candidate in pool:
            if len(out) >= count:
                break
            if candidate == "line" and not has_date:
                continue
            if candidate == "bar" and not has_cat:
                continue
            out.append(candidate)

        # Completa con card solo si no hay alternativa.
        while len(out) < count:
            if has_cat and out.count("bar") < 2:
                out.append("bar")
            elif has_date and out.count("line") < 2:
                out.append("line")
            elif "table" not in out:
                out.append("table")
            else:
                out.append("card")

        # Límite defensivo: no más de 2 KPIs por página.
        card_positions = [i for i, v in enumerate(out) if v == "card"]
        if len(card_positions) > 2:
            for idx in card_positions[2:]:
                if has_cat:
                    out[idx] = "bar"
                elif has_date:
                    out[idx] = "line"
                else:
                    out[idx] = "table"

        return out[:count]


def _build_line_visual(visual_id: str, x: int, y: int, w: int, h: int, idx: int, visual_info: dict, date_field: tuple[str, str] | None = None) -> dict:
    """Construye una visualización de línea para tendencias."""
    table = _sanitize_identifier(str(visual_info.get("table", "")))
    field = _sanitize_identifier(str(visual_info.get("field", "")))
    is_measure = visual_info.get("is_measure", False)
    
    if not table or not field:
        return _build_card_visual(visual_id, x, y, w, h, idx, visual_info)
    
    visual = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json",
        "name": visual_id,
        "position": {
            "x": x,
            "y": y,
            "z": 10 + idx,
            "width": w,
            "height": h,
            "tabOrder": idx,
        },
        "visual": {
            "visualType": "lineChart",
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [
                            {
                                "field": {
                                    "Measure" if is_measure else "Column": {
                                        "Expression": {"SourceRef": {"Entity": table}},
                                        "Property": field,
                                    }
                                },
                                "queryRef": f"{table}.{field}",
                            }
                        ]
                    }
                }
            }
        }
    }
    
    # Agregar eje X con fecha si está disponible
    if date_field:
        date_table, date_field_name = date_field
        visual["visual"]["query"]["queryState"]["Category"] = {
            "projections": [
                {
                    "field": {
                        "Column": {
                            "Expression": {"SourceRef": {"Entity": date_table}},
                            "Property": date_field_name,
                        }
                    },
                    "queryRef": f"{date_table}.{date_field_name}",
                }
            ]
        }
    
    return visual


def _build_bar_visual(visual_id: str, x: int, y: int, w: int, h: int, idx: int, visual_info: dict, category_field: tuple[str, str] | None = None) -> dict:
    """Construye una visualización de barras para comparaciones."""
    table = _sanitize_identifier(str(visual_info.get("table", "")))
    field = _sanitize_identifier(str(visual_info.get("field", "")))
    is_measure = visual_info.get("is_measure", False)
    
    if not table or not field:
        return _build_card_visual(visual_id, x, y, w, h, idx, visual_info)
    
    visual = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json",
        "name": visual_id,
        "position": {
            "x": x,
            "y": y,
            "z": 10 + idx,
            "width": w,
            "height": h,
            "tabOrder": idx,
        },
        "visual": {
            "visualType": "barChart",
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [
                            {
                                "field": {
                                    "Measure" if is_measure else "Column": {
                                        "Expression": {"SourceRef": {"Entity": table}},
                                        "Property": field,
                                    }
                                },
                                "queryRef": f"{table}.{field}",
                            }
                        ]
                    }
                }
            }
        }
    }
    
    # Agregar eje X con categoría si está disponible
    if category_field:
        cat_table, cat_field_name = category_field
        visual["visual"]["query"]["queryState"]["Category"] = {
            "projections": [
                {
                    "field": {
                        "Column": {
                            "Expression": {"SourceRef": {"Entity": cat_table}},
                            "Property": cat_field_name,
                        }
                    },
                    "queryRef": f"{cat_table}.{cat_field_name}",
                }
            ]
        }
    
    return visual


def _build_table_visual(visual_id: str, x: int, y: int, w: int, h: int, idx: int, fields: list[tuple[str, str, bool]]) -> dict:
    """Construye una tabla para detalle (lista de (tabla, campo, is_measure))."""
    visual = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json",
        "name": visual_id,
        "position": {
            "x": x,
            "y": y,
            "z": 10 + idx,
            "width": w,
            "height": h,
            "tabOrder": idx,
        },
        "visual": {
            "visualType": "table",
            "query": {
                "queryState": {
                    "Values": {
                        "projections": []
                    }
                }
            }
        }
    }
    
    # Agregar campos a la tabla
    for table, field, is_measure in fields:
        if table and field:
            visual["visual"]["query"]["queryState"]["Values"]["projections"].append({
                "field": {
                    "Measure" if is_measure else "Column": {
                        "Expression": {"SourceRef": {"Entity": _sanitize_identifier(table)}},
                        "Property": _sanitize_identifier(field),
                    }
                },
                "queryRef": f"{table}.{field}",
            })
    
    return visual


def _build_card_visual(visual_id: str, x: int, y: int, w: int, h: int, idx: int, visual_info: dict) -> dict:
    """Construye una tarjeta visual profesional, robusta y segura."""
    table = _sanitize_identifier(str(visual_info.get("table", "")))
    field = _sanitize_identifier(str(visual_info.get("field", "")))
    vis_type = visual_info.get("type", "card")
    is_measure = visual_info.get("is_measure", False)
    
    # Visualización vacía pero bien formada
    if vis_type == "blank" or not table or not field:
        return {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json",
            "name": visual_id,
            "position": {
                "x": x,
                "y": y,
                "z": 10 + idx,
                "width": w,
                "height": h,
                "tabOrder": idx,
            },
            "visual": {
                "visualType": "card",
            },
        }
    
    # Tarjeta con datos verificados
    visual = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json",
        "name": visual_id,
        "position": {
            "x": x,
            "y": y,
            "z": 10 + idx,
            "width": w,
            "height": h,
            "tabOrder": idx,
        },
        "visual": {
            "visualType": "card",
        },
    }
    
    # Construir referencia al campo
    if is_measure:
        # Es una medida: usar propiedad Measure
        visual["visual"]["query"] = {
            "queryState": {
                "Values": {
                    "projections": [
                        {
                            "field": {
                                "Measure": {
                                    "Expression": {
                                        "SourceRef": {
                                            "Entity": table,
                                        }
                                    },
                                    "Property": field,
                                }
                            },
                            "queryRef": f"{table}.{field}",
                        }
                    ]
                }
            }
        }
    else:
        # Es una columna: usar propiedad Column
        visual["visual"]["query"] = {
            "queryState": {
                "Values": {
                    "projections": [
                        {
                            "field": {
                                "Column": {
                                    "Expression": {
                                        "SourceRef": {
                                            "Entity": table,
                                        }
                                    },
                                    "Property": field,
                                }
                            },
                            "queryRef": f"{table}.{field}",
                        }
                    ]
                }
            }
        }
    
    return visual


def _build_layout(
    width: int,
    height: int,
    count: int,
    template: str,
    reserve_header: bool = True,
) -> list[tuple[int, int, int, int]]:
    if count <= 0:
        return []

    # Layout narrativo: una franja superior para el hero y una grilla limpia debajo.
    x0, y0 = 24, 56
    gx, gy = 18, 24

    if not reserve_header:
        if count <= 4:
            w, h = 590, 220
            grid_cols = 2
        else:
            grid_cols = 3
            w = int((width - (x0 * 2) - (gx * (grid_cols - 1))) / grid_cols)
            h = int((height - y0 - 36 - gy) / 2)

        positions: list[tuple[int, int, int, int]] = []
        for i in range(count):
            r = i // grid_cols
            c = i % grid_cols
            vx = x0 + c * (w + gx)
            vy = y0 + r * (h + gy)
            positions.append((vx, vy, w, h))
        return positions

    header_h = 162 if count > 1 else 180
    header_gap = 18 if count > 1 else 0
    body_top = y0 + header_h + header_gap
    body_height = max(180, height - body_top - 28)

    if count == 1:
        return [(x0, y0, width - (x0 * 2), header_h)]

    positions = [(x0, y0, width - (x0 * 2), header_h)]
    body_positions = _build_layout(width, body_height, count - 1, template, reserve_header=False)
    for vx, vy, vw, vh in body_positions:
        positions.append((vx, vy + body_top, vw, vh))
    return positions[:count]


def _normalize_visual_types(visual_types: list[str], count: int) -> list[str]:
    if count <= 0:
        return []
    safe = [str(v or "card").strip().lower() for v in (visual_types or [])]
    if not safe:
        safe = ["card"]
    while len(safe) < count:
        safe.append("card")
    return safe[:count]


def _build_structured_layout(
    width: int,
    height: int,
    count: int,
    template: str,
    visual_types: list[str],
    header_band: bool = True,
) -> list[tuple[int, int, int, int]]:
    if count <= 0:
        return []

    if header_band:
        return _build_layout(width=width, height=height, count=count, template=template, reserve_header=True)

    m = 24
    top = 52
    gx = 16
    gy = 20
    usable_w = width - (m * 2)

    # Estructura ejecutiva: KPIs arriba, lectura principal abajo.
    if template == "kpi" and count >= 4:
        kpi_h = 150
        third_w = int((usable_w - (gx * 2)) / 3)
        positions = [
            (m, top, third_w, kpi_h),
            (m + third_w + gx, top, third_w, kpi_h),
            (m + (third_w + gx) * 2, top, third_w, kpi_h),
            (m, top + kpi_h + gy, usable_w, max(280, height - top - kpi_h - gy - 32)),
        ]
        if count > 4:
            # Agrega piezas de soporte en una fila final.
            remaining = count - 4
            y2 = positions[3][1] + positions[3][3] + gy
            support_h = max(120, height - y2 - 24)
            support_w = int((usable_w - (gx * max(remaining - 1, 0))) / max(remaining, 1))
            for i in range(remaining):
                positions.append((m + i * (support_w + gx), y2, support_w, support_h))
        return positions[:count]

    # Estructura tendencia: gráfico principal arriba, comparativos debajo.
    if template == "tendencia" and count >= 4:
        big_h = 290
        half_w = int((usable_w - gx) / 2)
        y1 = top + big_h + gy
        h2 = int((height - y1 - gy - 24) / 2)
        positions = [
            (m, top, usable_w, big_h),
            (m, y1, half_w, h2),
            (m + half_w + gx, y1, half_w, h2),
            (m, y1 + h2 + gy, usable_w, h2),
        ]
        if count > 4:
            extra_h = h2
            extra_w = int((usable_w - gx) / 2)
            positions.append((m, y1 + h2 + gy, extra_w, extra_h))
            if count > 5:
                positions.append((m + extra_w + gx, y1 + h2 + gy, extra_w, extra_h))
        return positions[:count]

    # Estructura territorial/comparativa: dos gráficos fuertes y detalle abajo.
    if template in {"territorio", "comparacion"} and count >= 4:
        half_w = int((usable_w - gx) / 2)
        top_h = 250
        mid_h = 210
        positions = [
            (m, top, half_w, top_h),
            (m + half_w + gx, top, half_w, top_h),
            (m, top + top_h + gy, usable_w, mid_h),
            (m, top + top_h + gy + mid_h + gy, usable_w, max(120, height - (top + top_h + gy + mid_h + gy) - 24)),
        ]
        if count > 4:
            remain = count - 4
            yx = positions[3][1]
            ex_w = int((usable_w - gx) / 2)
            for i in range(remain):
                px = m if i % 2 == 0 else m + ex_w + gx
                py = yx + (0 if i < 2 else (positions[3][3] + gy))
                positions.append((px, py, ex_w, max(120, int(positions[3][3] / 2))))
        return positions[:count]

    return _build_layout(width=width, height=height, count=count, template=template)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-PbipPath", required=True, help="Ruta al archivo .pbip")
    parser.add_argument("-Verbose", default="0", help="Mostrar diagnóstico detallado")
    parser.add_argument("-NarrativeTemplate", default="auto", help="auto|kpi|tendencia|comparacion|territorio")
    parser.add_argument("-VisualCount", default="auto", help="Cantidad de visuales a generar (2-8) o 'auto'")
    parser.add_argument("-VisualStrategy", default="auto", help="auto|rule|llm")
    parser.add_argument("-OllamaModel", default="qwen3:8b", help="Modelo Ollama para decidir el plan visual")
    parser.add_argument("-OllamaBaseUrl", default="http://localhost:11434", help="URL base de Ollama local")
    parser.add_argument("-AllowHybridCustom", default="1", help="Permite decisiones html/deneb/textbox con fallback seguro (1|0)")
    parser.add_argument("-StrictDataBinding", default="1", help="Evita mezclar ejes de tablas distintas para no romper visuales (1|0)")
    args = parser.parse_args()

    pbip_path = Path(_clean_path_value(args.PbipPath)).expanduser()
    verbose = args.Verbose.lower() in {"1", "true", "yes"}
    requested_template = str(args.NarrativeTemplate or "auto").strip().lower()
    if requested_template not in NARRATIVE_TEMPLATES:
        requested_template = "auto"
    visual_strategy = str(args.VisualStrategy or "auto").strip().lower()
    if visual_strategy not in VISUAL_STRATEGIES:
        visual_strategy = "auto"
    allow_hybrid_custom = str(args.AllowHybridCustom).strip().lower() in {"1", "true", "yes"}
    strict_data_binding = str(args.StrictDataBinding).strip().lower() in {"1", "true", "yes"}
    
    report_def = _resolve_report_definition(pbip_path)
    pages_meta_path = report_def / "pages" / "pages.json"
    
    if not pages_meta_path.exists():
        raise RuntimeError(f"No existe pages.json en: {pages_meta_path}")
    
    pages_meta = _read_json(pages_meta_path)
    pages_meta, removed = _remove_existing_autovis_page(report_def, pages_meta, "AutoVis IA")
    
    # Analizar el modelo
    tables_dir = _resolve_semantic_tables_dir(pbip_path)
    analyzer = ModelAnalyzer(tables_dir)
    
    # ===== NUEVA LÓGICA: Decidir estrategia adaptativa =====
    rule_decision = analyzer.decide_page_strategy()
    llm_plan = None
    if visual_strategy in {"auto", "llm"}:
        llm_plan = _request_ollama_visual_plan(analyzer, model=args.OllamaModel, base_url=args.OllamaBaseUrl)

    if visual_strategy == "llm" and llm_plan and llm_plan.get("ok"):
        decision = llm_plan
        decision_source = "llm"
    elif visual_strategy == "rule":
        decision = rule_decision
        decision_source = "rule"
    elif llm_plan and llm_plan.get("ok"):
        decision = llm_plan
        decision_source = "llm"
    else:
        decision = rule_decision
        decision_source = "rule"
    
    if verbose:
        print("=" * 60)
        print("ANÁLISIS DEL MODELO:")
        print(f"  - Tablas: {len(analyzer.tables)}")
        print(f"  - Medidas: {len(analyzer.measures)}")
        print(f"  - Campos fecha: {len(analyzer.date_fields)}")
        print(f"  - Campos categóricos: {len(analyzer.categorical_fields)}")
        print()
        print("DECISIÓN AUTOMÁTICA:")
        print(f"  - Estrategia: {decision['page_strategy']}")
        print(f"  - Fuente de decision: {decision_source}")
        print(f"  - Páginas a generar: {decision['page_count']}")
        for reason in decision['reasoning']:
            print(f"    {reason}")
        print("=" * 60)
    
    # Obtener dimensiones de página
    width, height = 1280, 720
    page_order = list(pages_meta.get("pageOrder") or [])
    if page_order:
        sample_page = report_def / "pages" / page_order[0] / "page.json"
        if sample_page.exists():
            sample = _read_json(sample_page)
            width = int(sample.get("width") or width)
            height = int(sample.get("height") or height)
    
    # Generar cada página según decisión
    new_page_ids = []
    pages_created = {}
    custom_visual_intents: list[dict[str, Any]] = []
    
    for page_key, page_spec in decision['pages'].items():
        page_name = page_spec.get("name", page_key)
        page_template = page_spec.get("template", "kpi")
        visual_count = page_spec.get("visual_count", 4)
        visual_types = _normalize_visual_types(page_spec.get("visual_types", ["card"] * visual_count), visual_count)
        hybrid_mode = bool(page_spec.get("hybrid_mode") or any(v in HYBRID_VISUAL_TYPES for v in visual_types))
        page_story = _sanitize_identifier(str(page_spec.get("narrative") or _storyline_for_page(page_template, page_name, [])))
        date_field = page_spec.get("date_field")
        categorical_field = page_spec.get("categorical_field")
        
        # Generar ID de página y crear directorio
        new_page_id = _make_id()
        page_dir = report_def / "pages" / new_page_id
        visuals_dir = page_dir / "visuals"
        visuals_dir.mkdir(parents=True, exist_ok=True)
        
        # Obtener visualizaciones para esta página
        visuals_info = analyzer.get_narrative_visuals(template=page_template, limit=visual_count)
        
        # Crear metadata de página
        page_json = {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
            "name": new_page_id,
            "displayName": page_name,
            "displayOption": "FitToPage",
            "height": height,
            "width": width,
            "annotations": [
                {"name": "autovis.version", "value": "smart.v3"},
                {"name": "autovis.strategy", "value": decision['page_strategy']},
                {"name": "autovis.strategy_source", "value": decision_source},
                {"name": "autovis.template", "value": page_template},
                {"name": "autovis.visual_count", "value": str(len(visuals_info))},
                {"name": "autovis.page_key", "value": page_key},
                {"name": "autovis.page_story", "value": page_story},
                {"name": "autovis.hybrid_mode", "value": "true" if hybrid_mode else "false"},
            ],
        }
        _write_json(page_dir / "page.json", page_json)
        
        # Crear visualizaciones con tipos variados
        positions = _build_structured_layout(
            width=width,
            height=height,
            count=len(visuals_info),
            template=page_template,
            visual_types=visual_types,
            header_band=True,
        )
        
        for i, visual_info in enumerate(visuals_info):
            vid = _make_id()
            vdir = visuals_dir / vid
            vdir.mkdir(parents=True, exist_ok=True)
            
            vx, vy, w, h = positions[i]
            planned_type = visual_types[i] if i < len(visual_types) else "card"
            suggested_type = str(visual_info.get("type") or "card").lower()

            # Hero inteligente: si hay soporte, prioriza visual analítico en vez de card plano.
            if i == 0:
                if page_template == "tendencia" and is_measure and analyzer.pick_best_date_field_for_table(source_table):
                    visual_type = "line"
                elif page_template in {"territorio", "comparacion"} and is_measure and analyzer.pick_best_category_field_for_table(source_table):
                    visual_type = "bar"
                else:
                    visual_type = "card"
            elif planned_type in HYBRID_VISUAL_TYPES:
                visual_type = "card"
                if allow_hybrid_custom:
                    custom_visual_intents.append(
                        {
                            "page": page_name,
                            "page_id": new_page_id,
                            "slot": i,
                            "planned_type": planned_type,
                            "fallback_visual": "card",
                            "source_table": source_table,
                            "source_field": str(visual_info.get("field") or ""),
                            "notes": "LLM solicito custom visual; fallback seguro aplicado.",
                        }
                    )
            else:
                # Si la planificación cae en card, usa la sugerencia semántica de la medida.
                visual_type = suggested_type if planned_type == "card" else planned_type

            source_table = str(visual_info.get("table") or "")
            is_measure = bool(visual_info.get("is_measure"))
            line_axis = analyzer.pick_best_date_field_for_table(source_table)
            bar_axis = analyzer.pick_best_category_field_for_table(source_table)

            if not is_measure:
                # Columnas de texto/fecha sin medida agregada: evita line/bar inválidos.
                visual_type = "card" if i == 0 else "table"

            if strict_data_binding:
                # Modo anti-roturas: evita usar ejes de otras tablas en line/bar.
                if line_axis and line_axis[0] != source_table:
                    line_axis = None
                if bar_axis and bar_axis[0] != source_table:
                    bar_axis = None
            
            # Construir visual del tipo especificado
            if visual_type == "line" and is_measure and line_axis:
                vjson = _build_line_visual(vid, vx, vy, w, h, i, visual_info, line_axis)
            elif visual_type == "bar" and is_measure and bar_axis:
                vjson = _build_bar_visual(vid, vx, vy, w, h, i, visual_info, bar_axis)
            elif visual_type == "table":
                # Para tabla, solo campos de la misma tabla para evitar cruces sin relación.
                fields = [(visual_info['table'], visual_info['field'], visual_info['is_measure'])]
                fields.extend(
                    analyzer.get_table_detail_fields(
                        source_table,
                        max_cols=2,
                        exclude_field=str(visual_info.get("field") or ""),
                    )
                )
                vjson = _build_table_visual(vid, vx, vy, w, h, i, fields)
            else:
                # Default: card
                vjson = _build_card_visual(vid, vx, vy, w, h, i, visual_info)
            
            _write_json(vdir / "visual.json", vjson)
            
            if verbose:
                print(f"  [{page_name}] Visual {i+1}: {visual_info['label']} ({visual_type})")
        
        new_page_ids.append(new_page_id)
        pages_created[page_key] = {
            "page_id": new_page_id,
            "page_name": page_name,
            "visual_count": len(visuals_info),
            "template": page_template,
            "narrative": page_story,
            "hybrid_mode": hybrid_mode,
        }
    
    # Actualizar orden de páginas
    for page_id in new_page_ids:
        if page_id not in page_order:
            page_order.append(page_id)
    pages_meta["pageOrder"] = page_order
    pages_meta["activePageName"] = new_page_ids[0] if new_page_ids else None
    pages_meta = _sync_pages_metadata(report_def, pages_meta)
    _write_json(pages_meta_path, pages_meta)
    
    # Guardar decisión en JSON para auditoría
    decision_file = pbip_path.parent / f"{pbip_path.stem}_autovis_decision.json"
    hybrid_plan_file = pbip_path.parent / f"{pbip_path.stem}_autovis_custom_visual_plan.json"

    if allow_hybrid_custom:
        _write_json(
            hybrid_plan_file,
            {
                "pbip_path": str(pbip_path),
                "strategy_source": decision_source,
                "custom_visual_intents": custom_visual_intents,
                "notes": [
                    "Plan de decisiones LLM para html/deneb/textbox.",
                    "Se mantiene fallback a visual nativo para evitar dashboards rotos.",
                ],
            },
        )

    decision_output = {
        "timestamp": str(Path(__file__).stat().st_mtime),
        "pbip_path": str(pbip_path),
        "strategy": decision,
        "pages_created": pages_created,
        "removed_pages": removed,
        "strict_data_binding": strict_data_binding,
        "allow_hybrid_custom": allow_hybrid_custom,
        "custom_visual_intents": len(custom_visual_intents),
    }
    _write_json(decision_file, decision_output)
    
    # Salida para auditoría
    print("AUTOVIS_SMART_OK: SI")
    print(f"PAGINAS_CREADAS: {len(new_page_ids)}")
    print(f"ESTRATEGIA: {decision['page_strategy']}")
    print(f"FUENTE_DECISION: {decision_source}")
    print(f"TABLAS_DETECTADAS: {len(analyzer.tables)}")
    print(f"MEDIDAS_DISPONIBLES: {len(analyzer.measures)}")
    print(f"CAMPOS_FECHA: {len(analyzer.date_fields)}")
    print(f"CAMPOS_CATEGORICOS: {len(analyzer.categorical_fields)}")
    print(f"PAGINAS_REMOVIDAS: {removed}")
    print(f"DECISION_GUARDADA: {decision_file}")
    if allow_hybrid_custom:
        print(f"PLAN_CUSTOM_GUARDADO: {hybrid_plan_file}")
    print(f"STRICT_DATA_BINDING: {strict_data_binding}")
    
    return 0


def _remove_existing_autovis_page(report_def: Path, pages_meta: dict, display_name: str) -> tuple[dict, int]:
    """Elimina páginas AutoVis anteriores (por nombre o anotaciones autovis.*)."""
    pages_dir = report_def / "pages"
    removed = 0
    current_order = list(pages_meta.get("pageOrder") or [])
    new_order: list[str] = []
    
    for page_id in current_order:
        page_json_path = pages_dir / page_id / "page.json"
        if not page_json_path.exists():
            continue
        
        try:
            page_obj = _read_json(page_json_path)
        except Exception:
            new_order.append(page_id)
            continue
        
        page_name = str(page_obj.get("displayName") or "").strip().lower()
        annotations = page_obj.get("annotations") or []
        has_autovis_annotation = any(
            str(item.get("name") or "").strip().lower().startswith("autovis.")
            for item in annotations
            if isinstance(item, dict)
        )

        if page_name == display_name.strip().lower() or has_autovis_annotation:
            page_folder = pages_dir / page_id
            if page_folder.exists() and page_folder.is_dir():
                for child in sorted(page_folder.rglob("*"), reverse=True):
                    if child.is_file():
                        child.unlink(missing_ok=True)
                    elif child.is_dir():
                        child.rmdir()
                page_folder.rmdir()
            removed += 1
            continue
        
        new_order.append(page_id)
    
    pages_meta["pageOrder"] = new_order
    active = str(pages_meta.get("activePageName") or "")
    if active not in new_order:
        pages_meta["activePageName"] = new_order[0] if new_order else ""
    
    return pages_meta, removed


if __name__ == "__main__":
    raise SystemExit(main())
