import Link from "next/link";
import { Suspense } from "react";
import { Codigo } from "@/components/ui";
import { api, fmt, SITIO } from "@/lib/api";

type Info = { indice?: Record<string, string> };

async function Cifras() {
  const { indice } = await api<Info>("info");
  if (!indice) return null;
  return (
    <p className="cifras-linea">
      <span><b>{fmt.format(Number(indice.norms))}</b> normas</span>
      <span><b>{fmt.format(Number(indice.with_text))}</b> con texto y reformas</span>
      <span><b>{indice.sources}</b> fuentes oficiales</span>
      <span><b>{fmt.format(Number(indice.municipalities))}</b> municipios censados</span>
      <span className="faint">índice del {indice.built?.slice(0, 10)}</span>
    </p>
  );
}

// Each example opens a real page that shows the capability, not a description of it.
const PRUEBAS: [string, string, string][] = [
  ["Leer una ley como estaba en una fecha", "/norma/CPEUM?articulo=27&fecha=1920-01-01", "El artículo 27 constitucional en 1920, antes de sus reformas."],
  ["Ver qué cambió en una reforma", "/norma/LFT?fecha=2026-05-14&cambios=1", "La última reforma a la Ley Federal del Trabajo, artículo por artículo."],
  ["Buscar normas de tu municipio", "/buscar?texto=anuncios&municipio=Zapopan", "Reglamentos de anuncios en Zapopan, con su fuente oficial."],
  ["Revisar lo publicado hoy", "/dof", "El DOF del día, consultado en vivo desde la API oficial."],
];

export default function Inicio() {
  return (
    <>
      <section className="heroe">
        <h1>La ley mexicana, con cada una de sus reformas</h1>
        <p className="lead">
          Leyes, reglamentos, bandos y NOM federales, de las 32 entidades y de cientos de municipios. Lee el texto vigente
          o el que regía en cualquier fecha, compara dos versiones y llega siempre a la fuente oficial.
        </p>
        <form className="buscador" action="/buscar" role="search">
          <input type="search" name="texto" placeholder="Ley, tema o palabra: jornada laboral, predial, anuncios…" aria-label="Buscar norma" />
          <button className="boton" type="submit">Buscar</button>
        </form>
        <Suspense fallback={<p className="cifras-linea faint">Cargando cifras…</p>}>
          <Cifras />
        </Suspense>
      </section>

      <section className="seccion">
        <h2>Qué puedes hacer</h2>
        <ul className="pruebas">
          {PRUEBAS.map(([t, h, d]) => (
            <li key={h}><Link href={h}>{t}</Link><span>{d}</span></li>
          ))}
        </ul>
      </section>

      <section className="seccion dos-col">
        <div className="texto">
          <h2>Conecta tu agente</h2>
          <p>
            Lo mismo, como servidor MCP: Claude, Cursor u otro agente consulta la ley y cita la fuente. Sin clave y sin
            instalar nada.
          </p>
          <Codigo titulo="Claude Code">{`claude mcp add --transport http legalize-mx ${SITIO}/mcp`}</Codigo>
          <p><Link href="/guia/mcp">Otros clientes, herramientas y recetas →</Link></p>
        </div>
        <div className="texto">
          <h2>De dónde sale</h2>
          <p>
            El texto y su historia salen del buscador legislativo de la SCJN; además se catalogan el DOF, la Cámara de
            Diputados, los congresos estatales, periódicos oficiales y cientos de portales municipales. Cada ley con texto vive en git, con un commit por
            reforma y la fecha en que se publicó: así se reconstruye cualquier versión.
          </p>
          <p><Link href="/como-se-hizo">Cómo se extrae y se procesa →</Link></p>
        </div>
      </section>
    </>
  );
}
