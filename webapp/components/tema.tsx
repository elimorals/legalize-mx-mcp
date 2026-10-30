"use client";
import { useEffect, useState } from "react";

type Tema = "sistema" | "light" | "dark";

// El script inline del layout aplica el tema guardado antes del primer pintado (la página no parpadea);
// aquí solo se refleja en los botones tras montar y se cambia al hacer clic.
export function SelectorTema() {
  const [tema, setTema] = useState<Tema>("sistema");
  useEffect(() => {
    try { setTema((localStorage.getItem("tema") as Tema) || "sistema"); } catch {}
  }, []);
  const elegir = (t: Tema) => {
    setTema(t);
    try { if (t === "sistema") localStorage.removeItem("tema"); else localStorage.setItem("tema", t); } catch {}
    if (t === "sistema") document.documentElement.removeAttribute("data-theme");
    else document.documentElement.setAttribute("data-theme", t);
  };
  return (
    <div className="tema" role="group" aria-label="Tema de color">
      {([["light", "Claro"], ["dark", "Oscuro"], ["sistema", "Auto"]] as [Tema, string][]).map(([t, txt]) => (
        <button key={t} type="button" aria-pressed={tema === t} onClick={() => elegir(t)}>{txt}</button>
      ))}
    </div>
  );
}
