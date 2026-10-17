---
name: legalize-mx
description: Consulta legislación mexicana real (federal, de las 32 entidades, municipal, tratados, NOM y DOF) con el MCP legalize-mx, incluido el texto que regía en una fecha pasada y qué cambió entre reformas, y la cita con su fuente oficial. Cárgala antes de llamar cualquier herramienta del MCP legalize-mx (buscar_norma, articulo, dof_del_dia…), porque dice en qué orden usarlas y cómo citar. Úsala siempre que el usuario pregunte qué dice, exige, prohíbe o permite una ley, código, reglamento, bando, NOM, decreto o la Constitución en México, o un artículo concreto ("art. 27 constitucional", "artículo 61 de la LFT"); cuando pregunte cómo era una norma antes, desde cuándo rige o qué cambió en una reforma; qué publicó hoy el DOF; o qué normativa tiene un estado o municipio (Zapopan, Oaxaca, CDMX…). También cuando un contrato, trámite, política o análisis de cumplimiento dependa de una norma mexicana, aunque el usuario no mencione la herramienta. No la uses para leyes de otros países ni para jurisprudencia o tesis de la SCJN, que este MCP no cubre.
---

# Legislación mexicana con legalize-mx

Este MCP da acceso a ~192,000 normas mexicanas: catálogo de la SCJN, 31 congresos, Diputados, DOF, periódicos oficiales y ~600 portales municipales. De ~34,000 tiene el texto completo con **todas sus reformas versionadas**. Para el resto tiene el enlace oficial y puede extraer el documento en vivo.

Su valor es que responde **con el texto real y la fuente**, no de memoria. La legislación mexicana se reforma constantemente: la LFT tuvo dos reformas en mayo de 2026. Una respuesta de memoria puede estar desactualizada sin que nadie lo note. Por eso, ante cualquier pregunta normativa, consulta el MCP antes de responder, aunque creas saber la respuesta.

## Herramientas

| Herramienta | Para qué |
|---|---|
| `buscar_norma(texto, estado?, municipio?, tipo?, vigente?, con_texto?, fuente?)` | Encontrar la norma y su `id`. Siempre es el primer paso |
| `articulo(id, numero, fecha?)` | Un artículo, vigente o a una fecha. La forma más barata de responder |
| `leer_norma(id, fecha?, desde?, extraer_en_vivo?)` | Texto completo, por partes |
| `historial(id)` | Reformas: fecha, decreto, artículos afectados |
| `diff(id, fecha_a, fecha_b?)` | Qué artículos cambiaron entre dos fechas, con el antes y el después |
| `fuentes(id)` | Enlaces oficiales para citar |
| `cobertura(estado?, municipio?)` | Qué hay y qué falta de un lugar, y dónde publica cada municipio |
| `dof_del_dia(fecha?)` / `leer_nota_dof(codigo)` | El DOF de hoy o de una fecha, en vivo |
| `actualizar_indice()` | Si alguna respuesta trae `aviso_indice` |

## Flujo

1. **Encuentra el `id` con `buscar_norma`.**
   - Usa el nombre de la norma y filtra por lugar: `estado="federal"`, `estado="JAL"`, `municipio="Zapopan"`.
   - Las leyes federales tienen id corto (`CPEUM`, `LFT`, `LGS`, `LAMP`, `CFF`…), pero confírmalo buscando.
   - Si hay varias parecidas, prefiere la que tenga `status: "in_force"` y `has_text: true`, salvo que pregunten por una abrogada.
2. **Responde con lo mínimo necesario.**
   - Si la pregunta apunta a un artículo, usa `articulo`.
   - Si no sabes cuál artículo es, `leer_norma` por partes (`desde=siguiente_desde`) hasta ubicarlo, y luego pide ese artículo.
   - Las leyes grandes pesan más de un millón de caracteres: no las leas completas si no hace falta.
3. **Preguntas en el tiempo** ("¿cómo era…?", "¿desde cuándo…?", "¿qué cambió…?"):
   - Usa `historial` para ubicar la reforma.
   - Luego `articulo(..., fecha=)` antes y después, o `diff(id, fecha_a, fecha_b)`.
   - Las fechas no tienen que coincidir con una reforma: el MCP toma la versión vigente en esa fecha.
4. **Si la norma tiene `has_text: false`:**
   - `leer_norma(id, extraer_en_vivo=true)` baja el documento oficial y lo extrae. Así funcionan muchas normas municipales, estatales sin Word y notas del DOF.
   - Ese texto viene sin estructura de artículos ni historial. Si es un PDF escaneado no saldrá texto: dalo como enlace.
5. **Lo publicado en los últimos días** puede no estar en el índice. Confírmalo con `dof_del_dia` / `leer_nota_dof`.
6. **Cita siempre.** Usa `fuentes(id)` y da al menos el nombre exacto de la norma, el artículo, la fecha de la versión que usaste (`vigente_al` o la fecha de la versión) y el enlace oficial (`ficha_scjn` o el documento del DOF/periódico oficial).

## Cómo presentar la respuesta

- **Contesta la pregunta primero** y luego muestra el texto del artículo, citado tal cual entre comillas o en bloque. No parafrasees la parte operativa: en derecho, la redacción exacta importa.
- **Dí qué versión usaste:** "vigente al 14 de mayo de 2026" o "texto de 1917". Si la norma fue reformada después de la fecha que pidió el usuario, menciónalo.
- **Si algo no está o no se pudo verificar, dilo.** Por ejemplo, la norma está catalogada pero sin texto, el PDF es escaneado o el municipio no publica en línea. No rellenes con memoria. `cobertura` sirve para explicar qué existe y qué no en un lugar.
- **Cierra con una advertencia breve** cuando la respuesta se vaya a usar en un caso real: es información de consulta; para un asunto concreto conviene un abogado y la verificación en la fuente oficial.

Ejemplo de respuesta bien formada:

> La jornada máxima diurna es de **ocho horas** (LFT, art. 61):
>
> > "La duración de la jornada diaria será de ocho horas la diurna, siete la nocturna y siete horas y media la mixta."
>
> Texto vigente al 14 de mayo de 2026. Ese artículo se reformó el 1 de mayo de 2026 (DECRETO 111/2026), así que antes de esa fecha la redacción era distinta.
> Fuente: [Ley Federal del Trabajo, SCJN](https://legislacion.scjn.gob.mx/Buscador/Paginas/wfOrdenamientoDetalle.aspx?IdOrd=410&Vig=1&TPub=6).

## Detalles que evitan errores

- **Números de artículo:** se aceptan `"27"`, `"27o"`, `"3 bis"`, `"283 quater"` y `"primero"`. Muchos decretos abren con "ARTÍCULO PRIMERO.- Se expide…" y los transitorios reinician la numeración. Si llegan `otras_coincidencias`, revisa que el artículo devuelto sea el del cuerpo de la ley.
- **Búsqueda:** cubre el título, el inicio del texto y los encabezados, no cada artículo. Si un concepto no aparece, busca la ley que lo regularía ("teletrabajo" → Ley Federal del Trabajo) y luego lee o pide el artículo.
- **Estados:** van con clave de 3 letras (`JAL`, `NLE`, `CMX`, `MEX`, `OAX`…) o `federal`. Los municipios van por nombre o clave INEGI.
- **NOM:** cada etapa es una nota distinta del DOF (`proyecto-nom`, `nom`, prórroga, cancelación). Para el texto en vigor, busca la definitiva (`tipo="nom"`) más reciente y su modificación posterior, si existe.
- **Versiones históricas sospechosas:** si un `diff` marca cientos de artículos "reformados" de golpe, o un artículo histórico no tiene que ver con la ley, puede ser una versión contaminada (error conocido de la fuente, en corrección). No la uses. Avisa al usuario y apóyate en el texto vigente o en el PDF oficial de esa reforma (`historial` → `publicaciones_scjn`).
- **Si aparece `aviso_indice`:** avísale al usuario y llama `actualizar_indice()` si la pregunta depende de algo reciente.
- **`GITHUB_TOKEN`:** sin token, GitHub permite 60 consultas por hora de historial y de lecturas por fecha. Si se agota, dilo y sugiere configurar un `GITHUB_TOKEN`.

## Fuera de alcance

- **Jurisprudencia y tesis (Semanario Judicial):** no están incluidas. Dilo, y no las inventes.
- **Interpretación legal de un caso concreto:** da el texto y su contexto normativo, no un dictamen.
- **Leyes de otros países.**
