"""Valores derivados: medias, carga, flotas de referencia y rango de NCH.

Implementa SDD §3.4, con T-12. Se calculan al arrancar y nunca se escriben en un
archivo de entrada (modelo §4.4, D-07).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from simulador_maas.aleatorios import MINUTOS_POR_HORA, Catalogo, media_exacta
from simulador_maas.config import NIVEL_BASE, Configuracion, ErrorSimulador

# Tolerancia del redondeo hacia arriba de flotas y límites del rango (T-12).
TOLERANCIA_TECHO = 1e-9


class ErrorReferencias(ErrorSimulador):
    """No se pueden calcular los valores derivados (§3.4)."""


@dataclass(frozen=True)
class Nivel:
    """Valores derivados de un nivel de demanda (§3.4)."""

    factor: float
    lam: float                      # λ (pedidos/min)
    media_ia: float                 # media del intervalo entre pedidos (min)
    carga: float                    # a = λ × E[S]


@dataclass(frozen=True)
class Referencias:
    """Valores derivados de la configuración y del catálogo (§3.4)."""

    e_tb: float
    e_d: float
    e_dem: float
    e_tv: float
    e_s: float
    niveles: dict[str, Nivel]       # en el orden de la configuración
    flota_actual: int
    flota_peor: int | None          # no existe si daría menos de 1
    rango: tuple[int, int]          # el de rango_manual, si se indicó, o el de la regla


def techo(x: float) -> int:
    """⌈x⌉ con la tolerancia de T-12."""
    return math.ceil(x - TOLERANCIA_TECHO)


def calcular_referencias(config: Configuracion, catalogo: Catalogo) -> Referencias:
    """Calcula los valores derivados de §3.4, en doble precisión y sin redondear."""
    e_tb = media_exacta(catalogo.fdps["TB"])
    e_d = media_exacta(catalogo.fdps["D"])
    e_dem = media_exacta(catalogo.fdps["DEM"])
    e_tv = MINUTOS_POR_HORA * e_d / config.velocidad_mph + e_dem
    e_s = e_tb + e_tv
    if not math.isfinite(e_s) or e_s <= 0:
        raise ErrorReferencias(
            f"E[S] = {e_s} con el catálogo {catalogo.ruta}: tiene que ser un número finito y mayor que 0; "
            "sin él no hay carga ni flotas de referencia (SDD §3.4).")

    niveles = {}
    for nombre, factor in config.niveles.items():
        lam = factor / config.media_ia_base_min
        niveles[nombre] = Nivel(factor=factor, lam=lam, media_ia=config.media_ia_base_min / factor,
                                carga=lam * e_s)

    flota_actual = techo(niveles[NIVEL_BASE].carga)
    flota_peor = flota_actual - 1 if flota_actual - 1 >= 1 else None

    if config.rango_manual is not None:
        rango = config.rango_manual
    else:
        cargas = [nivel.carga for nivel in niveles.values()]
        rango = (max(1, techo(min(cargas)) - config.rango_margen_inferior),
                 techo(max(cargas)) + config.rango_margen_superior)

    return Referencias(e_tb=e_tb, e_d=e_d, e_dem=e_dem, e_tv=e_tv, e_s=e_s, niveles=niveles,
                       flota_actual=flota_actual, flota_peor=flota_peor, rango=rango)
