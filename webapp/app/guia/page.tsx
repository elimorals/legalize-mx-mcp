import type { Metadata } from "next";
import Link from "next/link";
import { Indice, MenuGuia } from "@/components/guia";
import { Codigo } from "@/components/ui";
import { SITIO } from "@/lib/api";

export const metadata: Metadata = {
  title: "Guía: web, MCP, CLI y API",
  description: "Cómo consultar la legislación mexicana de legalize-mx: MCP remoto y local, plugin de Claude Code, CLI, API y datos abiertos.",
};

const PIN = "git+https://github.com/elimorals/legalize-mx-mcp@v0.1.0";

const CAMINOS: [string, string, string, string][] = [
  ["Esta web", "Cualquier persona", "Nada", "/buscar"],
  ["MCP remoto", "Quien usa Claude, Cursor u otro agente", "Un cliente MCP", "/guia/mcp"],
  ["Plugin de Claude Code", "Quien quiere que el agente sepa cuándo y cómo consultar la ley", "Claude Code", "/guia/mcp#plugin"],
  ["MCP local", "Uso intenso del historial, trabajo sin internet o un clon propio del repo", "uv", "/guia/mcp#local"],
  ["CLI legalize-mx", "Terminal y scripts", "uv", "/guia/api#cli"],
  ["API JSON", "Apps y sitios que integran la búsqueda", "Una petición HTTP", "/guia/api"],
  ["Datos abiertos", "Análisis masivo", "git o Hugging Face", "/acerca#datos"],
];

const PROBLEMAS: [string, string][] = [
  ["El cliente no conecta al MCP remoto",
    `La URL debe terminar en /mcp y usar https (${SITIO}/mcp). El servidor solo habla Streamable HTTP: si tu cliente solo soporta stdio, usa el puente mcp-remote (npx -y mcp-remote ${SITIO}/mcp) o el MCP local.`],
  ["Una llamada GET a /mcp responde 405",
    "Es normal: el servidor no guarda sesión y no abre flujos GET. Los clientes MCP hablan por POST."],
  ["historial o diff fallan por límite de GitHub",
    "El historial se lee de la API de GitHub. Si el remoto llega a su límite, usa el MCP local con tu propio GITHUB_TOKEN o con LEGALIZE_MX_REPO apuntando a un clon del repo de leyes."],
  ["El texto dice “como se publicó” u OCR",
    "Esa norma no tiene versión consolidada: es el texto del periódico oficial sin reformas posteriores, a veces leído con OCR. La respuesta lo avisa en aviso_texto; verifica con el PDF oficial."],
  ["Busco por estado y no sale nada",
    "Usa la clave de 3 letras (JAL, OAX, CMX) o el nombre de la entidad. La búsqueda pide todas las palabras: prueba con menos."],
  ["leer_norma no trae texto",
    "Solo está catalogada. Con extraer_en_vivo=true el servidor baja el documento oficial y extrae el texto; un PDF escaneado sale vacío porque necesita OCR."],
];

export default function Guia() {
  return (
    <section className="seccion texto">
      <h1>Guía</h1>
      <MenuGuia actual="/guia" />
      <p>
        La misma legislación —el catálogo de la SCJN, congresos, DOF, periódicos oficiales y portales municipales, con el
        historial de reformas en git— se consulta de varias formas. Todas leen las mismas fuentes; ninguna escribe nada.
      </p>
      <Indice items={[["cual", "¿Cuál uso?"], ["rapido", "Empezar en un minuto"], ["problemas", "Solución de problemas"]]} />

      <h2 id="cual">¿Cuál uso?</h2>
      <div className="tabla-scroll" style={{ marginBottom: 24 }}>
        <table>
          <thead><tr><th>Forma</th><th>Para quién</th><th>Qué necesitas</th></tr></thead>
          <tbody>{CAMINOS.map(([f, q, n, h]) => <tr key={f}><td><Link href={h}>{f}</Link></td><td className="ancho">{q}</td><td className="ancho">{n}</td></tr>)}</tbody>
        </table>
      </div>

      <h2 id="rapido">Empezar en un minuto</h2>
      <Codigo titulo="MCP remoto en Claude Code">{`claude mcp add --transport http legalize-mx ${SITIO}/mcp
claude mcp list        # legalize-mx ... ✔ Connected`}</Codigo>
      <Codigo titulo="Plugin de Claude Code (MCP + skill)">{`/plugin install legalize-mx --marketplace elimorals/legalize-mx-mcp`}</Codigo>
      <Codigo titulo="CLI">{`uvx --from ${PIN} legalize-mx articulo CPEUM 27 --fecha 1920-01-01`}</Codigo>
      <Codigo titulo="API">{`curl "${SITIO}/api/buscar_norma?texto=jornada+laboral&estado=federal&limite=5"`}</Codigo>

      <h2 id="problemas">Solución de problemas</h2>
      {PROBLEMAS.map(([p, s]) => (
        <details key={p} className="panel" style={{ marginBottom: 8 }}>
          <summary style={{ cursor: "pointer", fontWeight: 600 }}>{p}</summary>
          <p style={{ margin: "8px 0 0" }}>{s}</p>
        </details>
      ))}
    </section>
  );
}
