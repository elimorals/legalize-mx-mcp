import Link from "next/link";
import type { Herramienta } from "@/lib/api";

const PAGINAS: [string, string][] = [["/guia", "Inicio"], ["/guia/mcp", "MCP"], ["/guia/api", "API y CLI"]];

export function MenuGuia({ actual }: { actual: string }) {
  return (
    <nav className="chips" aria-label="Secciones de la guía" style={{ margin: "0 0 20px" }}>
      {PAGINAS.map(([h, t]) => (
        <Link key={h} href={h} className={`chip${h === actual ? " oro" : ""}`} aria-current={h === actual ? "page" : undefined}>{t}</Link>
      ))}
    </nav>
  );
}

/** Tool descriptions mark parameters with backticks; show them as code, not as literal ticks. */
export function ConCodigo({ texto }: { texto: string }) {
  return <>{texto.split(/`([^`]+)`/).map((t, i) => (i % 2 ? <code key={i}>{t}</code> : t))}</>;
}

export function Indice({ items }: { items: [string, string][] }) {
  return (
    <div className="panel" style={{ margin: "0 0 24px" }}>
      <b>En esta página</b>
      <ol style={{ margin: "8px 0 0", paddingLeft: 20 }}>{items.map(([id, t]) => <li key={id}><a href={`#${id}`}>{t}</a></li>)}</ol>
    </div>
  );
}

const tipo = (p: Herramienta["inputSchema"]["properties"] extends Record<string, infer P> | undefined ? P : never) =>
  p.type ?? p.anyOf?.map((a) => a.type).filter((t) => t && t !== "null").join(" | ") ?? "—";

/** Parameter table built from the inputSchema the MCP publishes (not written by hand). */
export function Parametros({ h }: { h: Herramienta }) {
  const props = Object.entries(h.inputSchema.properties ?? {});
  if (!props.length) return <p className="dim">Sin parámetros.</p>;
  const req = new Set(h.inputSchema.required ?? []);
  return (
    <div className="tabla-scroll" style={{ marginBottom: 12 }}>
      <table>
        <thead><tr><th>Parámetro</th><th>Tipo</th><th>Por defecto</th></tr></thead>
        <tbody>
          {props.map(([k, p]) => (
            <tr key={k}>
              <td className="mono">{k}{req.has(k) ? " *" : ""}</td>
              <td>{tipo(p)}</td>
              <td className="mono">{p.default === undefined || p.default === null ? "—" : JSON.stringify(p.default)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
