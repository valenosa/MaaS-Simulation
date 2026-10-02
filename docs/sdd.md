# Especificación técnica del simulador (SDD)

**Simulador MaaS · cantidad óptima de choferes · Lyft, zona de Boston**

- **Versión:** 0.1
- **Basado en:** modelo v2.1 ([`modelo.md`](modelo.md))
- **Fecha:** 2 de octubre de 2026
- **Estado:** borrador. Las secciones 0 a 7 y 14 a 16 están listas para revisión; las 8 a 13 están pendientes.
- **Autores:** _completar integrantes del grupo_

---

## Cómo leer este documento

> **El símbolo "§" significa "sección".** "§6.6" es la sección 6.6 de este documento; "modelo §8.3" es la sección 8.3 del documento del modelo.

| Para… | Ver |
|---|---|
| Implementar el simulador | Todo, en orden, empezando por §0.2 |
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
8. Orquestación del experimento (pendiente)
9. Salidas (pendiente)
10. Análisis (pendiente)
11. Errores y casos borde (pendiente)
12. Plan de pruebas (pendiente)
13. Plan de implementación por etapas (pendiente)
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
9. **Al terminar la primera iteración, avisarle al equipo que queda la segunda.** Cuando pasen las pruebas de la última etapa de §13, recordar que existe la lista de mejoras de la segunda iteración (modelo, sección 12.3) y mostrarla. Si quien implementa es un agente de IA, lo dice explícitamente en su mensaje final, aunque nadie se lo pregunte. La primera de la lista es que la tarifa dependa de la distancia (P-14).

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

### 0.5 Estado de este borrador

Esta versión cubre las etapas A y B del plan (esqueleto, estructuras, motor e invariantes), más la sección 5, que se adelantó para dejar definido el entregable de las FDP. Las secciones 8 a 13 tienen solo su título y una línea de alcance.

Todo el documento distingue la primera iteración (la entrega) de la segunda (mejoras posteriores), según D-16. Lo de la segunda iteración está resumido en §1.4 y especificado en §5.10.

**Para la primera revisión, conviene mirar especialmente:**

- §6.6 a §6.8: que cada rutina haga exactamente lo que dice el modelo §8.
- §6.9: el cierre del horizonte cuando el último evento ocurre antes de TF.
- §5.6: que el formato de entrega sea claro para quien complete las FDP.
- §1.4 y §5.10: qué queda para la segunda iteración.
- §14: las decisiones técnicas tomadas.

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
| V2 | Las definitivas, en el catálogo `config/fdp_v2.toml` (§5.6). Respecto de la V1, solo cambian la distancia y la tarifa | Obtener los resultados de la entrega | P-03 y P-04 |

Pasar de la V1 a la V2 es cambiar el archivo de catálogo en la configuración. No requiere cambios de código ni de este documento, siempre que las FDP definitivas usen los tipos soportados (§5.3).

### 1.3 Pendientes del modelo y su efecto en la implementación

| Pendiente | Efecto en la implementación |
|---|---|
| P-01, P-02, P-09 | Ninguno: son consultas o avisos a la cátedra |
| P-03, P-04 | Solo el contenido del catálogo de la V2 |
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
| Validación del catálogo de FDP | Estructura, modo de la tarifa y error si aparece un valor negativo | Soporte, muestra de control, huella del archivo y tipos permitidos por versión | §5.9 y §5.10.3 |
| Validación de la configuración | Claves obligatorias y tipos | Rangos y rechazo de claves desconocidas | §3.3 |
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

### 2.2 Estructura de archivos

```
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
catalogo_fdp = "config/fdp_v1.toml"
rango_margen_inferior = …
rango_margen_superior = …
rango_manual = []            # opcional: [desde, hasta] reemplaza la regla del rango
verificar_invariantes = true
registrar_eventos = false

[analisis]
espera_total_max_min = …     # X
abandono_max_pct = …         # Y
nivel_confianza = …
```

| Clave | Tipo | Unidad | Origen del valor | Validación de rango (§3.3) |
|---|---|---|---|---|
| `modelo.velocidad_mph` | real | mi/h | S-06, modelo §4.2 | > 0 |
| `modelo.umbral_tolerancia_min` | real | min | D-02 | > 0; se admite infinito |
| `modelo.horizonte_min` | real | min | D-05 | > 0 |
| `demanda.media_ia_base_min` | real | min | D-01 | > 0 |
| `demanda.niveles` | tabla de nombre a real | — | modelo §9.3 | Al menos un nivel; todos > 0; existe `base` y vale 1 |
| `experimento.replicas` | entero | — | D-05 | ≥ 2: el intervalo de confianza necesita al menos dos |
| `experimento.semilla_base` | entero | — | T-08 | ≥ 0 |
| `experimento.catalogo_fdp` | texto | — | §5 | El archivo existe y es válido (§5.9) |
| `experimento.rango_margen_inferior` | entero | choferes | modelo §9.5 | ≥ 0 |
| `experimento.rango_margen_superior` | entero | choferes | modelo §9.5 | ≥ 0 |
| `experimento.rango_manual` | lista de 0 o 2 enteros | choferes | modelo §10.5 | Si tiene dos: 1 ≤ desde ≤ hasta |
| `experimento.verificar_invariantes` | booleano | — | T-13 | — |
| `experimento.registrar_eventos` | booleano | — | §9 | — |
| `analisis.espera_total_max_min` | real | min | D-03 | > 0 |
| `analisis.abandono_max_pct` | real | % | D-03 | Entre 0 y 100 |
| `analisis.nivel_confianza` | real | — | modelo §6.3 | Mayor que 0 y menor que 1 |

### 3.3 Reglas de validación

**Primera iteración:**

- Una clave obligatoria ausente es un error. Todas son obligatorias salvo `rango_manual`.
- Cada valor tiene el tipo de la tabla de §3.2; si no, es un error.
- Existe el nivel `base` y su factor vale 1. Es la única validación de rango de la primera iteración, porque sin ella la flota actual se calcularía mal sin ningún aviso (D-07).
- Cada mensaje de error indica la clave, el valor leído y la regla que no se cumple.
- La validación termina antes de simular: una configuración inválida no produce ninguna corrida.

**Segunda iteración (§1.4):**

- El resto de la columna "Validación de rango" de §3.2.
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
- Si E[S] ≤ 0, es un error: no hay carga ni flotas de referencia que calcular.

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
| Nivel de demanda y su media del intervalo entre pedidos | §3.4 |
| U, v y TF | Configuración (§3.2) |
| E[S] y E[TB] | §3.4 |
| Fuentes de valores aleatorios de la réplica | §5.1 y §5.2 |
| `verificar_invariantes` y `registrar_eventos` | Configuración (§3.2) |

### 4.7 Resultado de una corrida

Al terminar, el motor devuelve un registro con:

- **Identificación:** nivel de demanda, NCH y réplica.
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

### 5.2 Generadores y semillas (D-09)

- Hay **cinco generadores independientes**, uno por variable aleatoria, cada una con un número fijo k: IA = 0, TB = 1, D = 2, DEM = 3 y TAR = 4.
- **La semilla del generador de la variable k en la réplica r** (con r = 0, 1, …, R − 1) es la secuencia de semillas de numpy con entropía `semilla_base` y clave de derivación (r, k): `SeedSequence(entropy=semilla_base, spawn_key=(r, k))`. Cada generador es un `numpy.random.Generator` sobre `PCG64` (T-08).
- **Las fuentes se crean de nuevo para cada corrida,** a partir de su réplica. Por eso, en la réplica r, todas las flotas y todos los niveles de demanda reciben exactamente la misma secuencia de cada variable.
- **Intervalo entre pedidos:** IA = (media del intervalo del nivel) × E, con E exponencial de media 1 sorteada del generador de IA. Así, en los tres niveles de demanda el pedido número k tiene los mismos atributos y solo cambia cuándo llega (D-09).
- **Cada generador lo usa una sola variable y se consume en orden de pedido.** El pedido número k recibe el k-ésimo valor de TB, de D, de DEM y de TAR.
- **Está prohibido usar la API global de números aleatorios** (`numpy.random.exponential`, `numpy.random.seed`, el módulo `random`): su secuencia depende de todo lo que se haya sorteado antes en el programa.
- Los generadores entregan valores de a uno, a partir de un búfer interno de tamaño fijo (T-09).

### 5.3 Tipos de FDP soportados

| Tipo | Parámetros | Cómo se sortea | Catálogos que lo usan |
|---|---|---|---|
| `scipy` | `familia`: nombre de la distribución en `scipy.stats`; `parametros`: tabla con los nombres de scipy (forma, `loc`, `scale`) | `scipy.stats.<familia>(**parametros).rvs(random_state=generador)` | V1, V2 y PRUEBA |
| `constante` | `valor` | Siempre el mismo valor | PRUEBA |
| `secuencia` | `valores`: lista | Los valores en orden; agotarlos es un error | PRUEBA |

- `constante` y `secuencia` existen solo para las pruebas (§12).
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
version = "V2"                           # "V1", "V2" o "PRUEBA"
fecha = "AAAA-MM-DD"
responsable = "…"
origen = "notebooks/NotebookFDPs.ipynb"  # de dónde salen los valores
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

1. **Secciones obligatorias:** `[catalogo]`, `[TB]`, `[D]`, `[DEM]` y `[TAR]`. `[TAR.diagnostico]` es obligatoria en la V2 y opcional en las demás versiones.
2. **El intervalo entre pedidos no va en el catálogo** de la V1 ni de la V2: lo define el modelo (D-01) y su media está en `experimento.toml`. Solo un catálogo de PRUEBA puede incluir una sección `[IA]`, con tipo `constante` o `secuencia`, para fijar las llegadas.
3. **Con tipo `scipy`,** `familia` es el nombre exacto en `scipy.stats`, y `parametros` usa los nombres exactos de scipy, incluidos los de forma: `a` para `gamma`, `s` para `lognorm`, `c` para `weibull_min`, `a` y `b` para `johnsonsb`. Si falta `loc`, vale 0; si falta `scale`, vale 1.
4. **Atención con las convenciones:** la lognormal de numpy (`lognormal(mean=μ, sigma=σ)`) equivale en scipy a `lognorm` con `s` = σ y `scale` = e^μ.
5. **Modo de la tarifa:** en la primera iteración solo se acepta `modo = "independiente"`, con la FDP de la tarifa en la misma sección `[TAR]` (T-17). El formato del modo "regresion" está en §5.10.1.
6. **Unidades:** las del modelo (minutos, millas y USD). Las claves de diagnóstico llevan la unidad en el nombre.
7. **Los valores se copian tal como salen del notebook, sin redondear.**
8. **Un catálogo nuevo no pisa al anterior:** se agrega como archivo nuevo y se cambia `catalogo_fdp` en `experimento.toml`. Así cualquier corrida vieja se puede repetir.

### 5.7 Catálogo de la V1

`config/fdp_v1.toml` traduce la columna "FDP provisoria (mock)" del modelo §4.2 a este formato. Los valores se copian del modelo; esta tabla solo indica cómo se expresa cada una:

| Variable | Provisoria del modelo | Cómo va en el catálogo |
|---|---|---|
| TB | Gamma con media 5 y desvío 1,5 (es la definitiva) | `scipy`, `familia = "gamma"`, con `a` = forma y `scale` = escala del modelo §4.2 |
| D | Lognormal (μ, σ) | `scipy`, `familia = "lognorm"`, con `s` = σ, `scale` = e^μ y `loc` = 0 |
| DEM | Exponencial (es la definitiva) | `scipy`, `familia = "expon"`, con `scale` = la media del modelo §4.2 |
| TAR | Uniforme entre a y b, independiente de la distancia | `modo = "independiente"`, `scipy`, `familia = "uniform"`, con `loc` = a y `scale` = b − a |

Con esta traducción, la V1 reproduce exactamente las FDP provisorias del modelo. La V2 solo cambia la distancia y la tarifa.

### 5.8 Medias exactas para los valores de referencia

| Tipo | Media |
|---|---|
| `scipy` | `scipy.stats.<familia>(**parametros).mean()` |
| `constante` | El valor |
| `secuencia` | Promedio de los valores |

- E[TV] y E[S] se calculan como en §3.4. No se estiman simulando: son exactas por linealidad de la esperanza (modelo §4.4).
- La media de la tarifa no interviene en ningún valor de referencia.

### 5.9 Validación del catálogo al cargarlo

Antes de simular, en la primera iteración (T-14):

1. **Estructura:** existen las secciones y claves de §5.6, y los tipos de FDP son los de §5.3.
2. **Modo de la tarifa:** es "independiente". Cualquier otro es un error que dice que ese modo es de la segunda iteración.
3. **Parámetros:** cada distribución `scipy` se puede construir con la familia y los parámetros dados. Si scipy rechaza un nombre o un parámetro, es un error que indica la variable.

Cualquier falla es un error, y no se simula nada. Los valores negativos se controlan durante la corrida (§5.4, T-10).

En la segunda iteración se agregan el control del soporte, la muestra de control, la huella del archivo y los tipos permitidos por versión (§5.10.3).

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
4. **Tipos por versión** (T-16).

---

## 6. Motor de simulación

### 6.1 Interfaz

```
simular_corrida(NCH, nivel, parametros, fuentes) → resultado
```

- **Entradas:** los parámetros de §4.6 y las fuentes de la réplica (§5.1).
- **Salida:** el resultado de §4.7 y, si `registrar_eventos` está activo, el registro de eventos (§9).
- **Precondiciones:** NCH es un entero ≥ 1; TF > 0; U > 0 (puede ser infinito); E[S] ≥ 0 y E[TB] ≥ 0.

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
   SI registrar_eventos ENTONCES registrar el evento FIN SI              // §9
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

**Propiedades entre corridas**, que verifica el orquestador (§8): en una misma réplica y un mismo nivel de demanda, todas las flotas tienen el mismo NT y la misma suma REC + RECP, con una tolerancia relativa de 10⁻⁹ porque el orden de las sumas cambia. Si no se cumplen, los números aleatorios comunes están rotos (D-09).

---

## 8. Orquestación del experimento

> **Pendiente (etapa C).** Recorrido de niveles de demanda × flotas × réplicas; cálculo de las flotas de referencia y del rango (§3.4); control de las propiedades entre corridas (§7); interfaz de línea de comandos.

## 9. Salidas

> **Pendiente (etapa C).** Formato exacto del archivo de métricas por corrida (una fila por corrida, con la ruta del catálogo y los valores derivados; la huella del catálogo es de la segunda iteración) y del registro opcional de eventos.

## 10. Análisis

> **Pendiente (etapa C).** Agregación por configuración con intervalos de confianza; criterio de decisión con X e Y configurables; marca "en el límite"; casos borde del modelo §10.5; gráficos del modelo §10.6.

## 11. Errores y casos borde

> **Pendiente (etapa C).** Tabla de situaciones y comportamiento esperado que no corresponden a una sola rutina.

## 12. Plan de pruebas

> **Pendiente (etapa D).** Primera iteración: la corrida calculada a mano (2 choferes, valores fijos y la tabla de eventos esperada fila por fila), la verificación de invariantes, el control de números aleatorios comunes y los casos borde principales. Segunda iteración (§1.4): el contraste con Erlang C y los casos borde exhaustivos.

## 13. Plan de implementación por etapas

> **Pendiente (etapa E).** Qué se construye primero y qué pruebas tienen que dar bien para avanzar. La última etapa de la primera iteración es avisarle al equipo que queda la segunda (§0.2, regla 9).

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
- **Decisión:** la semilla de la variable k en la réplica r es `SeedSequence(entropy=semilla_base, spawn_key=(r, k))`, con k fijo por variable (§5.2). Cada generador es un `Generator` sobre `PCG64`.
- **Por qué:** cada combinación de réplica y variable tiene una secuencia propia, independiente y reproducible, que no cambia si se agregan réplicas.
- **Alternativas:** derivar semillas sumando números a la semilla base, que puede producir secuencias correlacionadas; o un solo generador, que rompe los números aleatorios comunes.

### T-09 · Búfer de tamaño fijo en los generadores

- **Origen:** técnica pura.
- **Decisión:** cada generador sortea valores en bloques de tamaño fijo y los entrega de a uno. El tamaño del bloque es una constante del código, no de la configuración.
- **Por qué:** sortear de a un valor con scipy es lento; en bloques es mucho más rápido. Como el tamaño es fijo, una semilla da siempre la misma secuencia.
- **Alternativas:** sortear de a uno, más lento; o sortear todo al principio, cuando todavía no se sabe cuántos valores hacen falta.

### T-10 · Un valor negativo de una FDP es un error

- **Origen:** D-14.
- **Decisión:** si una FDP entrega un valor negativo para TB, D, DEM o TAR durante la corrida, el motor se detiene con un error que indica la variable, el valor y el catálogo.
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
- **Decisión:** `verificar_invariantes` vale verdadero por defecto y siempre en las pruebas. Desactivarlo solo tiene sentido para medir rendimiento.
- **Por qué:** con este volumen de corridas verificarlos cuesta poco, y detecta errores de implementación en el momento en que ocurren.
- **Alternativas:** verificarlos solo en las pruebas, con lo que un error que solo aparece con ciertas semillas pasaría inadvertido.

### T-14 · Validación del catálogo al cargarlo

- **Origen:** D-14.
- **Decisión:** antes de simular se valida el catálogo. En la primera iteración, la estructura, el modo de la tarifa y que scipy acepte cada familia con sus parámetros (§5.9). En la segunda, además, el soporte y una muestra de control de 10.000 valores por variable (§5.10.3); la muestra usa generadores de validación con semilla `SeedSequence(entropy=semilla_base, spawn_key=(2³² − 1, k))`, una clave que ninguna réplica usa.
- **Por qué:** un catálogo con errores se detecta antes de gastar tiempo en el experimento, y la muestra de control no consume números de ninguna corrida.
- **Alternativas:** no validar, con lo que los errores aparecerían en medio del experimento o, peor, no aparecerían.

### T-15 · Huella del catálogo en las salidas

- **Alcance:** segunda iteración (§5.10.3). En la primera, las salidas registran solo la ruta del catálogo.
- **Origen:** D-10.
- **Decisión:** cada salida registra la ruta y el SHA-256 del catálogo usado, y del CSV de distancias si lo hay.
- **Por qué:** permite saber con qué FDP exactas se obtuvo cada resultado, aunque el archivo se modifique después.
- **Alternativas:** registrar solo la ruta, que no detecta cambios en el contenido.

### T-16 · Tipos de FDP restringidos según la versión del catálogo

- **Alcance:** segunda iteración (§5.10.3).
- **Origen:** D-14.
- **Decisión:** los catálogos V1 y V2 admiten los tipos `scipy` y `empirica`; uno de PRUEBA, además, `constante` y `secuencia`, y una sección `[IA]` (§5.3, §5.6).
- **Por qué:** los valores fijos y la IA del catálogo existen solo para las pruebas. Restringirlos evita que lleguen por error a los resultados de la entrega.
- **Alternativas:** admitir todos los tipos en cualquier catálogo, con lo que un catálogo de prueba podría usarse por error en el experimento.

### T-17 · La tarifa tiene un modo en el catálogo

- **Origen:** D-14, D-16.
- **Decisión:** la sección `[TAR]` del catálogo incluye la clave `modo`. En la primera iteración solo se acepta "independiente", con la FDP de la tarifa en la misma sección. El modo "regresion" queda reservado para la segunda iteración (§5.10.1).
- **Por qué:** la segunda iteración se agrega sin cambiar el formato de los catálogos ya entregados: un catálogo de la primera iteración sigue siendo válido después.
- **Alternativas:** agregar la clave recién en la segunda iteración, que obligaría a modificar los catálogos existentes.

---

## 15. Matriz de trazabilidad

| Decisión | Secciones del SDD | Módulos | Pruebas |
|---|---|---|---|
| D-01 | §3.2, §5.2 | `config`, `aleatorios` | Pendiente (§12) |
| D-02 | §3.4, §6.6 | `referencias`, `motor` | Pendiente (§12) |
| D-03 | §3.2; criterio en §10 | `config`, `analisis` | Pendiente (§12) |
| D-04 | §6.5, §6.9, §6.10, INV-06, INV-F | `motor` | Pendiente (§12) |
| D-05 | §3.2, §6.2, §6.6, §6.9 | `config`, `motor` | Pendiente (§12) |
| D-06 | §8 | `experimento` | Pendiente (§12) |
| D-07 | §3.4, T-12 | `referencias` | Pendiente (§12) |
| D-08 | §4.3, §4.5, §6.4, T-04, T-05, T-06 | `entidades`, `motor` | Pendiente (§12) |
| D-09 | §5.2, §5.4, propiedades entre corridas (§7), T-08 | `aleatorios`, `experimento` | Pendiente (§12) |
| D-10 | §2.3, §6.1, §10, T-15 (segunda iteración) | `analisis` | Pendiente (§12) |
| D-11 | §0.3, §4.5, §4.8 | Todos | — |
| D-12 | §6.7 | `motor` | Pendiente (§12) |
| D-13 | Sin impacto en la implementación: es notación de la TEI | — | — |
| D-14 | §5.3 a §5.9, T-10, T-14, T-17; segunda iteración: §5.10, T-16 | `aleatorios` | Pendiente (§12) |
| D-15 | Segunda iteración: §5.10.1, T-11 | `aleatorios` | Pendiente (§12) |
| D-16 | §0.2 (reglas 8 y 9), §1.4, §3.3, §5.10, §13 | Todos | — |

---

## 16. Cambios

| Versión | Fecha | Cambio | Motivo |
|---|---|---|---|
| 0.1 | 2026-10-02 | Borrador: secciones 0 a 7 y 14 a 16 completas; 8 a 13 con su alcance. Primera y segunda iteración separadas (§1.4, §5.10); tarifa en modo "independiente" (T-17). Basado en el modelo v2.1 | Etapas A y B del plan, más la sección 5 adelantada para definir el entregable de las FDP; recorte de la primera iteración por el plazo (D-16) |
