# Simulador MaaS: cantidad óptima de choferes (Lyft, Boston)

Trabajo Práctico Nº 5 de **Simulación** (UTN FRBA, Ingeniería en Sistemas de Información).

Simulación de eventos discretos (evento a evento) de una plataforma de movilidad tipo Lyft, para encontrar la **cantidad de choferes (NCH)** que mantiene una espera aceptable para los clientes sin disparar el tiempo ocioso de la flota.

> **Estado:** primera iteración implementada con las FDP provisorias (V1). El simulador, sus pruebas y el análisis funcionan: ver "Cómo se corre", más abajo. Falta correr el experimento de la entrega con las FDP definitivas, cuando llegue `config/fdp_v2.toml` (etapa 5 del SDD). El proyecto sigue Spec-Driven Development: el modelo manda, el SDD se deriva de él y el código implementa el SDD. La entrega se hace en dos iteraciones: ver "Segunda iteración", más abajo.

---

## Por dónde empezar

| Si querés… | Leé |
|---|---|
| Entender **qué** se modela y **por qué** se tomó cada decisión | [`docs/modelo.md`](docs/modelo.md) |
| Saber **cómo** se implementa el simulador (contrato técnico) | [`docs/sdd.md`](docs/sdd.md) |
| Ver de dónde sale cada FDP | [`notebooks/fdps.ipynb`](notebooks/fdps.ipynb); reglas en [`docs/modelo.md`](docs/modelo.md), secciones 4.3 y 4.5 |
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
| ~~Notebook reproducible~~ | **Hecho:** [`notebooks/fdps.ipynb`](notebooks/fdps.ipynb) | Modelo, sección 4.5.4 |
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
├── notebooks/             ← de dónde sale cada FDP (fdps.ipynb)
├── data/                  ← datos (ver data/README.md)
│   ├── raw/               ← dataset original de Kaggle (NO se sube, es muy pesado)
│   └── processed/         ← versión limpia y reducida (se sube si es chica)
├── config/                ← parámetros del experimento y catálogos de FDP (V1; la V2 cuando llegue)
├── src/                   ← código del simulador: el paquete simulador_maas
├── tests/                 ← pruebas automáticas del simulador
├── results/               ← salidas de las corridas
│   ├── finales/           ← corridas que respaldan la entrega (se suben)
│   └── pruebas/           ← corridas intermedias (NO se suben)
├── pyproject.toml         ← declara el paquete simulador_maas y sus dependencias
├── requirements.txt       ← instala el paquete, pytest y lo que usa el notebook
└── .gitignore             ← qué no se sube al repositorio
```

Cada carpeta tiene su propio `README.md` con más detalle. La estructura completa del código, con `config/` y `pyproject.toml`, está en [`docs/sdd.md`](docs/sdd.md), sección 2.2.

---

## Cómo se corre

Todos los comandos se corren desde la raíz del repositorio. El detalle de cada opción está en [`docs/sdd.md`](docs/sdd.md), sección 8.6.

### Instalación (una sola vez)

Hace falta Python 3.11 o posterior. Conviene un entorno virtual (`.venv/` ya está en `.gitignore`):

```bash
python -m venv .venv
```

Activarlo (`.venv\Scripts\activate` en Windows, `source .venv/bin/activate` en Linux o macOS) e instalar:

```bash
pip install -r requirements.txt
```

Eso instala el paquete `simulador_maas` en modo editable (los cambios en `src/` se ven sin reinstalar), pytest y lo que usa el notebook. Para el simulador solo, alcanza con `pip install -e .` y `pip install pytest`.

### Pruebas

```bash
pytest
```

### 1. Experimento: todas las corridas

Recorre los niveles de demanda, las flotas y las réplicas de `config/experimento.toml`, y escribe `experimento.json` y `corridas.csv`. Con las FDP provisorias tarda menos de un minuto.

```bash
python -m simulador_maas experimento
```

Por defecto escribe en `results/pruebas/AAAAMMDD-HHMMSS/`, que no se sube. Para los resultados de la entrega, elegí una carpeta en `results/finales/`. Nunca se pisa una carpeta que ya existe:

```bash
python -m simulador_maas experimento --salida results/finales/v2
```

### 2. Análisis: el criterio, los escenarios y los gráficos

Lee un experimento ya corrido y escribe las tablas, los avisos y los gráficos en una subcarpeta `analisis_X<x>_Y<y>/`. También muestra por pantalla los escenarios y la mejor flota de cada nivel.

```bash
python -m simulador_maas analisis --entrada results/pruebas/AAAAMMDD-HHMMSS
```

Para probar otro criterio no hace falta volver a simular: los umbrales X (espera, en minutos) e Y (abandono, en %) se cambian desde la línea de comandos.

```bash
python -m simulador_maas analisis --entrada results/pruebas/AAAAMMDD-HHMMSS --espera-max 12 --abandono-max 3
```

### 3. Corrida individual: para depurar o para la tabla de eventos

Simula una sola corrida (flota, nivel y réplica) y muestra su resultado. Con `--eventos`, escribe además la tabla de eventos en un CSV.

```bash
python -m simulador_maas corrida --nch 9 --nivel alto --replica 3
```

La tabla de eventos calculada a mano del SDD (sección 12.3), que sirve para el documento de la entrega, se obtiene con:

```bash
python -m simulador_maas corrida --nch 2 --config tests/datos/pr01_config.toml --eventos results/pruebas/eventos_pr01.csv
```

### Pasar a las FDP definitivas (V2)

Cuando esté `config/fdp_v2.toml` (SDD, sección 5.6), se cambia una línea de `config/experimento.toml`, `catalogo_fdp = "fdp_v2.toml"`, y se corre el experimento en `results/finales/`. No hay que tocar el código: el tiempo medio de servicio, las flotas de referencia y el rango de flotas se recalculan solos.

---

## Convenciones del repositorio

- **Enlaces en Markdown estándar** (`[texto](ruta/al/archivo.md)`), no `[[wikilinks]]` de Obsidian: GitHub no los entiende.
- **Una decisión, un solo lugar.** Las decisiones de diseño se registran en `docs/modelo.md` (sección "Registro de decisiones", D-01, D-02…). El SDD y el código las referencian por su número, no las repiten. El proceso completo es el de la skill `sdd-gobernanza`.
- **Unidades:** tiempo en minutos, distancia en millas, dinero en USD.
- **Semillas fijas:** toda corrida debe ser reproducible.
