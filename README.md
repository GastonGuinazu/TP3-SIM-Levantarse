# TP3 - Simulacion de Montecarlo (LEVANTARSE) — Grupo 4K2

Aplicacion PyQt5 para simular la rutina diaria de preparar a Luna para ir al jardin.

## Ejecutar

```bash
py -3 -m pip install -r requirements.txt
py -3 main.py
```

## Pruebas automatizadas (QA)

En Windows se recomienda **Python 3.11 o 3.12** (wheels de NumPy y PyQt5). Con 3.13 puede fallar la instalacion.

```bash
py -3.11 -m pip install -r requirements.txt
py -3.11 -m unittest discover -s tests -v
```

- `tests/test_qa_simulacion.py`: validacion de parametros, escenarios deterministas, ventana de filas, N=100000, coherencia indicadores vs ultima fila (sin depender de la UI).
- `tests/test_qa_ui_smoke.py`: construccion de la ventana PyQt5 (se omite si no hay PyQt5).

**Prueba visual manual (no automatizable del todo):** abrir la app, cambiar N/i/semilla, comprobar que el mensaje bajo “Simular” coincide con el tramo mostrado; hacer scroll en el vector de estado y verificar encabezados fijos, seleccion y `Ctrl+C` en Excel.

## Parametros configurables (desde la UI)

- `N`: cantidad de dias a simular.
- `i`: fila inicial del vector de estado a visualizar (`i..i+199` mas fila `N` si falta).
- Umbral de tardanza (minutos): para el indicador `% dias que superan umbral`.
- Semilla (`seed`): reproducibilidad de todos los RND del modelo.

**Demora extra / imprevisto:**

- `P(Demora extra)` y `Media demora extra exp.` (exponencial en minutos cuando el evento ocurre).

**Distribuciones con limites editables:**

- `Pausa U(min)`, `Pausa U(max)`: duracion si hay pausa intermedia (la probabilidad de pausa esta fija en codigo por enunciado).
- `Actividad U(min)`, `Actividad U(max)`: vestirse, desayuno e higiene cada uno con uniforme independiente.

**Valores fijos por enunciado en `monte_carlo.py`:** probabilidades de estrategia de despertar (`30% / 50% / 20%`), probabilidad de pausa intermedia, probabilidad de reaccion lenta cuando la estrategia no es suave y el incremento al tiempo base, y los rangos de tiempo base de despertar por estrategia (`Suave` 2-4 min, `Insistente` 1-3, `Luz encendida` 1-2).

Ver columnas `RND ...` en el vector de estado para cada sorteo visible en pantalla (incluido el uniforme interno de la exponencial cuando `Hubo extra` es Si).

## Demora extra y texto del enunciado (para la defensa)

En el PDF, el apartado de **25 de cada 100 dias** describe un imprevisto (buscar algo perdido, etc.) con **tiempo exponencial de media 8 minutos**. En el codigo eso es un solo bloque:

- **`P(Demora extra)`** = probabilidad de que ese dia exista ese imprevisto (por defecto **0,25**, como “25 de 100 dias”).
- **`Media demora extra exp.`** = parametro **media** (valor esperado en minutos) de la **exponencial** que muestrea los minutos sumados al dia cuando el evento ocurre (por defecto **8**).

Cuando `Hubo extra` es Si, la columna **RND exp extra** del vector es el uniforme \(U(0,1)\) que entra en la formula \(-\text{media}\cdot\ln(1-U)\). La columna **RND extra** es el uniforme distinto usado solo para decidir si ese dia ocurre la demora extra (comparado con `P(Demora extra)`).

En la interfaz y en el vector de estado aparece como **«extra»** / **«demora extra»**: mismo sentido que el parrafo del PDF. Las preguntas 2 y 3 del TP relacionan **pausa intermedia** con este evento (**juguete perdido** en la tabla de indicadores).

## Resultados que informa

- 1) Tiempo promedio de preparar a Luna.
- 2) Porcentaje de dias con pausa y demora extra (juguete / imprevisto del 25%).
- 3) Cantidad de dias sin pausa y sin demora extra.
- 4) Tiempo maximo de preparacion.
- 5) Tiempo minimo de preparacion.
- 6) Tres variables adicionales:
  - `% dias con reaccion lenta al despertar`
  - `% dias que superan umbral de tardanza`
  - `promedio de demora extra cuando ocurre`

## Vector de estado y rendimiento

- Se visualiza el tramo solicitado dias `i` a `i+199` (200 filas) y, si corresponde, siempre la fila final `N`.
- La simulacion trabaja por acumuladores y no almacena las `N` filas completas; en el vector de estado figuran **todas** las columnas de acumuladores del modelo.
- Grillas sin paginacion, con scroll horizontal/vertical y encabezados fijos.
- Seleccion persistente y copia a Excel con `Ctrl + C`.

## Archivos del proyecto

- `main.py` — arranque de la app.
- `montecarloui.py` — interfaz PyQt5.
- `monte_carlo.py` — motor Montecarlo (LEVANTARSE).
- `funciones.py` — generador aleatorio (uniforme y exponencial).
- `requirements.txt` — dependencias.