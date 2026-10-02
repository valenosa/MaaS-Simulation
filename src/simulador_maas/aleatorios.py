"""FDP, generadores y semillas.

Implementa SDD §5.1 a §5.9 (primera iteración), con T-08, T-09, T-10, T-14 y T-17.
No implementa §5.10 (segunda iteración): el modo "regresion" de la tarifa, el tipo
`empirica` ni la validación completa del catálogo.
"""

from __future__ import annotations

import math
import tomllib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import scipy.stats

from simulador_maas.config import ErrorSimulador, es_numero

# Número fijo k de cada variable aleatoria (§5.2).
NUMERO_VARIABLE = {"IA": 0, "TB": 1, "D": 2, "DEM": 3, "TAR": 4}

# Tamaño del bloque de los generadores con búfer (T-09). No se cambia.
TAMANO_BLOQUE = 1024

MINUTOS_POR_HORA = 60

VERSIONES = ("V1", "V2", "PRUEBA")
VERSION_PRUEBA = "PRUEBA"
VERSION_V2 = "V2"
TIPOS = ("scipy", "constante", "secuencia")
MODO_INDEPENDIENTE = "independiente"
MODO_REGRESION = "regresion"
VARIABLES_OBLIGATORIAS = ("TB", "D", "DEM", "TAR")
CLAVES_DIAGNOSTICO_V2 = ("n_filas", "media_datos_usd", "desvio_datos_usd")


class ErrorCatalogo(ErrorSimulador):
    """El catálogo de FDP no cumple el contrato de §5.6 o la validación de §5.9."""


class ErrorFDP(ErrorSimulador):
    """Una FDP entregó un valor inválido durante la corrida (§5.3, §5.4, T-10)."""


@dataclass(frozen=True)
class FDP:
    """Una variable aleatoria del catálogo (§5.3)."""

    variable: str
    tipo: str
    familia: str | None = None
    parametros: dict[str, float] | None = None
    valor: float | None = None
    valores: tuple[float, ...] | None = None

    def distribucion(self):
        """Distribución congelada de scipy (solo tipo `scipy`)."""
        return getattr(scipy.stats, self.familia)(**self.parametros)


@dataclass(frozen=True)
class Catalogo:
    """Catálogo de FDP ya validado (§5.9)."""

    ruta: str
    texto: str
    version: str
    modo_tarifa: str
    fdps: dict[str, FDP]            # TB, D, DEM, TAR y, solo en un catálogo de PRUEBA, IA


# ---------------------------------------------------------------------------
# Carga y validación (§5.6, §5.9, T-14)
# ---------------------------------------------------------------------------

def cargar_catalogo(ruta: str) -> Catalogo:
    """Lee un catálogo de FDP y lo valida en el orden de §5.9. Cualquier falla es un error."""
    try:
        texto = Path(ruta).read_bytes().decode("utf-8")
    except OSError as e:
        raise ErrorCatalogo(f"No se puede leer el catálogo {ruta}: {e}") from e
    try:
        datos = tomllib.loads(texto)
    except tomllib.TOMLDecodeError as e:
        raise ErrorCatalogo(f"El catálogo {ruta} no es TOML válido: {e}") from e

    def error(mensaje: str) -> ErrorCatalogo:
        return ErrorCatalogo(f"Catálogo {ruta}: {mensaje}")

    # 1. Versión.
    seccion = datos.get("catalogo")
    if not isinstance(seccion, dict):
        raise error("falta la sección [catalogo].")
    version = seccion.get("version")
    if version not in VERSIONES:
        raise error(f"[catalogo] version vale {version!r}: tiene que ser uno de {', '.join(VERSIONES)}.")

    # 2. Modo de la tarifa (T-17). Va antes que la estructura: en modo "regresion", [TAR] no tiene `tipo`.
    tar = datos.get("TAR")
    if not isinstance(tar, dict):
        raise error("falta la sección [TAR].")
    if "modo" not in tar:
        raise error("[TAR] no tiene la clave obligatoria 'modo'.")
    if tar["modo"] != MODO_INDEPENDIENTE:
        raise error(
            f"[TAR] modo = {tar['modo']!r} no se acepta: en la primera iteración solo existe "
            f"el modo '{MODO_INDEPENDIENTE}'. El modo '{MODO_REGRESION}' es de la segunda iteración "
            "(SDD §5.10.1, D-16).")

    # 3. Estructura.
    for variable in VARIABLES_OBLIGATORIAS:
        if not isinstance(datos.get(variable), dict):
            raise error(f"falta la sección [{variable}].")
    if version == VERSION_V2:
        diagnostico = tar.get("diagnostico")
        if not isinstance(diagnostico, dict):
            raise error("falta la sección [TAR.diagnostico], obligatoria en la V2 (§5.6, regla 1).")
        for clave in CLAVES_DIAGNOSTICO_V2:
            if clave not in diagnostico:
                raise error(f"[TAR.diagnostico] no tiene la clave obligatoria '{clave}' (§5.6, regla 1).")

    fdps = {variable: _leer_fdp(variable, datos[variable], error) for variable in VARIABLES_OBLIGATORIAS}

    if "IA" in datos:
        if version != VERSION_PRUEBA:
            raise error("la sección [IA] solo se admite en un catálogo de PRUEBA: el intervalo entre "
                        "pedidos lo define el modelo (D-01) y su media está en experimento.toml (§5.6, regla 2).")
        if not isinstance(datos["IA"], dict):
            raise error("[IA] tiene que ser una sección.")
        if datos["IA"].get("tipo") not in ("constante", "secuencia"):
            raise error(f"[IA] tipo = {datos['IA'].get('tipo')!r}: solo se admiten 'constante' o 'secuencia' "
                        "(§5.6, regla 2).")
        ia = _leer_fdp("IA", datos["IA"], error)
        if ia.tipo == "constante" and not ia.valor > 0:
            raise error(f"[IA] constante vale {ia.valor!r}: tiene que ser mayor que 0, "
                        "o el reloj no avanzaría (§5.6, regla 2).")
        if ia.tipo == "secuencia" and not all(x >= 0 for x in ia.valores):
            raise error("[IA] secuencia tiene valores negativos: tienen que ser ≥ 0 (§5.6, regla 2).")
        fdps["IA"] = ia

    # 4. Parámetros de cada distribución de scipy.
    for variable, fdp in fdps.items():
        if fdp.tipo == "scipy":
            _validar_scipy(fdp, error)

    return Catalogo(ruta=ruta, texto=texto, version=version, modo_tarifa=tar["modo"], fdps=fdps)


def _leer_fdp(variable: str, seccion: dict, error) -> FDP:
    """Controla la estructura de una variable (§5.9, paso 3) y convierte sus valores a real (§5.3)."""
    tipo = seccion.get("tipo")
    if "tipo" not in seccion:
        raise error(f"[{variable}] no tiene la clave obligatoria 'tipo'.")
    if tipo not in TIPOS:
        raise error(f"[{variable}] tipo = {tipo!r}: los tipos de la primera iteración son {', '.join(TIPOS)} (§5.3).")

    if tipo == "scipy":
        for clave in ("familia", "parametros"):
            if clave not in seccion:
                raise error(f"[{variable}] no tiene la clave obligatoria '{clave}' del tipo scipy.")
        familia, parametros = seccion["familia"], seccion["parametros"]
        if not isinstance(familia, str):
            raise error(f"[{variable}] familia = {familia!r}: tiene que ser un texto.")
        if not isinstance(parametros, dict):
            raise error(f"[{variable}] parametros = {parametros!r}: tiene que ser una tabla.")
        for nombre, valor in parametros.items():
            if not es_numero(valor):
                raise error(f"[{variable}] el parámetro {nombre} = {valor!r} tiene que ser un número.")
        return FDP(variable, tipo, familia=familia,
                   parametros={nombre: float(valor) for nombre, valor in parametros.items()})

    if tipo == "constante":
        if "valor" not in seccion:
            raise error(f"[{variable}] no tiene la clave obligatoria 'valor' del tipo constante.")
        if not es_numero(seccion["valor"]):
            raise error(f"[{variable}] valor = {seccion['valor']!r}: tiene que ser un número.")
        return FDP(variable, tipo, valor=float(seccion["valor"]))

    # secuencia
    if "valores" not in seccion:
        raise error(f"[{variable}] no tiene la clave obligatoria 'valores' del tipo secuencia.")
    valores = seccion["valores"]
    if not isinstance(valores, list) or not valores or not all(es_numero(x) for x in valores):
        raise error(f"[{variable}] valores = {valores!r}: tiene que ser una lista de números con al menos un valor.")
    return FDP(variable, tipo, valores=tuple(float(x) for x in valores))


def _validar_scipy(fdp: FDP, error) -> None:
    """§5.9, paso 4: la familia es una distribución continua de scipy, se construye y su media es finita."""
    candidata = getattr(scipy.stats, fdp.familia, None)
    if candidata is None:
        raise error(f"[{fdp.variable}] la familia {fdp.familia!r} no existe en scipy.stats.")
    if not isinstance(candidata, scipy.stats.rv_continuous):
        raise error(f"[{fdp.variable}] {fdp.familia!r} existe en scipy.stats, pero no es una distribución continua.")
    try:
        media = float(fdp.distribucion().mean())
    except Exception as e:  # scipy informa los parámetros inválidos con distintos tipos de excepción
        raise error(f"[{fdp.variable}] scipy no puede construir {fdp.familia} con {fdp.parametros}: {e}") from e
    if not math.isfinite(media):
        raise error(f"[{fdp.variable}] {fdp.familia} con {fdp.parametros} tiene media {media}: "
                    "los parámetros no son válidos.")


# ---------------------------------------------------------------------------
# Medias exactas (§5.8)
# ---------------------------------------------------------------------------

def media_exacta(fdp: FDP) -> float:
    """Media exacta de una FDP del catálogo (§5.8)."""
    if fdp.tipo == "scipy":
        return float(fdp.distribucion().mean())
    if fdp.tipo == "constante":
        return fdp.valor
    return math.fsum(fdp.valores) / len(fdp.valores)


# ---------------------------------------------------------------------------
# Generadores y fuentes de una réplica (§5.1 a §5.5)
# ---------------------------------------------------------------------------

def crear_generador(semilla_base: int, r: int, k: int) -> np.random.Generator:
    """Generador de la variable k en la réplica r (§5.2, T-08)."""
    semilla = np.random.SeedSequence(entropy=semilla_base, spawn_key=(r, k))
    return np.random.Generator(np.random.PCG64(semilla))


class _ConBufer:
    """Entrega de a uno valores sorteados en bloques de TAMANO_BLOQUE (T-09)."""

    def __init__(self, sortear_bloque):
        self._sortear_bloque = sortear_bloque
        self._bloque: list[float] = []
        self._pos = 0

    def __call__(self) -> float:
        if self._pos == len(self._bloque):
            self._bloque = self._sortear_bloque(TAMANO_BLOQUE).tolist()
            self._pos = 0
        x = self._bloque[self._pos]
        self._pos += 1
        return x


class _Secuencia:
    """Los valores de una secuencia en orden; agotarla es un error (§5.3)."""

    def __init__(self, fdp: FDP, ruta_catalogo: str):
        self._fdp = fdp
        self._ruta = ruta_catalogo
        self._pos = 0

    def __call__(self) -> float:
        if self._pos == len(self._fdp.valores):
            raise ErrorFDP(f"La secuencia de {self._fdp.variable} del catálogo {self._ruta} se agotó "
                           f"después de {len(self._fdp.valores)} valores.")
        x = self._fdp.valores[self._pos]
        self._pos += 1
        return x


def _sorteador(fdp: FDP, generador: np.random.Generator, ruta_catalogo: str):
    """Función sin argumentos que devuelve el próximo valor de la FDP (§5.3)."""
    if fdp.tipo == "scipy":
        distribucion = fdp.distribucion()
        return _ConBufer(lambda n: distribucion.rvs(size=n, random_state=generador))
    if fdp.tipo == "constante":
        valor = fdp.valor
        return lambda: valor
    return _Secuencia(fdp, ruta_catalogo)


class Fuentes:
    """Fuentes de valores aleatorios de una réplica (§5.1). El motor solo usa sus dos operaciones."""

    def __init__(self, catalogo: Catalogo, semilla_base: int, r: int, media_ia: float, v: float):
        self._catalogo = catalogo
        self._v = v
        generadores = {variable: crear_generador(semilla_base, r, k) for variable, k in NUMERO_VARIABLE.items()}
        if "IA" in catalogo.fdps:
            # Catálogo de PRUEBA con [IA]: los valores tal cual, sin escalar por el nivel (§5.2).
            self._ia = _sorteador(catalogo.fdps["IA"], generadores["IA"], catalogo.ruta)
        else:
            # IA = (media del intervalo del nivel) × E, con E exponencial de media 1 (§5.2, D-09).
            exponencial = _ConBufer(generadores["IA"].standard_exponential)
            self._ia = lambda: media_ia * exponencial()
        self._tb = _sorteador(catalogo.fdps["TB"], generadores["TB"], catalogo.ruta)
        self._d = _sorteador(catalogo.fdps["D"], generadores["D"], catalogo.ruta)
        self._dem = _sorteador(catalogo.fdps["DEM"], generadores["DEM"], catalogo.ruta)
        self._tar = _sorteador(catalogo.fdps["TAR"], generadores["TAR"], catalogo.ruta)

    def sortear_ia(self) -> float:
        """El próximo intervalo entre pedidos (min), ya escalado al nivel de demanda (§5.2)."""
        return self._ia()

    def sortear_atributos(self) -> tuple[float, float, float, float, float]:
        """tb, d, dem, tv y tar de un pedido (§5.4)."""
        tb = self._tb()
        d = self._d()
        dem = self._dem()
        tar = self._sortear_tarifa(d)
        for variable, valor in (("TB", tb), ("D", d), ("DEM", dem), ("TAR", tar)):
            if valor < 0:
                raise ErrorFDP(f"Valor negativo de FDP: la variable {variable} dio {valor!r} "
                               f"con el catálogo {self._catalogo.ruta} (T-10).")
        tv = d * MINUTOS_POR_HORA / self._v + dem
        return tb, d, dem, tv, tar

    def _sortear_tarifa(self, d: float) -> float:
        """Tarifa (§5.5, D-14). El parámetro d lo usará el modo "regresion" de la segunda iteración."""
        if self._catalogo.modo_tarifa == MODO_INDEPENDIENTE:
            return self._tar()
        raise ErrorCatalogo("modo de tarifa no implementado en la primera iteración")


def crear_fuentes(catalogo: Catalogo, semilla_base: int, r: int, media_ia: float, v: float) -> Fuentes:
    """Fuentes de la réplica r para un nivel de demanda (§5.1)."""
    return Fuentes(catalogo, semilla_base, r, media_ia, v)
