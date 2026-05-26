# v2 — criterios, no casos

La crítica a la v1 era justa: **escribir casos de test a mano no escala** y
sesga (escribís los mismos happy paths que pensó el dev). Pero la respuesta no
es "que los escriba el generator" — eso trae el auto-aprobado.

La respuesta es: **escribís criterios/propiedades, no casos**, y **quien escribe
los tests no es quien escribe el código**.

## Qué cambia respecto de v1

| | v1 | v2 (esta) |
|---|---|---|
| Quién escribe los tests | el humano, a mano | el **evaluator** (agente separado) |
| Qué escribís a mano | 10 casos concretos | propiedades / invariantes (el "qué") |
| Cómo se generan los casos | uno por uno | **Hypothesis** genera cientos, con edge cases |
| Oracle | igualdad caso a caso | **diferencial**: fórmula de referencia `h*3600+m*60+s` |
| Garantía | el dev pensó esos 10 | vale para *cualquier* input válido |

## Los tres roles (nadie se autoaprueba)

1. **Humano** → escribe `CONTRACT.md` como propiedades (P1-P6) e invariantes (E1-E4).
2. **Evaluator** → traduce esas propiedades a `tests/test_duration.py` con
   Hypothesis. Escribe SOLO en `tests/`, nunca en `src/`.
3. **Generator** → implementa `src/duration.py`. Nunca toca `tests/`.

`tests/` arranca **vacío**: el evaluator lo llena en vivo.

## Cómo correrlo

```bash
cd v2-criterios-no-casos
pip install -r requirements.txt        # pytest + hypothesis
claude
```
En el chat:
> Usá el evaluator para escribir los tests property-based desde CONTRACT.md.
> Después el generator para implementar src/. Iterá hasta que `pytest -q` pase.

## Qué observar en clase

- El **evaluator** escribe property-based tests. Hypothesis no prueba 3 casos:
  prueba cientos, y cuando encuentra un input que rompe una propiedad, te da el
  **contraejemplo mínimo** ("parse('h') devolvió 0, esperaba ValueError").
- El **generator** que clavó los ejemplos del contrato igual puede fallar P1
  para inputs raros (números enormes, combinaciones que no probó). Ahí se ve la
  diferencia entre "pasa mis 10 casos" y "cumple la propiedad".
- El contraejemplo de Hypothesis es feedback objetivo y accionable — mucho mejor
  que "che, no anda".

## Referencia — qué tipo de tests debería producir el evaluator

(esto es para que el docente sepa qué esperar; en el repo `tests/` está vacío)

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

@given(h=nn, m=nn)                           # P4: espacios irrelevantes
def test_p4(h, m):
    assert parse_duration(f"{h}h{m}m") == parse_duration(f"  {h}h  {m}m ")

@pytest.mark.parametrize("bad", ["", "   ", "abc", "h", "ms", "30"])  # E1-E4
def test_errors(bad):
    with pytest.raises(ValueError):
        parse_duration(bad)

@given(txt=st.text(alphabet="qwerty", min_size=1, max_size=8))        # E2 random
def test_e2(txt):
    with pytest.raises(ValueError):
        parse_duration(txt)
```

## Nota sobre permisos

En este demo la separación de roles (generator no toca tests/, evaluator no toca
src/) se sostiene por el system prompt de cada subagente + el hecho de que corren
en context windows separados. Para enforcement **duro** (que sea imposible, no
sólo pedido), se usan hooks `PreToolUse` o managed settings con path deny-lists
— eso lo vemos en el Módulo 4 (Claude Code).
