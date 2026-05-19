from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


MODEL_PATH = Path("data/model/Modelo_Reporte_Paginas_2026.xlsx")
SHEET_FACT = "Hecho_Participacion_General"
SHEET_COMUNA = "Dim_Comuna"
OUT_DIR = Path("entregables") / "reportes_2025"
OUT_FILE = OUT_DIR / "reporte_participantes_2025_por_comuna_instancia_general.pdf"
BASE_EQUIVALENCIA_COMUNAS = 26738

VALUE_COLUMNS = [
    "participantes",
    "mujeres",
    "hombres",
    "pri_infanc",
    "nino_adole",
    "juventud",
    "adulto",
    "adulto_may",
]

RENAMES = {
    "participantes": "Participantes",
    "mujeres": "Mujeres",
    "hombres": "Hombres",
    "pri_infanc": "Primera infancia",
    "nino_adole": "Nino/adolescente",
    "juventud": "Juventud",
    "adulto": "Adulto",
    "adulto_may": "Adulto mayor",
}


def _safe_int_series(df: pd.DataFrame, cols: Iterable[str]) -> pd.DataFrame:
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


def _clean_text(value: object, default: str) -> str:
    if pd.isna(value):
        return default
    text = str(value).strip()
    return text if text else default


def _format_number(value: object) -> str:
    try:
        return f"{int(value):,}".replace(",", ".")
    except Exception:
        return str(value)


def _format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def _parse_percent_to_ratio(value: object) -> float:
    text = str(value).strip().replace("%", "").replace(",", ".")
    if not text:
        return 0.0
    try:
        return float(text) / 100.0
    except Exception:
        return 0.0


def _split_integer_total(total: int, n: int) -> list[int]:
    if n <= 0:
        return []
    base = total // n
    remainder = total % n
    return [base + (1 if i < remainder else 0) for i in range(n)]


def _to_table_data(df: pd.DataFrame) -> list[list[str]]:
    headers = [str(c) for c in df.columns]
    rows: list[list[str]] = [headers]
    numeric_cols = set(df.select_dtypes(include=["number"]).columns.tolist())
    for _, row in df.iterrows():
        values = []
        for col in df.columns:
            val = row[col]
            values.append(_format_number(val) if col in numeric_cols else str(val))
        rows.append(values)
    return rows


def _build_styled_table(df: pd.DataFrame, col_widths: list[float] | None = None) -> Table:
    data = _to_table_data(df)
    table = Table(data, colWidths=col_widths, repeatRows=1)
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#EAF2F8")]),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
    )
    table.setStyle(style)
    return table


def _draw_page_number(canvas, doc) -> None:
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(28.7 * cm, 1.0 * cm, f"Pagina {doc.page}")


def _load_and_aggregate() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, int]]:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"No existe el archivo fuente: {MODEL_PATH}")

    fact = pd.read_excel(MODEL_PATH, sheet_name=SHEET_FACT)
    fact.columns = [str(c).strip() for c in fact.columns]
    required = ["anio", "comuna_cod", "instancia", *VALUE_COLUMNS]
    missing_cols = [c for c in required if c not in fact.columns]
    if missing_cols:
        raise ValueError(f"Faltan columnas requeridas en {SHEET_FACT}: {missing_cols}")

    fact = _safe_int_series(fact, VALUE_COLUMNS)
    fact["anio"] = pd.to_numeric(fact["anio"], errors="coerce").fillna(0).astype(int)
    data_2025 = fact[fact["anio"] == 2025].copy()

    xl = pd.ExcelFile(MODEL_PATH)
    if SHEET_COMUNA in xl.sheet_names:
        dim_comuna = pd.read_excel(MODEL_PATH, sheet_name=SHEET_COMUNA)
        dim_comuna.columns = [str(c).strip() for c in dim_comuna.columns]
        if "comuna_cod" in dim_comuna.columns and "comuna_nombre" in dim_comuna.columns:
            dim_map = dim_comuna[["comuna_cod", "comuna_nombre"]].dropna(subset=["comuna_cod"]).copy()
            dim_map["comuna_cod"] = pd.to_numeric(dim_map["comuna_cod"], errors="coerce").fillna(-1).astype(int)
            dim_map["comuna_nombre"] = dim_map["comuna_nombre"].map(lambda x: _clean_text(x, "SIN NOMBRE"))
            data_2025["comuna_cod"] = pd.to_numeric(data_2025["comuna_cod"], errors="coerce").fillna(-1).astype(int)
            data_2025 = data_2025.merge(dim_map, on="comuna_cod", how="left")
        else:
            data_2025["comuna_nombre"] = "SIN NOMBRE"
    else:
        data_2025["comuna_nombre"] = "SIN NOMBRE"

    data_2025["comuna_nombre"] = data_2025["comuna_nombre"].map(lambda x: _clean_text(x, "SIN NOMBRE"))
    data_2025["instancia"] = data_2025["instancia"].map(lambda x: _clean_text(x, "SIN INSTANCIA"))

    # Excluye comuna 99 del reporte por comuna y redistribuye sus valores entre todas las otras comunas.
    data_2025["comuna_cod"] = pd.to_numeric(data_2025["comuna_cod"], errors="coerce").fillna(-1).astype(int)
    mask_99 = data_2025["comuna_cod"] == 99
    redistribucion_99 = data_2025.loc[mask_99, VALUE_COLUMNS].sum() if mask_99.any() else pd.Series(0, index=VALUE_COLUMNS)
    data_2025_sin_99 = data_2025.loc[~mask_99].copy()

    general = data_2025[VALUE_COLUMNS].sum().to_frame().T.rename(columns=RENAMES)
    general.insert(0, "Nivel", "General")

    por_instancia = (
        data_2025.groupby("instancia", dropna=False)[VALUE_COLUMNS]
        .sum()
        .reset_index()
        .rename(columns={"instancia": "Instancia", **RENAMES})
        .sort_values(by="Participantes", ascending=False)
    )

    por_comuna = (
        data_2025_sin_99.groupby(["comuna_cod", "comuna_nombre"], dropna=False)[VALUE_COLUMNS]
        .sum()
        .reset_index()
        .rename(columns={"comuna_cod": "Comuna cod", "comuna_nombre": "Comuna", **RENAMES})
        .sort_values(by=["Comuna cod", "Comuna"], ascending=[True, True])
    )

    if mask_99.any() and not por_comuna.empty:
        por_comuna = por_comuna.reset_index(drop=True)
        n_comunas = len(por_comuna)
        for src_col, dst_col in RENAMES.items():
            distribucion = _split_integer_total(int(redistribucion_99[src_col]), n_comunas)
            por_comuna[dst_col] = por_comuna[dst_col].astype(int) + pd.Series(distribucion)

    total_general_participantes = int(general["Participantes"].iloc[0]) if not general.empty else 0
    total_comunas_participantes = int(por_comuna["Participantes"].sum()) if not por_comuna.empty else 0

    def _enriquecer_porcentajes(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        if total_general_participantes > 0:
            out["% Participantes vs total general"] = (
                out["Participantes"] / total_general_participantes
            ).map(_format_percent)
        else:
            out["% Participantes vs total general"] = "0.00%"

        if total_comunas_participantes > 0:
            out["% Participantes vs total comunas"] = (
                out["Participantes"] / total_comunas_participantes
            ).map(_format_percent)
        else:
            out["% Participantes vs total comunas"] = "0.00%"
        return out

    general["% Participantes vs total general"] = "100.00%"
    general["% Participantes vs total comunas"] = (
        _format_percent(total_general_participantes / total_comunas_participantes)
        if total_comunas_participantes > 0
        else "0.00%"
    )
    por_instancia = _enriquecer_porcentajes(por_instancia)
    por_comuna = _enriquecer_porcentajes(por_comuna)

    metrics = {
        "registros_2025": int(len(data_2025)),
        "participantes": total_general_participantes,
        "mujeres": int(general["Mujeres"].iloc[0]) if not general.empty else 0,
        "hombres": int(general["Hombres"].iloc[0]) if not general.empty else 0,
        "instancias": int(por_instancia.shape[0]),
        "comunas": int(por_comuna.shape[0]),
        "total_comunas_participantes": total_comunas_participantes,
    }
    return general, por_instancia, por_comuna, metrics


def build_pdf() -> None:
    general, por_instancia, por_comuna, metrics = _load_and_aggregate()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    indicadores_generales = [
        "Participantes",
        "Mujeres",
        "Hombres",
        "Primera infancia",
        "Nino/adolescente",
        "Juventud",
        "Adulto",
        "Adulto mayor",
    ]
    total_participantes_general = int(general["Participantes"].iloc[0]) if not general.empty else 0
    rows_general_proyectada: list[dict[str, object]] = []
    for indicador in indicadores_generales:
        valor = int(general[indicador].iloc[0]) if not general.empty else 0
        ratio = (valor / total_participantes_general) if total_participantes_general > 0 else 0.0
        rows_general_proyectada.append(
            {
                "Indicador": indicador,
                "Valor general 2025": valor,
                "% sobre total general": _format_percent(ratio),
                "Base referencia": BASE_EQUIVALENCIA_COMUNAS,
                "Valor proyectado base 26738": int(round(ratio * BASE_EQUIVALENCIA_COMUNAS, 0)),
            }
        )
    tabla_general_proyectada = pd.DataFrame(rows_general_proyectada)

    tabla_equivalencia = por_comuna[["Comuna cod", "Comuna", "% Participantes vs total comunas"]].copy()
    tabla_equivalencia["Base referencia"] = BASE_EQUIVALENCIA_COMUNAS
    tabla_equivalencia["Participantes equivalentes (base 26738)"] = (
        tabla_equivalencia["% Participantes vs total comunas"]
        .map(_parse_percent_to_ratio)
        .mul(BASE_EQUIVALENCIA_COMUNAS)
        .round(0)
        .astype(int)
    )

    grupos_etarios = [
        "Primera infancia",
        "Nino/adolescente",
        "Juventud",
        "Adulto",
        "Adulto mayor",
    ]
    tablas_equivalencia_etarios: list[tuple[str, pd.DataFrame]] = []
    for grupo in grupos_etarios:
        total_grupo = int(por_comuna[grupo].sum()) if not por_comuna.empty else 0
        tabla_grupo = por_comuna[["Comuna cod", "Comuna", grupo]].copy()
        tabla_grupo[f"% {grupo} vs total comunas"] = (
            (tabla_grupo[grupo] / total_grupo).fillna(0.0).map(_format_percent)
            if total_grupo > 0
            else "0.00%"
        )
        tabla_grupo["Base referencia"] = BASE_EQUIVALENCIA_COMUNAS
        tabla_grupo[f"{grupo} equivalentes (base 26738)"] = (
            tabla_grupo[f"% {grupo} vs total comunas"]
            .map(_parse_percent_to_ratio)
            .mul(BASE_EQUIVALENCIA_COMUNAS)
            .round(0)
            .astype(int)
        )
        tablas_equivalencia_etarios.append((grupo, tabla_grupo))

    doc = SimpleDocTemplate(
        str(OUT_FILE),
        pagesize=landscape(A4),
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.5 * cm,
        title="Reporte Participantes 2025",
        author="Dashboard DAGRD",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1F4E78"),
        alignment=1,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2E4053"),
        alignment=1,
    )
    section_style = ParagraphStyle(
        "SectionCustom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        textColor=colors.HexColor("#1F4E78"),
        spaceAfter=6,
        spaceBefore=10,
    )
    body_style = ParagraphStyle(
        "BodyCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
    )

    story = [
        Paragraph("REPORTE DE PARTICIPANTES 2025", title_style),
        Spacer(1, 0.2 * cm),
        Paragraph("Consolidado por nivel general, instancias y comunas", subtitle_style),
        Spacer(1, 0.5 * cm),
        Paragraph("Resumen ejecutivo", section_style),
        Paragraph(
            (
                f"Registros analizados para 2025: <b>{_format_number(metrics['registros_2025'])}</b><br/>"
                f"Participantes totales: <b>{_format_number(metrics['participantes'])}</b><br/>"
                f"Mujeres: <b>{_format_number(metrics['mujeres'])}</b> | "
                f"Hombres: <b>{_format_number(metrics['hombres'])}</b><br/>"
                f"Instancias reportadas: <b>{_format_number(metrics['instancias'])}</b> | "
                f"Comunas reportadas: <b>{_format_number(metrics['comunas'])}</b><br/>"
                f"Total participantes en tabla de comunas: <b>{_format_number(metrics['total_comunas_participantes'])}</b>"
            ),
            body_style,
        ),
        Spacer(1, 0.3 * cm),
        Paragraph("Tabla general (2025)", section_style),
        _build_styled_table(
            general,
            col_widths=[
                2.0 * cm,
                2.0 * cm,
                1.8 * cm,
                1.8 * cm,
                2.4 * cm,
                2.4 * cm,
                1.8 * cm,
                1.8 * cm,
                2.2 * cm,
                3.1 * cm,
                3.1 * cm,
            ],
        ),
        Spacer(1, 0.3 * cm),
        Paragraph("Tabla general proyectada a base 26738 (sin desglose por comuna)", section_style),
        _build_styled_table(tabla_general_proyectada),
        PageBreak(),
        Paragraph("Tabla por instancia (2025)", section_style),
        _build_styled_table(por_instancia),
        PageBreak(),
        Paragraph("Tabla por comuna (2025)", section_style),
        _build_styled_table(por_comuna),
        PageBreak(),
        Paragraph(
            "Tabla de equivalencia por comuna (porcentaje vs total comunas aplicado a base 26738)",
            section_style,
        ),
        _build_styled_table(tabla_equivalencia),
    ]

    for grupo, tabla_grupo in tablas_equivalencia_etarios:
        story.extend(
            [
                PageBreak(),
                Paragraph(
                    f"Equivalencia por comuna para {grupo} (base 26738)",
                    section_style,
                ),
                _build_styled_table(tabla_grupo),
            ]
        )

    doc.build(story, onFirstPage=_draw_page_number, onLaterPages=_draw_page_number)
    print(f"OK: PDF generado en {OUT_FILE}")
    print(
        "Resumen: "
        f"registros_2025={metrics['registros_2025']}, "
        f"participantes={metrics['participantes']}, "
        f"instancias={metrics['instancias']}, comunas={metrics['comunas']}"
    )


if __name__ == "__main__":
    build_pdf()
