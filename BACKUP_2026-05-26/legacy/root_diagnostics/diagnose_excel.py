#!/usr/bin/env python3
"""Diagnose Excel structure to debug ETL issues."""
import sys
from pathlib import Path
import pandas as pd
import openpyxl

def diagnose():
    excel_file = Path("data/source/Reporte de actividades equipo social 2026 (1).xlsx")
    
    if not excel_file.exists():
        print(f"❌ File not found: {excel_file}")
        return
    
    print(f"📊 Diagnosing: {excel_file}\n")
    
    # Try openpyxl
    try:
        wb = openpyxl.load_workbook(excel_file)
        print(f"✅ OpenPyXL loaded successfully")
        print(f"   Sheets: {wb.sheetnames}")
        ws = wb.active
        print(f"   Active sheet: {ws.title}")
        print(f"   Dimensions: {ws.dimensions}")
        print()
    except Exception as e:
        print(f"❌ OpenPyXL error: {e}\n")
    
    # Try pandas to get headers
    try:
        df = pd.read_excel(excel_file, sheet_name=0, nrows=1)
        print(f"✅ Pandas loaded sheet with {len(df.columns)} columns")
        print(f"\n   Column names (first 30):")
        for i, col in enumerate(df.columns[:30], 1):
            print(f"   {i:2d}. {col}")
        
        if len(df.columns) > 30:
            print(f"\n   ... and {len(df.columns) - 30} more columns")
            for i, col in enumerate(df.columns[30:min(60, len(df.columns))], 31):
                print(f"   {i:2d}. {col}")
        
        # Search for specific columns the ETL needs
        print(f"\n🔍 Searching for required columns:")
        required = ["procesos", "participantes", "fecha", "instancia", "comuna", "mujeres", "hombres"]
        for req in required:
            found = [c for c in df.columns if req.lower() in c.lower()]
            if found:
                print(f"   ✅ '{req}': {found}")
            else:
                print(f"   ❌ '{req}': NOT FOUND")
        
        print(f"\n   Total rows: {len(df)}")
        
    except Exception as e:
        print(f"❌ Pandas error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose()
