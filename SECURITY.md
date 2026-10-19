# Seguridad

## Reportar una vulnerabilidad

Abre un *security advisory* privado en GitHub (pestaña **Security → Report a vulnerability** de `elimorals/legalize-mx-mcp`). No uses un issue público. Respondo en un plazo de una semana.

## Qué no contiene este repo

- **Credenciales.** No hay claves, tokens ni contraseñas en el código ni en el historial de git. Se verificó con `detect-secrets` sobre todas las versiones de cada archivo.
- **Datos personales.** Solo hay legislación pública y enlaces oficiales.
- El único secreto que el MCP usa es un `GITHUB_TOKEN` **opcional**, que el usuario pone en su propio entorno. Solo se envía a `api.github.com`, y `httpx` lo quita si una redirección lleva a otro dominio.

## Modelo de amenazas y defensas

| Riesgo | Defensa |
|---|---|
| **SSRF:** que un índice manipulado o una redirección de un portal hagan que el MCP pida `localhost`, la red interna o el endpoint de metadatos de la nube | Antes de **cada** petición, redirecciones incluidas, se resuelve el host y se rechaza todo lo que no sea `http(s)` hacia una IP pública (`remote.check_public_url`). Máximo 5 redirecciones |
| **Documentos enormes** o respuestas infinitas | Descarga con tope (`LEGALIZE_MX_MAX_DOC_MB`, 100 MB por defecto) |
| **Bombas zip en .docx** y **expansión de entidades XML** | Tope al tamaño descomprimido de `document.xml`. Se rechaza cualquier `.docx` que declare `DOCTYPE` o `ENTITY` |
| **PDF malicioso** | Se procesa con `pdftotext` en un directorio temporal, como proceso aparte, con *timeout* de 300 s y sin shell |
| **Índice SQLite manipulado** | Se abre en solo lectura, con `trusted_schema = OFF` y en modo defensivo (Python 3.12+). El `sha256` del manifiesto se verifica, y la descompresión tiene tope (`LEGALIZE_MX_MAX_INDEX_GB`) |
| **Inyección SQL** | Todas las consultas van parametrizadas. El texto de búsqueda se reduce a palabras (`\w+`) entre comillas de FTS5 |
| **Inyección de comandos** | `git` y `pdftotext` reciben listas de argumentos, sin shell, con `--` antes de las rutas |
| **Caché** | Nombres de archivo por hash: sin *path traversal* |
| **Servidor HTTP expuesto** | Escucha en `127.0.0.1` por defecto. Con otro `--host` muestra un aviso, porque **no tiene autenticación**; si lo expones, ponlo detrás de un proxy con autenticación |

## Confianza en los datos

El MCP confía en tres orígenes: el dataset `elimoralsmendox/legalize-mx` de Hugging Face (índice), el repo `elimorals/legalize-mx` de GitHub (texto e historial) y los portales oficiales (documentos en vivo).
- El `sha256` del índice protege contra corrupción en la descarga, **no** contra que alguien controle la cuenta que lo publica.
- Si usas el MCP para decisiones sensibles, verifica siempre contra el documento oficial que devuelve `fuentes()`.

## Dependencias

Solo `httpx` y `mcp`, más `pypdf` como opción. `uv.lock` fija las versiones. La última auditoría con `pip-audit`, el 19-oct-2026, no encontró vulnerabilidades conocidas.
