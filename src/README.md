# src/

Código del simulador. **Vacío a propósito**: no se escribe código hasta que el SDD ([`docs/sdd.md`](../docs/sdd.md)) esté aprobado.

Estructura prevista (se confirma en el SDD):

- **Motor de simulación:** procesa los eventos TLL, TLC y TPS y guarda métricas crudas por corrida. No conoce el criterio de decisión.
- **FDPs:** generadores intercambiables (mock en la V1, ajustadas del TP4 en la V2), sin tocar el motor.
- **Análisis:** lee las métricas crudas, aplica el criterio de decisión (umbrales configurables) y arma tablas y gráficos.
