#!/usr/bin/env python3
"""Loop de orquestación (versión CI-style, automatizada).

    generator implementa src/  ──►  ORACLE (runner.py + spec.yaml vía pytest)
            ▲                                   │
            └────── contraejemplo si FAIL ◄─────┘

El oracle NO es un LLM: es `runner.py`, una pieza fija que lee `spec.yaml` (el
criterio, escrito por el humano como dato) y corre cientos de inputs con
Hypothesis. Determinístico → no se puede "convencer". El que escribe el código
(generator) no escribe ni toca el criterio ni el oracle.

Requisitos:
  - Claude Code:  npm i -g @anthropic-ai/claude-code ; claude login
  - deps:  pip install -r requirements.txt

Uso:
  python orchestrate.py            # loop completo
  python orchestrate.py --oracle   # solo correr el oracle (pytest) y salir
"""
import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
MAX_ROUNDS = 5

GENERATOR_PROMPT = (
    "Usá el subagente 'generator'. Leé CONTRACT.md y spec.yaml e implementá "
    "src/duration.py para cumplir el criterio (es property-based: tiene que valer "
    "para cualquier input válido). NO toques spec.yaml ni runner.py. "
    "No declares éxito: dejá el código y terminá."
)

GENERATOR_FIX_PROMPT = (
    "Usá el subagente 'generator'. El oracle falló:\n\n{issues}\n\n"
    "Arreglá src/duration.py para que pase. NO toques spec.yaml ni runner.py."
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
    ap.add_argument("--oracle", action="store_true", help="solo correr el oracle y salir")
    args = ap.parse_args()

    if args.oracle:
        passed, out = run_oracle()
        print(out)
        print("ORACLE:", "PASS" if passed else "FAIL")
        sys.exit(0 if passed else 1)

    print("=" * 60)
    print("Generator  ->  Oracle (spec.yaml + runner.py)")
    print("=" * 60)

    issues = None
    for rnd in range(1, MAX_ROUNDS + 1):
        print(f"\n-- Ronda {rnd}/{MAX_ROUNDS} -----------------------------")
        print("[generator] implementando...")
        run_claude(GENERATOR_PROMPT if issues is None
                   else GENERATOR_FIX_PROMPT.format(issues=issues))

        print("[oracle] pytest + hypothesis (lee spec.yaml)...")
        passed, out = run_oracle()
        tail = out.strip().splitlines()[-1] if out.strip() else "(sin salida)"
        print(tail)

        if passed:
            print(f"\nCriterio cumplido en {rnd} ronda(s). Loop terminado.")
            return

        # el contraejemplo de Hypothesis es el feedback para el generator
        issues = out[-1500:]

    print(f"\nNo se cumplió el criterio en {MAX_ROUNDS} rondas. "
          "Revisá spec.yaml o subí MAX_ROUNDS.")
    sys.exit(1)


if __name__ == "__main__":
    main()
