# Parte 4: Bitácora de IA

## Entrada 1 – Parte 1: Scraping

**1. ¿Qué le pedimos a la IA?**

Al revisar `datos/decretos_lluvias.csv` notamos que no aparecía el **DS 007-2025-PCM**, una declaratoria por lluvias de enero de 2025. Le pedimos a Claude que revisara el notebook de scraping para ver por qué no salía y que lo corrigiera, dejando una nota de cómo se identificó.

**2. ¿Qué nos respondió?**

 Claude encontró que el decreto sí se scrapeaba, pero que en **las dos páginas de gob.pe** (el buscador y la página de la norma) su título era solo *"Declaratoria del Estado de Emergencia"*, sin lugar ni motivo, así que `es_lluvia` quedaba en `False`. Lo mismo pasaba con el DS 008-2025-PCM. Propuso abrir el PDF del decreto con `pypdf` cuando el título no empieza con "Decreto Supremo". Como el título del PDF viene en MAYÚSCULAS, también cambió la búsqueda de departamentos para que no distinga mayúsculas:

  ```python
  re.search(r"\b" + re.escape(d) + r"\b", titulo, re.IGNORECASE)
  ```

**3. ¿Qué estaba mal y cómo nos dimos cuenta?**

Leer el PDF estaba bien: el 007 es *"por peligro inminente ante intensas precipitaciones pluviales"* en 19 departamentos y el Callao, y el 008 es por colapso del alcantarillado en Chiclayo (no es de lluvias). Pero el `re.IGNORECASE` se apartaba de la consigna, que pide buscar los departamentos **en el título original (con mayúsculas)** y por palabra completa. Además, contradecía nuestra propia explicación de la celda "Cómo evitamos contar mal". Nos dimos cuenta al pasarle a Claude las indicaciones completas de la tarea y compararlas con el cambio.

**4. ¿Cómo lo corregimos?**

Se volvió a la búsqueda con mayúsculas que pide la consigna. En su lugar, el título del PDF se pasa a minúsculas con `.capitalize()` y se vuelven a escribir los departamentos tal como están en la lista `departamentos` (por ejemplo, "Áncash", "La Libertad", "Callao"). Luego se volvió a correr todo el notebook y se verificó el resultado: las normas de lluvias pasaron de 17 a 18, el 007 suma una declaratoria a cada uno de sus 20 departamentos y nada más cambió; el 008 siguió fuera de lluvias. Con los datos nuevos se actualizaron también los textos de `cruce_analisis.ipynb` (correlación 0.20 y 26.8 % de declaratorias por peligro inminente, contando por departamento).


## Entrada 2 – Parte 1: Scraping (robots.txt)

  **1. ¿Qué le pedimos a la IA?**

  Le pedimos a la IA el código para recorrer la búsqueda de gob.pe mes por mes con Selenium y la explicación del `robots.txt`.

  **2. ¿Qué nos respondió?**

  La explicación decía correctamente que el `robots.txt` prohíbe las URL con `?sheet=` o `&sheet=` (la paginación). Pero el código que dio armaba esas mismas URL cuando un mes tenía más resultados de los que caben en una página:

  ```python
  if sheet and sheet > 1:
      url += f"&sheet={sheet}"
  ```

  **3. ¿Qué estaba mal y cómo nos dimos cuenta?**

  El código contradecía la propia explicación: si un mes hubiera tenido más resultados, el script habría entrado a URL que el `robots.txt` prohíbe. Nos dimos cuenta al releer la celda del `robots.txt` junto con la función `build_url`. En nuestra temporada no llegó a pasar, porque el mes con más resultados (abril, con 17) cupo completo en la primera página, como muestra la tabla de verificación.

  **4. ¿Cómo lo corregimos?**

  Se quitó la paginación del código, para que el script nunca pida una URL con `sheet`, y se corrigió la explicación del `robots.txt`. La tabla de verificación sigue mostrando que en  todos los meses `resultados_totales` coincide con `resultados_extraidos`, así que no se perdió ningún resultado.



## Entrada 3 – Parte 2: API

**1. ¿Qué le pedimos a la IA?**

En el paso 2, la tabla de departamentos de Wikipedia (`tablas[1]`) tenía 24 filas porque no incluía al Callao. Se tomó la fila del Callao de otra tabla del mismo artículo (`tablas[3]`, la de provincias con régimen especial) y se le pidió a Claude cómo agregarla a la tabla `capitales`, para llegar a las 25 filas que pide la verificación.

**2. ¿Qué nos respondió?**

Claude sugirió unir las dos tablas con `pd.concat`, en una celda aparte:

```python
capitales = pd.concat([capitales, callao], ignore_index=True)
print(capitales.shape)
```

**3. ¿Qué estaba mal y cómo nos dimos cuenta?**

El código funcionaba bien solo si la celda se ejecutaba una vez. Como el resultado se guarda con el mismo nombre (`capitales`), cada vez que se vuelve a ejecutar la celda se parte de la tabla que ya tiene el Callao y se agrega otro. Claude no advirtió eso, y en un notebook es común volver a ejecutar una celda mientras se prueba.

Nos dimos cuenta porque `print(capitales.shape)` mostró 28 filas en lugar de 25. Al consultar a Claude, explicó que la celda se había ejecutado 4 veces:

| Ejecución | Filas |
|---|---|
| 1.ª | 24 + 1 = 25 ✅ |
| 2.ª | 25 + 1 = 26 |
| 3.ª | 26 + 1 = 27 |
| 4.ª | 27 + 1 = 28 |

**4. ¿Cómo lo corregimos?**

Se volvieron a ejecutar las celdas en orden, desde la que crea `capitales` a partir de `tablas[1]` (24 filas) hasta la del `pd.concat`, una sola vez cada una. Así la tabla quedó con 25 filas, y se comprobó con `print(capitales.shape)`, que mostró `(25, 2)`. Al final, el notebook se ejecutó completo con Restart → Run All para asegurar que cada celda corriera una sola vez y en orden.

## Entrada 4 – Parte 3: Cruce y análisis

**1. ¿Qué le pedimos a la IA?**

En el paso 9 se le pidió a Claude el código para ver qué departamentos tienen más declaratorias de emergencia y cuáles tienen más lluvia, ordenando la tabla final según cada criterio.

**2. ¿Qué nos respondió?**

Claude armó una lista de columnas para mostrar solo algunas y las imprimió con `print`:

```python
columnas = ["departamento", "declaratorias", "prorrogas", "lluvia_total_mm", "dias_lluvia_fuerte"]

# 9.1 Los que tienen más declaratorias y los que tienen más lluvia
print("Más declaratorias:")
print(tabla_final.sort_values(["declaratorias", "lluvia_total_mm"], ascending=False)[columnas].head(9), "\n")

print("Más lluvia:")
print(tabla_final.sort_values("lluvia_total_mm", ascending=False)[columnas].head(5), "\n")

```

**3. ¿Qué estaba mal y cómo nos dimos cuenta?**

Al ejecutar la celda, una de las tablas se mostraba por partes: `print` convierte el DataFrame en texto y, cuando no entra a lo ancho, lo corta en bloques de columnas, lo que dificultaba leerla. Además, nos pareció innecesario recortar columnas. Al volver a preguntarle a Claude, respondió que había elegido solo esas columnas justamente para que la tabla no se cortara al mostrarla, pero igual se seguía cortando.

También notamos que la tabla de "Más declaraciones" usaba `head(9)`. Aunque se entiende que la IA eligió ese número con algún criterio, con 9 filas aun no se alcanzaban a ver donde acaban los empates, y eso debe poder apreciarse para quien corre o lee el código.

**4. ¿Cómo lo corregimos?**

Le pedimos que mostrara los datos tal cual, como DataFrame, usando `display` en lugar de `print`, para que el notebook los muestre como tabla completa y sin cortes. Además, le dimo un orden especifico para las columnas para mejor visibilizacion en lugar de generar una lista que recorta variables. También cambiamos el `head` a 10 en ambas tablas, para que se vean todos los empates:

```python
# Primero ordenamos las columnas (una sola vez)
resumen = tabla_final[["ubigeo", "departamento", "declaratorias", "prorrogas",
                       "lluvia_total_mm", "dias_lluvia_fuerte"]]

# 9.1 Los que tienen más declaratorias y los que tienen más lluvia
print("Más declaratorias:")
display(resumen.sort_values(["declaratorias", "lluvia_total_mm"], ascending=False).head(10))

print("Más lluvia:")
display(resumen.sort_values("lluvia_total_mm", ascending=False).head(10))
```
