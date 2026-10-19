# Referencia de herramientas

Parámetros, respuesta y errores de cada herramienta del MCP. Los ejemplos con respuestas reales están en [EJEMPLOS.md](../EJEMPLOS.md). Cada herramienta tiene su subcomando equivalente en el CLI (`legalize-mx <subcomando> --help`).

**Convenciones**
- **Fechas:** `AAAA-MM-DD`.
- **Textos largos:** se entregan por partes. Si la respuesta trae `siguiente_desde`, se pide la siguiente parte con `desde=<valor>`.
- **Errores:** llegan como `{"error": "…"}`, con contexto extra cuando ayuda (`parecidos`, `sugerencia`).

---

## `buscar_norma`

| Parámetro | Tipo | Por defecto | Uso |
|---|---|---|---|
| `texto` | str | `""` | Palabras a buscar en el título, el inicio del texto y sus encabezados. Todas deben aparecer; la última se busca como prefijo. Sin texto, lista lo que cumpla los filtros |
| `estado` | str | — | `federal`, una clave de 3 letras (`JAL`, `CMX`…) o un alias (`cdmx`, `edomex`, `nuevo leon`) |
| `municipio` | str | — | Nombre (sin acentos también funciona) o clave INEGI de 3 dígitos |
| `tipo` | str | — | Valor de `rank` (ver [DATOS.md](DATOS.md)) |
| `vigente` | bool | — | `true` solo vigentes; `false` solo abrogadas o sin dato |
| `con_texto` | bool | — | Solo normas con texto procesado |
| `fuente` | str | — | Slug de la fuente (ver [FUENTES.md](FUENTES.md)) |
| `limite`, `desde` | int | 20, 0 | Paginación |

**Orden:** primero las coincidencias en el título; entre ellas, las que tienen texto, y luego los títulos más cortos (más exactos). Después van las coincidencias solo en el contenido, por relevancia.

**Respuesta:** `resultados[]` con `id`, `title`, `origin`, `scope`, `state`, `municipality`, `rank`, `status`, `publication_date`, `last_updated`, `has_text`, `texto_estado`, `fuente_texto`, `url` y `fragmento` (las coincidencias van entre «»). También `n` y `siguiente_desde`, y `aviso_indice` si corresponde.

## `leer_norma`

| Parámetro | Tipo | Por defecto | Uso |
|---|---|---|---|
| `id` | str | — | Id de la norma. Acepta también la abreviatura federal o el título exacto |
| `fecha` | str | — | Devuelve el texto vigente en esa fecha |
| `desde`, `max_caracteres` | int | 0, 60000 | Paginación |
| `extraer_en_vivo` | bool | false | Si la norma no tiene texto, baja el documento oficial y lo extrae |

**Con texto:** `texto`, `texto_estado`, `fuente_texto`, `vigente_al`, `version` (solo con `fecha`: fecha, tipo, disposición, sha), `caracteres_totales`, `siguiente_desde`, `fuente_oficial` y `aviso_texto` (como se publicó u OCR).

**Sin texto:** `texto_disponible=false`, `motivo` y `documentos_oficiales[]` (tipo, descripción, fecha, url).
- Con `extraer_en_vivo=true` agrega `extraido_en_vivo` (url, formato, caracteres) y el `texto` paginado.
- Las notas del DOF se leen por su API.
- Un PDF escaneado devuelve una `nota`, porque no tiene capa de texto.
- Un `.doc` antiguo devuelve el enlace.

**Errores:** id inexistente, o `la norma no existía el <fecha>`.

## `articulo`

| Parámetro | Uso |
|---|---|
| `id` | Id de la norma (debe tener texto) |
| `numero` | `"27"`, `"27o"`, `"27°"`, `"3 bis"`, `"283 quater"`, `"primero"`, `"único"` |
| `fecha` | Opcional: el artículo como estaba en esa fecha |

**Respuesta:** `articulo` (encabezado tal como está en la ley), `texto` y `aviso_texto` si corresponde.
- Si el número aparece varias veces (transitorios, artículos del decreto), agrega `otras_coincidencias`. Gana el que está escrito como se pidió: dígitos frente a ordinal.
- Si no existe, devuelve `parecidos` y `total_articulos`.

## `historial`

**Respuesta:**
- **`versiones[]`:** las versiones en git, de la más antigua a la más reciente, con `fecha` (Source-Date), `tipo`, `disposicion`, `cambio`, `articulos_afectados` y `sha`.
- **`publicaciones_scjn[]`:** todo lo que la SCJN registra, cada publicación con su PDF y Word. Incluye fe de erratas y complementos que no cambian el texto.
- **`repo`:** enlace al historial en GitHub.

**Límite:** sin `GITHUB_TOKEN`, GitHub permite 60 consultas por hora. El historial se guarda en caché 24 h por versión del índice.

## `diff`

| Parámetro | Uso |
|---|---|
| `id` | Id de la norma |
| `fecha_a` | Versión vigente en esa fecha |
| `fecha_b` | Opcional; si se omite, compara contra la versión actual |
| `max_caracteres` | Tope de la respuesta (40000) |

**Respuesta:** `version_a`, `version_b`, `articulos_reformados[]`, `articulos_adicionados[]`, `articulos_derogados_o_eliminados[]` y `cambios[]` (artículo, tipo y, según el caso, `diff` unificado o `texto`).
- La comparación es **artículo por artículo**. Un diff del texto completo se desalinea en leyes de miles de líneas.
- Si se rebasa el tope, `nota` dice cuántos cambios quedaron fuera.

## `fuentes`

Devuelve los enlaces para citar o verificar una norma:
- `documentos_oficiales[]`;
- `ficha_scjn`;
- `markdown_versionado` y `historial_git`, en GitHub;
- `dataset`.

## `cobertura`

- **Sin parámetros:** el país completo: normas por fuente (total y con texto), por tipo, y municipios por clasificación con su población.
- **Con `estado`:** lo mismo para ese estado.
- **Con `estado` y `municipio`:** la ficha del censo de ese municipio, más cuántas normas suyas hay en el índice y cuántas con texto.

## `dof_del_dia`

| Parámetro | Uso |
|---|---|
| `fecha` | Por defecto, hoy |
| `solo_normativas` | `true` (por defecto): decretos, acuerdos, reglamentos, NOM, lineamientos, reglas, circulares…; `false`: todo, incluidos avisos, convocatorias y edictos |

**Respuesta:** `notas[]` con `codigo`, `titulo`, `dependencia`, `seccion`, `pagina`, `edicion` y `url`. Se consulta en vivo a la API oficial.

## `leer_nota_dof`

`codigo` (de `dof_del_dia`): devuelve el texto completo, paginado.

## `actualizar_indice`

Baja el índice publicado más reciente y lo usa sin reiniciar. Devuelve `antes`, `ahora`, `archivo` y `actualizado`.

---

## Avisos que pueden venir en cualquier respuesta

| Campo | Cuándo | Qué hacer |
|---|---|---|
| `aviso_indice` | Hay un índice más nuevo, o el local tiene más de 7 días | `actualizar_indice()`; para lo reciente, `dof_del_dia()` |
| `aviso_texto` | El texto es como se publicó (no consolidado), o viene de OCR | Decirlo al citar; verificar cifras con el PDF oficial |
| `nota` | Texto parcial, PDF escaneado, diff truncado… | Seguir la indicación |
