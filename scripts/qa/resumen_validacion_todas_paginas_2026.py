#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

BASE = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")
CSV_VALIDACION = BASE / "data" / "reference" / "powerbi_consultas_validacion_excel_2026.csv"
OUT_CSV = BASE / "data" / "reference" / "resumen_validacion_todas_paginas_2026.csv"
OUT_JSON = BASE / "data" / "reference" / "resumen_validacion_todas_paginas_2026.json"


def main() -> None:
    df = pd.read_csv(CSV_VALIDACION)
    df["pagina"] = df["pagina"].astype(str).str.strip()
    df["visual_tipo"] = df["visual_tipo"].astype(str).str.strip().str.lower()
    df["agregacion"] = df["agregacion"].astype(str).str.strip().str.upper()

    visuales_totales = df.groupby("pagina")["visual_name"].nunique().rename("total_visuales")

    mask_auditable = (
        (df["visual_tipo"] == "card")
        & (df["agregacion"].isin(["SUM", "MIN", "COUNT", "DISTINCTCOUNT"]))
        & (df["query_ref"].astype(str).str.len() > 0)
    )
    auditables = (
        df[mask_auditable]
        .groupby("pagina")["visual_name"]
        .nunique()
        .rename("auditables_auto")
    )

    resumen = pd.concat([visuales_totales, auditables], axis=1).fillna(0)
    resumen["auditables_auto"] = resumen["auditables_auto"].astype(int)
    resumen["total_visuales"] = resumen["total_visuales"].astype(int)
    resumen["no_auditables"] = resumen["total_visuales"] - resumen["auditables_auto"]
    resumen["cobertura_pct"] = (resumen["auditables_auto"] / resumen["total_visuales"] * 100).round(1)

    resumen = resumen.reset_index().sort_values("total_visuales", ascending=False)
    resumen.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    top_manual = (
        df[(df["visual_tipo"] == "card") & (df["agregacion"].isin(["SUM", "COUNT", "DISTINCTCOUNT"]))]
        [["pagina", "visual_name", "query_ref", "filtro_columnas", "filtro_valores"]]
        .drop_duplicates()
        .head(20)
    )

    payload = {
        "kpis": {
            "total_visuales": int(df["visual_name"].nunique()),
            "total_paginas": int(df["pagina"].nunique()),
            "auditables_auto": int(df[mask_auditable]["visual_name"].nunique()),
            "no_auditables": int(df["visual_name"].nunique() - df[mask_auditable]["visual_name"].nunique()),
        },
        "resumen_por_pagina": resumen.to_dict(orient="records"),
        "top20_prioridad_manual": top_manual.to_dict(orient="records"),
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"OK CSV: {OUT_CSV}")
    print(f"OK JSON: {OUT_JSON}")
    print(payload["kpis"])


if __name__ == "__main__":
    main()
