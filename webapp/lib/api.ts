import "server-only";

// The Python service (servidor/) answers both /mcp and /api/<tool>. In production MCP_URL is the
// private binding declared in vercel.json; locally it falls back to the public deployment.
const BASE = process.env.MCP_URL ?? "https://legalize-mx.vercel.app";
export const SITIO = process.env.NEXT_PUBLIC_SITIO ?? "https://legalize-mx.vercel.app";

type Params = Record<string, string | number | boolean | undefined | null>;

/** One tool of the MCP as JSON. Errors from the tool come back in `error`, never thrown. */
export async function api<T = Record<string, unknown>>(tool: string, params: Params = {}, revalidate = 3600) {
  const url = new URL(`/api/${tool}`, BASE);
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
  try {
    const r = await fetch(url, { next: { revalidate } });
    return (await r.json()) as T & { error?: string };
  } catch (e) {
    return { error: `no pude consultar el servidor: ${(e as Error).message}` } as T & { error?: string };
  }
}

export type Herramienta = { name: string; description?: string; inputSchema: { properties?: Record<string, Prop>; required?: string[] } };
export type Prop = { type?: string; anyOf?: { type?: string }[]; default?: unknown; description?: string };

/** The tool list exactly as the MCP publishes it (descriptions and parameters are not copied by hand). */
export async function herramientas(): Promise<Herramienta[]> {
  try {
    const r = await fetch(new URL("/mcp", BASE), {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json, text/event-stream" },
      body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/list" }),
      next: { revalidate: 86400 },
    });
    return (await r.json()).result.tools;
  } catch {
    return [];
  }
}

export type Norma = {
  id: string; title: string; origin: string; scope?: string; state: string | null; municipality: string | null;
  rank: string | null; status: string | null; publication_date: string | null; last_updated: string | null;
  has_text: boolean; url?: string; fragmento?: string | null; texto_estado?: string; fuente_texto?: string;
};

export const ESTADOS: [string, string][] = [
  ["federal", "Federal"], ["AGU", "Aguascalientes"], ["BCN", "Baja California"], ["BCS", "Baja California Sur"],
  ["CAM", "Campeche"], ["CHP", "Chiapas"], ["CHH", "Chihuahua"], ["CMX", "Ciudad de México"], ["COA", "Coahuila"],
  ["COL", "Colima"], ["DUR", "Durango"], ["GUA", "Guanajuato"], ["GRO", "Guerrero"], ["HID", "Hidalgo"],
  ["JAL", "Jalisco"], ["MEX", "Estado de México"], ["MIC", "Michoacán"], ["MOR", "Morelos"], ["NAY", "Nayarit"],
  ["NLE", "Nuevo León"], ["OAX", "Oaxaca"], ["PUE", "Puebla"], ["QUE", "Querétaro"], ["ROO", "Quintana Roo"],
  ["SLP", "San Luis Potosí"], ["SIN", "Sinaloa"], ["SON", "Sonora"], ["TAB", "Tabasco"], ["TAM", "Tamaulipas"],
  ["TLA", "Tlaxcala"], ["VER", "Veracruz"], ["YUC", "Yucatán"], ["ZAC", "Zacatecas"],
];
export const nombreEstado = (c: string | null) => ESTADOS.find(([k]) => k === c)?.[1] ?? c ?? "";

// The most common `rank` values in the index.
export const TIPOS: [string, string][] = [
  ["ley", "Ley"], ["codigo", "Código"], ["reglamento", "Reglamento"], ["bando", "Bando"], ["decreto", "Decreto"],
  ["acuerdo", "Acuerdo"], ["lineamientos", "Lineamientos"], ["reglas", "Reglas"], ["nom", "NOM"],
  ["tratado", "Tratado"], ["ley_de_ingresos", "Ley de ingresos"], ["presupuesto", "Presupuesto"],
  ["manual", "Manual"], ["estatuto", "Estatuto"], ["circular", "Circular"],
];

export const ESTATUS: Record<string, string> = { repealed: "Abrogada", annulled: "Anulada", expired: "Vencida" };

const RANGOS: Record<string, string> = {
  constitucion: "Constitución", ley: "Ley", ley_federal: "Ley federal", ley_general: "Ley general", codigo: "Código",
  reglamento: "Reglamento", bando: "Bando", decreto: "Decreto", acuerdo: "Acuerdo", "acuerdo-general": "Acuerdo general",
  lineamientos: "Lineamientos", reglas: "Reglas", nom: "NOM", "proyecto-nom": "Proyecto de NOM", tratado: "Tratado",
  ley_de_ingresos: "Ley de ingresos", presupuesto: "Presupuesto", manual: "Manual", estatuto: "Estatuto",
  circular: "Circular", disposiciones: "Disposiciones", miscelanea: "Miscelánea", otro: "Otro",
};
export const rango = (r: string | null | undefined) => (r ? RANGOS[r] ?? r.replaceAll("_", " ") : "");

const ORIGENES: Record<string, string> = { scjn: "SCJN", dof: "DOF", diputados: "Cámara de Diputados" };
export const origen = (o: string | null | undefined) => (o ? ORIGENES[o] ?? o : "");

export const fmt = new Intl.NumberFormat("es-MX");
export const uno = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v) || undefined;

export function urlCon(base: string, params: Record<string, string | number | undefined>) {
  const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined && v !== "").map(([k, v]) => [k, String(v)]));
  const s = q.toString();
  return s ? `${base}?${s}` : base;
}

// Display casing for titles the sources publish in capitals ("CONSTITUCION POLITICA DE LOS…").
// Only all-caps titles are touched; the official title stays available to cite.
const MENORES = new Set(["de", "del", "la", "las", "el", "los", "y", "e", "en", "para", "por", "a", "al", "con", "sobre", "o", "u", "que", "se", "su", "sus", "lo"]);
const SIGLAS = new Set(["cdmx", "dof", "nom", "sat", "imss", "issste", "infonavit", "pemex", "cfe", "inegi", "scjn", "unam", "ipn", "conagua", "sep", "shcp", "iva", "isr", "ieps", "dif", "tlcan", "t-mec"]);
const ACENTOS: Record<string, string> = {
  constitucion: "constitución", politica: "política", codigo: "código", organica: "orgánica", organico: "orgánico",
  administracion: "administración", educacion: "educación", informacion: "información", proteccion: "protección",
  participacion: "participación", procuraduria: "procuraduría", republica: "república", mexico: "méxico",
  juridica: "jurídica", economico: "económico", economica: "económica", credito: "crédito", publico: "público",
  publica: "pública", publicos: "públicos", tecnico: "técnico", transito: "tránsito", regimen: "régimen",
  poblacion: "población", contribucion: "contribución", fiscalizacion: "fiscalización", legislacion: "legislación",
  comision: "comisión", union: "unión", accion: "acción", funcion: "función", prevencion: "prevención",
  atencion: "atención", ecologico: "ecológico", ecologica: "ecológica", energia: "energía", via: "vía",
  estadistica: "estadística", tecnologia: "tecnología", vehiculos: "vehículos",
  policia: "policía", gestion: "gestión", inversion: "inversión", produccion: "producción", obligacion: "obligación",
  construccion: "construcción", titulo: "título", electrica: "eléctrica", electricas: "eléctricas", publicas: "públicas", juridicos: "jurídicos", ambito: "ámbito", reglamentacion: "reglamentación", organizacion: "organización", tecnica: "técnica", tecnicas: "técnicas", planeacion: "planeación", juridico: "jurídico",
};

export function titulo(t: string) {
  const limpio = t.replace(/^\d{1,3}\s+(?=\p{L})/u, "").trim(); // "03 Reglamento…" (municipal file names)
  if (/\p{Ll}/u.test(limpio) || limpio.length < 5) return limpio;
  return limpio.split(/(\s+)/).map((w, i) => {
    if (/^\s+$/.test(w)) return w;
    const m = /^([^\p{L}\d]*)([\p{L}\d.\-]+)(.*)$/u.exec(w);
    if (!m) return w;
    const [, pre, palabra, post] = m;
    const base = palabra.toLowerCase().replace(/\.$/, "");
    if (/\d/.test(palabra) || /^(?=[ivx])x{0,3}(?:ix|iv|v?i{0,3})\.?$/i.test(palabra) || SIGLAS.has(base)) return w;
    const conAcento = ACENTOS[base] ? palabra.toLowerCase().replace(base, ACENTOS[base]) : palabra.toLowerCase();
    const cap = i > 0 && MENORES.has(base) ? conAcento : conAcento.charAt(0).toUpperCase() + conAcento.slice(1);
    return pre + cap + post;
  }).join("");
}

export function lugar(n: Pick<Norma, "state" | "municipality">) {
  if (!n.state || n.state === "federal") return "Federal";
  return n.municipality ? `${n.municipality}, ${nombreEstado(n.state)}` : nombreEstado(n.state);
}
