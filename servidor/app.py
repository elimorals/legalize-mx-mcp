"""The hosted MCP: the same server as `legalize-mx-mcp --http`, as an ASGI app for Vercel.

POST /mcp            streamable HTTP, stateless (each request stands alone)
GET  /api/<tool>     the same tools as JSON for the website, e.g. /api/buscar_norma?texto=jornada

The build (vercel.json) copies src/legalize_mx_mcp next to this file and runs descargar_indice.py,
so the index ships inside the function. Locally: copy the package the same way, then
`python descargar_indice.py && uvicorn app:app`.
"""

from __future__ import annotations

import inspect
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))  # the package is copied next to this file
os.environ.setdefault("LEGALIZE_MX_INDEX", str(HERE / "index.sqlite"))
os.environ.setdefault("LEGALIZE_MX_CACHE", "/tmp/legalize-mx")  # the only writable dir
os.environ.setdefault("LEGALIZE_MX_MAX_DOC_MB", "25")

from starlette.requests import Request
from starlette.responses import JSONResponse

from legalize_mx_mcp import core
from legalize_mx_mcp.server import mcp

# The index is redeployed with the site; a public server must not download one per instance.
mcp.remove_tool("actualizar_indice")
mcp.settings.stateless_http = True
mcp.settings.json_response = True
mcp.settings.transport_security = None  # public host: FastMCP's localhost-only default rejects it

API = (
    "buscar_norma",
    "leer_norma",
    "articulo",
    "historial",
    "diff",
    "fuentes",
    "cobertura",
    "dof_del_dia",
    "leer_nota_dof",
    "info",
)
CORS = {"Access-Control-Allow-Origin": "*", "Cache-Control": "public, s-maxage=3600"}


def _cast(value: str, annotation: str):
    if "bool" in annotation:
        return value.lower() in ("1", "true", "si", "sí")
    if "int" in annotation:
        return int(value)
    return value


@mcp.custom_route("/api/{tool}", methods=["GET"])
async def api(request: Request) -> JSONResponse:
    tool = request.path_params["tool"]
    if tool not in API:
        return JSONResponse({"error": f"herramienta desconocida: {tool}", "herramientas": API}, 404)
    fn = getattr(core, tool)
    params = inspect.signature(fn).parameters
    try:
        args = {
            k: _cast(v, str(params[k].annotation))
            for k, v in request.query_params.items()
            if k in params
        }
        out = fn(**args)
    except (TypeError, ValueError) as exc:
        return JSONResponse({"error": str(exc)}, 400, headers=CORS)
    except Exception as exc:  # noqa: BLE001 — upstream portals fail; say so as JSON
        return JSONResponse({"error": f"{type(exc).__name__}: {exc}"}, 502)
    return JSONResponse(out, 400 if out.get("error") else 200, headers=CORS)


app = mcp.streamable_http_app()
