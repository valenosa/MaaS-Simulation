# src/

Código del simulador: el paquete `simulador_maas`, que implementa la primera iteración del SDD ([`docs/sdd.md`](../docs/sdd.md)). Cada módulo indica en su encabezado qué secciones del SDD implementa. Cómo se instala y se corre está en el [README principal](../README.md).

Antes de cambiar algo, leé las reglas del SDD, sección 0.2. Entre otras cosas, los cambios siguen el orden modelo → SDD → código, y lo de la segunda iteración no se programa hasta que el equipo decida empezarla y actualice el SDD (sección 1.4).

| Qué | Dónde (en el SDD) |
|---|---|
| Archivos del paquete y qué hace cada uno | Sección 2.2 |
| Qué módulo puede usar a cuál | Sección 2.3 |
| Cómo se instala el paquete | Sección 2.1 y decisión T-23 |
| Orden de construcción por etapas, y qué pruebas cierran cada una | Sección 13 |
| Subcomandos `experimento`, `corrida` y `analisis` | Sección 8.6 |

La idea general: el motor simula un día y devuelve métricas crudas, sin conocer el criterio de decisión. El análisis lee los archivos de salida y aplica el criterio, así que cambiar los umbrales no requiere volver a simular. Las FDP se cambian en `config/`, sin tocar el código.
