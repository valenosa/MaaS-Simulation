# tests/

Pruebas automáticas del simulador. Se definen en el plan de verificación del SDD ([`docs/sdd.md`](../docs/sdd.md)):

- **Casos deterministas:** FDPs constantes con resultado calculable a mano.
- **Casos borde:** NCH = 1, NCH muy grande, cola vacía al terminar, vaciamiento.
- **Invariantes:** se verifican después de cada evento (por ejemplo, disponibles + en camino + ocupados = NCH).
- **Cordura analítica:** contraste contra resultados teóricos de colas (Erlang C).
