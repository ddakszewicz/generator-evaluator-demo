# Generator / Evaluator demo

Ejemplo mínimo del patrón **Generator / Evaluator** con Claude Code.
De la charla "Agentes SWE de largo horizonte":

> **Separá el agente que construye del agente que juzga.** Un agente que se
> corrige a sí mismo arrastra dos sesgos: ansiedad de contexto (cierra antes de
> tiempo) y sesgo de autoevaluación (aprueba su propio trabajo mediocre).

## Por qué un evaluator-LLM no es "el autoaprobado movido un casillero"

Por dos propiedades, y son el corazón del patrón:

1. **Contexto fresco.** El evaluator es un agente **separado, con su propio
   context window**. No ve el razonamiento del generator ("escribí X, debería
   andar"). Ese sesgo vive en el contexto del generator; el evaluator no lo
   hereda → juzga el **artefacto**, no la intención.
2. **No puede tocar lo que juzga (permisos asimétricos).** Sólo Read + Bash.
   No edita `src/` (no "arregla para aprobar") ni `spec.yaml` (no afloja el
   criterio). *La separación está en la config, no en el prompt.*

Más: **postura adversarial** (tuneado para romper, no confirmar) y **"the
verifier is the ceiling"** (el sistema no supera la calidad de su juez).

## El oracle es el instrumento del evaluator, no su reemplazo

Cuando existe una verdad objetiva, no la tirás: la usás como **árbitro duro**.
Acá el oracle es `runner.py` + `spec.yaml` (criterio del humano como **dato**,
corrido con Hypothesis). El evaluator se apoya en él **y** agrega lo que el
oracle no ve (fragilidad, casos que el spec no cubre). Es el caso del compilador
C: agentes generator/evaluator **y** GCC como oracle — complementarios.

## Estructura

```
generator-evaluator-demo/
├── spec.yaml            ← el CRITERIO como dato. Lo dueña el humano. NO es código.
├── runner.py            ← oracle genérico y fijo: corre spec.yaml con Hypothesis
├── pytest.ini           ← hace que pytest colecte runner.py
├── CONTRACT.md          ← la intención en prosa (para humanos)
├── src/duration.py      ← lo implementa el GENERATOR (arranca como stub)
├── .claude/agents/
│   ├── generator.md     ← escribe src/. No toca spec.yaml ni runner.py
│   └── evaluator.md     ← agente aparte, sólo Read+Bash. Juzga, no arregla
├── requirements.txt     ← pytest, hypothesis, pyyaml
└── orchestrate.py       ← loop: generator → evaluator → oracle → feedback
```

## Reparto de roles (nadie se autoaprueba)

| Pieza | Quién | Garantía |
|---|---|---|
| **Criterio** | humano, en `spec.yaml` (dato) | pocas líneas, revisable de un vistazo |
| **Código** | `generator` (write en src/) | no toca spec ni runner |
| **Juez** | `evaluator` (Read+Bash, contexto fresco) | no edita código ni criterio; adversarial |
| **Árbitro duro** | `runner.py` + Hypothesis | determinístico; ancla el veredicto |

En `orchestrate.py`, la **terminación del loop la decide pytest**, no el LLM — el
veredicto está anclado a la verdad objetiva.

## Cómo correrlo

### Interactivo
```bash
pip install -r requirements.txt
claude
```
> Usá el generator para implementar src/ contra CONTRACT.md y spec.yaml. Después
> el evaluator para juzgar. Iterá hasta que `pytest -q` pase.

### Automatizado
```bash
pip install -r requirements.txt
npm i -g @anthropic-ai/claude-code && claude login   # si no lo tenés
python orchestrate.py
```

### Ver el oracle
```bash
python orchestrate.py --oracle      # arranca en ROJO: el stub no implementa nada
```

## Qué observar en clase

- `src/` es un stub → arranca en rojo.
- El humano sólo tocó `spec.yaml` (dato declarativo); nadie escribió test code.
- El **generator** que clava los `ejemplos` igual puede fallar la **propiedad**
  para inputs raros; Hypothesis le encuentra el contraejemplo mínimo.
- El **evaluator**, con contexto fresco y sin poder editar, corre el oracle e
  interpreta — y marca cosas que el spec no cubre. No puede aprobar lo que pytest
  reprueba.

## ¿Y si NO hay oracle objetivo?

Para "¿esta UI se entiende?" o "¿este resumen es fiel?" no hay fórmula. Ahí el
evaluator-LLM es el **único** juez posible (sin árbitro duro detrás), y sus dos
propiedades — contexto fresco + no puede tocar lo que juzga — son lo que lo hace
confiable. Lo reforzás con rúbrica que dueña el humano y spot-checks.

## Permisos: pedido vs imposible

Que el generator no toque `spec.yaml`/`runner.py` y que el evaluator no toque
`src/` se sostiene por sus system prompts + sus tools. Para enforcement **duro**
(imposible, no sólo pedido) se usan hooks `PreToolUse` o managed settings con
path deny-lists — Módulo 4 (Claude Code).
