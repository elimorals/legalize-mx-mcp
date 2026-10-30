import Link from "next/link";
import { Copiar } from "@/components/cliente";
import { ESTATUS, fmt, lugar, rango, type Norma } from "@/lib/api";

export function Cifra({ n, l }: { n: string | number; l: string }) {
  return (
    <div className="cifra">
      <div className="n">{typeof n === "number" ? fmt.format(n) : n}</div>
      <div className="l">{l}</div>
    </div>
  );
}

export function Texto({ has_text, texto_estado, fuente_texto }: Pick<Norma, "has_text" | "texto_estado" | "fuente_texto">) {
  if (!has_text) return <span className="chip">Solo catalogada</span>;
  if (texto_estado === "as_enacted") return <span className="chip oro">Como se publicó{fuente_texto === "ocr" ? " (OCR)" : ""}</span>;
  return <span className="chip ok">Texto y reformas</span>;
}

export function NormaItem({ n }: { n: Norma }) {
  return (
    <li className="item">
      <h3 className="titulo-norma"><Link href={`/norma/${encodeURIComponent(n.id)}`}>{n.title}</Link></h3>
      <div className="meta">
        <span>{lugar(n)}</span>
        {n.rank && <span>{rango(n.rank)}</span>}
        {n.status && ESTATUS[n.status] && <span className="chip no">{ESTATUS[n.status]}</span>}
        <Texto {...n} />
        {n.last_updated && <span className="faint">reforma {n.last_updated}</span>}
      </div>
      {n.fragmento && <p dangerouslySetInnerHTML={{ __html: resaltar(n.fragmento) }} />}
    </li>
  );
}

// The index marks hits with «»; escape everything else before turning them into <mark>.
function resaltar(s: string) {
  const esc = s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return esc.replace(/«/g, "<mark>").replace(/»/g, "</mark>");
}

export function Select({ name, label, valor, opciones, todos = "Todos" }: { name: string; label: string; valor?: string; opciones: [string, string][]; todos?: string }) {
  return (
    <label>{label}
      <select name={name} defaultValue={valor ?? ""}>
        <option value="">{todos}</option>
        {opciones.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
      </select>
    </label>
  );
}

export function Codigo({ children, titulo }: { children: string; titulo?: string }) {
  return (
    <figure className="codigo">
      <figcaption>{titulo && <span className="faint">{titulo}</span>}<Copiar texto={children} /></figcaption>
      <pre><code>{children}</code></pre>
    </figure>
  );
}

export function Fallo({ msg }: { msg: string }) {
  return <p className="aviso">No se pudo obtener esto ahora: {msg}</p>;
}
