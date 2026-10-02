"""Orquestación y línea de comandos: PR-03 (a), PR-04, PR-10 (f) y PR-11 (SDD §8, §9, §12.2)."""

import json
import math
from datetime import datetime

import pytest

from conftest import CONFIG_EXPERIMENTO, CONFIG_V1, dato
from simulador_maas import __main__ as cli
from simulador_maas import experimento
from simulador_maas.experimento import ErrorExperimento, ejecutar_experimento, preparar
from simulador_maas.motor import simular_corrida
from simulador_maas.aleatorios import crear_fuentes

INICIO = datetime(2026, 10, 2, 15, 30).astimezone()


def test_pr03a_numeros_aleatorios_comunes_entre_flotas():
    prep = preparar(CONFIG_V1)
    media_ia = prep.ref.niveles["base"].media_ia
    resultados = []
    for nch in (4, 9, 17):
        fuentes = crear_fuentes(prep.catalogo, prep.config.semilla_base, 0, media_ia, prep.config.velocidad_mph)
        resultados.append(simular_corrida(nch, "base", prep.parametros, fuentes)[0])
    assert len({r.nt for r in resultados}) == 1
    total = resultados[0].rec + resultados[0].recp
    assert all(math.isclose(r.rec + r.recp, total, rel_tol=1e-9) for r in resultados)


@pytest.fixture(scope="module")
def pr11(tmp_path_factory):
    """El experimento reducido de PR-11, corrido una vez para varias pruebas."""
    salida = tmp_path_factory.mktemp("pr11") / "experimento"
    ejecutar_experimento(dato("pr11_config.toml"), str(salida), INICIO)
    return salida


def test_pr11_corridas_csv_tiene_seis_filas(pr11):
    lineas = (pr11 / "corridas.csv").read_text(encoding="utf-8").splitlines()
    assert lineas[0] == ",".join(experimento.COLUMNAS_CORRIDAS)
    filas = [linea.split(",") for linea in lineas[1:]]
    assert len(filas) == 6                                          # 3 flotas × 2 réplicas
    assert [(f[0], f[1], f[2]) for f in filas] == [
        ("base", "8", "0"), ("base", "8", "1"), ("base", "9", "0"),
        ("base", "9", "1"), ("base", "10", "0"), ("base", "10", "1")]


def test_pr11_experimento_json(pr11):
    datos = json.loads((pr11 / "experimento.json").read_text(encoding="utf-8"))
    assert list(datos) == ["fecha", "versiones", "configuracion", "catalogo", "analisis", "referencias"]
    assert datos["fecha"] == INICIO.isoformat(timespec="seconds")
    assert datos["versiones"]["simulador_maas"] == "1.0.0"
    assert datos["catalogo"]["ruta"].endswith("tests/datos/../../config/fdp_v1.toml")
    assert "version = \"V1\"" in datos["catalogo"]["contenido"]
    assert datos["analisis"] == {"espera_total_max_min": 10.0, "abandono_max_pct": 5.0, "nivel_confianza": 0.95}
    ref = datos["referencias"]
    assert math.isclose(ref["e_s"], 20.0163854565, rel_tol=1e-9)
    assert list(ref["niveles"]) == ["base"]
    assert math.isclose(ref["niveles"]["base"]["carga"], 8.0065541826, rel_tol=1e-9)
    assert (ref["flota_actual"], ref["flota_peor"]) == (9, 8)
    assert ref["rango"] == [8, 10] and ref["flotas"] == [8, 9, 10]


def test_pr04_reproducibilidad(pr11, tmp_path):
    otra = tmp_path / "otra"
    ejecutar_experimento(dato("pr11_config.toml"), str(otra), INICIO)
    assert (otra / "corridas.csv").read_bytes() == (pr11 / "corridas.csv").read_bytes()


def test_carpeta_existente_no_se_sobrescribe(pr11):
    with pytest.raises(ErrorExperimento, match="ya existe"):
        ejecutar_experimento(dato("pr11_config.toml"), str(pr11), INICIO)


def test_pr10f_corrida_con_nch_0_da_error_antes_de_simular(monkeypatch):
    def no_deberia_llamarse(*args, **kwargs):
        raise AssertionError("la corrida no debería empezar")
    monkeypatch.setattr(cli, "ejecutar_corrida", no_deberia_llamarse)
    with pytest.raises(SystemExit) as salida:
        cli.main(["corrida", "--nch", "0", "--config", CONFIG_EXPERIMENTO])
    assert salida.value.code != 0


def test_corrida_con_nivel_inexistente_da_error(capsys):
    assert cli.main(["corrida", "--nch", "2", "--nivel", "pico", "--config", CONFIG_EXPERIMENTO]) != 0
    assert "pico" in capsys.readouterr().err


def test_pr01_corrida_escribe_la_tabla_de_eventos(tmp_path, capsys):
    """`corrida --nch 2 --eventos ARCHIVO` con la configuración de PR-01 reproduce §12.3 (§9.3)."""
    archivo = tmp_path / "eventos.csv"
    assert cli.main(["corrida", "--nch", "2", "--config", dato("pr01_config.toml"), "--eventos", str(archivo)]) == 0
    assert "pet: 4.25" in capsys.readouterr().out
    lineas = archivo.read_text(encoding="utf-8").splitlines()
    assert lineas[0] == ",".join(experimento.COLUMNAS_EVENTOS)
    assert len(lineas) == 1 + 14
    assert lineas[1] == "0,0.0,INICIO,,,estado inicial,2,0,0,0,1.0,HV;HV,HV;HV,0,0,0,0.0,0.0,0.0,0.0,0.0,0.0,0.0"
    assert lineas[6] == "5,4.0,TLL,,3,espera (TEE = 9),0,0,2,1,5.0,HV;HV,13.0;15.5,3,2,0,0.0,3.0,0.0,0.0,3.5,3.0,1.5"
    assert lineas[14] == ("13,34.0,TPS,2,5,termina; queda disponible,2,0,0,0,HV,HV;HV,HV;HV,5,4,1,"
                          "9.0,17.0,110.0,40.0,9.0,8.0,43.0")
