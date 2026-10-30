import type { Metadata } from "next";
import { Suspense } from "react";
import { Fallo } from "@/components/ui";
import { api, uno } from "@/lib/api";

export const metadata: Metadata = {
  title: "DOF del día",
  description: "Lo normativo que publicó hoy el Diario Oficial de la Federación, consultado en vivo desde su API oficial.",
};

type Nota = { codigo: number; titulo: string; dependencia?: string; seccion?: string; pagina?: number; edicion?: string; url: string };
type Dia = { fecha?: string; n?: number; notas?: Nota[] };

const EDICION: Record<string, string> = { matutinas: "Matutina", vespertinas: "Vespertina", extraordinarias: "Extraordinaria" };

async function Notas({ searchParams }: PageProps<"/dof">) {
  const sp = await searchParams;
  const fecha = uno(sp.fecha);
  const todas = uno(sp.todas) === "1";
  const d = await api<Dia>("dof_del_dia", { fecha, solo_normativas: todas ? false : undefined }, 900);
  return (
    <>
      <form className="panel selector" action="/dof">
        <label>Fecha<input type="date" name="fecha" defaultValue={d.fecha ?? fecha} /></label>
        <label className="casilla"><input type="checkbox" name="todas" value="1" defaultChecked={todas} /> Incluir avisos, convocatorias y edictos</label>
        <button className="boton" type="submit">Ver</button>
      </form>
      {d.error ? <Fallo msg={d.error} /> : !d.notas?.length ? (
        <p>El DOF no publicó notas {todas ? "" : "normativas "}el {d.fecha}. Los fines de semana y días festivos no suele haber edición.</p>
      ) : (
        <>
          <p className="dim">{d.n} {todas ? "notas" : "notas normativas"} del {d.fecha}.</p>
          <ul className="lista">
            {d.notas.map((n) => (
              <li key={n.codigo} className="item">
                <h3 className="titulo-norma"><a href={n.url} rel="noopener">{n.titulo}</a></h3>
                <div className="meta">
                  {n.dependencia && <span>{n.dependencia}</span>}
                  {n.edicion && <span>Edición {EDICION[n.edicion] ?? n.edicion}</span>}
                  {n.pagina ? <span>página {n.pagina}</span> : null}
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </>
  );
}

export default function Dof(props: PageProps<"/dof">) {
  return (
    <section className="seccion">
      <h1>DOF del día</h1>
      <p className="texto dim">Decretos, acuerdos, reglamentos, lineamientos y NOM que publicó el Diario Oficial de la Federación. Se consulta en vivo; cada nota enlaza al DOF.</p>
      <Suspense fallback={<p className="cargando">Consultando el DOF…</p>}>
        <Notas {...props} />
      </Suspense>
    </section>
  );
}
