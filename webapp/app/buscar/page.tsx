import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { Fallo, NormaItem, Select } from "@/components/ui";
import { api, ESTADOS, nombreEstado, rango, TIPOS, uno, urlCon, type Norma } from "@/lib/api";

export const metadata: Metadata = {
  title: "Buscar normas",
  description: "Buscador de leyes, reglamentos, bandos y NOM federales, estatales y municipales de México.",
};

const POR_PAGINA = 20;

type Resultado = { resultados?: Norma[]; siguiente_desde?: number | null };
type Filtros = { texto?: string; estado?: string; municipio?: string; tipo?: string; con_texto?: string; vigente?: string };

const ETIQUETA: Record<keyof Omit<Filtros, "texto">, (v: string) => string> = {
  estado: (v) => nombreEstado(v),
  municipio: (v) => `Municipio: ${v}`,
  tipo: (v) => rango(v),
  vigente: (v) => (v === "true" ? "Vigentes" : "No vigentes"),
  con_texto: () => "Con texto",
};

async function Resultados({ searchParams }: PageProps<"/buscar">) {
  const sp = await searchParams;
  const f: Filtros = {
    texto: uno(sp.texto), estado: uno(sp.estado), municipio: uno(sp.municipio), tipo: uno(sp.tipo),
    con_texto: uno(sp.con_texto), vigente: uno(sp.vigente),
  };
  const desde = Number(uno(sp.desde)) || 0;
  const activos = (Object.keys(ETIQUETA) as (keyof typeof ETIQUETA)[]).filter((k) => f[k]);
  const r = await api<Resultado>("buscar_norma", { ...f, limite: POR_PAGINA, desde });
  const res = r.resultados ?? [];
  const sinTexto = res.filter((n) => !n.has_text).length;

  return (
    <>
      <form className="panel" action="/buscar" role="search" style={{ marginBottom: 12 }}>
        <div className="busca">
          <input type="search" name="texto" defaultValue={f.texto} placeholder="Palabras del título o del texto" aria-label="Buscar norma" />
          <button className="boton" type="submit">Buscar</button>
        </div>
        <details className="mas">
          <summary>Filtros{activos.length ? ` (${activos.length})` : ""}</summary>
          <div className="filtros">
            <Select name="estado" label="Ámbito" valor={f.estado} opciones={ESTADOS} todos="Todo el país" />
            <label>Municipio
              <input type="text" name="municipio" defaultValue={f.municipio} placeholder="Ej. Zapopan" />
            </label>
            <Select name="tipo" label="Tipo" valor={f.tipo} opciones={TIPOS} />
            <Select name="vigente" label="Vigencia" valor={f.vigente} todos="Cualquiera" opciones={[["true", "Vigentes"], ["false", "No vigentes"]]} />
            <Select name="con_texto" label="Texto" valor={f.con_texto} todos="Con o sin texto" opciones={[["true", "Solo con texto"]]} />
          </div>
        </details>
      </form>

      {activos.length > 0 && (
        <p className="chips filtros-activos" aria-label="Filtros activos">
          {activos.map((k) => (
            <Link key={k} className="chip quitar" href={urlCon("/buscar", { ...f, [k]: undefined })} aria-label={`Quitar filtro ${ETIQUETA[k](f[k]!)}`}>
              {ETIQUETA[k](f[k]!)} <span aria-hidden>×</span>
            </Link>
          ))}
          {activos.length > 1 && <Link className="chip" href={urlCon("/buscar", { texto: f.texto })}>Quitar todos</Link>}
        </p>
      )}

      {r.error ? <Fallo msg={r.error} /> : !res.length ? (
        <div className="panel">
          <p>Sin resultados{f.texto ? <> para «{f.texto}»</> : null}.</p>
          <p className="dim" style={{ marginBottom: 0 }}>La búsqueda pide todas las palabras: prueba con menos, con sinónimos o quita filtros.</p>
        </div>
      ) : (
        <>
          <h2 className="conteo" aria-live="polite">
            {desde > 0 ? `${desde + 1}–${desde + res.length}` : res.length === POR_PAGINA ? `Primeras ${POR_PAGINA}` : `${res.length}`} {res.length === 1 ? "norma" : "normas"}
            {f.texto ? <> para «{f.texto}»</> : null}
          </h2>
          {!f.texto && <p className="faint">Sin palabras de búsqueda: se muestran las de reforma más reciente.</p>}
          {sinTexto > 0 && !f.con_texto && (
            <p className="nota-lista">
              {sinTexto === res.length
                ? <>Ninguna de estas tiene texto procesado aquí: están <b>solo catalogadas</b>.</>
                : <>{res.length - sinTexto} de {res.length} tienen texto procesado; las demás están <b>solo catalogadas</b>.</>}{" "}
              Su ficha enlaza el documento oficial y puede extraer el texto al momento.{" "}
              <Link href={urlCon("/buscar", { ...f, con_texto: "true" })}>Ver solo las que tienen texto</Link>
            </p>
          )}
          <ul className="lista">{res.map((n) => <NormaItem key={n.id} n={n} />)}</ul>
          <nav className="paginacion" aria-label="Paginación">
            {desde > 0 && <Link className="boton sec" href={urlCon("/buscar", { ...f, desde: Math.max(0, desde - POR_PAGINA) || undefined })}>← Anteriores</Link>}
            {r.siguiente_desde ? <Link className="boton sec" href={urlCon("/buscar", { ...f, desde: r.siguiente_desde })}>Siguientes →</Link> : null}
          </nav>
        </>
      )}
    </>
  );
}

export default function Buscar(props: PageProps<"/buscar">) {
  return (
    <section className="seccion">
      <h1>Buscar normas</h1>
      <Suspense fallback={<p className="cargando">Buscando…</p>}>
        <Resultados {...props} />
      </Suspense>
    </section>
  );
}
