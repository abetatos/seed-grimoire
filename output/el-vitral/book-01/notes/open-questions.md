# Open questions (rolling)

> Threads discussed in chat that did NOT get resolved. Surface these at
> the start of the next session. The agent appends as discussions happen
> and marks items resolved (strike-through) when they close.

## Pendientes

- (2026-06-25, ch 1) **Desincronía nombres bundle ↔ canon.** `build_context.py` emite **Tobías / Vela / Bras** (tutor / cazador / ideólogo verde) pero `book-01/canon/characters.md` dice **Mauro / Cándido / Tilo**. Resolver cuál es el bueno y sincronizar **antes del cap 4** (entra el tutor). No afecta al cap 1.
  - (2026-06-29, ch 1) **Evidencia:** el bundle de contexto del cap 1 (`_context-ch01.md`) salió **consistente con Mauro/Cándido/Tilo** — no se observó ninguna fuga de Tobías/Vela/Bras esta sesión. Aún así, **verificar build_context** (puede venir de un mapping de nombres por defecto / placeholder en otra ruta) antes del cap 4.
  - (2026-07-01, ch 1) **Reconfirmado:** el bundle del cap 1 volvió a salir limpio (Mauro/Cándido/Tilo). Sigue pendiente **verificar build_context antes del cap 4**.
  - (2026-07-01, ch 2) **Reconfirmado (cap 2):** el bundle `_context-ch02.md` también salió limpio (Mauro/Cándido/Tilo). **Ya solo faltan 2 capítulos para el 4** (entra Mauro como tutor con nombre en escena): verificar/limpiar el mapping en `build_context.py` **esta sesión o la próxima**, antes de escribir el cap 4.

- (2026-07-01, ch 1) **Rimar las siembras Mauro del cap 2/4 con los pre-toques del cap 1.** El barrido inverso encontró en el cap 1 (decisión del autor: dejar como foreshadow, no reprogramar) dos imágenes que se adelantan a su siembra: las **manos manchadas** de Mauro (`las-manos-del-lector`, siembra formal cap 2) y la **mirada que busca/mide** envuelta en ternura (`el-tutor-tiene-agenda`, siembra formal cap 4). Al sembrarlas en 2/4, **rimar** con lo ya visto (Bruno ya se fijó en las manos; la mirada ya "buscaba"), no re-presentarlas como nuevas.
  - (2026-07-01, ch 2) **Mitad del cap 2 HECHA:** `las-manos-del-lector` se plantó rimando con el cap 1 —no se re-presentaron las manos manchadas como nuevas, sino que se añadió la **capa nueva** (la soltura ante el cristal del rito). **Queda abierto** el cap 4: al sembrar formalmente `el-tutor-tiene-agenda` (la mirada que **mide**), rimar con la mirada que en el cap 1 "ya buscaba", sin re-presentarla como nueva y **sin hacerla legible** (la lectura como medición es del cap 13).

- (2026-07-01, ch 1) **Coherencia del salvamento (magia).** El primer uso involuntario salva a Sela **por contacto** (muñeca) pero **no la agrisa**: Bruno solo roza el fondo ambiental difuso y no controla el caudal. Mantener coherente cuando aflore en escena la ley "el contacto toma de quien se le pone encima" (Sela fue tocada y no quedó gris) — no es contradicción ahora (ninguna ley está en la página), pero vigilar en el drenaje del clímax.

## Resueltos (archivo)

- ~~(2026-06-25) **`critique-plan` saltado.**~~ **RESUELTO 2026-07-01:** corrido en limpio (subagente book-critic) → **PASS** (0 MUST, 2 SHOULD). Se aplicó el fix de consistencia POV (setup.md:194 Saúl→Olmo); las 2 verdades-de-más se difieren a II-III por decisión del autor. Además: reset del estado de capítulos (2 caps escritos contra un plan previo) para reescribir desde el cap 1 contra el plan finalizado.
