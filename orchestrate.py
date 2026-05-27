#!/usr/bin/env python3
"""Loop de orquestación Generator / Evaluator (CI-style, automatizado).

    generator implementa src/
         │
         ▼
    evaluator (agente SEPARADO, contexto fresco, no toca código)
         │  corre el oracle como instrumento + review adversarial
         ▼
    ORACLE (runner.py + spec.yaml vía pytest)  ── árbitro duro, anclaje objetivo
         ├─ PASS → listo
         └─ FAIL → feedback del evaluator vuelve al generator → repetir

Tres piezas, complementarias:
  - generator: escribe src/ (write).
  - evaluator: agente aparte, sólo Read+Bash. No edita src/ (no arregla para
    aprobar) ni spec.yaml (no afloja el criterio). Su independencia viene de
    NO compartir el contexto del generator + NO poder tocar lo que juzga.
  - oracle: runner.py corre spec.yaml con Hypothesis. Determinístico. Es el
    instrumento del evaluator y el anclaje del veredicto (la terminación del loop
    no depende de lo que diga el LLM, sino de pytest).

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
    "Usá el subagente 'generator'. El evaluator reportó:\n\n{feedback}\n\n"
    "Arreglá src/duration.py. NO toques spec.yaml ni runner.py."
)

EVALUATOR_PROMPT = (
    "Usá el subagente 'evaluator'. Corré el oracle (`pytest -q`) sobre "
    "src/duration.py, interpretá los contraejemplos, hacé review adversarial de "
    "lo que el oracle no cubre, y devolvé el JSON de veredicto + feedback."
)


def run_oracle() -> tuple[bool, str]:
    """Anclaje objetivo: pytest. La terminación del loop depende de esto, no del LLM."""
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
    print("Generator -> Evaluator (agente aparte) -> Oracle")
    print("=" * 60)

    feedback = None
    for rnd in range(1, MAX_ROUNDS + 1):
        print(f"\n-- Ronda {rnd}/{MAX_ROUNDS} -----------------------------")

        print("[generator] implementando...")
        run_claude(GENERATOR_PROMPT if feedback is None
                   else GENERATOR_FIX_PROMPT.format(feedback=feedback))

        print("[evaluator] juzgando (contexto fresco, no toca código)...")
        feedback = run_claude(EVALUATOR_PROMPT)
        print(feedback)

        # anclaje objetivo: la decisión de terminar NO la toma el LLM, la toma pytest
        passed, _ = run_oracle()
        if passed:
            print(f"\nOracle en verde. Criterio cumplido en {rnd} ronda(s).")
            return

    print(f"\nNo se cumplió el criterio en {MAX_ROUNDS} rondas. "
          "Revisá spec.yaml o subí MAX_ROUNDS.")
    sys.exit(1)


if __name__ == "__main__":
    main()
