# notebooks/

Análisis exploratorio y ajuste de FDPs (trabajo heredado del TP4). El notebook es [`NotebookFDPs.ipynb`](NotebookFDPs.ipynb).

## Antes de trabajar acá

Leé estas secciones. Tienen todo lo necesario y son la única fuente: si algo de este README las contradijera, valen ellas.

| Qué | Dónde |
|---|---|
| Reglas para ajustar FDPs | [`docs/modelo.md`](../docs/modelo.md), sección 4.3 |
| Plan de trabajo: qué hacer, criterios de aceptación y qué entregar | [`docs/modelo.md`](../docs/modelo.md), sección 4.5 |
| Formato exacto del entregable (`config/fdp_v2.toml`) | [`docs/sdd.md`](../docs/sdd.md), sección 5.6 |

## Qué falta, en resumen

- **Para la entrega (primera iteración):** rehacer el ajuste de la distancia con familias positivas (sección 4.5.1) y filtrar el recargo dinámico en la tarifa (sección 4.5.2). La búsqueda y la demora ya están definidas en el modelo: no hay que hacer nada con ellas.
- **Para después (segunda iteración):** la tarifa según la distancia (sección 4.5.6), la validación de la velocidad (sección 4.5.5) y dejar el notebook prolijo y reproducible (sección 4.5.4). Si te sobra tiempo antes de la entrega, podés adelantar cualquiera.

## Al subir el notebook

- Dejá las salidas visibles: GitHub muestra el notebook renderizado y es la evidencia del trabajo para los docentes.
- Antes de subirlo, comprobá que corran las celdas que producen los valores entregados.
