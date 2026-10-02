# Simulador MaaS: cantidad óptima de choferes (Lyft, Boston)

Trabajo Práctico Nº 5 de **Simulación** (UTN FRBA, Ingeniería en Sistemas de Información).

Simulación de eventos discretos (evento a evento) de una plataforma de movilidad tipo Lyft, para encontrar la **cantidad de choferes (NCH)** que mantiene una espera aceptable para los clientes sin disparar el tiempo ocioso de la flota.

> **Estado:** etapa de diseño. El modelo y la especificación técnica se están cerrando antes de escribir código (Spec-Driven Development). La entrega se hace en dos iteraciones: ver "Segunda iteración", más abajo.

---

## Por dónde empezar

| Si querés… | Leé |
|---|---|
| Entender **qué** se modela y **por qué** se tomó cada decisión | [`docs/modelo.md`](docs/modelo.md) |
| Saber **cómo** se implementa el simulador (contrato técnico) | [`docs/sdd.md`](docs/sdd.md) |
| Completar las FDP definitivas en el notebook | [`docs/modelo.md`](docs/modelo.md), secciones 4.3 y 4.5, y el formato de entrega en [`docs/sdd.md`](docs/sdd.md), sección 5.6 |
| Ver qué queda para después de la entrega | "Segunda iteración", más abajo |
| Ver por qué la demanda es un supuesto y cómo se ajustan las FDPs | [`docs/fdps-decisiones.pdf`](docs/fdps-decisiones.pdf) |
| Leer la consigna del TP y el formato del documento | [`docs/enunciado/`](docs/enunciado/) |

---

## Segunda iteración

El trabajo se entrega en dos tandas ([`docs/modelo.md`](docs/modelo.md), decisión D-16):

- **Primera iteración (la entrega):** todo lo necesario para una conclusión correcta y defendible, y todo lo que pide la consigna.
- **Segunda iteración:** mejoras que no cambian la decisión sobre la flota. Se hacen **una vez que la simulación funcione**. Si te sobra tiempo antes de la entrega, podés tomar cualquiera: ninguna bloquea nada.

| Mejora | Qué aporta | Procedimiento |
|---|---|---|
| **Tarifa según la distancia** (regresión) | Hoy la tarifa de cada viaje no depende de su largo: un viaje corto puede salir caro. Con la mejora, cada viaje queda coherente | Modelo, sección 4.5.6; en el simulador, SDD, sección 5.10 |
| Validar la velocidad media con datos | Respaldo para un supuesto (13 mi/h) | Modelo, sección 4.5.5 |
| Sensibilidad al umbral de tolerancia | Saber si la conclusión depende del umbral de 15 minutos | Correr el experimento con 10 y 20 minutos |
| Notebook reproducible | Prolijidad del trabajo del TP4 | Modelo, sección 4.5.4 |
| Distribución empírica para la distancia | Alternativa si ninguna familia ajusta bien | Modelo, sección 4.5.1; SDD, sección 5.10 |
| Validación completa de la configuración y del catálogo | Más protección contra errores | SDD, secciones 3.3 y 5.10 |
| Contraste con Erlang C y casos borde exhaustivos | Más evidencia de que el simulador es correcto | Modelo, sección 9.7; SDD, sección 12 |

La lista completa y su justificación están en [`docs/modelo.md`](docs/modelo.md), sección 12.3. Quien termine la implementación de la primera iteración, sea una persona o un agente de IA, tiene que avisarle al equipo que esta lista existe.

---

## Mapa del repositorio

```
SimuladorMaaS/
├── README.md              ← este archivo: qué es el proyecto y dónde está cada cosa
├── docs/                  ← toda la documentación
│   ├── modelo.md          ← documento del modelo (qué y por qué)
│   ├── sdd.md             ← especificación técnica (cómo)
│   ├── fdps-decisiones.pdf← diagnóstico del dataset y decisiones sobre FDPs
│   ├── fdps-mock.md       ← nota: las FDP provisorias ahora están en el modelo y el SDD
│   ├── enunciado/         ← consigna del TP5 y formato del documento de la entrega
│   └── img/               ← diagramas e imágenes usados en los documentos
├── notebooks/             ← análisis exploratorio y ajuste de FDPs (TP4)
├── data/                  ← datos (ver data/README.md)
│   ├── raw/               ← dataset original de Kaggle (NO se sube, es muy pesado)
│   └── processed/         ← versión limpia y reducida (se sube si es chica)
├── src/                   ← código del simulador
├── tests/                 ← pruebas automáticas del simulador
├── results/               ← salidas de las corridas
│   ├── finales/           ← corridas que respaldan la entrega (se suben)
│   └── pruebas/           ← corridas intermedias (NO se suben)
├── requirements.txt       ← dependencias de Python
└── .gitignore             ← qué no se sube al repositorio
```

Cada carpeta tiene su propio `README.md` con más detalle.

---

## Cómo se corre

_Pendiente: se completa cuando exista el código en `src/`._

```bash
pip install -r requirements.txt
```

---

## Convenciones del repositorio

- **Enlaces en Markdown estándar** (`[texto](ruta/al/archivo.md)`), no `[[wikilinks]]` de Obsidian: GitHub no los entiende.
- **Una decisión, un solo lugar.** Las decisiones de diseño se registran en `docs/modelo.md` (sección "Registro de decisiones", D-01, D-02…). El SDD y el código las referencian por su número, no las repiten. El proceso completo es el de la skill `sdd-gobernanza`.
- **Unidades:** tiempo en minutos, distancia en millas, dinero en USD.
- **Semillas fijas:** toda corrida debe ser reproducible.
