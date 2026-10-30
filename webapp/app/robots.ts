import type { MetadataRoute } from "next";
import { SITIO } from "@/lib/api";

export default function robots(): MetadataRoute.Robots {
  return { rules: { userAgent: "*", allow: "/", disallow: ["/api/", "/mcp"] }, sitemap: `${SITIO}/sitemap.xml` };
}
