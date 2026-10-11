"""Lluvia por distrito con la API histórica de Open-Meteo (mismo criterio que el Assignment 2).

Punto de consulta: punto representativo (dentro del polígono) de cada distrito.
Salida: datos/lluvias_distritos.csv  (ubigeo, latitud, longitud, lluvia_total_mm, dias_lluvia_fuerte, dias_sin_dato)
"""
from pathlib import Path
import sys
import time

import geopandas as gpd
import pandas as pd
import requests

DATOS = Path(__file__).resolve().parent.parent / "datos"

INI, FIN, LOTE = "2025-01-01", "2025-05-31", 50
URL = "https://archive-api.open-meteo.com/v1/archive"

g = gpd.read_file(sys.argv[1]).rename(columns={"UBIGEO": "ubigeo"})  # shapefile distrital INEI 2023
g["ubigeo"] = g["ubigeo"].astype(str).str.zfill(6)
pts = g.geometry.representative_point()
g["latitud"], g["longitud"] = pts.y.round(4), pts.x.round(4)

filas = []
for i in range(0, len(g), LOTE):
    b = g.iloc[i:i + LOTE]
    params = {"latitude": ",".join(map(str, b.latitud)), "longitude": ",".join(map(str, b.longitud)),
              "start_date": INI, "end_date": FIN, "daily": "precipitation_sum", "timezone": "America/Lima"}
    for intento in range(6):
        r = requests.get(URL, params=params, timeout=60)
        if r.status_code == 200:
            break
        print("reintento", r.status_code, r.text[:100])
        time.sleep(30 * (intento + 1))
    r.raise_for_status()
    res = r.json()
    res = res if isinstance(res, list) else [res]
    for (_, fila), x in zip(b.iterrows(), res):
        p = pd.Series(x["daily"]["precipitation_sum"], dtype="float")
        filas.append({"ubigeo": fila.ubigeo, "latitud": fila.latitud, "longitud": fila.longitud,
                      "lluvia_total_mm": round(p.sum(), 1), "dias_lluvia_fuerte": int((p >= 20).sum()),
                      "dias_sin_dato": int(p.isna().sum())})
    print(i + len(b), "/", len(g), flush=True)
    time.sleep(2)

out = pd.DataFrame(filas)
out.to_csv(DATOS / "lluvias_distritos.csv", index=False)
print(out.describe())
