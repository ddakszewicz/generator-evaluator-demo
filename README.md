# Generator / Evaluator demo

Ejemplo mínimo del patrón **Generator / Evaluator** con Claude Code.
La idea (de la charla "Agentes SWE de largo horizonte"):

> **Separá el agente que construye del agente que juzga.**
> Un agente que se corrige a sí mismo arrastra dos sesgos: ansiedad de contexto
> (cierra antes de tiempo) y sesgo de autoevaluación (aprueba su propio trabajo
> mediocre). Dos roles separados, con permisos asimétricos, lo destraban.

## La idea central: escribís criterios, no casos

El humano **no escribe los tests a mano** (no escala y sesga). Escribe el
**contrato**: qué propiedades tiene que cumplir el código. El **evaluator**
traduce esas propiedades a tests con **property-based testing** (Hypothesis), que
genera cientos de casos automáticamente. El **generator** escribe el código.
Nadie se autoaprueba: el que construye no es el que escribe los tests.

## La tarea (chiquita a propósito)

Implementar `parse_duration("1h30m") -> 5400` en `src/duration.py`.
El foco no es la tarea — es el **workflow**.

## Estructura

```
generator-evaluator-demo/
├── CONTRACT.md              ← el contrato: propiedades P1-P6 + invariantes E1-E4
├── src/duration.py          ← lo que implementa el GENERATOR (arranca como stub)
├── tests/                   ← VACÍO: lo llena el EVALUATOR (property-based)
├── .claude/agents/
│   ├── generator.md         ← construye src/. tools: Read/Write/Edit/Bash
│   └── evaluator.md         ← escribe tests/ y juzga. No toca src/
├── requirements.txt         ← pytest + hypothesis
└── orchestrate.py           ← el loop automatizado (CI-style)
```

## Los tres roles (nadie se autoaprueba)

1. **Humano** → escribe `CONTRACT.md` como propiedades (el "qué").
2. **Evaluator** → traduce las propiedades a `tests/test_duration.py` con
   Hypothesis. Escribe SOLO en `tests/`, nunca en `src/`.
3. **Generator** → implementa `src/duration.py`. Nunca toca `tests/`.

El oracle final es **objetivo**: pytest + Hypothesis corren cientos de inputs y,
para P1, comparan contra una fórmula de referencia (`h*3600+m*60+s`) — no contra
la implementación.

## Cómo correrlo

### Opción A — interactivo (la más simple)
```bash
cd generator-evaluator-demo
pip install -r requirements.txt
claude
```
Y en el chat:
> Usá el evaluator para escribir los tests property-based desde CONTRACT.md.
> Después el generator para implementar src/. Iterá hasta que `pytest -q` pase.

### Opción B — automatizado (mostrar el loop sin humano)
```bash
pip install -r requirements.txt
npm i -g @anthropic-ai/claude-code && claude login   # si no lo tenés
python orchestrate.py
```

## Qué observar en clase

- `tests/` arranca **vacío** y `src/` es un stub → el sistema arranca en rojo.
- El **evaluator** escribe property-based tests. Hypothesis no prueba 3 casos:
  prueba cientos, y cuando encuentra un input que rompe una propiedad, te da el
  **contraejemplo mínimo** (ej: "parse('h') devolvió 0, esperaba ValueError").
- El **generator** que clava los ejemplos del contrato igual puede fallar P1 para
  inputs raros que no probó. Ahí se ve la diferencia entre "pasa mis 10 casos" y
  "cumple la propiedad".
- El contraejemplo de Hypothesis es feedback objetivo y accionable.

## Qué tipo de tests debería producir el evaluator (referencia para el docente)

```python
from hypothesis import given, strategies as st
nn = st.integers(min_value=0, max_value=10**6)

@given(h=nn, m=nn, s=nn)                     # P1: oracle diferencial
def test_p1(h, m, s):
    assert parse_duration(f"{h}h{m}m{s}s") == h*3600 + m*60 + s

@given(h=nn, m=nn, s=nn)                     # P3: case-insensitive
def test_p3(h, m, s):
    t = f"{h}h{m}m{s}s"
    assert parse_duration(t) == parse_duration(t.upper())

@pytest.mark.parametrize("bad", ["", "   ", "abc", "h", "ms", "30"])  # E1-E4
def test_errors(bad):
    with pytest.raises(ValueError):
        parse_duration(bad)
```

## Guardrails

- `MAX_ROUNDS = 5` en `orchestrate.py` — corta el loop (no factura infinita).
- El generator no escribe tests; el evaluator no escribe src. La separación es lo
  que evita el autoaprobado.
- pytest + Hypothesis son determinísticos como veredicto final — no dependen de
  la opinión del LLM. Para enforcement **duro** de los permisos (que sea
  imposible tocar la carpeta ajena, no sólo pedido) se usan hooks `PreToolUse` o
  managed settings — eso se ve en el Módulo 4 (Claude Code).
