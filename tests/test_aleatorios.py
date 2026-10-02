"""Generación de valores aleatorios: PR-03 (b) y PR-10 (a) y (b) (SDD §5, §12.2)."""

import math

import pytest

from conftest import CONFIG_V1, dato
from simulador_maas.aleatorios import ErrorCatalogo, cargar_catalogo, crear_fuentes
from simulador_maas.config import cargar_configuracion
from simulador_maas.referencias import calcular_referencias

PEDIDOS = 100


def test_pr03b_mismos_atributos_e_intervalos_proporcionales_entre_niveles():
    config = cargar_configuracion(CONFIG_V1)
    catalogo = cargar_catalogo(config.ruta_catalogo)
    ref = calcular_referencias(config, catalogo)

    atributos, intervalos = {}, {}
    for nombre, nivel in ref.niveles.items():
        fuentes = crear_fuentes(catalogo, config.semilla_base, 0, nivel.media_ia, config.velocidad_mph)
        atributos[nombre] = [fuentes.sortear_atributos() for _ in range(PEDIDOS)]
        intervalos[nombre] = [fuentes.sortear_ia() for _ in range(PEDIDOS)]

    assert atributos["bajo"] == atributos["base"] == atributos["alto"]
    for nombre, nivel in ref.niveles.items():
        for ia, ia_base in zip(intervalos[nombre], intervalos["base"]):
            assert math.isclose(ia / ia_base, nivel.media_ia / ref.niveles["base"].media_ia, rel_tol=1e-12)


def test_pr10a_tarifa_en_modo_regresion_es_de_la_segunda_iteracion():
    with pytest.raises(ErrorCatalogo, match="segunda iteración"):
        cargar_catalogo(dato("pr10a_tarifa_regresion.toml"))


@pytest.mark.parametrize("archivo", [
    "pr10b_familia_inexistente.toml",     # no existe en scipy
    "pr10b_no_es_distribucion.toml",      # describe: existe, pero no es una distribución
    "pr10b_gamma_media_no_finita.toml",   # gamma con a = -1: media NaN
])
def test_pr10b_familia_invalida_da_error_con_la_variable(archivo):
    with pytest.raises(ErrorCatalogo, match=r"\[TB\]"):
        cargar_catalogo(dato(archivo))
