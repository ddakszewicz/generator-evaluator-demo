"""Runner genérico — convierte spec.yaml en checks property-based.

NO se edita por tarea. Es el harness fijo, task-agnostic, que hace de **oracle**:
lee el spec (dato, escrito por el humano), genera cientos de inputs con
Hypothesis y verifica. Determinístico — no es un LLM, no se puede "convencer".

Se corre con pytest (ver pytest.ini, que lo colecta) o directo:  pytest -q
"""
import builtins
import importlib
import sys
from pathlib import Path

import pytest
import yaml
from hypothesis import given, strategies as st

ROOT = Path(__file__).resolve().parent
SPEC = yaml.safe_load((ROOT / "spec.yaml").read_text(encoding="utf-8"))

# importar la función bajo prueba (src/ al path)
sys.path.insert(0, str(ROOT / "src"))
_mod_name, _fn_name = SPEC["target"].rsplit(".", 1)
target = getattr(importlib.import_module(_mod_name), _fn_name)


def _strategy(p):
    if p["type"] == "int":
        return st.integers(min_value=p.get("min", 0), max_value=p.get("max", 10**6))
    raise ValueError(f"tipo de param no soportado: {p['type']}")


_STRATS = {name: _strategy(spec) for name, spec in SPEC.get("params", {}).items()}


def _expected(params):
    # eval acotado: sin builtins, solo aritmética sobre los params del spec
    return eval(SPEC["expected"], {"__builtins__": {}}, dict(params))


def _spaced(text):
    # inserta un espacio antes de cada letra (unidad) + extremos
    inner = text[0] + "".join((" " + c if c.isalpha() else c) for c in text[1:])
    return f"  {inner}  "


# --- Propiedad central: correctitud composicional (oracle diferencial) -------
@given(st.data())
def test_correctness(data):
    params = {name: data.draw(s) for name, s in _STRATS.items()}
    inp = SPEC["build"].format(**params)
    assert target(inp) == _expected(params)


# --- Invariantes -------------------------------------------------------------
@given(st.data())
def test_invariants(data):
    invs = SPEC.get("invariantes", [])
    if not invs:
        return
    params = {name: data.draw(s) for name, s in _STRATS.items()}
    inp = SPEC["build"].format(**params)
    base = target(inp)
    for inv in invs:
        if inv == "case_insensitive":
            assert target(inp.upper()) == base
            assert target(inp.lower()) == base
        elif inv == "whitespace_insensitive":
            assert target(_spaced(inp)) == base
        else:
            raise ValueError(f"invariante desconocida en spec: {inv}")


# --- Invariantes de error ----------------------------------------------------
@pytest.mark.parametrize("case", SPEC.get("errores", []),
                         ids=lambda c: f"raises::{c['in']!r}")
def test_errors(case):
    exc = getattr(builtins, case["raises"])
    with pytest.raises(exc):
        target(case["in"])


# --- Ejemplos (sanity / doc) -------------------------------------------------
@pytest.mark.parametrize("case", SPEC.get("ejemplos", []),
                         ids=lambda c: f"ej::{c['in']!r}")
def test_examples(case):
    assert target(case["in"]) == case["out"]
