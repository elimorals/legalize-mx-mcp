# Modelo de datos

## Identificadores

| Tipo | Forma | Ejemplos |
|---|---|---|
| Ley federal con abreviatura oficial de Diputados | abreviatura | `CPEUM`, `LFT`, `LGS`, `CFF`, `LAMP` |
| Resto del catálogo SCJN (federal) | `FED-{título en slug}-{IdOrd SCJN}` | `FED-reglamento-de-los-articulos-121-y-122-de-la-ley-federal-del-101205` |
| Estatal / municipal (SCJN) | `{ESTADO}-{slug}-{IdOrd}` | `JAL-codigo-penal-para-el-estado-libre-y-soberano-de-jalisco-5757` |
| CDMX (SCJN) | `CMX-{slug}-{IdOrd}` | `CMX-ley-de-movilidad-de-la-ciudad-de-mexico-antes-ley-de-101763` |
| Tratado (SCJN) | `TRA-{slug}-{IdOrd}` | `TRA-convenio-para-evitar-la-doble-tributacion-y-prevenir-la-85288` |
| Cualquier otra fuente | `{fuente}:{id en la fuente}` | `dof:5801377`, `congreso-jal:…`, `muni-html:jal-zapopan:f30bbb480326df84` |

- Los ids son **estables**: no cambian cuando la norma se reforma.
- **Estados:** claves de 3 letras (`AGU` … `ZAC`, `CMX`) o `federal`.
- **Municipios:** clave INEGI de 3 dígitos dentro del estado. En los datos se guarda también en su forma de 5 dígitos (estado + municipio).

## Una norma en el índice

| Campo | Significado |
|---|---|
| `id`, `title` | Identificador y título oficial |
| `origin` | Fuente: `scjn`, `dof`, `congreso-xxx`, `muni-…` (ver [FUENTES.md](FUENTES.md)) |
| `scope` | `federal`, `state`, `cdmx`, `municipal`, `tratados` |
| `state`, `municipality`, `municipality_inegi` | Ubicación |
| `rank` | Tipo: `constitucion`, `ley`, `ley_federal`, `ley_general`, `ley_organica`, `codigo`, `reglamento`, `bando`, `ley_de_ingresos`, `presupuesto`, `acuerdo`, `decreto`, `lineamientos`, `reglas`, `manual`, `estatuto`, `tratado`, `nom`, `proyecto-nom`, `otro`… |
| `status` | `in_force`, `repealed` o `unknown` (la fuente no lo dice) |
| `publication_date`, `last_updated` | Primera publicación y última reforma conocida |
| `has_text` | `true` si hay texto versionado en git |
| `texto_estado` | `point_in_time` (consolidado), `as_enacted` (como se publicó) o vacío si no hay texto |
| `fuente_texto` | `docx`, `pdf` u `ocr` |
| `url` | Ficha o documento oficial |

## Una norma en el repo git

Cada ley es un archivo Markdown en `elimorals/legalize-mx`, con *frontmatter* YAML:

```yaml
---
title: "LEY FEDERAL DEL TRABAJO"
identifier: "LFT"
country: "mx"
rank: "ley_federal"
publication_date: "1970-04-01"
last_updated: "2026-05-14"
status: "in_force"
source: "https://legislacion.scjn.gob.mx/Buscador/Paginas/wfOrdenamientoDetalle.aspx?IdOrd=410&Vig=1&TPub=6"
scjn_id: "410"
reform_count: "60"
abbreviation: "LFT"
---
# LEY FEDERAL DEL TRABAJO

## TITULO PRIMERO. Principios Generales

###### Artículo 1°.

La presente Ley es de observancia general en toda la República…
```

- **Estructura:** títulos y capítulos van como encabezados `##`–`#####`; cada artículo, como `######`. Así `articulo()` los ubica.
- **Textos como se publicaron:** agregan `text_state: "as_enacted"` y `text_source: "pdf"` u `"ocr"`, más `last_amendment`, que es la reforma más reciente registrada.

### Commits

Cada commit corresponde a una publicación oficial:

```
[reform] LEY FEDERAL DEL TRABAJO — arts. 303, 304, 305 and 7 more

Norm: LFT
Disposition: DOF-5787418
Date: 2026-05-14
Source: https://legislacion.scjn.gob.mx/…
Affected articles: Artículo 303., CAPITULO XI, Artículo 304., …
Change: DECRETO 124/2026

Source-Id: DOF-5787418
Norm-Id: LFT
Source-Date: 2026-05-14
```

- **Tipos:** `bootstrap` (texto original), `reform`, `new`, `repeal`, `correction`.
- **Fechas:** la del autor y la del commit son la fecha legislativa. Para fechas anteriores a 1970 git guarda `1970-01-02`; la fecha real está en el trailer `Source-Date`.

## El índice (SQLite)

Archivo `index/index-<versión>.sqlite.gz` en el dataset de Hugging Face; `index/latest.json` apunta a la versión vigente y trae su `sha256`.

| Tabla | Contenido |
|---|---|
| `norms` | Una fila por norma, con los campos de arriba más `repo_path`, `reforms` (JSON con cada publicación y sus enlaces) y `extra` |
| `norms_fts` | Búsqueda de texto completo (FTS5, sin acentos) sobre el título y el inicio del texto con sus encabezados |
| `coverage` | Censo municipal: estado, INEGI, nombre, clasificación, población, dominio, URL de normatividad y de gaceta, fuente estatal |
| `meta` | Versión, fecha de construcción y conteos |

## El dataset de Hugging Face (`elimoralsmendox/legalize-mx`)

| Ruta | Contenido |
|---|---|
| `data/catalog.parquet` | Catálogo SCJN completo, con y sin texto, y enlaces de cada reforma |
| `data/laws.parquet` | Una fila por ley en el repo: frontmatter y Markdown vigente |
| `index/` | El índice del MCP |

## Clasificación municipal (`cobertura`)

| Valor | Significa |
|---|---|
| `abierta` | Publica sus normas en su propio sitio |
| `compilacion_estatal` | Sus normas no fiscales las publica el periódico oficial o una compilación del estado |
| `compilacion_estatal_solo_fiscal` / `compilacion_estatal_ley_ingresos` | Solo hay leyes de ingresos o presupuestos emitidos por el congreso |
| `sitio_sin_normas` | Tiene sitio, pero no se encontraron normas en él (no quiere decir que no existan) |
| `sin_sitio` | No se encontró dominio oficial |
| `bloqueado` | El sitio tiene WAF o captcha |
| `sin_verificar` | No se pudo comprobar |
