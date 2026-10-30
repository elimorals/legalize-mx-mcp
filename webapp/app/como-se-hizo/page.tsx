import type { Metadata } from "next";
import Link from "next/link";
import { Indice } from "@/components/guia";
import { Codigo } from "@/components/ui";

export const metadata: Metadata = {
  title: "Cómo se hizo: el ETL",
  description:
    "Cómo se extrae, procesa, versiona y publica la legislación de legalize-mx: fuentes oficiales, extracción, conversión a Markdown, historial en git, OCR, índice, controles de calidad y límites.",
};

// Every figure on this page was checked against the pipeline code, the git repo and the published
// index on 2026-10-30. Update the date when the numbers change.
const CORTE = "30 de octubre de 2026";

function Tabla({ cab, filas, num = [] }: { cab: string[]; filas: (string | number)[][]; num?: number[] }) {
  return (
    <div className="tabla-scroll" style={{ margin: "0 0 20px" }}>
      <table>
        <thead><tr>{cab.map((c, i) => <th key={c} className={num.includes(i) ? "n" : ""}>{c}</th>)}</tr></thead>
        <tbody>
          {filas.map((f, j) => (
            <tr key={j}>{f.map((v, i) => (
              <td key={i} className={num.includes(i) ? "n" : i === f.length - 1 && !num.includes(i) ? "ancho" : ""}>
                {typeof v === "number" ? v.toLocaleString("es-MX") : v}
              </td>
            ))}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const ETAPAS: [string, string][] = [
  ["Descubrimiento", "Recorre el buscador legislativo de la SCJN ámbito por ámbito (federal, CDMX, cada estado y tratados) y arma un catálogo con una ficha por norma."],
  ["Extracción", "Por cada norma lee su tabla de reformas y baja, para cada fecha de publicación, el Word con el texto consolidado tal como quedó. Las demás fuentes oficiales se catalogan con sus enlaces."],
  ["Capa cruda", "Guarda cada documento original tal como lo sirve el portal, nombrado por su huella sha256: si dos fuentes publican el mismo archivo, se guarda una vez."],
  ["Transformación", "Convierte cada Word (o PDF, con OCR si hace falta) en Markdown: títulos, capítulos y artículos como encabezados; notas de reforma aparte; metadatos al inicio."],
  ["Historial", "Ordena las versiones de cada norma por fecha y escribe un commit de git por reforma, fechado con la publicación oficial."],
  ["Publicación", "Sube el repositorio a GitHub, exporta el catálogo y las leyes a Hugging Face y construye un índice de búsqueda que usan el MCP y esta web."],
];

export default function ComoSeHizo() {
  return (
    <section className="seccion texto lectura">
      <h1>Cómo se hizo</h1>
      <p className="lead">
        legalize-mx convierte la legislación mexicana publicada en portales oficiales en datos abiertos y verificables:
        un archivo de texto por norma y un commit de git por reforma. Esta página describe el proceso completo, de la
        descarga a la publicación, con sus controles y sus límites.
      </p>
      <p className="faint">Cifras verificadas contra el código, el repositorio y el índice publicado al {CORTE}.</p>

      <Indice items={[
        ["resumen", "El proceso en seis etapas"], ["fuentes", "Fuentes"], ["extraccion", "Extracción"],
        ["transformacion", "Transformación"], ["historial", "Historial en git"], ["pdf", "Normas sin Word: PDF y OCR"],
        ["publicacion", "Publicación e índice"], ["calidad", "Calidad e integridad"], ["actualizacion", "Actualización"],
        ["limites", "Límites y pendientes"], ["reproducir", "Revisarlo tú"],
      ]} />

      <h2 id="resumen">El proceso en seis etapas</h2>
      <ol className="etapas">
        {ETAPAS.map(([t, d]) => <li key={t}><b>{t}</b><span>{d}</span></li>)}
      </ol>
      <p>
        La fuente principal es el buscador legislativo de la <b>Suprema Corte de Justicia de la Nación</b>: por cada
        reforma de una norma ofrece el Word con el texto consolidado a esa fecha, y eso permite reconstruir su historia
        completa. El DOF y la Cámara de Diputados aportan identificadores y sirven para detectar reformas nuevas. Las
        otras 52 fuentes oficiales se catalogan y se enlazan, pero aún no aportan texto.
      </p>

      <h2 id="fuentes">Fuentes</h2>
      <p>Solo fuentes oficiales. Conteos del índice publicado (versión 202610180210).</p>
      <Tabla
        cab={["Fuente", "Qué aporta", "Cómo se consulta", "Normas", "Con texto"]}
        num={[3, 4]}
        filas={[
          ["SCJN, buscador legislativo", "Catálogo federal, de la CDMX, de los 31 estados y tratados; un Word por reforma y el PDF del periódico oficial", "Páginas web (ASP.NET)", 110862, 33998],
          ["Cámara de Diputados (LeyesBiblio)", "Leyes federales vigentes y abrogadas; da la abreviatura que se usa como identificador (LFT, CPEUM)", "Páginas web", 628, 0],
          ["Diario Oficial de la Federación", "Notas normativas de cada día", "API oficial en JSON", 27594, 0],
          ["DOF, índice de NOM", "Normas Oficiales Mexicanas", "Páginas web", 6698, 0],
          ["Congresos estatales y Consejería de la CDMX", "Texto vigente de leyes estatales", "Páginas web o API de cada portal", 10377, 0],
          ["Periódicos oficiales y compilaciones estatales", "Normas estatales y municipales: bandos, reglamentos, leyes de ingresos", "Páginas web, WordPress, JSON", 37330, 0],
          ["Portales municipales", "Reglamentación publicada por los propios municipios", "WordPress, páginas web, JSON y hojas de cálculo", 21800, 0],
        ]}
      />
      <p className="dim">
        En total 215,289 normas de 53 orígenes. El Marco Geoestadístico del INEGI da las claves de los 2,478 municipios.
        La lista completa de portales está en <a href="https://github.com/elimorals/legalize-mx-mcp/blob/main/docs/FUENTES.md">docs/FUENTES.md</a>.
      </p>

      <h2 id="extraccion">Extracción</h2>
      <h3>Suprema Corte</h3>
      <ul>
        <li>El buscador es una aplicación web que pagina por <i>postback</i>: cada página de resultados necesita el estado de la anterior, así que se recorre en orden, como lo haría un navegador.</li>
        <li>La ficha de cada norma lista sus reformas de diez en diez, de la más nueva a la más vieja. De cada una se baja el Word del texto consolidado y se registra el enlace al PDF del periódico oficial.</li>
        <li>Si el portal responde con su protección anti-bots, la página no se procesa: se marca como bloqueada en lugar de leer basura.</li>
        <li>Un Word dañado (sin su <code>document.xml</code>) se reintenta una vez; si sigue mal, esa versión se salta y queda en el registro.</li>
      </ul>
      <h3>Diario Oficial y Cámara de Diputados</h3>
      <ul>
        <li>El DOF se lee de su API oficial: las notas de cada día (ediciones matutina, vespertina y extraordinaria) y el texto de cada nota.</li>
        <li>Se descartan avisos y convocatorias. El histórico recorrido va de junio de 1992 a septiembre de 2026.</li>
        <li>De Diputados se toman los índices de leyes vigentes, abrogadas y reglamentos.</li>
      </ul>
      <h3>Cortesía con los portales</h3>
      <ul>
        <li>Como máximo una petición por segundo por portal, con esperas crecientes ante errores temporales (409, 429, 502, 503, 504) y un agente identificado como <code>legalize-bot</code>.</li>
        <li>Los portales que piden ir más lento se respetan (Morelos a una petición cada cuatro segundos; la API de San Luis Potosí, 100 por minuto).</li>
        <li>No se rodean captchas ni protecciones: esos portales quedan sin cubrir (ver <a href="#limites">límites</a>).</li>
        <li>Una norma solo se vuelve a escribir si cambian su enlace, su huella o sus fechas.</li>
      </ul>
      <h3>Capa cruda</h3>
      <p>
        Cada original se guarda con su huella sha256 como nombre, más un manifiesto con enlace, tamaño y huella por
        documento. Primero se bajaron los PDF de las normas sin Word, porque son la única copia de su texto.
      </p>

      <h2 id="transformacion">Transformación</h2>
      <h3>De Word a Markdown</h3>
      <ul>
        <li>Se lee solo el cuerpo del documento, así que encabezados y pies de página no se cuelan. Negritas, cursivas y tablas se conservan.</li>
        <li>La jerarquía se reconoce así: <i>libro › título › capítulo › sección › artículo</i>. Fracciones e incisos se quedan como párrafos, para no inventar estructura.</li>
        <li>Las notas que la SCJN agrega a un párrafo reformado, como «(REFORMADO, D.O.F. 31 DE DICIEMBRE DE 1974)», se separan del texto de la ley.</li>
      </ul>
      <h3>Metadatos</h3>
      <p>Cada archivo empieza con una cabecera según la especificación abierta Legalize Format v0.4:</p>
      <Codigo titulo="Inicio de un archivo (campos principales)">{`---
title: "LEY FEDERAL DEL TRABAJO"
identifier: "LFT"
country: "mx"
rank: "ley_federal"
publication_date: "1970-04-01"
last_updated: "2026-05-14"
status: "in_force"
source: "https://legislacion.scjn.gob.mx/…?IdOrd=…&Vig=1&TPub=6"
jurisdiction: "mx"
---`}</Codigo>
      <p className="dim">Además: dependencia, periódico oficial, categoría y sección originales, número de reformas, abreviatura y, en normas municipales, el municipio con su clave INEGI.</p>
      <h3>Identificadores</h3>
      <ul>
        <li>Ley federal que está en Diputados: su abreviatura, como <code>LFT</code> o <code>CPEUM</code>.</li>
        <li>Cualquier otra del catálogo de la SCJN: entidad, título y clave de la SCJN, como <code>AGU-codigo-penal-para-el-estado-de-aguascalientes-94225</code>. La clave desempata títulos repetidos.</li>
        <li>Otras fuentes: fuente y su clave, como <code>dof:5801377</code>.</li>
        <li>Carpeta por jurisdicción: <code>mx</code> (federal), <code>mx-cmx</code>, <code>mx-agu</code> (estatal) y <code>mx-agu-005</code> (municipal, con la clave INEGI).</li>
      </ul>
      <h3>Tipo y vigencia</h3>
      <p>El tipo se deduce del inicio del título (constitución, código, ley orgánica, reglamento, bando…). La vigencia viene de la SCJN:</p>
      <Tabla cab={["Vigencia en la SCJN", "Estado"]} filas={[
        ["Vigente", "Vigente"], ["Abrogado, derogado, sustituida, no vigente", "Abrogada"], ["Extinguido, cesada", "Vencida"], ["Sin efecto, ineficaz", "Anulada"],
      ]} />
      <h3>Sin duplicados</h3>
      <ul>
        <li>Las reformas publicadas el mismo día se juntan en una versión, y el commit nombra todos los decretos de ese día.</li>
        <li>Un Word idéntico a otro ya visto no genera versión nueva, ni un artículo que no cambió.</li>
        <li>Antes de escribir un commit se verifica que no exista ya uno con la misma publicación y norma.</li>
      </ul>

      <h2 id="historial">Historial en git</h2>
      <p>
        Cada Word de la SCJN es una fotografía del texto completo después de una reforma. El proceso ordena esas
        fotografías por fecha y escribe un commit por cada una: el primero (<code>[bootstrap]</code>) con el texto original
        y uno <code>[reform]</code> por cada reforma. Así, leer la ley en una fecha es leer el commit vigente ese día, y
        comparar dos reformas es un <i>diff</i> de git.
      </p>
      <Tabla cab={["Tipo de commit", "Cantidad"]} num={[1]} filas={[["[reform]: una reforma", 75251], ["[bootstrap]: texto original", 33998], ["[fix-pipeline]: mantenimiento del repo", 2], ["Total", 109251]]} />
      <h3>Formato de cada commit</h3>
      <p>El asunto dice qué norma y qué artículos cambiaron; el cuerpo y los <i>trailers</i> llevan la fecha y la publicación oficial.</p>
      <Codigo titulo="Una reforma real">{`[reform] REGLAMENTO INTERIOR DE LA SECRETARIA GENERAL DE GOBIERNO DEL ESTADO DE ZACATECAS — art. 27

Norm: ZAC-reglamento-interior-de-la-secretaria-general-de-gobierno-22214
Disposition: PO-ZAC-2010-05-05-22214-3
Date: 2010-05-05
Affected articles: ARTICULO 27.
Change: REGLAMENTO 36 SUPLEMENTO

Source-Id: PO-ZAC-2010-05-05-22214-3
Norm-Id: ZAC-reglamento-interior-de-la-secretaria-general-de-gobierno-22214
Source-Date: 2010-05-05`}</Codigo>
      <ul>
        <li><b>Identificador de la publicación:</b> en leyes federales, el número de nota del DOF (<code>DOF-5787418</code>) cuando una sola nota de ese día nombra la ley; si no, la fecha con la clave de la SCJN. En estatales, <code>PO-</code> más entidad, fecha y clave.</li>
        <li><b>Fechas anteriores a 1970:</b> git no acepta fechas previas a 1970, así que esos commits quedan fechados el 2 de enero de 1970 y la fecha real va en <code>Source-Date</code>. Son 2,264 commits; la publicación más antigua del repositorio es de 1814.</li>
        <li><b>Autor:</b> todos los commits los firma la identidad del proceso, no una persona, como pide la especificación.</li>
      </ul>

      <h2 id="pdf">Normas sin Word: PDF y OCR</h2>
      <p>
        Para unas 75,000 normas la SCJN no publica Word, solo el PDF del periódico oficial. Su texto se extrae así:
      </p>
      <ol>
        <li>Se leen las líneas del PDF con su posición en la página.</li>
        <li>Cada página recibe una calificación de calidad. Si queda baja (por ejemplo, porque es un escaneo), se vuelve a leer con OCR en español (Tesseract, imagen a 300 dpi en escala de grises) y se conserva la mejor de las dos lecturas.</li>
        <li>Se quitan encabezados, pies y números de página.</li>
        <li>Como un periódico trae muchas publicaciones, la norma se localiza comparando su título con el del catálogo, y se corta donde empieza la siguiente.</li>
        <li>Se rearman los párrafos y se unen las palabras cortadas con guion.</li>
      </ol>
      <p>Estos textos se marcan como <b>«como se publicó»</b>: no incorporan reformas posteriores, y se indica si salieron del PDF o de OCR.</p>
      <Tabla cab={["Resultado", "Normas"]} num={[1]} filas={[
        ["Texto de la capa del PDF", 31840], ["Texto con OCR", 7886], ["OCR recortado (más de 60 páginas)", 138],
        ["PDF aún no descargado", 30985], ["No se encontró la norma en el PDF", 3662], ["Error o tiempo agotado", 261],
      ]} />
      <p className="aviso">
        Estado al {CORTE}: los 39,864 textos extraídos están listos pero <b>aún no están publicados</b>. Por eso en esta
        web esas normas aparecen como «solo catalogadas». No hay todavía una medición de la exactitud del OCR.
      </p>

      <h2 id="publicacion">Publicación e índice</h2>
      <ul>
        <li><b>Repositorio git</b> (<a href="https://github.com/elimorals/legalize-mx">elimorals/legalize-mx</a>): 33,998 normas con texto, en 568 carpetas municipales más las federales y estatales. Cada archivo vive en <code>{"{jurisdicción}/{2 caracteres}/{identificador}.md"}</code>.</li>
        <li><b>Dataset en Hugging Face</b> (<a href="https://huggingface.co/datasets/elimoralsmendox/legalize-mx">elimoralsmendox/legalize-mx</a>): el catálogo completo (con o sin texto) y las leyes en Parquet, más el índice de búsqueda.</li>
        <li><b>Originales</b> (<a href="https://huggingface.co/datasets/elimoralsmendox/legalize-mx-raw">legalize-mx-raw</a>): por ahora solo los PDF de Baja California Sur (923 archivos, verificados uno por uno); el resto está en pausa por espacio y ancho de banda.</li>
      </ul>
      <h3>El índice de búsqueda</h3>
      <ul>
        <li>Una base SQLite con búsqueda de texto completo (FTS5, sin distinguir acentos) sobre el título y el inicio de cada norma: sus primeros 1,500 caracteres y hasta 2,500 de encabezados.</li>
        <li>Incluye la cobertura de los 2,478 municipios y la versión y fecha de construcción.</li>
        <li>Se publica comprimido (unos 93 MB; 491 MB sin comprimir) junto a un manifiesto con su huella sha256. El MCP lo baja, verifica la huella y lo abre en solo lectura.</li>
        <li>Orden de resultados: primero coincidencias en el título, luego normas con texto, luego títulos más cortos y al final relevancia (BM25).</li>
      </ul>
      <p>
        El texto y el historial no están en el índice: el MCP y esta web los leen directamente del repositorio git, así que
        reflejan la última publicación aunque el índice sea de unos días antes.
      </p>

      <h2 id="calidad">Calidad e integridad</h2>
      <h3>El incidente del texto ajeno</h3>
      <p>
        En algunas reformas, la SCJN respondió al enlace del Word de una norma con el texto de <i>otra</i>. El proceso
        verificaba que el archivo fuera un Word válido, pero no que fuera de esa norma, y lo publicó como una versión.
        La causa no está confirmada; en el 89 % de los casos la norma afectada y la ajena se descargaron con menos de
        15 minutos de diferencia, lo que apunta a respuestas cruzadas entre peticiones simultáneas.
      </p>
      <Tabla cab={["Alcance detectado", "Versiones", "Leyes"]} num={[1, 2]} filas={[
        ["Federal", 156, 129], ["Estatal", 796, 664], ["CDMX", 35, 31], ["Tratados", 1, 1], ["Total", 988, 825], ["…con el texto vigente ajeno", 196, 196],
      ]} />
      <ul>
        <li><b>Reparación (17 de octubre de 2026):</b> se reconstruyeron 824 leyes sin 985 versiones ajenas, se reescribió el historial público y se regeneró el dataset. La Constitución pasó de 245 a 236 versiones. Tres detecciones dudosas se conservaron.</li>
        <li><b>Recuperación:</b> se volvieron a bajar las reformas afectadas y 817 leyes recuperaron versiones.</li>
        <li><b>Guardia permanente:</b> ahora cada versión debe parecerse a las demás de su norma. Dos versiones seguidas de una ley comparten 90 % o más de su vocabulario; un texto ajeno, entre 2 % y 27 %. Con menos de 40 % se descarta.</li>
        <li>Los originales de la SCJN se descargan en un solo proceso.</li>
      </ul>
      <h3>Otras verificaciones</h3>
      <ul>
        <li>146 pruebas automáticas del proceso de México, con páginas y documentos reales grabados como referencia.</li>
        <li>El enlace de cada nota del DOF con su ley resuelve el 95.8 % sin ambigüedad en 410 días; lo que no se resuelve se reporta, nunca se adivina.</li>
        <li>Regla general: nunca se inventa una fecha. Si no se conoce, queda vacía.</li>
      </ul>

      <h2 id="actualizacion">Actualización</h2>
      <p>La actualización diaria está definida en dos pasos:</p>
      <ol>
        <li>Detectar reformas del día: notas del DOF que son decretos, ligadas por título a su ley, más la página de reformas recientes de la SCJN.</li>
        <li>Publicar: commit incremental, envío a GitHub y a Hugging Face.</li>
      </ol>
      <p className="aviso">
        Estado al {CORTE}: la tarea diaria existe pero <b>todavía no corre de forma automática</b>; las publicaciones se
        hacen a mano. Las otras 52 fuentes y el índice de búsqueda también se actualizan a mano. Lo más reciente del DOF
        siempre se puede consultar en vivo en <Link href="/dof">DOF del día</Link>.
      </p>

      <h2 id="limites">Límites y pendientes</h2>
      <ul>
        <li><b>Texto:</b> 33,998 normas tienen texto; 39,864 extraídas de PDF esperan publicación y unas 31,000 esperan que se descargue su PDF.</li>
        <li><b>Otras fuentes sin texto:</b> congresos, periódicos oficiales, municipios y DOF están catalogados y enlazados. Falta su capa de texto y unirlas con la SCJN cuando son la misma norma.</li>
        <li><b>Sin cubrir:</b> Veracruz (su gaceta tiene captcha), la Gaceta de la CDMX, el periódico oficial de Michoacán, el congreso de San Luis Potosí, el periódico oficial de Aguascalientes y 103 sitios municipales descartados.</li>
        <li><b>DOF histórico:</b> el recorrido llega a junio de 1992; falta 1917–1992.</li>
        <li><b>Fecha de entrada en vigor:</b> no se registra; las versiones usan la fecha de publicación.</li>
        <li><b>Jurisprudencia y tesis:</b> aún no.</li>
      </ul>
      <h3>Censo municipal</h3>
      <p>De cada uno de los 2,478 municipios se sabe dónde publica sus normas, o por qué no se encontró:</p>
      <Tabla cab={["Situación", "Municipios"]} num={[1]} filas={[
        ["Sitio propio con normas", 695], ["Cubierto por una compilación estatal", 751], ["Solo normas fiscales", 538],
        ["Sitio sin normas", 259], ["Sin sitio", 148], ["Sin verificar", 71], ["Sitio bloqueado", 16],
      ]} />
      <p className="dim">Los 1,446 municipios con normas no fiscales suman el 81.3 % de la población (Censo 2020). «No encontrado» no quiere decir que no existan.</p>

      <h2 id="reproducir">Revisarlo tú</h2>
      <ul>
        <li>Cada versión de cada ley está en <a href="https://github.com/elimorals/legalize-mx">github.com/elimorals/legalize-mx</a>: <code>git log</code> de un archivo es su historial de reformas.</li>
        <li>El catálogo y los textos en Parquet, en <a href="https://huggingface.co/datasets/elimoralsmendox/legalize-mx">Hugging Face</a>.</li>
        <li>El servidor MCP, el índice y esta web, en <a href="https://github.com/elimorals/legalize-mx-mcp">elimorals/legalize-mx-mcp</a>.</li>
        <li>El proceso sigue la especificación abierta de <a href="https://github.com/legalize-dev/legalize">Legalize</a>, que publica la legislación de varios países como git.</li>
      </ul>
      <p className="aviso">Todo el texto se extrae automáticamente y puede tener errores de origen o de conversión. No es asesoría legal: verifica siempre con la fuente oficial.</p>
    </section>
  );
}
