# Reestructuración v2 — motor de estado del mundo en Python + planificación generativa por capas

> **Estado: EN CURSO.** Diseñado en otra conversación, persistido a disco el
> 2026-07-19. Aplicar entre libros / en un `/clear` limpio, fase a fase, suite
> verde tras cada una. Es ORTOGONAL pero solapa con `IMPROVEMENT-PLAN.md` en el
> área write↔update-canon (ver "Relación con IMPROVEMENT-PLAN" al final).
>
> ### Progreso
> - **Fase 0 ✅ (2026-07-19)** working tree commiteado en 3 commits lógicos
>   (infra M1-5+1c / contenido book-01 / este plan); `.DS_Store` ignorado; suite
>   verde. **Pendiente/aplazado:** mover `chapters/01.md` a `notes/calibration/`
>   NO se hizo — en disco es el borrador del smith (blind-compare), no el
>   fragmento del 5-jul que el plan asume; el autor decide cuál es el corpus.
> - **Fase 1 ✅ (2026-07-20)** motor `scripts/lib/engine/` completo (graph, clock,
>   state, story, events, queries, render, store) + `scripts/world_tool.py` (única
>   puerta de escritura, valida por replay antes de tocar disco). 35 tests
>   (unit + fixture-world: where/copresent/feasible/replay + los 4 rechazos de
>   integridad + el gate CLI). Suite 215 OK; smoke-test con python3 3.9. Añadí
>   `engine/store.py` (I/O, no listado en el plan pero implícito) y helpers de
>   `state/` en `paths.py`.
> - **Fase 2a ✅ (2026-07-20)** capa de código segura: `context.py`
>   `_world_state_block` (render_opening_state + fichas de escenario, inyectado
>   tarde en write/critique, gated en que exista `state/`, fallback legacy
>   intacto) + `lint.py` `check_world_replay` (el único check estructural). +6
>   tests, 221 OK. ADITIVO: ningún libro tiene `state/` aún, así que solo lo
>   ejercitan fixtures; Fase 4 retira los volcados legacy en libros migrados.
> - **Fase 2b ✅ (2026-07-20, capa de skills — a ciegas, ADITIVA y gated en
>   `state/`)** El autor eligió reescribir skills ya (sin migrar primero). Núcleo
>   determinado del bucle write↔update-canon, dormido hasta Fase 4: `chapter-smith`
>   + `write-chapter` emiten MANIFEST (event log tipado con vocab de `world_tool` +
>   cita en cada seed-touch) + DEVIATIONS + SUMMARY; `update-canon` + `canon-scribe`
>   ganan step 1b "commit del manifiesto" (aplica cada evento por `world_tool
>   log-event` → replay valida → rechazo = FLAG; verifica citas; status DERIVADO de
>   los touches). **Reconciliación 1c:** el manifiesto lo emite el smith (formaliza
>   PLANTED/INVENTED); warm-fill sigue pre-lock, el commit replaya el manifiesto
>   final. `CLAUDE.md` + `IMPROVEMENT-PLAN.md` actualizados. Suite 221 OK (prosa,
>   sin nuevos tests). **DIFERIDO a Fase 4** (fiction hasta construir las capas):
>   plan-book/plan-chapter/critique-plan L1-L5. **DIFERIDO (necesita el schema del
>   store)**: backend JSON de `mark_seed`/`mark_truth` + hook a `state/*.json` +
>   `migrate_story.py` (Fase 4 paso 0). El commit del manifiesto NO es ejecutable
>   hasta que esos + un libro migrado existan — es spec validable en Fase 4.
> - **Fase 3 ✅ (2026-07-20)** — estilo, independiente del store y testeable de
>   punta a punta. (1) El símil explicativo pasa a **cap duro contado**:
>   `explanatory_simile_per_scene` en toml + fila `TicCount` worst-scene en
>   `audit_chapter_tics`; el `over` se activa solo con over-cap Y densidad sobre
>   el suelo de `audit_prose`, así el cap 1 (una escena de 3.7k, ~2.4/1000) sigue
>   limpio y el fixture (varios símiles en una escena corta) dispara. Recencia:
>   bullet dedicado en `VOICE_SPINE_BRAKES` + línea en `_CRAFT_ANTIPATTERNS`.
>   critique 8b: fila SÍ + peor escena ≥3 → MUST `[style-cap]` (no está en
>   `_REJECT_TIER` → REVISE, nunca REJECT, sin tocar verdict.py). (2) Repetición
>   **intra-capítulo** informativa: `intra_chapter_repetition` (`_motif_echoes`
>   sobre el mapa de escenas + pares de frases casi idénticas por
>   `SequenceMatcher ≥ 0.75`, ≥6 palabras) — sección nueva del report, sin cap.
>   (3) Nuevo `scripts/calibrate_diff.py` (git HEAD vs working tree, alineado por
>   frase, deltas medibles → `notes/_calibration-chNN.md`) + skill `calibrate-style`
>   (destila las ediciones a mano del autor en reglas nombradas, ruteadas a
>   style-rules/toml[[extra_patterns]]/[caps], AskUserQuestion, anti-fotocopia
>   >3 palabras; interactiva, sin subagente). +9 tests, **suite 233 OK**.
> - **Fase 4 ⏳** migración el-vitral (autor en el loop por capa).

## Context

El autor detectó que el **contrato espacio-temporal** de la historia (dónde está
cada uno en todo momento, quién habla, la geografía de cada espacio) importa más
que la escritura misma — y hoy no existe: la unidad mínima planificada es el
capítulo, la escenografía que la prosa inventa nunca vuelve a canon, y el tiempo es
texto libre. Además el estilo no está marcado (el símil explicativo "A, como B
que…" es el tic nº1 y el peor vigilado).

**Dirección del autor sobre el primer borrador del plan (v1, rechazado por overkill):**

- **Grafos de verdad, no Markdown parseado.** Usar la potencia de Python: el
  contrato espacial es para TODO el libro (regiones ⊃ ciudades ⊃ edificios ⊃ salas)
  y en todo momento debe quedar claro dónde está cada personaje.
- **Odio los checks.** Nada de baterías de validación post-hoc: la generación por
  capas debe ser tan buena que el libro solo necesite una lectura superficial para
  encontrar fallos. Los errores deben ser difíciles POR CONSTRUCCIÓN.
- **Interacción más fina** entre escribir y update-canon.
- **Flujo deseado:** esqueleto → temporalidad, espacio, personajes, layout de
  capítulo, seeds/shadows (+ algo más si procede) → un critique de plan que ya
  detecte fallas → el LLM al escribir se auto-orienta.
- **Aplicar YA** a el-vitral book-01 (cap 1 borrado); IA propone cada capa, autor
  revisa; modelo positivo de estilo sin re-activar exemplars.

## La inversión central: el motor de estado (`scripts/lib/engine/`)

Hoy: Markdown como fuente de verdad + parsers "loud" + checks que cazan
contradicciones después. Nuevo: **estado estructurado en JSON mutado solo por
scripts** (precedente `mark_seed.py`), un motor Python stdlib que lo reproduce y
consulta, y **vistas Markdown COMPUTADAS** que son lo que el LLM lee. El LLM nunca
edita JSON; propone en conversación y el skill aplica via CLI.

**Módulos nuevos (stdlib puro: dataclasses + json + BFS, sin networkx):**

- `engine/graph.py` — el grafo espacial. Nodos jerárquicos:
  `Place(id, name, kind ∈ {region, ciudad, aldea, edificio, sala, camino}, parent,
  pois[], desc, provenance)`. Aristas: `Edge(a, b, mode, cost)` con coste
  cualitativo ordinal (minutos < horas < medio-día < día < días). Consultas:
  `path(a,b)`, `travel_cost(a,b)`, `contains(region, place)`.
- `engine/clock.py` — reloj del libro: `(día, franja)` con franjas ordenadas
  `{madrugada … noche}`; aritmética ordinal, monótono por construcción al aplicar
  eventos.
- `engine/state.py` — entidades: personajes y objetos clave con `position` (place
  id), `status`, `holding`. `WorldState` = posiciones + reloj + conocimiento en un
  instante.
- `engine/events.py` — event sourcing: log tipado por capítulo,
  `state/events/ch-NN.jsonl`. Vocabulario pequeño: `move`, `travel`, `time`,
  `acquire/drop/transfer`, `learn(char, seed_id|fact)`, `reveal(truth_id)`,
  `plant/echo/payoff(seed_id, cita)`, `enter/exit_scene`, `status`.
  `replay(hasta cap N, escena M) -> WorldState`. Aplicar un evento imposible (mover
  sin arista, reloj hacia atrás, transferir lo que no se tiene, un reveal sobre su
  cap) falla EN EL COMMIT — un único punto de integridad, no una batería de checks.
- `engine/story.py` — seeds y shadow como primera clase del motor:
  `Seed(id, desc, schedule{plant/echo/payoff → capítulos}, …)` en
  `state/seeds.json`; `Truth(id, desc, reveal_caps{cap → dosis}, …)` en
  `state/shadow.json`. Su ciclo de vida son eventos del mismo log: el touch-log
  `Realized:` ES el event log (entradas plant/echo/payoff con cita de la prosa);
  `seed_status(id, t)`, `due(N)`, `overdue(N)` son queries; un reveal por encima del
  cap del capítulo es un estado irrepresentable, no una regla que comprobar. Toda la
  maquinaria sagrada actual (hook never-compress, mutación quirúrgica de `seeds.py`,
  el gotcha del dígito suelto en `Payoff in:`) existía para compensar Markdown como
  almacén — desaparece de raíz. `mark_seed.py` / `mark_truth.py` CONSERVAN nombre e
  interfaz CLI (los skills no cambian) pero escriben al almacén JSON.
- `engine/queries.py` — lo que hace útil el motor: `where(entity, t)`,
  `copresent(t)` (quién coincide con quién), `overhear_surface(scene)` (quién puede
  oír), `feasible(entity, place, t1, t2)` (¿puede X estar en Y en el cap N dado
  dónde estaba?), `who_knows(seed_id, t)`.
- `engine/render.py` — las vistas que entran al bundle: `render_opening_state(N)`
  ("Estado del mundo al abrir el cap N": dónde está cada uno, reloj, qué sabe el POV
  — sustituye al `continuity-chNN.md` escrito a mano), `render_place(id)` (ficha de
  escenario con POIs y salidas), `render_itinerary(char)`. Regenerables a
  `notes/_state-chNN.md` (gitignored).
- `scripts/world_tool.py` — CLI de mutación (`add-place`, `connect`, `place-poi`,
  `set-position`, `log-event`, `replay`, `where`): la única puerta de escritura al
  estado.

**Datos en disco:** `output/<series>/book-NN/state/world.json`, `state/entities.json`,
`state/seeds.json`, `state/shadow.json`, `state/events/ch-NN.jsonl`. Todo
determinista, versionado, diffable. El hook `protect-never-compress.sh` pasa a
bloquear Edit/Write directo de `state/*.json` (misma filosofía: mutar solo via
scripts). Para lectura humana, vistas regenerables `notes/_seeds-view.md` /
`notes/_state-chNN.md` (gitignored).

**Por qué esto elimina checks:** el contrato de escena ya no se escribe a mano y se
valida después — se **deriva** del motor (el planner consulta itinerarios y reloj:
solo puede montar escenas con gente que de verdad puede estar allí), y el lock-in
compromete eventos cuya integridad valida el replay una sola vez. Teleports, relojes
rotos y testigos imposibles pasan de "fallos que cazar" a "estados irrepresentables".

## Escribir ↔ update-canon: el bucle fino (lock-in = commit, no caza)

- **plan-chapter** deriva del motor el contrato del cap N (escenas con lugar, reloj,
  presentes computados de itinerarios, quién habla/oye, tempo) → lo propone en chat
  → el autor corrige → persiste los eventos planificados del capítulo.
- **write-chapter** escribe la prosa Y emite, en el mismo turno (voz viva, coste
  marginal):
  - **el manifiesto:** el log de eventos que la página realmente escenificó
    (movimientos, aprendizajes, traspasos, avance de reloj, plants/echoes con cita)
    + facts nuevos enumerados (`INVENTED:` un tic de Mauro; `POI:` la viga quemada
    del granero);
  - **el resumen del capítulo** (acaba de escribirlo — su resumen es mejor y gratis;
    hoy el scribe relee 18k palabras para reconstruirlo);
  - **desviaciones del plan declaradas** ("la historia pide que Mauro llegue antes")
    — el canal de auto-reorientación.
- **update-canon** queda reducido a un **commit**: (a) `replay` valida e integra los
  eventos del manifiesto — posiciones, reloj, seeds, reveals, todo lo dinámico entra
  al motor sin tocar ningún `.md`; (b) verificación ligera: las citas del manifiesto
  y el resumen se contrastan contra la prosa (mismo mecanismo que
  `verify_critique_quotes.py` — verificar, no descubrir); (c) los pocos `INVENTED`
  narrativos se aplican como líneas aditivas (la mayoría son eventos o POIs via
  `world_tool`, no ediciones de canon); (d) contradicción o desviación de plan =
  FLAG al autor. Por construcción queda poco residuo: L3/L5 caracterizan a los
  personajes y su conocimiento ANTES de escribir, así que la página solo añade
  toques — y llegan ya enumerados. El gemelo pesado del pipeline (204k de output,
  cazando) colapsa a una pasada de verificación + trabajo de script.
- La costura de continuidad ("Opens at / On stage") pasa a ser render computado —
  deja de poder desincronizarse de la realidad.

## Las capas (plan-book reestructurado como profundización progresiva)

Cada capa: la IA la propone COMPLETA (tablas legibles en chat), el autor corrige, el
skill aplica al motor via CLI. Cada capa escribe información que todas las siguientes
reutilizan.

- **L0 — esqueleto:** actos + trabajo de cada capítulo (el outline actual, se
  conserva).
- **L1 — espacio:** el grafo del mundo entero del libro: regiones, ciudades,
  edificios, salas donde la historia entra; POIs solo donde un beat los necesita (el
  pozo existe porque Sela cae en él); aristas con costes cualitativos cubriendo cada
  desplazamiento del outline.
- **L2 — tiempo:** el calendario del libro: reloj por capítulo. Al asignarlo,
  `feasible()` ya delata viajes imposibles — la falla aflora AL PLANIFICAR, no en
  critique.
- **L3 — personajes:** itinerarios — posición de cada personaje nombrado por
  capítulo (incluidos los que están fuera de página: el antagonista también se
  mueve). `copresent()` revela encuentros posibles/imposibles que el outline asume.
- **L4 — layout de capítulo:** lista de escenas por capítulo derivada de L1-L3:
  lugar, reloj, presentes, quién habla / quién calla / quién puede oír, trabajo,
  tempo + pausas. Gruesa para todo el libro (lugar+reparto+trabajo — suficiente para
  que critique-plan audite), fina just-in-time en plan-chapter (diálogo, tempo,
  salidas).
- **L5 — conocimiento (el "algo más"):** quién sabe qué y desde cuándo. Seeds y
  shadow viven YA en el motor (`engine/story.py`): los eventos `learn`/`reveal`/
  `plant`/`echo`/`payoff` referencian sus ids, `who_knows(seed, t)` +
  `overhear_surface(scene)` responden en tiempo de plan, y los reveal-caps son
  restricciones de commit. Una escena donde un secreto se dice delante de quien no
  debe saberlo se ve en el plan, no en la página. El seed envelope del bundle pasa a
  computarse con una query; los checks de seeds de `lint_book` (schedule sanity,
  seed↔shadow refs) se vuelven by-construction (claves foráneas del almacén).
- **critique-plan** se profundiza para auditar el plan YA denso, capa a capa (huecos
  del grafo, itinerarios rotos, exposición imposible, seeds sin escena portadora) —
  la falla se encuentra donde es barata. **Objetivo declarado:** tras esto, el libro
  escrito solo necesita lectura superficial.

## La unidad mínima de un capítulo (presupuesto de tokens)

El contrato L4 es la clave de scoping: el motor sabe qué lugares y personajes toca el
cap N, así que el bundle de write deja de volcar canon "por si acaso" y pasa a
computarse por query. La unidad mínima:

- Contrato del capítulo (escenas finas: lugar, reloj, presentes, hablan/oyen, tempo)
  — ~1-2k
- Estado de apertura computado (`render_opening_state(N)`: dónde está cada uno,
  reloj, qué sabe el POV) — <1k
- Fichas solo de lo presente: `render_place` de los 2-4 lugares del cap + ficha de
  voz/motivación de los 5-8 personajes en escena (con su estado actual del motor) —
  ~2-3k
- Envelope de seeds due en N (query, con citas Realized para rimar) + slice del
  shadow — ~1k
- Costura de continuidad (resumen N-1 + escena final verbatim) — insustituible para
  la voz — ~2k
- Estilo: `style.md` operativo + style-rules + voice-spine/brakes — ~4-5k
- Decisiones vinculantes + beat sheet — ~1k

**Total ~11-14k frente a los ~26k actuales (≈ −50%)**, y desaparecen los bloques
enteros de canon-en-medio-de-baja-atención (world/factions/magic/timeline completos,
setup, serie). El mismo scoping aplica al bundle de critique. El coste se desplaza a
la construcción (L1-L5 + revisiones) — que se paga UNA vez por libro (y un incremento
fino por capítulo en plan-chapter), mientras el ahorro se cobra en cada write +
critique + lock-in. Los levers Phase-C diferidos del TODO (canon scoping, setup
filter) quedan realizados de forma natural por esta vía — mejor que como filtros de
Markdown.

## Estilo (adelgazado de v1 — lo estructural ya no necesita policía)

- **Símil explicativo → cap duro contado:** `explanatory_simile_per_scene = 1` en
  toml + fila `TicCount` en `audit_chapter_tics` (reutiliza `_SIMILE_RE` +
  `split_scenes`, patrón worst-scene). Y el fix de recencia: bullet en
  `VOICE_SPINE_BRAKES` ("El símil explicativo (A, como B que…) máx. uno por escena —
  colapsa la comparación en un verbo que escenifique") + línea en
  `_CRAFT_ANTIPATTERNS`. En critique 8b: sobre cap por ≥2 → MUST `[style-cap]`
  (REVISE, nunca REJECT).
- **Repetición intra-capítulo → solo informe, sin caps nuevos:** `_motif_echoes`
  re-apuntado a las escenas de un capítulo + frases casi-duplicadas
  (`difflib.SequenceMatcher ≥ 0.75` sobre oraciones ≥6 palabras) como filas
  informativas del report — evidencia para el crítico, no gates.
- **calibrate-style (skill nuevo) + `scripts/calibrate_diff.py`:** el modelo positivo
  sin exemplars. Entrada: `git show HEAD:chapters/NN.md` vs working tree (ediciones a
  mano del autor) o `--before/--after`. El script alinea oraciones (difflib +
  `split_sentences`) y emite `notes/_calibration-chNN.md` (pares alineados + deltas
  medibles). El skill destila con el autor cada cluster en una regla nombrada y
  generalizada (nunca cita >3 palabras seguidas de la prosa — anti-fotocopia),
  tipada a destino: cadencia → `notes/style-rules.md` `## Cadencia` (ya inyectado en
  9b); tic regexable → `[[extra_patterns]]` del toml; recalibrado → `[caps]`.
  Confirmación por `AskUserQuestion`.
- El **tempo estructural** (lento/medio/rápido + pausas nombradas) vive en la escena
  de L4, no en reglas: el ritmo se planifica donde se decide.

## Cambios por fichero

**Nuevo código (cada módulo con tests unittest):** `scripts/lib/engine/{graph,clock,
state,events,story,queries,render}.py`, `scripts/world_tool.py`,
`scripts/calibrate_diff.py`, `scripts/migrate_story.py` (one-shot: parsea los
`seeds.md`/`shadow.md` existentes REUTILIZANDO los parsers actuales de
`lib/seeds.py`/`lib/shadows.py` → `state/seeds.json`/`state/shadow.json`; archiva los
`.md` originales en `notes/archive/`, nunca los borra).

**Modificados:**

- `scripts/lib/context.py` — el bundle de write/critique pasa a computado y scoped
  por el contrato: bloque "Estado del mundo + escenografía del cap N"
  (`render_opening_state` + fichas solo de lugares/personajes presentes), colocado
  tarde, sustituyendo la inyección de `continuity-chNN.md` escrito a mano Y los
  volcados completos de canon (world/factions/magic/timeline dejan de entrar enteros;
  fallback legacy si un libro no tiene motor); envelope de seeds via query; bullets
  de símil en `VOICE_SPINE_BRAKES` + `_CRAFT_ANTIPATTERNS`.
- `.claude/skills/update-canon/SKILL.md` — reescrito como commit: replay+verificación
  de manifiesto y resumen del escritor, INVENTED aditivos, FLAGs; el scribe deja de
  releer el capítulo para descubrir. El resumen del capítulo lo emite write-chapter.
- `scripts/lib/prose_lint.py` + `notes/prose-lint.toml` — fila de símil (cap duro);
  filas informativas intra-capítulo.
- `scripts/lint_book.py` / `lib/lint.py` — UNA adición: replay completo del event log
  del libro (el único check estructural; sustituye a la batería v1 de
  scenes/places/clock checks, que NO se construye). Los checks actuales de seeds
  (schedule sanity, seed↔shadow refs) se retiran al quedar cubiertos por el almacén.
- `scripts/mark_seed.py` / `scripts/mark_truth.py` — mismo nombre y flags, backend
  nuevo (escriben eventos/registros al almacén via engine). `lib/seeds.py`/
  `lib/shadows.py` quedan como parsers solo-migración;
  `update_status_in_text`/`append_realized_in_text` mueren con su causa.
- `.claude/hooks/protect-never-compress.sh` — pasa de proteger
  `plan/seeds.md`+`plan/shadow.md` a proteger `state/*.json`.
- **Skills:** `plan-book` (capas L1-L5 con stop de revisión por capa; invocación
  retrofit), `plan-chapter` (deriva contrato del motor, propone, persiste eventos
  planificados), `write-chapter` (manifiesto + resumen del cap + facts espaciales +
  desviaciones declaradas), `critique-plan` (auditoría por capas del plan denso),
  `critique-chapter` (8b `[style-cap]`; SIN batería 8e; bundle scoped), nuevo
  `calibrate-style`.
- `CLAUDE.md` — actualizar la doctrina: "deterministic Markdown + stdlib" pasa a
  "ficheros deterministas (Markdown para prosa y canon narrativo; JSON de estado
  mutado solo por scripts) + stdlib; las vistas que lee el LLM se computan". Retirar
  los gotchas de `seeds.md` (never-compress, mutación quirúrgica, dígito suelto) — su
  causa desaparece. + 6-8 líneas sobre el motor. Una frase en `IMPROVEMENT-PLAN.md`:
  el manifiesto de write-chapter ES el hand-off PLANTED/INVENTED de Movement 1,
  formalizado.

## Secuencia

**Fase 0 — seguridad:** commit del working tree sucio; mover `chapters/01.md`
(fragmento bendecido 5-jul, untracked) → `notes/calibration/ch01-fragmento-bendecido.md`
con header "corpus de calibración, nunca inyectado". Suite verde.

**Fase 1 — motor:** engine (graph → clock → state → events → queries → render) +
`world_tool.py` + tests. Criterio: montar un mini-mundo de fixture y responder
`where`/`copresent`/`feasible`/`replay`.

**Fase 2 — integración pipeline:** `context.py` (bloque computado) → skills de plan →
write-chapter (manifiesto) → update-canon (commit) → critique-plan/chapter → lint
(replay). Tests de context.

**Fase 3 — estilo:** prose_lint + brakes + calibrate-style.

**Fase 4 — migración el-vitral (autor en el loop por capa):**
0. `migrate_story.py`: `seeds.md`/`shadow.md` → almacén; verificar renderizando
   `notes/_seeds-view.md` y comparando cobertura contra los originales (ningún seed,
   status, touch-log ni truth perdido); originales archivados.
1. **L1 retrofit:** grafo desde `world.md` + los Where/when del outline + la
   plaza/casa del fragmento (procedencia obs. cap 1 (fragmento) — ya bendecidas).
   Revisión.
2. **L2-L3:** reloj por capítulo + itinerarios (Bruno, Sela, Mauro, Brígida,
   oficiante, antagonista fuera de página). Revisión — aquí `feasible()` da su primer
   fruto real.
3. **L4 gruesa** libro entero + **L5 conocimiento** (eventos learn/reveal
   referenciando los seeds existentes). Revisión.
4. **critique-plan profundo** sobre el plan denso; resolver hallazgos.
5. **Replan fino cap 1** (`decisions-ch01.md` sobrevive como input vinculante) →
   reescribir cap 1 → primer commit de eventos real.

## Qué NO construir

- networkx / DB / coordenadas / mapas ASCII — grafo stdlib con costes cualitativos;
  disposición en prosa dentro de la ficha renderizada.
- Simulación autónoma (NPCs que "viven") — el motor responde consultas, no simula.
- La batería de checks v1 (critique 8e, parsers de Markdown `scenes.py`/`places.py`,
  caps intra-capítulo) — sustituida por derivación + un commit validado.
- Escenas finas de los caps 2-24 por adelantado; aritmética de reloj más allá de
  ordinales.
- Re-activación de exemplars; `notes/calibration/` jamás se inyecta.
- Script que pre-rellene capas sin conversación (precedente "pre-fill produce ruido").

## Verificación

- **Fase 1:** suite verde; fixture-mundo responde `where`/`copresent`/`feasible`;
  replay rechaza move-sin-arista, reloj retrógrado, transfer-sin-posesión y
  reveal-sobre-cap.
- **Migración seeds/shadow:** `mark_seed.py --realized` sobre el almacén migrado
  produce el mismo efecto observable que antes (touch-log visible en `_seeds-view.md`
  y en el envelope computado del bundle); diff de cobertura contra los `.md`
  archivados limpio.
- **Fase 2:** `build_context.py --phase write` del cap 1 antes/después — el bloque
  computado aparece con posiciones y escenografía correctas; `lint_book` ejecuta el
  replay del libro.
- **Fase 4:** tras L2-L3, introducir a propósito un itinerario imposible →
  `feasible()` lo delata en el plan. Pipeline completo del cap 1: contrato derivado →
  prosa → manifiesto → commit limpio → `render_opening_state(2)` muestra el mundo
  correcto para el cap 2.
- **Estilo:** fixture con 3 símiles en una escena → fila sobre cap en el report;
  `calibrate_diff` sobre un par before/after produce pares alineados.

## Relación con IMPROVEMENT-PLAN.md (el plan pequeño ya ejecutado)

`IMPROVEMENT-PLAN.md` (Movements 1-5 + 1c, casi todo landed 2026-07-19) es
ORTOGONAL en intención (coste + voz) pero SOLAPA con este v2 en el área
write↔update-canon:

- **Compatible / reutilizado:** Movement 1 (`chapter-smith`) sobrevive — v2 dice
  explícitamente que "el manifiesto de write-chapter ES el hand-off PLANTED/INVENTED
  de Movement 1, formalizado". El scoping de bundle de v2 (L4) REALIZA los levers
  Phase-C diferidos y va más allá que Movement 2 (brief) / Movement 5 (slim critique).
- **Parcialmente resuperpuesto:** el bucle fino write↔update-canon de v2 (manifiesto
  + resumen emitido por write-chapter + update-canon = commit) es un rediseño más
  profundo que 1b. El smith persistente (1c) y el warm-fill / `chapter-grounder`
  (M3) NO están contemplados en v2 — son capa de profundidad de prosa, ortogonal;
  pueden coexistir, pero al reescribir write-chapter/update-canon para v2 hay que
  reintegrarlos conscientemente (el manifiesto lo emite el smith; el DRAFTING_PAUSED
  / desviaciones declaradas son el mismo canal de auto-reorientación que v2 pide).
- **Nada de lo hecho hay que revertir** para empezar v2, pero al llegar a Fase 2 se
  decide cómo el smith persistente emite el manifiesto y cómo el warm-fill convive
  con update-canon-como-commit.
