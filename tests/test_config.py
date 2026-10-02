"""Validación de la configuración: PR-10 (d) y (e) (SDD §3.2, §3.3, §12.2)."""

import dataclasses
import math

import pytest

from conftest import CONFIG_EXPERIMENTO, CONFIG_V1, dato
from simulador_maas.config import ErrorConfiguracion, cargar_configuracion


def test_configuracion_del_experimento_es_valida():
    config = cargar_configuracion(CONFIG_EXPERIMENTO)
    assert list(config.niveles) == ["bajo", "base", "alto"]
    assert config.rango_manual is None


def test_la_copia_con_la_v1_coincide_con_la_configuracion_del_experimento():
    """tests/datos/v1_config.toml es config/experimento.toml con el catálogo V1 (§12.1)."""
    experimento, v1 = cargar_configuracion(CONFIG_EXPERIMENTO), cargar_configuracion(CONFIG_V1)
    distintos = {"ruta", "texto", "catalogo_fdp", "ruta_catalogo"}
    for campo in dataclasses.fields(experimento):
        if campo.name not in distintos:
            assert getattr(v1, campo.name) == getattr(experimento, campo.name), campo.name
    assert v1.ruta_catalogo.endswith("config/fdp_v1.toml")


def test_pr10d_sin_nivel_base_da_error():
    with pytest.raises(ErrorConfiguracion, match="base"):
        cargar_configuracion(dato("pr10d_sin_nivel_base.toml"))


def test_pr10e_horizonte_cero_da_error_con_la_clave():
    with pytest.raises(ErrorConfiguracion, match="horizonte_min"):
        cargar_configuracion(dato("pr10e_horizonte_cero.toml"))


@pytest.mark.parametrize("archivo", ["pr10e_rango_manual_desde_cero.toml", "pr10e_rango_manual_un_valor.toml"])
def test_pr10e_rango_manual_invalido_da_error(archivo):
    with pytest.raises(ErrorConfiguracion, match="rango_manual"):
        cargar_configuracion(dato(archivo))


def test_pr10e_horizonte_infinito_da_error():
    with pytest.raises(ErrorConfiguracion, match="horizonte_min"):
        cargar_configuracion(dato("pr10e_horizonte_infinito.toml"))


def test_pr10e_umbral_infinito_es_valido():
    assert math.isinf(cargar_configuracion(dato("pr10e_umbral_infinito.toml")).umbral_tolerancia_min)
