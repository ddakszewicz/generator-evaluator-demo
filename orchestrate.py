#!/usr/bin/env python3
"""Loop de orquestación Generator / Evaluator (versión CI-style, automatizada).

Flujo:

    1. evaluator escribe los tests (property-based) desde CONTRACT.md   ← una vez
    2. generator implementa src/
    3. ORACLE: pytest + hypothesis
       ├─ PASS → listo
       └─ FAIL → el evaluator junta el contraejemplo, vuelve al paso 2

El oracle (pytest + Hypothesis) es objetivo: corre cientos de inputs y no se
puede "convencer". Quien escribe los tests (evaluator) NO es quien escribe el
código (generator) — esa separación evita el autoaprobado.

Requisitos:
  - Claude Code:  npm i -g @anthropic-ai/claude-code ; claude login
  - deps:  pip install -r requirements.txt

Uso:
  python orchestrate.py            # loop completo
  python orchestrate.py --oracle   # solo correr pytest (ver estado actual)

Nota: la forma MÁS simple es interactiva — abrís `claude` en esta carpeta y le
decís el flujo. Este script lo automatiza para mostrarlo sin intervención.
"""
import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
MAX_ROUNDS = 5

EVAL_WRITE_TESTS = (
    "Usá el subagente 'evaluator'. Leé CONTRACT.md y escribí "
    "tests/test_duration.py con property-based testing (Hypothesis), una "
    "propiedad/invariante por test. NO toques src/. No implementes nada, solo "
    "los tests."
)

GENERATOR_PROMPT = (
    "Usá el subagente 'generator'. Leé CONTRACT.md e implementá "
    "src/duration.py para cumplir todas las propiedades. NO toques tests/. "
    "No declares éxito: dejá el código y terminá."
)

GENERATOR_FIX_PROMPT = (
    "Usá el subagente 'generator'. El oracle falló con este contraejemplo / "
    "salida:\n\n{issues}\n\nArreglá SOLO eso en src/duration.py y terminá."
)

EVAL_VERDICT = (
    "Usá el subagente 'evaluator'. Corré `pytest -q` y devolvé el JSON de "
    "veredicto (overall + properties + counterexamples)."
)


def run_oracle() -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=REPO, capture_output=True, text=True,
    )
    return proc.returncode == 0, proc.stdout + proc.stderr


def run_claude(prompt: str) -> str:
    try:
        proc = subprocess.run(
            ["claude", "-p", prompt],
            cwd=REPO, capture_output=True, text=True, timeout=600,
        )
    except FileNotFoundError:
        print("ERROR: no se encontró `claude`. Instalá: npm i -g @anthropic-ai/claude-code")
        sys.exit(1)
    return proc.stdout + proc.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oracle", action="store_true", help="solo correr pytest y salir")
    args = ap.parse_args()

    if args.oracle:
        passed, out = run_oracle()
        print(out)
        print("ORACLE:", "PASS" if passed else "FAIL")
        sys.exit(0 if passed else 1)

    print("=" * 60)
    print("Generator / Evaluator  ·  criterios -> tests -> código")
    print("=" * 60)

    # Paso 1: el evaluator escribe los tests desde el contrato (una sola vez)
    print("\n[evaluator] escribiendo tests property-based desde CONTRACT.md...")
    run_claude(EVAL_WRITE_TESTS)

    # Pasos 2-4: loop generator -> oracle -> feedback
    issues = None
    for rnd in range(1, MAX_ROUNDS + 1):
        print(f"\n-- Ronda {rnd}/{MAX_ROUNDS} -----------------------------")
        print("[generator] implementando...")
        run_claude(GENERATOR_PROMPT if issues is None
                   else GENERATOR_FIX_PROMPT.format(issues=issues))

        print("[oracle] pytest + hypothesis...")
        passed, out = run_oracle()
        print(out.strip().splitlines()[-1] if out.strip() else "(sin salida)")

        if passed:
            print("[evaluator] veredicto final...")
            print(run_claude(EVAL_VERDICT))
            print(f"\nContrato cumplido en {rnd} ronda(s). Loop terminado.")
            return

        # el evaluator resume el contraejemplo para el generator
        issues = run_claude(EVAL_VERDICT)

    print(f"\nNo se cumplió el contrato en {MAX_ROUNDS} rondas. "
          "Revisá el contrato o si el evaluator es lo bastante adversarial.")
    sys.exit(1)


if __name__ == "__main__":
    main()
