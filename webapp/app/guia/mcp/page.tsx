import type { Metadata } from "next";
import { Suspense } from "react";
import { ConCodigo, Indice, MenuGuia, Parametros } from "@/components/guia";
import { Codigo } from "@/components/ui";
import { herramientas, SITIO } from "@/lib/api";

export const metadata: Metadata = {
  title: "Guía del MCP",
  description: "Servidor MCP de legalize-mx: conectarlo en Claude Code, Claude Desktop y Cursor, sus herramientas con parámetros y recetas.",
};

const URL_MCP = `${SITIO}/mcp`;
const PIN = "git+https://github.com/elimorals/legalize-mx-mcp@v0.1.0";

const RECETAS: [string, string][] = [
  ["¿Qué dice hoy el artículo 123 de la Ley Federal del Trabajo sobre la jornada? Cita la fuente oficial.", "buscar_norma → articulo → fuentes"],
  ["¿Cómo decía el artículo 27 constitucional en 1920?", "articulo(CPEUM, 27, fecha)"],
  ["¿Qué cambió en la LFT desde enero de 2025?", "diff(LFT, 2025-01-01)"],
  ["¿Qué reglamentos de anuncios tiene Zapopan y qué dicen de los permisos?", "buscar_norma(municipio) → leer_norma"],
  ["¿Qué publicó hoy el DOF que sea normativo?", "dof_del_dia → leer_nota_dof"],
  ["¿Qué tan cubierto está Oaxaca? ¿Qué municipios no tienen fuente?", "cobertura(estado, municipio)"],
];

const NOTAS: Record<string, string> = {
  leer_norma: "Textos largos vienen por partes (siguiente_desde). Con extraer_en_vivo=true baja el documento oficial si la norma solo está catalogada.",
  historial: "Lee el historial de GitHub; cada commit es una reforma con su fecha de publicación (Source-Date), incluso antes de 1970.",
  diff: "Compara artículo por artículo, no el texto entero: los transitorios reinician la numeración y un diff completo se desalinea.",
  dof_del_dia: "Consulta la API oficial del DOF en vivo. solo_normativas quita avisos, convocatorias y edictos.",
};

async function Herramientas() {
  const hs = await herramientas();
  if (!hs.length) return <p className="aviso">No pude leer la lista de herramientas del servidor ahora.</p>;
  return (
    <>
      {hs.map((h) => (
        <div key={h.name} id={h.name} style={{ marginBottom: 24 }}>
          <h3 className="mono">{h.name}</h3>
          <p><ConCodigo texto={h.description ?? ""} /></p>
          {NOTAS[h.name] && <p className="dim">{NOTAS[h.name]}</p>}
          <Parametros h={h} />
        </div>
      ))}
    </>
  );
}

export default function GuiaMcp() {
  return (
    <section className="seccion texto">
      <h1>MCP</h1>
      <MenuGuia actual="/guia/mcp" />
      <p>
        Un servidor MCP público y sin clave en <code>{URL_MCP}</code> (Streamable HTTP, sin sesión). Las herramientas
        son de solo lectura y cada respuesta trae el enlace oficial para citar.
      </p>
      <Indice items={[["conectar", "Conectar"], ["plugin", "Plugin de Claude Code"], ["local", "MCP local"], ["herramientas", "Herramientas"], ["recetas", "Recetas"]]} />

      <h2 id="conectar">Conectar</h2>
      <Codigo titulo="Claude Code">{`claude mcp add --transport http legalize-mx ${URL_MCP}
claude mcp list        # legalize-mx ... ✔ Connected`}</Codigo>
      <Codigo titulo="Cursor, Claude Desktop y otros clientes con HTTP (.mcp.json / mcp.json)">{`{
  "mcpServers": {
    "legalize-mx": { "url": "${URL_MCP}" }
  }
}`}</Codigo>
      <Codigo titulo="Clientes que solo hablan stdio">{`{
  "mcpServers": {
    "legalize-mx": { "command": "npx", "args": ["-y", "mcp-remote", "${URL_MCP}"] }
  }
}`}</Codigo>

      <h2 id="plugin">Plugin de Claude Code</h2>
      <p>Instala el MCP y la skill <code>legalize-mx</code>, que le enseña al agente cuándo consultarlo, en qué orden y cómo citar.</p>
      <Codigo>{`/plugin install legalize-mx --marketplace elimorals/legalize-mx-mcp`}</Codigo>

      <h2 id="local">MCP local</h2>
      <p>
        Corre en tu máquina con <a href="https://docs.astral.sh/uv/">uv</a>. Baja el índice (~90 MB) una vez y lo
        actualiza solo. Úsalo si consultas mucho historial: con tu <code>GITHUB_TOKEN</code> el límite de GitHub sube a
        5,000 consultas por hora, o con <code>LEGALIZE_MX_REPO</code> lee un clon local sin red. También agrega{" "}
        <code>actualizar_indice</code>, que el remoto no necesita.
      </p>
      <Codigo>{`claude mcp add legalize-mx -- uvx --from ${PIN} legalize-mx-mcp`}</Codigo>

      <h2 id="herramientas">Herramientas</h2>
      <p className="dim">Descripciones y parámetros leídos en vivo del servidor.</p>
      <Suspense fallback={<p className="cargando">Leyendo herramientas…</p>}>
        <Herramientas />
      </Suspense>

      <h2 id="recetas">Recetas</h2>
      <p>Preguntas para pegar en tu agente con el MCP conectado, y lo que usa por debajo.</p>
      <div className="tabla-scroll">
        <table>
          <thead><tr><th>Pregunta</th><th>Herramientas</th></tr></thead>
          <tbody>{RECETAS.map(([p, h]) => <tr key={p}><td className="ancho">{p}</td><td className="mono">{h}</td></tr>)}</tbody>
        </table>
      </div>
    </section>
  );
}
