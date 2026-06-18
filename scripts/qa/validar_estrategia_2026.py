#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

BASE = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")
CSV_VALIDACION = BASE / "data" / "reference" / "powerbi_consultas_validacion_excel_2026.csv"


def _resolve_excel_fuente() -> Path:
    source_dir = BASE / "data" / "source"
    candidates = sorted(
        source_dir.glob("Reporte de actividades equipo social 2026*.xlsx"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if candidates:
        return candidates[0]
    return source_dir / "Reporte de actividades equipo social 2026.xlsx"


EXCEL_FUENTE = _resolve_excel_fuente()
OUT_CSV = BASE / "data" / "reference" / "validacion_estrategia_resultados_2026.csv"
OUT_JSON = BASE / "data" / "reference" / "validacion_estrategia_resumen_2026.json"


AGREGACIONES_VALIDAS = {"SUM", "MIN", "COUNT"}


def _parse_sheet1_column(query_ref: str) -> str | None:
    q = str(query_ref or "").strip()
    if q.startswith("Sum(Sheet1.") and q.endswith(")"):
        return q[len("Sum(Sheet1.") : -1]
    if q.startswith("Min(Sheet1.") and q.endswith(")"):
        return q[len("Min(Sheet1.") : -1]
    if q.startswith("Count(Sheet1.") and q.endswith(")"):
        return q[len("Count(Sheet1.") : -1]
    return None


def _apply_filters(df: pd.DataFrame, filter_cols: str, filter_vals: str) -> tuple[pd.DataFrame, str]:
    cols = [c.strip() for c in str(filter_cols or "").split("|") if c.strip()]
    vals = [v.strip() for v in str(filter_vals or "").split("|") if v.strip()]

    if not cols or not vals:
        return df, "SIN_FILTRO"

    if len(cols) == 1:
        col = cols[0]
        if col not in df.columns:
            return df.iloc[0:0], f"ERROR_FILTRO_COL_NO_EXISTE:{col}"
        # un filtro, varios valores => IN
        out = df[df[col].astype(str).str.strip().isin(vals)]
        return out, "OK"

    # multiples columnas (se toma AND posicional)
    out = df
    for i, col in enumerate(cols):
        if col not in out.columns:
            return out.iloc[0:0], f"ERROR_FILTRO_COL_NO_EXISTE:{col}"
        if i >= len(vals):
            break
        out = out[out[col].astype(str).str.strip() == vals[i]]
    return out, "OK"


def main() -> None:
    df_val = pd.read_csv(CSV_VALIDACION)
    df_val["pagina"] = df_val["pagina"].astype(str).str.strip()

    df = df_val[
        (df_val["pagina"] == "Estrategia")
        & (df_val["visual_tipo"].astype(str).str.lower() == "card")
        & (df_val["agregacion"].astype(str).str.upper().isin(AGREGACIONES_VALIDAS))
    ].copy()

    df_excel = pd.read_excel(EXCEL_FUENTE, sheet_name="Sheet1")

    rows: list[dict[str, object]] = []
    for _, r in df.iterrows():
        query_ref = str(r.get("query_ref", ""))
        agg = str(r.get("agregacion", "")).upper()
        fcols = str(r.get("filtro_columnas", "") or "")
        fvals = str(r.get("filtro_valores", "") or "")

        if "Base completa para PBI" in query_ref:
            rows.append(
                {
                    "pagina": "Estrategia",
                    "visual_name": r.get("visual_name"),
                    "query_ref": query_ref,
                    "agregacion": agg,
                    "filtro_columnas": fcols,
                    "filtro_valores": fvals,
                    "valor_obtenido": None,
                    "estado_confianza": "NO_AUDITABLE_BASE_COMPLETA",
                    "nota": "Consulta apunta a Base completa para PBI, no directa a Sheet1",
                }
            )
            continue

        col = _parse_sheet1_column(query_ref)
        if not col:
            rows.append(
                {
                    "pagina": "Estrategia",
                    "visual_name": r.get("visual_name"),
                    "query_ref": query_ref,
                    "agregacion": agg,
                    "filtro_columnas": fcols,
                    "filtro_valores": fvals,
                    "valor_obtenido": None,
                    "estado_confianza": "NO_PARSEABLE",
                    "nota": "No se pudo parsear columna Sheet1 desde query_ref",
                }
            )
            continue

        if col not in df_excel.columns:
            rows.append(
                {
                    "pagina": "Estrategia",
                    "visual_name": r.get("visual_name"),
                    "query_ref": query_ref,
                    "agregacion": agg,
                    "filtro_columnas": fcols,
                    "filtro_valores": fvals,
                    "valor_obtenido": None,
                    "estado_confianza": "ERROR_COLUMNA_NO_EXISTE",
                    "nota": f"Columna no existe en Sheet1: {col}",
                }
            )
            continue

        df_f, filter_status = _apply_filters(df_excel, fcols, fvals)
        if filter_status.startswith("ERROR"):
            rows.append(
                {
                    "pagina": "Estrategia",
                    "visual_name": r.get("visual_name"),
                    "query_ref": query_ref,
                    "agregacion": agg,
                    "filtro_columnas": fcols,
                    "filtro_valores": fvals,
                    "valor_obtenido": None,
                    "estado_confianza": filter_status,
                    "nota": "Error aplicando filtro",
                }
            )
            continue

        if agg == "SUM":
            v = pd.to_numeric(df_f[col], errors="coerce").sum()
        elif agg == "MIN":
            num = pd.to_numeric(df_f[col], errors="coerce")
            v = num.min() if not num.dropna().empty else None
        elif agg == "COUNT":
            v = int(df_f[col].count())
        else:
            v = None

        rows.append(
            {
                "pagina": "Estrategia",
                "visual_name": r.get("visual_name"),
                "query_ref": query_ref,
                "agregacion": agg,
                "filtro_columnas": fcols,
                "filtro_valores": fvals,
                "valor_obtenido": v,
                "estado_confianza": "VALIDADO",
                "nota": f"Filas evaluadas: {len(df_f)}",
            }
        )

    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    summary = {
        "total_consultas": int(len(out_df)),
        "validadas": int((out_df["estado_confianza"] == "VALIDADO").sum()),
        "no_auditables": int((out_df["estado_confianza"].str.startswith("NO_AUDITABLE", na=False)).sum()),
        "errores": int((out_df["estado_confianza"].str.startswith("ERROR", na=False)).sum()),
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"OK CSV: {OUT_CSV}")
    print(f"OK JSON: {OUT_JSON}")
    print(summary)


if __name__ == "__main__":
    main()
