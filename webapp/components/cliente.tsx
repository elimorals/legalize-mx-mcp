"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

export function Nav({ items }: { items: [string, string][] }) {
  const ruta = usePathname();
  // /guia/mcp belongs to "MCP", not to "Guía"; everything else matches by prefix
  const actual = items.map(([h]) => h).filter((h) => ruta === h || ruta.startsWith(`${h}/`)).sort((a, b) => b.length - a.length)[0];
  return (
    <nav className="nav" aria-label="Principal">
      {items.map(([href, txt]) => <Link key={href} href={href} aria-current={href === actual ? "page" : undefined}>{txt}</Link>)}
    </nav>
  );
}

export function Copiar({ texto }: { texto: string }) {
  const [hecho, setHecho] = useState(false);
  return (
    <button type="button" className="copiar" onClick={async () => {
      try { await navigator.clipboard.writeText(texto); setHecho(true); setTimeout(() => setHecho(false), 1600); } catch {}
    }}>{hecho ? "Copiado" : "Copiar"}</button>
  );
}
