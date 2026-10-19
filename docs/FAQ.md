# Preguntas frecuentes

**¿Es oficial?**
No. Es una copia de consulta tomada solo de fuentes oficiales: SCJN, DOF, congresos, periódicos oficiales y portales municipales. Cada respuesta trae el enlace al documento oficial, que es el que vale. Para un asunto real, verifica ahí y consulta a un abogado.

**¿Tiene todas las leyes de México?**
Tiene catalogadas ~215,000 normas de 53 fuentes: federales, de las 32 entidades, tratados, NOM y lineamientos del DOF, y normativa municipal. El texto completo procesado y versionado existe para una parte de ellas; las demás se pueden leer en vivo desde su portal. Los números exactos y lo que falta (por ejemplo Veracruz, por reCAPTCHA, o los municipios sin sitio) están en [FUENTES.md](FUENTES.md), en `cobertura()` y en el [ROADMAP](../ROADMAP.md).

**¿Qué diferencia hay entre `point_in_time` y `as_enacted`?**
- `point_in_time` es el texto **consolidado**: cada versión incorpora sus reformas, así que el texto a una fecha es el que estaba vigente ese día.
- `as_enacted` es el texto **tal como se publicó** en el periódico oficial, cuando la fuente no tiene versión consolidada. Sus reformas aparecen en `historial()`, pero el texto no las incorpora; la respuesta lo dice en `aviso_texto`.

**¿Qué tan confiable es el texto de OCR?**
El texto reconocido es bueno: la mediana es de 0.96 palabras válidas por cada palabra. Pero en documentos escaneados puede haber errores en cifras, nombres y tablas. Esas respuestas traen `aviso_texto`, y las cifras conviene confirmarlas con el PDF oficial (`fuentes()`).

**¿Incluye jurisprudencia y tesis?**
Todavía no. Está en prioridad 1 del [ROADMAP](../ROADMAP.md): son 312 mil tesis del Semanario Judicial, más el vínculo de cada tesis con los artículos que interpreta.

**¿Qué tan actualizado está?**
- **El texto y el historial** se leen de GitHub al momento.
- **El índice** se republica conforme entran normas. Si el tuyo se atrasa, las respuestas traen `aviso_indice`.
- **Lo publicado hoy** se consulta con `dof_del_dia()`, que va en vivo al DOF.

**¿Por qué una búsqueda no encuentra una palabra que sé que está en la ley?**
El índice busca en el título, el inicio del texto y sus encabezados, no en cada artículo, para pesar ~90 MB y no varios GB. Busca la ley por su nombre y pide el artículo, o lee la ley por partes.

**Me salió "GitHub limits anonymous API use…"**
GitHub permite 60 consultas anónimas por hora para el historial y las lecturas por fecha. Configura `GITHUB_TOKEN` (cualquier token personal sirve), o apunta `LEGALIZE_MX_REPO` a un clon local del repo.

**¿Puedo usarlo sin internet?**
Sí, con dos variables de entorno:
- `LEGALIZE_MX_INDEX`, apuntando a un índice local;
- `LEGALIZE_MX_REPO`, apuntando a un clon local de `elimorals/legalize-mx`.

La extracción en vivo y el DOF del día sí necesitan red.

**¿Cuánto pesa?**
- **Índice:** ~90 MB de descarga y ~500 MB en disco, en `~/.cache/legalize-mx`.
- **Clon completo del repo, si lo quieres local:** ~2 GB.

**¿Puedo usarlo desde Claude.ai u otro cliente remoto?**
Sí, levantando el servidor HTTP (`legalize-mx-mcp --http`) en una máquina accesible y registrándolo como conector remoto.

**¿Cómo reporto un error en un texto?**
Abre un issue en `elimorals/legalize-mx-mcp` con el `id` de la norma, la fecha que consultaste y qué está mal. Los errores de datos se corrigen reprocesando la ley completa, no con un parche encima.

**¿Qué licencia tiene?**
El código es MIT. Los textos legales son de dominio público: el art. 14, fr. VIII, de la Ley Federal del Derecho de Autor excluye de protección los textos legislativos, administrativos y judiciales oficiales.
