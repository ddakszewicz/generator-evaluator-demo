# Sprint Contract v2 — parse_duration (por propiedades, no por casos)

> Diferencia clave con v1: acá **NO escribimos casos de test a mano**.
> Escribimos **propiedades** e **invariantes** — el "qué" — y el evaluator las
> traduce a tests con property-based testing (Hypothesis), que genera cientos de
> casos automáticamente, incluyendo edge cases que nosotros no pensamos.
>
> El humano define la intención. El evaluator escribe los tests. El generator
> escribe el código. Tres roles, nadie se autoaprueba.

## Objetivo

`parse_duration(text: str) -> int` en `src/duration.py`: convierte una duración
en texto (`"1h30m"`) a **segundos** (int).

## Formato de entrada (válido)

- Unidades: `h` (horas), `m` (minutos), `s` (segundos).
- Forma canónica: una o más unidades en orden `h`, `m`, `s`, cada una precedida
  por un entero no negativo. Ej: `"2h"`, `"45m"`, `"1h30m15s"`.
- Insensible a mayúsculas y a espacios.

## Propiedades (el evaluator las convierte a tests con Hypothesis)

| # | Propiedad | Forma property-based |
|---|-----------|----------------------|
| P1 | **Correctitud composicional** | para todo `h,m,s ≥ 0`: `parse(f"{h}h{m}m{s}s") == h*3600 + m*60 + s` |
| P2 | **Subconjuntos válidos** | sólo-h, sólo-m, sólo-s, y pares (h+m, m+s, h+s) cumplen P1 con los faltantes en 0 |
| P3 | **Case-insensitive** | `parse(t) == parse(t.upper()) == parse(t.lower())` |
| P4 | **Espacios irrelevantes** | insertar espacios arbitrarios entre tokens no cambia el resultado |
| P5 | **Monotonía** | si `total_segundos(a) < total_segundos(b)` entonces `parse(a) < parse(b)` |
| P6 | **No-negatividad** | el resultado siempre es `int >= 0` |

## Invariantes de error (también property-based donde aplica)

| # | Invariante | Forma |
|---|-----------|-------|
| E1 | String vacío o sólo-espacios → `ValueError` | `parse("")`, `parse("   ")` |
| E2 | Cualquier texto sin un patrón `\d+[hms]` válido → `ValueError` | strings de letras random |
| E3 | Unidad sin número (`"h"`, `"ms"`) → `ValueError` | |
| E4 | Número sin unidad (`"30"`) → `ValueError` | |

## Oracle

- **Property-based** (Hypothesis): P1-P6 corridos contra cientos de inputs generados.
- **Diferencial**: P1 usa una fórmula de referencia independiente (`h*3600+m*60+s`)
  como verdad — el test no depende de mirar la implementación.

## Definición de "terminado"

`pytest -q` verde, con Hypothesis sin contraejemplos (`--hypothesis-seed=random`).
El generator no toca `tests/`. El evaluator no toca `src/`.
