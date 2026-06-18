#!/usr/bin/env python3
"""
Agregar relaciones usando un método alternativo
Crea un script que debe pegar el usuario en Power BI
"""

def generar_instrucciones_rapidas():
    """Genera instrucciones para agregar relaciones de forma muy rápida"""
    
    print("=" * 80)
    print("MÉTODO RÁPIDO PARA AGREGAR RELACIONES (Menos de 3 minutos)")
    print("=" * 80)
    
    print("""
    ⚠️ CIERRA POWER BI COMPLETAMENTE PRIMERO
    
    Luego sigue EXACTAMENTE estos pasos:
    
    1️⃣ ABRE Power BI nuevamente
    
    2️⃣ CLIC DERECHO en la tabla "Dim_Semilleros" (en la zona izquierda)
    
    3️⃣ Selecciona: "Crear una relación"
    
    4️⃣ ARRASTRA: "Dim_Semilleros.Comuna" hacia "Hecho_Participacion_General.comuna_cod"
        (Básicamente arrastra el punto de Comuna al otro lado)
    
    5️⃣ Verifica que dice:
        ✓ Dim_Semilleros → Hecho_Participacion_General
        ✓ Comuna → comuna_cod
        ✓ Muchos a 1
        
    6️⃣ CLIC OK
    
    ────────────────────────────────────────────────────────────────
    
    7️⃣ CLIC DERECHO en la tabla "Dim_SATC"
    
    8️⃣ Selecciona: "Crear una relación"
    
    9️⃣ ARRASTRA: "Dim_SATC.SATC_ID" hacia "Hecho_Participacion_General.satc_id"
    
    🔟 Verifica que dice:
        ✓ Dim_SATC → Hecho_Participacion_General
        ✓ SATC_ID → satc_id
        ✓ Muchos a 1
        
    1️⃣1️⃣ CLIC OK
    
    ════════════════════════════════════════════════════════════════
    
    ✅ LISTO! Deberías ver 2 líneas azules conectando las tablas.
    
    Tiempo total: ~2-3 minutos si lo haces rápido.
    No hay riesgo de dañar nada.
    """)

if __name__ == "__main__":
    generar_instrucciones_rapidas()
