# data/

## raw/ — dataset original (no se sube al repositorio)

El dataset de Kaggle pesa varios cientos de MB y GitHub rechaza archivos de más de 100 MB, por eso esta carpeta está en `.gitignore`.

**Para obtenerlo:**

1. Descargar el dataset _"Uber and Lyft Dataset Boston, MA"_ (nov–dic 2018) desde Kaggle.
2. Guardar el CSV dentro de `data/raw/` sin renombrarlo.
3. Correr el notebook de `notebooks/` de arriba hacia abajo.

_Completar acá el enlace exacto de Kaggle y el nombre del archivo CSV._

**Advertencia:** el dataset son **cotizaciones** consultadas periódicamente a las APIs, no viajes realizados. Por eso **no se usa para el intervalo de arribo**, solo para distancia y tarifa. Ver [`docs/fdps-decisiones.pdf`](../docs/fdps-decisiones.pdf).

## processed/ — datos limpios (se sube si es chico)

Versión reducida que genera el notebook: solo Lyft, solo las columnas necesarias (distancia, tarifa, producto), deduplicada por timestamp + origen + destino.

Se sube al repositorio solo si pesa menos de ~50 MB. Si pesa más, se ignora y se regenera con el notebook.
