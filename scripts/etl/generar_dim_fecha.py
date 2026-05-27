#!/usr/bin/env python3
"""
================================================================================
SCRIPT: generar_dim_fecha.py
PROPÓSITO: Generar tabla Dim_Fecha a partir de BD PERSONAS ATENDIDAS
ENTRADA: BD PERSONAS ATENDIDAS ORDINARIO 01-01-2025 A 24-05-2026.xlsx
SALIDA: data/model/Dim_Fecha.csv
================================================================================

COLUMNAS DE SALIDA:
  - fecha_key: YYYYMMDD format (int)
  - fecha_date: YYYY-MM-DD format (string)
  - año: 2025, 2026 (int)
  - mes: 1-12 (int)
  - mes_nombre: Enero, Febrero, etc. (string)
  - trimestre: Q1, Q2, Q3, Q4 (string)
  - semana: 1-53 (int)
  - día_semana: Lunes, Martes, etc. (string)

FILAS ESPERADAS: ~521 fechas únicas (01-01-2025 a 24-05-2026)

AUTOR: GitHub Copilot
FECHA: 2026-05-26
================================================================================
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# Configuración de rutas
PROJECT_ROOT = Path(__file__).parent.parent.parent
INPUT_FILE = PROJECT_ROOT / "data/model" / "BD PERSONAS ATENDIDAS ORDINARIO 01-01-2025 A 24-05-2026.xlsx"
OUTPUT_FILE = PROJECT_ROOT / "data/model" / "Dim_Fecha.csv"

# Mapeo de meses españoles
MESES_ES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

# Mapeo de días de semana españoles
DIAS_SEMANA_ES = {
    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado',
    'Sunday': 'Domingo'
}

def read_personas_data(file_path):
    """
    Lee el archivo BD PERSONAS ATENDIDAS y extrae la columna FECHA ATENCIÓN
    """
    print(f"[INFO] Leyendo archivo: {file_path}")
    
    if not file_path.exists():
        print(f"[ERROR] Archivo no encontrado: {file_path}")
        sys.exit(1)
    
    try:
        # Leer el archivo - primero intentar detectar la hoja correcta
        xls = pd.ExcelFile(file_path)
        print(f"[INFO] Hojas disponibles: {xls.sheet_names}")
        
        # Leer la primera hoja (generalmente contiene los datos)
        df = pd.read_excel(file_path, sheet_name=0)
        print(f"[INFO] Datos cargados: {df.shape[0]} filas, {df.shape[1]} columnas")
        print(f"[INFO] Columnas: {list(df.columns)}")
        
        return df
    except Exception as e:
        print(f"[ERROR] Error al leer archivo: {e}")
        sys.exit(1)

def extract_and_validate_dates(df):
    """
    Extrae la columna FECHA ATENCIÓN y valida su contenido
    """
    # Buscar columna de fecha (variantes posibles)
    fecha_col = None
    for col in df.columns:
        if 'FECHA' in col.upper() or 'fecha' in col.lower():
            fecha_col = col
            break
    
    if fecha_col is None:
        print(f"[ERROR] No se encontró columna de fecha. Columnas disponibles: {list(df.columns)}")
        sys.exit(1)
    
    print(f"[INFO] Columna de fecha encontrada: '{fecha_col}'")
    
    # Extraer y limpiar fechas
    try:
        fechas = pd.to_datetime(df[fecha_col], errors='coerce')
        
        # Mostrar estadísticas
        nulls = fechas.isna().sum()
        print(f"[INFO] Total fechas: {len(fechas)}, Nulos: {nulls}")
        
        if nulls > 0:
            print(f"[WARN] Se encontraron {nulls} valores nulos/inválidos")
        
        # Extraer fechas únicas y ordenar
        fechas_unicas = fechas.dropna().unique()
        fechas_unicas = pd.Series(fechas_unicas).sort_values().reset_index(drop=True)
        
        print(f"[INFO] Fechas únicas: {len(fechas_unicas)}")
        print(f"[INFO] Rango: {fechas_unicas.min()} a {fechas_unicas.max()}")
        
        return fechas_unicas
    
    except Exception as e:
        print(f"[ERROR] Error al procesar fechas: {e}")
        sys.exit(1)

def create_dim_fecha(fechas):
    """
    Crea la tabla Dim_Fecha con todas las columnas requeridas
    """
    print("\n[INFO] Generando dimensión temporal...")
    
    # Crear DataFrame base
    dim_fecha = pd.DataFrame()
    dim_fecha['fecha_date'] = fechas.dt.strftime('%Y-%m-%d')
    
    # Columnas numéricas básicas
    dim_fecha['año'] = fechas.dt.year
    dim_fecha['mes'] = fechas.dt.month
    
    # Mes en texto español
    dim_fecha['mes_nombre'] = fechas.dt.month.map(MESES_ES)
    
    # Fecha_key en formato YYYYMMDD
    dim_fecha['fecha_key'] = fechas.dt.strftime('%Y%m%d').astype(int)
    
    # Trimestre
    dim_fecha['trimestre'] = 'Q' + (fechas.dt.month.div(3).astype(int) + 1).astype(str)
    
    # Semana del año (ISO)
    dim_fecha['semana'] = fechas.dt.isocalendar().week.astype(int)
    
    # Día de semana en español
    dim_fecha['día_semana'] = fechas.dt.day_name().map(DIAS_SEMANA_ES)
    
    # Reordenar columnas según especificación
    dim_fecha = dim_fecha[[
        'fecha_key', 'fecha_date', 'año', 'mes', 'mes_nombre',
        'trimestre', 'semana', 'día_semana'
    ]]
    
    # Validación de integridad
    print(f"[INFO] Filas generadas: {len(dim_fecha)}")
    print(f"[INFO] Columnas: {list(dim_fecha.columns)}")
    print(f"[INFO] Sin duplicados: {not dim_fecha['fecha_key'].duplicated().any()}")
    print(f"[INFO] Sin nulos: {dim_fecha.isnull().sum().sum() == 0}")
    
    # Mostrar primeras y últimas filas
    print("\n[INFO] PRIMERAS FILAS:")
    print(dim_fecha.head())
    print("\n[INFO] ÚLTIMAS FILAS:")
    print(dim_fecha.tail())
    
    # Estadísticas
    print(f"\n[INFO] ESTADÍSTICAS:")
    print(f"  Años únicos: {dim_fecha['año'].nunique()} - {sorted(dim_fecha['año'].unique())}")
    print(f"  Meses cubiertos: {dim_fecha['mes'].nunique()} (1-12)")
    print(f"  Trimestres: {sorted(dim_fecha['trimestre'].unique())}")
    print(f"  Semanas (min-max): {dim_fecha['semana'].min()}-{dim_fecha['semana'].max()}")
    print(f"  Días de semana únicos: {dim_fecha['día_semana'].nunique()}")
    
    return dim_fecha

def save_csv(df, output_path):
    """
    Guarda la tabla Dim_Fecha en CSV
    """
    print(f"\n[INFO] Guardando CSV en: {output_path}")
    
    try:
        # Asegurar que el directorio existe
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Guardar CSV
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"[SUCCESS] Archivo guardado exitosamente")
        print(f"[INFO] Ruta: {output_path}")
        print(f"[INFO] Tamaño: {output_path.stat().st_size / 1024:.2f} KB")
        
        # Validación de lectura
        df_test = pd.read_csv(output_path)
        print(f"[INFO] Validación: {len(df_test)} filas leídas correctamente")
        
        return True
    
    except Exception as e:
        print(f"[ERROR] Error al guardar CSV: {e}")
        sys.exit(1)

def main():
    """
    Función principal que orquesta todo el proceso
    """
    print("=" * 80)
    print("GENERADOR DIM_FECHA - INICIANDO PROCESO")
    print("=" * 80)
    print(f"[INFO] Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[INFO] Entrada: {INPUT_FILE}")
    print(f"[INFO] Salida: {OUTPUT_FILE}")
    print("=" * 80)
    
    try:
        # PASO 1: Leer datos
        df_personas = read_personas_data(INPUT_FILE)
        
        # PASO 2: Extraer y validar fechas
        fechas = extract_and_validate_dates(df_personas)
        
        # PASO 3: Crear dimensión
        dim_fecha = create_dim_fecha(fechas)
        
        # PASO 4: Guardar CSV
        save_csv(dim_fecha, OUTPUT_FILE)
        
        print("\n" + "=" * 80)
        print("[SUCCESS] PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 80)
        print(f"[INFO] Dim_Fecha.csv generado con {len(dim_fecha)} filas")
        print(f"[INFO] Listo para importar a Power BI / Excel")
        print("=" * 80)
        
        return 0
    
    except Exception as e:
        print(f"\n[ERROR] Proceso fallido: {e}")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
