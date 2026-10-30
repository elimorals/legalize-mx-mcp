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

export function lugar(n: Pick<Norma, "state" | "municipality">) {
  if (!n.state || n.state === "federal") return "Federal";
  return n.municipality ? `${n.municipality}, ${nombreEstado(n.state)}` : nombreEstado(n.state);
}
