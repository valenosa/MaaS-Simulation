# notebooks/

Análisis exploratorio y ajuste de FDPs (trabajo heredado del TP4).

## Reglas

- **Correr de arriba hacia abajo** con la semilla fijada al principio.
- **Dejar las salidas visibles** (gráficos, tablas) al subir: GitHub muestra el notebook renderizado y es la evidencia del trabajo para los docentes.
- **Leer los parámetros de las FDPs desde el código** (`get_best()` de Fitter), no copiarlos a mano.
- **Elegir distribuciones por BIC y QQ-plot**, no por el p-valor de KS (con miles de datos siempre rechaza).
- **Solo familias con soporte positivo** para distancia y tarifa; nada de `np.clip` para corregir negativos.

El detalle de qué hacer con cada FDP está en [`docs/fdps-decisiones.pdf`](../docs/fdps-decisiones.pdf).
