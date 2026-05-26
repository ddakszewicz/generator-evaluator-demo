# Sprint Contract — parse_duration

> El contrato es la pieza más importante. Es la spec **verificable por máquina**
> contra la que el generator construye y el evaluator califica. Si esto es vago,
> todo lo demás falla.

## Objetivo

Implementar `parse_duration(text: str) -> int` en `src/duration.py`.
Convierte una duración escrita en texto a **segundos** (int).

## Criterios (cada uno tiene que ser verificable)

| # | Criterio | Verificado por |
|---|----------|----------------|
| 1 | `"1h30m"` devuelve `5400` | `parse_duration("1h30m") == 5400` |
| 2 | `"45m"` devuelve `2700` | `parse_duration("45m") == 2700` |
| 3 | `"90s"` devuelve `90` | `parse_duration("90s") == 90` |
| 4 | `"2h"` devuelve `7200` | `parse_duration("2h") == 7200` |
| 5 | Combinaciones: `"1h30m15s"` devuelve `5415` | `parse_duration("1h30m15s") == 5415` |
| 6 | Espacios se ignoran: `" 1h 30m "` devuelve `5400` | `parse_duration(" 1h 30m ") == 5400` |
| 7 | Case-insensitive: `"1H30M"` devuelve `5400` | `parse_duration("1H30M") == 5400` |
| 8 | String vacío levanta `ValueError` | `pytest.raises(ValueError)` |
| 9 | Texto inválido (`"abc"`) levanta `ValueError` | `pytest.raises(ValueError)` |
| 10 | Unidad sin número (`"h"`) levanta `ValueError` | `pytest.raises(ValueError)` |

## Oracle

`tests/test_duration.py` (pytest) es el árbitro objetivo. Verde = el contrato se cumple.
El generator NO puede tocar los tests. El evaluator los corre, no los edita.

## Definición de "terminado"

`pytest -q` pasa los 10 tests, sin warnings de import, sin código muerto.
