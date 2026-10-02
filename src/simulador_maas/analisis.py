"""Análisis: agregación, criterio de decisión, escenarios, sensibilidad, avisos y gráficos.

Implementa SDD §10 (§10.1 a §10.6), con T-20, T-21 y T-22. Solo lee las salidas de un
experimento (§9.1, §9.2); nunca llama al motor, así que cambiar X e Y no requiere volver
a simular (§2.3, D-10).
"""

from __future__ import annotations

import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.stats
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from simulador_maas.config import NIVEL_BASE, ErrorSimulador

ARCHIVO_EXPERIMENTO = "experimento.json"
ARCHIVO_CORRIDAS = "corridas.csv"

# Métricas que se agregan por configuración (§10.2) y sus estadísticos (§10.6).
METRICAS = ("pet", "pec", "pa", "pto", "ptc", "ptv", "rec", "recp", "rpc")
ESTADISTICOS = ("media", "desvio", "ic_inf", "ic_sup")
COLUMNAS_RESUMEN = (("nivel", "nch", "n_replicas", "n_sin_pedidos")
                    + tuple(f"{m}_{e}" for m in METRICAS for e in ESTADISTICOS)
                    + ("cumple", "en_el_limite"))
COLUMNAS_ENTERAS = ("nch", "n_replicas", "n_sin_pedidos", "cumple", "en_el_limite")
ESCENARIOS = ("peor", "actual", "mejor")
METRICAS_SENSIBILIDAD = ("pet", "pa", "pto", "rec", "recp")

# Gráficos (§10.5, T-21): PNG de 300 dpi, de 16 × 9 cm, letra de 8 puntos, en escala de grises.
CM_POR_PULGADA = 2.54
ANCHO_CM, ALTO_CM = 16, 9
DPI = 300
TAMANO_LETRA = 8
GRISES = ("0", "0.4", "0.65")
MARCADORES = ("o", "s", "^", "D", "v")
LINEAS = ("-", "--", ":", "-.")
EJE_NCH = "Cantidad de choferes (NCH)"


class ErrorAnalisis(ErrorSimulador):
    """La carpeta del experimento no se puede analizar (§8.6)."""


@dataclass(frozen=True)
class Criterio:
    """Parámetros del análisis (§10.1), con las mismas claves que `analisis` en experimento.json."""

    espera_total_max_min: float     # X
    abandono_max_pct: float         # Y
    nivel_confianza: float


def nombre_carpeta(x: float, y: float) -> str:
    """analisis_X<x>_Y<y>: sin decimales si son enteros y, si no, como los escribe str() (§10.6)."""
    def formato(v: float) -> str:
        return str(int(v)) if float(v).is_integer() else str(v)
    return f"analisis_X{formato(x)}_Y{formato(y)}"


def ejecutar_analisis(entrada: str, espera_max: float | None = None, abandono_max: float | None = None) -> Path:
    """Analiza un experimento ya corrido y escribe sus archivos en <entrada>/analisis_X<x>_Y<y>/ (§10.6)."""
    carpeta = Path(entrada)
    if not (carpeta / ARCHIVO_EXPERIMENTO).is_file():
        raise ErrorAnalisis(f"{entrada} no es la carpeta de un experimento: no tiene {ARCHIVO_EXPERIMENTO}.")
    if not (carpeta / ARCHIVO_CORRIDAS).is_file():
        raise ErrorAnalisis(f"{entrada} no tiene {ARCHIVO_CORRIDAS}: el experimento quedó incompleto (§8.3).")

    experimento = json.loads((carpeta / ARCHIVO_EXPERIMENTO).read_text(encoding="utf-8"))
    guardado = experimento["analisis"]
    criterio = Criterio(
        espera_total_max_min=guardado["espera_total_max_min"] if espera_max is None else espera_max,
        abandono_max_pct=guardado["abandono_max_pct"] if abandono_max is None else abandono_max,
        nivel_confianza=guardado["nivel_confianza"],
    )
    ref = experimento["referencias"]
    niveles = list(ref["niveles"])
    corridas = pd.read_csv(carpeta / ARCHIVO_CORRIDAS, dtype={"nivel": str})

    resumen = agregar(corridas, niveles, criterio)
    mejores = {nivel: _mejor_flota(resumen, nivel) for nivel in niveles}
    avisos = generar_avisos(resumen, niveles, mejores, ref["flota_actual"], ref["flota_peor"])
    escenarios = _escenarios(resumen, mejores.get(NIVEL_BASE), ref["flota_actual"], ref["flota_peor"])
    sensibilidad = _sensibilidad(resumen, niveles, mejores, ref["flota_actual"])

    salida = carpeta / nombre_carpeta(criterio.espera_total_max_min, criterio.abandono_max_pct)
    if salida.exists():
        shutil.rmtree(salida)                                   # se regenera desde corridas.csv (T-20)
    salida.mkdir()
    (salida / "parametros.json").write_text(
        json.dumps({"espera_total_max_min": criterio.espera_total_max_min,
                    "abandono_max_pct": criterio.abandono_max_pct,
                    "nivel_confianza": criterio.nivel_confianza}, indent=2) + "\n", encoding="utf-8")
    _escribir_csv(resumen, salida / "resumen.csv")
    _escribir_csv(escenarios, salida / "escenarios.csv")
    _escribir_csv(sensibilidad, salida / "sensibilidad.csv")
    (salida / "avisos.txt").write_text("\n".join(avisos or ["Sin avisos"]) + "\n", encoding="utf-8")
    _graficar(resumen, niveles, criterio, salida)

    _mostrar(escenarios, mejores, avisos, salida)
    return salida


# ---------------------------------------------------------------------------
# Agregación y criterio (§10.2, §10.3)
# ---------------------------------------------------------------------------

def _estadisticos(valores: pd.Series, nivel_confianza: float) -> tuple[int, float, float, float, float]:
    """n, media, desvío muestral e intervalo de confianza con t de Student, sin las celdas vacías (§10.2)."""
    x = valores.dropna().to_numpy(dtype=float)
    n = len(x)
    media = float(np.mean(x)) if n > 0 else math.nan
    if n < 2:
        return n, media, math.nan, math.nan, math.nan
    s = float(np.std(x, ddof=1))
    alfa = 1 - nivel_confianza
    h = float(scipy.stats.t.ppf(1 - alfa / 2, n - 1)) * s / math.sqrt(n)
    return n, media, s, media - h, media + h


def _contiene(inf: float, sup: float, valor: float) -> bool:
    """El intervalo contiene al valor, con los extremos incluidos; un intervalo indefinido da falso (§10.3)."""
    return not (math.isnan(inf) or math.isnan(sup)) and inf <= valor <= sup


def agregar(corridas: pd.DataFrame, niveles: list[str], criterio: Criterio) -> pd.DataFrame:
    """Una fila por nivel y flota, con los estadísticos de cada métrica y el criterio (§10.2, §10.3)."""
    filas = []
    for nivel in niveles:
        del_nivel = corridas[corridas["nivel"] == nivel]
        for nch in sorted(del_nivel["nch"].unique()):
            grupo = del_nivel[del_nivel["nch"] == nch]
            fila = {"nivel": nivel, "nch": int(nch), "n_replicas": len(grupo),
                    "n_sin_pedidos": int(grupo["sin_pedidos"].sum())}
            n_minimo = len(grupo)
            for m in METRICAS:
                n, media, desvio, ic_inf, ic_sup = _estadisticos(grupo[m], criterio.nivel_confianza)
                n_minimo = min(n_minimo, n)
                fila.update({f"{m}_media": media, f"{m}_desvio": desvio, f"{m}_ic_inf": ic_inf, f"{m}_ic_sup": ic_sup})
            # Una media indefinida no cumple: las comparaciones con NaN dan falso.
            fila["cumple"] = int(fila["pet_media"] <= criterio.espera_total_max_min
                                 and fila["pa_media"] <= criterio.abandono_max_pct)
            fila["en_el_limite"] = int(_contiene(fila["pet_ic_inf"], fila["pet_ic_sup"], criterio.espera_total_max_min)
                                       or _contiene(fila["pa_ic_inf"], fila["pa_ic_sup"], criterio.abandono_max_pct))
            fila["_n_minimo"] = n_minimo                         # para A7; no se escribe
            filas.append(fila)
    return pd.DataFrame(filas, columns=list(COLUMNAS_RESUMEN) + ["_n_minimo"])


def _fila(resumen: pd.DataFrame, nivel: str, nch: int) -> pd.Series | None:
    filas = resumen[(resumen["nivel"] == nivel) & (resumen["nch"] == nch)]
    return None if filas.empty else filas.iloc[0]


def _mejor_flota(resumen: pd.DataFrame, nivel: str) -> int | None:
    """NCH*: la menor flota que cumple en el nivel (§10.3, D-03)."""
    cumplen = resumen[(resumen["nivel"] == nivel) & (resumen["cumple"] == 1)]["nch"]
    return None if cumplen.empty else int(cumplen.min())


def generar_avisos(resumen: pd.DataFrame, niveles: list[str], mejores: dict[str, int | None],
                   flota_actual: int, flota_peor: int | None) -> list[str]:
    """Avisos A1 a A8, ordenados por código, nivel y flota (§10.3, T-22)."""
    avisos: list[tuple[str, int, int, str]] = []           # (código, orden del nivel, flota, línea)

    def agregar_aviso(codigo: str, nivel: str | None, flota: int, texto: str) -> None:
        orden = niveles.index(nivel) if nivel is not None else -1
        linea = f"{codigo} [{nivel}] {texto}" if nivel is not None else f"{codigo} {texto}"
        avisos.append((codigo, orden, flota, linea))

    for nivel in niveles:
        del_nivel = resumen[resumen["nivel"] == nivel]
        mejor = mejores[nivel]
        if mejor is None:
            agregar_aviso("A1", nivel, 0, f"Ninguna flota cumple en el nivel {nivel}: ampliar el rango hacia arriba.")
        else:
            if mejor == del_nivel["nch"].max():
                agregar_aviso("A2", nivel, 0, f"La mejor flota del nivel {nivel} es el límite del rango: "
                                              "ampliarlo para ver la sobreoferta.")
            for _, fila in del_nivel[(del_nivel["nch"] > mejor) & (del_nivel["cumple"] == 0)].iterrows():
                agregar_aviso("A5", nivel, int(fila["nch"]),
                              f"Resultados no monótonos en el nivel {nivel}: la flota {int(fila['nch'])} no cumple.")
            if _fila(resumen, nivel, mejor)["en_el_limite"] == 1:
                agregar_aviso("A6", nivel, 0, f"La mejor flota del nivel {nivel} está en el límite: "
                                              "mirar también la siguiente.")
        for _, fila in del_nivel.iterrows():
            if fila["n_sin_pedidos"] > 0 or fila["_n_minimo"] < 2:
                agregar_aviso("A7", nivel, int(fila["nch"]), f"En el nivel {nivel}, flota {int(fila['nch'])}: "
                                                             f"{int(fila['n_sin_pedidos'])} réplicas sin pedidos.")

    actual = _fila(resumen, NIVEL_BASE, flota_actual)
    if actual is not None and actual["cumple"] == 1:
        agregar_aviso("A3", NIVEL_BASE, 0, "La flota actual ya cumple el criterio.")
    mejor_base = mejores.get(NIVEL_BASE)
    if mejor_base is not None and flota_peor is not None and mejor_base <= flota_peor:
        agregar_aviso("A4", NIVEL_BASE, 0, "El criterio puede ser demasiado laxo: revisar X e Y.")
    if flota_peor is None:
        agregar_aviso("A8", None, 0, f"No existe flota peor: la flota actual es {flota_actual}.")

    return [linea for *_, linea in sorted(avisos)]


# ---------------------------------------------------------------------------
# Escenarios y sensibilidad (§10.4)
# ---------------------------------------------------------------------------

def _escenarios(resumen: pd.DataFrame, mejor: int | None, flota_actual: int, flota_peor: int | None) -> pd.DataFrame:
    """Peor, actual y mejor, con el nivel base (§10.4, D-06, D-07)."""
    flotas = {"peor": flota_peor, "actual": flota_actual, "mejor": mejor}
    filas = []
    for escenario in ESCENARIOS:
        if escenario == "peor" and flota_peor is None:
            continue                                            # A8
        fila = _fila(resumen, NIVEL_BASE, flotas[escenario]) if flotas[escenario] is not None else None
        if fila is None:
            # Sin NCH*: todo vacío salvo el escenario y el nivel (§10.4, A1).
            filas.append({"escenario": escenario, "nivel": NIVEL_BASE})
        else:
            filas.append({"escenario": escenario, **fila[list(COLUMNAS_RESUMEN)].to_dict()})
    return pd.DataFrame(filas, columns=["escenario", *COLUMNAS_RESUMEN])


def _sensibilidad(resumen: pd.DataFrame, niveles: list[str], mejores: dict[str, int | None],
                  flota_actual: int) -> pd.DataFrame:
    """Para cada nivel, NCH* y cómo le va a la flota actual (§10.4, modelo §10.3)."""
    filas = []
    for nivel in niveles:
        actual = _fila(resumen, nivel, flota_actual)
        fila = {"nivel": nivel, "nch_mejor": mejores[nivel], "nch_actual": flota_actual,
                "actual_cumple": int(actual is not None and actual["cumple"] == 1)}
        for m in METRICAS_SENSIBILIDAD:
            fila[f"{m}_media"] = math.nan if actual is None else actual[f"{m}_media"]
        filas.append(fila)
    tabla = pd.DataFrame(filas)
    tabla["nch_mejor"] = tabla["nch_mejor"].astype("Int64")
    return tabla


def _escribir_csv(tabla: pd.DataFrame, ruta: Path) -> None:
    """Formato común de §9: enteros como enteros aunque haya celdas vacías (Int64), NaN como celda vacía."""
    tabla = tabla.drop(columns=["_n_minimo"], errors="ignore").copy()
    for columna in COLUMNAS_ENTERAS:
        if columna in tabla.columns:
            tabla[columna] = tabla[columna].astype("Int64")
    tabla.to_csv(ruta, index=False, encoding="utf-8", lineterminator="\n")


# ---------------------------------------------------------------------------
# Gráficos (§10.5, T-21)
# ---------------------------------------------------------------------------

def _figura() -> tuple[Figure, object]:
    figura = Figure(figsize=(ANCHO_CM / CM_POR_PULGADA, ALTO_CM / CM_POR_PULGADA), dpi=DPI)
    ejes = figura.subplots()
    ejes.xaxis.set_major_locator(MaxNLocator(integer=True))
    ejes.set_xlabel(EJE_NCH, fontsize=TAMANO_LETRA)
    ejes.tick_params(labelsize=TAMANO_LETRA)
    return figura, ejes


def _guardar(figura: Figure, ejes, ruta: Path) -> None:
    ejes.legend(fontsize=TAMANO_LETRA, frameon=False)
    figura.tight_layout()
    figura.savefig(ruta, dpi=DPI)


def _grafico_con_intervalo(resumen: pd.DataFrame, niveles: list[str], metrica: str, eje_y: str,
                           ruta: Path, umbral: tuple[float, str] | None) -> None:
    figura, ejes = _figura()
    for k, nivel in enumerate(niveles):
        datos = resumen[resumen["nivel"] == nivel]
        media = datos[f"{metrica}_media"].to_numpy(dtype=float)
        error = np.vstack([media - datos[f"{metrica}_ic_inf"].to_numpy(dtype=float),
                           datos[f"{metrica}_ic_sup"].to_numpy(dtype=float) - media])
        ejes.errorbar(datos["nch"], media, yerr=error, label=nivel, color=GRISES[k % len(GRISES)],
                      marker=MARCADORES[k % len(MARCADORES)], linestyle=LINEAS[k % len(LINEAS)],
                      markersize=3, linewidth=0.8, capsize=2, elinewidth=0.6)
    if umbral is not None:
        valor, etiqueta = umbral
        ejes.axhline(valor, color="0", linestyle=":", linewidth=0.8, label=etiqueta)
    ejes.set_ylabel(eje_y, fontsize=TAMANO_LETRA)
    _guardar(figura, ejes, ruta)


def _graficar(resumen: pd.DataFrame, niveles: list[str], criterio: Criterio, salida: Path) -> None:
    x, y = criterio.espera_total_max_min, criterio.abandono_max_pct
    _grafico_con_intervalo(resumen, niveles, "pet", "Espera total media (min)", salida / "fig_espera.png",
                           (x, f"X = {x:g} min"))
    _grafico_con_intervalo(resumen, niveles, "pa", "Abandono (%)", salida / "fig_abandono.png",
                           (y, f"Y = {y:g} %"))
    _grafico_con_intervalo(resumen, niveles, "pto", "Tiempo ocioso (%)", salida / "fig_ocio.png", None)

    # Recaudación: sin intervalos; el tipo de línea distingue REC de RECP y el marcador, el nivel.
    figura, ejes = _figura()
    for k, nivel in enumerate(niveles):
        datos = resumen[resumen["nivel"] == nivel]
        for metrica, linea in (("rec", "-"), ("recp", "--")):
            ejes.plot(datos["nch"], datos[f"{metrica}_media"], label=f"{metrica.upper()} · {nivel}",
                      color=GRISES[k % len(GRISES)], marker=MARCADORES[k % len(MARCADORES)], linestyle=linea,
                      markersize=3, linewidth=0.8)
    ejes.set_ylabel("Recaudación diaria (USD)", fontsize=TAMANO_LETRA)
    _guardar(figura, ejes, salida / "fig_recaudacion.png")


# ---------------------------------------------------------------------------
# Pantalla (§10.6)
# ---------------------------------------------------------------------------

def _mostrar(escenarios: pd.DataFrame, mejores: dict[str, int | None], avisos: list[str], salida: Path) -> None:
    columnas = ["escenario", "nch", "pet_media", "pa_media", "pto_media", "rec_media", "recp_media"]
    print("Escenarios (nivel base):")
    print(escenarios[columnas].to_string(index=False))
    print("\nMejor flota por nivel:")
    for nivel, mejor in mejores.items():
        print(f"  {nivel}: {'ninguna cumple' if mejor is None else mejor}")
    print("\nAvisos:")
    for linea in avisos or ["Sin avisos"]:
        print(f"  {linea}")
    print(f"\nArchivos en {salida}")
