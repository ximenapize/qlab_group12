# Parte 4: Bitácora de IA

## Entrada 1 – Parte 1: Scraping

**1. ¿Qué le pedimos a la IA?**

xx

**2. ¿Qué nos respondió?**

xx 

**3. ¿Qué estaba mal y cómo nos dimos cuenta?**

xxx

**4. ¿Cómo lo corregimos?**


## Entrada 2 – Parte 2: API

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

## Entrada 3 – Parte 3: Cruce y análisis

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
