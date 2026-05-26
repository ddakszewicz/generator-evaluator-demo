# Generator / Oracle demo

Ejemplo mínimo del patrón **Generator / Evaluator** llevado a su forma más
robusta: cuando hay una verdad objetiva, el "evaluator" no es un LLM — es un
**oracle determinístico**.

De la charla "Agentes SWE de largo horizonte":

> **Separá el que construye del que juzga.** Y, si podés, que el que juzga sea
> objetivo (un oracle), no otro LLM que se pueda autoaprobar.

## La idea central: el criterio es DATO, no código

El recorrido de decisiones (y por qué este diseño):

1. **¿Tests a mano?** No escala y sesga (escribís los mismos happy paths).
2. **¿Que los escriba el generator?** Se autoaprueba (escribe código que pasa sus
   propios tests).
3. **¿Que los escriba un evaluator LLM?** Lo mismo, movido un casillero: puede
   escribir tests flojos o aflojarlos para que den verde.
4. **¿Tests escritos a mano por el humano?** Sigue siendo escribir *código*, que
   es justo lo que queremos delegar.
5. **Solución:** el humano escribe el **criterio como dato** (`spec.yaml`), y una
   pieza fija y genérica (`runner.py`) lo ejecuta. El humano escribe el *qué*
   (declarativo, pocas líneas), nunca el *cómo*.

## Estructura

```
generator-evaluator-demo/
├── spec.yaml            ← el CRITERIO como dato. Lo dueña el humano. NO es código.
├── runner.py            ← oracle genérico y fijo: lee spec.yaml, corre con Hypothesis
├── pytest.ini           ← hace que pytest colecte runner.py
├── CONTRACT.md          ← la intención en prosa (para humanos)
├── src/duration.py      ← lo implementa el GENERATOR (arranca como stub)
├── .claude/agents/
│   └── generator.md     ← implementa src/. No toca spec.yaml ni runner.py
├── requirements.txt     ← pytest, hypothesis, pyyaml
└── orchestrate.py       ← loop automatizado: generator → oracle → feedback
```

## Cómo se reparten los roles (nadie se autoaprueba)

| Rol | Quién | Por qué no es gameable |
|---|---|---|
| **Criterio** | el humano, en `spec.yaml` | son pocas líneas de dato, las revisás de un vistazo |
| **Oracle** | `runner.py` (fijo) + Hypothesis | determinístico, corre cientos de inputs, no es un LLM |
| **Código** | el `generator` | no puede tocar `spec.yaml` ni `runner.py` |

La correctitud (P central) se chequea contra una **fórmula de referencia**
(`h*3600+m*60+s`) que sale del spec — no de mirar la implementación. Eso es un
**oracle diferencial**.

## Cómo correrlo

### Interactivo (lo más simple)
```bash
pip install -r requirements.txt
claude
```
> Usá el generator para implementar src/duration.py contra CONTRACT.md y
> spec.yaml. Iterá hasta que `pytest -q` pase.

### Automatizado
```bash
pip install -r requirements.txt
npm i -g @anthropic-ai/claude-code && claude login   # si no lo tenés
python orchestrate.py
```

### Ver el estado del oracle
```bash
python orchestrate.py --oracle      # arranca en ROJO: el stub no implementa nada
```

## Qué observar en clase

- `src/` es un stub → el oracle arranca en **rojo**.
- El humano sólo tocó `spec.yaml` (dato). Nadie escribió test code por tarea.
- El **generator** que clava los `ejemplos` igual puede fallar la **propiedad**
  para inputs raros (números enormes, combinaciones que no probó). Hypothesis se
  los encuentra y devuelve el **contraejemplo mínimo** — feedback objetivo.
- El veredicto final no depende de la opinión de ningún LLM: es pytest.

## ¿Y si NO hay oracle objetivo?

Para "¿este diseño es coherente?", "¿esta UI se entiende?" no hay fórmula. Ahí sí
necesitás un **evaluator LLM** — y aceptás que es más débil. Lo mitigás: separado
del generator, prompt adversarial, rúbrica que dueña el humano, y spot-checks.
Cuando existe un oracle duro (tests, compilador, types, una API real), preferilo
siempre: es el caso del compilador C donde el oracle era GCC ("compila Linux o no").

## Nota sobre permisos

Que el generator "no toque spec.yaml ni runner.py" lo sostiene su system prompt +
correr en su propio context. Para enforcement **duro** (imposible, no sólo
pedido) se usan hooks `PreToolUse` o managed settings con path deny-lists — eso
se ve en el Módulo 4 (Claude Code).
