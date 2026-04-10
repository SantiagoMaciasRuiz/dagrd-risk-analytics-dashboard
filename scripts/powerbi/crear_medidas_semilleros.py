#!/usr/bin/env python3
"""
Generar medidas DAX para Semilleros en Power BI
"""

OUTPUT_FILE = "scripts/dax/medidas_semilleros.dax"

DAX_MEASURES = """// ============================================
// MEDIDAS PARA SEMILLEROS
// Generadas: 2026-03-18
// Fuente: Dim_Semilleros (20 semilleros confiables)
// ============================================

Total_Semilleros = DISTINCTCOUNT(Dim_Semilleros[Semillero])
// Resultado: 20 semilleros únicos registrados

Semilleros_por_Comuna = DISTINCTCOUNT(Dim_Semilleros[Comuna])
// Resultado: 9 comunas con presencia de semilleros

Semilleros_Activos = CALCULATE(
    DISTINCTCOUNT(Dim_Semilleros[Semillero]),
    FILTER(Hecho_Participacion_General, Hecho_Participacion_General[bloque_comunidad] = "Semilleros")
)
// Semilleros con participación registrada

Comuna_Seleccionada_Semilleros = IFERROR(
    VALUES(Dim_Semilleros[Comuna_Nombre]),
    "Seleccionar"
)
// Para usar en slicers de comunas con semilleros
"""

def crear_medidas_semilleros():
    """Crear archivo de medidas DAX para Semilleros"""
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(DAX_MEASURES)
    
    print(f"✓ Medidas DAX para Semilleros creadas")
    print(f"  - Archivo: {OUTPUT_FILE}")
    print(f"  - 4 medidas nuevas generadas")
    print(f"\nPróximos pasos:")
    print(f"  1. Copiar contenido de {OUTPUT_FILE}")
    print(f"  2. Ir a Power BI Desktop → Modelado → Nueva medida")
    print(f"  3. Pegar cada medida en su tabla correspondiente")
    print(f"  4. Refrescar datos (Ctrl+Shift+R)")

if __name__ == "__main__":
    crear_medidas_semilleros()
