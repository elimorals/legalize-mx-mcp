# Ejemplos

Llamadas reales a cada herramienta, con su respuesta. Las respuestas están **recortadas**: los textos largos terminan en `…` y las listas muestran sus primeros elementos. Se capturaron el 16 de octubre de 2026 con el índice `202610162229`.

Cada herramienta aparece primero como llamada MCP y después como su equivalente en el CLI.

**Contenido**

1. [Antes de empezar](#antes-de-empezar)
2. [buscar_norma](#buscar_norma)
3. [leer_norma](#leer_norma)
4. [articulo](#articulo)
5. [historial](#historial)
6. [diff](#diff)
7. [fuentes](#fuentes)
8. [cobertura](#cobertura)
9. [dof_del_dia y leer_nota_dof](#dof_del_dia-y-leer_nota_dof)
10. [actualizar_indice y aviso_indice](#actualizar_indice-y-aviso_indice)
11. [Flujos completos de un agente](#flujos-completos-de-un-agente)
12. [Errores y límites](#errores-y-límites)

---

## Antes de empezar

**Identificadores.** Todas las herramientas, salvo `buscar_norma`, `cobertura` y `dof_del_dia`, reciben el `id` de una norma, que siempre sale de `buscar_norma`.

| Tipo de norma | Forma del id | Ejemplo |
|---|---|---|
| Ley federal con abreviatura de Diputados | abreviatura | `CPEUM`, `LFT`, `LGS`, `LAMP` |
| Resto del catálogo de la SCJN | `{ESTADO}-{título}-{id SCJN}` | `JAL-codigo-penal-para-el-estado-libre-y-soberano-de-jalisco-5757` |
| Tratado internacional | `TRA-{título}-{id}` | `TRA-convenio-para-evitar-la-doble-tributacion-y-prevenir-la-85288` |
| Cualquier otra fuente | `{fuente}:{id}` | `dof:5578283`, `congreso-jal:…`, `muni-html:jal-zapopan:f30bbb480326df84` |

**`has_text`** indica si la norma tiene texto procesado e historial en git.
- Si es `true`, funcionan `leer_norma`, `articulo`, `historial` (versiones en git) y `diff`.
- Si es `false`, la norma solo está catalogada. `leer_norma` devuelve sus documentos oficiales, y con `extraer_en_vivo=true` baja uno y lo extrae.

**Textos largos.** Se entregan por partes. Si la respuesta trae `siguiente_desde`, pide la siguiente parte con `desde=<ese valor>`.

**Estados.** Van con clave de 3 letras: `AGU`, `BCN`, `BCS`, `CAM`, `CHP`, `CHH`, `CMX`, `COA`, `COL`, `DUR`, `GUA`, `GRO`, `HID`, `JAL`, `MEX`, `MIC`, `MOR`, `NAY`, `NLE`, `OAX`, `PUE`, `QUE`, `ROO`, `SLP`, `SIN`, `SON`, `TAB`, `TAM`, `TLA`, `VER`, `YUC` y `ZAC`. Lo federal va como `federal`. También se aceptan `cdmx`, `edomex` y `nuevo leon`.

---

## buscar_norma

Busca en el título y en el inicio del texto de cada norma. Primero aparecen las coincidencias en el título, y entre ellas las que tienen texto. Todas las palabras deben aparecer, y la última se busca como prefijo (`proteccion civ` encuentra "protección civil").

### Una ley federal por su nombre

```json
buscar_norma(texto="ley federal del trabajo", estado="federal", limite=3)
```
```json
{
  "resultados": [
    {
      "id": "LFT",
      "title": "LEY FEDERAL DEL TRABAJO",
      "origin": "scjn",
      "state": "federal",
      "rank": "ley_federal",
      "status": "in_force",
      "publication_date": "1970-04-01",
      "last_updated": "2026-05-14",
      "has_text": true,
      "url": "https://legislacion.scjn.gob.mx/Buscador/Paginas/wfOrdenamientoDetalle.aspx?IdOrd=410&Vig=1&TPub=6",
      "fragmento": "«LEY» «FEDERAL» «DEL» «TRABAJO» …"
    },
    {
      "id": "FED-reglamento-de-los-articulos-121-y-122-de-la-ley-federal-del-101205",
      "title": "REGLAMENTO DE LOS ARTICULOS 121 Y 122 DE LA LEY FEDERAL DEL TRABAJO",
      "rank": "reglamento", "status": "in_force", "has_text": true
    },
    {
      "id": "FED-reglamento-de-los-articulos-121-y-122-de-la-ley-federal-del-9226",
      "title": "REGLAMENTO DE LOS ARTICULOS 121 Y 122 DE LA LEY FEDERAL DEL TRABAJO",
      "rank": "reglamento", "status": "repealed", "has_text": true
    }
  ],
  "n": 3,
  "siguiente_desde": 3
}
```
CLI: `legalize-mx buscar "ley federal del trabajo" --estado federal --limite 3`

### Un código estatal

```json
buscar_norma(texto="codigo penal", estado="JAL", limite=3)
```
```json
{
  "resultados": [
    {"id": "JAL-codigo-penal-para-el-estado-libre-y-soberano-de-jalisco-5757",
     "title": "CODIGO PENAL PARA EL ESTADO LIBRE Y SOBERANO DE JALISCO",
     "rank": "codigo", "status": "in_force", "last_updated": "2026-09-08", "has_text": true},
    {"id": "JAL-codigo-de-procedimientos-penales-para-el-estado-libre-y-5764",
     "title": "CODIGO DE PROCEDIMIENTOS PENALES PARA EL ESTADO LIBRE Y SOBERANO DE JALISCO",
     "rank": "codigo", "status": "repealed", "has_text": true},
    {"id": "JAL-decreto-no-24864-lx-14-se-emiten-las-declaratorias-de-100286",
     "title": "DECRETO NO. 24864/LX/14, SE EMITEN LAS DECLARATORIAS DE INCORPORACION DEL SISTEMA PROCESAL PENAL ACUSATORIO …",
     "rank": "decreto", "has_text": true}
  ]
}
```

`status` distingue lo vigente (`in_force`) de lo abrogado (`repealed`). Para quedarte solo con lo vigente, agrega `vigente=true`.

### Normas municipales

```json
buscar_norma(texto="bando de policia", estado="OAX", limite=3)
```
```json
{
  "resultados": [
    {"id": "muni-html-2:oax-san-lucas-ojitlan:c4f4d2eaa7a48f7d", "title": "BANDO DE POLICIA",
     "origin": "muni-html-2", "scope": "municipal", "municipality": "San Lucas Ojitlán",
     "rank": "bando", "has_text": false,
     "url": "https://sanlucasojitlan.gob.mx/transparencia/2026/gaceta/bando_policia.pdf"},
    {"id": "muni-html-2:oax-san-marcos-arteaga:c7ca4821a57c81ff", "title": "BANDO DE POLICIA",
     "municipality": "San Marcos Arteaga", "has_text": false,
     "url": "https://sanmarcosarteaga.gob.mx/transparencia/2026/gaceta/bando_policia.pdf"},
    {"id": "muni-html-2:oax-san-juan-bautista-jayacatlan:ef619f13b00fa2e2", "title": "BANDO DE POLICIA Leer Mas",
     "municipality": "San Juan Bautista Jayacatlán", "has_text": false}
  ]
}
```

Los títulos municipales vienen tal como los publica cada portal: a veces son genéricos ("BANDO DE POLICIA") o traen restos del botón ("Leer Mas"). El municipio va en `municipality`. Para un municipio en particular usa `municipio="San Lucas Ojitlán"`, o su clave INEGI de 3 dígitos.

### Por contenido, no por título

```json
buscar_norma(texto="teletrabajo", estado="federal", con_texto=true, limite=3)
```
```json
{
  "resultados": [
    {"id": "FED-acuerdo-general-del-pleno-del-consejo-de-la-judicatura-159872",
     "title": "ACUERDO GENERAL DEL PLENO DEL CONSEJO DE LA JUDICATURA FEDERAL [POR EL QUE SE CREA EL COMITE TECNICO DE TRABAJO A DISTANCIA …]",
     "fragmento": " … EN EL PROPIO CONSEJO, EN RELACIÓN CON EL «TELETRABAJO», PUBLICADO EN EL D.O.F. … "},
    {"id": "LFT", "title": "LEY FEDERAL DEL TRABAJO",
     "fragmento": " … CAPITULO XII. Trabajo a domicilio · CAPITULO XII BIS. «Teletrabajo» · CAPITULO XIII. Personas Trabajadoras del Hogar … "}
  ]
}
```

El índice busca en el título, en los primeros 1,500 caracteres de cada texto y en sus encabezados (títulos y capítulos). Por eso la LFT aparece por su "CAPÍTULO XII BIS. Teletrabajo". Una palabra que solo aparece en un artículo no se encuentra; para eso lee la norma o pide el artículo.

### NOM y regulación del DOF

```json
buscar_norma(texto="etiquetado alimentos", fuente="dof", limite=3)
```
```json
{
  "resultados": [
    {"id": "dof:5578283",
     "title": "Decreto por el que se reforman y adicionan diversas disposiciones de la Ley General de Salud, en materia de sobrepeso, obesidad y de etiquetado de alimentos y bebidas no alcohólicas.",
     "rank": "ley", "publication_date": "2019-11-08", "has_text": false},
    {"id": "dof:5590668",
     "title": "Modificación a la Norma Oficial Mexicana NOM-051-SCFI/SSA1- 2010, Especificaciones generales de etiquetado para alimentos y bebidas no alcohólicas preenvasados …",
     "rank": "nom", "publication_date": "2020-03-27"},
    {"id": "dof:5575205",
     "title": "Proyecto de Modificación a la Norma Oficial Mexicana NOM-051- SCFI/SSA1-2010 …",
     "rank": "proyecto-nom", "publication_date": "2019-10-11"}
  ]
}
```

Cada etapa de una NOM es una nota distinta del DOF: el proyecto (`proyecto-nom`), la modificación o la norma definitiva (`nom`), las prórrogas y las cancelaciones. Con `tipo="nom"` te quedas solo con las definitivas.

### Tratados internacionales

```json
buscar_norma(texto="doble tributacion", tipo="tratado", limite=3)
```
```json
{
  "resultados": [
    {"id": "TRA-convenio-para-evitar-la-doble-tributacion-y-prevenir-la-85288",
     "title": "CONVENIO PARA EVITAR LA DOBLE TRIBUTACION Y PREVENIR LA EVASION FISCAL EN RELACION CON LOS IMPUESTOS SOBRE LA RENTA (REPUBLICA DEL PERU, 2011)",
     "scope": "tratados", "rank": "tratado", "status": "in_force", "has_text": false}
  ],
  "n": 1
}
```

**Filtros disponibles:** `estado`, `municipio`, `tipo` (`ley`, `ley_federal`, `ley_general`, `ley_organica`, `codigo`, `reglamento`, `bando`, `ley_de_ingresos`, `presupuesto`, `acuerdo`, `decreto`, `lineamientos`, `reglas`, `manual`, `estatuto`, `tratado`, `nom`, `proyecto-nom`…), `vigente`, `con_texto` y `fuente` (`scjn`, `dof`, `diputados`, `congreso-xxx`, `gto-normateca`, `puebla-ojp`, `muni-html`…). Sin `texto`, lista las normas que cumplen los filtros.

---

## leer_norma

### Texto vigente, por partes

```json
leer_norma(id="LFT", max_caracteres=600)
```
```json
{
  "id": "LFT",
  "title": "LEY FEDERAL DEL TRABAJO",
  "status": "in_force",
  "texto_estado": "point_in_time",
  "vigente_al": "2026-05-14",
  "texto": "# LEY FEDERAL DEL TRABAJO\n\n> <small>[N. DE E. EN RELACIÓN CON LA ENTRADA EN VIGOR DEL PRESENTE ORDENAMIENTO …]</small>\n\nLEY FEDERAL DEL TRABAJO\n\nÚLTIMA REFORMA PUBLICADA EN EL DIARIO OFICIAL DE LA FEDERACIÓN: 14 DE MAYO DE …",
  "caracteres_totales": 1213676,
  "desde": 0,
  "siguiente_desde": 600,
  "nota": "texto parcial; pide desde=600 para continuar",
  "fuente_oficial": "https://legislacion.scjn.gob.mx/Buscador/Paginas/wfOrdenamientoDetalle.aspx?IdOrd=410&Vig=1&TPub=6"
}
```

La LFT completa tiene 1.2 millones de caracteres. Para preguntas concretas, `articulo` es mucho más barato que leerla entera.

### El texto que regía en una fecha

```json
leer_norma(id="LFT", fecha="2019-01-01", max_caracteres=400)
```
```json
{
  "id": "LFT",
  "vigente_al": "2018-06-22",
  "texto": "# LEY FEDERAL DEL TRABAJO\n\nLEY FEDERAL DEL TRABAJO\n\nÚLTIMA REFORMA PUBLICADA EN EL DIARIO OFICIAL DE LA FEDERACIÓN: 22 DE JUNIO DE 2018. …",
  "caracteres_totales": 697781,
  "version": {"fecha": "2018-06-22", "tipo": "reform", "disposicion": "DOF-5528936", "sha": "3d1a267eb51fd3748c8f595cf5d9fc95774dc5e1"}
}
```

El 1 de enero de 2019 regía la versión de la reforma del 22 de junio de 2018. Entonces la ley tenía 697,781 caracteres; hoy tiene 1,213,676.

### Una norma sin texto procesado

```json
leer_norma(id="AGU-acuerdo-07-2016-por-el-que-se-crea-el-sistema-de-datos-113302")
```
```json
{
  "id": "AGU-acuerdo-07-2016-por-el-que-se-crea-el-sistema-de-datos-113302",
  "title": "ACUERDO 07/2016 POR EL QUE SE CREA EL SISTEMA DE DATOS PERSONALES DE LAS UNIDADES DE ATENCION TEMPRANA DEL ESTADO DE AGUASCALIENTES",
  "texto_disponible": false,
  "motivo": "texto extraído del PDF del periódico oficial, pendiente de publicar",
  "documentos_oficiales": [
    {"tipo": "pdf", "descripcion": "ACUERDO (S) · 9 PRIMERA SECCION", "fecha": "2016-02-29",
     "url": "https://legislacion.scjn.gob.mx/Buscador/Paginas/AbrirDocReforma.aspx?q=…"}
  ],
  "nota": "pasa extraer_en_vivo=true para bajar y extraer el documento oficial ahora"
}
```

### Extraído en vivo del portal municipal

```json
leer_norma(id="muni-html:jal-zapopan:f30bbb480326df84", extraer_en_vivo=true, max_caracteres=400)
```
```json
{
  "title": "Reglamento de Protección Civil del Municipio de Zapopan, Jalisco.",
  "municipality": "Zapopan",
  "status": "repealed",
  "texto_disponible": false,
  "extraido_en_vivo": {
    "url": "https://servicios.zapopan.gob.mx:8000/wwwportal/publicfiles/descargasEnlaces/Reglamento-de-Protecci%C3%B3n-Civil-del-Municipio-de-Zapopan-Jalisco.pdf",
    "formato": "pdf",
    "caracteres": 88281
  },
  "texto": " Gaceta Municipal Vol. XI No. 36. Reglamento de Protección Civil del Municipio\n     de Zapopan, Jalisco. 22 de noviembre de 2004. Segunda Época. …",
  "caracteres_totales": 88281,
  "siguiente_desde": 400
}
```

El texto extraído en vivo sale tal como viene en el documento: sin estructura de artículos ni historial. Si el PDF es escaneado no tiene capa de texto, y la respuesta lo dice en `nota`.

### Una nota del DOF, en vivo

```json
leer_norma(id="dof:5578283", extraer_en_vivo=true, max_caracteres=350)
```
```json
{
  "extraido_en_vivo": {"fuente": "API del DOF", "caracteres": 6516},
  "texto": "DECRETO por el que se reforman y adicionan diversas disposiciones de la Ley General de Salud, en materia de sobrepeso, obesidad y de etiquetado de alimentos y bebidas no alcohólicas …",
  "caracteres_totales": 6516,
  "siguiente_desde": 350
}
```

Hay notas del DOF que no existen como texto, solo dentro del PDF de la edición. En ese caso la respuesta lo dice y apunta a la página:

```json
leer_norma(id="dof:5590668", extraer_en_vivo=true)
```
```json
{
  "nota": "el DOF no publica esta nota como texto: solo está en el PDF de la edición, página 4; usa los documentos_oficiales",
  "documentos_oficiales": [
    {"tipo": "pdf", "url": "https://sidof.segob.gob.mx/dof/sidof/documentos/pdf/285941"},
    {"tipo": "ficha", "url": "https://www.dof.gob.mx/nota_detalle.php?codigo=5590668&fecha=27/03/2020"}
  ]
}
```

---

## articulo

### El artículo 27 constitucional de 1917 y el de hoy

```json
articulo(id="CPEUM", numero="27", fecha="1920-01-01")
```
```json
{
  "id": "CPEUM",
  "articulo": "Art. 27.",
  "texto": "La propiedad de las tierras y aguas comprendidas dentro de los límites del territorio nacional, corresponde originariamente a la Nación, la cual, ha tenido y tiene el derecho de transmitir el dominio de ellas a los particulares, constituyendo la propiedad privada.\n\nEsta no podrá ser expropiada sino por causa de utilida …"
}
```
```json
articulo(id="CPEUM", numero="27")
```
```json
{
  "articulo": "Art. 27.",
  "texto": "La propiedad de las tierras y aguas comprendidas dentro de los límites del territorio nacional, corresponde originariamente a la Nación, la cual ha tenido y tiene el derecho de transmitir el dominio de ellas a los particulares, constituyendo la propiedad privada.\n\nLas expropiaciones sólo podrán hacerse por causa de uti …"
}
```

### Artículos con bis, ter, quáter…

```json
articulo(id="LFT", numero="283 quater")
```
```json
{
  "articulo": "Artículo 283 Quáter.",
  "texto": "La Secretaría del Trabajo y Previsión Social podrá expedir un certificado de cumplimiento de obligaciones laborales y de seguridad social de conformidad con las disposiciones generales que al efecto emitan las autoridades competentes.\n\n> <small>(REFORMADO PRIMER PÁRRAFO, D.O.F. 24 DE ENERO DE 2024)</small> …"
}
```

`numero` acepta `"27"`, `"27o"`, `"27°"`, `"3 bis"`, `"283 quater"`, `"primero"` y `"único"`.
- Si en la ley hay más de un artículo con ese número, porque los transitorios reinician la numeración, la respuesta trae `otras_coincidencias`.
- Si pides un número escrito con dígitos, gana el artículo que también usa dígitos. Así, `"1"` de la Ley de Amparo devuelve el "Artículo 1o." de la ley, no el "ARTÍCULO PRIMERO.- Se expide…" del decreto.

### Cuando no existe

```json
articulo(id="LFT", numero="9999")
```
```json
{"id": "LFT", "error": "no encontré el artículo '9999'", "parecidos": ["999", "99"], "total_articulos": 1285}
```

---

## historial

```json
historial(id="LFT")
```
```json
{
  "id": "LFT",
  "title": "LEY FEDERAL DEL TRABAJO",
  "n_versiones": 51,
  "versiones": [
    {"fecha": "1970-04-01", "tipo": "bootstrap", "sha": "74dbe3d74ccfcd256bba591650bd98ab1b2676a1"},
    {"fecha": "1972-04-24", "tipo": "reform", "disposicion": "DOF-4807159", "cambio": "DECRETO 46",
     "articulos_afectados": "Artículo 96., Artículo 97., Artículo 110., CAPITULO III, Artículo 136., …"},
    {"fecha": "1974-01-09", "tipo": "reform", "disposicion": "DOF-4655649", "cambio": "DECRETO 6"},
    "… (45 más)",
    {"fecha": "2026-05-01", "tipo": "reform", "disposicion": "DOF-2026-05-01-410-60",
     "cambio": "DECRETO 111/2026 EDICION VESPERTINA"},
    {"fecha": "2026-05-14", "tipo": "reform", "disposicion": "DOF-5787418", "cambio": "DECRETO 124/2026"}
  ],
  "repo": "https://github.com/elimorals/legalize-mx/commits/main/mx/5a/LFT.md",
  "publicaciones_scjn": [
    {"fecha": "1970-04-01", "categoria": "LEY", "seccion": "26 SECCION SEGUNDA",
     "pdf": "https://legislacion.scjn.gob.mx/…", "docx": "https://legislacion.scjn.gob.mx/…"},
    {"fecha": "1970-04-30", "categoria": "FE DE ERRATAS", "seccion": "51", "pdf": "https://legislacion.scjn.gob.mx/…"},
    "… (59 más)"
  ]
}
```

**`versiones` contra `publicaciones_scjn`:**
- **`versiones`** son los textos que tenemos versionados en git. `leer_norma`, `articulo` y `diff` pueden reconstruir cada uno.
- **`publicaciones_scjn`** es todo lo que la SCJN registra: reformas, fe de erratas y complementos, cada uno con su PDF del periódico oficial y, a veces, el Word.

Una norma sin texto solo trae `publicaciones_scjn`. La LFT tiene 51 versiones y 63 publicaciones porque algunas publicaciones, como las fe de erratas, no cambian el texto consolidado.

---

## diff

```json
diff(id="LFT", fecha_a="2025-01-01")
```
```json
{
  "id": "LFT",
  "version_a": "2024-12-24",
  "version_b": "vigente",
  "articulos_reformados": ["1", "2", "3", "16", "… (30 más)"],
  "articulos_adicionados": ["283 quater", "305 bis"],
  "articulos_derogados_o_eliminados": [],
  "cambios": [
    {"articulo": "1", "tipo": "reformado",
     "diff": "--- antes\n+++ despues\n@@ -3 +3 @@\n-> <small>(REFORMADO, D.O.F. 30 DE NOVIEMBRE DE 2012)</small>\n+> <small>(REFORMADO PRIMER PÁRRAFO, D.O.F. 15 DE ENERO DE 2026)</small>"},
    {"articulo": "2", "tipo": "reformado",
     "diff": "--- antes\n+++ despues\n@@ -1 +1,3 @@\n-Las normas del trabajo tienden a conseguir el equilibrio entre los factores de la producción y la justicia social, así como propiciar el trabajo digno o decente en todas las relaciones laborales.\n+Las normas del trabajo tienden a conseguir el equilibrio …"},
    "…"
  ],
  "nota": "se muestran 3 cambios de 36; sube max_caracteres o pide articulo(id, numero, fecha) para el resto"
}
```

- **Las fechas no tienen que coincidir con una reforma:** se toma la versión vigente en cada fecha. Aquí, `2025-01-01` resolvió a la reforma del 24 de diciembre de 2024.
- **Sin `fecha_b`** compara contra la versión vigente.
- **La comparación es artículo por artículo**, y cada cambio trae su diff (`-` antes, `+` después). Los reformados van primero, luego los adicionados y al final los eliminados.

---

## fuentes

```json
fuentes(id="LFT")
```
```json
{
  "id": "LFT",
  "title": "LEY FEDERAL DEL TRABAJO",
  "origen": "scjn",
  "documentos_oficiales": [
    {"tipo": "docx", "descripcion": "texto vigente (SCJN)", "url": "https://legislacion.scjn.gob.mx/Buscador/Paginas/AbrirDocArticulo.aspx?q=…"},
    {"tipo": "docx", "descripcion": "LEY · 26 SECCION SEGUNDA", "fecha": "1970-04-01", "url": "https://legislacion.scjn.gob.mx/…"},
    {"tipo": "pdf", "descripcion": "LEY · 26 SECCION SEGUNDA", "fecha": "1970-04-01", "url": "https://legislacion.scjn.gob.mx/…"},
    "… (114 más)"
  ],
  "ficha_scjn": "https://legislacion.scjn.gob.mx/Buscador/Paginas/wfOrdenamientoDetalle.aspx?IdOrd=410&Vig=1&TPub=6",
  "markdown_versionado": "https://github.com/elimorals/legalize-mx/blob/main/mx/5a/LFT.md",
  "historial_git": "https://github.com/elimorals/legalize-mx/commits/main/mx/5a/LFT.md",
  "dataset": "https://huggingface.co/datasets/elimoralsmendox/legalize-mx"
}
```

Al citar una norma, la referencia es `ficha_scjn` o el `documentos_oficiales` de la publicación correspondiente, no el Markdown. El Markdown es la copia de trabajo; la fuente es el documento oficial.

---

## cobertura

### Un municipio

```json
cobertura(estado="JAL", municipio="Zapopan")
```
```json
{
  "municipios": [
    {
      "state": "JAL",
      "inegi": "120",
      "name": "Zapopan",
      "classification": "abierta",
      "population": 1476491,
      "domain": "www.zapopan.gob.mx",
      "normatividad_url": "https://www.zapopan.gob.mx/v3/inclusion/normatividad/reglamentos-de-aplicacion-municipal",
      "gaceta_url": "https://www.zapopan.gob.mx/v3/normatividad/gacetas-municipales?keys&field_anio_value=2026",
      "state_carrier": "[{\"source\": \"Congreso de Jalisco — Biblioteca Virtual, leyes de ingresos municipales\", …}]",
      "normas_indexadas": 198,
      "con_texto": 4
    }
  ]
}
```

**Valores de `classification`** (del censo de los 2,478 municipios):

| Valor | Significa |
|---|---|
| `abierta` | El municipio publica sus normas en su propio sitio |
| `compilacion_estatal` | Sus normas no fiscales las publica el periódico oficial o una compilación del estado |
| `compilacion_estatal_solo_fiscal` / `compilacion_estatal_ley_ingresos` | Solo hay sus leyes de ingresos o presupuestos, emitidos por el congreso |
| `sitio_sin_normas` | Tiene sitio, pero el rastreador no encontró normas. No quiere decir que no existan |
| `sin_sitio` | No se encontró dominio oficial |
| `bloqueado` | El sitio tiene WAF o captcha |
| `sin_verificar` | No se pudo comprobar |

### Un estado

```json
cobertura(estado="OAX")
```
```json
{
  "normas": {
    "scjn": {"total": 8439, "con_texto": 1171},
    "oaxaca-poe-municipal": {"total": 9680, "con_texto": 0},
    "congreso-oax": {"total": 279, "con_texto": 0},
    "muni-wordpress-2": {"total": 67, "con_texto": 0},
    "muni-html-2": {"total": 22, "con_texto": 0}
  },
  "por_rango": {"ley": 9437, "ley_de_ingresos": 6837, "reglamento": 1050, "bando": 485, "manual": 157, "…": "…"},
  "municipios_por_clasificacion": {
    "compilacion_estatal": {"municipios": 302, "poblacion": 2791430},
    "compilacion_estatal_solo_fiscal": {"municipios": 238, "poblacion": 988733},
    "abierta": {"municipios": 30, "poblacion": 351985}
  }
}
```

### Todo el país

```json
cobertura()
```
```json
{
  "normas": {
    "scjn": {"total": 110862, "con_texto": 33974},
    "oaxaca-poe-municipal": {"total": 9680},
    "dof-nom": {"total": 6698},
    "dof": {"total": 6483},
    "puebla-ojp": {"total": 6283},
    "…": "53 fuentes"
  },
  "por_rango": {"reglamento": 56128, "ley": 33291, "ley_de_ingresos": 27378, "presupuesto": 13345, "acuerdo": 9232,
                "codigo": 6842, "bando": 4756, "nom": 4121, "tratado": 1536, "…": "…"},
  "municipios_por_clasificacion": {
    "compilacion_estatal": {"municipios": 751, "poblacion": 20849190},
    "abierta": {"municipios": 695, "poblacion": 81546126},
    "compilacion_estatal_solo_fiscal": {"municipios": 302, "poblacion": 2632826},
    "sitio_sin_normas": {"municipios": 259, "poblacion": 9028789},
    "compilacion_estatal_ley_ingresos": {"municipios": 236, "poblacion": 6327077},
    "sin_sitio": {"municipios": 148, "poblacion": 2590154},
    "sin_verificar": {"municipios": 71, "poblacion": 1824923},
    "bloqueado": {"municipios": 16, "poblacion": 1214939}
  },
  "indice": {"version": "202610162229", "norms": "192146", "with_text": "33974"}
}
```

---

## dof_del_dia y leer_nota_dof

Las dos consultan la API oficial del DOF en el momento, sin pasar por el índice. Sirven para lo publicado hoy, que todavía no entra al índice.

```json
dof_del_dia(fecha="2026-10-16")
```
```json
{
  "fecha": "2026-10-16",
  "fuente": "API oficial del DOF (en vivo)",
  "n": 6,
  "notas": [
    {"codigo": 5801377,
     "titulo": "Acuerdo por el que se crea la Academia del Centro Nacional de Inteligencia, Órgano Administrativo Desconcentrado de la Secretaría de Seguridad y Protección Ciudadana.",
     "dependencia": "SECRETARIA DE SEGURIDAD Y PROTECCION CIUDADANA", "pagina": 4, "edicion": "matutinas",
     "url": "https://www.dof.gob.mx/nota_detalle.php?codigo=5801377&fecha=16/10/2026"},
    {"codigo": 5801379,
     "titulo": "Acuerdo por el que se modifica el diverso por el que se da a conocer a los gobiernos de las entidades federativas la distribución y calendarización … Ramos Generales 28 …",
     "dependencia": "SECRETARIA DE HACIENDA Y CREDITO PUBLICO"},
    {"codigo": 5801381,
     "titulo": "Circular por la que se comunica a las dependencias y entidades de la Administración Pública Federal … que deberán abstenerse de aceptar propuestas …",
     "dependencia": "SECRETARIA ANTICORRUPCION Y BUEN GOBIERNO"},
    {"codigo": 5801398,
     "titulo": "Acuerdo del Consejo General del Instituto Nacional Electoral por el que se establecen los criterios y plazos de procedimientos relacionados con el periodo de precampañas para el Proceso Electoral Federal 2026-2027.",
     "dependencia": "INSTITUTO NACIONAL ELECTORAL"},
    "… (2 más)"
  ]
}
```

Por defecto solo devuelve lo normativo: decretos, acuerdos, reglamentos, NOM, lineamientos, reglas, circulares… Con `solo_normativas=false` también trae avisos, convocatorias y edictos (ese día, 118 notas en total).

```json
leer_nota_dof(codigo="5801377", max_caracteres=500)
```
```json
{
  "codigo": "5801377",
  "titulo": "Acuerdo por el que se crea la Academia del Centro Nacional de Inteligencia, Órgano Administrativo Desconcentrado de la Secretaría de Seguridad y Protección Ciudadana.",
  "fecha": "16-10-2026",
  "caracteres": 9006,
  "texto": "ACUERDO por el que se crea la Academia del Centro Nacional de Inteligencia … Al margen un sello con el Escudo Nacional, que dice: Estados Unidos Mexicanos.- Seguridad.- Secretaría de Seguridad y Protección Ciudadana. MTRO. OMAR HAMID GARCÍA …",
  "caracteres_totales": 9006,
  "siguiente_desde": 500
}
```

CLI: `legalize-mx dof`, `legalize-mx dof --fecha 2026-10-16 --todas`, `legalize-mx nota-dof 5801377`.

---

## actualizar_indice y aviso_indice

Cuando se publica un índice más nuevo que el tuyo, `buscar_norma`, `cobertura` e `info` lo avisan:

```json
{
  "resultados": ["…"],
  "aviso_indice": "Hay un índice más reciente (202611010300; el tuyo es 202610162229). Ejecuta actualizar_indice() para usarlo."
}
```

Si tu copia tiene más de 7 días, el aviso cambia:

```json
{"aviso_indice": "El índice tiene 9 días: las normas publicadas después pueden faltar. Confirma lo reciente con dof_del_dia() o la fuente oficial."}
```

Para actualizar sin reiniciar:

```json
actualizar_indice()
```
```json
{"antes": "202610162154", "ahora": "202610162229", "archivo": "~/.cache/legalize-mx/index-202610162229.sqlite", "actualizado": true}
```

CLI: `legalize-mx actualizar`. El texto y el historial de cada ley siempre vienen de GitHub, así que reflejan la última reforma publicada aunque tu índice sea de días antes.

---

## Flujos completos de un agente

Estas son las secuencias de llamadas que hace un agente bien instruido para preguntas reales.

### "¿Cuántas horas puede durar la jornada laboral según la ley?"

1. `buscar_norma(texto="ley federal del trabajo", estado="federal", limite=1)` devuelve `LFT`.
2. `articulo(id="LFT", numero="61")` devuelve *"La duración de la jornada diaria será de ocho horas la diurna, siete la nocturna y siete horas y media la mixta."*
3. `historial(id="LFT")` muestra una reforma del 1 de mayo de 2026 (DECRETO 111/2026) que tocó los artículos 58 a 71.
4. `diff(id="LFT", fecha_a="2026-04-30", fecha_b="2026-05-02")` compara la versión del 15 de enero con la del 1 de mayo y lista el 61 entre los reformados, con su diff.
5. `fuentes(id="LFT")` da la ficha de la SCJN y el decreto en el DOF para citar.

La respuesta: cita el artículo 61 vigente, dice desde cuándo rige y qué decía antes, y enlaza el DOF.

### "¿Qué dice el reglamento de tránsito de Monterrey sobre estacionarse en doble fila?"

1. `buscar_norma(texto="reglamento transito", municipio="Monterrey")` devuelve `NLE-reglamento-de-vialidad-y-transito-del-municipio-de-81535` con `has_text=true`.
2. `leer_norma(id="NLE-reglamento-de-vialidad-y-transito-del-municipio-de-81535")`. Si es largo, sigue con `desde=siguiente_desde` hasta encontrar "doble fila", y luego pide ese artículo con `articulo`.
3. `fuentes(id=<id>)` da el enlace oficial del documento.

Si el resultado trajera `has_text=false`, el paso 2 sería `leer_norma(id=<id>, extraer_en_vivo=true)`, que baja el documento del portal y lo extrae. Si no hubiera ningún resultado, `cobertura(estado="NLE", municipio="Monterrey")` dice dónde publica Monterrey su normativa (`normatividad_url`, `gaceta_url`).

### "¿Salió algo hoy en el DOF sobre la NOM-051?"

1. `dof_del_dia()` lista lo normativo de hoy, y el agente busca "NOM-051" en los títulos.
2. Si aparece, `leer_nota_dof(codigo=<codigo>)` trae el texto completo.
3. Para la historia de la norma: `buscar_norma(texto="NOM-051", fuente="dof")` devuelve todas sus etapas (proyecto, modificación, respuestas a comentarios) ordenadas por relevancia, cada una con su fecha.

### "¿Qué decía originalmente el artículo 27 constitucional y qué cambió?"

1. `articulo(id="CPEUM", numero="27", fecha="1920-01-01")` da el texto de 1917.
2. `articulo(id="CPEUM", numero="27")` da el texto vigente.
3. `historial(id="CPEUM")` lista las reformas que tocaron el artículo 27, buscando "27" en `articulos_afectados`, con su fecha y decreto.

> **Aviso conocido.** Algunas versiones históricas intermedias de unas cuantas leyes, entre ellas la CPEUM, quedaron mezcladas con el texto de otra norma por un error de la fuente al descargarlas. Se reconoce porque un `diff` marca cientos de artículos "reformados" de golpe. El texto vigente no está afectado. La corrección está en curso.

---

## Errores y límites

| Respuesta | Qué pasó | Qué hacer |
|---|---|---|
| `{"error": "no encontré la norma 'X'"}` | El id no existe | Obtenlo con `buscar_norma` |
| `{"error": "la norma no existía el 1900-01-01"}` | La fecha es anterior a la publicación | Usa una fecha posterior a `publication_date` |
| `{"error": "no encontré el artículo '311 bis'", "parecidos": [...]}` | Ese artículo no está en esa versión | Revisa `parecidos`, o prueba con otra fecha |
| `"texto_disponible": false` | La norma está catalogada pero sin texto procesado | `extraer_en_vivo=true`, o abre `documentos_oficiales` |
| `"nota": "el PDF parece escaneado …"` | El documento oficial es una imagen | Hace falta OCR: abre el PDF |
| `GitHub limits anonymous API use to 60 requests/hour` | Se agotó el cupo anónimo de GitHub para `historial`, `diff` y lecturas por fecha | Define `GITHUB_TOKEN`, o espera. Los historiales consultados quedan en caché 24 h |
| `"aviso_indice": …` | Tu índice no es el más reciente | `actualizar_indice()` |

**Qué no hace (todavía):**

- **Jurisprudencia y tesis:** el Semanario Judicial no está incluido.
- **Búsqueda en el texto completo de cada artículo:** el índice cubre el título, el inicio y los encabezados. Para lo demás, lee la norma o el artículo.
- **OCR en vivo:** los PDF escaneados se devuelven como enlace.
- **Historial de las normas sin texto:** solo trae su lista de publicaciones (`publicaciones_scjn`).
