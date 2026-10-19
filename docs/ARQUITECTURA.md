# Arquitectura

Cómo llega una norma desde el portal oficial hasta la respuesta de un agente.

```
 PORTALES OFICIALES                     PIPELINE (legalize-mex)                 PUBLICADO                  ESTE REPO
 ─────────────────                      ───────────────────────                 ─────────                  ─────────
 SCJN (catálogo + Word + PDF) ──┐
 DOF (API sidof)               ─┤  cosecha a 1 req/s por host      ┌─► GitHub elimorals/legalize-mx ──┐
 31 congresos + Consejería     ─┼─► catálogo + originales (crudo) ─┤     (Markdown, 1 commit/reforma) │
 periódicos oficiales (POE)    ─┤  texto: Word → bloques;          │                                   ├─► MCP / CLI
 ~600 portales municipales     ─┘  PDF → recorte + OCR             └─► Hugging Face legalize-mx  ──────┘
                                    filtro de identidad por versión       data/ (parquet) + index/ (SQLite)
```

## Las tres capas de datos

1. **Crudo.** Los documentos originales (Word, PDF, HTML) tal como los sirve cada portal, guardados por hash (`raw-mx/objects/`) con un manifiesto por fuente. No se publican: pesan ~600 GB.
2. **Catálogo.** Una ficha por norma: título, ámbito, estado, municipio, estatus, fechas y **todos los enlaces oficiales** (cada reforma con su Word o PDF). Cubre ~215,000 normas, tengan texto o no.
3. **Texto.** Markdown por norma en git, con **un commit por reforma** fechado en la fecha legislativa (trailer `Source-Date`). Hay dos tipos:
   - **Consolidado** (`point_in_time`): de los Word de la SCJN; cada versión incorpora la reforma correspondiente.
   - **Como se publicó** (`as_enacted`): del PDF del periódico oficial, por la capa de texto o por OCR. Las reformas posteriores quedan registradas como commits sin cambio de texto.

## Componentes de este repo

| Archivo | Qué hace |
|---|---|
| `src/legalize_mx_mcp/index.py` | Descarga, cachea y consulta el índice SQLite (FTS5); filtros, cobertura y aviso de índice desactualizado |
| `src/legalize_mx_mcp/remote.py` | Todo lo que se pide al momento: texto e historial del repo de GitHub, documentos oficiales en vivo (Word/PDF/HTML) y API del DOF |
| `src/legalize_mx_mcp/core.py` | Las herramientas como funciones: armado de respuestas, artículos, diff por artículo, paginación y avisos |
| `src/legalize_mx_mcp/server.py` | Servidor MCP (FastMCP), por stdio o HTTP |
| `src/legalize_mx_mcp/cli.py` | CLI `legalize-mx`, con los mismos subcomandos que las herramientas |
| `scripts/build_index.py` | Construye el índice a partir del catálogo, el repo git y el censo municipal |
| `scripts/publish_index.sh` | Sube el índice a `index/` del dataset de Hugging Face y borra el anterior |
| `scripts/gen_fuentes_md.py` | Genera [FUENTES.md](FUENTES.md) a partir del índice |
| `skills/legalize-mx/` | La skill de Claude Code que enseña a usar el MCP, con sus evaluaciones |

## Por qué así

- **Sin servidor propio.** El índice (~90 MB) se baja una vez de Hugging Face y vive en la máquina del usuario; el texto lo sirve GitHub. Instalarlo es gratis y no hay nada que mantener encendido.
- **Índice ligero, texto por demanda.** El texto completo (~1,500 millones de caracteres) haría un índice de varios GB. El índice guarda títulos, metadatos y el inicio de cada texto; el texto completo se pide por norma.
- **Git como base del historial.** Cada reforma es un commit con fecha, decreto y artículos afectados. "¿Qué decía el 1 de enero de 2019?" se resuelve con el último commit anterior a esa fecha, y el diff de git es el diff legislativo.
- **En vivo solo cuando hace falta.** Las normas sin texto procesado y el DOF del día se consultan en el portal oficial en ese momento.

## Garantías de calidad

- **Filtro de identidad por versión.** El pipeline descarta toda versión cuyo texto no corresponde a la norma. Se agregó después de detectar que la SCJN servía Word de otras normas bajo carga paralela; en octubre de 2026 se corrigieron 985 versiones en 824 leyes.
- **Descargas de la SCJN en un solo proceso**, por la misma razón.
- **Fechas legislativas reales.** Git no guarda fechas anteriores a 1970, así que el MCP usa el trailer `Source-Date` para todo cálculo por fecha.
- **Avisos en las respuestas.** `aviso_texto` cuando el texto es como se publicó o viene de OCR; `aviso_indice` cuando el índice está desactualizado.
