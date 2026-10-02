"""Punto de entrada: `python -m simulador_maas <subcomando>`.

Implementa SDD §8.6: los subcomandos `experimento` y `corrida`, con la validación de sus opciones.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

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

    try:
        if args.subcomando == "experimento":
            inicio = datetime.now().astimezone()
            salida = args.salida or f"{CARPETA_PRUEBAS}/{inicio:%Y%m%d-%H%M%S}"
            ejecutar_experimento(args.config, salida, inicio)
            print(f"Experimento terminado: {salida}")
        else:
            ejecutar_corrida(args.config, args.nch, args.nivel, args.replica, args.eventos)
    except (ErrorSimulador, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
