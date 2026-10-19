"""Write docs/FUENTES.md from the built index: one row per source with its counts.

python3 scripts/gen_fuentes_md.py dist/index.sqlite docs/FUENTES.md
"""

import sqlite3
import sys
from pathlib import Path

# What each source is and where it comes from (official sites only).
DESC = {
    "scjn": (
        "Catálogo legislativo de la SCJN: federal, CDMX, 31 estados y tratados",
        "legislacion.scjn.gob.mx",
    ),
    "dof": (
        "Notas normativas del Diario Oficial de la Federación (NOM, lineamientos, acuerdos generales, reglamentos, decretos)",
        "sidof.segob.gob.mx",
    ),
    "dof-nom": (
        "Índice oficial de Normas Oficiales Mexicanas del DOF",
        "dof.gob.mx/normasOficiales",
    ),
    "diputados": (
        "Leyes federales vigentes, abrogadas y reglamentos de la Cámara de Diputados",
        "diputados.gob.mx/LeyesBiblio",
    ),
    "oaxaca-poe-municipal": (
        "Periódico Oficial de Oaxaca, publicaciones municipales y leyes de ingresos (570 municipios)",
        "periodicooficial.oaxaca.gob.mx",
    ),
    "puebla-ojp": (
        "Orden Jurídico Poblano: normativa estatal y de los 217 municipios",
        "ojp.puebla.gob.mx",
    ),
    "slp-poe": ("Periódico Oficial de San Luis Potosí (API)", "periodicooficial.slp.gob.mx"),
    "gto-normateca": (
        "Normateca Estatal y Municipal de Guanajuato (46/46 municipios)",
        "normatividadestatalymunicipal.guanajuato.gob.mx",
    ),
    "tlaxcala-poe": (
        "Índice anual del Periódico Oficial de Tlaxcala (60/60 municipios)",
        "publicaciones.tlaxcala.gob.mx",
    ),
    "jalisco-transparencia-municipal": (
        "Información fundamental de municipios pequeños de Jalisco hospedada por el estado",
        "transparencia.info.jalisco.gob.mx",
    ),
    "guerrero-poe-bandos": (
        "Periódico Oficial de Guerrero: bandos y publicaciones municipales",
        "periodicooficial.guerrero.gob.mx",
    ),
    "morelos-marco": (
        "Marco Jurídico de Morelos: estatal y 36/36 municipios (Word)",
        "marcojuridico.morelos.gob.mx",
    ),
    "edomex-bandos": (
        "Bandos municipales del Estado de México 2016–2026",
        "legislacion.edomex.gob.mx",
    ),
    "sinaloa-poe": (
        "Periódico Oficial de Sinaloa: índice de cada edición desde 2003",
        "iip/POE Sinaloa",
    ),
    "sinaloa-iip": (
        "Reglamentos municipales del Instituto de Investigaciones Parlamentarias de Sinaloa",
        "iip.congresosinaloa.gob.mx",
    ),
    "hidalgo-poe": (
        "Periódico Oficial de Hidalgo (normativa estatal y municipal)",
        "periodico.hidalgo.gob.mx",
    ),
    "tamaulipas-poe": (
        "Reglamentos municipales del Periódico Oficial de Tamaulipas",
        "po.tamaulipas.gob.mx",
    ),
    "chiapas-sgg": (
        "Reglamentos y leyes de ingresos municipales de la SGG de Chiapas (2001–2021)",
        "sgg.chiapas.gob.mx",
    ),
    "consejeria-cmx": (
        "Consejería Jurídica de la CDMX, incluido el histórico",
        "data.consejeria.cdmx.gob.mx",
    ),
    "muni-wordpress": (
        "Portales municipales propios en WordPress (municipios grandes)",
        "portales .gob.mx",
    ),
    "muni-wordpress-2": (
        "Portales municipales propios en WordPress (censo nacional)",
        "portales .gob.mx",
    ),
    "muni-html": ("Portales municipales propios en HTML (municipios grandes)", "portales .gob.mx"),
    "muni-html-2": ("Portales municipales propios en HTML (censo nacional)", "portales .gob.mx"),
    "muni-api": (
        "APIs propias de municipios (Tijuana, León, Puebla, Querétaro, Mérida, Hermosillo…)",
        "portales .gob.mx",
    ),
}
STATE_NAMES = {
    "agu": "Aguascalientes",
    "bcn": "Baja California",
    "bcs": "Baja California Sur",
    "cam": "Campeche",
    "chp": "Chiapas",
    "chh": "Chihuahua",
    "cmx": "Ciudad de México",
    "coa": "Coahuila",
    "col": "Colima",
    "dur": "Durango",
    "gua": "Guanajuato",
    "gro": "Guerrero",
    "hid": "Hidalgo",
    "jal": "Jalisco",
    "mex": "Estado de México",
    "mic": "Michoacán",
    "mor": "Morelos",
    "nay": "Nayarit",
    "nle": "Nuevo León",
    "oax": "Oaxaca",
    "pue": "Puebla",
    "que": "Querétaro",
    "roo": "Quintana Roo",
    "slp": "San Luis Potosí",
    "sin": "Sinaloa",
    "son": "Sonora",
    "tab": "Tabasco",
    "tam": "Tamaulipas",
    "tla": "Tlaxcala",
    "ver": "Veracruz",
    "yuc": "Yucatán",
    "zac": "Zacatecas",
}


def describe(slug: str) -> tuple[str, str]:
    if slug in DESC:
        return DESC[slug]
    if slug.startswith("congreso-"):
        st = slug.split("-", 1)[1]
        return (
            f"Leyes y códigos publicados por el Congreso de {STATE_NAMES.get(st, st.upper())}",
            "sitio del congreso",
        )
    return ("", "")


def main() -> None:
    db = sqlite3.connect(sys.argv[1])
    meta = dict(db.execute("SELECT key, value FROM meta"))
    rows = db.execute(
        "SELECT origin, count(*), sum(has_text), sum(status='in_force'), min(nullif(publication_date,'')),"
        " max(nullif(publication_date,'')), count(DISTINCT state), count(DISTINCT municipality_inegi)"
        " FROM norms GROUP BY origin ORDER BY 2 DESC"
    ).fetchall()
    out = [
        "# Fuentes",
        "",
        (
            f"Generado de forma automática por `scripts/gen_fuentes_md.py` con el índice `{meta.get('version')}` "
            f"({meta.get('built', '')[:10]}). Total: **{int(meta.get('norms', 0)):,} normas** de "
            f"**{meta.get('sources')} fuentes**, **{int(meta.get('with_text', 0)):,} con texto**."
        ),
        "",
        (
            "Todas las fuentes son oficiales. El id de una norma de cualquier fuente distinta de la SCJN es "
            "`{fuente}:{id}`; las de la SCJN usan su propio id (ver [DATOS.md](DATOS.md))."
        ),
        "",
        "| Fuente (`fuente=`) | Qué es | Sitio | Normas | Con texto | Vigentes | Fechas | Estados | Municipios |",
        "|---|---|---|---:|---:|---:|---|---:|---:|",
    ]
    for o, n, t, v, d0, d1, ns, nm in rows:
        what, site = describe(o)
        dates = f"{(d0 or '')[:4]}–{(d1 or '')[:4]}" if d0 else "—"
        out.append(
            f"| `{o}` | {what} | {site} | {n:,} | {t or 0:,} | {v or 0:,} | {dates} | {ns} | {nm} |"
        )
    out += [
        "",
        "**Cómo leer la tabla**",
        "",
        (
            "- **Con texto:** normas cuyo texto está procesado y versionado en git (`has_text`). El resto se puede "
            "leer en vivo con `leer_norma(id, extraer_en_vivo=true)`."
        ),
        (
            "- **Vigentes:** solo cuentan las que la fuente marca como vigentes. Muchas fuentes municipales no lo "
            "indican, y aparecen como `unknown`."
        ),
        "- **Fechas** y **municipios** se llenan solo cuando la fuente los publica.",
        (
            "- Las fuentes se solapan: una misma ley puede venir de la SCJN y del congreso de su estado. Se conservan "
            "las dos, porque cada una es un documento oficial distinto, y la búsqueda prioriza la que tiene texto."
        ),
        "",
        "Cobertura municipal por municipio: `cobertura(estado, municipio)` (censo de los 2,478 municipios).",
    ]
    Path(sys.argv[2]).parent.mkdir(parents=True, exist_ok=True)
    Path(sys.argv[2]).write_text("\n".join(out) + "\n")
    print(f"{sys.argv[2]}: {len(rows)} fuentes")


if __name__ == "__main__":
    main()
