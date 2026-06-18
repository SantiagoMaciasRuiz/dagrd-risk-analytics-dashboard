import sys
sys.path.insert(0, r"C:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard\scripts\etl")

try:
    from reparar_hojas_modelo_para_powerbi import _build_dim_comites_desde_consolidado_confiable, _get_consolidado_comites_path
    
    print(f"Consolidado path: {_get_consolidado_comites_path()}")
    print()
    
    result = _build_dim_comites_desde_consolidado_confiable()
    if result is not None:
        print(f"✓ Función ejecutada exitosamente")
        print(f"  Filas retornadas: {len(result)}")
        print(f"  Columnas: {result.columns.tolist()}")
        print()
        print(result.head(10))
    else:
        print("✗ Función retornó None")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
