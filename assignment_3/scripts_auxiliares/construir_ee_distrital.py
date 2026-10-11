"""Construye la tabla distrital de estados de emergencia a partir de la base del PUCP.

Replica los chunks 1 a 3 de protestas_ee_v2.Rmd (carga, separación de modificatorias y expansión
geográfica a nivel distrital) y deja el extracto que usa el dashboard.

Base de datos original (citar):
    Alcantara, K., Aragón, J., Cruz, M., Gutiérrez, N., Ilizarbe, C., Pinillos, X. & Retamozo, D. (2026).
    Base de Estados de Emergencia en el Perú (Versión julio 2026) [Base de datos]. Escuela de Gobierno y
    Políticas Públicas - Pontificia Universidad Católica del Perú (PUCP).

Uso:
    python construir_ee_distrital.py DisposicionesEstadosDeEmergencia.xlsx catalogo_ubigeo_maestro.csv [salida_completa.csv]

Salidas:
    datos/ee_distrital_2025.csv   extracto enero–mayo 2025 (declaratorias y prórrogas de lluvias y orden interno)
    salida_completa.csv           (opcional) toda la expansión distrital 2000–2025

Lo que NO replica del Rmd: los chunks 4 y 5 (términos y modificatorias), que solo corrigen la fecha efectiva de
fin (fecha_final_real) con tablas manuales (modificatorias.xlsx). El dashboard cuenta decretos por fecha de
promulgación y no usa fechas de fin efectivas, así que no los necesita.
"""
from pathlib import Path
import re
import sys
import unicodedata

import pandas as pd

DATOS = Path(__file__).resolve().parent.parent / "datos"

BASE_XLSX, CATALOGO = sys.argv[1], sys.argv[2]
SALIDA_COMPLETA = sys.argv[3] if len(sys.argv) > 3 else None
INI, FIN = "2025-01-01", "2025-05-31"


def sin_tildes_mayus(s):
    if pd.isna(s):
        return s
    s = unicodedata.normalize("NFKD", str(s).strip())
    return "".join(c for c in s if not unicodedata.combining(c)).upper()


def codigo_ds(x):
    """'DECRETO SUPREMO Nº 003-2000-PCM' -> '003-2000' (misma regla que extraer_codigo_ds del Rmd)."""
    m = re.search(r"\d{2,3}-\d{4}", str(x))
    if not m:
        return pd.NA
    c = m.group(0)
    return "0" + c if len(c.split("-")[0]) == 2 else c


def lista(x, ancho):
    """'1703, 2102' -> ['1703', '2102'] con ceros a la izquierda; vacío si no hay dato."""
    if pd.isna(x) or str(x).strip() == "":
        return []
    return [p.strip().zfill(ancho) for p in str(x).split(",") if p.strip()]


# ── Chunk 1: carga ───────────────────────────────────────────────────────────
cat = pd.read_csv(CATALOGO, dtype=str)
cat["ubigeo_dist"] = cat["ubigeo"].str.zfill(6)
cat["ubigeo_prov"], cat["ubigeo_dep"] = cat["ubigeo_dist"].str[:4], cat["ubigeo_dist"].str[:2]
for c_, n_ in (("dep", "dep_norm"), ("prov", "prov_norm"), ("dist", "dist_norm")):
    cat[n_] = cat[c_].map(sin_tildes_mayus)
cat["fecha_creacion"] = pd.to_datetime(cat["fecha_creacion"], errors="coerce")
cat = cat[["ubigeo_dist", "ubigeo_prov", "ubigeo_dep", "dep_norm", "prov_norm", "dist_norm", "fecha_creacion"]]

hojas = pd.read_excel(BASE_XLSX, sheet_name=None, dtype=str)
ee = next(h for h in hojas.values() if "decreto_supremo" in h.columns)  # hoja de datos (la otra es la carátula)
for c in ("departamento", "provincia", "distrito"):
    ee[c] = ee[c].map(sin_tildes_mayus)
for c in ("fecha_promulgacion", "fecha_inicio", "fecha_final"):
    ee[c] = pd.to_datetime(ee[c], errors="coerce")
ee["disposicion"] = ee["disposicion"].str.strip().str.upper()
ee["id_disposicion"] = ee["ID"].astype(float).astype(int)
# La base pública no trae los códigos de grupo manuales del Rmd: se derivan del decreto
ee["ds_actual"] = ee["decreto_supremo"].map(codigo_ds)
ee["ds_madre"] = ee["nombre_ds_original"].map(codigo_ds)
ee["id_grupo_ee"] = ee["ds_madre"]
print("Filas base:", len(ee), "| disposiciones:", ee["disposicion"].value_counts().to_dict())

# ── Chunk 2: separar modificatorias ──────────────────────────────────────────
ee_trabajo = ee[ee["disposicion"] != "MODIFICATORIA"].copy()
ee_para_expandir = ee_trabajo[ee_trabajo["disposicion"].isin(["DECLARATORIA", "PRÓRROGA"])].reset_index(drop=True)
print("Filas a expandir (declaratorias + prórrogas):", len(ee_para_expandir))

# ── Chunk 3: expansión geográfica a distrito ─────────────────────────────────
# Prioridad: nacional > ubigeo_distrito explícito > provincia > departamento.
# Solo distritos que ya existían en la fecha de promulgación.
es_nacional = ee_para_expandir["departamento"].fillna("").str.contains("TODO")
CAT_COLS = ["ubigeo_dist", "dep_norm", "prov_norm", "dist_norm", "fecha_creacion"]


def existia(df):
    return df[df["fecha_creacion"].isna() | (df["fecha_creacion"] <= df["fecha_promulgacion"])].drop(columns="fecha_creacion")


# Paso 1: nacionales -> cross join con el catálogo
nac = ee_para_expandir[es_nacional].merge(cat[CAT_COLS], how="cross")
nac = existia(nac).rename(columns={"ubigeo_dist": "ubigeo_distrito_final"})

resto = ee_para_expandir[~es_nacional]

# Paso 2: ubigeo_distrito explícito
d = resto.assign(ubigeo_dist=resto["ubigeo_distrito"].map(lambda x: lista(x, 6))).explode("ubigeo_dist")
d = d[d["ubigeo_dist"].notna() & (d["ubigeo_dist"].astype(str).str.len() == 6)]
d = d.merge(cat[CAT_COLS].rename(columns={"ubigeo_dist": "ubigeo_dist_l"}), left_on="ubigeo_dist", right_on="ubigeo_dist_l", how="left",
            suffixes=("", "_cat")).drop(columns=["ubigeo_dist_l"])
con_dist = existia(d).rename(columns={"ubigeo_dist": "ubigeo_distrito_final"})
print("Filas con distrito explícito:", len(con_dist))

# Paso 3: provincias sin cobertura distrital
r = resto.assign(prov_l=resto["ubigeo_provincia"].map(lambda x: lista(x, 4)),
                 dist_l=resto["ubigeo_distrito"].map(lambda x: lista(x, 6)))
r = r.explode("prov_l")
r = r[r["prov_l"].notna()]
r = r[[not any(x[:4] == p for x in ds) for p, ds in zip(r["prov_l"], r["dist_l"])]]
desde_prov = r.drop(columns=["prov_l", "dist_l"]).assign(prov_clean=r["prov_l"]).merge(
    cat[["ubigeo_dist", "ubigeo_prov", "dep_norm", "prov_norm", "dist_norm", "fecha_creacion"]].drop_duplicates(),
    left_on="prov_clean", right_on="ubigeo_prov", how="inner")
desde_prov = existia(desde_prov).rename(columns={"ubigeo_dist": "ubigeo_distrito_final"}).drop(columns=["prov_clean", "ubigeo_prov"])
print("Filas expandidas desde provincia:", len(desde_prov))

# Paso 4: departamentos sin cobertura provincial
r = resto.assign(dep_l=resto["ubigeo_departamento"].map(lambda x: lista(x, 2)),
                 prov_l=resto["ubigeo_provincia"].map(lambda x: lista(x, 4)))
r = r.explode("dep_l")
r = r[r["dep_l"].notna()]
r = r[[not any(x[:2] == dep for x in ps) for dep, ps in zip(r["dep_l"], r["prov_l"])]]
desde_dep = r.drop(columns=["dep_l", "prov_l"]).assign(dep_clean=r["dep_l"]).merge(
    cat[["ubigeo_dist", "ubigeo_dep", "dep_norm", "prov_norm", "dist_norm", "fecha_creacion"]].drop_duplicates(),
    left_on="dep_clean", right_on="ubigeo_dep", how="inner")
desde_dep = existia(desde_dep).rename(columns={"ubigeo_dist": "ubigeo_distrito_final"}).drop(columns=["dep_clean", "ubigeo_dep"])
print("Filas expandidas desde departamento:", len(desde_dep))

# Paso 5: unir y quitar duplicados (decreto × grupo × distrito)
ee_distrital = pd.concat([nac, con_dist, desde_prov, desde_dep], ignore_index=True)
ee_distrital = ee_distrital.drop(columns=[c for c in ("ubigeo_distrito", "ubigeo_provincia", "ubigeo_departamento",
                                                     "ubigeo_dist", "ubigeo_prov", "ubigeo_dep") if c in ee_distrital])
ee_distrital = ee_distrital.drop_duplicates(["decreto_supremo", "id_grupo_ee", "ubigeo_distrito_final"])
ee_distrital["fecha_final_real"] = ee_distrital["fecha_final"]

print("\n=== RESUMEN EXPANSIÓN ===")
print("Total filas ee_distrital:  ", len(ee_distrital))
print("Distritos únicos cubiertos:", ee_distrital["ubigeo_distrito_final"].nunique())
print("Grupos únicos:             ", ee_distrital["id_grupo_ee"].nunique())
chk = ee_distrital.merge(cat[["ubigeo_dist", "fecha_creacion"]], left_on="ubigeo_distrito_final", right_on="ubigeo_dist")
print("Distritos en EE anterior a su creación:", int((chk["fecha_creacion"] > chk["fecha_promulgacion"]).sum()))
sin_cat = set(ee_distrital["ubigeo_distrito_final"]) - set(cat["ubigeo_dist"])
print("Ubigeos de la base que no están en el catálogo:", sorted(sin_cat))

if SALIDA_COMPLETA:
    ee_distrital.to_csv(SALIDA_COMPLETA, index=False)

# ── Extracto para el dashboard (enero–mayo 2025) ─────────────────────────────
w = ee_distrital[(ee_distrital["fecha_promulgacion"] >= INI) & (ee_distrital["fecha_promulgacion"] <= FIN)].copy()


def tipo(r):
    if r["tipo_emergencia"] == "Perturbación del orden interno":
        return "Perturbación del orden interno"
    if r["motivo_declarado"] == "Consecuencias de precipitaciones pluviales":
        return "Lluvias"
    return "Otros"


w["tipo"] = w.apply(tipo, axis=1)
w = w[w["tipo"] != "Otros"]
w["ubigeo"] = w["ubigeo_distrito_final"]
w["departamento"], w["provincia"], w["distrito"] = w["dep_norm"].str.title(), w["prov_norm"].str.title(), w["dist_norm"].str.title()
w["disposicion"] = w["disposicion"].str.capitalize()
out = w[["ubigeo", "departamento", "provincia", "distrito", "id_disposicion", "decreto_supremo",
         "fecha_promulgacion", "disposicion", "tipo"]].drop_duplicates()
out["fecha_promulgacion"] = out["fecha_promulgacion"].dt.date
out.to_csv(DATOS / "ee_distrital_2025.csv", index=False)
print("\nExtracto del dashboard:", out.shape, out["tipo"].value_counts().to_dict(),
      "| decretos:", out["id_disposicion"].nunique(), "| distritos:", out["ubigeo"].nunique())
