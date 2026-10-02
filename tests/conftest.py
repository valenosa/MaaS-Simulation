"""Rutas comunes de las pruebas (SDD §12.1)."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "tests" / "datos"
CONFIG_EXPERIMENTO = str(RAIZ / "config" / "experimento.toml")
CATALOGO_V1 = str(RAIZ / "config" / "fdp_v1.toml")


def dato(nombre: str) -> str:
    """Ruta de un archivo de tests/datos/."""
    return str(DATOS / nombre)
