# Lluvias y declaratorias de emergencia en el Perú (enero–mayo 2025)

**Dashboard público:** _(pegar aquí el enlace de share.streamlit.io una vez desplegado)_

## 1. Pregunta
Entre enero y mayo de 2025, ¿dónde se declaró estado de emergencia, por qué motivo (lluvias o perturbación del orden interno) y coincide con dónde llovió más?

## 2. Datos
- `datos/ee_distrital_2025.csv`: base propia de estados de emergencia expandida a **distrito** (declaratorias y prórrogas con fecha de promulgación entre el 1 ene y el 31 may 2025; 50 decretos, 1 804 distritos). Tipo "Lluvias" = emergencia por precipitaciones pluviales; el otro tipo es "Perturbación del orden interno". Se genera con `scripts_auxiliares/construir_ee_distrital.py`, que expande a distrito los decretos supremos de la base de datos citada abajo (pasos 1 a 3 de la metodología del proyecto).
- `datos/lluvias_distritos.csv`: lluvia total y días de lluvia fuerte (≥ 20 mm) entre el 1 ene y el 31 may 2025 en el punto central de cada uno de los 1 891 distritos, API histórica de [Open-Meteo](https://open-meteo.com/) (script `scripts_auxiliares/lluvias_distritos.py`; no hubo días sin dato).
- `datos/tabla_final.csv` (Assignment 2): lluvia en la capital de cada departamento (Open-Meteo) y conteo de declaratorias y prórrogas por lluvias, obtenido de los decretos supremos de la PCM publicados en [gob.pe](https://www.gob.pe/) que entregó el curso. Se usa solo para validar: sus 228 decretos (157 + 71) coinciden con los de lluvias de la base del PUCP.
- `datos/mapa_distritos.geojson`, `mapa_provincias.geojson`, `departamentos_ubigeo.geojson`: polígonos simplificados derivados del shapefile distrital INEI 2023 (1 891 distritos), cruzados por ubigeo como texto; los 1 804 distritos de la base de emergencias cruzan todos (0 sin polígono).

## Cómo se construyen los datos
La app **solo lee** los archivos ya generados en `datos/`; no descarga ni recalcula nada al abrirse (así carga rápido y no depende de APIs en la nube). Para rehacerlos desde cero:

```bash
pip install -r scripts_auxiliares/requirements-datos.txt
python scripts_auxiliares/actualizar_datos.py --base DisposicionesEstadosDeEmergencia.xlsx \
                           --catalogo catalogo_ubigeo_maestro.csv \
                           --shp "ruta/Distrital INEI 2023.shp" [--sin-lluvia]
```

| Paso | Script | Qué hace | Insumo (no está en el repo) |
|---|---|---|---|
| 1 | `scripts_auxiliares/construir_ee_distrital.py` | Expande los decretos a distrito → `ee_distrital_2025.csv` | Base de Estados de Emergencia (PUCP) y catálogo de ubigeos |
| 2 | `scripts_auxiliares/prep_datos.py` | Genera los mapas livianos de distrito, provincia y departamento | Shapefile distrital INEI 2023 |
| 3 | `scripts_auxiliares/lluvias_distritos.py` | Descarga la lluvia de cada distrito (Open-Meteo) → `lluvias_distritos.csv` | Ninguno (API gratuita, sin clave) |

### De dónde sale la base de emergencias y cómo se llega al distrito
- **Fuente:** la *Base de Estados de Emergencia en el Perú (Versión julio 2026)* registra los decretos supremos de estado de emergencia entre 2000 y 2025, una fila por decreto y territorio, con su disposición (declaratoria, prórroga, modificatoria o término), tipo, motivo, fechas y ubigeos. Es el resultado de la colaboración entre el Observatorio para la Democracia y Gobernabilidad (EGPP-PUCP) y el proyecto de investigación “Cuando la excepción es la norma: veinte años de democracia y estado de emergencia en el Perú” (Carmen Ilizarbe). Los decretos de la base se recopilaron del diario oficial *El Peruano* y del SPIJ (Sistema Peruano de Información Jurídica). Está disponible en el sitio del Observatorio: <https://democracia-gobernabilidad.pucp.edu.pe/poderes-del-estado/ejecutivo/ministerios/estados-de-emergencia>. Se cita abajo.
- **Problema:** cada decreto menciona territorios a distinto nivel (todo el país, un departamento, algunas provincias o una lista de distritos).
- **Solución (`scripts_auxiliares/construir_ee_distrital.py`):** cada fila se expande a **una fila por distrito**, con esta prioridad:
  1. decreto nacional (“todo el país”) → todos los distritos;
  2. distritos listados explícitamente → esos distritos;
  3. provincias sin distritos listados → todos los distritos de esa provincia;
  4. departamentos sin provincias listadas → todos los distritos del departamento.
  Solo se incluyen los distritos que **ya existían en la fecha del decreto** (según el catálogo de ubigeos con la fecha de creación de cada distrito) y se eliminan duplicados por decreto, grupo y distrito.
- **Metodología de referencia:** estos son los pasos 1 a 3 del código `protestas_ee_v2.Rmd` del proyecto sobre protestas y estados de emergencia (R). No se replican los pasos 4 y 5 (términos y modificatorias), que solo corrigen la fecha efectiva de fin; aquí los decretos se cuentan por fecha de promulgación.
- **Tipos:** “Lluvias” = `motivo_declarado` igual a “Consecuencias de precipitaciones pluviales”; “Perturbación del orden interno” = `tipo_emergencia` con ese nombre. Se descartan las demás causas (sequías, incendio, saneamiento).
- **Validación:** el resultado coincide fila por fila con la tabla distrital del proyecto original para el periodo (50 decretos, 1 804 distritos) y los decretos de lluvias por departamento suman 228, igual que las declaratorias más prórrogas de `tabla_final.csv` del Assignment 2.

### Cita de la base de datos
Alcantara, K., Aragón, J., Cruz, M., Gutiérrez, N., Ilizarbe, C., Pinillos, X. & Retamozo, D. (2026). *Base de Estados de Emergencia en el Perú (Versión julio 2026)* [Base de datos]. Escuela de Gobierno y Políticas Públicas - Pontificia Universidad Católica del Perú (PUCP).

## 3. Hallazgos
1. **Dos tipos de emergencia, dos geografías.** Las emergencias por lluvias (18 decretos) alcanzan 1 782 distritos de 189 provincias, con más distritos en Lima (171), Áncash (157), Ayacucho (121) y Junín (115). Las de orden interno (32 decretos, casi todos prórrogas) se concentran en 556 distritos de 51 provincias, sobre todo Lima, Cusco, Arequipa y Apurímac.
2. **Más lluvia no significó más emergencias por lluvias.** A nivel distrital la correlación de Spearman entre lluvia y número de decretos por lluvias es 0.08 (1 782 distritos): las declaratorias no siguen la intensidad de la lluvia medida. A nivel departamental pasa lo mismo: Madre de Dios, el segundo más lluvioso (1 751 mm en su capital), tuvo pocos decretos, y Lima, con 54 mm, tuvo muchos.

## 4. Limitaciones
- La lluvia distrital se mide en **un solo punto por distrito** (el centro del polígono): distritos grandes o con mucho relieve pueden variar dentro de sí. Es un reanálisis de Open-Meteo (cuadrícula de unos 9–25 km), no una estación.
- Solo cubre cinco meses de 2025 y cuenta decretos por distrito, no su magnitud ni sus daños.
- Un mismo decreto cubre muchos distritos, así que la cantidad de distritos no equivale a la de decretos.
- Los nombres de la base vienen sin tildes.

## Cómo ejecutarlo en local
```bash
cd assignment_3
pip install -r requirements.txt
streamlit run app.py
```
(o `uv run streamlit run app.py`)
