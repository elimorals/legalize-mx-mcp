import type { Metadata, Viewport } from "next";
import Link from "next/link";
import { IBM_Plex_Mono, IBM_Plex_Sans, Newsreader } from "next/font/google";
import { Nav } from "@/components/cliente";
import { SelectorTema } from "@/components/tema";
import { SITIO } from "@/lib/api";
import "./globals.css";

const sans = IBM_Plex_Sans({ variable: "--f-sans", subsets: ["latin"], weight: ["400", "600"] });
const mono = IBM_Plex_Mono({ variable: "--f-mono", subsets: ["latin"], weight: ["400"] });
const disp = Newsreader({ variable: "--f-disp", subsets: ["latin"], weight: ["400", "600", "700"], style: ["normal", "italic"] });

export const metadata: Metadata = {
  metadataBase: new URL(SITIO),
  title: { default: "Legislación mexicana con historial de reformas", template: "%s · legalize-mx" },
  description:
    "Busca leyes, reglamentos y bandos federales, estatales y municipales de México, lee el texto vigente o el de cualquier fecha y conecta tu agente de IA por MCP.",
  openGraph: { type: "website", locale: "es_MX", siteName: "legalize-mx" },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fbf8f1" },
    { media: "(prefers-color-scheme: dark)", color: "#1b1815" },
  ],
};

const SCRIPT_TEMA = `(function(){try{var t=localStorage.getItem("tema");if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t)}catch(e){}})()`;

const NAV: [string, string][] = [
  ["/buscar", "Buscar"],
  ["/cobertura", "Cobertura"],
  ["/guia", "Guía"],
  ["/guia/mcp", "MCP"],
  ["/como-se-hizo", "Cómo se hizo"],
  ["/acerca", "Acerca"],
];

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es-MX" className={`${sans.variable} ${mono.variable} ${disp.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: SCRIPT_TEMA }} />
      </head>
      <body>
        <header className="cabecera">
          <div className="contenedor">
            <div className="fila">
              <Link href="/" className="marca">legalize<b>mx</b><span className="sub"> · legislación con historial</span></Link>
              <SelectorTema />
            </div>
            <Nav items={NAV} />
          </div>
        </header>
        <main className="contenedor">{children}</main>
        <footer className="pie">
          <div className="contenedor">
            <p>Proyecto independiente y no oficial. No es asesoría legal: verifica siempre con la fuente oficial.</p>
            <p>
              <a href="https://github.com/elimorals/legalize-mx-mcp">Código (MIT)</a> ·{" "}
              <a href="https://github.com/elimorals/legalize-mx">Leyes en git</a> ·{" "}
              <a href="https://huggingface.co/datasets/elimoralsmendox/legalize-mx">Dataset</a> ·{" "}
              <Link href="/guia">MCP, CLI y API</Link> · <Link href="/como-se-hizo">Cómo se hizo</Link>
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
