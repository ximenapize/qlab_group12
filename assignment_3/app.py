"""Dashboard: estados de emergencia en el Perú (enero–mayo 2025), a nivel departamento, provincia y distrito."""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

BASE = Path(__file__).parent / "datos"
FUENTE = ("Fuentes: Alcantara, K., Aragón, J., Cruz, M., Gutiérrez, N., Ilizarbe, C., Pinillos, X. & Retamozo, D. (2026). "
          "Base de Estados de Emergencia en el Perú (Versión julio 2026) [Base de datos]. EGPP-PUCP. "
          "Lluvia: Open-Meteo. Mapas: INEI 2023.")
NIVELES = {"Departamento": 2, "Provincia": 4, "Distrito": 6}
GEO = {"Departamento": "departamentos_ubigeo.geojson", "Provincia": "mapa_provincias.geojson",
       "Distrito": "mapa_distritos.geojson"}

st.set_page_config(page_title="Estados de emergencia en el Perú", layout="wide")


@st.cache_data
def cargar_ee():
    df = pd.read_csv(BASE / "ee_distrital_2025.csv", dtype=str)
    df["id_disposicion"] = df["id_disposicion"].astype(float).astype(int)
    return df


@st.cache_data
def cargar_lluvia():
    return pd.read_csv(BASE / "tabla_final.csv", dtype={"ubigeo": str}, encoding="utf-8-sig")


@st.cache_data
def cargar_lluvia_distrital():
    return pd.read_csv(BASE / "lluvias_distritos.csv", dtype={"ubigeo": str})


@st.cache_data
def cargar_geojson(nivel):
    with open(BASE / GEO[nivel], encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def ubigeos_con_poligono(nivel):
    return {ft["properties"]["ubigeo"] for ft in cargar_geojson(nivel)["features"]}


ee = cargar_ee()
lluvia = cargar_lluvia()
lluvia_dist = cargar_lluvia_distrital()

st.title("Estados de emergencia en el Perú")
st.caption("Enero–mayo 2025 · Lluvias vs. perturbación del orden interno, por departamento, provincia y distrito")

# ---------- Filtros (barra lateral) ----------
st.sidebar.header("Filtros")
tipos = st.sidebar.multiselect("Tipo de estado de emergencia", sorted(ee["tipo"].unique()),
                               default=sorted(ee["tipo"].unique()))
disp = st.sidebar.multiselect("Disposición", ["Declaratoria", "Prórroga"], default=["Declaratoria", "Prórroga"])
f = ee[ee["tipo"].isin(tipos) & ee["disposicion"].isin(disp)]

deps = st.sidebar.multiselect("Departamento", sorted(f["departamento"].unique()))
if deps:
    f = f[f["departamento"].isin(deps)]
provs = st.sidebar.multiselect("Provincia", sorted(f["provincia"].unique()),
                               help="Se limita a los departamentos elegidos")
if provs:
    f = f[f["provincia"].isin(provs)]
dists = st.sidebar.multiselect("Distrito", sorted(f["distrito"].unique()),
                               help="Se limita a lo elegido arriba")
if dists:
    f = f[f["distrito"].isin(dists)]

nivel = st.sidebar.radio("Nivel del mapa y ranking", list(NIVELES), index=2)
n = NIVELES[nivel]

if f.empty:
    st.warning("Ningún registro cumple los filtros. Amplía la selección.")
    st.stop()

# ---------- Métricas ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Decretos supremos distintos", f["id_disposicion"].nunique())
c2.metric("Distritos con emergencia", f["ubigeo"].nunique())
c3.metric("Provincias", f["ubigeo"].str[:4].nunique())
c4.metric("Declaratorias / Prórrogas (distrito-norma)",
          f"{(f['disposicion'] == 'Declaratoria').sum():,} / {(f['disposicion'] == 'Prórroga').sum():,}")

# Agregado por unidad del nivel elegido
f = f.assign(unidad=f["ubigeo"].str[:n])
nombre = {2: "departamento", 4: "provincia", 6: "distrito"}[n]
etiqueta = f.groupby("unidad").agg(
    departamento=("departamento", "first"), provincia=("provincia", "first"), distrito=("distrito", "first"))
agg = (f.groupby(["unidad", "tipo"]).id_disposicion.nunique().rename("normas").reset_index())
total = agg.groupby("unidad")["normas"].sum().rename("total").reset_index().merge(etiqueta, on="unidad")
total["nombre"] = total[nombre] if nivel == "Departamento" else (
    total["provincia"] + " (" + total["departamento"] + ")" if nivel == "Provincia"
    else total["distrito"] + " (" + total["provincia"] + ")")

tab_mapa, tab_graf, tab_tabla = st.tabs(["Mapa", "Gráficos", "Tabla"])

with tab_mapa:
    geo = cargar_geojson(nivel)
    sin_poligono = sorted(set(total["unidad"]) - ubigeos_con_poligono(nivel))
    fig_map = px.choropleth_map(
        total, geojson=geo, locations="unidad", featureidkey="properties.ubigeo", color="total",
        hover_name="nombre", hover_data={"unidad": False, "total": True},
        color_continuous_scale="YlOrRd", map_style="carto-positron", zoom=4.2,
        center={"lat": -9.2, "lon": -75.0}, opacity=0.8,
        labels={"total": "Decretos distintos"},
        title=f"Decretos de emergencia por {nombre} (enero–mayo 2025)",
    )
    fig_map.update_layout(height=650, margin=dict(t=60, r=0, l=0, b=0))
    st.plotly_chart(fig_map, width="stretch")
    if sin_poligono:
        st.caption(f"{len(sin_poligono)} unidades no se dibujan porque no existen en el mapa base "
                   f"{', '.join(sin_poligono)}. Sí cuentan en métricas y tabla.")

with tab_graf:
    g1, g2 = st.columns(2)
    with g1:
        top = total.nlargest(15, "total")["unidad"]
        b = agg[agg["unidad"].isin(top)].merge(total[["unidad", "nombre"]], on="unidad")
        orden = total.set_index("unidad").loc[top, "nombre"].tolist()[::-1]
        fig_bar = px.bar(b, x="normas", y="nombre", color="tipo", orientation="h",
                         category_orders={"nombre": orden},
                         labels={"normas": "Decretos distintos", "nombre": nombre.capitalize(), "tipo": "Tipo"},
                         title=f"Top 15 {nombre}s con más decretos de emergencia")
        fig_bar.update_layout(height=600, margin=dict(t=60), legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig_bar, width="stretch")
    with g2:
        dd = (f.groupby(["ubigeo", "departamento", "provincia", "distrito"]).id_disposicion.nunique()
              .rename("normas").reset_index().merge(lluvia_dist, on="ubigeo"))
        dd["lugar"] = dd["distrito"] + " (" + dd["provincia"] + ")"
        fig_sc = px.scatter(
            dd, x="lluvia_total_mm", y="normas", color="departamento", hover_name="lugar",
            hover_data={"departamento": False, "dias_lluvia_fuerte": True},
            labels={"lluvia_total_mm": "Lluvia total en el distrito (mm)", "normas": "Decretos distintos",
                    "dias_lluvia_fuerte": "Días con lluvia fuerte", "departamento": "Departamento"},
            title="Más lluvia en el distrito no implicó más decretos de emergencia")
        fig_sc.update_layout(height=600, margin=dict(t=60))
        st.plotly_chart(fig_sc, width="stretch")

with tab_tabla:
    st.subheader("Datos filtrados (una fila por distrito)")
    tabla = (f.pivot_table(index=["ubigeo", "departamento", "provincia", "distrito"], columns="disposicion",
                           values="id_disposicion", aggfunc="nunique", fill_value=0).reset_index())
    for c in ("Declaratoria", "Prórroga"):
        if c not in tabla:
            tabla[c] = 0
    tabla["Total"] = tabla["Declaratoria"] + tabla["Prórroga"]
    st.dataframe(tabla.sort_values("Total", ascending=False), width="stretch", hide_index=True)
    st.download_button("Descargar CSV", tabla.to_csv(index=False).encode("utf-8-sig"), "ee_filtrado.csv", "text/csv")

st.caption(FUENTE)
