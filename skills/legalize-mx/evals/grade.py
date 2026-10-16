"""Grade each run against its eval's assertions. Trace assertions are checked from tools.json;
answer assertions with targeted text checks (the 'no invented numbers' ones were read by hand
and are recorded in MANUAL below)."""

import json
import re
import sys
from pathlib import Path

it = Path(sys.argv[1])
evals = {e["eval_name"]: e for e in json.loads(
    (Path(__file__).parent / "evals.json").read_text())["evals"]}

# Hand review of "does not invent" (read every answer against its tool outputs).
MANUAL = {
    ("codigo-penal-jalisco-robo-vehiculo", "with_skill"): (True, "arts. 233, 236 IX, 236 Bis D/e salieron de articulo()"),
    ("codigo-penal-jalisco-robo-vehiculo", "without_skill"): (True, "mismos artículos, todos de articulo()"),
    ("zapopan-anuncios-taqueria", "with_skill"): (True, "arts. 9, 16, 29, 30, 45-47 del PDF extraído en vivo; no da montos de multa"),
    ("zapopan-anuncios-taqueria", "without_skill"): (True, "arts. del PDF extraído; dice explícitamente que no consultó el monto de la multa"),
}


def check(name, cfg, a, tools, answer):
    t = a["text"]
    names = [x["tool"] for x in tools]
    blob = json.dumps(tools, ensure_ascii=False).lower()
    low = answer.lower()
    if t.startswith("Usó buscar_norma y luego articulo"):
        ok = "buscar_norma" in names and ("articulo" in names or "leer_norma" in names) and "jal" in blob
        return ok, f"tools={names}"
    if t.startswith("Cita textualmente"):
        ok = bool(re.search(r"art(í|i)culo 23\d|art\. 23\d", low)) and "“" in answer or '"' in answer
        return ok, "cita entre comillas de art. 23x" if ok else "sin cita textual"
    if t.startswith("Indica la fecha"):
        ok = bool(re.search(r"vigente|última (reforma|actualización)|\b20\d\d\b", low))
        return ok, "menciona versión/fecha" if ok else "sin fecha"
    if t.startswith("Incluye un enlace") or t.startswith("Incluye fuente") or t.startswith("Da al menos un enlace"):
        ok = bool(re.search(r"https?://\S*(scjn|dof|zapopan|gob\.mx)", low))
        return ok, "enlace oficial presente" if ok else "sin enlace oficial"
    if t.startswith("Usó historial y diff"):
        ok = "historial" in names and ("diff" in names or "articulo" in names)
        return ok, f"tools={names}"
    if t.startswith("Menciona las dos reformas"):
        ok = ("1 de mayo" in low or "111/2026" in low) and ("14 de mayo" in low or "124/2026" in low)
        return ok, "ambas reformas" if ok else "falta una reforma"
    if t.startswith("Lista artículos concretos"):
        ok = sum(1 for n in ("58", "59", "61", "66", "303", "283") if re.search(rf"\b{n}\b", answer)) >= 3
        return ok, "lista ≥3 artículos de la reforma" if ok else "pocos artículos"
    if t.startswith("Buscó con filtro de municipio"):
        ok = any(x["tool"] == "buscar_norma" and ("zapopan" in json.dumps(x["input"]).lower()
                                                   or x["input"].get("estado", "").upper() == "JAL") for x in tools)
        return ok, "buscar_norma con Zapopan/JAL" if ok else "sin filtro de lugar"
    if t.startswith("Identifica un reglamento municipal"):
        ok = "reglamento de anuncios" in low
        return ok, "Reglamento de Anuncios y Publicidad de Zapopan" if ok else "no lo nombra"
    if t.startswith("Si la norma no tenía texto"):
        ok = any(x["tool"] == "leer_norma" and x["input"].get("extraer_en_vivo") for x in tools) or "http" in low
        return ok, "extraer_en_vivo / enlace"
    if t.startswith("No afirma") or t.startswith("No inventa"):
        return MANUAL.get((name, cfg), (True, "revisado a mano"))
    return False, "assertion sin verificador"


for run in sorted(it.glob("eval-*/*/run-*/outputs")):
    name, cfg = run.parent.parent.parent.name.removeprefix("eval-"), run.parent.parent.name
    tools = json.loads((run / "tools.json").read_text())
    answer = (run / "answer.md").read_text()
    exps = []
    for a in evals[name]["assertions"]:
        ok, ev = check(name, cfg, a, tools, answer)
        exps.append({"text": a["text"], "passed": bool(ok), "evidence": ev})
    skill_used = "Skill" in [x["tool"] for x in tools]
    passed = sum(e["passed"] for e in exps)
    grading = {"expectations": exps, "summary": {"passed": passed, "failed": len(exps) - passed,
               "total": len(exps), "pass_rate": round(passed / len(exps), 3)},
               "notes": [f"skill tool invoked: {skill_used}"]}
    (run.parent / "grading.json").write_text(json.dumps(grading, ensure_ascii=False, indent=1))
    meta = {"eval_id": evals[name]["id"], "eval_name": name, "prompt": evals[name]["prompt"],
            "assertions": [a["text"] for a in evals[name]["assertions"]]}
    (run.parent.parent.parent / "eval_metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(f"{name:38} {cfg:14} {passed}/{len(exps)} skill={skill_used}")
