"""MCP server. stdio by default; `legalize-mx-mcp --http [--port 8000]` serves streamable HTTP."""

from __future__ import annotations

import argparse
import sys

from mcp.server.fastmcp import FastMCP

from legalize_mx_mcp import core

mcp = FastMCP(
    "legalize-mx",
    instructions=(
        "Legislación mexicana federal, estatal y municipal (SCJN, congresos, periódicos oficiales, "
        "portales municipales y DOF), con el historial de reformas en git. Empieza con buscar_norma "
        "para obtener el id; luego leer_norma, articulo, historial, diff o fuentes. Cita siempre la "
        "fuente oficial que devuelve fuentes(). Si una norma no tiene texto procesado, leer_norma con "
        "extraer_en_vivo=true baja el documento oficial. dof_del_dia consulta el DOF en vivo. "
        "Si una respuesta trae aviso_indice, avisa al usuario y ofrece actualizar_indice()."
    ),
)


@mcp.tool()
def buscar_norma(
    texto: str = "",
    estado: str | None = None,
    municipio: str | None = None,
    tipo: str | None = None,
    vigente: bool | None = None,
    con_texto: bool | None = None,
    fuente: str | None = None,
    limite: int = 20,
    desde: int = 0,
) -> dict:
    """Busca normas por texto (título y contenido) con filtros.

    estado: clave de 3 letras (JAL, NLE, CMX…) o "federal". municipio: nombre o clave INEGI.
    tipo: ley, ley_federal, ley_general, codigo, reglamento, bando, ley_de_ingresos, presupuesto,
    acuerdo, decreto, lineamientos, tratado, nom… vigente: true/false. con_texto: solo las que
    tienen texto procesado. fuente: "scjn" o el slug de una fuente (congreso-jal, dof, muni-html…).
    """
    return core.buscar_norma(
        texto, estado, municipio, tipo, vigente, con_texto, fuente, limite, desde
    )


@mcp.tool()
def leer_norma(
    id: str,
    fecha: str | None = None,
    desde: int = 0,
    max_caracteres: int = 60_000,
    extraer_en_vivo: bool = False,
) -> dict:
    """Texto de una norma: el vigente, o el que regía en `fecha` (AAAA-MM-DD).

    Textos largos vienen por partes: usa `desde` con el valor `siguiente_desde`. Si la norma solo
    está catalogada, devuelve sus documentos oficiales; con extraer_en_vivo=true los baja y extrae.
    """
    return core.leer_norma(id, fecha, desde, max_caracteres, extraer_en_vivo)


@mcp.tool()
def articulo(id: str, numero: str, fecha: str | None = None) -> dict:
    """Un artículo específico ("27", "3 bis", "primero"), vigente o a una fecha."""
    return core.articulo(id, numero, fecha)


@mcp.tool()
def historial(id: str) -> dict:
    """Reformas de una norma: fecha, tipo de cambio, decreto y artículos afectados."""
    return core.historial(id)


@mcp.tool()
def diff(id: str, fecha_a: str, fecha_b: str | None = None, max_caracteres: int = 40_000) -> dict:
    """Qué cambió entre la versión vigente en fecha_a y la de fecha_b (por omisión, la actual)."""
    return core.diff(id, fecha_a, fecha_b, max_caracteres)


@mcp.tool()
def fuentes(id: str) -> dict:
    """Enlaces oficiales a los documentos originales (para citar o verificar)."""
    return core.fuentes(id)


@mcp.tool()
def cobertura(estado: str | None = None, municipio: str | None = None) -> dict:
    """Qué hay y qué falta: normas por fuente y tipo, y la fuente municipal de cada municipio."""
    return core.cobertura(estado, municipio)


@mcp.tool()
def dof_del_dia(fecha: str | None = None, solo_normativas: bool = True) -> dict:
    """Lo que publicó hoy (o en `fecha`) el Diario Oficial de la Federación, en vivo."""
    return core.dof_del_dia(fecha, solo_normativas)


@mcp.tool()
def leer_nota_dof(codigo: str, desde: int = 0, max_caracteres: int = 60_000) -> dict:
    """Texto completo de una nota del DOF por su código (de dof_del_dia), en vivo."""
    return core.leer_nota_dof(codigo, desde, max_caracteres)


@mcp.tool()
def actualizar_indice() -> dict:
    """Baja ahora el índice más reciente publicado y lo usa. Úsalo cuando una respuesta traiga
    `aviso_indice`, o si buscas algo publicado en los últimos días."""
    return core.actualizar_indice()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--http", action="store_true", help="servir por HTTP en lugar de stdio")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    a = ap.parse_args()
    if a.http:
        if a.host not in ("127.0.0.1", "localhost", "::1"):
            print(
                f"AVISO: escuchando en {a.host}:{a.port} sin autenticación. Cualquiera que llegue a "
                "este puerto puede usar el servidor y hacer que descargue documentos de internet. "
                "Ponlo detrás de un proxy con autenticación o limita el acceso por red.",
                file=sys.stderr,
            )
        mcp.settings.host, mcp.settings.port = a.host, a.port
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
