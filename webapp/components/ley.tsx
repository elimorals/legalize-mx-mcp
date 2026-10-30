import Link from "next/link";

// The law's Markdown has three kinds of blocks: headings ("## TITULO", "### Artículo 27."),
// notes the SCJN appends to a reformed paragraph ("> <small>(REFORMADO, D.O.F. …)</small>"),
// and paragraphs. Articles get stable anchors so a reader can link straight to one.

export type Bloque = { tipo: "h2" | "h3" | "nota" | "p"; texto: string; id?: string };

export function slugArticulo(h: string) {
  const s = h.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
    .replace(/^(articulo|art\.)\s*/, "").replace(/[°º]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  return `art-${s || "x"}`;
}

const esArticulo = (h: string) => /^(art[ií]culo|art\.)\s/i.test(h.normalize("NFC"));

export function bloques(md: string): Bloque[] {
  const vistos = new Map<string, number>();
  return md.split(/\n{2,}/).map((b): Bloque => {
    const t = b.trim();
    const h = /^(#{1,6})\s+(.*)$/.exec(t);
    if (h) {
      const texto = h[2];
      let id: string | undefined;
      if (esArticulo(texto)) {
        const base = slugArticulo(texto);
        const n = (vistos.get(base) ?? 0) + 1; // transitories restart numbering
        vistos.set(base, n);
        id = n === 1 ? base : `${base}-${n}`;
      }
      return { tipo: h[1].length <= 2 ? "h2" : "h3", texto, id };
    }
    const nota = /^>\s*(?:<small>)?([\s\S]*?)(?:<\/small>)?$/.exec(t);
    if (nota && t.startsWith(">")) return { tipo: "nota", texto: nota[1].trim() };
    return { tipo: "p", texto: t };
  });
}

export function Cuerpo({ bs }: { bs: Bloque[] }) {
  return (
    <div className="ley">
      {bs.map((b, i) => {
        if (b.tipo === "h2") return <h2 key={i}>{b.texto}</h2>;
        if (b.tipo === "h3") return <h3 key={i} id={b.id}>{b.id ? <a href={`#${b.id}`} className="ancla">{b.texto}</a> : b.texto}</h3>;
        if (b.tipo === "nota") return <p key={i} className="nota-reforma">{b.texto}</p>;
        return <p key={i}>{b.texto}</p>;
      })}
    </div>
  );
}

/** Jump list of the articles in the part being shown. */
export function IndiceArticulos({ bs }: { bs: Bloque[] }) {
  const arts = bs.filter((b) => b.id);
  if (arts.length < 4) return null;
  return (
    <details className="indice-arts">
      <summary>Artículos en esta parte ({arts.length})</summary>
      <ol>{arts.map((a) => <li key={a.id}><a href={`#${a.id}`}>{a.texto.replace(/^Art[ií]culo\s*/i, "").replace(/\.$/, "")}</a></li>)}</ol>
    </details>
  );
}

/** "Artículo 97., Artículo 110., CAPITULO I, [N. DE E. …]" → the article numbers and the editor notes apart. */
export function articulosDe(s: string | undefined | null) {
  const arts = [...(s ?? "").matchAll(/Art[ií]culo\s+([^,[\]]+?)\.?(?=,|$)/g)].map((m) => m[1].trim());
  const notas = [...(s ?? "").matchAll(/\[([^\]]+)\]/g)].map((m) => m[1].trim());
  return { arts, notas };
}

export function Diff({ texto }: { texto: string }) {
  const lineas = texto.split("\n").filter((l) => !/^(---|\+\+\+|@@)/.test(l));
  return (
    <div className="diff">
      {lineas.map((l, i) => {
        const tipo = l.startsWith("+") ? "mas" : l.startsWith("-") ? "menos" : "";
        const t = l.slice(tipo ? 1 : 0).replace(/^>\s*<small>(.*)<\/small>$/, "$1");
        return t.trim() ? <p key={i} className={tipo}><span aria-hidden>{tipo === "mas" ? "+" : tipo === "menos" ? "−" : " "}</span>{t}</p> : null;
      })}
    </div>
  );
}

export function VerVersion({ id, fecha, children }: { id: string; fecha?: string; children: React.ReactNode }) {
  return <Link href={fecha ? `/norma/${encodeURIComponent(id)}?fecha=${fecha}` : `/norma/${encodeURIComponent(id)}`}>{children}</Link>;
}
