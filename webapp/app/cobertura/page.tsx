import type { Metadata } from "next";
import { Suspense } from "react";
import { Fallo, Select } from "@/components/ui";
import { api, ESTADOS, fmt, nombreEstado, origen, rango, uno } from "@/lib/api";

export const metadata: Metadata = {
  title: "Cobertura",
  description: "Qué hay y qué falta: normas por fuente y tipo, y la fuente municipal de cada uno de los 2,478 municipios.",
};

type Cob = {
  normas?: Record<string, { total: number; con_texto: number | null }>;
  por_rango?: Record<string, number>;
  municipios_por_clasificacion?: Record<string, { municipios: number; poblacion: number | null }>;
};

function Tabla({ cab, filas }: { cab: string[]; filas: (string | number)[][] }) {
  return (
    <div className="tabla-scroll" style={{ marginBottom: 24 }}>
      <table>
        <thead><tr>{cab.map((c, i) => <th key={c} className={i ? "n" : ""}>{c}</th>)}</tr></thead>
        <tbody>{filas.map((f) => <tr key={String(f[0])}>{f.map((v, i) => <td key={i} className={i ? "n" : ""}>{typeof v === "number" ? fmt.format(v) : v}</td>)}</tr>)}</tbody>
      </table>
    </div>
  );
}

async function Datos({ searchParams }: PageProps<"/cobertura">) {
  const estado = uno((await searchParams).estado);
  const c = await api<Cob>("cobertura", { estado });
  if (c.error) return <Fallo msg={c.error} />;
  const fuentes = Object.entries(c.normas ?? {}).sort((a, b) => b[1].total - a[1].total);
  return (
    <>
      <form className="panel selector" action="/cobertura">
        <Select name="estado" label="Ámbito" valor={estado} opciones={ESTADOS} todos="Todo el país" />
        <button className="boton" type="submit">Ver</button>
      </form>
      <h2>Normas por fuente{estado ? ` · ${nombreEstado(estado)}` : ""}</h2>
      <Tabla cab={["Fuente", "Normas", "Con texto"]} filas={fuentes.map(([k, v]) => [origen(k), v.total, v.con_texto ?? 0])} />
      <h2>Por tipo</h2>
      <Tabla cab={["Tipo", "Normas"]} filas={Object.entries(c.por_rango ?? {}).map(([k, v]) => [rango(k) || "Sin tipo", v])} />
      {estado !== "federal" && (
        <>
          <h2>Municipios por fuente de sus normas</h2>
          <p className="dim">Cada municipio está clasificado según dónde publica su reglamentación, o por qué no se encontró.</p>
          <Tabla cab={["Clasificación", "Municipios", "Población"]}
            filas={Object.entries(c.municipios_por_clasificacion ?? {}).map(([k, v]) => [k.replaceAll("_", " "), v.municipios, v.poblacion ?? 0])} />
        </>
      )}
    </>
  );
}

export default function Cobertura(props: PageProps<"/cobertura">) {
  return (
    <section className="seccion">
      <h1>Cobertura</h1>
      <p className="texto dim">Qué normas hay en el índice, de qué fuente vienen y cuántas tienen texto procesado.</p>
      <Suspense fallback={<p className="cargando">Contando…</p>}>
        <Datos {...props} />
      </Suspense>
    </section>
  );
}
