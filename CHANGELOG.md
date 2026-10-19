# Cambios

## v0.1.0 — 2026-10-19 (beta pública)

Primera versión pública.

**Herramientas**

- **Búsqueda y lectura:** `buscar_norma` (texto completo con filtros por estado, municipio, tipo, vigencia, fuente y texto disponible), `leer_norma` (vigente o a una fecha, paginado, con extracción en vivo del documento oficial) y `articulo` (vigente o a una fecha; acepta bis, ter, quáter y ordinales).
- **Historial y fuentes:** `historial` (cada reforma con fecha, decreto y artículos afectados), `diff` (cambios artículo por artículo entre dos fechas) y `fuentes` (enlaces oficiales para citar).
- **Cobertura y DOF:** `cobertura` (normas por fuente y tipo, y censo de los 2,478 municipios), `dof_del_dia` y `leer_nota_dof` (DOF en vivo).
- **Mantenimiento:** `actualizar_indice`.
- **CLI `legalize-mx`** con los mismos subcomandos.

**Datos**

- Índice de ~215,000 normas de 53 fuentes oficiales: SCJN, 31 congresos, Consejería CDMX, Diputados, DOF, periódicos oficiales y ~600 portales municipales.
- ~34,000 normas con texto consolidado y todas sus reformas en git, con fechas legislativas reales (incluso anteriores a 1970).
- Historial corregido: se eliminaron 985 versiones con texto de otra norma en 824 leyes, y 817 leyes recuperaron sus reformas.

**Calidad y seguridad**

- **Avisos en las respuestas:** `aviso_texto` (texto como se publicó, o de OCR) y `aviso_indice` (índice desactualizado).
- **Protecciones:** SSRF, tope de tamaño a las descargas, bombas zip y entidades XML en .docx, e índice SQLite tratado como no confiable. Ver [SECURITY.md](SECURITY.md).
- **Plugin de Claude Code** con la skill `legalize-mx`: activación medida en 19/20 (recall 10/10).
- **Pruebas:** 24 tests offline y CI en Linux y macOS, Python 3.10–3.13.

**Pendiente para v1.0:** ver [ROADMAP.md](ROADMAP.md). Lo principal: publicar ~40,000 textos de PDF (como se publicaron), actualizar el índice a diario sin depender de una máquina personal y agregar jurisprudencia.
