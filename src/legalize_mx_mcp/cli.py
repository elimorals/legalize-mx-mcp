"""CLI: the same tools as the MCP server, printing JSON (or plain text for reading).

legalize-mx buscar "trabajo jornada" --estado federal
legalize-mx leer LFT [--fecha 2019-01-01] [--texto]
legalize-mx articulo LFT 123
legalize-mx historial LFT
legalize-mx diff LFT 2019-01-01 [2026-01-01]
legalize-mx fuentes LFT
legalize-mx cobertura [--estado JAL] [--municipio Zapopan]
legalize-mx dof [--fecha 2026-10-15] [--todas]
legalize-mx info
legalize-mx actualizar
"""

from __future__ import annotations

import argparse
import json
import sys

from legalize_mx_mcp import core


def _bool(v: str | None) -> bool | None:
    return None if v is None else v.lower() in ("1", "si", "sí", "true", "yes")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="legalize-mx", description="Legislación mexicana para agentes"
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("buscar")
    s.add_argument("texto", nargs="?", default="")
    s.add_argument("--estado")
    s.add_argument("--municipio")
    s.add_argument("--tipo")
    s.add_argument("--vigente")
    s.add_argument("--con-texto")
    s.add_argument("--fuente")
    s.add_argument("--limite", type=int, default=20)
    s.add_argument("--desde", type=int, default=0)

    s = sub.add_parser("leer")
    s.add_argument("id")
    s.add_argument("--fecha")
    s.add_argument("--desde", type=int, default=0)
    s.add_argument("--max", type=int, default=60_000)
    s.add_argument("--en-vivo", action="store_true", help="bajar y extraer el documento oficial")
    s.add_argument("--texto", action="store_true", help="imprimir solo el texto")

    s = sub.add_parser("articulo")
    s.add_argument("id")
    s.add_argument("numero")
    s.add_argument("--fecha")

    s = sub.add_parser("historial")
    s.add_argument("id")

    s = sub.add_parser("diff")
    s.add_argument("id")
    s.add_argument("fecha_a")
    s.add_argument("fecha_b", nargs="?")

    s = sub.add_parser("fuentes")
    s.add_argument("id")

    s = sub.add_parser("cobertura")
    s.add_argument("--estado")
    s.add_argument("--municipio")

    s = sub.add_parser("dof")
    s.add_argument("--fecha")
    s.add_argument("--todas", action="store_true", help="incluir avisos, convocatorias, etc.")

    s = sub.add_parser("nota-dof")
    s.add_argument("codigo")

    sub.add_parser("info")
    sub.add_parser("actualizar", help="bajar el índice más reciente")

    a = ap.parse_args(argv)
    if a.cmd == "buscar":
        out = core.buscar_norma(
            a.texto,
            a.estado,
            a.municipio,
            a.tipo,
            _bool(a.vigente),
            _bool(a.con_texto),
            a.fuente,
            a.limite,
            a.desde,
        )
    elif a.cmd == "leer":
        out = core.leer_norma(a.id, a.fecha, a.desde, a.max, a.en_vivo)
        if a.texto and out.get("texto"):
            print(out["texto"])
            return 0
    elif a.cmd == "articulo":
        out = core.articulo(a.id, a.numero, a.fecha)
    elif a.cmd == "historial":
        out = core.historial(a.id)
    elif a.cmd == "diff":
        out = core.diff(a.id, a.fecha_a, a.fecha_b)
    elif a.cmd == "fuentes":
        out = core.fuentes(a.id)
    elif a.cmd == "cobertura":
        out = core.cobertura(a.estado, a.municipio)
    elif a.cmd == "dof":
        out = core.dof_del_dia(a.fecha, not a.todas)
    elif a.cmd == "nota-dof":
        out = core.leer_nota_dof(a.codigo)
    elif a.cmd == "actualizar":
        out = core.actualizar_indice()
    else:
        out = core.info()
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2, default=str)
    print()
    return 1 if isinstance(out, dict) and out.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
