import type { Metadata } from "next";
import { Indice, MenuGuia } from "@/components/guia";
import { Codigo } from "@/components/ui";
import { SITIO } from "@/lib/api";

export const metadata: Metadata = {
  title: "API y CLI",
  description: "API JSON pública y CLI de legalize-mx: los mismos datos y herramientas que el MCP.",
};

const PIN = "git+https://github.com/elimorals/legalize-mx-mcp@v0.1.0";

const ENDPOINTS: [string, string][] = [
  ["buscar_norma?texto=&estado=&municipio=&tipo=&vigente=&con_texto=&fuente=&limite=&desde=", "Búsqueda con filtros"],
  ["leer_norma?id=&fecha=&desde=&max_caracteres=&extraer_en_vivo=", "Texto vigente o a una fecha"],
  ["articulo?id=&numero=&fecha=", "Un artículo"],
  ["historial?id=", "Reformas"],
  ["diff?id=&fecha_a=&fecha_b=", "Cambios entre dos fechas"],
  ["fuentes?id=", "Enlaces oficiales"],
  ["cobertura?estado=&municipio=", "Qué hay y qué falta"],
  ["dof_del_dia?fecha=&solo_normativas=", "DOF del día, en vivo"],
  ["leer_nota_dof?codigo=", "Una nota del DOF"],
  ["info", "Versión del índice"],
];

export default function GuiaApi() {
  return (
    <section className="seccion texto">
      <h1>API y CLI</h1>
      <MenuGuia actual="/guia/api" />
      <Indice items={[["api", "API JSON"], ["cli", "CLI"]]} />

      <h2 id="api">API JSON</h2>
      <p>
        Cada herramienta del MCP también responde por <code>GET {SITIO}/api/&lt;herramienta&gt;</code> con los mismos
        parámetros en la URL y la misma respuesta. Sin clave, con CORS abierto. Un error de la herramienta vuelve con
        estado 400 y el campo <code>error</code>; si falla un portal oficial, 502.
      </p>
      <div className="tabla-scroll" style={{ marginBottom: 16 }}>
        <table>
          <thead><tr><th>Ruta</th><th>Qué hace</th></tr></thead>
          <tbody>{ENDPOINTS.map(([r, q]) => <tr key={r}><td className="mono ancho">/api/{r}</td><td>{q}</td></tr>)}</tbody>
        </table>
      </div>
      <Codigo titulo="Ejemplos">{`curl "${SITIO}/api/buscar_norma?texto=protecci%C3%B3n+civil&municipio=Zapopan"
curl "${SITIO}/api/articulo?id=CPEUM&numero=27&fecha=1920-01-01"
curl "${SITIO}/api/diff?id=LFT&fecha_a=2025-01-01"`}</Codigo>

      <h2 id="cli">CLI</h2>
      <p>Los mismos subcomandos, en tu terminal, con <a href="https://docs.astral.sh/uv/">uv</a>:</p>
      <Codigo>{`alias legalize-mx="uvx --from ${PIN} legalize-mx"
legalize-mx buscar "jornada laboral" --estado federal
legalize-mx articulo CPEUM 27 --fecha 1920-01-01
legalize-mx diff LFT 2025-01-01
legalize-mx leer LFT --texto
legalize-mx cobertura --estado OAX
legalize-mx dof`}</Codigo>
    </section>
  );
}
