"""Rutas y ayudas comunes de las pruebas (SDD §12.1)."""

from pathlib import Path

from simulador_maas.aleatorios import cargar_catalogo, crear_fuentes
from simulador_maas.config import NIVEL_BASE, cargar_configuracion
from simulador_maas.entidades import ParametrosCorrida
from simulador_maas.referencias import calcular_referencias

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "tests" / "datos"
CONFIG_EXPERIMENTO = str(RAIZ / "config" / "experimento.toml")
CATALOGO_V1 = str(RAIZ / "config" / "fdp_v1.toml")
# config/experimento.toml con el catálogo V1: PR-02, PR-03 y PR-08 (§12.1).
CONFIG_V1 = str(DATOS / "v1_config.toml")


def dato(nombre: str) -> str:
    """Ruta de un archivo de tests/datos/."""
    return str(DATOS / nombre)


class Preparado:
    """Lo necesario para llamar al motor directamente, sin el orquestador (SDD §4.6, §12.1)."""

    def __init__(self, ruta_config: str):
        self.config = cargar_configuracion(ruta_config)
        self.catalogo = cargar_catalogo(self.config.ruta_catalogo)
        self.ref = calcular_referencias(self.config, self.catalogo)
        # Todas las pruebas corren con los invariantes activos (§12.1).
        self.parametros = ParametrosCorrida(
            umbral_tolerancia_min=self.config.umbral_tolerancia_min,
            horizonte_min=self.config.horizonte_min,
            e_s=self.ref.e_s,
            e_tb=self.ref.e_tb,
            verificar_invariantes=True,
        )

    def fuentes(self, r: int = 0, nivel: str = NIVEL_BASE):
        return crear_fuentes(self.catalogo, self.config.semilla_base, r, self.ref.niveles[nivel].media_ia,
                             self.config.velocidad_mph)
