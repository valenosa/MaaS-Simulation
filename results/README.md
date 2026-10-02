# results/

Salidas del simulador.

| Carpeta | Contenido | ¿Se sube? |
|---|---|---|
| `finales/` | Corridas que respaldan el informe y la presentación. | Sí |
| `pruebas/` | Corridas intermedias, de depuración o exploración. | No (está en `.gitignore`) |

Cada experimento escribe en su propia carpeta y nunca pisa una que ya existe. Por defecto va a `pruebas/`, con la fecha y la hora; para la entrega se elige una carpeta en `finales/` con la opción `--salida`. Adentro quedan `experimento.json`, con la fecha, las versiones, la configuración, el catálogo de FDP y las semillas, `corridas.csv` y una subcarpeta por cada criterio analizado. El detalle está en [`docs/sdd.md`](../docs/sdd.md), secciones 8.6 y 9.

Regla: un resultado que aparece en el informe tiene que estar en `finales/` y poder regenerarse con el mismo código y las mismas semillas.
