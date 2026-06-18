from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


BASE = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")


def _resolve_source_xlsx() -> Path:
    source_dir = BASE / "data" / "source"
    candidates = sorted(
        source_dir.glob("Reporte de actividades equipo social 2026*.xlsx"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if candidates:
        return candidates[0]
    return source_dir / "Reporte de actividades equipo social 2026.xlsx"


SOURCE_XLSX = _resolve_source_xlsx()
OUT_DIR = Path(
    r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard\data\reference"
)


def normalize_text(value: str) -> str:
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"[;|,]+$", "", value).strip()
    return value.upper()


def split_items(raw_value: str) -> list[str]:
    if raw_value is None:
        return []
    text = str(raw_value).replace("\xa0", " ").strip()
    if not text or text.lower() in {"nan", "none"}:
        return []

    chunks = re.split(r"[\n\r;|]+", text)
    values: list[str] = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        if "," in chunk and len(chunk) > 35:
            values.extend([p.strip() for p in chunk.split(",") if p.strip()])
        else:
            values.append(chunk)
    return values


def main() -> None:
    if not SOURCE_XLSX.exists():
        raise FileNotFoundError(f"No existe el archivo fuente: {SOURCE_XLSX}")

    xls = pd.ExcelFile(SOURCE_XLSX)
    sheet_name = "Sheet1" if "Sheet1" in xls.sheet_names else xls.sheet_names[0]
    df = pd.read_excel(SOURCE_XLSX, sheet_name=sheet_name, dtype=str)

    normalized_columns = {}
    for col in df.columns:
        clean_name = str(col).replace("\xa0", " ")
        clean_name = re.sub(r"\s+", " ", clean_name).strip()
        normalized_columns[col] = clean_name

    comuna_columns: list[tuple[int, str, str]] = []
    for original_col, clean_col in normalized_columns.items():
        match = re.match(
            r"^Comité/Comisión\s+CGRD\s+Comuna\s+(\d+)$",
            clean_col,
            flags=re.IGNORECASE,
        )
        if match:
            comuna_columns.append((int(match.group(1)), original_col, clean_col))

    comuna_columns.sort(key=lambda x: x[0])

    global_counter: dict[str, int] = {}
    global_examples: dict[str, str] = {}
    by_comuna_counter: dict[tuple[int, str], int] = {}
    name_to_comunas: dict[str, set[int]] = {}

    for comuna_num, original_col, _ in comuna_columns:
        for raw_cell in df[original_col].fillna("").astype(str):
            for item in split_items(raw_cell):
                normalized_item = normalize_text(item)
                if not normalized_item or normalized_item in {"|", "-"}:
                    continue

                global_counter[normalized_item] = global_counter.get(normalized_item, 0) + 1
                by_key = (comuna_num, normalized_item)
                by_comuna_counter[by_key] = by_comuna_counter.get(by_key, 0) + 1
                name_to_comunas.setdefault(normalized_item, set()).add(comuna_num)

                if normalized_item not in global_examples:
                    global_examples[normalized_item] = item.strip()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    global_rows = []
    for name, count in sorted(global_counter.items(), key=lambda x: (-x[1], x[0])):
        comunas = sorted(name_to_comunas.get(name, set()))
        global_rows.append(
            {
                "nombre_normalizado": name,
                "nombre_ejemplo": global_examples.get(name, name),
                "apariciones_totales": count,
                "numero_comunas": len(comunas),
                "comunas": ";".join(str(c) for c in comunas),
            }
        )

    by_comuna_rows = []
    for (comuna, name), count in sorted(
        by_comuna_counter.items(), key=lambda x: (x[0][0], -x[1], x[0][1])
    ):
        by_comuna_rows.append(
            {
                "comuna": comuna,
                "nombre_normalizado": name,
                "nombre_ejemplo": global_examples.get(name, name),
                "apariciones": count,
            }
        )

    out_global = OUT_DIR / "validacion_comites_comisiones_listado_global_2026.csv"
    out_by_comuna = OUT_DIR / "validacion_comites_comisiones_listado_por_comuna_2026.csv"

    pd.DataFrame(global_rows).to_csv(out_global, index=False, encoding="utf-8-sig")
    pd.DataFrame(by_comuna_rows).to_csv(out_by_comuna, index=False, encoding="utf-8-sig")

    print(f"Hoja usada: {sheet_name}")
    print(f"Columnas comuna detectadas: {len(comuna_columns)}")
    print(f"Total nombres unicos: {len(global_rows)}")
    print(f"Total apariciones: {sum(global_counter.values())}")
    print(f"Archivo global: {out_global}")
    print(f"Archivo por comuna: {out_by_comuna}")

    print("\nTop 20 nombres por apariciones:")
    for row in global_rows[:20]:
        print(
            f"- {row['nombre_normalizado']} => {row['apariciones_totales']} "
            f"(comunas: {row['comunas']})"
        )


if __name__ == "__main__":
    main()
