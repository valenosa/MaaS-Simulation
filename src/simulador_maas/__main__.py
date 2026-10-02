"""Punto de entrada: `python -m simulador_maas <subcomando>`.

Implementa SDD §8.6: los subcomandos `experimento`, `corrida` y `analisis`, con la validación de sus opciones.
"""

from __future__ import annotations

import argparse
import math
import sys
from datetime import datetime

from simulador_maas.analisis import ejecutar_analisis
from simulador_maas.config import NIVEL_BASE, ErrorSimulador
from simulador_maas.experimento import ejecutar_corrida, ejecutar_experimento

CONFIG_POR_DEFECTO = "config/experimento.toml"
CARPETA_PRUEBAS = "results/pruebas"
NIVEL_POR_DEFECTO = NIVEL_BASE
REPLICA_POR_DEFECTO = 0


def _crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m simulador_maas",
        description="Simulador MaaS: cantidad óptima de choferes (docs/sdd.md, §8.6).")
    sub = parser.add_subparsers(dest="subcomando", required=True)

    p = sub.add_parser("experimento", help="Corre el experimento completo y escribe sus salidas (§8.3).")
    p.add_argument("--config", default=CONFIG_POR_DEFECTO, help=f"Configuración (por defecto, {CONFIG_POR_DEFECTO}).")
    p.add_argument("--salida", help=f"Carpeta del experimento (por defecto, {CARPETA_PRUEBAS}/AAAAMMDD-HHMMSS). "
                                    "Para la entrega, results/finales/<nombre>.")

    p = sub.add_parser("corrida", help="Simula una sola corrida, para depurarla o para la tabla de eventos (§8.4).")
    p.add_argument("--nch", type=int, required=True, help="Flota de la corrida.")
    p.add_argument("--nivel", default=NIVEL_POR_DEFECTO, help=f"Nivel de demanda (por defecto, {NIVEL_POR_DEFECTO}).")
    p.add_argument("--replica", type=int, default=REPLICA_POR_DEFECTO,
                   help=f"Réplica (por defecto, {REPLICA_POR_DEFECTO}).")
    p.add_argument("--config", default=CONFIG_POR_DEFECTO, help=f"Configuración (por defecto, {CONFIG_POR_DEFECTO}).")
    p.add_argument("--eventos", help="Archivo CSV donde se escribe el registro de eventos (§9.3).")

    p = sub.add_parser("analisis", help="Aplica el criterio a un experimento ya corrido, sin volver a simular (§10).")
    p.add_argument("--entrada", required=True, help="Carpeta de un experimento ya corrido.")
    p.add_argument("--espera-max", type=float, help="Umbral X (min); por defecto, el guardado en experimento.json.")
    p.add_argument("--abandono-max", type=float, help="Umbral Y (%%); por defecto, el guardado en experimento.json.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _crear_parser()
    args = parser.parse_args(argv)

    # Validación de las opciones, antes de hacer cualquier otra cosa (§8.6).
    if args.subcomando == "corrida":
        if args.nch < 1:
            parser.error(f"--nch vale {args.nch}: tiene que ser un entero ≥ 1.")
        if args.replica < 0:
            parser.error(f"--replica vale {args.replica}: tiene que ser un entero ≥ 0.")
    if args.subcomando == "analisis":
        # Los mismos rangos que en la configuración (§3.2).
        if args.espera_max is not None and not (math.isfinite(args.espera_max) and args.espera_max > 0):
            parser.error(f"--espera-max vale {args.espera_max}: tiene que ser > 0 y finito.")
        if args.abandono_max is not None and not 0 <= args.abandono_max <= 100:
            parser.error(f"--abandono-max vale {args.abandono_max}: tiene que estar entre 0 y 100.")

    try:
        if args.subcomando == "experimento":
            inicio = datetime.now().astimezone()
            salida = args.salida or f"{CARPETA_PRUEBAS}/{inicio:%Y%m%d-%H%M%S}"
            ejecutar_experimento(args.config, salida, inicio)
            print(f"Experimento terminado: {salida}")
        elif args.subcomando == "corrida":
            ejecutar_corrida(args.config, args.nch, args.nivel, args.replica, args.eventos)
        else:
            ejecutar_analisis(args.entrada, args.espera_max, args.abandono_max)
    except (ErrorSimulador, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
