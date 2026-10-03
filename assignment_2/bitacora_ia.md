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

xx

**2. ¿Qué nos respondió?**

xx 

**3. ¿Qué estaba mal y cómo nos dimos cuenta?**

xxx

**4. ¿Cómo lo corregimos?**

xxx
