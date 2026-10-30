import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Acerca",
  description: "De dónde salen los textos de legalize-mx, cómo se versionan, qué límites tienen y cómo descargar los datos.",
};

export default function Acerca() {
  return (
    <section className="seccion texto">
      <h1>Acerca</h1>
      <p>
        legalize-mx convierte la legislación mexicana en datos abiertos y verificables: cada ley con texto es un archivo
        Markdown en git y cada reforma es un commit con la fecha en que se publicó. Así se puede leer cualquier versión,
        comparar dos fechas artículo por artículo y saber de dónde salió cada palabra.
      </p>

      <h2 id="fuentes">Fuentes</h2>
      <ul>
        <li>Catálogo de la SCJN: federal, las 32 entidades y tratados, con el Word de cada reforma.</li>
        <li>Los congresos estatales y la Consejería Jurídica de la CDMX.</li>
        <li>Cámara de Diputados (leyes federales) y el Diario Oficial de la Federación (NOM, lineamientos, acuerdos).</li>
        <li>Periódicos oficiales estatales y cientos de portales municipales.</li>
      </ul>
      <p>
        La lista completa, con conteos, está en{" "}
        <a href="https://github.com/elimorals/legalize-mx-mcp/blob/main/docs/FUENTES.md">docs/FUENTES.md</a>.
      </p>

      <h2 id="limites">Límites</h2>
      <ul>
        <li>No todas las normas tienen texto: muchas están solo catalogadas, con enlace al documento oficial.</li>
        <li>Hoy solo las normas del catálogo de la SCJN con Word tienen texto. Las de otras fuentes, y las que solo tienen PDF, están catalogadas con su documento oficial: la ficha puede extraer el texto al momento.</li>
        <li>El texto se extrae automáticamente y puede tener errores de origen o de conversión.</li>
        <li>Aún no hay jurisprudencia ni tesis.</li>
      </ul>
      <p className="aviso">No es asesoría legal. Verifica siempre con la fuente oficial antes de usarlo en un asunto real.</p>

      <p>El proceso completo, paso por paso, está en <Link href="/como-se-hizo">Cómo se hizo</Link>.</p>

      <h2 id="datos">Datos abiertos</h2>
      <ul>
        <li><a href="https://github.com/elimorals/legalize-mx">elimorals/legalize-mx</a>: un Markdown por ley, un commit por reforma.</li>
        <li><a href="https://huggingface.co/datasets/elimoralsmendox/legalize-mx">Dataset en Hugging Face</a>, con el índice de búsqueda en <code>index/</code>.</li>
        <li><a href="https://github.com/elimorals/legalize-mx-mcp">elimorals/legalize-mx-mcp</a>: el MCP, la CLI, esta web y la skill.</li>
      </ul>

      <h2 id="licencia">Licencia</h2>
      <p>
        Código bajo MIT. Los textos legales son de dominio público: el artículo 14, fracción VIII, de la Ley Federal del
        Derecho de Autor excluye de protección los textos legislativos y administrativos.
      </p>
    </section>
  );
}
