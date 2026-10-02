"""Valores derivados: PR-08 (SDD §3.4, §12.2)."""

import math

from conftest import CONFIG_V1
from simulador_maas.aleatorios import cargar_catalogo
from simulador_maas.config import cargar_configuracion
from simulador_maas.referencias import calcular_referencias


def test_pr08_valores_derivados_con_la_v1():
    config = cargar_configuracion(CONFIG_V1)
    ref = calcular_referencias(config, cargar_catalogo(config.ruta_catalogo))

    assert math.isclose(ref.e_s, 20.0163854565, rel_tol=1e-9)
    assert math.isclose(ref.niveles["bajo"].carga, 5.6045879278, rel_tol=1e-9)
    assert math.isclose(ref.niveles["base"].carga, 8.0065541826, rel_tol=1e-9)
    assert math.isclose(ref.niveles["alto"].carga, 10.408520437, rel_tol=1e-9)
    assert ref.flota_actual == 9
    assert ref.flota_peor == 8
    assert ref.rango == (4, 17)
