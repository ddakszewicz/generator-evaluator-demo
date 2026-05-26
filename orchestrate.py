#!/usr/bin/env python3
"""Loop de orquestación Generator / Evaluator (versión CI-style, automatizada).

Implementa el ciclo del Sprint Contract:

    plan ──► generator construye ──► ORACLE (pytest) ──► evaluator califica
                    ▲                                          │
                    └──────────── issues si FAIL ◄─────────────┘

El oracle duro es pytest: es objetivo y no se puede "convencer". El evaluator
agrega criterio cualitativo encima (lee el contrato, razona sobre evidencia).

Requisitos:
  - Claude Code instalado y logueado:  npm i -g @anthropic-ai/claude-code ; claude login
  - pytest:  pip install pytest

Uso:
  python orchestrate.py            # corre el loop completo
  python orchestrate.py --oracle   # solo corre pytest (ver estado actual)

Nota pedagógica: la forma MÁS simple de hacer esto es interactiva — abrís
`claude` en esta carpeta y le decís "usá el generator para cumplir CONTRACT.md,
después el evaluator para verificar; iterá hasta que pase". Este script es la
versión automatizada para mostrar el loop sin intervención humana.
"""
import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
MAX_ROUNDS = 5

GENERATOR_PROMPT = (
    "Usá el subagente 'generator'. Leé CONTRACT.md e implementá "
    "src/duration.py para cumplir TODOS los criterios, incluidos los casos de "
    "error. No toques tests/. No declares éxito: dejá el código y terminá."
)

GENERATOR_FIX_PROMPT = (
    "Usá el subagente 'generator'. El evaluator reportó fallas:\n\n{issues}\n\n"
    "Arreglá SOLO eso en src/duration.py y terminá sin declarar éxito."
)

EVALUATOR_PROMPT = (
    "Usá el subagente 'evaluator'. Verificá src/duration.py contra CONTRACT.md "
    "corriendo `pytest -q`. Devolvé el JSON de veredicto (overall PASS/FAIL + "
    "items con evidencia)."
)


def run_oracle() -> tuple[bool, str]:
    """Corre pytest. Devuelve (passed, output)."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=REPO, capture_output=True, text=True,
    )
    output = proc.stdout + proc.stderr
    return proc.returncode == 0, output


def run_claude(prompt: str) -> str:
    """Invoca Claude Code en modo headless. Devuelve el texto de salida.

    Usa `claude -p` (print/non-interactive). Para que pueda editar archivos sin
    frenar por permisos en un loop automático, conviene tener allow-lists en
    .claude/settings.json o correr con un permission-mode acorde.
    """
    try:
        proc = subprocess.run(
            ["claude", "-p", prompt],
            cwd=REPO, capture_output=True, text=True, timeout=600,
        )
    except FileNotFoundError:
        print("ERROR: no se encontró el comando `claude`.")
        print("Instalá Claude Code:  npm i -g @anthropic-ai/claude-code")
        print("Después:  claude login")
        sys.exit(1)
    return proc.stdout + proc.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oracle", action="store_true",
                    help="solo correr pytest y salir")
    args = ap.parse_args()

    if args.oracle:
        passed, out = run_oracle()
        print(out)
        print("ORACLE:", "PASS ✅" if passed else "FAIL ❌")
        sys.exit(0 if passed else 1)

    print("=" * 60)
    print("LOOP Generator / Evaluator  ·  Sprint Contract")
    print("=" * 60)

    issues = None
    for rnd in range(1, MAX_ROUNDS + 1):
        print(f"\n── Ronda {rnd}/{MAX_ROUNDS} ─────────────────────────────")

        # 1. Generator construye (o arregla)
        print("[generator] construyendo...")
        if issues is None:
            run_claude(GENERATOR_PROMPT)
        else:
            run_claude(GENERATOR_FIX_PROMPT.format(issues=issues))

        # 2. Oracle duro (pytest) — el árbitro objetivo
        print("[oracle] pytest...")
        passed, out = run_oracle()
        print(out.strip().splitlines()[-1] if out.strip() else "(sin salida)")

        if passed:
            # 3. Evaluator confirma (criterio cualitativo encima del oracle verde)
            print("[evaluator] verificando contra el contrato...")
            verdict = run_claude(EVALUATOR_PROMPT)
            print(verdict)
            print(f"\n✅ Contrato cumplido en {rnd} ronda(s). Loop terminado.")
            return

        # 4. Falla → el evaluator detalla qué falta, se lo pasamos al generator
        print("[evaluator] juntando issues para el generator...")
        issues = run_claude(EVALUATOR_PROMPT)

    print(f"\n❌ No se cumplió el contrato en {MAX_ROUNDS} rondas. "
          "Revisá el contrato o el evaluator (¿es lo bastante adversarial?).")
    sys.exit(1)


if __name__ == "__main__":
    main()
