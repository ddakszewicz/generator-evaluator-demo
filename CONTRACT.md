# Contrato — parse_duration

> La intención en prosa (para humanos). El criterio **ejecutable** vive en
> `spec.yaml` (dato declarativo) y lo corre `runner.py` (oracle fijo).
> Nadie escribe tests a mano por tarea; nadie se autoaprueba.

## Objetivo

`parse_duration(text: str) -> int` en `src/duration.py`: convierte una duración
en texto (`"1h30m"`) a **segundos** (int).

## Formato válido

- Unidades: `h` (horas), `m` (minutos), `s` (segundos).
- Una o más unidades en orden `h`, `m`, `s`, cada una precedida por un entero no
  negativo. Ej: `"2h"`, `"45m"`, `"1h30m15s"`.
- Insensible a mayúsculas y a espacios.

## Qué se verifica (definido como dato en `spec.yaml`)

- **Correctitud**: para cualquier `h,m,s ≥ 0`, `parse("{h}h{m}m{s}s")` da
  `h*3600 + m*60 + s` (verdad de referencia, no mira la implementación).
- **Invariantes**: insensible a mayúsculas y a espacios.
- **Errores**: vacío, texto sin patrón válido, unidad sin número, número sin
  unidad → `ValueError`.

## Definición de "terminado"

`pytest -q` en verde. Hypothesis corre cientos de inputs por propiedad.
El generator implementa `src/`; no toca `spec.yaml` ni `runner.py`.
