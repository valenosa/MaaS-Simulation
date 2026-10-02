"""Orquestación del experimento y sus salidas.

Implementa SDD §8.1 a §8.5 y §9.1 a §9.3, con T-18, T-19 y T-20. No simula (eso lo hace
el motor, §6) ni decide (eso lo hace el análisis, §10).
"""

from __future__ import annotations

import csv
import importlib.metadata
import json
import math
import platform
import time
from dataclasses import dataclass, fields
from datetime import datetime
from pathlib import Path

import numpy as np
import scipy

from simulador_maas.aleatorios import Catalogo, cargar_catalogo, crear_fuentes
from simulador_maas.config import Configuracion, ErrorSimulador, cargar_configuracion
from simulador_maas.entidades import HV, ParametrosCorrida, ResultadoCorrida
from simulador_maas.motor import simular_corrida
from simulador_maas.referencias import Referencias, calcular_referencias

ARCHIVO_EXPERIMENTO = "experimento.json"
ARCHIVO_CORRIDAS = "corridas.csv"

# Tolerancia relativa de las propiedades entre corridas (§8.5).
TOLERANCIA_ENTRE_CORRIDAS = 1e-9

# Columnas de corridas.csv, en orden (§9.2).
COLUMNAS_CORRIDAS = (
    "nivel", "nch", "replica", "nt", "narr", "nat", "suma_espera_cola", "suma_espera_total",
    "rec", "recp", "sto", "stc", "stv", "pet", "pec", "pa", "pto", "ptc", "ptv", "rpc",
    "t_ultimo_evento", "n_eventos", "ns_max", "sin_pedidos",
)

# Columnas del registro de eventos, en orden (§9.3).
COLUMNAS_EVENTOS = (
    "n", "t", "evento", "chofer", "cliente", "detalle", "ncd", "ncc", "nco", "ns", "tll", "tlc", "tps",
    "nt", "nat", "narr", "suma_espera_cola", "suma_espera_total", "rec", "recp", "sto", "stc", "stv",
)


class ErrorExperimento(ErrorSimulador):
    """El experimento o una corrida individual no pueden seguir (§8, §11)."""


@dataclass(frozen=True)
class Preparacion:
    """Resultado de `preparar` (§8.2)."""

    config: Configuracion
    catalogo: Catalogo
    ref: Referencias
    flotas: list[int]
    parametros: ParametrosCorrida


def preparar(ruta_config: str) -> Preparacion:
    """Valida la configuración y el catálogo y calcula los valores derivados y las flotas (§8.2)."""
    config = cargar_configuracion(ruta_config)
    catalogo = cargar_catalogo(config.ruta_catalogo)
    ref = calcular_referencias(config, catalogo)
    flotas = set(range(ref.rango[0], ref.rango[1] + 1))
    flotas.add(ref.flota_actual)                                    # T-19
    if ref.flota_peor is not None:
        flotas.add(ref.flota_peor)
    parametros = ParametrosCorrida(
        umbral_tolerancia_min=config.umbral_tolerancia_min,
        horizonte_min=config.horizonte_min,
        e_s=ref.e_s,
        e_tb=ref.e_tb,
        verificar_invariantes=config.verificar_invariantes,
    )
    return Preparacion(config, catalogo, ref, sorted(flotas), parametros)


def _correr(prep: Preparacion, nch: int, nivel: str, r: int,
            registrar_eventos: bool = False) -> tuple[ResultadoCorrida, list[dict]]:
    """Crea las fuentes de la réplica y simula; ante un error, agrega el nivel, la flota y la réplica (§8.3)."""
    config = prep.config
    fuentes = crear_fuentes(prep.catalogo, config.semilla_base, r, prep.ref.niveles[nivel].media_ia,
                            config.velocidad_mph)
    try:
        return simular_corrida(nch, nivel, prep.parametros, fuentes, registrar_eventos=registrar_eventos)
    except ErrorSimulador as e:
        raise ErrorExperimento(f"Falló la corrida del nivel {nivel}, flota {nch}, réplica {r}: {e}") from e


# ---------------------------------------------------------------------------
# Experimento (§8.3) y propiedades entre corridas (§8.5)
# ---------------------------------------------------------------------------

def ejecutar_experimento(ruta_config: str, salida: str, inicio: datetime) -> None:
    """Recorre niveles, flotas y réplicas y escribe experimento.json y corridas.csv (§8.3)."""
    prep = preparar(ruta_config)
    carpeta = Path(salida)
    try:
        carpeta.mkdir(parents=True, exist_ok=False)
    except FileExistsError as e:
        raise ErrorExperimento(f"La carpeta de salida {salida} ya existe: no se sobrescriben resultados (T-20).") from e
    _escribir_experimento_json(carpeta / ARCHIVO_EXPERIMENTO, prep, inicio)

    filas: list[tuple[int, ResultadoCorrida]] = []
    reloj = time.monotonic()
    for nivel in prep.config.niveles:
        for nch in prep.flotas:
            for r in range(prep.config.replicas):
                resultado, _ = _correr(prep, nch, nivel, r)
                filas.append((r, resultado))
            print(f"nivel {nivel} · NCH {nch} · {prep.config.replicas} réplicas · "
                  f"{time.monotonic() - reloj:.1f} s", flush=True)

    verificar_propiedades_entre_corridas(filas)
    _escribir_corridas_csv(carpeta / ARCHIVO_CORRIDAS, filas)


def verificar_propiedades_entre_corridas(filas: list[tuple[int, ResultadoCorrida]]) -> None:
    """En cada nivel y réplica, todas las flotas tienen el mismo NT y la misma REC + RECP (§8.5, D-09)."""
    grupos: dict[tuple[str, int], list[ResultadoCorrida]] = {}
    for r, resultado in filas:
        grupos.setdefault((resultado.nivel, r), []).append(resultado)
    for (nivel, r), resultados in grupos.items():
        primero = resultados[0]
        difieren = [x.nch for x in resultados
                    if x.nt != primero.nt
                    or not math.isclose(x.rec + x.recp, primero.rec + primero.recp, rel_tol=TOLERANCIA_ENTRE_CORRIDAS)]
        if difieren:
            raise ErrorExperimento(
                f"Los números aleatorios comunes están rotos (D-09): en el nivel {nivel}, réplica {r}, "
                f"las flotas {difieren} no tienen el mismo NT o la misma REC + RECP que la flota {primero.nch}. "
                f"No se escribe {ARCHIVO_CORRIDAS}.")


# ---------------------------------------------------------------------------
# Corrida individual (§8.4)
# ---------------------------------------------------------------------------

def ejecutar_corrida(ruta_config: str, nch: int, nivel: str, r: int, archivo_eventos: str | None) -> None:
    """Simula una corrida, muestra su resultado y, si se pide, escribe su registro de eventos (§8.4, T-18)."""
    prep = preparar(ruta_config)
    if nivel not in prep.config.niveles:
        raise ErrorExperimento(f"El nivel {nivel!r} no existe en la configuración {ruta_config}: "
                               f"los niveles son {', '.join(prep.config.niveles)}.")
    resultado, registro = _correr(prep, nch, nivel, r, registrar_eventos=archivo_eventos is not None)
    print(f"replica: {r}")
    for campo in fields(resultado):
        print(f"{campo.name}: {getattr(resultado, campo.name)}")
    if archivo_eventos is not None:
        escribir_registro_eventos(archivo_eventos, registro)


# ---------------------------------------------------------------------------
# Salidas (§9)
# ---------------------------------------------------------------------------

def celda(valor: object) -> str:
    """Formato común de los CSV (§9): reales sin redondear, NaN y None como celda vacía, lógicos como 0 o 1."""
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "1" if valor else "0"
    if isinstance(valor, float):
        if math.isnan(valor):
            return ""
        if valor == HV:
            return "HV"                                         # solo aparece en el registro de eventos
        return repr(valor)
    return str(valor)


def _escribir_csv(ruta: Path | str, columnas: tuple[str, ...], filas: list[list[str]]) -> None:
    with open(ruta, "w", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo, lineterminator="\n")
        escritor.writerow(columnas)
        escritor.writerows(filas)


def _escribir_corridas_csv(ruta: Path, filas: list[tuple[int, ResultadoCorrida]]) -> None:
    """Una fila por corrida, en el orden del recorrido (§9.2)."""
    salida = []
    for r, resultado in filas:
        valores = {campo.name: getattr(resultado, campo.name) for campo in fields(resultado)}
        valores["replica"] = r
        salida.append([celda(valores[columna]) for columna in COLUMNAS_CORRIDAS])
    _escribir_csv(ruta, COLUMNAS_CORRIDAS, salida)


def escribir_registro_eventos(ruta: str, registro: list[dict]) -> None:
    """Registro de eventos en archivo (§9.3); si el archivo existe, se reemplaza (§8.4)."""
    salida = []
    for fila in registro:
        salida.append([";".join(celda(x) for x in fila[columna]) if columna in ("tlc", "tps") else celda(fila[columna])
                       for columna in COLUMNAS_EVENTOS])
    _escribir_csv(ruta, COLUMNAS_EVENTOS, salida)


def _escribir_experimento_json(ruta: Path, prep: Preparacion, inicio: datetime) -> None:
    """experimento.json, con la estructura exacta de §9.1."""
    config, ref = prep.config, prep.ref
    contenido = {
        "fecha": inicio.isoformat(timespec="seconds"),
        "versiones": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "simulador_maas": importlib.metadata.version("simulador_maas"),
        },
        "configuracion": {"ruta": config.ruta, "contenido": config.texto},
        "catalogo": {"ruta": config.ruta_catalogo, "contenido": prep.catalogo.texto},
        "analisis": {
            "espera_total_max_min": config.espera_total_max_min,
            "abandono_max_pct": config.abandono_max_pct,
            "nivel_confianza": config.nivel_confianza,
        },
        "referencias": {
            "e_tb": ref.e_tb, "e_d": ref.e_d, "e_dem": ref.e_dem, "e_tv": ref.e_tv, "e_s": ref.e_s,
            "niveles": {
                nombre: {"factor": nivel.factor, "lambda": nivel.lam, "media_ia": nivel.media_ia, "carga": nivel.carga}
                for nombre, nivel in ref.niveles.items()
            },
            "flota_actual": ref.flota_actual,
            "flota_peor": ref.flota_peor,
            "rango": list(ref.rango),
            "flotas": prep.flotas,
        },
    }
    with open(ruta, "w", encoding="utf-8", newline="") as archivo:
        json.dump(contenido, archivo, indent=2, ensure_ascii=False, allow_nan=False)
        archivo.write("\n")
