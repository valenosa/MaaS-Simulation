"""Motor: PR-01, PR-02, PR-05 a PR-07 y PR-10 (c) (SDD §6, §7, §12.2 a §12.4)."""

import math

import pytest

from conftest import CONFIG_V1, Preparado, dato
from simulador_maas.aleatorios import ErrorFDP
from simulador_maas.entidades import HV
from simulador_maas.motor import simular_corrida

# ---------------------------------------------------------------------------
# PR-01: corrida calculada a mano (§12.3)
# ---------------------------------------------------------------------------

# Eventos y estado, después de cada evento:
# n, T, evento, chofer (en TLC y TPS), Ncd, Ncc, Nco, Ns, TLL, TLC(1), TLC(2), TPS(1), TPS(2)
PR01_EVENTOS = [
    (0, 0, "INICIO", None, 2, 0, 0, 0, 1, HV, HV, HV, HV),
    (1, 1, "TLL", None, 1, 1, 0, 0, 2.5, 3, HV, HV, HV),
    (2, 2.5, "TLL", None, 0, 2, 0, 0, 4, 3, 3.5, HV, HV),
    (3, 3, "TLC", 1, 0, 1, 1, 0, 4, HV, 3.5, 13, HV),
    (4, 3.5, "TLC", 2, 0, 0, 2, 0, 4, HV, HV, 13, 15.5),
    (5, 4, "TLL", None, 0, 0, 2, 1, 5, HV, HV, 13, 15.5),
    (6, 5, "TLL", None, 0, 0, 2, 1, 20, HV, HV, 13, 15.5),
    (7, 13, "TPS", 1, 0, 1, 1, 0, 20, 16, HV, HV, 15.5),
    (8, 15.5, "TPS", 2, 1, 1, 0, 0, 20, 16, HV, HV, HV),
    (9, 16, "TLC", 1, 1, 0, 1, 0, 20, HV, HV, 29, HV),
    (10, 20, "TLL", None, 0, 1, 1, 0, HV, HV, 22, 29, HV),
    (11, 22, "TLC", 2, 0, 0, 2, 0, HV, HV, HV, 29, 34),
    (12, 29, "TPS", 1, 1, 0, 1, 0, HV, HV, HV, HV, 34),
    (13, 34, "TPS", 2, 2, 0, 0, 0, HV, HV, HV, HV, HV),
]

# Contadores y acumuladores, después de cada evento:
# n, NT, NAT, NARR, SEC, SET, REC, RECP, STO, STC, STV
PR01_ACUMULADORES = [
    (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (1, 1, 1, 0, 0, 0, 0, 0, 2, 0, 0),
    (2, 2, 2, 0, 0, 0, 0, 0, 3.5, 1.5, 0),
    (3, 2, 2, 0, 0, 2, 0, 0, 3.5, 2.5, 0),
    (4, 2, 2, 0, 0, 3, 0, 0, 3.5, 3, 0.5),
    (5, 3, 2, 0, 0, 3, 0, 0, 3.5, 3, 1.5),
    (6, 4, 2, 1, 0, 3, 0, 40, 3.5, 3, 3.5),
    (7, 4, 3, 1, 9, 3, 10, 40, 3.5, 3, 19.5),
    (8, 4, 3, 1, 9, 3, 30, 40, 3.5, 5.5, 22),
    (9, 4, 3, 1, 9, 15, 30, 40, 4, 6, 22),
    (10, 5, 4, 1, 9, 15, 30, 40, 8, 6, 26),
    (11, 5, 4, 1, 9, 17, 30, 40, 8, 8, 28),
    (12, 5, 4, 1, 9, 17, 60, 40, 8, 8, 42),
    (13, 5, 4, 1, 9, 17, 110, 40, 9, 8, 43),
]

TOL = 1e-9


def cerca(valor, esperado):
    """Igualdad con tolerancia absoluta de 10⁻⁹ en los reales; HV se compara exacto (§12.3)."""
    return valor == pytest.approx(esperado, abs=TOL)


@pytest.fixture(scope="module")
def pr01():
    p = Preparado(dato("pr01_config.toml"))
    assert p.ref.e_tb == 2 and p.ref.e_d == 12 and p.ref.e_s == 14
    return simular_corrida(2, "base", p.parametros, p.fuentes(), registrar_eventos=True)


def test_pr01_tabla_de_eventos_y_estado(pr01):
    _, registro = pr01
    assert len(registro) == len(PR01_EVENTOS)
    for fila, (n, t, evento, chofer, ncd, ncc, nco, ns, tll, tlc1, tlc2, tps1, tps2) in zip(registro, PR01_EVENTOS):
        assert fila["n"] == n and cerca(fila["t"], t) and fila["evento"] == evento, fila
        if evento in ("TLC", "TPS"):
            assert fila["chofer"] == chofer, fila
        assert (fila["ncd"], fila["ncc"], fila["nco"], fila["ns"]) == (ncd, ncc, nco, ns), fila
        assert cerca(fila["tll"], tll), fila
        assert cerca(fila["tlc"], [tlc1, tlc2]) and cerca(fila["tps"], [tps1, tps2]), fila


def test_pr01_contadores_y_acumuladores(pr01):
    _, registro = pr01
    claves = ("nt", "nat", "narr", "suma_espera_cola", "suma_espera_total", "rec", "recp", "sto", "stc", "stv")
    for fila, (n, *esperados) in zip(registro, PR01_ACUMULADORES):
        assert fila["n"] == n
        for clave, esperado in zip(claves, esperados):
            assert cerca(fila[clave], esperado), (n, clave, fila[clave], esperado)


def test_pr01_valores_finales(pr01):
    r, _ = pr01
    assert (r.nt, r.nat, r.narr) == (5, 4, 1)
    assert cerca(r.sto + r.stc + r.stv, 60)
    assert cerca(r.pet, 4.25) and cerca(r.pec, 2.25) and cerca(r.pa, 20)
    assert cerca(r.pto, 15) and cerca(r.ptc, 8 / 60 * 100) and cerca(r.ptv, 43 / 60 * 100)
    assert cerca(r.rec + r.recp, 150) and cerca(r.rpc, 55)
    assert (r.n_eventos, r.ns_max) == (13, 1) and cerca(r.t_ultimo_evento, 34)
    assert not r.sin_pedidos


def test_pr01_tipos_del_registro_en_memoria(pr01):
    """Forma en memoria del registro (§9.3): reales, enteros, math.inf para HV y None para lo vacío."""
    _, registro = pr01
    inicio, tll = registro[0], registro[1]
    assert inicio["chofer"] is None and inicio["cliente"] is None and inicio["detalle"] == "estado inicial"
    assert isinstance(inicio["t"], float) and isinstance(inicio["sto"], float) and inicio["tlc"] == [math.inf] * 2
    assert tll["chofer"] == 1 and tll["cliente"] == 1 and tll["detalle"] == "asignado al chofer 1"
    assert registro[5]["detalle"] == "espera (TEE = 9)"
    assert registro[6]["detalle"] == "se arrepiente (TEE = 16)"
    assert registro[7]["detalle"] == "termina; toma al cliente 3" and registro[7]["cliente"] == 1
    assert registro[8]["detalle"] == "termina; queda disponible"


# ---------------------------------------------------------------------------
# PR-02: invariantes con el catálogo V1 (§12.2)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("nch", [1, 4, 9, 17])
@pytest.mark.parametrize("r", [0, 1, 2])
def test_pr02_ninguna_corrida_viola_un_invariante(nch, r):
    p = Preparado(CONFIG_V1)
    resultado, registro = simular_corrida(nch, "base", p.parametros, p.fuentes(r))
    assert registro == []
    assert resultado.nt == resultado.nat + resultado.narr and resultado.nt > 0


# ---------------------------------------------------------------------------
# PR-05 a PR-07: casos borde (§12.4)
# ---------------------------------------------------------------------------

def test_pr05_dia_sin_pedidos():
    p = Preparado(dato("pr05_config.toml"))
    r, _ = simular_corrida(3, "base", p.parametros, p.fuentes())
    assert r.nt == 0 and r.sin_pedidos
    assert math.isnan(r.pet) and math.isnan(r.pec) and math.isnan(r.pa)
    assert cerca(r.sto, 90) and cerca(r.pto, 100) and r.rec == 0
    assert r.n_eventos == 0 and r.t_ultimo_evento == 0


def test_pr06_eventos_simultaneos_primero_el_fin_de_viaje():
    p = Preparado(dato("pr06_config.toml"))
    r, registro = simular_corrida(1, "base", p.parametros, p.fuentes(), registrar_eventos=True)
    assert (r.nt, r.nat, r.narr) == (2, 2, 0)
    assert cerca(r.rec, 20) and cerca(r.sto, 24) and cerca(r.stv, 6) and r.n_eventos == 6
    # En el instante 4 coinciden el fin del primer viaje y la llegada del segundo pedido.
    assert [(f["t"], f["evento"]) for f in registro[3:5]] == [(4, "TPS"), (4, "TLL")]


def test_pr07_tee_igual_a_u_espera():
    p = Preparado(dato("pr07_config.toml"))
    r, _ = simular_corrida(1, "base", p.parametros, p.fuentes())
    assert (r.narr, r.nat) == (0, 2)
    assert cerca(r.suma_espera_cola, 2) and cerca(r.suma_espera_total, 2)


def test_pr07_con_u_2999_se_arrepiente():
    p = Preparado(dato("pr07_config_u2999.toml"))
    r, _ = simular_corrida(1, "base", p.parametros, p.fuentes())
    assert (r.narr, r.nat) == (1, 1) and cerca(r.recp, 10)


# ---------------------------------------------------------------------------
# PR-10 (c): valor negativo de una FDP durante la corrida (§5.4, T-10)
# ---------------------------------------------------------------------------

class _Espia:
    """Cuenta los pedidos sorteados, para saber en cuál falló la corrida."""

    def __init__(self, fuentes):
        self._fuentes = fuentes
        self.pedidos = 0

    def sortear_ia(self):
        return self._fuentes.sortear_ia()

    def sortear_atributos(self):
        self.pedidos += 1
        return self._fuentes.sortear_atributos()


def test_pr10c_busqueda_negativa_da_error_en_el_primer_pedido():
    p = Preparado(dato("pr10c_config.toml"))
    assert p.ref.e_s == 2                                   # pasa los controles de §3.4
    espia = _Espia(p.fuentes())
    with pytest.raises(ErrorFDP, match="TB"):
        simular_corrida(1, "base", p.parametros, espia)
    assert espia.pedidos == 1                               # el primer pedido, que llega en T = 1
