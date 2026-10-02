# tests/

Pruebas automáticas del simulador, con pytest. Están especificadas, con sus valores esperados, en el SDD ([`docs/sdd.md`](../docs/sdd.md)), sección 12. Acá no se repiten.

| Qué | Dónde (en el SDD) |
|---|---|
| Lista de pruebas de la primera iteración (PR-01 a PR-11) | Sección 12.2 |
| Corrida calculada a mano, evento por evento (PR-01) | Sección 12.3 |
| Casos borde (PR-05 a PR-07) | Sección 12.4 |
| Análisis con datos sintéticos (PR-09) | Sección 12.5 |
| Pruebas de la segunda iteración (PR-12 a PR-15): **no se implementan todavía** | Sección 12.6 |
| Qué pruebas cierran cada etapa de la implementación | Sección 13 |

Las configuraciones y los catálogos de prueba van en `tests/datos/`. Las pruebas se corren con `pytest` desde la raíz del repositorio, con el paquete instalado (SDD, sección 12.1).
