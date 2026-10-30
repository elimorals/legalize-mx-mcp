import type { MetadataRoute } from "next";
import { SITIO } from "@/lib/api";

export default function sitemap(): MetadataRoute.Sitemap {
  return ["", "/buscar", "/cobertura", "/guia", "/guia/mcp", "/guia/api", "/acerca", "/norma/CPEUM", "/norma/LFT"]
    .map((p) => ({ url: `${SITIO}${p}` }));
}
