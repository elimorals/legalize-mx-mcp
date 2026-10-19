# Roadmap

La meta es ser **la fuente abierta más completa y confiable de derecho mexicano para agentes**: más cobertura que los servicios cerrados, historial verificable y todo con fuente oficial.

Hoy vamos adelante en el nivel municipal, el historial de reformas, el DOF y la apertura de los datos. Vamos atrás en jurisprudencia, en la proporción de normas con texto y en la calidad de parte del historial. Este documento dice cómo se cierra cada brecha.

## Dónde estamos frente a otros MCP de derecho mexicano

| | Lex API MX | Corpus Iuris | Ansvar / LexMex | **legalize-mx** |
|---|---|---|---|---|
| Leyes federales | Sí | Sí | Parcial | **Sí** |
| Estatales (32) | No | Sí (6,710 leyes) | No | **Sí, catálogo completo de la SCJN** |
| Municipal | No | No | No | **~600 portales + censo de 2,478 municipios** |
| NOM, lineamientos, DOF | No | Parcial | No | **Sí** |
| Historial y texto a una fecha | Con fecha | Vigencia fechada | No | **Todas las reformas en git, diff por artículo** |
| Jurisprudencia y tesis | No | **311,701 tesis** | No | **No (prioridad 1)** |
| Abierto, sin clave | No (clave + plan) | No (OAuth) | Sí | **Sí** |

---

## Prioridad 1: Calidad del historial

**El problema.** La SCJN sirvió el Word de otra norma en algunas reformas, y el pipeline lo aceptó como si fuera una versión.

| Alcance (detector del 16-oct-2026) | Versiones | Leyes |
|---|---:|---:|
| Total contaminado | 988 | 825 |
| Federal (24 leyes codificadas, entre ellas CPEUM, CFF, LGS, LIVA, LGIPE) | 156 | 129 |
| Estatal | 796 | 664 |
| CDMX | 35 | 31 |
| Ya publicadas como commit | 962 | 801 |
| **Texto vigente (HEAD) ajeno** | **196** | **196** |

**Lo ya hecho**
- **Causa encontrada:** el pipeline validaba que el archivo fuera un Word, pero no que fuera de esa norma. Lo más probable, sin confirmar, es que el servidor de la SCJN mezcle respuestas entre peticiones simultáneas: en el 89 % de los casos, la norma afectada y la ajena se descargaron con menos de 15 minutos de diferencia.
- **Corrección integrada:** el pipeline descarta toda versión cuyo texto no corresponda a la norma, en cosecha, reproceso y actualización diaria. Tiene 12 tests.
- **Detector:** precisión de ~98 %. Es censo versión por versión en `versiones-contaminadas.jsonl`.

**Hecho el 17-oct-2026:** se reconstruyeron **824 leyes sin 985 versiones ajenas** y se reescribió el historial público con *force push*: la CPEUM bajó de 245 a 236 versiones. También se regeneró el dataset de Hugging Face. Hay un respaldo del estado anterior. Las 3 detecciones dudosas, con similitud ≥ 0.3, se conservaron.

**Lo que falta**
1. Volver a bajar, en un solo proceso, las reformas que queden con hueco.
2. **Verificación permanente:** un chequeo de identidad en cada publicación, que falle si una versión no nombra su norma o difiere demasiado de sus vecinas.

## Prioridad 1: Jurisprudencia y tesis

**Meta:** igualar o superar a Corpus Iuris. Son las **312,089 tesis** del Semanario Judicial (50,611 jurisprudencias y 261,478 aisladas), más 23,071 ejecutorias, 10,226 votos y 4,082 acuerdos generales.

1. **Fuente ya mapeada:** la API del Semanario (`sjf2.scjn.gob.mx/services/sjftesismicroservice/api/public/tesis`) devuelve JSON con texto completo.
2. **Descarga** en un solo proceso, a ≤0.5 peticiones por segundo (~8 días), cuando termine la cosecha legislativa. Comparte protección anti-bots con el buscador legislativo, así que no deben correr a la vez.
3. **Otras fuentes:** tesis del TEPJF y del TFJA. Las de tribunales estatales, donde se puedan obtener.
4. **Herramientas nuevas:** `buscar_tesis(texto, epoca?, instancia?, materia?, tipo?)`, `leer_tesis(registro)` y `tesis_de_articulo(id, numero)`, que da los criterios que interpretan un artículo dado.
5. **Vínculo ley ↔ tesis:** extraer de cada tesis los artículos que cita y enlazarlos con la norma en el índice. Ningún competidor lo ofrece.

## Prioridad 2: Texto completo para todo lo catalogado

**Hoy:** 34,000 normas con texto e historial, de 192,000 catalogadas.

1. **Texto de los PDF de la SCJN:** ~74,000 normas sin Word. **39,864 extraídas** (31,840 de la capa de texto del PDF + 7,886 con OCR + 138 con OCR parcial) y **en publicación desde el 19-oct-2026**, como `as_enacted` con `text_source: pdf/ocr`. El MCP lo avisa en `aviso_texto`. Las ~31,000 restantes esperan a que bajen sus PDF.
2. **Capa de texto para las fuentes nuevas:** congresos, periódicos oficiales, municipios y DOF, más la deduplicación contra la SCJN. Una norma con dos fuentes oficiales queda con una sola identidad y ambas fuentes.
3. **OCR** para los PDF escaneados de municipios y periódicos oficiales.
4. **Índice con búsqueda en el texto completo** de cada artículo, no solo en el título y el inicio. Sería un índice opcional "completo", de unos 2–3 GB.

## Prioridad 2: Calidad de la skill y del MCP

1. **Batería completa de pruebas de la skill:** preguntas reales con y sin skill, calificación objetiva (cita exacta, versión, fuente, cero inventos) y ajuste automático de la descripción para que se active cuando debe.
2. **Pruebas de regresión del MCP** contra preguntas con respuesta conocida: artículos, fechas y diffs verificados a mano.
3. **Métricas públicas de calidad por fuente:** precisión del recorte de PDF, normas con texto y versiones verificadas.

## Prioridad 3: Cobertura que falta

- **Veracruz:** 212 municipios, con el 38 % de su población cubierta. Su gaceta tiene reCAPTCHA; hay que pedir datos abiertos o buscar otra vía oficial.
- **CDMX (gaceta), POE de Michoacán y congreso de SLP:** bloqueados o caídos.
- **POE de Aguascalientes:** requiere ~20,000 llamadas por listado.
- **103 sitios municipales descartados** y **407 municipios** "sin sitio" o "sin normas encontradas": requieren búsqueda manual o un navegador para los sitios que cargan por JavaScript.
- **Regulación de organismos autónomos y dependencias** (CNBV, Banxico, SAT, COFEPRIS…) que no pasa por el DOF.

## Prioridad 3: Operación

- **Actualización diaria automática** de todas las fuentes, no solo de la SCJN y el DOF, con publicación del índice.
- **Servidor HTTP público opcional** (Hugging Face Spaces) para clientes que no pueden correr procesos locales.
- **Publicación en PyPI** (`uvx legalize-mx-mcp`) y en los directorios de MCP.
