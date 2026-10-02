"""Motor de simulación: una corrida, evento a evento.

Implementa SDD §6 (§6.1 a §6.10) y §7 (invariantes), con el registro de eventos de §9.3
y T-02, T-04 a T-07, T-13 y T-18. No conoce el criterio de decisión ni otras corridas (D-10).
"""

from __future__ import annotations

import math

from simulador_maas.aleatorios import Fuentes
from simulador_maas.config import ErrorSimulador
from simulador_maas.entidades import HV, Cliente, EstadoCorrida, ParametrosCorrida, ResultadoCorrida

TLL, TLC, TPS = "TLL", "TLC", "TPS"
INICIO = "INICIO"

# Tolerancia relativa de INV-06 e INV-F (§7).
TOLERANCIA_AREAS = 1e-9

# Decimales del TEE en el detalle del registro de eventos (§9.3).
DECIMALES_TEE = 4


class ErrorInvariante(ErrorSimulador):
    """No se cumple un invariante de §7."""


def simular_corrida(nch: int, nivel: str, parametros: ParametrosCorrida, fuentes: Fuentes,
                    registrar_eventos: bool = False) -> tuple[ResultadoCorrida, list[dict]]:
    """Simula una corrida (§6.1). Devuelve el resultado de §4.7 y el registro de §9.3 (vacío si no se pide)."""
    tf = parametros.horizonte_min
    e = EstadoCorrida.inicial(nch)
    registro: list[dict] = []

    # Inicialización (§6.2).
    ia = fuentes.sortear_ia()
    e.tll = ia if ia < tf else HV
    if registrar_eventos:
        registro.append(_fila(e, 0, INICIO, None, None, "estado inicial"))

    # Ciclo principal (§6.3).
    while _hay_eventos_pendientes(e):
        tipo, i, t_evento = _proximo_evento(e)
        _acumular_areas(e, e.t_anterior, t_evento, tf)
        t_previo = e.t
        e.t = t_evento
        e.t_anterior = t_evento
        if tipo == TPS:
            cliente, detalle = _rutina_tps(e, i)
            chofer = i + 1
        elif tipo == TLC:
            cliente, detalle = _rutina_tlc(e, i)
            chofer = i + 1
        else:
            cliente, detalle, i_asignado = _rutina_tll(e, parametros, fuentes)
            chofer = None if i_asignado is None else i_asignado + 1
        e.n_eventos += 1
        e.ns_max = max(e.ns_max, e.ns)
        if parametros.verificar_invariantes:
            _verificar_invariantes(e, tf, t_previo, _describir(e.n_eventos, tipo, chofer))
        if registrar_eventos:
            registro.append(_fila(e, e.n_eventos, tipo, chofer, cliente, detalle))

    _cerrar_horizonte(e, tf)
    if parametros.verificar_invariantes:
        _verificar_invariante_final(e, tf)
    return _calcular_metricas(e, nivel, tf), registro


# ---------------------------------------------------------------------------
# Próximo evento y áreas (§6.4, §6.5, §6.9)
# ---------------------------------------------------------------------------

def _hay_eventos_pendientes(e: EstadoCorrida) -> bool:
    return e.tll != HV or any(x != HV for x in e.tlc) or any(x != HV for x in e.tps)


def _proximo_evento(e: EstadoCorrida) -> tuple[str, int | None, float]:
    """Menor instante de la TEF; ante un empate exacto, TPS, después TLC y por último TLL,
    y dentro del mismo tipo el chofer de menor número (§6.4, D-08, T-06)."""
    min_tps = min(e.tps)
    min_tlc = min(e.tlc)
    t_evento = min(e.tll, min_tlc, min_tps)
    if min_tps == t_evento:
        return TPS, e.tps.index(t_evento), t_evento
    if min_tlc == t_evento:
        return TLC, e.tlc.index(t_evento), t_evento
    return TLL, None, t_evento


def _acumular_areas(e: EstadoCorrida, desde: float, hasta: float, tf: float) -> None:
    """Suma Ncd, Ncc y Nco por el tramo transcurrido, cortado en TF (§6.5, D-04)."""
    a = min(desde, tf)
    b = min(hasta, tf)
    if b > a:
        dt = b - a
        e.sto += e.ncd * dt
        e.stc += e.ncc * dt
        e.stv += e.nco * dt


def _cerrar_horizonte(e: EstadoCorrida, tf: float) -> None:
    """Acumula el tramo entre el último evento y TF, si quedó alguno (§6.9)."""
    _acumular_areas(e, e.t_anterior, tf, tf)


# ---------------------------------------------------------------------------
# Rutinas de evento (§6.6 a §6.8)
# ---------------------------------------------------------------------------

def _rutina_tll(e: EstadoCorrida, parametros: ParametrosCorrida,
                fuentes: Fuentes) -> tuple[int, str, int | None]:
    """Llega un pedido (§6.6, modelo §8.1). Devuelve el cliente, el detalle y el chofer asignado."""
    # 1. Se crea el cliente.
    e.nt += 1
    tb, d, dem, tv, tar = fuentes.sortear_atributos()
    c = Cliente(id=e.nt, t_llegada=e.t, tb=tb, d=d, dem=dem, tv=tv, tar=tar)

    # 2. Se agenda la próxima llegada.
    ia = fuentes.sortear_ia()
    e.tll = e.t + ia if e.t + ia < parametros.horizonte_min else HV

    # 3. Asignación, espera o arrepentimiento.
    if e.ncd >= 1:
        i = next(j for j in range(e.nch) if e.tlc[j] == HV and e.tps[j] == HV)   # S-04
        c.t_asignacion = e.t
        e.nat += 1
        e.suma_espera_cola += 0                                                  # atendido sin esperar
        e.ncd -= 1
        e.ncc += 1
        e.ca[i] = c
        e.tlc[i] = e.t + c.tb
        return c.id, f"asignado al chofer {i + 1}", i

    tee = (e.ns + 1) * parametros.e_s / e.nch + parametros.e_tb                # D-02; Ns antes de sumar a c
    if tee > parametros.umbral_tolerancia_min:
        e.narr += 1
        e.recp += c.tar                                                         # c sale del sistema
        return c.id, f"se arrepiente (TEE = {_formatear_tee(tee)})", None
    e.cola.append(c)
    return c.id, f"espera (TEE = {_formatear_tee(tee)})", None


def _rutina_tlc(e: EstadoCorrida, i: int) -> tuple[int, str]:
    """El chofer i + 1 llega a buscar al cliente (§6.7, modelo §8.2)."""
    c = e.ca[i]
    c.t_recogida = e.t
    e.suma_espera_total += e.t - c.t_llegada
    e.ncc -= 1
    e.nco += 1
    e.tlc[i] = HV
    e.tps[i] = e.t + c.tv
    return c.id, "recogido"


def _rutina_tps(e: EstadoCorrida, i: int) -> tuple[int, str]:
    """El chofer i + 1 termina el viaje (§6.8, modelo §8.3)."""
    c = e.ca[i]
    e.rec += c.tar                                                              # c sale del sistema
    e.tps[i] = HV
    e.ca[i] = None
    if e.ns >= 1:
        c2 = e.cola.popleft()                                                   # orden de llegada, S-04
        c2.t_asignacion = e.t
        e.suma_espera_cola += e.t - c2.t_llegada
        e.nat += 1
        e.nco -= 1
        e.ncc += 1
        e.ca[i] = c2
        e.tlc[i] = e.t + c2.tb
        return c.id, f"termina; toma al cliente {c2.id}"
    e.nco -= 1
    e.ncd += 1
    return c.id, "termina; queda disponible"


# ---------------------------------------------------------------------------
# Métricas (§6.10)
# ---------------------------------------------------------------------------

def _calcular_metricas(e: EstadoCorrida, nivel: str, tf: float) -> ResultadoCorrida:
    sin_pedidos = e.nt == 0
    if sin_pedidos:
        pet = pec = pa = math.nan                                               # indefinido, nunca 0
    else:
        pet = e.suma_espera_total / e.nat
        pec = e.suma_espera_cola / e.nat
        pa = e.narr / e.nt * 100
    capacidad = e.nch * tf
    return ResultadoCorrida(
        nivel=nivel, nch=e.nch, nt=e.nt, narr=e.narr, nat=e.nat,
        suma_espera_cola=e.suma_espera_cola, suma_espera_total=e.suma_espera_total,
        rec=e.rec, recp=e.recp, sto=e.sto, stc=e.stc, stv=e.stv,
        pet=pet, pec=pec, pa=pa,
        pto=e.sto / capacidad * 100, ptc=e.stc / capacidad * 100, ptv=e.stv / capacidad * 100,
        rpc=e.rec / e.nch,
        t_ultimo_evento=e.t, n_eventos=e.n_eventos, ns_max=e.ns_max, sin_pedidos=sin_pedidos,
    )


# ---------------------------------------------------------------------------
# Invariantes (§7)
# ---------------------------------------------------------------------------

def _verificar_invariantes(e: EstadoCorrida, tf: float, t_previo: float, evento: str) -> None:
    """INV-01 a INV-09, después de cada evento (§7, T-13)."""
    def falla(invariante: str, detalle: str) -> ErrorInvariante:
        return ErrorInvariante(f"No se cumple {invariante} después del evento {evento}, en T = {e.t!r}: "
                               f"{detalle}.\nEstado: {_estado_completo(e)}")

    if e.ncd + e.ncc + e.nco != e.nch:
        raise falla("INV-01", f"Ncd + Ncc + Nco = {e.ncd + e.ncc + e.nco} ≠ NCH = {e.nch}")
    if e.ns > 0 and e.ncd != 0:
        raise falla("INV-02", f"Ns = {e.ns} > 0 con Ncd = {e.ncd}")
    en_camino = sum(1 for x in e.tlc if x != HV)
    ocupados = sum(1 for x in e.tps if x != HV)
    if e.ncc != en_camino or e.nco != ocupados:
        raise falla("INV-03", f"Ncc = {e.ncc} y Nco = {e.nco}, pero hay {en_camino} TLC y {ocupados} TPS pendientes")
    for i in range(e.nch):
        if e.tlc[i] != HV and e.tps[i] != HV:
            raise falla("INV-03", f"el chofer {i + 1} tiene TLC y TPS pendientes a la vez")
        if (e.ca[i] is not None) != (e.tlc[i] != HV or e.tps[i] != HV):
            raise falla("INV-04", f"CA({i + 1}) = {e.ca[i]} no coincide con TLC y TPS")
    if e.nt != e.nat + e.narr + e.ns:
        raise falla("INV-05", f"NT = {e.nt} ≠ NAT + NARR + Ns = {e.nat + e.narr + e.ns}")
    area = e.sto + e.stc + e.stv
    if not math.isclose(area, e.nch * min(e.t, tf), rel_tol=TOLERANCIA_AREAS):
        raise falla("INV-06", f"STO + STC + STV = {area!r} ≠ NCH × min(T, TF) = {e.nch * min(e.t, tf)!r}")
    if e.t < t_previo:
        raise falla("INV-07", f"T retrocedió desde {t_previo!r}")
    if min(e.tll, min(e.tlc), min(e.tps)) < e.t:
        raise falla("INV-07", "hay un evento pendiente anterior a T")
    if not (e.tll == HV or e.tll < tf):
        raise falla("INV-08", f"TLL = {e.tll!r} no es HV ni menor que TF = {tf!r}")
    for c in e.cola:
        if c.t_asignacion is not None or not c.t_llegada <= e.t:
            raise falla("INV-09", f"el cliente {c.id} de la cola tiene asignación o llegó después de T")
    for i, c in enumerate(e.ca):
        if c is None:
            continue
        if c.t_asignacion is None or not c.t_llegada <= c.t_asignacion <= e.t:
            raise falla("INV-09", f"CA({i + 1}) = cliente {c.id} no cumple t_llegada ≤ t_asignacion ≤ T")
        if e.tps[i] != HV and (c.t_recogida is None or not c.t_asignacion <= c.t_recogida <= e.t):
            raise falla("INV-09", f"CA({i + 1}) = cliente {c.id} no cumple t_asignacion ≤ t_recogida ≤ T")


def _verificar_invariante_final(e: EstadoCorrida, tf: float) -> None:
    """INV-F, una vez, después del cierre del horizonte (§7)."""
    def falla(detalle: str) -> ErrorInvariante:
        return ErrorInvariante(f"No se cumple INV-F al terminar la corrida, en T = {e.t!r}: {detalle}.\n"
                               f"Estado: {_estado_completo(e)}")

    if e.ns != 0:
        raise falla(f"Ns = {e.ns}")
    if e.nt != e.nat + e.narr:
        raise falla(f"NT = {e.nt} ≠ NAT + NARR = {e.nat + e.narr}")
    if any(x != HV for x in e.tlc) or any(x != HV for x in e.tps):
        raise falla("quedan eventos pendientes en TLC o TPS")
    if any(c is not None for c in e.ca):
        raise falla("quedan clientes asignados")
    area = e.sto + e.stc + e.stv
    if not math.isclose(area, e.nch * tf, rel_tol=TOLERANCIA_AREAS):
        raise falla(f"STO + STC + STV = {area!r} ≠ NCH × TF = {e.nch * tf!r}")


def _describir(n: int, tipo: str, chofer: int | None) -> str:
    return f"n° {n} ({tipo})" if tipo == TLL else f"n° {n} ({tipo}({chofer}))"


def _estado_completo(e: EstadoCorrida) -> str:
    return (f"T={e.t!r}, TLL={e.tll!r}, TLC={e.tlc}, TPS={e.tps}, "
            f"CA={[None if c is None else c.id for c in e.ca]}, Ncd={e.ncd}, Ncc={e.ncc}, Nco={e.nco}, "
            f"cola={[c.id for c in e.cola]}, NT={e.nt}, NAT={e.nat}, NARR={e.narr}, "
            f"SEC={e.suma_espera_cola!r}, SET={e.suma_espera_total!r}, REC={e.rec!r}, RECP={e.recp!r}, "
            f"STO={e.sto!r}, STC={e.stc!r}, STV={e.stv!r}")


# ---------------------------------------------------------------------------
# Registro de eventos (§9.3, T-18)
# ---------------------------------------------------------------------------

def _formatear_tee(tee: float) -> str:
    """TEE con 4 decimales, sin ceros sobrantes ni punto final: 9 → '9', 9,5 → '9.5' (§9.3)."""
    return f"{tee:.{DECIMALES_TEE}f}".rstrip("0").rstrip(".")


def _fila(e: EstadoCorrida, n: int, evento: str, chofer: int | None, cliente: int | None,
          detalle: str) -> dict:
    """Una fila del registro, con el estado después del evento, en su forma en memoria (§9.3)."""
    return {
        "n": n, "t": e.t, "evento": evento, "chofer": chofer, "cliente": cliente, "detalle": detalle,
        "ncd": e.ncd, "ncc": e.ncc, "nco": e.nco, "ns": e.ns,
        "tll": e.tll, "tlc": list(e.tlc), "tps": list(e.tps),
        "nt": e.nt, "nat": e.nat, "narr": e.narr,
        "suma_espera_cola": e.suma_espera_cola, "suma_espera_total": e.suma_espera_total,
        "rec": e.rec, "recp": e.recp, "sto": e.sto, "stc": e.stc, "stv": e.stv,
    }
