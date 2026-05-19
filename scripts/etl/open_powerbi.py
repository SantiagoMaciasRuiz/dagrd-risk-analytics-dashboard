#!/usr/bin/env python3
import os
import time

pbix_path = r"Tableros\tableroDAGRDCOPIA.pbix"

print("Abriendo Power BI con el archivo actualizado...")
os.startfile(pbix_path)
print("✓ Power BI abierto. Espera 30 segundos para que cargue el modelo completamente...")
time.sleep(30)
print("✓ Listo. Verifica que los cambios TMDL se han sincronizado.")
