# Modelo de simulación: cantidad óptima de choferes en una plataforma MaaS

**Lyft · zona de Boston · simulación evento a evento**

- **Versión:** 2.0
- **Fecha:** 1 de octubre de 2026
- **Estado:** en revisión del equipo
- **Materia:** Simulación · UTN FRBA · Trabajo Práctico Nº 5
- **Autores:** _completar integrantes del grupo_
- **Reemplaza a:** v1.0, presentada en el análisis previo (los cambios están en la sección 13)

---

## Cómo leer este documento

Este documento explica **qué** se modela y **por qué** se tomó cada decisión. **Cómo** se programa está en la especificación técnica ([`sdd.md`](sdd.md)), que se deriva de este documento y no repite sus justificaciones.

| Para… | Ver |
|---|---|
| Entender el modelo en cinco minutos | Resumen |
| Entender cómo funciona el sistema | Secciones 1, 2 y 3 |
| Revisar por qué se decidió cada cosa | Sección 11 (registro de decisiones) |
| Encontrar lo que pide la cátedra (variables, TEI, TEF, escenarios) | Secciones 5, 7 y 10 |
| Programar el simulador | Secciones 4 a 9, y después `sdd.md` |

**Convenciones**

- **Unidades:** tiempo en minutos, distancia en millas, dinero en USD.
- **Identificadores:** D-xx son decisiones (sección 11), S-xx supuestos (sección 3) y P-xx pendientes (sección 12).
- **Valores numéricos:** están calculados con las FDP provisorias (mock). Cambian cuando se carguen las FDP ajustadas en el TP4; las reglas para calcularlos no cambian.

**Contenido**

0. Resumen
1. Contexto y objetivo
2. Descripción del sistema
3. Supuestos del modelo
4. Datos de entrada y FDPs
5. Clasificación de variables
6. Métricas de resultado
7. Tabla de Eventos Independientes y Tabla de Eventos Futuros
8. Descripción de los eventos
9. Diseño experimental
10. Criterio de decisión y escenarios
11. Registro de decisiones
12. Pendientes y limitaciones
13. Cambios respecto de la v1.0
14. Glosario

---

## 0. Resumen

- **Sistema:** pedidos de viaje de Lyft en una zona de Boston, atendidos por una flota de NCH choferes conectados.
- **Pregunta:** ¿cuál es la menor flota que da un servicio aceptable, y cómo cambia si la demanda sube o baja un 30 %?
- **Servicio aceptable:** espera total media (desde el pedido hasta que llega el auto) de 10 minutos o menos, y no más de un 5 % de clientes que abandonan (D-03).
- **Dinámica:** tres eventos. Llega un pedido (TLL), el chofer llega a buscar al cliente (TLC) y termina el viaje (TPS). Si no hay choferes libres y la app estima más de 15 minutos de espera, el cliente se arrepiente (D-02).
- **Experimento:** días de 24 horas (1440 min), 30 réplicas por configuración, tres niveles de demanda y un rango de flotas (de 4 a 17 choferes con las FDP provisorias).
- **Escenarios:** peor (flota por debajo de la demanda media), actual (flota dimensionada por el promedio) y mejor (la menor flota que cumple el criterio). Con las FDP provisorias, peor = 8 y actual = 9; el mejor sale de la simulación.
- **Forma de la respuesta:** "conviene pasar de 9 a N choferes; si la demanda sube un 30 %, harían falta M".

---

## 1. Contexto y objetivo

### 1.1 Problema

Una plataforma de movilidad como Lyft tiene que decidir cuántos choferes necesita conectados en una zona. La decisión tiene dos costos que se mueven en sentidos opuestos:

- **Con pocos choferes**, los clientes esperan mucho. Algunos cancelan y toman otro medio de transporte, y la plataforma pierde esa tarifa.
- **Con muchos choferes**, los clientes casi no esperan, pero los choferes pasan buena parte del día sin viajes. Ganan poco y tienden a dejar la plataforma.

El objetivo es encontrar el punto de equilibrio: la menor flota que mantiene el servicio dentro de un nivel aceptable.

### 1.2 Preguntas que responde la simulación

1. Con la demanda actual, ¿cuál es la menor cantidad de choferes conectados (NCH) que cumple el criterio de servicio?
2. ¿Qué le pasa a la flota actual si la demanda aumenta o disminuye un 30 %? ¿Cuántos choferes harían falta en cada caso?

### 1.3 Por qué hace falta simular

La cuenta intuitiva es: "llegan 0,4 pedidos por minuto y cada pedido ocupa a un chofer unos 20 minutos, así que con 8 choferes alcanza". Esa cuenta usa solo promedios. En la realidad los pedidos llegan en ráfagas y algunos viajes son mucho más largos que otros, así que con esa flota se forma cola en los momentos de mayor carga. Medir cuántos choferes más hacen falta para absorber esa variabilidad es justamente lo que aporta la simulación.

Además, el sistema combina elementos que las fórmulas cerradas de teoría de colas no cubren juntas: un servicio en dos etapas (búsqueda y viaje), clientes que se arrepienten según el tiempo de espera que les muestra la app y un horizonte finito de un día.

### 1.4 Alcance

**Incluido:** una plataforma, una zona, demanda constante durante el día, arrepentimiento al momento de pedir y tarifa que depende de la distancia.

**Fuera de alcance:** tarifa dinámica, ubicación geográfica de choferes y clientes, perfil horario de la demanda, turnos y desconexiones de choferes, cancelaciones durante la espera, viajes compartidos y competencia con otras plataformas.

### 1.5 Relación con la consigna del TP5

| La consigna pide | Dónde está |
|---|---|
| Clasificación de variables | Sección 5 |
| Tabla de Eventos Independientes (TEI) | Sección 7.1 |
| Tabla de Eventos Futuros (TEF) | Sección 7.2 |
| FDPs obtenidas en el TP4 | Sección 4 (ver P-01: la demanda es un supuesto) |
| Al menos tres escenarios: actual, mejor y peor | Sección 10.2 |
| Conclusión sobre el escenario más conveniente | Sección 10.4 |
| Desarrollo computacional | [`sdd.md`](sdd.md) y la carpeta `src/` |

---

## 2. Descripción del sistema

### 2.1 Recorrido de un pedido

1. Un cliente pide un viaje.
2. Si hay un chofer disponible, la plataforma se lo asigna en el acto.
3. Si no hay, la app le muestra un tiempo estimado de espera. Si supera los 15 minutos, el cliente se arrepiente y se va, y la plataforma pierde la tarifa. Si no, el cliente queda esperando en una cola por orden de llegada.
4. Cuando un chofer termina un viaje y hay clientes esperando, toma al primero de la cola.
5. El chofer asignado va a buscar al cliente (tiempo de búsqueda), lo recoge y hace el viaje (tiempo de viaje).
6. Al terminar el viaje, el cliente paga la tarifa y el chofer queda disponible, o toma al siguiente cliente de la cola si hay alguno.

```mermaid
flowchart TD
    A(["Llega un pedido (TLL)"]) --> B{"¿Hay un chofer disponible?"}
    B -- "Sí" --> C["Se le asigna el chofer"]
    B -- "No" --> E{"¿Tiempo estimado de espera mayor a 15 min?"}
    E -- "Sí" --> F(["Se arrepiente: se pierde la tarifa"])
    E -- "No" --> G["Espera en la cola, por orden de llegada"]
    G -- "un chofer termina un viaje (TPS)" --> C
    C --> H["El chofer va a buscarlo: tiempo de búsqueda TB"]
    H -- "lo recoge (TLC)" --> I["Viaje: tiempo de viaje TV"]
    I --> J(["Fin del viaje (TPS): se cobra la tarifa"])
```

### 2.2 Estados de un chofer

Cada chofer está, en todo momento, en uno y solo uno de tres estados:

| Estado | Significado | Variable que los cuenta |
|---|---|---|
| Disponible | Conectado y sin pedido asignado | Ncd |
| En camino | Yendo a buscar a un cliente que se le asignó | Ncc |
| Ocupado | Con el cliente a bordo, haciendo el viaje | Nco |

```mermaid
stateDiagram-v2
    direction LR
    state "Disponible (Ncd)" as D
    state "En camino (Ncc)" as C
    state "Ocupado (Nco)" as O
    [*] --> D: inicio del día
    D --> C: se le asigna un pedido que llega (TLL)
    C --> O: llega y recoge al cliente (TLC)
    O --> D: termina el viaje y no hay cola (TPS)
    O --> C: termina el viaje y hay cola (TPS)
```

Como cada chofer está en exactamente un estado, siempre se cumple que **Ncd + Ncc + Nco = NCH**.

### 2.3 Ejemplo de un pedido en el tiempo

| Minuto | Qué pasa | Evento |
|---|---|---|
| 100 | El cliente pide un viaje. No hay choferes disponibles, pero el tiempo estimado es menor a 15 minutos, así que entra a la cola. | TLL |
| 103 | Un chofer termina otro viaje y se le asigna este cliente. | TPS de ese chofer |
| 108 | El chofer llega y recoge al cliente. | TLC |
| 123 | Termina el viaje y el cliente paga. | TPS |

En este ejemplo:

- La **espera en cola** fue de 3 minutos (de 100 a 103). Es la parte de la espera que depende de cuántos choferes haya.
- El **tiempo de búsqueda** fue de 5 minutos (de 103 a 108). No depende de la flota (supuesto S-05).
- La **espera total**, la que percibe el cliente, fue de 8 minutos (de 100 a 108).
- El chofer quedó comprometido 20 minutos con este cliente (de 103 a 123): búsqueda más viaje. A esa suma se la llama **tiempo de servicio** (S).

---

## 3. Supuestos del modelo

Todo modelo simplifica la realidad. Esta tabla deja explícito qué se simplificó, por qué, y cómo puede afectar a los resultados.

| ID | Supuesto | Por qué | Efecto en los resultados |
|---|---|---|---|
| S-01 | Una sola plataforma (Lyft) y una zona chica de Boston. | Delimita el sistema. Las distancias del dataset vienen de rutas entre unos 12 barrios. | Los resultados valen para la zona, no para toda la ciudad. |
| S-02 | NCH es la cantidad de choferes **conectados al mismo tiempo**, y se mantiene constante todo el día. | Es la variable que la plataforma gestiona, por ejemplo con incentivos. Los turnos quedan fuera de alcance. | NCH no es la cantidad de choferes registrados: sostener 10 conectados todo el día requiere más personas rotando. |
| S-03 | Demanda homogénea: un pedido cada 2,5 minutos en promedio durante todo el día. Los pedidos llegan de a uno y los intervalos son exponenciales (proceso de Poisson). | No hay datos del perfil horario de Boston (D-01). | No hay horas pico. El nivel de demanda +30 % se puede leer como una aproximación a una hora pico. |
| S-04 | Cola única por orden de llegada. Si hay varios choferes disponibles, el pedido se asigna al de menor número. | Los choferes son idénticos, así que la elección no cambia ninguna métrica agregada. Se elige la regla más simple y determinista. | Las métricas por chofer individual (viajes de cada uno) no son significativas; solo las agregadas. |
| S-05 | El tiempo de búsqueda no depende de cuántos choferes haya libres ni de NCH. | No se modela la geografía. | En la realidad, con pocos choferes libres el más cercano suele estar más lejos. El modelo subestima la espera con flotas chicas, así que el NCH recomendado es una **cota inferior**. |
| S-06 | Tiempo de viaje = distancia ÷ velocidad media de 13 mi/h (≈ 21 km/h), más una demora aleatoria por tráfico. | El dataset no tiene duraciones de viaje. | Depende de la validación de la velocidad (P-07). |
| S-07 | El cliente solo puede arrepentirse al momento de pedir, según el tiempo estimado que muestra la app. Una vez en la cola, no abandona. El chofer no cancela. | Ver D-02. | Si en la realidad se cancelan pedidos mientras se espera, el abandono real es mayor que el simulado. |
| S-08 | Todo cliente que recibe un chofer completa el viaje y paga la tarifa al terminar. | Simplificación. | — |
| S-09 | Al terminar un viaje, el chofer queda disponible en el acto, sin reposicionarse. El traslado hacia el próximo cliente está incluido en el tiempo de búsqueda. | No se modela la geografía. | — |
| S-10 | Sin tarifa dinámica: la tarifa depende solo de la distancia. | Se modela el producto estándar sin recargo (D-14). | La recaudación no refleja los precios más altos de los momentos de alta demanda. |
| S-11 | El día empieza vacío: sin cola y con todos los choferes disponibles. | Condición inicial simple. Con demanda constante, el efecto del arranque dura poco frente a 1440 minutos. | Leve subestimación de la espera en los primeros minutos del día. |
| S-12 | Los atributos de cada cliente son independientes entre sí, salvo la tarifa y el tiempo de viaje, que dependen de la distancia. | No hay datos que indiquen otra relación. | — |

---

## 4. Datos de entrada y FDPs

### 4.1 Qué datos hay y para qué sirven

El dataset del TP4 (Kaggle, Uber y Lyft en Boston, noviembre y diciembre de 2018) **no registra viajes, sino cotizaciones**: un script consultó las APIs de Uber y Lyft cada pocos minutos, para rutas fijas entre unos 12 barrios y para cada producto. Lo confirman tres evidencias:

- Hasta 203 filas comparten el mismo timestamp: son un lote de consultas, no clientes simultáneos.
- Varios días tienen casi exactamente 20.000 filas, incluidos sábado, domingo y lunes. La demanda real no es tan constante.
- Hay días sin datos o casi vacíos: el script estuvo apagado.

Por eso el dataset sirve para algunas variables y no para otras. El detalle está en [`fdps-decisiones.pdf`](fdps-decisiones.pdf).

| Variable | ¿Sale del dataset? | Motivo |
|---|---|---|
| Intervalo entre pedidos | No | La diferencia entre timestamps mide el ritmo del script, no la demanda (D-01). |
| Distancia | Sí | Columna `distance`, deduplicada. |
| Tarifa | Sí | Columna `price`, solo el producto estándar. |
| Tiempo de viaje | No | No existe en el dataset; se calcula a partir de la distancia. |
| Tiempo de búsqueda | No | No existe en el dataset; es un supuesto. |

### 4.2 Fichas de las FDPs

| Símbolo | Variable | Origen | Distribución definitiva | FDP provisoria (mock) | Estado |
|---|---|---|---|---|---|
| IA | Intervalo entre pedidos (min) | Supuesto (D-01) | Exponencial, media 2,5 (niveles de demanda en 9.3) | La misma | Definitiva |
| TB | Tiempo de búsqueda (min) | Supuesto | Gamma o lognormal, media 5 y desvío 1,5 | Normal recortada en 1: `max(1, N(5; 1,5))` | Pendiente (P-06) |
| D | Distancia (mi) | Dataset: Lyft, deduplicado por timestamp + origen + destino | Lognormal, gamma, Weibull o empírica, elegida por BIC y gráfico QQ | Lognormal (μ = 1, σ = 0,5), media 3,08 | Pendiente (P-03) |
| DEM | Demora por tráfico (min) | Supuesto | Distribución con soporte positivo, a definir | `max(0, N(0; 2))`, media 0,80 | Pendiente (P-05) |
| TV | Tiempo de viaje (min) | Calculado | TV = D × 60 / v + DEM, con v = 13 mi/h | La misma | Validación pendiente (P-07) |
| TAR | Tarifa (USD) | Dataset: producto `Lyft`, sin recargo dinámico | base + k × D + residuo | Uniforme entre 5 y 25, independiente de D | Pendiente (P-04) |

### 4.3 Reglas para el ajuste de las FDPs

- Solo familias con soporte positivo para distancia, búsqueda y demora. Nunca corregir valores negativos con un recorte (`np.clip`): crea un pico falso en el mínimo.
- Elegir la distribución por BIC y gráfico QQ, no por el p-valor de Kolmogorov-Smirnov: con decenas de miles de datos, ese test rechaza casi cualquier distribución.
- Leer los parámetros desde el código del notebook (por ejemplo, `get_best()` de Fitter), no copiarlos a mano.
- Fijar la semilla al principio del notebook y correrlo de arriba hacia abajo.
- Revisar las muestras generadas: ningún valor negativo ni absurdo.

### 4.4 Valores de referencia: tiempo medio de servicio

Varios cálculos del modelo (el arrepentimiento y la flota actual) usan el **tiempo medio de servicio** E[S]: cuánto tiempo, en promedio, queda comprometido un chofer con un cliente desde que se lo asignan hasta que termina el viaje.

$$
E[S] = E[TB] + E[TV] = E[TB] + \frac{60 \cdot E[D]}{v} + E[DEM]
$$

Por linealidad de la esperanza, E[S] se calcula **de forma exacta** a partir de las medias de las FDP, sin necesidad de simular. Se calcula una sola vez, antes de las corridas, y se usa sin redondear.

| Valor | Con las FDP provisorias |
|---|---|
| E[TB] | 5,00 min |
| E[D] | 3,08 mi |
| E[TV] = 60 × E[D] / 13 + E[DEM] | 14,22 + 0,80 = 15,01 min |
| **E[S]** | **20,01 min** |

> **Sensibilidad a tener en cuenta.** Con las FDP provisorias, la carga del nivel base (sección 9.3) da 8,006, apenas por encima de 8. Si la demora por tráfico (P-05) tuviera media 0, daría 7,69, y la flota actual (D-07) pasaría de 9 a 8 choferes. Por eso los números de este documento son ilustrativos hasta que se carguen las FDP definitivas.

---

## 5. Clasificación de variables

### 5.1 Variables exógenas

Son las que vienen de afuera del sistema: o las impone el entorno (datos) o las decide la empresa (control).

| Tipo | Variable | Descripción |
|---|---|---|
| Datos aleatorios | IA | Intervalo entre pedidos (min) |
| Datos aleatorios | TB | Tiempo de búsqueda (min) |
| Datos aleatorios | D | Distancia del viaje (mi) |
| Datos aleatorios | DEM | Demora por tráfico (min) |
| Datos aleatorios | TAR | Tarifa (USD), a través de su residuo aleatorio |
| Datos calculados | TV | Tiempo de viaje: D × 60 / v + DEM |
| Datos fijos (supuestos) | v | Velocidad media: 13 mi/h |
| Datos fijos (supuestos) | U | Umbral de tolerancia del cliente: 15 min (D-02) |
| Datos fijos (supuestos) | base, k | Parámetros de la tarifa (P-04) |
| **Control** | **NCH** | **Cantidad de choferes conectados. Es la variable de decisión.** |

El umbral U es un dato y no una variable de control: la empresa no decide cuánta paciencia tienen sus clientes.

### 5.2 Variables endógenas de estado

| Variable | Descripción |
|---|---|
| Ncd | Cantidad de choferes disponibles |
| Ncc | Cantidad de choferes en camino hacia un cliente |
| Nco | Cantidad de choferes ocupados con un cliente a bordo |
| Ns | Cantidad de clientes esperando en la cola |

Además está el reloj de la simulación, T, que avanza de evento en evento.

### 5.3 Variables endógenas de resultado

Son las métricas que produce cada corrida. Se definen en la sección 6: PET, PA, PEC, PTO, REC y RECP, más algunas complementarias.

### 5.4 Variables auxiliares

Contadores y acumuladores que se actualizan durante la corrida y con los que se calculan los resultados al final.

| Variable | Qué guarda | Dónde se actualiza |
|---|---|---|
| NT | Cantidad de pedidos recibidos | TLL |
| NARR | Cantidad de clientes que se arrepintieron | TLL |
| NAT | Cantidad de clientes atendidos: los que recibieron un chofer, incluidos los que no esperaron | TLL (asignación inmediata) y TPS (asignación desde la cola) |
| SEC | Suma de las esperas en cola de los clientes atendidos | Mismos momentos que NAT |
| SET | Suma de las esperas totales de los clientes atendidos | TLC |
| REC | Recaudación acumulada (USD) | TPS |
| RECP | Recaudación perdida: suma de las tarifas de los clientes arrepentidos (USD) | TLL |
| STO | Chofer-minutos disponibles (ocio) dentro de [0, TF] | Antes de cada evento |
| STC | Chofer-minutos en camino dentro de [0, TF] | Antes de cada evento |
| STV | Chofer-minutos ocupados con cliente a bordo dentro de [0, TF] | Antes de cada evento |
| CA(i) | Cliente asignado al chofer i, para poder registrar su recogida y cobrar su tarifa | TLL, TPS |
| E[S], E[TB] | Tiempo medio de servicio y de búsqueda (sección 4.4). Son constantes durante la corrida. | Antes de simular |

### 5.5 Atributos de cada cliente

Cada cliente es una entidad temporal: nace en TLL y sale del sistema cuando se arrepiente o cuando termina su viaje.

| Atributo | Descripción | Cuándo se define |
|---|---|---|
| t_llegada | Instante en que pidió el viaje | TLL |
| TB, D, DEM, TV, TAR | Valores aleatorios propios del cliente | Todos se sortean en TLL, aunque después se arrepienta (D-09) |
| t_asignacion | Instante en que se le asignó un chofer | TLL o TPS |
| t_recogida | Instante en que el chofer lo recogió | TLC |

### 5.6 Parámetros del experimento

No son variables del sistema, sino de cómo se lo estudia: no cambian lo que ocurre dentro de una corrida, sino qué corridas se hacen y cómo se leen sus resultados.

| Parámetro | Valor | Dónde se define |
|---|---|---|
| TF | 1440 min (un día) | D-05 |
| R | 30 réplicas por configuración | D-05 |
| Semillas | Una por réplica, compartida entre configuraciones | D-09 |
| Niveles de demanda | Base, −30 % y +30 % | Sección 9.3 |
| Rango de NCH | Regla de la sección 9.5 | Sección 9.5 |
| X | 10 min: tope de la espera total media | D-03 |
| Y | 5 %: tope del abandono | D-03 |

X e Y son parámetros del **criterio de decisión**: se aplican sobre los resultados, después de simular. Por eso se configuran en el análisis y no en el motor (D-10).

### 5.7 Invariantes

Propiedades que se tienen que cumplir siempre. Sirven para verificar que el simulador está bien programado.

1. Ncd + Ncc + Nco = NCH.
2. Si hay clientes en la cola (Ns > 0), no hay choferes disponibles (Ncd = 0).
3. Ncc es igual a la cantidad de TLC(i) pendientes y Nco a la cantidad de TPS(i) pendientes. Ningún chofer tiene los dos pendientes a la vez.
4. NT = NAT + NARR + Ns: todo pedido está atendido, arrepentido o esperando.
5. STO + STC + STV = NCH × (tiempo transcurrido dentro de [0, TF]).
6. El reloj T nunca retrocede.
7. Al terminar: Ns = 0, NT = NAT + NARR y STO + STC + STV = NCH × TF.

---

## 6. Métricas de resultado

### 6.1 Definiciones

| Símbolo | Métrica | Cálculo | Uso |
|---|---|---|---|
| PET | Espera total media (min) | SET / NAT | **Criterio:** ≤ X = 10 min |
| PA | Porcentaje de abandono | NARR / NT × 100 | **Criterio:** ≤ Y = 5 % |
| PEC | Espera en cola media (min) | SEC / NAT | Informativa: la parte de la espera que depende de la flota |
| PTO | Porcentaje de tiempo ocioso | STO / (NCH × TF) × 100 | Informativa: muestra la sobreoferta |
| REC | Recaudación diaria (USD) | Valor final de REC | Informativa: resultado de negocio |
| RECP | Recaudación perdida por abandono (USD) | Valor final de RECP | Informativa |
| PTC / PTV | Porcentaje del tiempo en camino / ocupado | STC o STV / (NCH × TF) × 100 | Complementaria. PTO + PTC + PTV = 100 |
| RPC | Recaudación por chofer (USD) | REC / NCH | Complementaria |

### 6.2 Reglas de cálculo y casos borde

- **Clientes sin espera.** Un cliente al que se le asigna un chofer en el momento en que pide tiene espera en cola 0, y **sí** cuenta en NAT. Si se lo excluyera, el promedio quedaría sesgado hacia arriba.
- **Arrepentidos.** No entran en PET ni en PEC, porque nunca esperaron un auto. Sí cuentan en PA y en RECP.
- **Por qué el criterio mira la espera y el abandono juntos.** Si muchos clientes se arrepienten, la espera de los que quedan parece buena justamente porque se fueron los que más iban a esperar. Mirar solo la espera premiaría a las flotas más chicas.
- **Denominador común.** Gracias al vaciamiento (D-05), al terminar la corrida todos los clientes atendidos ya fueron recogidos y terminaron su viaje. Por eso SEC y SET se dividen por el mismo NAT.
- **Ocio y utilización.** Se miden solo dentro de [0, TF]. Durante el vaciamiento no llegan pedidos y los choferes quedan libres por construcción; contar ese tiempo inflaría el ocio de forma artificial.
- **Recaudación.** Incluye las tarifas de todos los pedidos hechos durante el día, aunque el viaje termine después de TF.
- **Día sin pedidos.** Si NT = 0, las métricas no están definidas. Con 576 pedidos esperados por día, la probabilidad es despreciable, pero el simulador lo tiene que informar en lugar de dividir por cero.

### 6.3 Agregación entre réplicas

Cada métrica se calcula por réplica. Para cada configuración (nivel de demanda y NCH) se informa la media de las R réplicas y su intervalo de confianza del 95 %:

$$
\bar{x} \pm t_{0.975,\,R-1} \cdot \frac{s}{\sqrt{R}}
$$

donde x̄ es la media de las réplicas, s su desvío estándar y t el valor de la distribución t de Student.

---

## 7. Tabla de Eventos Independientes y Tabla de Eventos Futuros

### 7.1 Tabla de Eventos Independientes (TEI)

| Evento | Eventos futuros no condicionados (EFNC) | Eventos futuros condicionados (EFC) | Condición |
|---|---|---|---|
| TLL: llega un pedido | TLL | TLC(i) | Hay un chofer disponible (Ncd ≥ 1); i es el chofer asignado |
| TLC(i): el chofer i llega a buscar al cliente | TPS(i) | — | — |
| TPS(i): el chofer i termina el viaje | — | TLC(i) | Hay clientes en la cola (Ns ≥ 1); el chofer i toma al primero |

**Notas**

- **TLL siempre agenda la próxima llegada** mientras dure el día. Cuando la próxima llegada cae en TF o después, se le asigna HV y no entran más pedidos (vaciamiento, D-05).
- **El arrepentimiento no aparece en la TEI** porque no agenda ningún evento futuro: es una rama dentro de la rutina de TLL que solo actualiza contadores (sección 8.1).
- **TPS(i) figura como EFNC de TLC(i)** porque se agenda siempre: todo cliente recogido termina su viaje. En la v1.0 figuraba como EFC "incondicionado" (D-13).

### 7.2 Tabla de Eventos Futuros (TEF)

| Sigla | Qué representa | Estructura | Valor cuando no hay evento pendiente |
|---|---|---|---|
| TLL | Instante de la próxima llegada de un pedido | Un valor | HV (a partir del fin del día) |
| TLC(i) | Instante en que el chofer i llega a buscar a su cliente | Vector, i = 1 … NCH | HV |
| TPS(i) | Instante en que el chofer i termina su viaje | Vector, i = 1 … NCH | HV |

HV (*high value*) es un valor mayor que cualquier instante posible de la simulación: indica que no hay evento pendiente. El próximo evento es siempre el menor valor entre TLL, todos los TLC(i) y todos los TPS(i).

El estado de cada chofer se puede leer directamente de la TEF:

| TLC(i) | TPS(i) | Estado del chofer i |
|---|---|---|
| HV | HV | Disponible |
| Instante pendiente | HV | En camino |
| HV | Instante pendiente | Ocupado |
| Instante pendiente | Instante pendiente | Imposible (violaría el invariante 3) |

El orden de procesamiento cuando dos eventos ocurren en el mismo instante lo fija el SDD.

---

## 8. Descripción de los eventos

Esta sección describe en lenguaje natural qué pasa en cada evento. El SDD la traduce a rutinas paso a paso y el diagrama de flujo del informe se dibuja a partir de ambos (P-11).

### 8.0 Paso común a todos los eventos

1. Se busca el evento más próximo de la TEF.
2. Antes de procesarlo, se acumula lo que pasó desde el evento anterior, solo la parte que cae dentro de [0, TF]: se suman Ncd, Ncc y Nco multiplicados por el tiempo transcurrido a STO, STC y STV, respectivamente.
3. Se avanza el reloj T hasta el instante del evento.

### 8.1 TLL: llega un pedido

1. **Se crea el cliente.** Se registra t_llegada = T, se sortean TB, D, DEM y el residuo de la tarifa, y se calculan TV y TAR. Se suma 1 a NT.
2. **Se agenda la próxima llegada:** TLL = T + IA. Si ese instante es TF o posterior, TLL = HV.
3. **Si hay un chofer disponible** (Ncd ≥ 1):
   - se elige el chofer disponible de menor número, i;
   - se registra t_asignacion = T (espera en cola 0) y se suma 1 a NAT;
   - Ncd baja 1 y Ncc sube 1; CA(i) pasa a ser este cliente;
   - se agenda TLC(i) = T + TB.
4. **Si no hay choferes disponibles** (Ncd = 0), se calcula el tiempo de espera estimado que le muestra la app (D-02):

   $$
   TEE = \frac{(Ns + 1) \cdot E[S]}{NCH} + E[TB]
   $$

   - Si **TEE > U**, el cliente se arrepiente: se suma 1 a NARR, se suma su TAR a RECP y el cliente sale del sistema.
   - Si **TEE ≤ U**, el cliente entra al final de la cola y Ns sube 1.

**Por qué esta fórmula.** Con todos los choferes comprometidos, en promedio se libera uno cada E[S] / NCH minutos. El cliente que llega es el número Ns + 1 de la fila, y después de que se le asigna un chofer todavía falta, en promedio, el tiempo de búsqueda. La fórmula usa solo **medias conocidas**, nunca los tiempos ya sorteados de los viajes en curso: la app no conoce el futuro.

**Equivalencia con un umbral de cola.** La regla equivale a "el cliente se arrepiente si encuentra al menos k personas esperando", pero con un k que crece con la flota, porque la cola avanza más rápido cuantos más choferes hay. Con las FDP provisorias:

| NCH | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Se arrepiente si Ns ≥ | 1 | 2 | 2 | 3 | 3 | 4 | 4 | 5 | 5 | 6 | 6 | 7 | 7 | 8 |

> Con las FDP provisorias, E[S] ≈ 20,01 y U − E[TB] = 10. En los casos frontera el TEE da 15,01 minutos, apenas por encima del umbral. Por eso la comparación es estricta (TEE > U) y E[S] se usa sin redondear: un redondeo a 20,0 cambiaría la mitad de esta tabla.

### 8.2 TLC(i): el chofer i llega a buscar al cliente

1. Se registra t_recogida = T para el cliente CA(i) y se suma a SET su espera total, T − t_llegada.
2. Ncc baja 1 y Nco sube 1.
3. TLC(i) = HV y se agenda el fin del viaje: TPS(i) = T + TV del cliente.

### 8.3 TPS(i): el chofer i termina el viaje

1. Se suma a REC la tarifa del cliente CA(i), que sale del sistema. TPS(i) = HV.
2. **Si hay clientes en la cola** (Ns ≥ 1), el chofer i toma al primero:
   - Ns baja 1; se registra t_asignacion = T, se suma a SEC su espera en cola (T − t_llegada) y se suma 1 a NAT;
   - Nco baja 1 y Ncc sube 1; CA(i) pasa a ser este cliente;
   - se agenda TLC(i) = T + TB del cliente.
3. **Si la cola está vacía** (Ns = 0): Nco baja 1 y Ncd sube 1. El chofer queda disponible.

### 8.4 Inicio y fin de cada corrida

**Inicio (T = 0):**

- Ncd = NCH; Ncc, Nco y Ns en 0.
- Todos los contadores y acumuladores en 0.
- TLC(i) y TPS(i) en HV para todos los choferes.
- La primera llegada se agenda en TLL = IA (primer intervalo sorteado).
- E[S] y E[TB] ya están calculados (sección 4.4).

**Fin:** cuando TLL = HV y no queda ningún TLC(i) ni TPS(i) pendiente. En ese momento la cola está necesariamente vacía: si quedaran clientes esperando, no habría choferes disponibles (invariante 2) y por lo tanto habría eventos pendientes. Con el estado final se calculan las métricas de la sección 6.

---

## 9. Diseño experimental

### 9.1 Horizonte y réplicas

- Cada corrida simula **un día: TF = 1440 minutos**, con vaciamiento al final (D-05).
- Cada configuración se corre **R = 30 veces**, con semillas distintas. Cada réplica representa un día distinto.
- Con las 30 réplicas se obtiene la media y el intervalo de confianza de cada métrica (sección 6.3). Si los intervalos resultan demasiado anchos para distinguir flotas vecinas, se puede aumentar R después de una corrida piloto.

### 9.2 Números aleatorios

- Hay un generador independiente para cada variable aleatoria: IA, TB, D, DEM y el residuo de la tarifa.
- Cada réplica r tiene su semilla, y se usa **la misma** para todos los NCH y los tres niveles de demanda. Así, en la réplica r el cliente número k tiene siempre los mismos atributos, y las diferencias entre configuraciones se deben solo a la flota o a la demanda (D-09).
- Toda corrida es reproducible: con el mismo código y la misma semilla se obtienen exactamente los mismos resultados.

### 9.3 Niveles de demanda

| Nivel | Variación | Media de IA (min) | λ (pedidos/min) | Pedidos esperados por día | Carga a, con FDP provisorias |
|---|---|---|---|---|---|
| Bajo | −30 % | 3,571 | 0,28 | ≈ 403 | 5,60 |
| **Base** | — | **2,500** | **0,40** | **576** | **8,01** |
| Alto | +30 % | 1,923 | 0,52 | ≈ 749 | 10,41 |

- Una demanda un 30 % mayor significa λ × 1,3, o sea una media de IA de 2,5 / 1,3. No es lo mismo que multiplicar la media por 0,7.
- La **carga** a = λ × E[S] es la cantidad media de choferes que la demanda mantiene ocupados (se mide en Erlangs). Con menos choferes que la carga, la capacidad media no alcanza para la demanda media.

### 9.4 Flotas de referencia

$$
a = \lambda_{base} \cdot E[S] \qquad \text{actual} = \lceil a \rceil \qquad \text{peor} = \lceil a \rceil - 1
$$

| Flota | Regla | Con FDP provisorias | Utilización (a / NCH) |
|---|---|---|---|
| Actual | ⌈a⌉: la menor flota cuya capacidad media cubre la demanda media | 9 | 0,89 |
| Peor | ⌈a⌉ − 1: la mayor flota con capacidad media por debajo de la demanda media | 8 | 1,00 |

- Se calculan **antes de simular**, solo a partir de las FDP y siempre con la demanda base: son las flotas de hoy, aunque después se analice qué pasa si la demanda cambia.
- Se recalculan solas al cargar las FDP definitivas.
- Si ⌈a⌉ = 1, no existe una flota peor válida y se informan solo la actual y la mejor.
- La justificación está en D-07.

### 9.5 Rango de flotas a simular

Se usa un rango común para los tres niveles de demanda, de modo que los gráficos tengan el mismo eje horizontal:

- **Límite inferior:** max(1, ⌈a del nivel bajo⌉ − 2). Muestra una falta de choferes marcada incluso con poca demanda.
- **Límite superior:** ⌈a del nivel alto⌉ + 6. Muestra la zona de sobreoferta (mucho ocio, mejora casi nula) incluso con mucha demanda.

Con las FDP provisorias el rango va de 4 a 17 choferes. Por construcción, incluye siempre a la flota actual y a la peor.

### 9.6 Volumen de corridas

14 flotas × 3 niveles de demanda × 30 réplicas = **1260 corridas**, con unos 1700 pedidos por réplica sumando los tres niveles. Es un volumen chico: no hace falta optimizar el rendimiento del simulador.

### 9.7 Verificación del simulador

El SDD define las pruebas. Como mínimo:

- **Casos deterministas:** con FDP constantes, el resultado se puede calcular a mano y comparar.
- **Invariantes:** los de la sección 5.7 se verifican después de cada evento.
- **Control de números aleatorios comunes:** en una misma réplica y nivel de demanda, REC + RECP tiene que dar lo mismo para todas las flotas.
- **Contraste analítico:** sin arrepentimiento y con tiempos de servicio exponenciales, la espera en cola tiene que acercarse a la de la fórmula de Erlang C.

---

## 10. Criterio de decisión y escenarios

### 10.1 Criterio

**Mejor flota (NCH\*) = la menor NCH que cumple a la vez:**

- espera total media PET ≤ X = 10 minutos, y
- porcentaje de abandono PA ≤ Y = 5 %.

Ambas condiciones se evalúan sobre la media de las 30 réplicas.

- **Por qué la menor:** cualquier flota más grande también cumple, pero con más ocio. La menor que cumple es el punto de equilibrio entre servicio y ociosidad.
- **Por qué las dos condiciones:** ver 6.2.
- **Margen estrecho:** si el intervalo de confianza de PET o de PA contiene al umbral, la flota se marca "en el límite". En ese caso se recomienda mirar también la flota siguiente.
- X e Y se configuran en el módulo de análisis (D-10): cambiarlos no requiere volver a simular.

### 10.2 Escenarios

Los tres escenarios que pide la consigna son tres flotas evaluadas con la demanda base (D-06):

| Escenario | NCH | Qué representa | Con FDP provisorias |
|---|---|---|---|
| Peor | ⌈a⌉ − 1 | Una flota por debajo de la demanda media: sin arrepentimiento, la cola crecería sin límite | 8 |
| Actual | ⌈a⌉ | La flota dimensionada "por el promedio" (sección 1.3) | 9 |
| Mejor | NCH\* | La menor flota que cumple el criterio | Resultado de la simulación |

### 10.3 Análisis de sensibilidad

Para cada nivel de demanda (bajo, base y alto) se informa:

- la mejor flota NCH\* para ese nivel;
- cómo se comporta la flota actual con ese nivel: espera, abandono, ocio y recaudación.

El nivel alto se puede leer como una aproximación a una hora pico (S-03).

### 10.4 Forma de las conclusiones

- **Escenario más conveniente:** "con la demanda actual conviene operar con NCH\* choferes en lugar de ⌈a⌉: la espera total baja de A a B minutos y el abandono de C % a D %, a costa de que el ocio suba de E % a F %".
- **Peor escenario:** "con un chofer menos que la flota actual, el abandono llega a G % y se pierden H USD por día".
- **Sensibilidad:** "si la demanda sube un 30 %, hacen falta M choferes; con la flota actual, el abandono llegaría a J %".

### 10.5 Casos borde del criterio

| Situación | Qué significa | Qué hacer |
|---|---|---|
| Ninguna flota del rango cumple el criterio | El rango quedó corto o los umbrales son demasiado exigentes | Ampliar el rango hacia arriba y volver a correr |
| NCH\* coincide con el límite superior del rango | No se puede ver la zona de sobreoferta | Ampliar el rango |
| NCH\* es igual o menor que la flota actual | La flota actual ya cumple, o hasta sobra | Es una conclusión válida: recomendar mantener o reducir |
| NCH\* es igual o menor que la flota peor | El criterio es demasiado laxo: acepta una flota por debajo de la demanda media | Revisar X e Y |

### 10.6 Presentación de resultados

El módulo de análisis genera, con una curva por nivel de demanda y el eje horizontal en NCH:

- PET y PA con sus intervalos de confianza y una línea en cada umbral;
- PTO, para mostrar el costo en ociosidad de cada flota;
- REC y RECP, para mostrar cuánto se recupera al agregar choferes.

---

## 11. Registro de decisiones

Cada decisión indica el problema que resuelve, qué alternativas se evaluaron, qué se eligió y qué consecuencias trae.

### D-01 · La demanda es un supuesto, no una FDP ajustada al dataset

- **Contexto:** la consigna pide usar las FDP del TP4, pero el dataset registra cotizaciones consultadas por un script, no viajes (sección 4.1). El intervalo calculado con los timestamps mide el ritmo del script: daría un pedido cada pocos segundos.
- **Alternativas consideradas:**
  - Ajustar el intervalo con los timestamps del dataset. Descartada: mide el script, no la demanda.
  - Derivar la tasa del informe del Departamento de Servicios Públicos de Massachusetts (DPU) con factores de participación de mercado, fracción de la zona y franja horaria. Descartada como cálculo exacto, porque dos de esos factores no tienen fuente. Se usa solo para verificar el orden de magnitud.
  - Usar viajes reales de Nueva York o Chicago. Es otra ciudad; queda como validación opcional de la forma exponencial y del perfil horario.
- **Decisión:** intervalos exponenciales con media 2,5 minutos (λ = 0,4 pedidos por minuto). El DPU informa unos 42,2 millones de viajes en Boston en 2018, unos 80 por minuto en toda la ciudad; con valores ilustrativos de participación y zona se obtiene un pedido cada 2,1 minutos, del mismo orden.
- **Consecuencias:** la incertidumbre del supuesto se cubre con el análisis de sensibilidad de ±30 % (D-06). Hay que confirmar con la cátedra que acepta la demanda como supuesto (P-01).

### D-02 · Arrepentimiento según el tiempo estimado de espera

- **Contexto:** sin abandono, todo cliente termina viajando aunque espere mucho. Eso genera dos problemas. Primero, la recaudación es la misma con cualquier NCH, así que no sirve para decidir. Segundo, con una flota menor o igual que la carga, la cola crece sin límite y la espera media depende solo del largo de la corrida.
- **Alternativas consideradas:**
  - Sin arrepentimiento. Descartada por lo anterior.
  - Arrepentimiento con un umbral fijo de cola (por ejemplo, "si hay más de 5 esperando, se va"), el patrón habitual de la cátedra. Descartada como regla directa: el cliente de una app no ve la cola sino un tiempo estimado, y la misma cola implica esperas muy distintas según la flota. Cinco personas esperando con 15 choferes es poco tiempo; con 9 es mucho.
  - Costo por chofer en lugar de abandono. Descartada: en Lyft el chofer cobra por viaje, un chofer ocioso no le cuesta a la plataforma, y ese costo ya lo refleja el porcentaje de tiempo ocioso.
  - Paciencia individual con abandono desde la cola. Requiere un evento nuevo y sacar clientes del medio de la cola; queda fuera de alcance (S-07).
  - Probabilidad de arrepentimiento creciente con la espera. Agrega supuestos que no tienen datos que los respalden.
- **Decisión:** al llegar, si no hay choferes disponibles, se calcula el tiempo de espera estimado TEE = (Ns + 1) × E[S] / NCH + E[TB]. Si TEE > U, con U = 15 minutos, el cliente se arrepiente. La justificación de la fórmula está en la sección 8.1. Es exacta si los tiempos de servicio fueran exponenciales, y una aproximación razonable en este caso, del mismo tipo que usa una app real.
- **Consecuencias:**
  - Sigue siendo una condición en TLL evaluada con variables de estado, como en los modelos de la cátedra. Equivale a un umbral de cola que crece con la flota (tabla de la sección 8.1).
  - La recaudación pasa a depender de NCH.
  - El sistema es siempre estable: la saturación aparece como abandono masivo, no como una cola infinita.
  - U es un supuesto sin datos; conviene un análisis de sensibilidad (P-10).

### D-03 · Criterio de decisión: espera total y abandono

- **Contexto:** "minimizar la espera sin disparar la ociosidad" combina dos objetivos que dependen de NCH en sentidos opuestos. Sin una regla que los combine, no existe un óptimo.
- **Alternativas consideradas:**
  - Espera en cola media ≤ 5 minutos. Es equivalente en promedio, porque la espera total es la espera en cola más el tiempo de búsqueda, que promedia 5 minutos. Es menos intuitiva para explicar.
  - Espera total media ≤ 5 minutos. Inalcanzable: la búsqueda sola ya promedia 5 minutos, así que ninguna flota la cumpliría de forma confiable.
  - Solo espera, sin mirar el abandono. Sesgada (sección 6.2).
  - Función de costo que pondere espera y cantidad de choferes. Requiere costos que no tienen fuente.
- **Decisión:** la mejor flota es la menor que cumple a la vez espera total media ≤ 10 minutos y abandono ≤ 5 %, sobre la media de las réplicas (sección 10.1).
- **Consecuencias:** la menor flota que cumple minimiza el ocio sujeto al nivel de servicio. El ocio no entra en el criterio, pero se informa para mostrar el costo de cada flota. X e Y son parámetros del análisis, no del modelo (D-10).

### D-04 · Medición del tiempo ocioso

- **Contexto:** la v1.0 usaba una sola variable, `tiempo_inicio_ocio`, para toda la flota. Con varios choferes libres a la vez, cada fin de viaje la sobrescribe. Por ejemplo: el chofer A queda libre en el minuto 10 y el B en el 12, que borra el 10; en el minuto 15 se asigna A y se suman 3 minutos de ocio en lugar de 5. Además, se perdía el ocio del inicio (en t = 0 todos están libres) y el del final.
- **Alternativas consideradas:**
  - Un vector de inicio de ocio por chofer, el esquema clásico de la cátedra. Es correcto, pero obliga a inicializar y cerrar a mano cada chofer.
  - Incluir el tiempo en camino como ocio. Descartada: el chofer que va a buscar a un cliente está trabajando.
- **Decisión:** antes de cada evento se suma Ncd × (tiempo transcurrido desde el evento anterior) al acumulador STO, en chofer-minutos. Solo cuenta como ocioso el chofer disponible. Se acumula dentro de [0, TF].
- **Consecuencias:** el cálculo es exacto, no depende de qué chofer se asigna y resuelve solo los bordes. Con el mismo método se miden el tiempo en camino (STC) y el ocupado (STV); los tres suman NCH × TF, lo que sirve de control.

### D-05 · Horizonte de un día, 30 réplicas y vaciamiento

- **Contexto:** la tasa de demanda es un promedio diario derivado de un total anual. Había que decidir cuánto tiempo simular y qué hacer con los clientes que quedan en el sistema al terminar.
- **Alternativas consideradas:**
  - Simular un año continuo. Con demanda constante es el mismo día promedio repetido 365 veces: no aporta picos y da un solo número, sin margen de error.
  - Simular un turno de 8 horas. Válido, pero las métricas de negocio se piensan por día.
  - Cortar en TF sin vaciamiento. Los clientes que siguen esperando quedan fuera del promedio, justo en las flotas más chicas, que son las que más esperan: sesgo de supervivencia.
- **Decisión:** TF = 1440 minutos, R = 30 réplicas independientes por configuración, y vaciamiento: a partir de TF no entran pedidos y se sigue procesando hasta terminar todos los viajes y vaciar la cola.
- **Consecuencias:** cada métrica tiene media e intervalo de confianza. El ocio se mide solo en [0, TF] (sección 6.2). R se puede revisar después de una corrida piloto.

### D-06 · Los escenarios son flotas; la demanda es un análisis de sensibilidad

- **Contexto:** la consigna pide analizar escenarios actual, mejor y peor, y concluir cuál es el más conveniente. "Conveniente" implica una elección, y lo que la empresa elige es la flota (variable de control), no la demanda (dato).
- **Alternativa considerada:** que los escenarios sean niveles de demanda (base, +30 % y −30 %). Descartada: la pregunta "¿cuál conviene?" no tiene una respuesta útil, porque la demanda no se elige.
- **Decisión:** los tres escenarios son flotas evaluadas con la demanda base (sección 10.2). La variación de ±30 % se presenta como análisis de sensibilidad (sección 10.3).
- **Consecuencias:** se corren las mismas simulaciones que con el enfoque alternativo; cambian la presentación y la conclusión, que queda alineada con la consigna. Conviene confirmarlo con la cátedra (P-02).

### D-07 · Flotas de referencia: actual y peor

- **Contexto:** no hay datos sobre la flota real de la zona, y hacen falta un escenario actual y uno peor que no sean números elegidos a mano.
- **Alternativas consideradas:**
  - Elegir los números a mano. Descartada: no se pueden justificar.
  - Definir la flota actual a partir de los resultados de la simulación. Descartada: es circular.
  - Definir el peor como el extremo inferior del rango simulado. Descartada: dependería de dónde se fije el rango.
- **Decisión:**
  - Flota actual = ⌈a⌉, con a = λ base × E[S]: la menor flota cuya capacidad media cubre la demanda media. Representa el error clásico de dimensionar por el promedio (sección 1.3).
  - Flota peor = ⌈a⌉ − 1: la mayor flota con capacidad media por debajo de la demanda media. Sin arrepentimiento sería inestable; con arrepentimiento, muestra el abandono masivo.
  - Ambas se calculan antes de simular, con E[S] exacto y con la demanda base.
- **Consecuencias:** con las FDP provisorias, actual = 9 y peor = 8. Se recalculan solas con las FDP definitivas. La carga está muy cerca de un entero con las FDP provisorias, así que el resultado es sensible a la demora por tráfico (sección 4.4).

### D-08 · TEF con vectores por chofer y HV

- **Contexto:** hay que representar los eventos pendientes y encontrar el próximo.
- **Alternativa considerada:** una cola de prioridad (`heapq`). Descartada: con unos 576 pedidos por día y a lo sumo 17 choferes, recorrer los vectores para encontrar el mínimo es instantáneo, y la cola de prioridad rompe la correspondencia uno a uno con el diagrama de flujo de la cátedra.
- **Decisión:** TLL es un valor único; TLC(i) y TPS(i) son vectores de NCH posiciones; HV indica que no hay evento pendiente.
- **Consecuencias:** el estado de cada chofer se lee de la TEF (sección 7.2). Como un chofer nunca tiene TLC y TPS pendientes a la vez, el SDD puede implementarlos con un único vector sin cambiar el modelo.

### D-09 · Números aleatorios comunes y reproducibilidad

- **Contexto:** con un único generador global, como en las FDP provisorias (`numpy.random.*`), el orden en que se consumen los números cambia con NCH. Cada flota vería un día distinto, y la comparación mezclaría el efecto de la flota con el del azar.
- **Decisión:**
  - Un generador independiente por variable aleatoria.
  - Cada réplica tiene su semilla, la misma para todas las flotas y los tres niveles de demanda.
  - Todos los atributos del cliente se sortean al llegar, aunque después se arrepienta. Incluye TB: como en este modelo no depende del chofer (S-05), puede tratarse como atributo del cliente.
  - IA = (media del nivel de demanda) × E, con E exponencial de media 1. Así, en los tres niveles el cliente número k tiene los mismos atributos: solo llega antes o después.
- **Consecuencias:** dentro de una réplica, las diferencias entre configuraciones se deben solo a la flota o a la demanda. Todo es reproducible. Sirve de control: REC + RECP es igual para todas las flotas de una misma réplica y nivel de demanda.

### D-10 · Motor de simulación y análisis separados

- **Contexto:** los umbrales X e Y del criterio tienen que poder cambiarse.
- **Alternativa considerada:** aplicar el criterio a mano al armar el informe. Descartada: cualquier cambio obliga a rehacer cuentas y es fácil equivocarse.
- **Decisión:** el motor corre cada combinación de nivel de demanda, NCH y réplica, y guarda las métricas crudas; no conoce el criterio. El módulo de análisis lee esas métricas, aplica el criterio con X e Y configurables y genera tablas y gráficos.
- **Consecuencias:** cambiar X o Y no requiere volver a simular.

### D-11 · Nomenclatura unificada

- **Contexto:** en la v1.0 y en las FDP provisorias, TLL y TLC se usaban a la vez como nombres de duraciones aleatorias y como instantes de eventos.
- **Decisión:** las FDP se llaman IA, TB, D, DEM, TV y TAR; los eventos, TLL, TLC(i) y TPS(i).
- **Consecuencias:** cada sigla tiene un único significado en todos los documentos y en el código.

### D-12 · Se mantiene el evento TLC

- **Contexto:** TLC solo pasa a un chofer de "en camino" a "ocupado". Se podría eliminar y agendar directamente el fin del viaje al asignar el chofer (T + TB + TV).
- **Decisión:** mantener TLC como evento.
- **Consecuencias:** permite registrar el instante de recogida (y con él la espera total, que es la del criterio), observar cuántos choferes están en camino y, en el futuro, modelar cancelaciones mientras el chofer va en camino.

### D-13 · TPS(i) es un evento futuro no condicionado de TLC(i)

- **Contexto:** en la v1.0, TPS figuraba como evento condicionado de TLC, con la aclaración "incondicionado".
- **Decisión:** se ubica como EFNC, porque se agenda siempre.
- **Consecuencias:** conviene confirmar la convención con la cátedra (P-02).

### D-14 · Origen de cada FDP

- **Contexto:** el dataset no tiene todas las variables y algunas de las que tiene no sirven (sección 4.1).
- **Alternativas consideradas:**
  - Tarifa uniforme e independiente de la distancia, como en las FDP provisorias. Descartada: no refleja que los viajes largos cuestan más.
  - Una sola distribución de tarifa que mezcle los seis productos y el recargo dinámico. Descartada: mezcla poblaciones distintas.
  - Ajustarle una FDP a la duración del viaje. Descartada: el dataset no tiene duraciones, y ajustar sobre datos generados por nosotros no aporta información.
- **Decisión:** del dataset salen solo la distancia y la tarifa (producto estándar, modelada como base + k × distancia + residuo). El tiempo de viaje se calcula desde la distancia sorteada. La búsqueda y la demora por tráfico son supuestos.
- **Consecuencias:** la tarifa y el tiempo de viaje quedan correlacionados con la distancia, como en la realidad.

---

## 12. Pendientes y limitaciones

### 12.1 Pendientes

| ID | Pendiente | Afecta a |
|---|---|---|
| P-01 | Confirmar con la cátedra que acepta la demanda como supuesto, ya que la consigna pide FDPs del TP4. | D-01 |
| P-02 | Confirmar con la cátedra el encuadre de los escenarios y la notación de la TEI. | D-06, D-13 |
| P-03 | Ajustar la FDP de distancia (Lyft, deduplicado). | D, E[S], flotas de referencia |
| P-04 | Ajustar el modelo de tarifa y definir qué pasa si el residuo da una tarifa menor que la mínima observada en el dataset. | TAR, REC |
| P-05 | Definir la FDP de la demora por tráfico, con soporte positivo. | TV, E[S], flotas de referencia |
| P-06 | Reemplazar la FDP provisoria de búsqueda (normal recortada) por gamma o lognormal con media 5 y desvío 1,5. | TB |
| P-07 | Validar la velocidad de 13 mi/h con distancia y duración de una misma fuente: el dataset de Chicago de noviembre y diciembre de 2018, o el DPU. | TV |
| P-08 | Actualizar [`fdps-mock.md`](fdps-mock.md) con generadores por variable con semilla y las FDP corregidas. | D-09 |
| P-09 | Informar a la cátedra los cambios respecto del análisis previo (sección 13). | — |
| P-10 | Opcional: analizar la sensibilidad de los resultados al umbral U (por ejemplo, con 10 y 20 minutos). | D-02 |
| P-11 | Dibujar el diagrama de flujo con el formato de la cátedra, a partir de la sección 8 y del SDD. | Informe |
| P-12 | Redactar el SDD. | Implementación |

### 12.2 Limitaciones principales

- **El NCH recomendado es una cota inferior.** El tiempo de búsqueda no empeora cuando quedan pocos choferes libres (S-05), así que el modelo es optimista con flotas chicas.
- **No hay horas pico.** La demanda es constante (S-03). El nivel alto de demanda es solo una aproximación.
- **El abandono simulado es un mínimo.** Los clientes solo pueden arrepentirse al pedir (S-07).
- **NCH son choferes conectados al mismo tiempo** (S-02), no choferes registrados ni turnos.
- **La demanda es un supuesto** validado solo en orden de magnitud (D-01).

---

## 13. Cambios respecto de la v1.0

| Tema | v1.0 | v2.0 | Motivo |
|---|---|---|---|
| Intervalo entre pedidos | Calculado con los timestamps del dataset | Supuesto: exponencial con media 2,5 min | El dataset son cotizaciones (D-01) |
| Tarifa | Columna `price`; uniforme en el mock | base + k × distancia + residuo, producto estándar | Correlación con la distancia (D-14) |
| Duración del viaje | "Se infiere" con un desvío | TV = D × 60 / v + DEM, con DEM de soporte positivo | Evitar picos artificiales (D-14, P-05) |
| Arrepentimiento | No existía | Al pedir, según el tiempo estimado, con U = 15 min | Sin abandono, la recaudación era constante y el sistema podía ser inestable (D-02) |
| Espera | Una sola, hasta la asignación | Espera en cola y espera total; el criterio usa la total | El cliente espera hasta que llega el auto (D-03) |
| Clientes atendidos | "Al iniciar su viaje" (ambiguo) | Al recibir un chofer, incluidos los que no esperaron | Evitar un promedio sesgado (sección 6.2) |
| Tiempo ocioso | Una variable para toda la flota | Área bajo Ncd en [0, TF] | Se sobrescribía y perdía los bordes (D-04) |
| Denominador del ocio | "Tiempo total simulado × NCH" | NCH × TF | Excluir el vaciamiento (D-05) |
| Recaudación | Indicador de decisión | Informativa; depende de NCH por el abandono; se agrega la recaudación perdida | Sin abandono era igual para cualquier flota (D-02) |
| Criterio de decisión | No definido | Menor NCH con espera total ≤ 10 min y abandono ≤ 5 % | D-03 |
| Escenarios | No definidos | Peor, actual y mejor sobre NCH, más sensibilidad de ±30 % en la demanda | D-06, D-07 |
| Horizonte | No definido | Un día, 30 réplicas y vaciamiento | D-05 |
| TEF | TLL, TLC y TPS sin índice | TLL, TLC(i) y TPS(i), con HV | D-08 |
| TEI | TPS como evento condicionado "incondicionado" de TLC | TPS(i) como EFNC de TLC(i); el arrepentimiento no figura porque no agenda eventos | D-13, sección 7.1 |
| Nombres | TLL y TLC también para duraciones | IA, TB, D, DEM, TV y TAR para las FDP | D-11 |
| Números aleatorios | No definido | Generadores por variable y semillas comunes | D-09 |

---

## 14. Glosario

| Término | Significado |
|---|---|
| Arrepentimiento | Abandono de un cliente al momento de pedir, cuando el tiempo estimado de espera supera su tolerancia. |
| Carga (a) | Cantidad media de choferes que la demanda mantiene ocupados: λ × E[S]. Se mide en Erlangs. |
| Chofer-minuto | Un chofer durante un minuto. Diez choferes libres durante tres minutos suman 30 chofer-minutos de ocio. |
| DPU | Departamento de Servicios Públicos de Massachusetts. Publica informes anuales de viajes de Uber y Lyft. |
| EFC | Evento futuro condicionado: se agenda solo si se cumple una condición. |
| EFNC | Evento futuro no condicionado: se agenda siempre que ocurre el evento que lo genera. |
| FDP | Función de distribución de probabilidad. |
| HV | *High value*: valor mayor que cualquier instante de la simulación; indica que no hay evento pendiente. |
| Intervalo de confianza (IC) | Rango que, con un 95 % de confianza, contiene al valor medio real de una métrica. |
| MaaS | *Mobility as a Service*: movilidad como servicio. |
| Números aleatorios comunes | Técnica que usa los mismos números aleatorios para comparar configuraciones, de modo que las diferencias se deban a la configuración y no al azar. |
| Réplica | Una corrida de un día con su propia semilla. |
| Semilla | Valor inicial del generador de números aleatorios. Con la misma semilla se obtiene siempre la misma secuencia. |
| TEE | Tiempo de espera estimado que la app le muestra al cliente. |
| TEF | Tabla de Eventos Futuros: los eventos pendientes y sus instantes. |
| TEI | Tabla de Eventos Independientes: qué eventos futuros genera cada evento y bajo qué condición. |
| Tiempo de servicio (S) | Tiempo que un chofer queda comprometido con un cliente: búsqueda más viaje. |
| Utilización | Fracción de la capacidad de la flota que usa la demanda: a / NCH. |
| Vaciamiento | Política de cierre: a partir de TF no entran pedidos, pero se terminan los viajes en curso y se atiende a los que ya esperaban. |
