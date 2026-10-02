# notebooks/

El notebook vigente es [`fdps.ipynb`](fdps.ipynb): explica de dónde sale cada FDP del simulador y genera los valores de [`config/fdp_v2.toml`](../config/fdp_v2.toml). Reemplaza a los notebooks del TP4; al principio tiene una sección, "Qué cambió respecto del notebook del TP4".

## Cómo correrlo

1. Poner el dataset en `data/raw/dataset-uber_lyft.csv` (ver [`data/README.md`](../data/README.md)).
2. Instalar las dependencias: `pip install -r requirements.txt`.
3. Abrirlo desde esta carpeta y ejecutarlo de arriba hacia abajo. No usa Google Drive ni Fitter.

La última sección compara los parámetros del ajuste con los de `config/fdp_v2.toml`: si alguien cambia uno sin el otro, se nota.

## Antes de cambiar una FDP

Las reglas están en [`docs/modelo.md`](../docs/modelo.md), sección 4.3, y el formato del catálogo en [`docs/sdd.md`](../docs/sdd.md), sección 5.6. Un cambio de FDP actualiza en el mismo commit el notebook, el catálogo y el modelo (sección 4.5.3).

## Al subirlo

Dejá las salidas visibles: GitHub muestra el notebook renderizado y es la evidencia del trabajo para los docentes.
