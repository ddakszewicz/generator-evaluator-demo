# Generator / Evaluator demo

Ejemplo mínimo del patrón **Generator / Evaluator** con Claude Code.
La idea (de la charla "Agentes SWE de largo horizonte"):

> **Separá el agente que construye del agente que juzga.**
> Un agente que se corrige a sí mismo arrastra dos sesgos: ansiedad de contexto
> (cierra antes de tiempo) y sesgo de autoevaluación (aprueba su propio trabajo
> mediocre). Dos roles separados, con permisos asimétricos, lo destraban.

## La tarea (chiquita a propósito)

Implementar `parse_duration("1h30m") -> 5400` en `src/duration.py`.
El foco no es la tarea — es el **workflow**.

## Dos versiones (mostrar la evolución en clase)

- **`/` (raíz, v1)** — tests escritos **a mano** por el humano. Baseline simple.
- **[`v2-criterios-no-casos/`](v2-criterios-no-casos/)** — el humano escribe
  **propiedades**, el **evaluator** genera los tests con property-based testing
  (Hypothesis). Responde a la crítica "escribir tests a mano no escala".

El arco pedagógico: v1 te muestra la separación de roles; v2 te muestra que lo
que escribís a mano es el **criterio**, no los **casos**.

## Estructura

```
generator-evaluator-demo/
├── CONTRACT.md              ← el Sprint Contract (criterios verificables)
├── src/duration.py          ← lo que el GENERATOR implementa (arranca como stub)
├── tests/test_duration.py   ← el ORACLE duro (pytest). Nadie lo edita.
├── .claude/agents/
│   ├── generator.md         ← subagente: construye. tools: Read/Write/Edit/Bash
│   └── evaluator.md         ← subagente: juzga. disallowedTools: Write/Edit
└── orchestrate.py           ← el loop automatizado (CI-style)
```

## Las 3 piezas del patrón

1. **El contrato** (`CONTRACT.md`) — la spec verificable. *El verifier es el techo:*
   si el contrato es vago, todo falla. Es donde más conviene invertir.
2. **Permisos asimétricos** — la separación está **en la config, no en el prompt**:
   - `generator.md`: `tools: Read, Write, Edit, Bash` (construye)
   - `evaluator.md`: `disallowedTools: Write, Edit` (no puede tocar el código)
3. **El oracle duro** (`pytest`) — árbitro objetivo. El evaluator lo corre, no lo
   discute. Sin un oracle, el evaluator es solo otra opinión.

## Cómo correrlo

### Opción A — interactivo (la más simple)
```bash
cd generator-evaluator-demo
claude
```
Y en el chat:
> Usá el subagente generator para cumplir CONTRACT.md. Después el evaluator para
> verificar contra los tests. Iterá hasta que `pytest -q` pase.

### Opción B — automatizado (mostrar el loop sin humano)
```bash
pip install pytest
npm i -g @anthropic-ai/claude-code && claude login   # si no lo tenés
python orchestrate.py
```

### Ver el estado del oracle en cualquier momento
```bash
python orchestrate.py --oracle      # corre solo pytest
# arranca en ROJO (el stub levanta NotImplementedError)
```

## Qué observar en clase

- Arranca en **rojo**: 10 tests fallando (el stub no hace nada).
- El **generator** suele clavar el happy path rápido pero **saltarse los casos de
  error** (tests 8-10). Ahí se ve el sesgo: "reporta éxito" antes de tiempo.
- El **evaluator** corre el oracle, marca los FAIL con evidencia, y NO aprueba.
- Tras 1-2 rondas de feedback, llega a **verde**.

El momento pedagógico: el generator solo casi nunca cierra los casos de error en
la primera. La separación de roles es lo que sube la calidad.

## Guardrails

- `MAX_ROUNDS = 5` en `orchestrate.py` — corta el loop (no factura infinita).
- El evaluator no puede editar (permisos) — no puede "arreglar para aprobarse".
- pytest es determinístico — el veredicto final no depende de la opinión del LLM.
