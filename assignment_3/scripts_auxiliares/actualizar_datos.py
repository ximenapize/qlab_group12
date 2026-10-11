"""Regenera todos los datos del dashboard desde cero (solo para quien los reconstruye; la app no lo necesita).

Orden:
  1. construir_ee_distrital.py  -> datos/ee_distrital_2025.csv   (base PUCP expandida a distrito)
  2. prep_datos.py              -> datos/mapa_*.geojson, departamentos_ubigeo.geojson   (desde el shapefile INEI 2023)
  3. lluvias_distritos.py       -> datos/lluvias_distritos.csv   (API de Open-Meteo, tarda unos minutos)

Uso:
  python actualizar_datos.py --base DisposicionesEstadosDeEmergencia.xlsx \\
                             --catalogo catalogo_ubigeo_maestro.csv --shp "ruta/shapefile_distrital.shp" [--sin-lluvia]
Dependencias: pip install -r scripts_auxiliares/requirements-datos.txt
"""
import argparse
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).parent

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument("--base", required=True, help="Excel de la Base de Estados de Emergencia en el Perú (PUCP)")
p.add_argument("--catalogo", required=True, help="catalogo_ubigeo_maestro.csv (ubigeos y fechas de creación de distritos)")
p.add_argument("--shp", required=True, help="Shapefile distrital INEI 2023 (1 891 distritos)")
p.add_argument("--sin-lluvia", action="store_true", help="No vuelve a descargar la lluvia de Open-Meteo")
a = p.parse_args()

for ruta in (a.base, a.catalogo, a.shp):
    if not Path(ruta).exists():
        sys.exit(f"No existe el archivo: {ruta}")

pasos = [
    ["construir_ee_distrital.py", a.base, a.catalogo],
    ["prep_datos.py", a.shp],
]
if not a.sin_lluvia:
    pasos.append(["lluvias_distritos.py", a.shp])

for paso in pasos:
    print(f"\n=== {paso[0]} ===", flush=True)
    subprocess.run([sys.executable, str(AQUI / paso[0]), *paso[1:]], check=True)
print("\nListo: datos/ actualizado. Ejecuta `streamlit run app.py` desde assignment_3/ para verlo.")
