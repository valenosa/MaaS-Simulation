# Simulador MaaS: cantidad óptima de choferes (Lyft, Boston)

Trabajo Práctico Nº 5 de **Simulación** (UTN FRBA, Ingeniería en Sistemas de Información).

Simulación de eventos discretos (evento a evento) de una plataforma de movilidad tipo Lyft, para encontrar la **cantidad de choferes (NCH)** que mantiene una espera aceptable para los clientes sin disparar el tiempo ocioso de la flota.

> **Estado:** etapa de diseño. El modelo y la especificación técnica se están cerrando antes de escribir código (Spec-Driven Development).

---

## Por dónde empezar

| Si querés… | Leé |
|---|---|
| Entender **qué** se modela y **por qué** se tomó cada decisión | [`docs/modelo.md`](docs/modelo.md) |
| Saber **cómo** se implementa el simulador (contrato técnico) | [`docs/sdd.md`](docs/sdd.md) |
| Ver por qué la demanda es un supuesto y cómo se ajustan las FDPs | [`docs/fdps-decisiones.pdf`](docs/fdps-decisiones.pdf) |
| Leer la consigna del TP | [`docs/enunciado/`](docs/enunciado/) |

---

## Mapa del repositorio

```
SimuladorMaaS/
├── README.md              ← este archivo: qué es el proyecto y dónde está cada cosa
├── docs/                  ← toda la documentación
│   ├── modelo.md          ← documento del modelo (qué y por qué)
│   ├── sdd.md             ← especificación técnica (cómo)
│   ├── fdps-decisiones.pdf← diagnóstico del dataset y decisiones sobre FDPs
│   ├── fdps-mock.md       ← FDPs provisorias para el MVP (a actualizar)
│   ├── enunciado/         ← consigna oficial del TP5
│   └── img/               ← diagramas e imágenes usados en los documentos
├── notebooks/             ← análisis exploratorio y ajuste de FDPs (TP4)
├── data/                  ← datos (ver data/README.md)
│   ├── raw/               ← dataset original de Kaggle (NO se sube, es muy pesado)
│   └── processed/         ← versión limpia y reducida (se sube si es chica)
├── src/                   ← código del simulador
├── tests/                 ← pruebas automáticas del simulador
├── results/               ← salidas de las corridas
│   ├── finales/           ← corridas que respaldan el informe (se suben)
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
- **Una decisión, un solo lugar.** Las decisiones de diseño se registran en `docs/modelo.md` (sección "Registro de decisiones", D-01, D-02…). El SDD y el código las referencian por su número, no las repiten.
- **Unidades:** tiempo en minutos, distancia en millas, dinero en USD.
- **Semillas fijas:** toda corrida debe ser reproducible.
