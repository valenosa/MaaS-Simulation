"""Estructuras de datos de una corrida.

Implementa SDD §4.1 a §4.7, con T-04, T-05 y T-07. Los nombres son los de §4.8.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

# Sin evento pendiente (T-04).
HV = math.inf


@dataclass(slots=True)
class Cliente:
    """Entidad temporal: nace en TLL y sale al arrepentirse o al terminar su viaje (§4.2)."""

    id: int                         # número de pedido en la corrida: el valor de NT al llegar
    t_llegada: float
    tb: float
    d: float
    dem: float
    tv: float
    tar: float
    t_asignacion: float | None = None
    t_recogida: float | None = None


@dataclass(frozen=True)
class ParametrosCorrida:
    """Parámetros que no cambian durante la corrida (§4.6). NCH y el nivel van aparte."""

    umbral_tolerancia_min: float    # U (puede ser infinito)
    horizonte_min: float            # TF
    e_s: float                      # E[S], para el TEE
    e_tb: float                     # E[TB], para el TEE
    verificar_invariantes: bool


@dataclass(slots=True)
class EstadoCorrida:
    """Estado global de una corrida (§4.5).

    Los choferes se numeran de 1 a NCH, como en el modelo; los vectores usan la posición
    i − 1 (§0.4). El estado de cada chofer se deduce de TLC y TPS (§4.3, T-05) y Ns es la
    longitud de la cola (§4.4, T-07).
    """

    nch: int
    t: float = 0.0
    t_anterior: float = 0.0
    tll: float = HV
    tlc: list[float] = field(default_factory=list)
    tps: list[float] = field(default_factory=list)
    ca: list[Cliente | None] = field(default_factory=list)
    ncd: int = 0
    ncc: int = 0
    nco: int = 0
    cola: deque[Cliente] = field(default_factory=deque)
    nt: int = 0
    narr: int = 0
    nat: int = 0
    suma_espera_cola: float = 0.0   # SEC
    suma_espera_total: float = 0.0  # SET
    rec: float = 0.0
    recp: float = 0.0
    sto: float = 0.0
    stc: float = 0.0
    stv: float = 0.0
    n_eventos: int = 0
    ns_max: int = 0

    @classmethod
    def inicial(cls, nch: int) -> EstadoCorrida:
        """Estado al inicio de la corrida (§6.2, modelo §8.4). TLL se agenda aparte."""
        return cls(nch=nch, tlc=[HV] * nch, tps=[HV] * nch, ca=[None] * nch, ncd=nch)

    @property
    def ns(self) -> int:
        return len(self.cola)


@dataclass(frozen=True)
class ResultadoCorrida:
    """Resultado de una corrida (§4.7). La réplica la agrega el orquestador (§8.3)."""

    nivel: str
    nch: int
    nt: int
    narr: int
    nat: int
    suma_espera_cola: float
    suma_espera_total: float
    rec: float
    recp: float
    sto: float
    stc: float
    stv: float
    pet: float                      # NaN si no hubo pedidos (§6.10)
    pec: float
    pa: float
    pto: float
    ptc: float
    ptv: float
    rpc: float
    t_ultimo_evento: float
    n_eventos: int
    ns_max: int
    sin_pedidos: bool
