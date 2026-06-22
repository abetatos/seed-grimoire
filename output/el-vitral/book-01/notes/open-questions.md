# Open questions (rolling)

> Threads discussed in chat that did NOT get resolved. Surface these at
> the start of the next session. The agent appends as discussions happen
> and marks items resolved (strike-through) when they close.

## Pendientes

- (2026-06-22, ch 1) **TODOs menores del plan, no gating:** identidad
  concreta y causa de muerte del progenitor Tobías; identidad de la madre
  Blanca de Bruno (probable revelación Libro II). *(El color del mentor →
  resuelto azul; el vínculo del ordeñado de Yedra → resuelto, ver abajo.)*
- (2026-06-22, ch 3) **Plausibilidad del complementario con aura verde modesta
  (no gating).** En ch 3 la cancelación se rinde a **radio corto (un palmo)** y
  con el magenta **forzando al máximo**. Mantener esa lógica en el payoff (ch 22)
  para que sea consistente: Yedra no necesita aura grande, necesita proximidad +
  contrafase. Confirmar al escribir ch 10/14 (echos) y ch 22 (pago).
- (2026-06-22) **Marcadores EXPAND visibles** en los capítulos: se quedan por
  ahora (estándar del repo); limpieza diferida cuando el flujo esté afianzado.
- (2026-06-22, ch 2) **Desfase outline ↔ seeds.md (no gating).** El beat sheet
  del ch 2 lista `borradores-del-mentor` (plant) y `recuerdo-que-se-apaga`
  (echo) como semillas del ch 2, pero `seeds.md` las programa en ch 5 (plant)
  y ch 13 (echo). Se resolvió tratándolas como **pre-toques suaves** en ch 2
  (la libreta del forastero; la canción que pierde un poco más) sin avanzar su
  Status. Decidir si conviene alinear el outline con seeds.md o registrar
  oficialmente estos pre-toques. Revisar también otros capítulos por si el
  outline cita semillas fuera de su calendario.

## Resueltas

- ~~(2026-06-22, ch 1↔2) Desfase del timing de la recaudación.~~ RESUELTO:
  se mantienen los doce días del pregón del ch 1; el outline del ch 2 abre
  ~12 días después (día de recaudación + Lectura) con pase de tiempo
  controlado.
- ~~(2026-06-22, ch 2) Color del mentor reformista.~~ RESUELTO: **azul**
  (paño azul, frío "de agua de pozo"), promovido a `canon/characters.md`.
- ~~(2026-06-22, ch 2) Escalera de erosión de memoria.~~ RESUELTO: ch 1 = el
  centro de la canción tarareada; ch 2 = la canción pierde **un poco más**
  (extiende el plant del ch 1, NO gasta contenido reservado); ch 13 = la voz
  del padre; ch 25 = su rostro. El ch 2 evita pre-empt del midpoint.
- ~~(2026-06-22, ch 2) Color del alma nueva de los Sales.~~ RESUELTO: **verde**
  (corto), no amarillo — amarillo es alta casa y rompía la pirámide.
- ~~(2026-06-22, ch 3) Vínculo del ordeñado de Yedra.~~ RESUELTO: **hermano
  menor, Tello (~15)**, *desaparecido* (no volvió) en la recaudación de otoño;
  contraste con el **Cosme** que volvió gris. Promovido a `canon/characters.md`.
- ~~(2026-06-22, ch 3) Rango del "guardia magenta" del seed.~~ RESUELTO:
  **magenta menor de casa que se apaga**, cobrador de la sisa de feria (no un
  simple guardia — magenta es Corona). Da coste térmico al forzar + motivo
  (probar que su color aún pesa). Promovido a canon.
- ~~(2026-06-22, ch 3) Desfase outline ↔ seeds.md en ch 3.~~ SIN DESFASE: el
  beat sheet del ch 3 (plant `complementario-verde-magenta`, echo `los-huecos`)
  coincide con `seeds.md` (plant ch 3 / echo ch 3). Avanzados sin incidencia.

## Avisos de herramienta

- (2026-06-22) **`mark_seed.py` corrompe `seeds.md`:** al avanzar estados,
  reescribe el fichero **truncando cada campo multilínea a su primera línea**
  (Detail / Real meaning / How to plant / How to pay off). Tras correrlo hubo
  que restaurar `seeds.md` a mano. Hasta arreglar el script, avanzar estados
  con Edit manual sobre el campo `Status:`, no con el script.
- (2026-06-22, ch 2) Al avanzar estados en `seeds.md` con Edit, un linter/hook
  los **revirtió una vez** (volvieron a `planted`/`planned`). Hubo que
  reaplicar. Verificar el campo `Status:` con grep DESPUÉS de editar seeds.md.
