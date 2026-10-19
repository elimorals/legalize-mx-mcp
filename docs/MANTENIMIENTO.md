# Mantenimiento

Para quien publica los datos. El pipeline que cosecha y genera el repo vive en `legalize-mex/pipeline` (rama `mx`); este repo solo construye y publica el índice del MCP.

## Ciclo de publicación

```
cosecha / actualización diaria  →  legalize commit (git)  →  push a GitHub  →  export a HF  →  índice del MCP
       (pipeline)                    (pipeline)              (pipeline)        (pipeline)       (este repo)
```

1. **Repo y dataset:** `pipeline/ops/mx/publicar.sh` hace el commit incremental, `repack`, push por partes y la exportación y subida a Hugging Face.
2. **Índice del MCP:**

   ```bash
   cd ~/Developer/legalize-mx-mcp
   rm -f dist/*.gz
   python3 scripts/build_index.py --data ~/Developer/legalize-mex/data-mx \
     --repo ~/Developer/legalize-mex/legalize-mx --censo ~/Developer/legalize-mex/research-censo \
     --municipios ~/Developer/legalize-mex/pipeline/src/legalize/fetcher/mx/municipios.json --out dist
   zsh scripts/publish_index.sh dist          # sube y deja una sola versión en HF
   python3 scripts/gen_fuentes_md.py dist/index.sqlite docs/FUENTES.md
   ```

   Construirlo tarda ~2 min y la descarga final pesa ~90 MB. Los clientes la detectan en ≤24 h y muestran `aviso_indice` mientras tanto.

## Reglas que no se rompen

- **Un commit = una publicación oficial.** Un error de datos nunca se corrige con un commit encima: la ley afectada se **reprocesa**. Se reconstruye su JSON, se quita su historial (`git filter-repo --invert-paths`), se recrean sus commits y se publica con `legalize push --force`. Lo mismo se hizo con las versiones contaminadas en octubre de 2026 (`pipeline/ops/mx/refill_finish.sh`).
- **SCJN en un solo proceso.** Con varios en paralelo, la SCJN sirvió documentos de otras normas.
- **Nada de credenciales ni de saltarse captchas o WAF.** Las fuentes bloqueadas se documentan como bloqueadas.
- **≤1 petición por segundo por host**; más lento si el sitio responde 429.
- **Antes de un force push:** respaldo con `cp -cR` (clon de APFS), verificaciones (que estén todos los archivos, que no haya texto ajeno, `git fsck`) y luego publicar.

## Calidad de la skill

```bash
cd ~/Developer/legalize-mx-mcp
# ¿se activa cuando debe? (20 preguntas, plugin real)
python3 skills/legalize-mx/evals/trigger_check.py skills/legalize-mx/evals/trigger-eval.json
# ¿responde mejor con skill que sin ella? (3 casos, con/sin skill)
skills/legalize-mx/evals/run_iteration.sh <workspace>/iteration-N
zsh skills/legalize-mx/evals/benchmark.sh <workspace>/iteration-N
```

Último resultado (17-oct-2026): activación 19/20, con recall 10/10 y 1 falso positivo razonable; respuestas con 100 % de aserciones cumplidas.

## Tests

```bash
uv run --extra dev pytest -q      # offline: índice y repo git de prueba, sin red
uvx ruff check src scripts tests
```
