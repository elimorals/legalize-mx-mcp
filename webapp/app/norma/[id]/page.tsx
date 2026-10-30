import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { articulosDe, bloques, Cuerpo, Diff, IndiceArticulos } from "@/components/ley";
import { Fallo, Texto } from "@/components/ui";
import { api, ESTATUS, fmt, lugar, origen, rango, titulo, uno, urlCon, type Norma } from "@/lib/api";

const PARTE = 40_000;

type Lectura = Norma & {
  texto?: string; caracteres_totales?: number; desde?: number; siguiente_desde?: number; vigente_al?: string;
  aviso_texto?: string; fuente_oficial?: string; texto_disponible?: boolean; motivo?: string; nota?: string;
  version?: { fecha?: string; disposicion?: string }; documentos_oficiales?: Doc[];
  extraido_en_vivo?: { formato?: string; nota?: string; fuente?: string };
};
type Doc = { tipo?: string; descripcion?: string; fecha?: string; url?: string };
type Version = { fecha?: string; tipo?: string; disposicion?: string; cambio?: string; articulos_afectados?: string };
type Historial = { versiones?: Version[]; n_versiones?: number; repo?: string; publicaciones_scjn?: { fecha?: string; categoria?: string; pdf?: string; docx?: string }[] };
type Fuentes = { documentos_oficiales?: Doc[]; markdown_versionado?: string; historial_git?: string; ficha_scjn?: string };
type Cambios = { version_a?: string; version_b?: string; articulos_reformados?: string[]; articulos_adicionados?: string[]; articulos_derogados_o_eliminados?: string[]; cambios?: { articulo: string; tipo: string; diff?: string; texto?: string }[]; nota?: string };
type Articulo = { articulo?: string; texto?: string; parecidos?: string[]; otras_coincidencias?: unknown[] };

type Q = { fecha?: string; desde: number; articulo?: string; cambios?: string; en_vivo?: string };

const idDe = (raw: string) => { try { return decodeURIComponent(raw); } catch { return raw; } };
const ruta = (id: string) => `/norma/${encodeURIComponent(id)}`;
const esFecha = (s?: string) => (s && /^\d{4}-\d{2}-\d{2}$/.test(s) ? s : undefined);

export async function generateMetadata({ params }: PageProps<"/norma/[id]">): Promise<Metadata> {
  const n = await api<Lectura>("leer_norma", { id: idDe((await params).id), max_caracteres: 200 });
  if (n.error && !n.title) return { title: "Norma no encontrada" };
  return { title: titulo(n.title), description: `${rango(n.rank) || "Norma"} · ${lugar(n)}${n.last_updated ? ` · última reforma ${n.last_updated}` : ""}. Texto, historial de reformas y fuente oficial.` };
}

// Word and PDF of the same publication are one entry with two links.
function agrupar(docs: Doc[]) {
  const m = new Map<string, { descripcion: string; fecha?: string; enlaces: [string, string][] }>();
  for (const d of docs) {
    if (!d.url) continue;
    const k = `${d.descripcion ?? d.tipo}|${d.fecha ?? ""}`;
    const g = m.get(k) ?? { descripcion: d.descripcion || d.tipo || "documento", fecha: d.fecha, enlaces: [] };
    const etiqueta = d.tipo === "pdf" ? "PDF" : d.tipo === "docx" ? "Word" : d.tipo === "ficha" ? "Página" : (d.tipo ?? "Abrir");
    if (!g.enlaces.some(([e]) => e === etiqueta)) g.enlaces.push([etiqueta, d.url]);
    m.set(k, g);
  }
  return [...m.values()].sort((a, b) => (a.fecha ? 1 : 0) - (b.fecha ? 1 : 0) || (b.fecha ?? "").localeCompare(a.fecha ?? ""));
}

function Selector({ id, q, ultima }: { id: string; q: Q; ultima?: string | null }) {
  return (
    <form className="panel selector" action={ruta(id)}>
      <label>Ver el texto como estaba el
        <input type="date" name="fecha" defaultValue={q.fecha} max={new Date().toISOString().slice(0, 10)} />
      </label>
      <label>Ir al artículo
        <input type="text" name="articulo" defaultValue={q.articulo} placeholder="Ej. 27, 3 bis, primero" inputMode="text" />
      </label>
      <button className="boton" type="submit">Ver</button>
      {(q.fecha || q.articulo) && <Link className="boton sec" href={ruta(id)}>Texto vigente{ultima ? ` (${ultima})` : ""}</Link>}
    </form>
  );
}

async function UnArticulo({ id, q }: { id: string; q: Q }) {
  const a = await api<Articulo>("articulo", { id, numero: q.articulo, fecha: q.fecha });
  if (a.error) {
    return (
      <div className="aviso">
        No encontré el artículo «{q.articulo}» en esta versión.
        {a.parecidos?.length ? <> ¿Buscabas {a.parecidos.map((p, i) => <span key={p}>{i ? ", " : " "}<Link href={urlCon(ruta(id), { articulo: p, fecha: q.fecha })}>{p}</Link></span>)}?</> : null}
      </div>
    );
  }
  return (
    <section className="destacado" aria-labelledby="art-sel">
      <h2 id="art-sel">{a.articulo}{q.fecha ? <span className="dim"> · vigente el {q.fecha}</span> : null}</h2>
      <Cuerpo bs={bloques(a.texto ?? "")} />
      {a.otras_coincidencias?.length ? <p className="faint">Hay otro artículo con ese número (por ejemplo en los transitorios).</p> : null}
    </section>
  );
}

async function QueCambio({ id, fecha, previa }: { id: string; fecha: string; previa?: string }) {
  if (!previa) return <p className="aviso">Es la versión original: no hay una anterior con qué compararla.</p>;
  const d = await api<Cambios>("diff", { id, fecha_a: previa, fecha_b: fecha, max_caracteres: 60_000 });
  if (d.error) return <Fallo msg={d.error} />;
  const resumen: [string, string[] | undefined][] = [["Reformados", d.articulos_reformados], ["Adicionados", d.articulos_adicionados], ["Derogados o eliminados", d.articulos_derogados_o_eliminados]];
  return (
    <section className="destacado" aria-labelledby="cambios">
      <h2 id="cambios">Qué cambió el {d.version_b}</h2>
      <p className="dim">Comparado con la versión del {d.version_a}, artículo por artículo.</p>
      <dl className="resumen-cambios">
        {resumen.map(([t, xs]) => xs?.length ? <div key={t}><dt>{t}</dt><dd>{xs.join(", ")}</dd></div> : null)}
      </dl>
      {d.cambios?.map((c) => (
        <div key={`${c.tipo}-${c.articulo}`} className="cambio">
          <h3>Artículo {c.articulo} <span className="chip">{c.tipo}</span></h3>
          {c.diff ? <Diff texto={c.diff} /> : <Cuerpo bs={bloques(c.texto ?? "")} />}
        </div>
      ))}
      {d.nota && <p className="faint">{d.nota}</p>}
    </section>
  );
}

async function Historia({ id, q, fechaVista }: { id: string; q: Q; fechaVista?: string }) {
  const h = await api<Historial>("historial", { id });
  if (h.error) return <Fallo msg={h.error} />;
  const vs = h.versiones ?? [];
  const recientes = [...vs].reverse();
  const fila = (v: Version) => {
    const { arts, notas } = articulosDe(v.articulos_afectados);
    const i = vs.indexOf(v);
    const actual = v.fecha === fechaVista;
    return (
      <li key={`${v.fecha}-${v.disposicion}`} className={`version${actual ? " actual" : ""}`}>
        <div className="v-cab">
          <Link className="mono" href={urlCon(ruta(id), { fecha: v.fecha })} aria-current={actual ? "true" : undefined}>{v.fecha}</Link>
          <span>{v.tipo === "bootstrap" ? "Texto original" : v.cambio || "Reforma"}</span>
          {v.tipo !== "bootstrap" && i > 0 && <Link className="v-acc" href={urlCon(ruta(id), { fecha: v.fecha, cambios: 1 })}>Qué cambió</Link>}
        </div>
        {arts.length > 0 && (
          <p className="v-arts">
            {arts.length === 1 ? "Artículo " : "Artículos "}{arts.slice(0, 10).join(", ")}{arts.length > 10 ? ` y ${arts.length - 10} más` : ""}
          </p>
        )}
        {notas.length > 0 && <details className="v-notas"><summary>Notas del editor ({notas.length})</summary>{notas.map((n, k) => <p key={k}>{n}</p>)}</details>}
      </li>
    );
  };
  if (!vs.length) {
    if (!h.publicaciones_scjn?.length) return <p className="dim">La fuente no registra reformas de esta norma.</p>;
    return (
      <ul className="versiones">{h.publicaciones_scjn.slice(0, 30).map((p, i) => (
        <li key={i} className="version"><div className="v-cab"><span className="mono">{p.fecha}</span><span>{p.categoria}</span>
          {p.docx && <a href={p.docx}>Word</a>} {p.pdf && <a href={p.pdf}>PDF</a>}</div></li>
      ))}</ul>
    );
  }
  return (
    <>
      <p className="dim">{fmt.format(h.n_versiones ?? vs.length)} versiones, de la más reciente a la original. Elige una fecha para leer esa versión.</p>
      <ol className="versiones">{recientes.slice(0, 8).map(fila)}</ol>
      {recientes.length > 8 && (
        <details className="mas-versiones">
          <summary>Ver las otras {fmt.format(recientes.length - 8)} versiones</summary>
          <ol className="versiones">{recientes.slice(8).map(fila)}</ol>
        </details>
      )}
      {h.repo && <p className="faint">Cada versión es un commit: <a href={h.repo}>historial en git</a>.</p>}
    </>
  );
}

async function Ficha({ params, searchParams }: PageProps<"/norma/[id]">) {
  const id = idDe((await params).id);
  const sp = await searchParams;
  const q: Q = { fecha: esFecha(uno(sp.fecha)), desde: Math.max(0, Number(uno(sp.desde)) || 0), articulo: uno(sp.articulo)?.trim() || undefined, cambios: uno(sp.cambios), en_vivo: uno(sp.en_vivo) };
  const [n, f] = await Promise.all([
    api<Lectura>("leer_norma", { id, fecha: q.fecha, desde: q.desde, max_caracteres: PARTE, extraer_en_vivo: q.en_vivo ? true : undefined }, q.en_vivo ? 0 : 3600),
    api<Fuentes>("fuentes", { id }),
  ]);
  if (n.error && !n.title) notFound();
  const conTexto = n.texto_disponible !== false;
  const docs = agrupar(f.documentos_oficiales ?? n.documentos_oficiales ?? []);
  const oficial = n.fuente_oficial ?? f.ficha_scjn ?? docs[0]?.enlaces[0]?.[1];
  const fechaVista = n.version?.fecha;

  // previous version, for "qué cambió": only fetched when asked for
  let previa: string | undefined;
  if (q.cambios && fechaVista) {
    const h = await api<Historial>("historial", { id });
    const vs = h.versiones ?? [];
    const i = vs.findIndex((v) => v.fecha === fechaVista);
    previa = i > 0 ? vs[i - 1].fecha : undefined;
  }

  // cut at the last paragraph so a part never ends mid-word
  let texto = n.texto ?? "";
  let siguiente = n.siguiente_desde;
  if (siguiente && texto.length > 2000) {
    const corte = texto.lastIndexOf("\n\n");
    if (corte > texto.length / 2) { siguiente = q.desde + corte; texto = texto.slice(0, corte); }
  }
  const bs = bloques(texto);
  const total = n.caracteres_totales ?? texto.length;
  const partes = Math.max(1, Math.ceil(total / PARTE));
  const parte = Math.floor(q.desde / PARTE) + 1;

  return (
    <article className="ficha">
      <p className="migas"><Link href="/buscar">Buscar</Link>{n.state && n.state !== "federal" ? <> · <Link href={`/buscar?estado=${n.state}`}>{lugar({ state: n.state, municipality: null })}</Link></> : <> · <Link href="/buscar?estado=federal">Federal</Link></>}</p>
      <h1>{titulo(n.title)}</h1>
      {titulo(n.title) !== n.title && <p className="titulo-oficial">Título oficial: {n.title}</p>}
      <p className="linea-meta">
        <span>{rango(n.rank) || "Norma"}</span><span>{lugar(n)}</span>
        {n.publication_date && <span>Publicada {n.publication_date}</span>}
        {n.last_updated && <span>Última reforma {n.last_updated}</span>}
        <span>Fuente: {origen(n.origin)}</span>
      </p>
      <div className="chips" style={{ marginBottom: 16 }}>
        <Texto has_text={conTexto} texto_estado={n.texto_estado} fuente_texto={n.fuente_texto} />
        {n.status && ESTATUS[n.status] && <span className="chip no">{ESTATUS[n.status]}</span>}
        {oficial && <a className="chip" href={oficial} rel="noopener">Fuente oficial ↗</a>}
      </div>

      {conTexto && <Selector id={n.id} q={q} ultima={n.last_updated} />}
      {n.aviso_texto && <p className="aviso">{n.aviso_texto}</p>}
      {q.fecha && fechaVista && !q.cambios && (
        <p className="aviso">Estás leyendo la versión que regía el {q.fecha}: la reforma del {fechaVista}{n.version?.disposicion ? ` (${n.version.disposicion})` : ""}.{" "}
          <Link href={urlCon(ruta(n.id), { fecha: fechaVista, cambios: 1 })}>Ver qué cambió en esa reforma</Link></p>
      )}
      {n.error && n.title && <p className="aviso">{n.error === `la norma no existía el ${q.fecha}` ? `Esta norma aún no existía el ${q.fecha}. Se publicó el ${n.publication_date ?? "—"}.` : n.error}</p>}

      {q.cambios && fechaVista && (
        <Suspense fallback={<p className="cargando">Comparando versiones…</p>}><QueCambio id={n.id} fecha={fechaVista} previa={previa} /></Suspense>
      )}
      {q.articulo && <Suspense fallback={<p className="cargando">Buscando el artículo…</p>}><UnArticulo id={n.id} q={q} /></Suspense>}

      <section aria-labelledby="texto">
        <h2 id="texto">{q.fecha && fechaVista ? `Texto vigente el ${q.fecha}` : "Texto vigente"}</h2>
        {texto ? (
          <>
            {partes > 1 && <p className="dim">Parte {parte} de {partes}. Para un artículo concreto usa “Ir al artículo”.</p>}
            <IndiceArticulos bs={bs} />
            <Cuerpo bs={bs} />
            {n.extraido_en_vivo && <p className="faint">Extraído en este momento del documento oficial ({n.extraido_en_vivo.formato ?? n.extraido_en_vivo.fuente}).</p>}
            {partes > 1 && (
              <nav className="paginacion" aria-label="Partes del texto">
                {q.desde > 0 && <Link className="boton sec" href={urlCon(ruta(n.id), { fecha: q.fecha, desde: Math.max(0, q.desde - PARTE) || undefined })}>← Parte anterior</Link>}
                <span className="dim">Parte {parte} de {partes}</span>
                {siguiente && <Link className="boton" href={urlCon(ruta(n.id), { fecha: q.fecha, desde: siguiente })}>Siguiente parte →</Link>}
              </nav>
            )}
          </>
        ) : n.error && q.fecha ? null : (
          <div className="panel">
            <p>{n.motivo ?? "Aún no tenemos el texto procesado de esta norma."} Los documentos oficiales están abajo.</p>
            {n.extraido_en_vivo?.nota ? <p className="dim">{n.extraido_en_vivo.nota}</p> : null}
            {!q.en_vivo && <Link className="boton sec" href={urlCon(ruta(n.id), { en_vivo: 1 })}>Extraer el texto del documento oficial ahora</Link>}
            {q.en_vivo && n.error && <p className="dim">{n.error}</p>}
          </div>
        )}
      </section>

      <section aria-labelledby="historial">
        <h2 id="historial">Historial de reformas</h2>
        <Suspense fallback={<p className="cargando">Cargando historial…</p>}>
          <Historia id={n.id} q={q} fechaVista={fechaVista} />
        </Suspense>
      </section>

      <section aria-labelledby="documentos">
        <h2 id="documentos">Documentos oficiales</h2>
        <p className="dim">Cita y verifica siempre contra el original.</p>
        <ul className="docs">
          {f.ficha_scjn && <li><a href={f.ficha_scjn} rel="noopener">Ficha de la norma en la SCJN</a></li>}
          {f.markdown_versionado && <li><a href={f.markdown_versionado}>Texto en git (todas las versiones)</a></li>}
          {docs.slice(0, 10).map((d, i) => (
            <li key={i}><span>{d.descripcion}{d.fecha ? <span className="dim"> · {d.fecha}</span> : null}</span>{" "}
              {d.enlaces.map(([e, u]) => <a key={e} href={u} rel="noopener nofollow" className="doc-enlace">{e}</a>)}</li>
          ))}
        </ul>
        {docs.length > 10 && <p className="faint">Se muestran las 10 publicaciones más recientes de {fmt.format(docs.length)}; el resto está en la ficha de la SCJN.</p>}
      </section>
    </article>
  );
}

export default function Pagina(props: PageProps<"/norma/[id]">) {
  return (
    <section className="seccion">
      <Suspense fallback={<p className="cargando">Cargando norma…</p>}>
        <Ficha {...props} />
      </Suspense>
    </section>
  );
}
