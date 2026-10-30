import Link from "next/link";

export default function NoEncontrado() {
  return (
    <section className="seccion texto">
      <h1>No encontré esa página</h1>
      <p>Si buscabas una norma, su identificador pudo cambiar. <Link href="/buscar">Búscala por nombre →</Link></p>
    </section>
  );
}
