"""Oracle duro del contrato. NO lo edita ni el generator ni el evaluator.

Cada test mapea 1:1 a una fila de la tabla de criterios en CONTRACT.md.
"""
import sys
from pathlib import Path

import pytest

# permitir `import duration` sin instalar nada
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from duration import parse_duration  # noqa: E402


# --- happy path -------------------------------------------------------------

def test_01_h_and_m():
    assert parse_duration("1h30m") == 5400


def test_02_only_m():
    assert parse_duration("45m") == 2700


def test_03_only_s():
    assert parse_duration("90s") == 90


def test_04_only_h():
    assert parse_duration("2h") == 7200


def test_05_h_m_s():
    assert parse_duration("1h30m15s") == 5415


# --- normalización ----------------------------------------------------------

def test_06_ignores_spaces():
    assert parse_duration(" 1h 30m ") == 5400


def test_07_case_insensitive():
    assert parse_duration("1H30M") == 5400


# --- casos de error (los que un generator apurado suele saltarse) -----------

def test_08_empty_raises():
    with pytest.raises(ValueError):
        parse_duration("")


def test_09_garbage_raises():
    with pytest.raises(ValueError):
        parse_duration("abc")


def test_10_unit_without_number_raises():
    with pytest.raises(ValueError):
        parse_duration("h")
