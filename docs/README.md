# docs/

Documentación del proyecto. Sigue el proceso de la skill `sdd-gobernanza`: el documento del modelo manda, el SDD se deriva de él y el código implementa el SDD. Cada decisión vive en un solo lugar.

| Documento | Para quién | Qué responde |
|---|---|---|
| [`modelo.md`](modelo.md) | Equipo, docentes, cualquier lector | **Qué** se modela y **por qué**: supuestos, datos y FDPs, variables, TEI y TEF, escenarios, criterio de decisión y registro de decisiones (D-01, D-02…). |
| [`sdd.md`](sdd.md) | Quien programe (persona o agente de IA) | **Cómo** se implementa: estructuras de datos, rutinas de evento paso a paso, invariantes, generación de valores aleatorios y pruebas. Cita las decisiones del modelo por número; no las repite. |

## Si vas a trabajar en…

| Tarea | Leer |
|---|---|
| Las FDP definitivas (notebook) | `modelo.md`, secciones 4.3 y 4.5; el formato de entrega está en `sdd.md`, sección 5.6 |
| El simulador | `sdd.md`, desde la sección 0.2 |
| Entender por qué se decidió algo | `modelo.md`, sección 11 |
| Saber qué queda para después de la entrega | `modelo.md`, sección 12.3 (segunda iteración) |
| El documento de la entrega | Formato en [`enunciado/formato_papers_estudiantes.doc`](enunciado/formato_papers_estudiantes.doc) |

## Documentos de apoyo

- [`fdps-decisiones.pdf`](fdps-decisiones.pdf): diagnóstico del dataset de Kaggle (son cotizaciones, no viajes) y criterios para cada FDP. Propone una tarifa por regresión sobre la distancia, que quedó para la segunda iteración.
- [`fdps-mock.md`](fdps-mock.md): ya no es una fuente; apunta a dónde están ahora las FDP provisorias.
- [`enunciado/`](enunciado/): consigna oficial del TP5 y formato del documento de la entrega (formato de paper).
- [`img/`](img/): diagramas e imágenes que usan los documentos.

## Orden de lectura sugerido

1. `enunciado/` → qué pide la cátedra.
2. `modelo.md` → cómo lo encaramos y por qué.
3. `sdd.md` → solo si vas a programar o revisar el código.
