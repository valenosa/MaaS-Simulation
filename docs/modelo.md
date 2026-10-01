> **⚠️ Versión 1.0 (la presentada en el análisis previo).** Este documento será reemplazado por la v2.0, que corrige problemas detectados en la revisión (contabilidad del ocio, definición de espera, arrepentimiento, criterio de decisión). Se conserva acá para que el historial de git muestre exactamente qué cambió entre versiones.

# **Análisis de cantidad óptima de choferes en una plataforma MaaS mediante técnicas de simulación evento a evento**

Este documento detalla el marco lógico y la estructura de variables para el modelo de simulación orientado a optimizar la flota de vehículos en una plataforma de movilidad como servicio (MaaS). El enfoque se centra en la eficiencia operativa y la satisfacción del usuario mediante la gestión de la oferta de choferes.

# **1\. Variables y FDPs (Trabajo Práctico 4\)**

El modelo se nutre de datos empíricos para definir el comportamiento del sistema mediante Funciones de Distribución de Probabilidad (FDP):

* **Intervalo de Arribo (IA) de solicitudes (minutos):** Esta variable determina la frecuencia con la que ingresan pedidos al sistema. Se calcula a partir de la diferencia de tiempo entre timestamps consecutivos de los viajes registrados en el dataset.  
* **Tiempo de Búsqueda / Despacho (minutos):** Tiempo que demora un chofer desde que se le asigna el viaje hasta que llega a la ubicación del cliente. Se modelará asumiendo una distribución con media y desviación estándar representativas del tráfico local.   
* **Distancia recorrida (millas):** Variable extraída directamente de la columna *distance* del dataset original, fundamental para determinar la duración del compromiso del recurso.  
* **Duración del viaje / Tiempo de Servicio (minutos):** Se infiere mediante el cálculo de la distancia sobre una velocidad promedio estimada para la ciudad de Boston (\~21 km/h). Para añadir realismo, se aplica una desviación estándar que genera variabilidad en los tiempos de servicio finales.  
* **Tarifa (USD):** Obtenida de la columna *price*. Se utiliza como un atributo de la entidad pasajero para fines de análisis financiero y rentabilidad, pero no actúa como un encadenador de eventos dentro del motor de simulación.

# **2\. Clasificación de Variables**

## **Exógenas**

Se dividen en datos de entrada y parámetros de control que el analista puede modificar para observar diferentes resultados.

* **Datos:** Intervalo entre arribos de solicitudes (minutos), Distancia recorrida (millas), Duración del viaje (minutos) y Tarifa (USD).  
* **Control (NCH):** Cantidad de choferes en la flota. Representa la variable de decisión principal para encontrar el punto de equilibrio óptimo.

## **Endógenas**

Estas variables describen el comportamiento interno del sistema y los resultados obtenidos tras la ejecución de los escenarios.

* **Estado:**  
  * **Ncd:** Cantidad de choferes disponibles.  
  * **Ncc:** Cantidad de choferes en camino (en tránsito hacia el cliente).  
  * **Nco:** Cantidad de choferes ocupados.  
  * **Ns:** Cantidad de clientes en espera (cola).  
  * *Nota:* En todo momento se mantiene la identidad **Ncd \+ Ncc \+ Nco \= NCH**. Los cambios en estas variables son instantáneos y ocurren ante la ejecución de los eventos.  
* **Variables Auxiliares**  
  * **tiempo\_llegada\_cliente:** Atributo de la entidad (pasajero) que guarda el valor del reloj en el instante exacto en que ingresa a la cola.  
  * **tiempo\_espera\_acumulado:** Acumulador global que suma los tiempos de espera individuales de cada cliente que logra iniciar su viaje.  
  * **clientes\_atendidos:** Contador global que se incrementa en 1 cada vez que un cliente inicia su viaje.  
  * **recaudación\_acumulada:** Acumulador global (en USD) que suma la tarifa generada por cada cliente que finaliza su viaje.  
  * **tiempo\_inicio\_ocio:** Variable auxiliar que registra la marca de tiempo exacta (timestamp) cuando ocurre un Evento de Salida (TPS) y el chofer queda libre porque la cola está vacía.  
  * **tiempo\_ocioso\_acumulado:** Variable sumatoria global. Cuando ocurre un Evento de Llegada (TLL) y el sistema asigna un viaje a un chofer que estaba libre, se calcula el delta de tiempo (`T. Actual - tiempo_inicio_ocio`) y se suma a este acumulador.  
* **Resultado:**  
  * **Tiempo promedio de espera diario:** Refleja la calidad del servicio. Se calcula al final de la ejecución, dividiendo el `tiempo_espera_acumulado` por los `clientes_atendidos`. *(El tiempo de espera individual se obtiene restando el `tiempo llegada cliente` al timestamp en el momento en que se le asigna un chofer).*  
  * **Recaudación total diaria (USD):** Indicador financiero de la configuración de flota actual. Es directamente el valor final del acumulador `Recaudación_Acumulada` al terminar el tiempo de simulación.   
  * **Porcentaje de tiempo ocioso:** Proporción del tiempo en que los choferes no están realizando viajes, útil para identificar sobreoferta. Se calcula dividiendo el `Tiempo_Ocioso_Acumulado` por el (`Tiempo Total Simulado × NCH`), multiplicado por 100\. 

# **3\. Clasificación de Eventos**

La dinámica del sistema está gobernada por eventos discretos que alteran el estado de las variables.

## **Tabla de Eventos Independientes (TEI)**

| Evento | Evento Futuro No Condicionado (EFNC) | Evento Futuro Condicionado (EFC) | Condición |
| :---- | :---- | :---- | :---- |
| Llegada de una solicitud (TLL) | Llegada de una solicitud (TLL) | Llegada de chofer (TLC) | Si hay choferes disponibles (Ncd \>= 1\) |
| Llegada de chofer(TLC)  | \- | Salida / Fin de viaje (TPS) | (Incondicionado, todo chofer que sube a un pasajero desemboca en un eventual fin de viaje) |
| Salida / Fin de viaje (TPS) | \- | Llegada de chofer(TLC) | Si hay clientes en espera (Ns\>=1) |

## **Tabla de Eventos Futuros (TEF)**

Esta tabla representa el cronograma de eventos que el motor de simulación debe procesar cronológicamente.

| Sigla | Evento | Descripción |
| :---- | :---- | :---- |
| **TLL** | Llegada | Tiempo de próxima llegada de solicitud de viaje. |
| **TLC** | Llegada chofer | Tiempo de próxima llegada de chofer. |
| **TPS** | Salida | Tiempo de próxima salida o finalización del viaje actual. |
