# docs/

Documentación del proyecto. Hay dos documentos principales, con roles distintos:

| Documento | Para quién | Qué responde |
|---|---|---|
| [`modelo.md`](modelo.md) | Equipo, docentes, cualquier lector | **Qué** se modela y **por qué**: supuestos, variables, TEI/TEF, escenarios, criterio de decisión y registro de decisiones (D-01, D-02…). |
| [`sdd.md`](sdd.md) | Quien programe (persona o agente de IA) | **Cómo** se implementa: rutinas de evento paso a paso, estructuras de datos, invariantes, pruebas. Referencia las decisiones de `modelo.md` por número; no las repite. |

Documentos de apoyo:

- [`fdps-decisiones.pdf`](fdps-decisiones.pdf): diagnóstico del dataset de Kaggle (son cotizaciones, no viajes) y guía para ajustar cada FDP.
- [`fdps-mock.md`](fdps-mock.md): FDPs provisorias para el MVP. **Desactualizado**: la búsqueda debe pasar a gamma/lognormal y falta definir la demora por tráfico. Se corrige junto con el SDD.
- [`enunciado/`](enunciado/): consigna oficial del TP5.
- [`img/`](img/): diagramas e imágenes que usan los documentos.

## Orden de lectura sugerido

1. `enunciado/` → qué pide la cátedra.
2. `modelo.md` → cómo lo encaramos y por qué.
3. `sdd.md` → solo si vas a programar o revisar el código.
