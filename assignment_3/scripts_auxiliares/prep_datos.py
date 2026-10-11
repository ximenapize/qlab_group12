"""Genera los mapas livianos del dashboard (se corre una vez en local).

Entrada (fuera del repo): shapefile distrital INEI 2023 (1 891 distritos)
Salidas en datos/: mapa_distritos.geojson, mapa_provincias.geojson, departamentos_ubigeo.geojson
Uso: python prep_datos.py ruta/al/shapefile.shp
(La tabla de emergencias se genera con construir_ee_distrital.py.)
"""
from pathlib import Path
import sys
import pandas as pd
import geopandas as gpd

DATOS = Path(__file__).resolve().parent.parent / "datos"

SHP = sys.argv[1]
g = gpd.read_file(SHP).rename(columns={"UBIGEO": "ubigeo"})
g["ubigeo"] = g["ubigeo"].astype(str).str.zfill(6)

# Nombres (para el tooltip de las unidades sin decretos)
for c in ("DEPARTAMEN", "PROVINCIA", "DISTRITO"):
    g[c] = g[c].str.title()
g["nombre"] = g["DISTRITO"] + " (" + g["PROVINCIA"] + ")"

m = g[["ubigeo", "nombre", "geometry"]].to_crs(32718)
m["geometry"] = m.simplify(800)
m.to_crs(4326).to_file(DATOS / "mapa_distritos.geojson", driver="GeoJSON")

p = g[["ubigeo", "PROVINCIA", "DEPARTAMEN", "geometry"]].copy()
p["ubigeo"] = p["ubigeo"].str[:4]
p = p.dissolve(by="ubigeo", as_index=False, aggfunc="first")
p["nombre"] = p["PROVINCIA"] + " (" + p["DEPARTAMEN"] + ")"
p = p[["ubigeo", "nombre", "geometry"]].to_crs(32718)
p["geometry"] = p.buffer(100).buffer(-100).simplify(1000)
p.to_crs(4326).to_file(DATOS / "mapa_provincias.geojson", driver="GeoJSON")

dp = g[["ubigeo", "DEPARTAMEN", "geometry"]].copy()
dp["ubigeo"] = dp["ubigeo"].str[:2]
dp = dp.dissolve(by="ubigeo", as_index=False, aggfunc="first").rename(columns={"DEPARTAMEN": "nombre"})
dp = dp.to_crs(32718)
dp["geometry"] = dp.buffer(100).buffer(-100).simplify(1000)
dp.to_crs(4326).to_file(DATOS / "departamentos_ubigeo.geojson", driver="GeoJSON")
