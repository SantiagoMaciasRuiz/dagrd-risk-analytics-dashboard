"""
Validación de datos: CAM_Detalle vs Empresas_Detalle
Reporte comparativo de empresas
"""
from datetime import datetime

# Datos extraídos de Power BI DAX queries
cam_detalle_empresas = [
    "Centro Comercial Aventura",
    "Centro Comercial Bosque Plaza",
    "Corporacion Parque explora",
    "Facultad Nacional de Salud Pública- UdeA",
    "FNSP- UdeA",
    "Forjas Bolívar S.A.S",
    "Fundacion organizacion vid",
    "Hospital Alma Mater de Antioquia",
    "Hospital Universitario San Vicente de Paul",
    "Iglesia Centro de Fe y Esperanza CFE Central",
    "Metro de Medellin",
    "Planetario de medellin",
    "Universidad de Antioquia- Facultad de Salud Publica",
    "Clinica Bolivariana",
    "Clínica Cardio VID",
    "Corporación de Fomento Asistencial del Hospital Universitario San Vicente de Paúl/Fomenthum Zona P",
    "Hospital Pablo Tobon Uribe",
    "IPS San Esteban",
    "UT Metro de la 80",
    "Zona P",
    "I.U. Pascual Bravo",
    "Institución Universitaria Colegio Mayor de Antioquia",
    "Institución Universitaria ITM",
    "Metro ligero de la 80",
    "Tecnológico de Antioquia I.U.",
    "Universidad de Antioquia",
    "Universidad Nacional de Colombia",
    "Cámara de Comercio de Medellín para Antioquía",
    "Centro Comercial Camino Real",
    "Clínica Soma",
    "Cooperativa Multiactiva de la Plaza de Flórez",
    "Edificio Centro Coltejer PH",
    "Fundacion organzacion vid",
    "Lotería de Medellín",
    "Placita de Flórez",
    "SEGURIDAD DE COLOMBIA ANTIOQUÍA LTDA",
    "SOCIEDAD DE MEJORAS PUBLICAS DE MEDELLIN",
    "Universidad Cooperativa de Colombia",
    "Centro cívico de Antioquia Plaza de la Libertad PH.",
    "Distrito Medellin",
    "Gobernacion de Antioquia",
    "IDEA",
    "Personería Distritaltal de Medellín",
    "Plaza Mayor",
    "Rama judicial",
    "Airplan S.A (bomberos)",
    "AUNA",
    "BRAC - Aeropuerto",
    "Cementerio Campos de Paz",
    "Centro comercial Arkadia",
    "Club El Rodeo",
    "CODISCOS",
    "Ejercito (Batallón de infanteria # 32) (invitados)",
    "Fundación colombiana de Cancerología clínica vida",
    "Rotonda Las Americas",
    "Torre medica las americas",
    "TRONEX",
    "A PARRA SAS",
    "Alico S.A.S",
    "Asociación de Copropietarios de la Urbanización Aldea de Guayabal",
    "Carpas IKL SAS",
    "Fraiche",
    "INDUSTRIAS ALIMENTICIAS PERMAN S.A.",
    "Parchita",
    "Siditel",
    "Ssp asesores",
    "Tostaditos Susanita S.A.S",
    "Transurcar",
    "Tronex-Codiscos",
    "VALLAS Y AVISOS SAS",
    "VISDECOL SAS",
    "AMTEX",
    "Renault Caribe Motors",
    "Alpina",
    "EMI",
    "ÉXITO",
    "HOMECENTER",
    "La Migueria",
    "MONTERREY",
    "POLITECNICO JAIME ISAZA CADAVIDA",
    "RENTING COLOMBIA",
    "TUYOMOTOR",
    "COMFAMA",
    "Hospital General",
    "Matelsa",
    "HOGAR SAN CRISTOBAL",
    "ITM",
    "POLICIA",
    "ESU",
    "BANCOLOMBIA",
    "CENTRO COMERCIAL PUNTO CLAVE",
    "EPS SANITAS",
]

# Empresas_Detalle (normalizadas en la medida)
empresas_detalle_mostradas = [
    "A PARRA SAS",
    "AIRPLAN S.A (BOMBEROS)",
    "ALICO S.A.S",
    "AMTEX",
    "ASOCIACION DE COPROPIETARIOS DE LA URBANIZACION ALDEA DE GUAYABAL",
    "AUNA",
    "BRAC - AEROPUERTO",
    "CAMARA DE COMERCIO DE MEDELLIN PARA ANTIOQUIA",
    "CARPAS IKL SAS",
    "CEMENTERIO CAMPOS DE PAZ",
    "CENTRO CIVICO DE ANTIOQUIA PLAZA DE LA LIBERTAD PH.",
    "CENTRO COMERCIAL ARKADIA",
    "CENTRO COMERCIAL AVENTURA",
    "CENTRO COMERCIAL BOSQUE PLAZA",
    "CENTRO COMERCIAL CAMINO REAL",
    "CLINICA BOLIVARIANA",
    "CLINICA CARDIO VID",
    "CLINICA SOMA",
    "CLUB EL RODEO",
    "CODISCOS",
    "COOPERATIVA MULTIACTIVA DE LA PLAZA DE FLOREZ",
    "CORPORACION DE FOMENTO ASISTENCIAL DEL HOSPITAL UNIVERSITARIO SAN VICENTE DE PAUL/FOMENTHUM ZONA P",
    "CORPORACION PARQUE EXPLORA",
    "DISTRITO MEDELLIN",
    "EDIFICIO CENTRO COLTEJER PH",
    "EJERCITO (BATALLON DE INFANTERIA # 32) (INVITADOS)",
    "FACULTAD NACIONAL DE SALUD PUBLICA- UDEA",
    "FNSP- UDEA",
    "FORJAS BOLIVAR S.A.S",
    "FRAICHE",
    "FUNDACION COLOMBIANA DE CANCEROLOGIA CLINICA VIDA",
    "FUNDACION ORGANIZACION VID",
    "FUNDACION ORGANZACION VID",
    "GOBERNACION DE ANTIOQUIA",
    "HOSPITAL ALMA MATER DE ANTIOQUIA",
    "HOSPITAL PABLO TOBON URIBE",
    "HOSPITAL UNIVERSITARIO SAN VICENTE DE PAUL",
    "I.U. PASCUAL BRAVO",
    "IDEA",
    "IGLESIA CENTRO DE FE Y ESPERANZA CFE CENTRAL",
    "INDUSTRIAS ALIMENTICIAS PERMAN S.A.",
    "INSTITUCION UNIVERSITARIA COLEGIO MAYOR DE ANTIOQUIA",
    "INSTITUCION UNIVERSITARIA ITM",
    "IPS SAN ESTEBAN",
    "LOTERIA DE MEDELLIN",
    "METRO DE MEDELLIN",
    "METRO LIGERO DE LA 80",
    "PARCHITA",
    "PERSONERIA DISTRITALTAL DE MEDELLIN",
    "PLACITA DE FLOREZ",
    "PLANETARIO DE MEDELLIN",
    "PLAZA MAYOR",
    "RAMA JUDICIAL",
    "RENAULT CARIBE MOTORS",
    "ROTONDA LAS AMERICAS",
    "SEGURIDAD DE COLOMBIA ANTIOQUIA LTDA",
    "SIDITEL",
    "SOCIEDAD DE MEJORAS PUBLICAS DE MEDELLIN",
    "SSP ASESORES",
    "TECNOLOGICO DE ANTIOQUIA I.U.",
    "TORRE MEDICA LAS AMERICAS",
    "TOSTADITOS SUSANITA S.A.S",
    "TRANSURCAR",
    "TRONEX",
    "TRONEX-CODISCOS",
    "UNIVERSIDAD COOPERATIVA DE COLOMBIA",
    "UNIVERSIDAD DE ANTIOQUIA",
    "UNIVERSIDAD DE ANTIOQUIA- FACULTAD DE SALUD PUBLICA",
    "UNIVERSIDAD NACIONAL DE COLOMBIA",
    "UT METRO DE LA 80",
    "VALLAS Y AVISOS SAS",
    "VISDECOL SAS",
    "ZONA P",
]

# Normalizador
def normalizar(empresa):
    """Normaliza empresa a mayúsculas y quita espacios extras"""
    return empresa.upper().strip()

# Crear listas de datos normalizados
cam_norm_list = [(normalizar(e), e) for e in cam_detalle_empresas]
detalle_norm_list = [(normalizar(e), e) for e in empresas_detalle_mostradas]

# Análisis
print("=" * 100)
print("VALIDACIÓN: CAM_Detalle vs Empresas_Detalle")
print("=" * 100)
print(f"\n📊 RESUMEN NUMÉRICO:")
print(f"  ✓ CAM_Detalle total registros: 97")
print(f"  ✓ CAM_Detalle empresas únicas: {len(cam_detalle_empresas)}")
print(f"  ✓ Medida Actividades_Empresa: 92")
print(f"  ✓ Empresas_Detalle mostradas: {len(empresas_detalle_mostradas)}")

# Buscar discrepancias
cam_norm = {norm: orig for norm, orig in cam_norm_list}
detalle_norm = {norm: orig for norm, orig in detalle_norm_list}

cam_norm_set = set(cam_norm.keys())
detalle_norm_set = set(detalle_norm.keys())

faltantes = cam_norm_set - detalle_norm_set
extras = detalle_norm_set - cam_norm_set

print(f"\n🔍 ANÁLISIS DE DIFERENCIAS:")
print(f"  • Empresas EN CAM pero NO en Empresas_Detalle: {len(faltantes)}")
print(f"  • Empresas EN Empresas_Detalle pero NO en CAM: {len(extras)}")

if faltantes:
    print(f"\n❌ EMPRESAS FALTANTES en Empresas_Detalle:")
    for emp_norm in sorted(faltantes):
        original = cam_norm[emp_norm]
        print(f"   • {original}")

if extras:
    print(f"\n⚠️  EMPRESAS EXTRAS en Empresas_Detalle (no en CAM):")
    for emp_norm in sorted(extras):
        original = detalle_norm[emp_norm]
        print(f"   • {original}")

print("\n" + "=" * 100)

# Guardar como CSV simple
import csv

with open('Validacion_CAM_Empresas_Detalle_RESUMEN.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Métrica', 'Valor'])
    writer.writerow(['CAM_Detalle total registros', 97])
    writer.writerow(['CAM_Detalle empresas únicas', len(cam_detalle_empresas)])
    writer.writerow(['Medida Actividades_Empresa', 92])
    writer.writerow(['Empresas_Detalle mostradas', len(empresas_detalle_mostradas)])
    writer.writerow(['Diferencia (CAM - Detalle)', len(cam_detalle_empresas) - len(empresas_detalle_mostradas)])
    writer.writerow(['Empresas faltantes', len(faltantes)])
    writer.writerow(['Empresas extras', len(extras)])

# Guardar faltantes
if faltantes:
    with open('Validacion_CAM_FALTANTES.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Empresa Original', 'Empresa Normalizada'])
        for emp_norm in sorted(faltantes):
            writer.writerow([cam_norm[emp_norm], emp_norm])

print(f"\n✅ Archivos generados:")
print(f"   • Validacion_CAM_Empresas_Detalle_RESUMEN.csv")
if faltantes:
    print(f"   • Validacion_CAM_FALTANTES.csv")

