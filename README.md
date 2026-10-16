# legalize-mx-mcp

MCP server y CLI para que agentes de IA consulten la **legislación mexicana federal, estatal y municipal**, con su historial de reformas.

Busca en el catálogo, lee el texto vigente o el que regía en una fecha, compara versiones y devuelve siempre el enlace oficial para citar.

Corre en tu máquina, sin servidor propio:

- **Índice de búsqueda:** se baja una vez del dataset [`elimoralsmendox/legalize-mx`](https://huggingface.co/datasets/elimoralsmendox/legalize-mx) en Hugging Face (~90 MB) y se actualiza solo.
- **Texto e historial:** se piden por norma al repo público [`elimorals/legalize-mx`](https://github.com/elimorals/legalize-mx), con un archivo Markdown por ley y un commit por reforma.
- **Documentos oficiales:** cuando una norma solo está catalogada, se bajan y se extraen en vivo del portal oficial (SCJN, congresos, periódicos oficiales, municipios). El DOF del día también se consulta en vivo.

## Qué contiene

| | |
|---|---|
| Normas en el índice | ~191,000, de 53 fuentes oficiales |
| Con texto e historial versionado | ~34,000, y creciendo |
| Fuentes | Catálogo de la SCJN (federal, 32 entidades, tratados), 31 congresos y la Consejería de CDMX, Cámara de Diputados, DOF (NOM, lineamientos, acuerdos), periódicos oficiales estatales y ~600 portales municipales |
| Cobertura municipal | Censo de los 2,478 municipios: cuál es la fuente de cada uno, o por qué no la hay |

**Cuándo no hay texto.** No todas las normas tienen texto procesado todavía. En esos casos `leer_norma` lo dice y devuelve los documentos oficiales. Con `extraer_en_vivo=true` baja el documento y extrae su texto en ese momento. Un PDF escaneado sale vacío, porque necesita OCR.

## Instalación

Necesitas [uv](https://docs.astral.sh/uv/). Para extraer PDF en vivo hace falta además `pdftotext` (`brew install poppler` o `apt install poppler-utils`), o instalar el extra `[pdf]`.

### Claude Code

```bash
claude mcp add legalize-mx -- uvx --from git+https://github.com/elimorals/legalize-mx-mcp legalize-mx-mcp
```

### Otros clientes MCP (`.mcp.json`, Claude Desktop, Cursor…)

```json
{
  "mcpServers": {
    "legalize-mx": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/elimorals/legalize-mx-mcp", "legalize-mx-mcp"],
      "env": { "GITHUB_TOKEN": "" }
    }
  }
}
```

Sin token, GitHub permite 60 consultas de historial por hora. El historial se guarda en caché 24 h. Con un `GITHUB_TOKEN` el límite sube a 5,000.

### CLI

```bash
uvx --from git+https://github.com/elimorals/legalize-mx-mcp legalize-mx buscar "jornada laboral" --estado federal
```

## Herramientas

| Herramienta | Qué hace |
|---|---|
| `buscar_norma(texto, estado?, municipio?, tipo?, vigente?, con_texto?, fuente?)` | Búsqueda de texto completo en títulos y contenido, con filtros |
| `leer_norma(id, fecha?, desde?, extraer_en_vivo?)` | Texto vigente, o el que regía en una fecha. Va por partes si es largo |
| `articulo(id, numero, fecha?)` | Un artículo: `"27"`, `"3 bis"`, `"primero"` |
| `historial(id)` | Reformas: fecha, decreto, artículos afectados |
| `diff(id, fecha_a, fecha_b?)` | Artículos reformados, adicionados y derogados entre dos fechas, más el diff |
| `fuentes(id)` | Enlaces oficiales para citar o verificar |
| `cobertura(estado?, municipio?)` | Qué hay y qué falta: normas por fuente y tipo, y la fuente de cada municipio |
| `dof_del_dia(fecha?, solo_normativas?)` | Lo que publicó el DOF ese día (en vivo) |
| `leer_nota_dof(codigo)` | Texto completo de una nota del DOF (en vivo) |
| `actualizar_indice()` | Baja ya el índice más reciente, sin reiniciar |

En el CLI son los subcomandos `buscar`, `leer`, `articulo`, `historial`, `diff`, `fuentes`, `cobertura`, `dof`, `nota-dof`, `actualizar` e `info`.

## Mantenerlo al día

El índice se publica de nuevo conforme entran normas y reformas. Tu copia local se mantiene así:

- **Al arrancar:** si pasaron más de 24 h desde la última revisión, el MCP consulta `index/latest.json`, que pesa unos bytes, y baja el índice solo si hay versión nueva.
- **Mientras corre:** si se publica un índice nuevo, `buscar_norma`, `cobertura` e `info` agregan a su respuesta un campo **`aviso_indice`** con el mensaje para el usuario. Con `actualizar_indice()` o `legalize-mx actualizar` se cambia a la versión nueva sin reiniciar.
- **Si tu copia tiene más de 7 días**, también aparece `aviso_indice`, porque lo publicado esos días puede faltar. Lo más reciente se confirma con `dof_del_dia()`, que consulta el DOF en vivo.
- **El texto y el historial** de cada ley siempre se leen del repo de GitHub, así que reflejan la última publicación aunque el índice sea de unos días antes.

### Ejemplos

```bash
legalize-mx articulo CPEUM 27 --fecha 1920-01-01     # el artículo 27 original de 1917
legalize-mx diff LFT 2025-01-01                      # qué cambió en la LFT desde enero de 2025
legalize-mx buscar "protección civil" --municipio Zapopan
legalize-mx leer "muni-html:jal-zapopan:f30bbb480326df84" --en-vivo
legalize-mx cobertura --estado OAX
legalize-mx dof
```

**Identificadores**

- **Leyes federales:** usan su abreviatura de Diputados (`CPEUM`, `LFT`, `LAMP`…).
- **Resto del catálogo de la SCJN:** `{ESTADO}-{titulo}-{id}`.
- **Otras fuentes:** `{fuente}:{id}`, por ejemplo `congreso-jal:…` o `dof:5801377`.

`buscar_norma` siempre devuelve el id.

## Servidor HTTP (opcional)

Para agentes que no pueden lanzar procesos locales:

```bash
legalize-mx-mcp --http --host 0.0.0.0 --port 8000     # streamable HTTP en /mcp
```

Corre igual en Hugging Face Spaces, Fly.io o cualquier VPS. No necesita base de datos: baja el mismo índice.

## Variables de entorno

| Variable | Para qué |
|---|---|
| `GITHUB_TOKEN` | Sube el límite de consultas de historial |
| `LEGALIZE_MX_REPO` | Ruta a un clon local de `legalize-mx`: texto e historial sin red |
| `LEGALIZE_MX_INDEX` | Ruta a un índice local (no lo descarga) |
| `LEGALIZE_MX_CACHE` | Carpeta de caché (por defecto `~/.cache/legalize-mx`) |

## Actualizar el índice (mantenedores)

```bash
python3 scripts/build_index.py --data …/data-mx --repo …/legalize-mx --censo …/research-censo \
  --municipios …/municipios.json --out dist
scripts/publish_index.sh dist          # sube index/ al dataset de Hugging Face
```

## Advertencia

Es una herramienta de consulta, no asesoría legal. El texto se obtiene automáticamente de fuentes oficiales y puede contener errores de origen o de conversión. Verifica siempre con la fuente oficial que devuelve `fuentes()` antes de usarlo en un asunto real.

## Licencia

MIT para el código. Los textos legales son de dominio público: el art. 14, fr. VIII, de la Ley Federal del Derecho de Autor excluye de protección los textos legislativos y administrativos.
