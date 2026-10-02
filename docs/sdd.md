# Especificación técnica del simulador (SDD)

**Simulador MaaS · cantidad óptima de choferes · Lyft, zona de Boston**

- **Versión:** 1.5
- **Basado en:** modelo v2.4 ([`modelo.md`](modelo.md))
- **Fecha:** 2 de octubre de 2026
- **Estado:** aprobado para implementar la primera iteración.
- **Autores:** _completar integrantes del grupo_

---

## Cómo leer este documento

> **El símbolo "§" significa "sección".** "§6.6" es la sección 6.6 de este documento; "modelo §8.3" es la sección 8.3 del documento del modelo.

| Para… | Ver |
|---|---|
| Implementar el simulador | Todo, en orden, empezando por §0.2; el orden de trabajo está en §13 |
| Correr el simulador | §8.6 |
| Ver la tabla de eventos de prueba (sirve para el documento de la entrega) | §12.3 |
| Saber qué no se implementa en la primera iteración | §1.4 y §5.10 |
| Completar las FDP definitivas | §5.6 (qué entregar y en qué formato) y la sección 4.5 del modelo (cómo obtenerlo) |
| Comprobar que cada decisión del modelo esté implementada | Matriz de trazabilidad (§15) |
| Entender una decisión técnica | §14 |

**Contenido**

0. Cómo usar este documento
1. Alcance de la implementación
2. Stack y estructura del código
3. Configuración
4. Estructuras de datos
5. Generación de valores aleatorios
6. Motor de simulación
7. Invariantes
8. Orquestación del experimento
9. Salidas
10. Análisis
11. Errores y casos borde
12. Plan de pruebas
13. Plan de implementación por etapas
14. Decisiones técnicas
15. Matriz de trazabilidad
16. Cambios

---

## 0. Cómo usar este documento

### 0.1 Qué es y qué no es

- **Es el contrato para implementar el simulador y su análisis sin ambigüedades.** Lo lee quien programa, sea una persona o un agente de IA.
- **Se deriva del documento del modelo**, en la versión que indica el encabezado. No repite sus justificaciones: las cita por identificador (D-xx, S-xx, P-xx) o por sección ("modelo §8.3").
- **Describe las rutinas en pseudocódigo, no en Python.** Las reglas del proyecto prohíben escribir código hasta que este documento esté aprobado.
- **No contiene los valores de los parámetros.** Los fija el modelo y el código los lee de la configuración (§3).
- **No cubre el trabajo de datos del notebook**, es decir, cómo se obtienen las FDP definitivas. Eso está en la sección 4.5 del modelo. Este documento solo define en qué formato el simulador recibe ese trabajo (§5.6).

### 0.2 Guía para quien implementa

1. **Implementar solo lo especificado.** Lo que no está escrito no se agrega, aunque parezca útil.
2. **Ante una ambigüedad o una contradicción, frenar y preguntar.** No decidir en silencio. Si hace falta una decisión técnica menor, proponerla como T-xx (§14).
3. **No modificar el modelo ni este documento desde la implementación.** Los cambios siguen el orden modelo → SDD → código.
4. **Avanzar por las etapas de §13.** Una etapa termina cuando pasan sus pruebas.
5. **Indicar en el encabezado de cada módulo qué secciones implementa**, por ejemplo: "Implementa SDD §6.6 a §6.8".
6. **Usar los nombres de §4.8**, que son los del modelo traducidos al código.
7. **No escribir números a mano en el código.** Todo valor sale de la configuración (§3), de un cálculo especificado acá o de una constante técnica definida en §14.
8. **No implementar lo marcado como "segunda iteración"** (§1.4 y §5.10), aunque esté especificado. Se implementa recién cuando el equipo decide empezar la segunda iteración (D-16).
9. **Al terminar la primera iteración, avisarle al equipo que queda la segunda.** Al terminar la etapa 6 de §13, recordar que existe la lista de mejoras de la segunda iteración (modelo, sección 12.3) y mostrarla. Si quien implementa es un agente de IA, lo dice explícitamente en su mensaje final, aunque nadie se lo pregunte. La primera de la lista es que la tarifa dependa de la distancia (P-14).

### 0.3 Identificadores

- **Del modelo:** D-xx (decisiones), S-xx (supuestos), P-xx (pendientes) y "modelo §N" para sus secciones.
- **De este documento:** T-xx (decisiones técnicas, §14), INV-xx (invariantes, §7) y PR-xx (pruebas, §12). Un "§N" sin más aclaración se refiere a este documento.
- **El símbolo "§"** significa "sección".

### 0.4 Convenciones del pseudocódigo

| Elemento | Notación |
|---|---|
| Asignación | `x ← valor` |
| Comparaciones | `=`, `≠`, `<`, `≤`, `>`, `≥`, siempre explícitas |
| Condicional | `SI … ENTONCES … SI NO … FIN SI` |
| Elección según un valor | `SEGÚN x: caso A … caso B …` |
| Repetición | `PARA CADA … HACER … FIN PARA`, `MIENTRAS … HACER … FIN MIENTRAS`, `REPETIR … HASTA QUE …` |
| Comentario | `// …` |
| Valor ausente | `vacío` |
| Sin evento pendiente | `HV` (§4.1) |

- Los tiempos están en minutos, las distancias en millas y los montos en USD, todos como números reales de doble precisión.
- Los choferes se numeran de 1 a NCH, como en el modelo. Si el código usa índices desde 0, la conversión es interna y no cambia el desempate por menor número.

### 0.5 Estado de este documento

El documento está completo para la primera iteración y aprobado para implementarla. Distingue la primera iteración (la entrega) de la segunda (mejoras posteriores), según D-16: lo de la segunda está resumido en §1.4 y especificado en §5.10 y §12.6.

**Para una revisión rápida, conviene mirar especialmente:**

- §6.6 a §6.8: que cada rutina haga exactamente lo que dice el modelo §8.
- §12.3: la corrida calculada a mano. Es la prueba más fuerte, y sirve como tabla de eventos para el documento de la entrega.
- §10.3: el criterio de decisión y sus avisos.
- §13: el orden de implementación.
- §14: las decisiones técnicas.

---

## 1. Alcance de la implementación

### 1.1 Qué se construye

| Componente | Qué hace | Sección |
|---|---|---|
| Configuración | Carga y valida los parámetros | §3 |
| Generación de valores aleatorios | Sortea los atributos de cada pedido con números aleatorios comunes | §5 |
| Motor | Simula una corrida: un día, una flota, una réplica, un nivel de demanda | §6 y §7 |
| Orquestador | Recorre niveles de demanda, flotas y réplicas, y escribe las salidas | §8 y §9 |
| Análisis | Agrega las corridas, aplica el criterio y genera tablas y gráficos | §10 |
| Pruebas | Verifican cada componente | §12 |

**Fuera de alcance:** el notebook de FDPs (modelo §4.5), el documento de la entrega, la presentación y el diagrama de flujo (P-11).

### 1.2 Versiones de las FDP

| Versión | Distribuciones | Para qué | Bloqueada por |
|---|---|---|---|
| V1 | Las provisorias del modelo §4.2, en el catálogo `config/fdp_v1.toml` (§5.7). La búsqueda y la demora ya son las definitivas | Construir, probar y verificar todo el simulador | Nada |
| V2 | Las definitivas, en el catálogo `config/fdp_v2.toml` (§5.6). Respecto de la V1, solo cambian la distancia y la tarifa | Obtener los resultados de la entrega | Nada: P-03 y P-04 resueltos en el modelo v2.4 |

Pasar de la V1 a la V2 es cambiar el archivo de catálogo en la configuración. No requiere cambios de código ni de este documento, siempre que las FDP definitivas usen los tipos soportados (§5.3).

### 1.3 Pendientes del modelo y su efecto en la implementación

| Pendiente | Efecto en la implementación |
|---|---|
| P-01, P-02, P-09 | Ninguno: son consultas o avisos a la cátedra |
| P-03, P-04 | Resueltos en el modelo v2.4: solo cambió el contenido del catálogo de la V2, sin cambios de código |
| P-05, P-06 | Resueltos: ya están en el catálogo de la V1 (§5.7) |
| P-07 | Segunda iteración. Si cambia la velocidad, se cambia solo en la configuración |
| P-10 | Segunda iteración. Se resuelve con corridas adicionales, cambiando el umbral U en la configuración |
| P-11 | Ninguno: es un entregable del documento de la entrega |
| P-12 | Este documento |
| P-13 | Ninguno: es trabajo del notebook |
| P-14 | Segunda iteración. Requiere programar el modo "regresión" de la tarifa (§5.10.1) |

### 1.4 Primera y segunda iteración (D-16)

La primera iteración implementa el modelo completo: ninguna decisión de diseño queda afuera. Lo que se posterga son mejoras que no cambian la decisión sobre la flota. Lo de la segunda iteración **no se implementa en la primera** (§0.2, regla 8).

| Tema | Primera iteración | Segunda iteración | Dónde se especifica |
|---|---|---|---|
| Tarifa | Modo "independiente": se sortea de su propia FDP (D-14) | Modo "regresión": según la distancia (D-14, D-15, P-14) | §5.5 y §5.10.1 |
| Tipos de FDP | `scipy`, más `constante` y `secuencia` para las pruebas | `empirica` | §5.3 y §5.10.2 |
| Validación del catálogo de FDP | Versión, modo de la tarifa, estructura (incluida la sección `[IA]`, que solo admite un catálogo de PRUEBA), familias y parámetros de scipy, y error si aparece un valor negativo | Soporte, muestra de control, huella del archivo y los demás tipos permitidos por versión | §5.9 y §5.10.3 |
| Validación de la configuración | Claves obligatorias, tipos y rangos | Rechazo de claves desconocidas | §3.3 |
| Pruebas | Corrida calculada a mano, invariantes, control de números comunes y casos borde principales | Contraste con Erlang C y casos borde exhaustivos | §12 |

Cuando el equipo decida empezar la segunda iteración, primero se actualiza este documento: lo que se vaya a implementar sale de §5.10 y pasa a la sección que corresponda. Recién después se programa.

---

## 2. Stack y estructura del código

### 2.1 Lenguaje y bibliotecas

| Elemento | Versión mínima | Uso |
|---|---|---|
| Python | 3.11 | Lenguaje (T-01) |
| numpy | 1.26 | Generadores aleatorios y semillas (§5.2) |
| scipy | 1.11 | Distribuciones de las FDP por nombre (§5.3) |
| pandas | 2.0 | Salidas y análisis (§9, §10) |
| matplotlib | 3.7 | Gráficos (§10) |
| pytest | 7.0 | Pruebas (§12) |

No se usan bibliotecas de simulación de eventos discretos (T-02).

El paquete se instala una sola vez, en modo editable, con `pip install -e .` desde la raíz del repositorio. `pyproject.toml` declara el paquete (versión 1.0.0 en la primera iteración), la versión mínima de Python y estas bibliotecas con sus versiones mínimas, salvo pytest, que va en `requirements.txt` (T-23).

### 2.2 Estructura de archivos

```
pyproject.toml            ← declara el paquete y sus dependencias (T-23)
requirements.txt          ← instala el paquete en modo editable, más pytest y lo que usa el notebook (T-23)
config/
├── experimento.toml      ← parámetros del modelo y del experimento (§3)
├── fdp_v1.toml           ← catálogo de FDP provisorias (§5.7)
└── fdp_v2.toml           ← catálogo de FDP definitivas (§5.6); lo entrega el trabajo del notebook
src/simulador_maas/
├── __init__.py
├── __main__.py           ← punto de entrada (§8)
├── config.py             ← carga y validación de la configuración (§3)
├── aleatorios.py         ← FDP, generadores y semillas (§5)
├── referencias.py        ← valores derivados (§3.4)
├── entidades.py          ← estructuras de datos (§4)
├── motor.py              ← una corrida (§6) y sus invariantes (§7)
├── experimento.py        ← orquestación y salidas (§8, §9)
└── analisis.py           ← agregación, criterio y gráficos (§10)
tests/                    ← pruebas (§12)
```

### 2.3 Dependencias entre módulos

| Módulo | Puede usar | No puede usar |
|---|---|---|
| `config` | Ninguno de los otros | — |
| `entidades` | Ninguno de los otros | — |
| `aleatorios` | `config` | `motor`, `experimento`, `analisis` |
| `referencias` | `config`, `aleatorios` | `motor`, `experimento`, `analisis` |
| `motor` | `config`, `entidades`, `aleatorios` | `experimento`, `analisis` |
| `experimento` | Todos salvo `analisis` | `analisis` |
| `analisis` | `config` | `motor`, `aleatorios`, `referencias`, `experimento` |

El análisis solo lee los archivos de salida y nunca llama al motor: así se pueden cambiar los umbrales del criterio sin volver a simular (D-10).

---

## 3. Configuración

### 3.1 Archivos

- **`config/experimento.toml`:** parámetros del modelo y del experimento. Lo mantiene el equipo de simulación.
- **Un catálogo de FDP por versión** (`config/fdp_v1.toml`, `config/fdp_v2.toml`): lo mantiene quien trabaja en las FDP (T-03). Su formato está en §5.6.

Los valores de cada parámetro se copian del modelo, que es la fuente. Si el modelo cambia un valor, se cambia también en el archivo, en el mismo commit.

Una ruta relativa escrita dentro de `experimento.toml` (por ahora, solo `catalogo_fdp`) se resuelve desde la carpeta de ese mismo archivo, no desde la carpeta en la que se corre el comando. Así una configuración y su catálogo funcionan juntos desde cualquier lugar; por ejemplo, los de las pruebas, en `tests/datos/` (§12.1).

### 3.2 Parámetros de `experimento.toml`

Estructura (los `…` se completan con los valores del modelo):

```toml
[modelo]
velocidad_mph = …            # v
umbral_tolerancia_min = …    # U; se admite inf (sin arrepentimiento, solo para pruebas)
horizonte_min = …            # TF

[demanda]
media_ia_base_min = …        # media del intervalo entre pedidos con la demanda base
niveles = { bajo = …, base = 1.0, alto = … }   # factores que multiplican a λ

[experimento]
replicas = …                 # R
semilla_base = …
catalogo_fdp = "fdp_v1.toml"  # relativa a la carpeta de este archivo (§3.1)
rango_margen_inferior = …
rango_margen_superior = …
rango_manual = []            # opcional: [desde, hasta] reemplaza la regla del rango
verificar_invariantes = true

[analisis]
espera_total_max_min = …     # X
abandono_max_pct = …         # Y
nivel_confianza = …
```

| Clave | Tipo | Unidad | Origen del valor | Validación de rango (§3.3) |
|---|---|---|---|---|
| `modelo.velocidad_mph` | real | mi/h | S-06, modelo §4.2 | > 0 y finito |
| `modelo.umbral_tolerancia_min` | real | min | D-02 | > 0; se admite infinito (es el único real que lo admite) |
| `modelo.horizonte_min` | real | min | D-05 | > 0 y finito |
| `demanda.media_ia_base_min` | real | min | D-01 | > 0 y finito |
| `demanda.niveles` | tabla de nombre a real | — | modelo §9.3 | Al menos un nivel; todos > 0 y finitos; existe `base` y vale 1 |
| `experimento.replicas` | entero | — | D-05 | ≥ 2: el intervalo de confianza necesita al menos dos |
| `experimento.semilla_base` | entero | — | modelo §9.2, D-09 | ≥ 0 |
| `experimento.catalogo_fdp` | texto | — | §5 | — (el archivo se controla en la primera iteración: §3.3) |
| `experimento.rango_margen_inferior` | entero | choferes | modelo §9.5 | ≥ 0 |
| `experimento.rango_margen_superior` | entero | choferes | modelo §9.5 | ≥ 0 |
| `experimento.rango_manual` | lista de 0 o 2 enteros | choferes | modelo §10.5 | Si tiene dos: 1 ≤ desde ≤ hasta |
| `experimento.verificar_invariantes` | booleano | — | T-13 | — |
| `analisis.espera_total_max_min` | real | min | D-03 | > 0 y finito |
| `analisis.abandono_max_pct` | real | % | D-03 | Entre 0 y 100 |
| `analisis.nivel_confianza` | real | — | modelo §6.3 | Mayor que 0 y menor que 1 |

**Infinito.** TOML admite `inf`, que cumple "> 0". Solo U lo admite, para correr sin arrepentimiento en las pruebas; en cualquier otro real, `inf` es un error. Sin este control, un `horizonte_min = inf` dejaría el motor en un ciclo sin fin, porque TLL nunca pasa a HV, y un factor de nivel infinito haría que todos los pedidos llegaran en el mismo instante. `nan` no hace falta controlarlo aparte: no cumple ninguna validación de rango, porque toda comparación con `nan` da falso.

### 3.3 Reglas de validación

**Primera iteración:**

- Una clave obligatoria ausente es un error. Todas son obligatorias salvo `rango_manual`.
- Cada valor tiene el tipo de la tabla de §3.2; si no, es un error. Un campo real acepta un entero de TOML y lo convierte a real: `velocidad_mph = 13` es válido. Un campo entero no acepta reales. Un booleano nunca vale como número, aunque en Python `bool` sea un subtipo de `int`: `replicas = true` es un error.
- Cada valor cumple la columna "Validación de rango" de §3.2. Son controles de una línea, y sin ellos un error de tipeo terminaría en una división por cero o en resultados sin sentido: por ejemplo, `horizonte_min = 0` o un `rango_manual` que empieza en 0 choferes. Entre ellos está que exista el nivel `base` con factor 1, sin el cual la flota actual se calcularía mal sin ningún aviso (D-07).
- `rango_manual` es una lista vacía o de exactamente dos enteros; una lista de uno o de tres es un error.
- El archivo de `catalogo_fdp` existe, con la ruta resuelta según §3.1. Su contenido no lo valida `config`, que no puede usar `aleatorios` (§2.3): lo valida `aleatorios` al cargarlo (§5.9), y `preparar` (§8.2) llama a las dos validaciones antes de simular.
- Cada mensaje de error indica la clave, el valor leído y la regla que no se cumple.
- La validación termina antes de simular: una configuración inválida no produce ninguna corrida.

Con estos controles se cumplen las precondiciones del motor (§6.1). Las opciones de la línea de comandos se validan aparte (§8.6).

**Segunda iteración (§1.4):**

- Una clave desconocida es un error, para que un error de tipeo no pase en silencio.

### 3.4 Valores derivados

Se calculan al arrancar, a partir de la configuración y del catálogo, y nunca se escriben en un archivo de entrada (modelo §4.4, D-07). Se registran en las salidas (§9) para que cada corrida sea trazable.

| Valor | Cálculo | Origen |
|---|---|---|
| E[TB], E[D], E[DEM] | Medias exactas de las FDP del catálogo (§5.8) | modelo §4.4 |
| E[TV] | 60 × E[D] / v + E[DEM] | modelo §4.4 |
| E[S] | E[TB] + E[TV] | modelo §4.4 |
| λ de cada nivel | factor del nivel / `media_ia_base_min` | modelo §9.3 |
| Media del intervalo de cada nivel | `media_ia_base_min` / factor del nivel | D-09 |
| Carga a de cada nivel | λ del nivel × E[S] | modelo §9.3 |
| Flota actual | ⌈a del nivel base⌉, con la tolerancia de T-12 | D-07 |
| Flota peor | Flota actual − 1; no existe si da menos de 1 | D-07 |
| Rango de NCH | Desde max(1, ⌈menor carga entre niveles⌉ − margen inferior) hasta ⌈mayor carga entre niveles⌉ + margen superior, con la tolerancia de T-12, salvo que `rango_manual` lo reemplace | modelo §9.5 |

- Todos se calculan en doble precisión y no se redondean antes de usarse.
- Si E[S] no es un número finito o es ≤ 0, es un error: no hay carga ni flotas de referencia que calcular. El control de "finito" importa porque scipy acepta algunos parámetros inválidos y devuelve NaN como media, y NaN ≤ 0 es falso.

---

## 4. Estructuras de datos

### 4.1 Tipos y constantes

- **Tiempos, distancias y montos:** reales de doble precisión.
- **Contadores:** enteros.
- **HV:** infinito positivo de punto flotante (T-04). Cualquier instante real es menor que HV.
- **vacío:** ausencia de valor (en Python, `None`).

### 4.2 Cliente (entidad temporal)

Nace en TLL y sale del sistema al arrepentirse o al terminar su viaje (modelo §5.5).

| Campo | Tipo | Unidad | Se define en | Descripción |
|---|---|---|---|---|
| `id` | entero | — | TLL | Número de pedido en la corrida: 1, 2, 3… en orden de llegada; es el valor de NT en ese momento |
| `t_llegada` | real | min | TLL | Instante del pedido |
| `tb` | real | min | TLL | Tiempo de búsqueda (§5.4) |
| `d` | real | mi | TLL | Distancia |
| `dem` | real | min | TLL | Demora por tráfico |
| `tv` | real | min | TLL | Tiempo de viaje: d × 60 / v + dem |
| `tar` | real | USD | TLL | Tarifa (§5.5) |
| `t_asignacion` | real o vacío | min | TLL o TPS | Instante en que se le asigna un chofer |
| `t_recogida` | real o vacío | min | TLC | Instante en que el chofer lo recoge |

Todos los atributos aleatorios se sortean al crear el cliente, aunque después se arrepienta (D-09).

### 4.3 Chofer

No hay una estructura "chofer" aparte. Cada chofer i, con 1 ≤ i ≤ NCH, queda descripto por tres posiciones de vector del estado global:

| Vector | Contenido |
|---|---|
| TLC(i) | Instante en que llega a buscar a su cliente, o HV |
| TPS(i) | Instante en que termina el viaje, o HV |
| CA(i) | Cliente asignado, o vacío |

Su estado se deduce de la TEF (modelo §7.2, T-05):

| TLC(i) | TPS(i) | Estado |
|---|---|---|
| HV | HV | Disponible |
| Distinto de HV | HV | En camino |
| HV | Distinto de HV | Ocupado |
| Distinto de HV | Distinto de HV | Imposible (INV-03) |

### 4.4 Cola

Secuencia de clientes por orden de llegada: se agrega al final y se quita del principio (en Python, `collections.deque`). Ns es la longitud de la cola y no se guarda aparte (T-07).

### 4.5 Estado global de una corrida

| Variable del modelo | Nombre en el código | Tipo | Valor inicial | Descripción |
|---|---|---|---|---|
| T | `t` | real | 0 | Reloj de la simulación |
| — | `t_anterior` | real | 0 | Instante del evento anterior, para acumular áreas (§6.5) |
| TLL | `tll` | real | Ver §6.2 | Instante de la próxima llegada |
| TLC(i) | `tlc[i]` | vector de NCH reales | HV | Llegada del chofer i a su cliente |
| TPS(i) | `tps[i]` | vector de NCH reales | HV | Fin del viaje del chofer i |
| CA(i) | `ca[i]` | vector de NCH clientes o vacío | vacío | Cliente asignado al chofer i |
| Ncd | `ncd` | entero | NCH | Choferes disponibles |
| Ncc | `ncc` | entero | 0 | Choferes en camino |
| Nco | `nco` | entero | 0 | Choferes ocupados |
| Ns | longitud de `cola` | entero | 0 | Clientes esperando |
| NT | `nt` | entero | 0 | Pedidos recibidos |
| NARR | `narr` | entero | 0 | Clientes arrepentidos |
| NAT | `nat` | entero | 0 | Clientes atendidos |
| SEC | `suma_espera_cola` | real | 0 | Suma de esperas en cola (min) |
| SET | `suma_espera_total` | real | 0 | Suma de esperas totales (min) |
| REC | `rec` | real | 0 | Recaudación (USD) |
| RECP | `recp` | real | 0 | Recaudación perdida (USD) |
| STO | `sto` | real | 0 | Chofer-minutos disponibles en [0, TF] |
| STC | `stc` | real | 0 | Chofer-minutos en camino en [0, TF] |
| STV | `stv` | real | 0 | Chofer-minutos ocupados en [0, TF] |
| — | `n_eventos` | entero | 0 | Diagnóstico: eventos procesados |
| — | `ns_max` | entero | 0 | Diagnóstico: cola más larga |

### 4.6 Parámetros de una corrida

No cambian durante la corrida:

| Parámetro | Origen |
|---|---|
| NCH | Orquestador (§8) |
| Nombre del nivel de demanda, solo para identificar el resultado (§4.7) | Orquestador (§8) |
| U y TF | Configuración (§3.2) |
| E[S] y E[TB], para el TEE (§6.6) | §3.4 |
| Fuentes de valores aleatorios de la réplica | §5.1 y §5.2 |
| `verificar_invariantes` | Configuración (§3.2) |
| `registrar_eventos` | Quien llama al motor: lo activan el subcomando `corrida` (§8.4, T-18) y las pruebas que comparan el registro (§12) |

La media del intervalo entre pedidos y la velocidad v no son parámetros del motor: las usan las fuentes, para escalar la IA (§5.2) y calcular tv (§5.4). El motor recibe los valores ya sorteados.

Las pruebas pueden llamar al motor directamente, sin pasar por el orquestador.

### 4.7 Resultado de una corrida

Al terminar, el motor devuelve un registro con:

- **Identificación:** nivel de demanda y NCH. La réplica la agrega el orquestador (§8.3), porque el motor solo recibe sus fuentes.
- **Contadores y acumuladores finales:** NT, NARR, NAT, SEC, SET, REC, RECP, STO, STC y STV.
- **Métricas** del modelo §6.1, calculadas según §6.10: PET, PEC, PA, PTO, PTC, PTV y RPC.
- **Diagnóstico:** instante del último evento, cantidad de eventos, cola más larga e indicador de día sin pedidos.

El formato de archivo de estos registros se define en §9.

### 4.8 Correspondencia de nombres

- Las variables del modelo se escriben en el código en minúsculas: `ncd`, `ncc`, `nco`, `nt`, `narr`, `nat`, `rec`, `recp`, `sto`, `stc`, `stv`, `tll`, `tlc`, `tps`, `ca`.
- SEC y SET usan nombres largos (`suma_espera_cola` y `suma_espera_total`) porque `set` es el nombre de un tipo de Python, y usarlo como variable lo taparía.
- Las métricas también van en minúsculas: `pet`, `pec`, `pa`, `pto`, `ptc`, `ptv`, `rpc`.
- Las variables aleatorias se identifican como IA, TB, D, DEM y TAR, igual que en el catálogo (§5.6).

---

## 5. Generación de valores aleatorios

### 5.1 Qué produce

Para cada pedido, los valores de IA (el intervalo hasta el próximo pedido), TB, D, DEM y TAR, y a partir de ellos TV. Cumple D-09 (números aleatorios comunes) y D-14 (origen de cada FDP). En la segunda iteración, además, D-15 (§5.10.1).

El motor no conoce las distribuciones: usa un objeto "fuentes de la réplica" con dos operaciones.

| Operación | Devuelve | Sección |
|---|---|---|
| `sortear_ia()` | El próximo intervalo entre pedidos (min), ya escalado al nivel de demanda | §5.2 |
| `sortear_atributos()` | tb, d, dem, tv y tar de un pedido | §5.4, §5.5 |

Las fuentes se crean con:

```
crear_fuentes(catalogo, semilla_base, r, media_ia, v) → fuentes
```

donde `catalogo` es el catálogo ya validado (§5.9), r la réplica, `media_ia` la media del intervalo del nivel de demanda (§3.4) y v la velocidad (para tv, §5.4).

### 5.2 Generadores y semillas (D-09)

- Hay **cinco generadores independientes**, uno por variable aleatoria, cada una con un número fijo k: IA = 0, TB = 1, D = 2, DEM = 3 y TAR = 4.
- **La semilla del generador de la variable k en la réplica r** (con r = 0, 1, …, R − 1) es la secuencia de semillas de numpy con entropía `semilla_base` y clave de derivación (r, k): `SeedSequence(entropy=semilla_base, spawn_key=(r, k))`. Cada generador es un `numpy.random.Generator` sobre `PCG64` (T-08).
- **Las fuentes se crean de nuevo para cada corrida,** a partir de su réplica. Por eso, en la réplica r, todas las flotas y todos los niveles de demanda reciben exactamente la misma secuencia de cada variable.
- **Intervalo entre pedidos:** IA = (media del intervalo del nivel) × E, con E exponencial de media 1 sorteada con el método `standard_exponential()` del generador de IA. Así, en los tres niveles de demanda el pedido número k tiene los mismos atributos y solo cambia cuándo llega (D-09). El método está fijado porque otros, como −ln(1 − U), dan otra secuencia con la misma semilla.
- **Si el catálogo es de PRUEBA y trae una sección `[IA]`** (§5.6, regla 2), `sortear_ia()` devuelve esos valores tal cual, sin escalarlos por el nivel. Así las pruebas fijan los instantes exactos de llegada.
- **Cada generador lo usa una sola variable y se consume en orden de pedido.** El pedido número k recibe el k-ésimo valor de TB, de D, de DEM y de TAR.
- **Está prohibido usar la API global de números aleatorios** (`numpy.random.exponential`, `numpy.random.seed`, el módulo `random`): su secuencia depende de todo lo que se haya sorteado antes en el programa.
- Los generadores entregan valores de a uno, a partir de un búfer interno de tamaño fijo (T-09).

### 5.3 Tipos de FDP soportados

| Tipo | Parámetros | Cómo se sortea | Catálogos que lo usan |
|---|---|---|---|
| `scipy` | `familia`: nombre de la distribución en `scipy.stats`; `parametros`: tabla con los nombres de scipy (forma, `loc`, `scale`) | `scipy.stats.<familia>(**parametros).rvs(random_state=generador)` | V1, V2 y PRUEBA |
| `constante` | `valor` | Siempre el mismo valor | PRUEBA |
| `secuencia` | `valores`: lista | Los valores en orden; agotarlos es un error | PRUEBA |

- `constante` y `secuencia` existen solo para las pruebas (§12). Se entregan de a un valor, sin búfer (T-09): con un búfer, una secuencia corta se agotaría antes de usarse. Sus valores se convierten a real al cargar el catálogo.
- Una exponencial se expresa con tipo `scipy`, `familia = "expon"` y `scale` igual a la media.
- La distribución empírica es de la segunda iteración (§5.10.2).
- Las normales recortadas de las FDP provisorias anteriores ya no se usan: la búsqueda y la demora quedaron definidas en el modelo §4.2.

### 5.4 Atributos de un pedido

```
procedimiento sortear_atributos():
   tb  ← sortear(TB)
   d   ← sortear(D)
   dem ← sortear(DEM)
   tar ← sortear_tarifa(d)                      // §5.5
   SI tb < 0 O d < 0 O dem < 0 O tar < 0 ENTONCES
      error "valor negativo de FDP", con la variable, el valor y el catálogo     // T-10
   FIN SI
   tv ← d × 60 / v + dem                        // modelo §4.2, S-06
   DEVOLVER (tb, d, dem, tv, tar)
```

- El orden de los sorteos es fijo. No afecta a los números aleatorios comunes, porque cada variable tiene su generador, pero hace el código predecible.
- Las fuentes no conocen la flota ni la corrida, así que su mensaje de error no las incluye. Quien llama al motor captura el error y agrega el nivel, la flota y la réplica (§8.3).
- El valor 0 se admite: lo usan algunas pruebas, por ejemplo con búsqueda o distancia nulas. Con las familias continuas de la V1 y la V2, su probabilidad es nula.

### 5.5 Tarifa (D-14)

```
procedimiento sortear_tarifa(d):
   SEGÚN modo de la tarifa en el catálogo:
      caso "independiente":                     // primera iteración (S-14)
         DEVOLVER sortear(TAR)                  // no usa d
      caso "regresion":                         // segunda iteración (§5.10.1)
         error "modo de tarifa no implementado en la primera iteración"
```

- En la primera iteración la tarifa se sortea de su propia FDP y no depende de la distancia (D-14, S-14). El parámetro `d` existe para que el modo "regresión" de la segunda iteración se agregue sin cambiar la interfaz.
- Un catálogo con modo "regresion" se rechaza al cargarlo (§5.9), así que el segundo caso no debería alcanzarse nunca: está por seguridad.
- Si la FDP elegida admite valores negativos con probabilidad despreciable (modelo §4.3), el control de §5.4 detiene la corrida en el caso extremadamente improbable de que aparezca uno.

### 5.6 Contrato de entrega de las FDP

Esta sección define el **entregable de quien complete las FDP definitivas** (modelo §4.5). Todo catálogo, de cualquier versión, tiene este formato.

**Archivo de la V2:** `config/fdp_v2.toml`.

```toml
[catalogo]
version = "V2"                           # "V1", "V2" o "PRUEBA"; la única clave obligatoria de esta sección
fecha = "AAAA-MM-DD"                     # las demás claves de [catalogo] son informativas
responsable = "…"
origen = "notebooks/fdps.ipynb"          # de dónde salen los valores
semilla_notebook = …                     # semilla con la que se obtuvieron

[TB]                                     # tiempo de búsqueda: definido en el modelo §4.2
tipo = "scipy"
familia = "gamma"
parametros = { a = …, scale = … }

[D]                                      # distancia (P-03)
tipo = "scipy"
familia = "…"                            # "lognorm", "gamma" o "weibull_min"
parametros = { … }

[DEM]                                    # demora por tráfico: definida en el modelo §4.2
tipo = "scipy"
familia = "expon"
parametros = { scale = … }

[TAR]                                    # tarifa (P-04; D-14)
modo = "independiente"                   # primera iteración; "regresion" es de la segunda (§5.10.1)
tipo = "scipy"
familia = "…"                            # la elegida en el notebook
parametros = { … }

[TAR.diagnostico]                        # informativo: el simulador no lo usa, solo lo registra
n_filas = …                              # filas usadas en el ajuste
media_datos_usd = …                      # media de los precios filtrados
desvio_datos_usd = …                     # desvío de los precios filtrados
```

**Reglas del contrato:**

1. **Secciones obligatorias:** `[catalogo]`, `[TB]`, `[D]`, `[DEM]` y `[TAR]`. `[TAR.diagnostico]` es obligatoria en la V2, con sus tres claves, y opcional en las demás versiones. En `[catalogo]`, la única clave obligatoria es `version`; `fecha`, `responsable`, `origen` y `semilla_notebook` son informativas: se copian en las salidas (§9.1), pero no se exigen. En cada variable son obligatorias `tipo` y las claves de ese tipo (§5.3); en `[TAR]`, además, `modo`.
2. **El intervalo entre pedidos no va en el catálogo** de la V1 ni de la V2: lo define el modelo (D-01) y su media está en `experimento.toml`. Una sección `[IA]` en un catálogo V1 o V2 es un error. Solo un catálogo de PRUEBA puede incluirla, con tipo `constante` (con valor mayor que 0: con 0 el reloj no avanzaría nunca) o `secuencia` (con valores ≥ 0), para fijar las llegadas.
3. **Con tipo `scipy`,** `familia` es el nombre exacto en `scipy.stats`, y `parametros` usa los nombres exactos de scipy, incluidos los de forma: `a` para `gamma`, `s` para `lognorm`, `c` para `weibull_min`, `a` y `b` para `johnsonsb`. Si falta `loc`, vale 0; si falta `scale`, vale 1.
4. **Atención con las convenciones:** la lognormal de numpy (`lognormal(mean=μ, sigma=σ)`) equivale en scipy a `lognorm` con `s` = σ y `scale` = e^μ.
5. **Modo de la tarifa:** en la primera iteración solo se acepta `modo = "independiente"`, con la FDP de la tarifa en la misma sección `[TAR]` (T-17). El formato del modo "regresion" está en §5.10.1.
6. **Unidades:** las del modelo (minutos, millas y USD). Las claves de diagnóstico llevan la unidad en el nombre.
7. **Los valores se copian tal como salen del notebook, sin redondear.**
8. **Un catálogo nuevo no pisa al anterior:** se agrega como archivo nuevo y se cambia `catalogo_fdp` en `experimento.toml`. Así cualquier corrida vieja se puede repetir.

### 5.7 Catálogo de la V1

`config/fdp_v1.toml` traduce la columna "FDP provisoria (mock)" del modelo §4.2 a este formato. Su sección `[catalogo]` lleva `version = "V1"`, `origen = "docs/modelo.md, sección 4.2"` y la fecha en que se crea el archivo; no lleva `semilla_notebook` ni `[TAR.diagnostico]`, porque sus valores no salen del notebook. Los valores se copian del modelo; esta tabla solo indica cómo se expresa cada una:

| Variable | Provisoria del modelo | Cómo va en el catálogo |
|---|---|---|
| TB | Gamma con media 5 y desvío 1,5 (es la definitiva) | `scipy`, `familia = "gamma"`, con `a` = forma y `scale` = escala del modelo §4.2 |
| D | Lognormal (μ, σ) | `scipy`, `familia = "lognorm"`, con `s` = σ, `scale` = e^μ y `loc` = 0 |
| DEM | Exponencial (es la definitiva) | `scipy`, `familia = "expon"`, con `scale` = la media del modelo §4.2 |
| TAR | Uniforme entre a y b, independiente de la distancia | `modo = "independiente"`, `scipy`, `familia = "uniform"`, con `loc` = a y `scale` = b − a |

Con esta traducción, la V1 reproduce exactamente las FDP provisorias del modelo. La V2 solo cambia la distancia y la tarifa.

La forma de la gamma de la búsqueda, (5 / 1,5)², se escribe con todos sus decimales (`a = 11.111111111111112`), no redondeada a 11,11: con el redondeo, la media daría 4,9995 en lugar de 5 (§5.6, regla 7).

### 5.8 Medias exactas para los valores de referencia

| Tipo | Media |
|---|---|
| `scipy` | `scipy.stats.<familia>(**parametros).mean()` |
| `constante` | El valor |
| `secuencia` | Promedio de los valores |

- E[TV] y E[S] se calculan como en §3.4. No se estiman simulando: son exactas por linealidad de la esperanza (modelo §4.4).
- La media de la tarifa no interviene en ningún valor de referencia.

### 5.9 Validación del catálogo al cargarlo

Antes de simular, en la primera iteración (T-14), en este orden:

1. **Versión:** `[catalogo]` tiene `version`, y vale "V1", "V2" o "PRUEBA".
2. **Modo de la tarifa:** `[TAR]` tiene `modo`, y vale "independiente". Cualquier otro valor es un error que dice que ese modo es de la segunda iteración. Va antes que la estructura porque una sección `[TAR]` en modo "regresion" no tiene `tipo` (§5.10.1), y el error tiene que decir por qué se rechaza, no que falta una clave.
3. **Estructura:** existen las secciones y claves obligatorias de §5.6 (regla 1), los tipos de FDP son los de §5.3 y la sección `[IA]` cumple la regla 2 de §5.6. Además:
   - con tipo `scipy`, `familia` es un texto y `parametros` es una tabla, que puede estar vacía (`parametros = {}`) y cuyos valores son números;
   - el `valor` de `constante` y los `valores` de `secuencia` son números (enteros o reales, nunca booleanos), y una `secuencia` tiene al menos un valor.
4. **Parámetros:** para cada distribución `scipy`:
   - la familia existe en `scipy.stats` y es una distribución continua (`isinstance(getattr(scipy.stats, familia), scipy.stats.rv_continuous)`): un nombre como `describe` existe, pero no es una distribución;
   - se puede construir con los parámetros dados;
   - su media (§5.8) es un número finito. scipy construye algunas distribuciones con parámetros inválidos, como `gamma` con `a = -1`, y devuelve NaN como media: este control las detecta.

   Cada falla es un error que indica la variable.

Cualquier falla es un error, y no se simula nada. Los valores negativos se controlan durante la corrida (§5.4, T-10).

En la segunda iteración se agregan el control del soporte, la muestra de control, la huella del archivo y el resto de los tipos permitidos por versión (§5.10.3). La regla de `[IA]` ya se controla en la primera, en el paso 3.

### 5.10 Segunda iteración: no implementar en la primera

Esta sección especifica lo que se implementa en la segunda iteración (D-16). Queda escrita para que, cuando llegue el momento, no haya que volver a diseñarlo. **No se implementa en la primera iteración** (§0.2, regla 8).

#### 5.10.1 Tarifa según la distancia: modo "regresión" (P-14; D-14 y D-15)

**Catálogo:** en lugar de la FDP de la tarifa, la sección `[TAR]` tiene los parámetros de la regresión y una subsección con la FDP del residuo. Los valores salen del modelo §4.5.6.

```toml
[TAR]
modo = "regresion"
base_usd = …
k_usd_por_mi = …
tarifa_minima_usd = …

[TAR.residuo]
tipo = "scipy"
familia = "…"                            # "norm", "t", "laplace" o "logistic"
parametros = { … }

[TAR.diagnostico]
r2 = …
n_filas = …
fraccion_resorteos = …
```

**Sorteo:** reemplaza al error del caso "regresion" de §5.5.

```
caso "regresion":
   resorteos ← 0
   REPETIR
      r ← sortear(TAR.residuo)                  // con el generador de TAR (k = 4)
      tar ← base + k × d + r
      SI tar < tarifa_minima ENTONCES
         resorteos ← resorteos + 1
         SI resorteos > MAX_RESORTEOS ENTONCES
            error "la FDP del residuo no es compatible con la tarifa mínima"     // T-11
         FIN SI
      FIN SI
   HASTA QUE tar ≥ tarifa_minima
   n_resorteos_tarifa ← n_resorteos_tarifa + resorteos
   DEVOLVER tar
```

- "Por debajo de la mínima" es estricto: una tarifa igual a la mínima se acepta (D-15).
- El residuo se sortea con el generador de la tarifa (k = 4), que puede consumir más de un valor por pedido por los re-sorteos. Como ese generador es propio de la variable, no altera a las demás, y los números aleatorios comunes se mantienen (D-09).
- Se agrega al estado de la corrida (§4.5) y a su resultado (§4.7) el diagnóstico `n_resorteos_tarifa`: la cantidad de re-sorteos de la corrida.
- Al implementarlo, §5.5 y §5.9 pasan a aceptar el modo "regresion".

#### 5.10.2 Distribución empírica (tipo `empirica`)

| Parámetros | Cómo se sortea | Media exacta |
|---|---|---|
| `archivo`: CSV con encabezado, en `data/processed/`; `columna`: nombre de la columna | Un valor de la muestra al azar, con reemplazo y con igual probabilidad para cada fila | Promedio de la muestra |

- La columna tiene solo números y al menos 100 filas.
- Se usa si ninguna familia paramétrica ajusta bien la distancia (modelo §4.5.1).

#### 5.10.3 Validación completa del catálogo

Además de lo de §5.9:

1. **Soporte:** para TB, D y DEM, el menor valor posible no es negativo. Se comprueba con el soporte de scipy (`.support()`) o con el mínimo de la muestra empírica. En los catálogos V1 y V2, TB y D deben ser además positivas: su menor valor posible es mayor que 0, o es 0 con probabilidad nula. Para la tarifa, `cdf(0)` menor que 10⁻⁹ (modelo §4.3).
2. **Muestra de control:** se sortean 10.000 valores de cada variable con un generador de validación propio (T-14). Se verifica que no haya valores negativos y que ninguna tarifa supere el tope de re-sorteos. Ese generador no se usa para nada más, así que validar no altera ninguna corrida.
3. **Huella:** se calcula el SHA-256 del catálogo, y del CSV de la distancia si es empírica, para registrarlo en las salidas (T-15).
4. **Tipos por versión** (T-16): `constante` y `secuencia` solo en un catálogo de PRUEBA. La sección `[IA]` ya se controla desde la primera iteración (§5.9, paso 3).

---

## 6. Motor de simulación

### 6.1 Interfaz

```
simular_corrida(NCH, nivel, parametros, fuentes, registrar_eventos = falso) → (resultado, registro)
```

- **Entradas:** los parámetros de §4.6, las fuentes de la réplica (§5.1) y si hay que registrar los eventos (T-18).
- **Salida:** el resultado de §4.7 y el registro de eventos con las filas de §9.3, que queda vacío si `registrar_eventos` es falso.
- **Precondiciones:** NCH es un entero ≥ 1; TF > 0 y finito; U > 0 (puede ser infinito); E[S] > 0 y finito. Las garantizan la validación de la configuración (§3.3), la del catálogo (§5.9), la de la línea de comandos (§8.6) y §3.4, así que el motor no las vuelve a controlar. Un valor negativo de una FDP se detecta recién al sortearlo (§5.4, T-10).

El motor no sabe nada del criterio de decisión ni de otras corridas (D-10).

### 6.2 Inicialización (modelo §8.4)

```
T ← 0 ; t_anterior ← 0
Ncd ← NCH ; Ncc ← 0 ; Nco ← 0 ; cola ← vacía
PARA CADA i DESDE 1 HASTA NCH HACER
   TLC(i) ← HV ; TPS(i) ← HV ; CA(i) ← vacío
FIN PARA
NT ← 0 ; NARR ← 0 ; NAT ← 0
SEC ← 0 ; SET ← 0 ; REC ← 0 ; RECP ← 0 ; STO ← 0 ; STC ← 0 ; STV ← 0
n_eventos ← 0 ; ns_max ← 0
IA ← fuentes.sortear_ia()
SI IA < TF ENTONCES TLL ← IA SI NO TLL ← HV FIN SI
SI registrar_eventos ENTONCES registrar el estado inicial (fila 0) FIN SI     // §9.3
```

La primera llegada sigue la misma regla que las demás: solo se agenda si cae antes de TF (modelo §8.4).

### 6.3 Ciclo principal (modelo §8.0)

```
MIENTRAS TLL ≠ HV O algún TLC(i) ≠ HV O algún TPS(i) ≠ HV HACER
   (tipo, i, t_evento) ← proximo_evento()            // §6.4
   acumular_areas(t_anterior, t_evento)              // §6.5, con el estado ANTERIOR al evento
   T ← t_evento ; t_anterior ← t_evento
   SEGÚN tipo:
      caso TPS: rutina_TPS(i)                        // §6.8
      caso TLC: rutina_TLC(i)                        // §6.7
      caso TLL: rutina_TLL()                         // §6.6
   n_eventos ← n_eventos + 1
   ns_max ← max(ns_max, Ns)
   SI verificar_invariantes ENTONCES verificar INV-01 a INV-09 FIN SI     // §7
   SI registrar_eventos ENTONCES registrar el evento FIN SI              // §9.3
FIN MIENTRAS
cerrar_horizonte()                                   // §6.9
SI verificar_invariantes ENTONCES verificar INV-F FIN SI                // §7
calcular_metricas()                                  // §6.10
```

### 6.4 Próximo evento y desempate (D-08, T-06)

1. `t_evento` es el menor valor entre TLL, todos los TLC(i) y todos los TPS(i).
2. Si más de un evento tiene ese instante, se procesa primero:
   1. un TPS(i), el de menor i;
   2. si no hay ninguno, un TLC(i), el de menor i;
   3. si tampoco, la TLL.
3. Los demás eventos de ese mismo instante se procesan en las vueltas siguientes del ciclo, con el mismo criterio.

- Con tiempos continuos, dos eventos casi nunca coinciden. Ocurre en las pruebas con valores fijos y cuando el tiempo de búsqueda es 0: la TLC queda en el mismo instante que la asignación.
- Procesar primero los fines de viaje libera choferes antes de que entre demanda nueva.
- La igualdad de instantes se evalúa exacta, sin tolerancia (T-06).

### 6.5 Acumulación de áreas (D-04, modelo §8.0)

```
procedimiento acumular_areas(desde, hasta):
   a ← min(desde, TF) ; b ← min(hasta, TF)
   SI b > a ENTONCES
      dt ← b − a
      STO ← STO + Ncd × dt
      STC ← STC + Ncc × dt
      STV ← STV + Nco × dt
   FIN SI
```

- Se llama antes de procesar cada evento, así que usa Ncd, Ncc y Nco del intervalo que termina.
- Después de TF no se acumula nada: durante el vaciamiento los choferes quedan libres por construcción (modelo §6.2).

### 6.6 Rutina TLL: llega un pedido (modelo §8.1)

**Origen:** D-02, D-05, D-09, D-14, S-04.
**Precondición:** T = TLL y T < TF.

```
// 1. Se crea el cliente
NT ← NT + 1
c ← nuevo cliente con id ← NT y t_llegada ← T
(c.tb, c.d, c.dem, c.tv, c.tar) ← fuentes.sortear_atributos()     // §5.4

// 2. Se agenda la próxima llegada
IA ← fuentes.sortear_ia()
SI T + IA < TF ENTONCES TLL ← T + IA SI NO TLL ← HV FIN SI

// 3. Asignación, espera o arrepentimiento
SI Ncd ≥ 1 ENTONCES
   i ← el menor índice con TLC(i) = HV y TPS(i) = HV            // S-04
   c.t_asignacion ← T
   NAT ← NAT + 1
   SEC ← SEC + 0                                                // atendido sin esperar: cuenta con 0
   Ncd ← Ncd − 1 ; Ncc ← Ncc + 1
   CA(i) ← c
   TLC(i) ← T + c.tb
SI NO
   TEE ← (Ns + 1) × E[S] / NCH + E[TB]                          // D-02; Ns antes de sumar a c
   SI TEE > U ENTONCES
      NARR ← NARR + 1
      RECP ← RECP + c.tar                                       // c sale del sistema
   SI NO
      agregar c al final de la cola                             // Ns aumenta en 1
   FIN SI
FIN SI
```

**Postcondición:** NT aumentó en 1, y exactamente uno de NAT, NARR o Ns aumentó en 1.

**Notas:**

- TEE usa E[S] y E[TB], que son constantes de la corrida (§3.4). Nunca usa el tb del propio cliente ni los tiempos ya sorteados de los viajes en curso: la app no conoce el futuro (D-02).
- La comparación es estricta: si TEE es igual a U, el cliente espera.
- E[S] y E[TB] se usan sin redondear (modelo §8.1).
- Si U es infinito, nadie se arrepiente.
- Cuando Ncd ≥ 1, la cola está vacía (INV-02): no hay nadie con prioridad sobre el cliente que llega.

### 6.7 Rutina TLC(i): el chofer i llega a buscar al cliente (modelo §8.2)

**Origen:** D-12.
**Precondición:** T = TLC(i), CA(i) ≠ vacío y TPS(i) = HV.

```
c ← CA(i)
c.t_recogida ← T
SET ← SET + (T − c.t_llegada)
Ncc ← Ncc − 1 ; Nco ← Nco + 1
TLC(i) ← HV
TPS(i) ← T + c.tv
```

**Postcondición:** el chofer i está ocupado: TLC(i) = HV y TPS(i) ≠ HV.

### 6.8 Rutina TPS(i): el chofer i termina el viaje (modelo §8.3)

**Origen:** D-04, S-04, S-08, S-09.
**Precondición:** T = TPS(i), CA(i) ≠ vacío y TLC(i) = HV.

```
c ← CA(i)
REC ← REC + c.tar                                                // c sale del sistema
TPS(i) ← HV ; CA(i) ← vacío
SI Ns ≥ 1 ENTONCES
   c2 ← quitar el primer cliente de la cola                      // orden de llegada, S-04
   c2.t_asignacion ← T
   SEC ← SEC + (T − c2.t_llegada)
   NAT ← NAT + 1
   Nco ← Nco − 1 ; Ncc ← Ncc + 1
   CA(i) ← c2
   TLC(i) ← T + c2.tb
SI NO
   Nco ← Nco − 1 ; Ncd ← Ncd + 1
FIN SI
```

**Postcondición:** el chofer i queda en camino, si había cola, o disponible, si no.

### 6.9 Fin de la corrida y cierre del horizonte (modelo §8.4)

El ciclo termina cuando TLL = HV y no queda ningún TLC(i) ni TPS(i) pendiente. En ese momento la cola está vacía: si quedara alguien esperando, no habría choferes disponibles (INV-02) y habría eventos pendientes.

```
procedimiento cerrar_horizonte():
   acumular_areas(t_anterior, TF)
```

**Por qué hace falta:** si el último evento ocurre antes de TF (por ejemplo, el último pedido terminó su viaje y la llegada siguiente cayó después de TF), ningún evento acumula el tramo entre ese instante y TF. En ese tramo todos los choferes están disponibles, así que se perdería ocio. El modelo pide medir el ocio en [0, TF] (D-04) y que al terminar STO + STC + STV = NCH × TF (modelo §5.7, invariante 7); este paso lo garantiza. Si el último evento ocurrió en TF o después, `acumular_areas` no suma nada.

### 6.10 Cálculo de las métricas (modelo §6.1 y §6.2)

```
SI NT = 0 ENTONCES
   sin_pedidos ← verdadero
   PET ← indefinido ; PEC ← indefinido ; PA ← indefinido
SI NO
   sin_pedidos ← falso
   PET ← SET / NAT
   PEC ← SEC / NAT
   PA ← NARR / NT × 100
FIN SI
PTO ← STO / (NCH × TF) × 100
PTC ← STC / (NCH × TF) × 100
PTV ← STV / (NCH × TF) × 100
RPC ← REC / NCH
```

- Si NT ≥ 1, entonces NAT ≥ 1: el primer pedido siempre encuentra todos los choferes disponibles. Por eso las divisiones por NAT son seguras.
- "Indefinido" se representa como NaN en el resultado, nunca como 0, para que no entre en ningún promedio por error.
- SEC y SET se dividen por el mismo NAT porque, gracias al vaciamiento, al terminar todos los atendidos ya fueron recogidos (modelo §6.2).

### 6.11 Volumen y rendimiento (informativo)

Con la demanda base hay unos 576 pedidos por corrida y alrededor de 1.700 eventos. Con a lo sumo 17 choferes (rango con las FDP provisorias), buscar el próximo evento recorriendo los vectores y verificar los invariantes en cada evento cuesta poco. El experimento completo procesa unos 2 millones de eventos, que en Python lleva minutos, no horas. No hace falta optimizar.

---

## 7. Invariantes

Se verifican después de cada evento, y INV-F una vez al final, cuando `verificar_invariantes` está activo: siempre en las pruebas y por defecto en el experimento (T-13). Si uno falla, el motor se detiene con un error que incluye el invariante, el evento que lo rompió, T y el estado completo.

| ID | Enunciado | Cuándo | Origen |
|---|---|---|---|
| INV-01 | Ncd + Ncc + Nco = NCH | Después de cada evento | modelo §5.7, invariante 1 |
| INV-02 | Si Ns > 0, entonces Ncd = 0 | Después de cada evento | modelo §5.7, invariante 2 |
| INV-03 | Ncc es la cantidad de choferes con TLC(i) ≠ HV; Nco es la cantidad con TPS(i) ≠ HV; ningún chofer tiene los dos distintos de HV | Después de cada evento | modelo §5.7, invariante 3 |
| INV-04 | CA(i) ≠ vacío si y solo si TLC(i) ≠ HV o TPS(i) ≠ HV | Después de cada evento | §4.3 |
| INV-05 | NT = NAT + NARR + Ns | Después de cada evento | modelo §5.7, invariante 4 |
| INV-06 | STO + STC + STV = NCH × min(T, TF), con una tolerancia relativa de 10⁻⁹ | Después de cada evento | modelo §5.7, invariante 5 |
| INV-07 | T no disminuye, y todo evento pendiente tiene un instante ≥ T | Después de cada evento | modelo §5.7, invariante 6 |
| INV-08 | TLL = HV o TLL < TF | Después de cada evento | modelo §8.1 |
| INV-09 | Cada cliente de la cola no tiene asignación y llegó en un instante ≤ T. Cada CA(i) cumple t_llegada ≤ t_asignacion ≤ T y, si el chofer está ocupado, t_asignacion ≤ t_recogida ≤ T | Después de cada evento | §4.2 |
| INV-F | Después del cierre: Ns = 0; NT = NAT + NARR; todos los TLC(i) y TPS(i) son HV; todos los CA(i) están vacíos; STO + STC + STV = NCH × TF, con una tolerancia relativa de 10⁻⁹ | Una vez, al final | modelo §5.7, invariante 7 |

**Propiedades entre corridas**, que verifica el orquestador (§8.5): en una misma réplica y un mismo nivel de demanda, todas las flotas tienen el mismo NT y la misma suma REC + RECP, con una tolerancia relativa de 10⁻⁹ porque el orden de las sumas cambia. Si no se cumplen, los números aleatorios comunes están rotos (D-09).

---

## 8. Orquestación del experimento

**Origen:** D-05, D-06, D-07, D-09, D-10.

### 8.1 Qué hace

El orquestador (`experimento.py`) prepara y recorre todas las corridas del experimento, controla que los números aleatorios comunes funcionen y escribe las salidas. No simula, porque eso lo hace el motor (§6), ni decide, porque eso lo hace el análisis (§10).

### 8.2 Preparación

```
procedimiento preparar(ruta_config):
   config ← leer y validar la configuración (§3.3)
   catalogo ← leer y validar el catálogo de FDP, con la ruta resuelta según §3.1 (§5.9)
   ref ← calcular los valores derivados (§3.4)
   flotas ← el rango de NCH (§3.4)
   agregar a flotas la flota actual y, si existe, la peor             // T-19
   ordenar flotas de menor a mayor, sin repetidos
   parametros ← U, TF, E[S], E[TB] y verificar_invariantes            // §4.6; NCH y nivel van aparte
   DEVOLVER (config, catalogo, ref, flotas, parametros)
```

Con el rango calculado por la regla del modelo §9.5, la flota actual y la peor ya están incluidas. Solo pueden faltar si `rango_manual` las deja afuera; en ese caso se agregan igual, porque sin ellas no existen los escenarios que pide la consigna.

### 8.3 Recorrido de las corridas

```
procedimiento ejecutar_experimento(ruta_config, salida):
   (config, catalogo, ref, flotas, parametros) ← preparar(ruta_config)
   crear la carpeta salida, con sus carpetas intermedias; si ya existe, error   // T-20
   escribir experimento.json en salida                                 // §9.1
   filas ← lista vacía
   PARA CADA nivel EN los niveles, en el orden de la configuración HACER
      PARA CADA NCH EN flotas, de menor a mayor HACER
         PARA CADA r DESDE 0 HASTA R − 1 HACER
            fuentes ← crear_fuentes(catalogo, semilla_base, r, media_ia del nivel, v)   // §5.1, §5.2
            (resultado, _) ← simular_corrida(NCH, nivel, parametros, fuentes)   // §6, sin registro de eventos
            agregar resultado, con la réplica r, a filas
         FIN PARA
         mostrar el avance: nivel, NCH, réplicas hechas y tiempo transcurrido
      FIN PARA
   FIN PARA
   verificar las propiedades entre corridas                            // §8.5
   escribir corridas.csv en salida                                     // §9.2
```

- Las fuentes se crean de nuevo en cada corrida (§5.2). Por eso el orden del recorrido no cambia ningún resultado: está fijado solo para que las filas de `corridas.csv` salgan siempre en el mismo orden.
- Si una corrida termina con error (un invariante que no se cumple, un valor negativo de una FDP), el experimento se detiene y el mensaje indica el nivel, la flota y la réplica. Esa corrida se puede repetir sola con el subcomando `corrida` (§8.4) para depurarla. La carpeta queda sin `corridas.csv`, lo que la marca como incompleta.

### 8.4 Corrida individual

```
procedimiento ejecutar_corrida(ruta_config, NCH, nivel, r, archivo_eventos):
   (config, catalogo, ref, flotas, parametros) ← preparar(ruta_config)
   fuentes ← crear_fuentes(catalogo, semilla_base, r, media_ia del nivel, v)
   (resultado, registro) ← simular_corrida(NCH, nivel, parametros, fuentes,
                                           registrar_eventos ← archivo_eventos ≠ vacío)
   mostrar el resultado por pantalla: una línea por valor de §4.7, con su nombre y su valor
   SI archivo_eventos ≠ vacío ENTONCES escribir el registro en archivo_eventos (§9.3) FIN SI
```

- Sirve para depurar una corrida y para obtener la tabla de eventos del documento de la entrega (T-18).
- NCH puede ser cualquier entero ≥ 1, aunque no esté entre las flotas del experimento.
- Si `archivo_eventos` ya existe, se reemplaza: es una salida de depuración que se regenera con el mismo comando.

### 8.5 Propiedades entre corridas (D-09)

Después del recorrido, para cada nivel y cada réplica, todas las flotas tienen que tener:

- el mismo NT, y
- la misma suma REC + RECP, con una tolerancia relativa de 10⁻⁹.

Si alguna no se cumple, los números aleatorios comunes están rotos. El experimento se detiene con un error que indica el nivel, la réplica y las flotas que difieren, y no escribe `corridas.csv`.

### 8.6 Línea de comandos

```
python -m simulador_maas experimento [--config RUTA] [--salida CARPETA]
python -m simulador_maas corrida --nch N [--nivel NOMBRE] [--replica R] [--config RUTA] [--eventos ARCHIVO]
python -m simulador_maas analisis --entrada CARPETA [--espera-max X] [--abandono-max Y]
```

Requieren el paquete instalado (§2.1, T-23). Las rutas de las opciones, y sus valores por defecto, son relativas a la carpeta desde la que se corre el comando: lo normal es correrlos desde la raíz del repositorio.

| Opción | Valor por defecto | Significado |
|---|---|---|
| `--config` | `config/experimento.toml` | Configuración (§3) |
| `--salida` | `results/pruebas/AAAAMMDD-HHMMSS`, con la fecha y hora de inicio | Carpeta del experimento. Para los resultados de la entrega se usa `results/finales/<nombre>` |
| `--nch` | Obligatoria | Flota de la corrida individual |
| `--nivel` | `base` | Nivel de demanda de la corrida individual |
| `--replica` | `0` | Réplica de la corrida individual |
| `--eventos` | Sin registro | Archivo CSV donde se escribe el registro de eventos |
| `--entrada` | Obligatoria | Carpeta de un experimento ya corrido |
| `--espera-max`, `--abandono-max` | Los de la configuración guardada en `experimento.json` | Umbrales X e Y del criterio (D-03, D-10) |

**Validación de las opciones,** antes de hacer cualquier otra cosa:

- `--nch` es un entero ≥ 1 y `--replica` un entero ≥ 0. Puede ser cualquier réplica, aunque sea mayor que R − 1: sus fuentes se crean igual (§5.2).
- `--nivel` es uno de los niveles de la configuración.
- `--espera-max`, si se da, es > 0, y `--abandono-max` está entre 0 y 100, como en §3.2.
- `--entrada` es una carpeta que contiene `experimento.json` y `corridas.csv`; si falta `corridas.csv`, el experimento quedó incompleto (§8.3).

Los errores terminan el programa con un código de salida distinto de 0 y un mensaje que dice qué falló y dónde.

---

## 9. Salidas

**Origen:** D-10.

Formato común de los CSV: UTF-8, separador coma, punto decimal y una fila de encabezado. Los números reales se escriben sin redondear. Un valor indefinido (NaN) se escribe como celda vacía. Los valores lógicos se escriben como 0 o 1. Las columnas enteras se escriben como enteros (`3`, no `3.0`) también cuando tienen celdas vacías; en pandas, con el tipo `Int64`.

### 9.1 `experimento.json`

Describe el experimento y permite reconstruirlo. Se escribe en UTF-8, con sangría de 2 espacios y con esta estructura exacta (los `…` son valores):

```json
{
  "fecha": "2026-10-02T15:30:00-03:00",
  "versiones": {"python": "…", "numpy": "…", "scipy": "…", "simulador_maas": "…"},
  "configuracion": {"ruta": "config/experimento.toml", "contenido": "…"},
  "catalogo": {"ruta": "config/fdp_v1.toml", "contenido": "…"},
  "analisis": {"espera_total_max_min": …, "abandono_max_pct": …, "nivel_confianza": …},
  "referencias": {
    "e_tb": …, "e_d": …, "e_dem": …, "e_tv": …, "e_s": …,
    "niveles": {
      "bajo": {"factor": …, "lambda": …, "media_ia": …, "carga": …},
      "base": {"factor": …, "lambda": …, "media_ia": …, "carga": …},
      "alto": {"factor": …, "lambda": …, "media_ia": …, "carga": …}
    },
    "flota_actual": …,
    "flota_peor": …,
    "rango": [desde, hasta],
    "flotas": [ … ]
  }
}
```

| Clave | Contenido |
|---|---|
| `fecha` | Fecha y hora de inicio, en formato ISO 8601 con la diferencia horaria |
| `versiones` | Versiones de Python, numpy, scipy y del paquete `simulador_maas`, como texto |
| `configuracion` | Ruta de `experimento.toml`, tal como se recibió en `--config` (o la de por defecto), y su **texto completo**, tal como se leyó. Va como texto y no como tabla para que sea una copia exacta, y porque un valor infinito (U = inf, §3.2) no tiene representación en JSON estándar |
| `catalogo` | Ruta del catálogo de FDP, resuelta según §3.1: la carpeta de la ruta de la configuración unida al valor de `catalogo_fdp`, sin convertirla en absoluta y con `/` como separador también en Windows (por ejemplo, `config/fdp_v1.toml`). Y su texto completo |
| `analisis` | X, Y y el nivel de confianza de la configuración, como números (§10.1) |
| `referencias` | Los valores derivados de §3.4. Los niveles van en el orden de la configuración. `flota_peor` vale `null` si no existe. `rango` es el que se usó: el de `rango_manual` si se indicó, o el de la regla. `flotas` es la lista de flotas simuladas (§8.2), de menor a mayor |

El análisis solo lee `analisis` y `referencias`. Copiar la configuración y el catálogo permite saber con qué valores exactos se obtuvo cada resultado, aunque los archivos cambien después. La huella SHA-256 del catálogo es de la segunda iteración (T-15).

### 9.2 `corridas.csv`

Una fila por corrida, en el orden del recorrido de §8.3: nivel, flota y réplica.

| Columna | Tipo | Unidad | Contenido |
|---|---|---|---|
| `nivel` | texto | — | Nivel de demanda |
| `nch` | entero | choferes | Flota |
| `replica` | entero | — | Réplica, desde 0 |
| `nt` | entero | pedidos | NT |
| `narr` | entero | pedidos | NARR |
| `nat` | entero | pedidos | NAT |
| `suma_espera_cola` | real | min | SEC |
| `suma_espera_total` | real | min | SET |
| `rec` | real | USD | REC |
| `recp` | real | USD | RECP |
| `sto` | real | chofer-minutos | STO |
| `stc` | real | chofer-minutos | STC |
| `stv` | real | chofer-minutos | STV |
| `pet` | real | min | PET; vacía si no hubo pedidos |
| `pec` | real | min | PEC; vacía si no hubo pedidos |
| `pa` | real | % | PA; vacía si no hubo pedidos |
| `pto` | real | % | PTO |
| `ptc` | real | % | PTC |
| `ptv` | real | % | PTV |
| `rpc` | real | USD por chofer | RPC |
| `t_ultimo_evento` | real | min | Instante del último evento; 0 si no hubo eventos |
| `n_eventos` | entero | — | Eventos procesados |
| `ns_max` | entero | pedidos | Cola más larga |
| `sin_pedidos` | 0 o 1 | — | 1 si NT = 0 |

### 9.3 Registro de eventos

Lo escribe solo el subcomando `corrida` con `--eventos` (T-18); las pruebas lo leen en memoria, sin escribirlo. Tiene una fila por evento, con el estado **después** de procesarlo, más una fila 0 con el estado inicial.

| Columna | Contenido |
|---|---|
| `n` | Número de evento; 0 para el estado inicial |
| `t` | Reloj T |
| `evento` | `INICIO`, `TLL`, `TLC` o `TPS` |
| `chofer` | Chofer del evento (en TLC y TPS) o chofer asignado al pedido (en TLL); vacío si no corresponde |
| `cliente` | Por su número de pedido: en TLL, el que llega; en TLC, el que es recogido; en TPS, el que termina su viaje. Vacío en INICIO |
| `detalle` | Qué pasó, en texto: "estado inicial", "asignado al chofer i", "espera (TEE = x)", "se arrepiente (TEE = x)", "recogido", "termina; toma al cliente j" o "termina; queda disponible". TEE se redondea a 4 decimales y se le sacan los ceros sobrantes y el punto final: 9 se escribe `9`, 9,5 se escribe `9.5` y 9,123456 se escribe `9.1235` |
| `ncd`, `ncc`, `nco`, `ns` | Variables de estado |
| `tll` | TLL, o `HV` |
| `tlc`, `tps` | Los vectores TLC y TPS, con sus valores separados por punto y coma y `HV` donde no hay evento |
| `nt`, `nat`, `narr` | Contadores |
| `suma_espera_cola`, `suma_espera_total`, `rec`, `recp`, `sto`, `stc`, `stv` | Acumuladores |

**En memoria,** el registro es una lista de filas, y cada fila es un diccionario con las columnas de esta tabla. Los valores son números: los instantes y acumuladores, reales; `n`, `chofer`, `cliente`, las variables de estado y los contadores, enteros; `tll` es un real, con `math.inf` para HV; `tlc` y `tps` son listas de NCH reales, con `math.inf` para HV, ordenadas por número de chofer. Lo vacío es `None`. Las pruebas comparan contra esta forma (§12.3).

**En el archivo,** con el formato común de §9: los reales se escriben como los escribe `repr()` de Python (`3.0`, `15.5`), los enteros sin decimales, `math.inf` como `HV` y `None` como celda vacía. Las celdas `tlc` y `tps` unen sus valores con punto y coma, con el mismo formato: por ejemplo, `3.0;HV`.

### 9.4 Carpeta de un experimento

```
<salida>/
├── experimento.json
├── corridas.csv
└── analisis_X<x>_Y<y>/          ← una por cada criterio analizado (§10.6)
```

---

## 10. Análisis

**Origen:** D-03, D-06, D-07, D-10; modelo §6.3 y §10.

El análisis (`analisis.py`) lee `experimento.json` y `corridas.csv` de una carpeta de experimento. Nunca llama al motor (§2.3).

### 10.1 Parámetros

- X (`espera_total_max_min`), Y (`abandono_max_pct`) y el nivel de confianza se toman de la clave `analisis` de `experimento.json` (§9.1).
- X e Y se pueden reemplazar desde la línea de comandos (§8.6). Así se aplica otro criterio sin volver a simular (D-10).

### 10.2 Agregación por configuración (modelo §6.3)

Para cada nivel y cada flota, y para cada métrica m entre PET, PEC, PA, PTO, PTC, PTV, REC, RECP y RPC:

```
valores ← los de las réplicas de ese nivel y esa flota, sin las celdas vacías (días sin pedidos)
n ← cantidad de valores
media ← promedio de los valores
s ← desvío estándar muestral, dividiendo por n − 1
α ← 1 − nivel_confianza
h ← t(1 − α / 2; n − 1) × s / √n          // t de Student: scipy.stats.t.ppf
IC ← [media − h ; media + h]
```

- Solo PET, PEC y PA pueden tener celdas vacías: son los días sin pedidos (§6.10). En las demás métricas, n es la cantidad de réplicas.
- Si n < 2, el desvío y el intervalo quedan indefinidos y se emite un aviso (A7). Si n = 0, la media también queda indefinida.
- `n_replicas` es la cantidad de filas de `corridas.csv` de ese nivel y esa flota, y `n_sin_pedidos` es la suma de su columna `sin_pedidos` (§10.6).

### 10.3 Criterio de decisión (D-03, modelo §10.1)

Para cada nivel y cada flota:

- **cumple** ⇔ media de PET ≤ X **y** media de PA ≤ Y. Las comparaciones no son estrictas: una media igual al umbral cumple. Una media indefinida no cumple.
- **en el límite** ⇔ el intervalo de PET contiene a X **o** el intervalo de PA contiene a Y, con los extremos incluidos. Si un intervalo es indefinido, esa parte da falso.

Para cada nivel, la **mejor flota** (NCH\*) es la menor flota que cumple.

**Avisos.** Se escriben en `avisos.txt` y se muestran por pantalla. Los cuatro primeros son los casos borde del modelo §10.5.

- **Formato de cada línea:** el código, el nivel entre corchetes (salvo en A8) y el texto. Por ejemplo: `A5 [base] Resultados no monótonos en el nivel base: la flota 5 no cumple.`
- **Una línea por caso:** A5, una por cada flota que no cumple; A7, una por cada nivel y flota afectados.
- **Orden:** por código (de A1 a A8), después por nivel, en el orden de la configuración, y después por flota, de menor a mayor.
- Las pruebas comparan el código, el nivel y la flota. El texto es orientativo.

| Código | Cuándo | Texto orientativo |
|---|---|---|
| A1 | Ninguna flota cumple en un nivel | "Ninguna flota cumple en el nivel N: ampliar el rango hacia arriba." |
| A2 | NCH\* es la mayor flota simulada | "La mejor flota del nivel N es el límite del rango: ampliarlo para ver la sobreoferta." Se usa la mayor flota simulada y no el límite superior del rango (modelo §10.5) porque, con T-19, puede haber flotas simuladas por encima del rango: lo que importa es si se ve alguna flota mayor que NCH\* |
| A3 | En el nivel base, la flota actual cumple | "La flota actual ya cumple el criterio." Es una conclusión válida, no un error. Se mira la flota actual directamente y no NCH\* ≤ flota actual, porque con resultados no monótonos (A5) lo segundo no garantiza lo primero |
| A4 | En el nivel base, NCH\* ≤ flota peor | "El criterio puede ser demasiado laxo: revisar X e Y." |
| A5 | Una flota mayor que NCH\* no cumple (T-22) | "Resultados no monótonos en el nivel N: la flota M no cumple." |
| A6 | NCH\* está en el límite | "La mejor flota del nivel N está en el límite: mirar también la siguiente." |
| A7 | `n_sin_pedidos` > 0, o n < 2 en alguna métrica (§10.2) | "En el nivel N, flota M: K réplicas sin pedidos." |
| A8 | No existe flota peor | "No existe flota peor: la flota actual es 1." |

### 10.4 Escenarios y sensibilidad (D-06, D-07; modelo §10.2 y §10.3)

- **Escenarios**, con el nivel base: peor = flota peor y actual = flota actual, las dos tomadas de `experimento.json`; mejor = NCH\* del nivel base. Si la flota peor no existe, se omite (A8). Si no hay NCH\*, la fila del escenario mejor queda con `escenario` = `mejor` y `nivel` = `base`, y todas sus demás celdas vacías (A1): la flota, las métricas, `n_replicas`, `n_sin_pedidos`, `cumple` y `en_el_limite`. Sin flota no hay una configuración de la que contar réplicas ni sobre la que evaluar el criterio.
- **Sensibilidad**, para cada nivel: NCH\* de ese nivel, y cómo le va a la flota actual con esa demanda.

### 10.5 Gráficos (modelo §10.6, T-21)

| Archivo | Eje horizontal | Eje vertical | Además |
|---|---|---|---|
| `fig_espera.png` | Cantidad de choferes (NCH) | Espera total media (min): PET, con su intervalo como barra de error | Línea horizontal en X |
| `fig_abandono.png` | Cantidad de choferes (NCH) | Abandono (%): PA, con su intervalo | Línea horizontal en Y |
| `fig_ocio.png` | Cantidad de choferes (NCH) | Tiempo ocioso (%): PTO, con su intervalo | — |
| `fig_recaudacion.png` | Cantidad de choferes (NCH) | Recaudación diaria (USD): REC y RECP | Sin intervalos, para que se lean las dos series de cada nivel |

- Una serie por nivel de demanda, en escala de grises. Las series se distinguen por marcador y tipo de línea (T-21). En `fig_recaudacion.png`, el tipo de línea distingue REC (continua) de RECP (discontinua), y el marcador distingue el nivel.
- Títulos de ejes en castellano y con unidades. PNG de 300 dpi, de 16 × 9 cm, con letra de al menos 8 puntos.

### 10.6 Archivos de salida

Van en `<entrada>/analisis_X<x>_Y<y>/`. X e Y se escriben sin decimales si son enteros (10 → `X10`) y, si no, como los escribe `str()` de Python (7.5 → `X7.5`); por ejemplo, `analisis_X10_Y5`. Si la carpeta existe, se reemplaza su contenido, porque el análisis se puede regenerar siempre a partir de `corridas.csv` (T-20).

| Archivo | Contenido |
|---|---|
| `parametros.json` | X, Y y el nivel de confianza usados, con las mismas claves que `analisis` en `experimento.json` |
| `resumen.csv` | Una fila por nivel y flota, ordenadas por nivel, en el orden de la configuración, y después por flota, de menor a mayor: `nivel`, `nch`, `n_replicas` y `n_sin_pedidos`; para cada métrica m (`pet`, `pec`, `pa`, `pto`, `ptc`, `ptv`, `rec`, `recp`, `rpc`), las columnas `m_media`, `m_desvio`, `m_ic_inf` y `m_ic_sup`; y `cumple` y `en_el_limite`, como 0 o 1 |
| `escenarios.csv` | Una fila por escenario del nivel base, en el orden peor, actual y mejor: una primera columna `escenario` (`peor`, `actual` o `mejor`) y las mismas columnas que `resumen.csv`. Si dos escenarios tienen la misma flota, cada uno tiene su fila. Si no hay NCH\*, la fila `mejor` tiene vacías todas las celdas salvo `escenario` y `nivel` (§10.4) |
| `sensibilidad.csv` | Una fila por nivel, en el orden de la configuración: `nivel`, `nch_mejor` (vacía si no hay), `nch_actual`, `actual_cumple` (0 o 1) y, para la flota actual en ese nivel, `pet_media`, `pa_media`, `pto_media`, `rec_media` y `recp_media` |
| `avisos.txt` | Un aviso por línea (§10.3), o "Sin avisos" |
| `fig_*.png` | Los gráficos de §10.5 |

Además se muestran por pantalla la tabla de escenarios y la mejor flota de cada nivel.

---

## 11. Errores y casos borde

| Situación | Comportamiento | Dónde |
|---|---|---|
| Configuración o catálogo inválidos, incluido un valor fuera de rango (por ejemplo, `horizonte_min = 0`, o `inf` en un real que no sea U) | Error antes de simular; no se escribe nada | §3.2, §3.3, §5.9 |
| Opción inválida en la línea de comandos (por ejemplo, `--nch 0` o un nivel que no existe) | Error antes de hacer nada | §8.6 |
| Catálogo con la tarifa en modo "regresion" | Error al cargarlo: es de la segunda iteración | §5.9 |
| Familia de scipy que no es una distribución continua, o con media no finita | Error al cargar el catálogo, con la variable | §5.9 |
| Sección `[IA]` en un catálogo V1 o V2, o IA `constante` 0 en uno de prueba | Error al cargar el catálogo | §5.6, regla 2 |
| Una FDP entrega un valor negativo | Error con la variable, el valor y el catálogo; quien llama al motor agrega el nivel, la flota y la réplica | §5.4, §8.3, T-10 |
| Una secuencia de prueba se agota | Error con la variable | §5.3 |
| No se cumple un invariante | Error con el invariante, el evento, T y el estado completo | §7 |
| No se cumplen las propiedades entre corridas | Error con el nivel, la réplica y las flotas; no se escribe `corridas.csv` | §8.5 |
| La carpeta de salida del experimento ya existe | Error: no se sobrescriben resultados | §8.3, T-20 |
| E[S] no finito o ≤ 0 | Error: no hay carga ni flotas de referencia | §3.4 |
| Día sin pedidos (NT = 0) | Métricas de espera y abandono vacías y `sin_pedidos` = 1; el análisis las excluye y avisa | §6.10, §10.2 |
| La flota actual es 1 | No hay flota peor; los escenarios son el actual y el mejor | §3.4, §10.4 |
| `rango_manual` deja afuera la flota actual o la peor | Se simulan igual | §8.2, T-19 |
| U infinito | Nadie se arrepiente (solo para pruebas) | §6.6 |
| TEE exactamente igual a U | El cliente espera | §6.6 |
| Eventos simultáneos | Se procesan en el orden de T-06 | §6.4 |
| El último evento ocurre antes de TF | El tramo hasta TF se acumula al cerrar | §6.9 |
| Un viaje termina después de TF | Se procesa (vaciamiento); las áreas se cortan en TF | §6.5 |
| Ninguna flota cumple, o la mejor es el límite del rango | Aviso A1 o A2: hay que ampliar el rango | §10.3 |
| Resultados no monótonos | Aviso A5: la conclusión requiere revisión | §10.3, T-22 |
| Menos de 2 réplicas válidas en una configuración | Intervalo indefinido; aviso A7 | §10.2 |

---

## 12. Plan de pruebas

**Origen:** modelo §9.7.

### 12.1 Organización

- Las pruebas usan pytest y viven en `tests/`. Se corren con `pytest` desde la raíz del repositorio, con el paquete instalado (T-23).
- Sus configuraciones y catálogos viven en `tests/datos/`. Los catálogos de prueba tienen `version = "PRUEBA"` y pueden usar los tipos `constante` y `secuencia` y la sección `[IA]` (§5.3, §5.6).
- Cada configuración de prueba tiene todas las claves obligatorias (§3.3). Las que una prueba no menciona toman los valores de `config/experimento.toml`; en las pruebas de esta sección no cambian el resultado.
- Una configuración de `tests/datos/` que usa el catálogo V1 lo indica como `catalogo_fdp = "../../config/fdp_v1.toml"`, porque la ruta es relativa a su propia carpeta (§3.1).
- Las pruebas que usan el catálogo V1 con los demás valores de `config/experimento.toml` (PR-02, PR-03 y PR-08) leen `tests/datos/v1_config.toml`, una copia de `config/experimento.toml` con el catálogo V1. Así no dependen del catálogo que use el experimento, y pasar a la V2 (§13, etapa 5) no cambia ninguna prueba. Si cambia un valor de `config/experimento.toml`, se cambia también en esa copia, en el mismo commit (§3.1).
- Las pruebas del motor (PR-01, PR-02, PR-05 a PR-07 y PR-10 (c)) pueden llamar a `simular_corrida` directamente, con `registrar_eventos` activo cuando comparan el registro (§4.6).
- Todas corren con `verificar_invariantes` activo.
- En las tablas de esta sección los números usan coma decimal, como el resto del documento.

### 12.2 Pruebas de la primera iteración

| ID | Tipo | Cubre | Qué verifica |
|---|---|---|---|
| PR-01 | Corrida calculada a mano | D-02, D-04, D-05, D-08, D-12, INV-01 a INV-09, INV-F | La tabla de eventos de §12.3, evento por evento, y los valores finales |
| PR-02 | Invariantes | D-14, INV-01 a INV-09, INV-F | Con `tests/datos/v1_config.toml` (catálogo V1, §12.1), nivel base, flotas 1, 4, 9 y 17 y réplicas 0 a 2: ninguna corrida viola un invariante |
| PR-03 | Números aleatorios comunes | D-01, D-09 | (a) Con `tests/datos/v1_config.toml` (catálogo V1, §12.1), nivel base, réplica 0 y flotas 4, 9 y 17: el mismo NT y la misma REC + RECP, con tolerancia relativa de 10⁻⁹. (b) Con la misma configuración, las fuentes de la réplica 0 en los niveles bajo, base y alto dan los mismos atributos para los primeros 100 pedidos, y sus intervalos entre pedidos son proporcionales a la media de cada nivel, con tolerancia relativa de 10⁻¹² (en punto flotante, el cociente no da exacto) |
| PR-04 | Reproducibilidad | D-09 | El experimento de PR-11, corrido dos veces, da archivos `corridas.csv` idénticos |
| PR-05 | Caso borde: día sin pedidos | D-04, D-05 | §12.4 |
| PR-06 | Caso borde: eventos simultáneos | D-08, T-06 | §12.4 |
| PR-07 | Caso borde: TEE igual a U | D-02 | §12.4 |
| PR-08 | Valores derivados | D-07; secciones 4.4 y 9.3 a 9.5 del modelo | Con `tests/datos/v1_config.toml`, es decir, el catálogo V1 y los demás valores de `config/experimento.toml` (§12.1): E[S] = 20,0163854565 y cargas de 5,6045879278, 8,0065541826 y 10,408520437, todos con tolerancia relativa de 10⁻⁹; flota actual 9; peor 8; rango de 4 a 17 |
| PR-09 | Análisis | D-03, D-06, D-10, T-22 | §12.5 |
| PR-10 | Validaciones | D-14, D-16, T-10 | (a) Un catálogo con `modo = "regresion"` da error al cargarlo, y el mensaje dice que es de la segunda iteración. (b) Da error al cargarlo un catálogo con una familia que no existe en scipy, con una que existe pero no es una distribución (`describe`) o con `gamma` y `a = -1` (media no finita). (c) Con los datos de PR-06, pero con búsqueda `constante` −1: E[S] = 2 pasa los controles, y la corrida da error al procesar el primer pedido (T = 1), con la variable TB en el mensaje. (d) Una configuración sin el nivel `base` da error. (e) Una configuración con `horizonte_min = 0` da error, con la clave en el mensaje, y también una con `horizonte_min = inf`, con `rango_manual = [0, 2]` o con `rango_manual = [5]`; en cambio, una con `umbral_tolerancia_min = inf` es válida (§3.2). (f) El subcomando `corrida` con `--nch 0` da error antes de simular |
| PR-11 | Experimento reducido de punta a punta | D-06, D-10 | Catálogo V1, solo el nivel base, 2 réplicas y `rango_manual` de 8 a 10; las demás claves, como en `config/experimento.toml`: `corridas.csv` tiene 6 filas (3 flotas por 2 réplicas); `experimento.json` tiene el E[S], la carga del nivel base y las flotas actual y peor de PR-08; y el análisis genera todos sus archivos sin errores |

### 12.3 PR-01: corrida calculada a mano

**Datos.** Configuración: v = 60 mi/h (así, el tiempo de viaje en minutos es igual a la distancia en millas), U = 15 min y TF = 30 min. Flota: NCH = 2. Catálogo de prueba:

| Variable | Tipo | Valores |
|---|---|---|
| IA | `secuencia` | 1; 1,5; 1,5; 1; 15; 15 |
| TB | `secuencia` | 2; 1; 3; 2; 2 |
| D | `secuencia` | 10; 12; 13; 13; 12 |
| DEM | `constante` | 0 |
| TAR | `secuencia`, modo independiente | 10; 20; 30; 40; 50 |

Con esto, E[TB] = 2, E[D] = 12 y E[S] = 2 + 60 × 12 / 60 + 0 = 14. Los pedidos llegan en los instantes 1; 2,5; 4; 5 y 20. El siguiente caería en 35, después de TF.

**Qué cubre:** asignación inmediata, cliente que espera, cliente que se arrepiente, fin de viaje que toma al primero de la cola, fin de viaje que deja al chofer disponible, llegada que cae después de TF, viaje que termina después de TF (vaciamiento) y corte de las áreas en TF.

**Eventos y estado**, después de cada evento:

| n | T | Evento | Qué pasa | Ncd | Ncc | Nco | Ns | TLL | TLC(1) | TLC(2) | TPS(1) | TPS(2) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | Inicio | — | 2 | 0 | 0 | 0 | 1 | HV | HV | HV | HV |
| 1 | 1 | TLL | Llega c1: se asigna al chofer 1 | 1 | 1 | 0 | 0 | 2,5 | 3 | HV | HV | HV |
| 2 | 2,5 | TLL | Llega c2: se asigna al chofer 2 | 0 | 2 | 0 | 0 | 4 | 3 | 3,5 | HV | HV |
| 3 | 3 | TLC(1) | El chofer 1 recoge a c1 | 0 | 1 | 1 | 0 | 4 | HV | 3,5 | 13 | HV |
| 4 | 3,5 | TLC(2) | El chofer 2 recoge a c2 | 0 | 0 | 2 | 0 | 4 | HV | HV | 13 | 15,5 |
| 5 | 4 | TLL | Llega c3: TEE = 1 × 14 / 2 + 2 = 9 ≤ 15, espera | 0 | 0 | 2 | 1 | 5 | HV | HV | 13 | 15,5 |
| 6 | 5 | TLL | Llega c4: TEE = 2 × 14 / 2 + 2 = 16 > 15, se arrepiente | 0 | 0 | 2 | 1 | 20 | HV | HV | 13 | 15,5 |
| 7 | 13 | TPS(1) | Termina c1: el chofer 1 toma a c3 | 0 | 1 | 1 | 0 | 20 | 16 | HV | HV | 15,5 |
| 8 | 15,5 | TPS(2) | Termina c2: el chofer 2 queda disponible | 1 | 1 | 0 | 0 | 20 | 16 | HV | HV | HV |
| 9 | 16 | TLC(1) | El chofer 1 recoge a c3 | 1 | 0 | 1 | 0 | 20 | HV | HV | 29 | HV |
| 10 | 20 | TLL | Llega c5: se asigna al chofer 2; la llegada siguiente (35) cae después de TF | 0 | 1 | 1 | 0 | HV | HV | 22 | 29 | HV |
| 11 | 22 | TLC(2) | El chofer 2 recoge a c5 | 0 | 0 | 2 | 0 | HV | HV | HV | 29 | 34 |
| 12 | 29 | TPS(1) | Termina c3: el chofer 1 queda disponible | 1 | 0 | 1 | 0 | HV | HV | HV | HV | 34 |
| 13 | 34 | TPS(2) | Termina c5, después de TF (vaciamiento) | 2 | 0 | 0 | 0 | HV | HV | HV | HV | HV |

**Contadores y acumuladores**, después de cada evento:

| n | NT | NAT | NARR | SEC | SET | REC | RECP | STO | STC | STV |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| 2 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 3,5 | 1,5 | 0 |
| 3 | 2 | 2 | 0 | 0 | 2 | 0 | 0 | 3,5 | 2,5 | 0 |
| 4 | 2 | 2 | 0 | 0 | 3 | 0 | 0 | 3,5 | 3 | 0,5 |
| 5 | 3 | 2 | 0 | 0 | 3 | 0 | 0 | 3,5 | 3 | 1,5 |
| 6 | 4 | 2 | 1 | 0 | 3 | 0 | 40 | 3,5 | 3 | 3,5 |
| 7 | 4 | 3 | 1 | 9 | 3 | 10 | 40 | 3,5 | 3 | 19,5 |
| 8 | 4 | 3 | 1 | 9 | 3 | 30 | 40 | 3,5 | 5,5 | 22 |
| 9 | 4 | 3 | 1 | 9 | 15 | 30 | 40 | 4 | 6 | 22 |
| 10 | 5 | 4 | 1 | 9 | 15 | 30 | 40 | 8 | 6 | 26 |
| 11 | 5 | 4 | 1 | 9 | 17 | 30 | 40 | 8 | 8 | 28 |
| 12 | 5 | 4 | 1 | 9 | 17 | 60 | 40 | 8 | 8 | 42 |
| 13 | 5 | 4 | 1 | 9 | 17 | 110 | 40 | 9 | 8 | 43 |

En el evento 13, el tramo de 29 a 34 se corta en TF: solo cuenta un minuto, con un chofer disponible y otro ocupado. Al cerrar el horizonte no se acumula nada más, porque el último evento ocurrió después de TF (§6.9).

**Valores finales esperados:**

| Valor | Esperado | Cuenta |
|---|---|---|
| NT, NAT, NARR y Ns | 5, 4, 1 y 0 | NT = NAT + NARR |
| STO + STC + STV | 60 | NCH × TF = 2 × 30 (INV-F) |
| PET | 4,25 min | SET / NAT = 17 / 4 |
| PEC | 2,25 min | SEC / NAT = 9 / 4 |
| PA | 20 % | NARR / NT = 1 / 5 |
| PTO | 15 % | 9 / 60 |
| PTC | 13,333… % | 8 / 60 |
| PTV | 71,666… % | 43 / 60 |
| REC + RECP | 150 USD | La suma de las cinco tarifas |
| RPC | 55 USD | 110 / 2 |
| Eventos, cola más larga y último evento | 13, 1 y 34 | — |

Esperas por cliente, para controlar: c1 espera 0 en cola y 2 en total; c2, 0 y 1; c3, 9 y 12; c5, 0 y 2. c4 se arrepiente y no entra en las esperas.

**Cómo se compara:** la prueba compara, fila por fila, las columnas de las dos tablas con las del registro de eventos (§9.3), con tolerancia absoluta de 10⁻⁹ en los reales. La columna "Qué pasa" es solo una explicación para el lector: no se compara con `detalle`. Para comparar, las tablas se traducen a la forma en memoria del registro (§9.3): "Inicio" es `INICIO`; "TLC(1)" es el evento `TLC` con `chofer` = 1, y lo mismo con TPS; HV es `math.inf`; y la coma decimal es el punto (1,5 es 1.5).

Esta tabla sirve además como tabla de eventos para el documento de la entrega: `corrida --nch 2 --eventos ARCHIVO`, con `--config` apuntando a la configuración de esta prueba, reproduce sus valores.

### 12.4 Casos borde: PR-05 a PR-07

En los tres: v = 60 mi/h, TF = 30 min, demora constante 0 y tarifa constante 10 (modo independiente).

| Prueba | NCH | U | IA | TB | D | Esperado |
|---|---|---|---|---|---|---|
| PR-05: día sin pedidos | 3 | 15 | `constante` 30 | `constante` 1 | `constante` 1 | La primera llegada cae en TF, así que no hay pedidos: NT = 0, `sin_pedidos` = 1, PET, PEC y PA vacías, STO = 90, PTO = 100 %, REC = 0, ningún evento y último evento en 0 |
| PR-06: eventos simultáneos | 1 | 2 | `secuencia` 1; 3; 100 | `constante` 0 | `constante` 3 | En el instante 4 coinciden el fin del primer viaje y la llegada del segundo pedido. Con el orden de T-06 (primero el fin de viaje), el segundo pedido encuentra al chofer libre: NT = 2, NAT = 2, NARR = 0, REC = 20, STO = 24, STV = 6 y 6 eventos. Si se procesara primero la llegada, el pedido vería TEE = 3 > 2 y se arrepentiría |
| PR-07: TEE igual a U | 1 | 3 | `secuencia` 1; 1; 100 | `constante` 0 | `constante` 3 | El segundo pedido llega con el chofer ocupado: TEE = 1 × 3 / 1 + 0 = 3, igual a U, así que espera: NARR = 0, NAT = 2, SEC = 2 y SET = 2. Con U = 2,999, el mismo pedido se arrepiente: NARR = 1, NAT = 1 y RECP = 10 |

### 12.5 PR-09: análisis con datos sintéticos

Se arma a mano una carpeta de experimento con:

- `experimento.json`, solo con las claves que lee el análisis (§9.1): `analisis` con X = 10, Y = 5 y nivel de confianza 0,95; y `referencias` con un solo nivel (`base`), `flota_actual` = 3, `flota_peor` = 2, `rango` = [2, 5] y `flotas` = [2, 3, 4, 5]. Los demás valores de `referencias` (las medias y los datos del nivel) pueden valer 0.
- `corridas.csv`: 3 réplicas por flota con estos valores, `nt` = 100 y `sin_pedidos` = 0 en todas las filas; las demás métricas pueden valer 0.

| Flota | PET de las réplicas | PA de las réplicas |
|---|---|---|
| 2 | 20; 22; 24 | 10; 12; 14 |
| 3 | 12; 10; 8 | 4; 5; 6 |
| 4 | 5; 5; 5 | 0; 0; 0 |
| 5 | 11; 11; 11 | 0; 0; 0 |

**Esperado**, con t(0,975; 2) = 4,3026527:

| Flota | Media de PET | IC de PET | Media de PA | IC de PA | Cumple | En el límite |
|---|---|---|---|---|---|---|
| 2 | 22 | [17,0317; 26,9683] | 12 | [7,0317; 16,9683] | No | No |
| 3 | 10 | [5,0317; 14,9683] | 5 | [2,5159; 7,4841] | Sí | Sí |
| 4 | 5 | [5; 5] | 0 | [0; 0] | Sí | No |
| 5 | 11 | [11; 11] | 0 | [0; 0] | No | No |

- Mejor flota: 3. Escenarios: peor = 2, actual = 3 y mejor = 3.
- Avisos, exactamente estos tres y en este orden: A3 [base] (la flota actual ya cumple), A5 [base] flota 5 (no cumple: resultados no monótonos) y A6 [base] (la mejor flota está en el límite). En particular, no aparece A7.
- `sensibilidad.csv`: nivel base, `nch_mejor` = 3, `nch_actual` = 3 y `actual_cumple` = 1.

### 12.6 Pruebas de la segunda iteración

No se implementan en la primera iteración (§1.4).

| ID | Qué verifica |
|---|---|
| PR-12 | Contraste con Erlang C: sin arrepentimiento (U infinito), con búsqueda nula y tiempo de viaje exponencial, la espera media en cola de un experimento largo se acerca a la de la fórmula de Erlang C (M/M/c) |
| PR-13 | Modo regresión de la tarifa: re-sorteos, tope de re-sorteos y números aleatorios comunes (§5.10.1) |
| PR-14 | Distribución empírica: sorteo con reemplazo y media exacta (§5.10.2) |
| PR-15 | Validación completa del catálogo (§5.10.3) y rechazo de claves desconocidas en la configuración (§3.3) |

---

## 13. Plan de implementación por etapas

Cada etapa termina cuando pasan sus pruebas. Conviene un commit por etapa, con un mensaje que cite las secciones implementadas; por ejemplo, `feat(motor): rutinas de evento [SDD §6]`.

| Etapa | Qué se construye | Termina cuando pasan |
|---|---|---|
| 1. Base | `pyproject.toml` y `requirements.txt` (T-23); `config.py`, `aleatorios.py` y `referencias.py`; `config/experimento.toml` y `config/fdp_v1.toml` con los valores del modelo; la carpeta `tests/datos/` | PR-08, PR-03 (b) y PR-10 (a), (b), (d) y (e) |
| 2. Motor | `entidades.py` y `motor.py`, con invariantes y registro de eventos | PR-01, PR-02, PR-05, PR-06, PR-07 y PR-10 (c) |
| 3. Experimento | `experimento.py` y `__main__.py`, con los subcomandos `experimento` y `corrida` | PR-03 (a), PR-04, PR-10 (f) y PR-11 sin la parte del análisis |
| 4. Análisis | `analisis.py` y el subcomando `analisis` | PR-09 y PR-11 completa. Además, el experimento completo con la V1 corre y genera tablas y gráficos |
| 5. V2 | Cuando llegue `config/fdp_v2.toml`: se cambia `catalogo_fdp` en `config/experimento.toml` y se corre el experimento completo en `results/finales/`. Las pruebas no cambian: las que usan la V1 tienen su propia configuración (§12.1) | El experimento termina sin errores y el análisis genera sus archivos |
| 6. Cierre | Completar "Cómo se corre" en el README principal (instalación y los tres subcomandos de §8.6) y avisarle al equipo | No tiene pruebas propias: termina cuando el README está completo, todas las pruebas de las etapas anteriores pasan y se dio el aviso. No espera a la etapa 5: si `config/fdp_v2.toml` todavía no llegó, se cierra con la V1 y el aviso lo dice |

Mientras se esperan las FDP de la V2, las etapas 1 a 4 se hacen con la V1. Pasar a la V2 no requiere cambios de código (§1.2).

**Al terminar la etapa 6** (regla 9 de §0.2), quien implementó le informa al equipo:

1. Dónde están los resultados de la entrega (`results/finales/…`) o, si la etapa 5 todavía no se hizo, que faltan porque se espera `config/fdp_v2.toml`, y que al llegar alcanza con la etapa 5.
2. Que queda la segunda iteración, con la lista del modelo, sección 12.3. La primera mejora es que la tarifa dependa de la distancia (P-14).
3. Que cualquier integrante puede tomar una mejora: el procedimiento de cada una está en el modelo, sección 4.5, y en este documento, secciones 5.10 y 12.6.

---

## 14. Decisiones técnicas

### T-01 · Python 3.11 o posterior, con configuración en TOML

- **Origen:** técnica pura.
- **Decisión:** el simulador requiere Python 3.11 o posterior. La configuración se escribe en TOML y se lee con `tomllib`, de la biblioteca estándar.
- **Por qué:** TOML es legible, admite comentarios y tablas, y leerlo no requiere dependencias extra.
- **Alternativas:** YAML, que requiere una biblioteca externa y es propenso a errores de sangría; JSON, que no admite comentarios.

### T-02 · Ciclo evento a evento propio, sin bibliotecas de simulación

- **Origen:** D-08.
- **Decisión:** el motor implementa el ciclo de §6.3 directamente, sin SimPy ni bibliotecas similares.
- **Por qué:** el código queda en correspondencia uno a uno con la TEI, la TEF y el diagrama de flujo de la simulación.
- **Alternativas:** SimPy, que oculta la TEF y el avance del reloj dentro de la biblioteca, justo lo que el TP tiene que mostrar.

### T-03 · Configuración en dos archivos: experimento y catálogo de FDP

- **Origen:** técnica pura.
- **Decisión:** los parámetros del modelo y del experimento van en `experimento.toml`; las FDP, en un catálogo por versión.
- **Por qué:** las FDP las completa otra persona o un agente (modelo §4.5). Con un archivo propio, su entrega no toca la configuración del experimento y cada versión queda guardada.
- **Alternativas:** un solo archivo, que mezcla responsabilidades y obliga a editar el mismo archivo desde dos frentes.

### T-04 · HV es el infinito de punto flotante

- **Origen:** D-08.
- **Decisión:** HV = +∞.
- **Por qué:** es mayor que cualquier instante sin elegir un número grande arbitrario, y el mínimo entre vectores funciona sin casos especiales.
- **Alternativas:** un valor grande fijo (por ejemplo, 10⁹). Funciona, pero es un número mágico que podría quedar corto con otro horizonte.

### T-05 · TEF con dos vectores, y el estado del chofer deducido de ella

- **Origen:** D-08.
- **Decisión:** se mantienen los vectores TLC(i) y TPS(i) del modelo, sin un vector de estado aparte.
- **Por qué:** coincide con la notación de la cátedra y del modelo §7.2. Un vector de estado adicional sería información duplicada que puede desincronizarse.
- **Alternativas:** un único vector "próximo evento del chofer" más un vector de estado. Es posible porque un chofer nunca tiene dos eventos pendientes, pero se aleja del diagrama de la cátedra.

### T-06 · Desempate entre eventos simultáneos

- **Origen:** D-08.
- **Decisión:** ante un empate exacto se procesa primero el fin de viaje, después la llegada del chofer al cliente y por último la llegada de un pedido; dentro del mismo tipo, el chofer de menor número (§6.4).
- **Por qué:** libera choferes antes de que entre demanda nueva y hace determinista cada corrida.
- **Alternativas:** el orden en que se agendaron los eventos, que depende de la implementación y no se puede reproducir de una versión a otra.

### T-07 · Cola como fuente de Ns, y contadores de choferes verificados

- **Origen:** técnica pura.
- **Decisión:** Ns es la longitud de la cola y no se guarda aparte. Ncd, Ncc y Nco se guardan como contadores, porque son variables de estado del modelo, e INV-03 verifica que coincidan con la TEF.
- **Por qué:** guardar Ns por separado permite que se desincronice de la cola. Los contadores de choferes se usan en cada acumulación de áreas y conviene tenerlos a mano, con una verificación.
- **Alternativas:** deducir todo de la TEF en cada evento, que es correcto pero aleja el código de las variables del modelo.

### T-08 · Semillas por réplica y por variable

- **Origen:** D-09.
- **Decisión:** la semilla de la variable k en la réplica r es `SeedSequence(entropy=semilla_base, spawn_key=(r, k))`, con k fijo por variable (§5.2). Cada generador es un `Generator` sobre `PCG64`. El valor de `semilla_base` es un parámetro del modelo (§9.2) y se lee de la configuración.
- **Por qué:** cada combinación de réplica y variable tiene una secuencia propia, independiente y reproducible, que no cambia si se agregan réplicas.
- **Alternativas:** derivar semillas sumando números a la semilla base, que puede producir secuencias correlacionadas; o un solo generador, que rompe los números aleatorios comunes.

### T-09 · Búfer de tamaño fijo en los generadores

- **Origen:** técnica pura.
- **Decisión:** los generadores de tipo `scipy` y el de IA (§5.2) sortean valores en bloques de 1.024 y los entregan de a uno. El tamaño del bloque es una constante del código, no de la configuración, y no se cambia. Los tipos `constante` y `secuencia` no usan búfer.
- **Por qué:** sortear de a un valor con scipy es lento; en bloques es mucho más rápido. Con las familias de la V1 y la exponencial de IA, la secuencia es la misma que sorteando de a uno (se verificó con bloques de 1 a 4.096), así que el tamaño solo afecta la velocidad. Con otras familias podría depender del tamaño del bloque; por eso es fijo.
- **Alternativas:** sortear de a uno, más lento; o sortear todo al principio, cuando todavía no se sabe cuántos valores hacen falta.

### T-10 · Un valor negativo de una FDP es un error

- **Origen:** D-14.
- **Decisión:** si una FDP entrega un valor negativo para TB, D, DEM o TAR durante la corrida, la corrida se detiene con un error que indica la variable, el valor y el catálogo; quien llamó al motor agrega el nivel, la flota y la réplica (§5.4, §8.3).
- **Por qué:** corregirlo en silencio, por ejemplo recortándolo, introduciría el pico que el modelo §4.3 prohíbe y ocultaría un catálogo mal armado.
- **Alternativas:** recortar o volver a sortear, que cambian la distribución sin que nadie lo haya decidido.

### T-11 · Tope de re-sorteos de la tarifa

- **Alcance:** segunda iteración (§5.10.1).
- **Origen:** D-15.
- **Decisión:** si un pedido necesita más de 1.000 re-sorteos del residuo, el motor se detiene con un error de configuración.
- **Por qué:** sin tope, un catálogo incompatible, como una tarifa mínima mayor que casi todas las tarifas posibles, dejaría el programa en un ciclo infinito.
- **Alternativas:** no poner tope, con riesgo de ciclo infinito.

### T-12 · Redondeo hacia arriba con tolerancia

- **Origen:** D-07.
- **Decisión:** las flotas de referencia y los límites del rango usan ⌈x − 10⁻⁹⌉ en lugar de ⌈x⌉.
- **Por qué:** un error de redondeo de punto flotante puede convertir un valor que debería ser exactamente entero, por ejemplo 8, en 8,0000000000000002, y el techo daría 9. Pasa sobre todo en las pruebas con valores redondos. Para los valores reales, la diferencia es despreciable.
- **Alternativas:** ⌈x⌉ directo, frágil ante errores de redondeo.

### T-13 · Invariantes activos por defecto

- **Origen:** técnica pura.
- **Decisión:** `verificar_invariantes` vale `true` en `config/experimento.toml` y en todas las configuraciones de prueba. Es una clave obligatoria (§3.3), no un valor por defecto del código. Desactivarlo solo tiene sentido para medir rendimiento.
- **Por qué:** con este volumen de corridas verificarlos cuesta poco, y detecta errores de implementación en el momento en que ocurren.
- **Alternativas:** verificarlos solo en las pruebas, con lo que un error que solo aparece con ciertas semillas pasaría inadvertido.

### T-14 · Validación del catálogo al cargarlo

- **Origen:** D-14.
- **Decisión:** antes de simular se valida el catálogo. En la primera iteración, la versión, el modo de la tarifa, la estructura (incluida la regla de la sección `[IA]`) y que scipy acepte cada familia con sus parámetros (§5.9). En la segunda, además, el soporte y una muestra de control de 10.000 valores por variable (§5.10.3); la muestra usa generadores de validación con semilla `SeedSequence(entropy=semilla_base, spawn_key=(2³² − 1, k))`, una clave que ninguna réplica usa.
- **Por qué:** un catálogo con errores se detecta antes de gastar tiempo en el experimento, y la muestra de control no consume números de ninguna corrida.
- **Alternativas:** no validar, con lo que los errores aparecerían en medio del experimento o, peor, no aparecerían.

### T-15 · Huella del catálogo en las salidas

- **Alcance:** segunda iteración (§5.10.3). En la primera, las salidas registran solo la ruta del catálogo.
- **Origen:** D-10.
- **Decisión:** cada salida registra la ruta y el SHA-256 del catálogo usado, y del CSV de distancias si lo hay.
- **Por qué:** permite saber con qué FDP exactas se obtuvo cada resultado, aunque el archivo se modifique después.
- **Alternativas:** registrar solo la ruta, que no detecta cambios en el contenido.

### T-16 · Tipos de FDP restringidos según la versión del catálogo

- **Alcance:** segunda iteración (§5.10.3), salvo la regla de la sección `[IA]`, que se controla desde la primera (§5.9, paso 3).
- **Origen:** D-14.
- **Decisión:** los catálogos V1 y V2 admiten los tipos `scipy` y `empirica`; uno de PRUEBA, además, `constante` y `secuencia`, y una sección `[IA]` (§5.3, §5.6).
- **Por qué:** los valores fijos y la IA del catálogo existen solo para las pruebas. Restringirlos evita que lleguen por error a los resultados de la entrega.
- **Alternativas:** admitir todos los tipos en cualquier catálogo, con lo que un catálogo de prueba podría usarse por error en el experimento.

### T-17 · La tarifa tiene un modo en el catálogo

- **Origen:** D-14, D-16.
- **Decisión:** la sección `[TAR]` del catálogo incluye la clave `modo`. En la primera iteración solo se acepta "independiente", con la FDP de la tarifa en la misma sección. El modo "regresion" queda reservado para la segunda iteración (§5.10.1).
- **Por qué:** la segunda iteración se agrega sin cambiar el formato de los catálogos ya entregados: un catálogo de la primera iteración sigue siendo válido después.
- **Alternativas:** agregar la clave recién en la segunda iteración, que obligaría a modificar los catálogos existentes.

### T-18 · El registro de eventos es solo para corridas individuales

- **Origen:** técnica pura.
- **Decisión:** el motor registra eventos solo si quien lo llama lo pide. El subcomando `experimento` nunca lo pide; `corrida --eventos` sí (§8.4, §9.3). No es una clave de la configuración.
- **Por qué:** un experimento completo generaría unos 2 millones de filas que nadie va a leer. El registro sirve para depurar una corrida y para la tabla de eventos del documento de la entrega.
- **Alternativas:** una clave de configuración que lo active para todo el experimento, como en la versión 0.1 de este documento, con riesgo de generar archivos enormes por error.

### T-19 · Las flotas actual y peor se simulan siempre

- **Origen:** D-07.
- **Decisión:** el conjunto de flotas simuladas es el rango más la flota actual y la peor (§8.2).
- **Por qué:** con `rango_manual` podrían quedar afuera, y sin ellas no existen los escenarios que pide la consigna.
- **Alternativas:** dar un error si el rango manual las excluye, que obliga a corregir la configuración sin necesidad.

### T-20 · Una carpeta por experimento, sin sobrescribir

- **Origen:** D-10.
- **Decisión:** cada experimento escribe en su propia carpeta, por defecto `results/pruebas/` con la fecha y hora; si la carpeta ya existe, es un error. Los análisis van en subcarpetas por criterio y sí se regeneran, porque se derivan de `corridas.csv` (§9.4, §10.6).
- **Por qué:** ningún resultado se pierde por repetir un comando, y los que respaldan la entrega quedan separados en `results/finales/`.
- **Alternativas:** sobrescribir siempre, con riesgo de perder resultados; o pedir confirmación, que impide correrlo sin supervisión.

### T-21 · Gráficos en blanco y negro

- **Origen:** formato del documento de la cátedra (`docs/enunciado/formato_papers_estudiantes.doc`).
- **Decisión:** las series se distinguen por marcador y tipo de línea, en escala de grises; PNG de 300 dpi (§10.5).
- **Por qué:** el formato pide figuras preferentemente en blanco y negro, para que una impresión monocromática no pierda información.
- **Alternativas:** colores, que se confunden al imprimir en blanco y negro.

### T-22 · Aviso de resultados no monótonos

- **Origen:** D-03.
- **Decisión:** el criterio se aplica tal como lo define el modelo, la menor flota que cumple, pero si una flota mayor no cumple, el análisis lo avisa (A5) en lugar de corregirlo.
- **Por qué:** con arrepentimiento, agregar un chofer puede, en teoría, empeorar la espera de algún cliente: alguien que antes se iba ahora se queda y ocupa un chofer. No se espera que pase con las medias de 30 réplicas, pero si pasa, la conclusión necesita una revisión humana.
- **Alternativas:** exigir que cumplan también todas las flotas mayores, que cambiaría el criterio del modelo sin una decisión del equipo.

### T-23 · El paquete se instala en modo editable

- **Origen:** técnica pura.
- **Decisión:** en la raíz del repositorio, `pyproject.toml` declara el paquete `simulador_maas` (código en `src/`, versión 1.0.0, construido con setuptools), Python 3.11 o posterior y las bibliotecas de §2.1, salvo pytest. También indica a pytest que las pruebas están en `tests/`. Cada integrante lo instala una vez con `pip install -e .`; en modo editable, los cambios en `src/` se ven sin reinstalar. `requirements.txt` hace esa misma instalación (con la línea `-e .`) y agrega pytest y las líneas que ya tiene para el notebook (`fitter` y `jupyter`), así que alcanza con `pip install -r requirements.txt`. Las cuatro bibliotecas del simulador (numpy, scipy, pandas y matplotlib) se sacan de `requirements.txt`, porque las instala `-e .` con las versiones mínimas de `pyproject.toml`; así cada versión mínima está escrita en un solo lugar. El contenido final de `requirements.txt` es, en este orden: `-e .`, `pytest>=7.0`, `fitter` y `jupyter`. Como `-e .` necesita `pyproject.toml`, los dos archivos se crean juntos en la etapa 1 (§13).
- **Por qué:** con el código en `src/`, Python no encuentra el paquete si no está instalado. Instalado, `python -m simulador_maas` y `pytest` funcionan igual en Windows y en Linux, sin configurar variables de entorno.
- **Alternativas:** definir la variable `PYTHONPATH=src` antes de cada comando, que se escribe distinto en cada sistema y es fácil de olvidar; o poner el paquete en la raíz del repositorio, que funciona sin instalar pero mezcla el código con la documentación y los datos.

---

## 15. Matriz de trazabilidad

| Decisión | Secciones del SDD | Módulos | Pruebas |
|---|---|---|---|
| D-01 | §3.2, §5.2 | `config`, `aleatorios` | PR-03, PR-08 |
| D-02 | §3.4, §6.6 | `referencias`, `motor` | PR-01, PR-07 |
| D-03 | §3.2, §10.1, §10.3, T-22 | `config`, `analisis` | PR-09 |
| D-04 | §6.5, §6.9, §6.10, INV-06, INV-F | `motor` | PR-01, PR-05, PR-06 |
| D-05 | §3.2, §6.2, §6.6, §6.9, §8.3 | `config`, `motor`, `experimento` | PR-01, PR-05 |
| D-06 | §8.3, §10.4 | `experimento`, `analisis` | PR-09, PR-11 |
| D-07 | §3.4, §8.2, §10.4, T-12, T-19 | `referencias`, `experimento`, `analisis` | PR-08 |
| D-08 | §4.3, §4.5, §6.4, T-04, T-05, T-06 | `entidades`, `motor` | PR-01, PR-06 |
| D-09 | §5.2, §5.4, §8.5, T-08 | `aleatorios`, `experimento` | PR-03, PR-04 |
| D-10 | §2.3, §6.1, §8, §9, §10, T-15 (segunda iteración), T-20 | `experimento`, `analisis` | PR-09, PR-11 |
| D-11 | §0.3, §4.5, §4.8 | Todos | — |
| D-12 | §6.7 | `motor` | PR-01 |
| D-13 | Sin impacto en la implementación: es notación de la TEI | — | — |
| D-14 | §5.3 a §5.9, T-10, T-14, T-17; segunda iteración: §5.10, T-16 | `aleatorios` | PR-02, PR-08, PR-10 |
| D-15 | Segunda iteración: §5.10.1, T-11 | `aleatorios` | PR-13 (segunda iteración) |
| D-16 | §0.2 (reglas 8 y 9), §1.4, §3.3, §5.10, §12.6, §13 | Todos | PR-10 |

---

## 16. Cambios

| Versión | Fecha | Cambio | Motivo |
|---|---|---|---|
| 0.1 | 2026-10-02 | Borrador: secciones 0 a 7 y 14 a 16 completas; 8 a 13 con su alcance. Primera y segunda iteración separadas (§1.4, §5.10); tarifa en modo "independiente" (T-17). Basado en el modelo v2.1 | Etapas A y B del plan, más la sección 5 adelantada para definir el entregable de las FDP; recorte de la primera iteración por el plazo (D-16) |
| 1.0 | 2026-10-02 | Secciones 8 a 13 completas: orquestación, salidas, análisis, errores y casos borde, pruebas (con la corrida calculada a mano) y plan de implementación. Decisiones técnicas T-18 a T-23. El registro de eventos deja de ser una clave de configuración (T-18). Ajustes: intervalos de los catálogos de prueba sin escalar (§5.2), búfer solo para el tipo `scipy` (T-09), precisión de la forma de la gamma (§5.7), la ruta del catálogo se resuelve desde la carpeta de la configuración (§3.1) e instalación del paquete (T-23). Basado en el modelo v2.2 | Etapas C, D y E del plan |
| 1.1 | 2026-10-02 | Aclaraciones para implementar sin preguntar, sin cambiar ninguna decisión. §3.2 y T-08 toman la semilla base de la sección 9.2 del modelo. Tipos en la configuración: enteros donde se piden reales, nunca booleanos (§3.3). E[S] tiene que ser finito (§3.4). Parámetros del motor y firma de `crear_fuentes`: la media del intervalo y v van a las fuentes (§4.6, §5.1, §8.2 a §8.4). Método fijo para la exponencial de IA (§5.2). Claves obligatorias del catálogo, `[IA]` prohibida en V1 y V2, encabezado de la V1 y orden y alcance de la validación (§5.6, §5.7, §5.9). Precondiciones del motor (§6.1). Estructura exacta de `experimento.json` (§9.1), columnas enteras (§9) y registro de eventos (§9.3). Agregación, formato y orden de los avisos y nombre de la carpeta del análisis (§10). Datos y tolerancias de PR-01, PR-03, PR-08 a PR-11 (§12). Búfer de 1.024 (T-09). Validación de rangos de la configuración y de las opciones de la línea de comandos en la primera iteración, para que se cumplan las precondiciones del motor (§3.3, §8.6, PR-10 (e) y (f)). Alcance de la validación del catálogo alineado en §1.4, §5.9, §5.10.3, T-14 y T-16. Forma en memoria y formato del registro de eventos (§9.3, §12.3). Rutas en `experimento.json` (§9.1), orden de las filas del análisis y fila del escenario mejor sin NCH\* (§10.4, §10.6). Contenido de `requirements.txt` (T-23). La etapa 6 no espera a la 5 (§0.2, regla 9, y §13). Estado: aprobado. Basado en el modelo v2.3 | Revisión por tres lectores sin contexto, que siguieron las rutinas literalmente y reprodujeron todas las pruebas |
| 1.2 | 2026-10-02 | Solo U admite infinito: en los demás reales de la configuración, `inf` es un error (§3.2, con la precondición de §6.1, la tabla de §11 y PR-10 (e)). Sin cambios en el modelo | Consulta durante la implementación de la etapa 1: §3.2 decía "se admite infinito" solo para U, pero con "> 0" a secas `inf` pasaba la validación en los demás reales y podía dejar el motor en un ciclo sin fin |
| 1.3 | 2026-10-02 | Sin NCH\*, la fila del escenario mejor tiene vacías todas las celdas salvo `escenario` y `nivel`, incluidas `n_replicas`, `n_sin_pedidos`, `cumple` y `en_el_limite` (§10.4, §10.6). Sin cambios en el modelo | Consulta durante la implementación de la etapa 4: §10.4 decía "la flota y todas sus métricas vacías", pero no qué iba en las demás columnas de la fila |
| 1.4 | 2026-10-02 | Sin cambios de especificación: el catálogo `config/fdp_v2.toml` ya existe (§1.2, §1.3) y usa `weibull_min` y `skewnorm`, dos familias de `scipy` admitidas por §5.3. El notebook de las FDP pasa a ser `notebooks/fdps.ipynb` (ejemplo de §5.6). Basado en el modelo v2.4 | FDP definitivas (P-03 y P-04) |
| 1.5 | 2026-10-02 | PR-02, PR-03 y PR-08 leen `tests/datos/v1_config.toml`, una copia de `config/experimento.toml` con el catálogo V1, en lugar de `config/experimento.toml` (§12.1, §12.2). La etapa 5 aclara que las pruebas no cambian (§13). Sin cambios en el modelo | Consulta antes de la etapa 5: §1.2 y §13 decían que pasar a la V2 era cambiar `catalogo_fdp` en `config/experimento.toml` sin tocar el código, pero §12.2 definía PR-08 con el catálogo V1 y `config/experimento.toml`, así que con la V2 la prueba fallaba |
