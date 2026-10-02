"""Análisis: PR-09 y PR-11 completa (SDD §10, §12.2, §12.5)."""

import json
import shutil
from datetime import datetime

import pandas as pd
import pytest

from conftest import DATOS, dato
from simulador_maas import __main__ as cli
from simulador_maas.analisis import ErrorAnalisis, ejecutar_analisis, nombre_carpeta
from simulador_maas.experimento import ejecutar_experimento

ARCHIVOS_ANALISIS = {"parametros.json", "resumen.csv", "escenarios.csv", "sensibilidad.csv", "avisos.txt",
                     "fig_espera.png", "fig_abandono.png", "fig_ocio.png", "fig_recaudacion.png"}


@pytest.fixture
def pr09(tmp_path):
    """Copia de la carpeta armada a mano, para que el análisis no escriba en tests/datos/."""
    carpeta = tmp_path / "pr09"
    shutil.copytree(DATOS / "pr09_experimento", carpeta)
    return carpeta


def _leer(ruta):
    return pd.read_csv(ruta, dtype={"nivel": str})


# PR-09 esperado (§12.5), con t(0,975; 2) = 4,3026527:
# flota: (media PET, IC PET, media PA, IC PA, cumple, en el límite)
PR09_ESPERADO = {
    2: (22, (17.0317, 26.9683), 12, (7.0317, 16.9683), 0, 0),
    3: (10, (5.0317, 14.9683), 5, (2.5159, 7.4841), 1, 1),
    4: (5, (5, 5), 0, (0, 0), 1, 0),
    5: (11, (11, 11), 0, (0, 0), 0, 0),
}


def test_pr09_resumen(pr09):
    salida = ejecutar_analisis(str(pr09))
    assert salida.name == "analisis_X10_Y5"
    assert {p.name for p in salida.iterdir()} == ARCHIVOS_ANALISIS
    resumen = _leer(salida / "resumen.csv")
    assert list(resumen["nch"]) == [2, 3, 4, 5]
    for _, fila in resumen.iterrows():
        pet, ic_pet, pa, ic_pa, cumple, limite = PR09_ESPERADO[fila["nch"]]
        assert fila["pet_media"] == pytest.approx(pet) and fila["pa_media"] == pytest.approx(pa)
        assert (fila["pet_ic_inf"], fila["pet_ic_sup"]) == pytest.approx(ic_pet, abs=1e-4)
        assert (fila["pa_ic_inf"], fila["pa_ic_sup"]) == pytest.approx(ic_pa, abs=1e-4)
        assert (fila["cumple"], fila["en_el_limite"]) == (cumple, limite)
    # Enteros como enteros (§9).
    primera = (salida / "resumen.csv").read_text(encoding="utf-8").splitlines()[1]
    assert primera.startswith("base,2,3,0,")


def test_pr09_escenarios_avisos_y_sensibilidad(pr09):
    salida = ejecutar_analisis(str(pr09))
    escenarios = _leer(salida / "escenarios.csv")
    assert list(escenarios["escenario"]) == ["peor", "actual", "mejor"]
    assert list(escenarios["nch"]) == [2, 3, 3]

    avisos = (salida / "avisos.txt").read_text(encoding="utf-8").splitlines()
    assert [linea.split()[:2] for linea in avisos] == [["A3", "[base]"], ["A5", "[base]"], ["A6", "[base]"]]
    assert "flota 5" in avisos[1]

    sensibilidad = _leer(salida / "sensibilidad.csv")
    assert len(sensibilidad) == 1
    fila = sensibilidad.iloc[0]
    assert (fila["nivel"], fila["nch_mejor"], fila["nch_actual"], fila["actual_cumple"]) == ("base", 3, 3, 1)

    parametros = json.loads((salida / "parametros.json").read_text(encoding="utf-8"))
    assert parametros == {"espera_total_max_min": 10, "abandono_max_pct": 5, "nivel_confianza": 0.95}


def test_umbral_desde_la_linea_de_comandos_sin_mejor_flota(pr09):
    """Otro X sin volver a simular (D-10). Sin NCH*: aviso A1 y la fila mejor vacía salvo escenario y nivel (§10.4)."""
    assert cli.main(["analisis", "--entrada", str(pr09), "--espera-max", "1"]) == 0
    salida = pr09 / "analisis_X1_Y5"
    avisos = (salida / "avisos.txt").read_text(encoding="utf-8").splitlines()
    assert avisos[0].startswith("A1 [base]")
    mejor = (salida / "escenarios.csv").read_text(encoding="utf-8").splitlines()[3].split(",")
    assert mejor[:2] == ["mejor", "base"] and all(celda == "" for celda in mejor[2:])
    assert _leer(salida / "sensibilidad.csv")["nch_mejor"].isna().all()


def test_nombre_de_la_carpeta():
    assert nombre_carpeta(10.0, 5.0) == "analisis_X10_Y5"
    assert nombre_carpeta(7.5, 5) == "analisis_X7.5_Y5"


def test_experimento_incompleto_da_error(pr09):
    (pr09 / "corridas.csv").unlink()
    with pytest.raises(ErrorAnalisis, match="incompleto"):
        ejecutar_analisis(str(pr09))


def test_pr11_completa_de_punta_a_punta(tmp_path):
    salida = tmp_path / "pr11"
    ejecutar_experimento(dato("pr11_config.toml"), str(salida), datetime.now().astimezone())
    analisis = ejecutar_analisis(str(salida))
    assert {p.name for p in analisis.iterdir()} == ARCHIVOS_ANALISIS
    assert list(_leer(analisis / "resumen.csv")["nch"]) == [8, 9, 10]
