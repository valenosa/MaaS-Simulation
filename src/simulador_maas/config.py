"""Carga y validación de la configuración del experimento.

Implementa SDD §3.1 a §3.3 (primera iteración). El rechazo de claves desconocidas
es de la segunda iteración (§1.4) y no está implementado.
"""

from __future__ import annotations

import math
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


class ErrorSimulador(Exception):
    """Base de los errores del simulador: entradas inválidas o corridas que no pueden seguir."""


class ErrorConfiguracion(ErrorSimulador):
    """La configuración no cumple las reglas de SDD §3.3."""


@dataclass(frozen=True)
class Configuracion:
    """Parámetros de `experimento.toml` ya validados (SDD §3.2)."""

    ruta: str                       # tal como se recibió (§9.1)
    texto: str                      # texto completo, tal como se leyó (§9.1)
    velocidad_mph: float
    umbral_tolerancia_min: float
    horizonte_min: float
    media_ia_base_min: float
    niveles: dict[str, float]       # nombre → factor, en el orden del archivo
    replicas: int
    semilla_base: int
    catalogo_fdp: str               # valor escrito en el archivo
    ruta_catalogo: str              # resuelta desde la carpeta de la configuración (§3.1)
    rango_margen_inferior: int
    rango_margen_superior: int
    rango_manual: tuple[int, int] | None
    verificar_invariantes: bool
    espera_total_max_min: float
    abandono_max_pct: float
    nivel_confianza: float


# Tipos de §3.2.
_REAL = "real"
_ENTERO = "entero"
_BOOLEANO = "booleano"
_TEXTO = "texto"
_TABLA_REALES = "tabla de nombre a real"
_LISTA_ENTEROS = "lista de 0 o 2 enteros"

# Claves de §3.2: (sección, clave, tipo, obligatoria).
_CLAVES = (
    ("modelo", "velocidad_mph", _REAL, True),
    ("modelo", "umbral_tolerancia_min", _REAL, True),
    ("modelo", "horizonte_min", _REAL, True),
    ("demanda", "media_ia_base_min", _REAL, True),
    ("demanda", "niveles", _TABLA_REALES, True),
    ("experimento", "replicas", _ENTERO, True),
    ("experimento", "semilla_base", _ENTERO, True),
    ("experimento", "catalogo_fdp", _TEXTO, True),
    ("experimento", "rango_margen_inferior", _ENTERO, True),
    ("experimento", "rango_margen_superior", _ENTERO, True),
    ("experimento", "rango_manual", _LISTA_ENTEROS, False),
    ("experimento", "verificar_invariantes", _BOOLEANO, True),
    ("analisis", "espera_total_max_min", _REAL, True),
    ("analisis", "abandono_max_pct", _REAL, True),
    ("analisis", "nivel_confianza", _REAL, True),
)

NIVEL_BASE = "base"


def es_entero(valor: object) -> bool:
    """Entero de TOML; un booleano nunca vale como número (§3.3)."""
    return isinstance(valor, int) and not isinstance(valor, bool)


def es_numero(valor: object) -> bool:
    """Entero o real de TOML, nunca booleano (§3.3)."""
    return es_entero(valor) or isinstance(valor, float)


def _tiene_tipo(valor: object, tipo: str) -> bool:
    if tipo == _REAL:
        return es_numero(valor)
    if tipo == _ENTERO:
        return es_entero(valor)
    if tipo == _BOOLEANO:
        return isinstance(valor, bool)
    if tipo == _TEXTO:
        return isinstance(valor, str)
    if tipo == _TABLA_REALES:
        return isinstance(valor, dict) and all(es_numero(v) for v in valor.values())
    if tipo == _LISTA_ENTEROS:
        return isinstance(valor, list) and len(valor) in (0, 2) and all(es_entero(v) for v in valor)
    raise AssertionError(f"tipo desconocido: {tipo}")


def _positivo_finito(x: float) -> bool:
    return math.isfinite(x) and x > 0


# Validación de rango de §3.2: clave → (regla en texto, control). Solo U admite infinito.
_RANGOS = {
    "velocidad_mph": ("tiene que ser > 0 y finito", _positivo_finito),
    "umbral_tolerancia_min": ("tiene que ser > 0 (se admite inf)", lambda x: x > 0),
    "horizonte_min": ("tiene que ser > 0 y finito", _positivo_finito),
    "media_ia_base_min": ("tiene que ser > 0 y finito", _positivo_finito),
    "replicas": ("tiene que ser ≥ 2: el intervalo de confianza necesita al menos dos", lambda x: x >= 2),
    "semilla_base": ("tiene que ser ≥ 0", lambda x: x >= 0),
    "rango_margen_inferior": ("tiene que ser ≥ 0", lambda x: x >= 0),
    "rango_margen_superior": ("tiene que ser ≥ 0", lambda x: x >= 0),
    "espera_total_max_min": ("tiene que ser > 0 y finito", _positivo_finito),
    "abandono_max_pct": ("tiene que estar entre 0 y 100", lambda x: 0 <= x <= 100),
    "nivel_confianza": ("tiene que ser mayor que 0 y menor que 1", lambda x: 0 < x < 1),
}


def ruta_relativa_a(ruta_config: str, ruta: str) -> str:
    """Resuelve `ruta` desde la carpeta de `ruta_config` (§3.1), sin volverla absoluta y con '/' (§9.1)."""
    return os.path.join(os.path.dirname(ruta_config), ruta).replace("\\", "/")


def cargar_configuracion(ruta: str) -> Configuracion:
    """Lee `experimento.toml` y lo valida según §3.3. Ante la primera regla que no se cumple, falla."""
    try:
        texto = Path(ruta).read_bytes().decode("utf-8")
    except OSError as e:
        raise ErrorConfiguracion(f"No se puede leer la configuración {ruta}: {e}") from e
    try:
        datos = tomllib.loads(texto)
    except tomllib.TOMLDecodeError as e:
        raise ErrorConfiguracion(f"La configuración {ruta} no es TOML válido: {e}") from e

    def error(nombre: str, valor: object, regla: str) -> ErrorConfiguracion:
        return ErrorConfiguracion(f"Configuración {ruta}: la clave '{nombre}' vale {valor!r}: {regla}.")

    valores: dict[str, object] = {}
    for seccion, clave, tipo, obligatoria in _CLAVES:
        nombre = f"{seccion}.{clave}"
        tabla = datos.get(seccion)
        if not isinstance(tabla, dict) or clave not in tabla:
            if obligatoria:
                raise ErrorConfiguracion(
                    f"Configuración {ruta}: falta la clave obligatoria '{nombre}'.")
            valores[clave] = []
            continue
        valor = tabla[clave]
        if not _tiene_tipo(valor, tipo):
            raise error(nombre, valor, f"tiene que ser de tipo {tipo}")
        if clave in _RANGOS:
            regla, cumple = _RANGOS[clave]
            if not cumple(valor):
                raise error(nombre, valor, regla)
        valores[clave] = valor

    niveles = {nombre: float(factor) for nombre, factor in valores["niveles"].items()}
    if not niveles:
        raise error("demanda.niveles", valores["niveles"], "tiene que tener al menos un nivel")
    for nombre, factor in niveles.items():
        if not _positivo_finito(factor):
            raise error(f"demanda.niveles.{nombre}", factor, "tiene que ser > 0 y finito")
    if NIVEL_BASE not in niveles or niveles[NIVEL_BASE] != 1:
        raise error("demanda.niveles", valores["niveles"],
                    f"tiene que existir el nivel '{NIVEL_BASE}' y valer 1 (D-07)")

    rango_manual = valores["rango_manual"]
    if rango_manual and not 1 <= rango_manual[0] <= rango_manual[1]:
        raise error("experimento.rango_manual", rango_manual, "con dos valores, tiene que cumplir 1 ≤ desde ≤ hasta")

    ruta_catalogo = ruta_relativa_a(ruta, valores["catalogo_fdp"])
    if not Path(ruta_catalogo).is_file():
        raise error("experimento.catalogo_fdp", valores["catalogo_fdp"],
                    f"no existe el archivo {ruta_catalogo} (la ruta es relativa a la carpeta de la configuración)")

    return Configuracion(
        ruta=ruta,
        texto=texto,
        velocidad_mph=float(valores["velocidad_mph"]),
        umbral_tolerancia_min=float(valores["umbral_tolerancia_min"]),
        horizonte_min=float(valores["horizonte_min"]),
        media_ia_base_min=float(valores["media_ia_base_min"]),
        niveles=niveles,
        replicas=valores["replicas"],
        semilla_base=valores["semilla_base"],
        catalogo_fdp=valores["catalogo_fdp"],
        ruta_catalogo=ruta_catalogo,
        rango_margen_inferior=valores["rango_margen_inferior"],
        rango_margen_superior=valores["rango_margen_superior"],
        rango_manual=tuple(rango_manual) if rango_manual else None,
        verificar_invariantes=valores["verificar_invariantes"],
        espera_total_max_min=float(valores["espera_total_max_min"]),
        abandono_max_pct=float(valores["abandono_max_pct"]),
        nivel_confianza=float(valores["nivel_confianza"]),
    )
