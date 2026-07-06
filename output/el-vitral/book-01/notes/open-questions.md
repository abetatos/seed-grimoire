# Open questions (rolling)

> Threads discussed in chat that did NOT get resolved. Surface these at
> the start of the next session. The agent appends as discussions happen
> and marks items resolved (strike-through) when they close.

## Pendientes

- (2026-07-06) **⚠ CUARTO ARRANQUE — reset a 0 capítulos para un run limpio con la forma
  de trabajar nueva.** Borrados el cap 1 (bloqueado esa misma mañana) y el cap 2 (recién
  escrito, a medio pipeline), sus summaries, critiques, continuity y `decisions-chNN`.
  Revertidos al baseline los ficheros que el lock-in tocó (`seeds.md` → 17 planned sin
  Realized; `canon/characters.md`, `canon/world.md`, `book-summary.md`). `shadow.md`
  reseteado quirúrgicamente: **las 10 verdades a `hidden` y todos los `Surfaced:` vacíos**
  — esto limpia también los fantasmas ch2/ch3 heredados del reset anterior (el pendiente
  de tooling sobre `lint_book` sigue abierto abajo). Se conservan plan (outline/arcs/
  seeds/shadow), estilo windowpane, `voice-exemplars.md` (vacío), las lecciones de
  `voice.md` y las decisiones durables de `decisions.md`. Novedad de contrato desde este
  arranque: **`write-chapter` escribe a presupuesto estructural (la longitud no se cuenta)**
  y `expand-chapter` solo repite pasada si la crítica nombra un need test sin insert —
  el pendiente del 2026-07-06 sobre "el borrador sale corto" queda superseded por este
  contrato. **Toda nota de estado de capítulo fechada antes de esta línea es STALE.**

- (2026-07-05) **⚠ TERCER ARRANQUE — caps 1-2 borrados otra vez, ahora contra el estilo nuevo.**
  El autor viró el libro a la escuela hard-magic con frase **windowpane** (ver `style.md`):
  prosa transparente, ley cero (momentazo por capítulo), try/fail, escalas de personaje
  (bloque "Sliding scales" al final de `plan/arcs.md`, check 4b en critique-chapter),
  `expand-chapter` reconvertido en grounding pass de 6 tipos. El **outline fue alineado cap
  a cap** (líneas nuevas **Momento (ley cero)** y **Elección del POV**; texture beats
  tipados `[mundo]/[escenario]/[factura]/[deliberación]/[reorientación]/[secundario]`).
  **Toda nota de estado de capítulo fechada antes de esta línea es STALE** (habla de pasadas
  borradas); las lecciones de pipeline/voz de `voice.md` siguen vigentes y las decisiones
  durables de `decisions.md` (p. ej. la Lectura como rito de varios días) también.

- (2026-06-25, ch 1) **Desincronía nombres bundle ↔ canon.** `build_context.py` emite **Tobías / Vela / Bras** (tutor / cazador / ideólogo verde) pero `book-01/canon/characters.md` dice **Mauro / Cándido / Tilo**. Resolver cuál es el bueno y sincronizar **antes del cap 4** (entra el tutor). No afecta al cap 1.
  - (2026-06-29, ch 1) **Evidencia:** el bundle de contexto del cap 1 (`_context-ch01.md`) salió **consistente con Mauro/Cándido/Tilo** — no se observó ninguna fuga de Tobías/Vela/Bras esta sesión. Aún así, **verificar build_context** (puede venir de un mapping de nombres por defecto / placeholder en otra ruta) antes del cap 4.
  - (2026-07-01, ch 1) **Reconfirmado:** el bundle del cap 1 volvió a salir limpio (Mauro/Cándido/Tilo). Sigue pendiente **verificar build_context antes del cap 4**.
  - (2026-07-01, ch 2) **Reconfirmado (cap 2):** el bundle `_context-ch02.md` también salió limpio (Mauro/Cándido/Tilo). **Ya solo faltan 2 capítulos para el 4** (entra Mauro como tutor con nombre en escena): verificar/limpiar el mapping en `build_context.py` **esta sesión o la próxima**, antes de escribir el cap 4.
  - (2026-07-02, ch 1 reescritura) **Reconfirmado otra vez tras el reset:** el bundle `_context-ch01.md` de la reescritura volvió a salir limpio (Mauro/Cándido/Tilo), en fase `plan`, `write` y `expand`. Con el estado reseteado a 0, **quedan 3 capítulos para el 4**. Sigue PENDIENTE verificar/limpiar el mapping en `build_context.py` antes de escribir el cap 4.
  - (2026-07-03, ch 2) **Reconfirmado (cap 2 escrito y bloqueado):** el bundle `_context-ch02.md` (plan/write/expand) volvió a salir limpio (Mauro/Cándido/Tilo). El siguiente es el **cap 3 (POV Olmo/Valverde)** y luego el **cap 4** (Mauro tutor con nombre en escena). **PRIORIDAD ALTA: verificar/limpiar el mapping en `build_context.py` antes del cap 4** — quedan 2 capítulos.
  - (2026-07-06, ch 1 — nuevo arranque) **Reconfirmado tras reescribir y BLOQUEAR el cap 1:** el bundle `_context-ch01.md` volvió a salir limpio (Mauro/Cándido/Tilo) en plan/write/expand; `grep` de Tobías/Vela/Bras solo encontró las menciones de esta propia nota, cero fugas. Con el cap 1 ya bloqueado, la cuenta es: **cap 2 → cap 3 (POV Olmo) → cap 4 (Mauro tutor con nombre)**. **Quedan 3 capítulos.** Sigue PENDIENTE verificar/limpiar el mapping en `build_context.py` antes del cap 4 (esta sesión de estado ya no lo necesita, pero conviene cerrarlo pronto).

- (2026-07-01, ch 1) **Rimar las siembras Mauro del cap 2/4 con los pre-toques del cap 1.** El barrido inverso encontró en el cap 1 (decisión del autor: dejar como foreshadow, no reprogramar) dos imágenes que se adelantan a su siembra: las **manos manchadas** de Mauro (`las-manos-del-lector`, siembra formal cap 2) y la **mirada que busca/mide** envuelta en ternura (`el-tutor-tiene-agenda`, siembra formal cap 4). Al sembrarlas en 2/4, **rimar** con lo ya visto (Bruno ya se fijó en las manos; la mirada ya "buscaba"), no re-presentarlas como nuevas.
  - (2026-07-01, ch 2) **Mitad del cap 2 HECHA:** `las-manos-del-lector` se plantó rimando con el cap 1 —no se re-presentaron las manos manchadas como nuevas, sino que se añadió la **capa nueva** (la soltura ante el cristal del rito). **Queda abierto** el cap 4: al sembrar formalmente `el-tutor-tiene-agenda` (la mirada que **mide**), rimar con la mirada que en el cap 1 "ya buscaba", sin re-presentarla como nueva y **sin hacerla legible** (la lectura como medición es del cap 13).
  - (2026-07-02, ch 1 reescritura) **⚠ La nota anterior es STALE tras el reset:** el cap 2 aún NO está escrito en esta pasada. La reescritura del cap 1 vuelve a plantar los dos pre-toques: (1) Bruno le mide las **manos manchadas** de una palidez que no sale (`las-manos-del-lector`), (2) el gris que **fija la cara** de Bruno al final (roza el arranque de `el-tutor-tiene-agenda`, sin hacerlo legible: la mirada que *mide* es del cap 13). El `canon-scribe` lo marcó como FLAG 3b; **resuelto por decisión permanente** (`decisions-ch01.md`): dejar como foreshadow, **NO** reprogramar — plant formal de `las-manos-del-lector` sigue en cap 2, sin cambio de estado ni de schedule. **Al escribir el cap 2:** rimar con la mancha ya vista (añadir capa nueva: la soltura ante el cristal), no re-presentar las manos como nuevas.
  - (2026-07-03, ch 2) **✅ Parte cap 2 HECHA (bloqueada):** `las-manos-del-lector` plantada (→`planted`) rimando con el cap 1 —la mancha ya vista solo se referencia; la capa nueva es la **soltura vieja ante el cristal** al guardar el prisma. El crítico (PASS) marcó SHOULD que la re-descripción de la mancha vieja se recortara ("un toque, no dos") — **aplicado**. **QUEDA ABIERTO SOLO el cap 4:** al plantar formalmente `el-tutor-tiene-agenda` (plant in 4, la mirada que **mide**), rimar con la mirada que en el cap 1 "ya buscaba" y con la **hebra fría / desazón sin palabra** que quedó implícita en el cap 2, **sin hacerla legible** (la lectura como medición es del cap 13).
  - (2026-07-06, ch 1 — nuevo arranque) **⚠ Las dos sub-notas de "cap 2" de arriba son STALE:** ese cap 2 se borró en el tercer arranque; NO está escrito en esta pasada. El cap 1 recién bloqueado replanta LOS DOS pre-toques, mudos: (1) Bruno le mide a Mauro las **manos manchadas de una palidez que no sale** ("de algo que le había comido el color a la piel y no se iba con el agua"), y (2) el gris que, apartado de la fila, **mira caras "como quien busca a alguien entre la gente"** y al final **le fija la cara** a Bruno ("No resbalaron."). El `canon-scribe` confirmó: `las-manos-del-lector` **NO** avanzada (plant formal = cap 2); `mauro-fue-lector` se dejó **hidden** (el pre-toque de manos no basta para que el lector lo sospeche). **Al escribir el cap 2:** plant formal de `las-manos-del-lector` rimando con la mancha ya vista (capa nueva: la soltura ante el cristal), sin re-presentar. **Cap 4:** `el-tutor-tiene-agenda` rimando con la mirada que "ya buscaba" en el cap 1, sin hacerla legible (medición = cap 13).

- (2026-07-01, ch 1) **Coherencia del salvamento (magia).** El primer uso involuntario salva a Sela **por contacto** (muñeca) pero **no la agrisa**: Bruno solo roza el fondo ambiental difuso y no controla el caudal. Mantener coherente cuando aflore en escena la ley "el contacto toma de quien se le pone encima" (Sela fue tocada y no quedó gris) — no es contradicción ahora (ninguna ley está en la página), pero vigilar en el drenaje del clímax.

- (2026-07-06, ch 1) **Patrón recurrente: el borrador de `write-chapter` sale CORTO y el expand no cierra el hueco.** El cap 1 salió a **4524 palabras** (57% del suelo de 8000); tras las 2 pasadas de expand (tope) quedó en **~5400 (68%)**. No es outline mal planeado (los 3 texture beats tipados se usaron) ni relleno pendiente honesto (prisma en detalle = cap 2; coste del don = oculto; clímax a propósito ágil). Es que el registro windowpane sale **económico** en el 1er pase y el autor quiere demora/extensión. **Palanca honesta = un borrador más generoso en `write-chapter`** (desplegar cada beat con más textura DESDE el primer pase), NO más expand (que a partir de aquí sería relleno). Probar en el cap 2: escribir los bloques más largos de partida.

- (2026-07-06, ch 1) **Hueco de tooling: `lint_book.py` no cruza los `Surfaced:` de `shadow.md` contra los capítulos bloqueados.** Por eso el reset "0 capítulos" pudo dejar entradas fantasma ch2/ch3 en shadow.md y el lint pasó limpio (lo cazó el `canon-scribe` al bloquear el cap 1, ver Resueltos). **Mejora propuesta (TODO):** que `lint_book` marque ERROR/WARN cuando un `Surfaced:` cite un capítulo > último bloqueado, y/o que un `reset de estado` limpie también los `Surfaced`/`Status` de shadow.md. Sin esto, cada reset futuro puede repetir el desajuste.

## Resueltos (archivo)

- ~~(2026-07-06, ch 1) **FLAG canon-scribe: contradicción canon↔prosa en las siluetas del taller.**~~ Canon decía "dibujadas a **carbón**"; la prosa bloqueada dice "cerco de **grasa y tizne** sobre la cal" (rastro por uso, no dibujo deliberado). **RESUELTO (decisión del autor):** corregir canon → prosa (`canon/world.md`), la imagen del rastro involuntario es más fuerte.
- ~~(2026-07-06, ch 1) **FLAG canon-scribe: `shadow.md` con `Surfaced:` fantasma ch2/ch3 (secuela del reset).**~~ Entradas de ch2 (`funcion-real-de-la-iglesia`, `el-portaluz`, `mauro-fue-lector`) y ch3 (`el-cribado`) existían sin que esos capítulos estuvieran escritos. **RESUELTO (decisión del autor, reconciliado ya):** re-fechadas a **ch1** las tres verdades-decoy que el cap 1 SÍ lleva a `sensed` (rito que drena color hacia arriba; moneda del santo; el carro se lleva a los que alumbran), reescritas a la prosa real; `mauro-fue-lector` revertida a **hidden** (su carrier `las-manos-del-lector` no planta hasta el cap 2). `lint_book` limpio, cero fantasmas. Causa raíz → nuevo pendiente de tooling arriba.

- ~~(2026-07-03, ch 2) **`el-blanco-frio` tocado fuera de plan en el cap 2.**~~ El `frío de la nuca` (secuela del destello del cap 1) reaparece 3× en el cap 2, pero sus ecos programados eran 5/11/15. **RESUELTO (decisión del autor):** registrar como eco → `el-blanco-frio`→`echoed-1`, Realized ch2 escrito, y **cap 2 añadido a su `Echo in`** (ahora 2, 5, 11, 15) para que el calendario coincida. Es secuela inmediata (no nueva manifestación): `naturaleza-de-bruno` se queda en `sensed`.
- ~~(2026-06-25) **`critique-plan` saltado.**~~ **RESUELTO 2026-07-01:** corrido en limpio (subagente book-critic) → **PASS** (0 MUST, 2 SHOULD). Se aplicó el fix de consistencia POV (setup.md:194 Saúl→Olmo); las 2 verdades-de-más se difieren a II-III por decisión del autor. Además: reset del estado de capítulos (2 caps escritos contra un plan previo) para reescribir desde el cap 1 contra el plan finalizado.
