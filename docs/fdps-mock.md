> **⚠️ Desactualizado.** FDPs provisorias de la V1 (MVP). Pendiente de corregir junto con el SDD:
> - **Búsqueda:** pasar de normal recortada (`max(1.0, ...)`, deja un pico en 1) a gamma o lognormal con media 5 y desvío 1,5.
> - **Demora por tráfico:** `max(0, normal)` deja un pico en 0; definir una distribución con soporte positivo.
> - **Tarifa:** pasar de uniforme a `base + k × distancia + residuo`.
> - **Generación:** usar un generador por variable con semilla, no la API global `numpy.random.*`.
>
> Ver [`fdps-decisiones.pdf`](fdps-decisiones.pdf) y el registro de decisiones en [`modelo.md`](modelo.md).

# Definición de Funciones de Distribución de Probabilidad (FDPs) - V1.0 (Placeholders)

Nota para el agente de IA: El equipo de datos actualmente está limpiando el dataset original de Boston. Para la Fase 1 del desarrollo (MVP), el motor de simulación debe utilizar las siguientes distribuciones "mockeadas" utilizando la librería `numpy.random`. Estas funciones serán reemplazadas por los parámetros reales en la V2.

1. Intervalo de Arribo (TLL):
- Distribución: Exponencial
- Implementación Python: `numpy.random.exponential(scale=2.5)` # Media de 2.5 minutos entre pedidos.

2. Tiempo de Búsqueda / Despacho (TLC):
- Distribución: Normal (truncada a positiva)
- Implementación Python: `max(1.0, numpy.random.normal(loc=5.0, scale=1.5))` # Media de 5 min, desvío 1.5.

3. Distancia Recorrida (millas):
- Distribución: Lognormal (placeholder ideal para distancias, ya que no admite negativos).
- Implementación Python: `numpy.random.lognormal(mean=1.0, sigma=0.5)` 

4. Duración del Viaje / Tiempo de Servicio (minutos):
- Lógica de cálculo: Se infiere a partir de la Distancia Recorrida asumiendo una velocidad promedio en Boston de 21 km/h (aprox. 13 millas/h), sumando una pequeña FDP de desviación para simular demoras por tráfico.
- Implementación Python: `(distancia_generada / (13.0 / 60.0)) + max(0, numpy.random.normal(loc=0, scale=2.0))`

5. Tarifa (USD):
- Distribución: Uniforme (se correlacionará con la distancia en V2).
- Implementación Python: `numpy.random.uniform(low=5.0, high=25.0)`
