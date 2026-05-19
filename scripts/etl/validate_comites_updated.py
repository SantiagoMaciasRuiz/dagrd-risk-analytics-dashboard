#!/usr/bin/env python3
import pandas as pd

df = pd.read_csv('data/model/Dim_Comites_Comisiones_2026.csv')
print(f'Filas actualizadas: {len(df)}')
print(f'Comunas únicas: {sorted(df["comuna_cod"].unique())}')
print(f'\nMuestra de datos actualizado:')
print(df[["comite_comision_nombre", "comite_comision_etiqueta"]].head(8).to_string())
