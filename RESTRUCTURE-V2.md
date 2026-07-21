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
> - **Fase 4 ⏳ (arrancada 2026-07-20)** — migración el-vitral (autor en el loop
>   por capa). **Paso 0 ✅ mecánico y test-gated:** `scripts/migrate_story.py`
>   mueve `seeds.md`/`shadow.md` → `state/{seeds,shadow}.json` sin pérdida. Split
>   honesto: los **seeds migran enteros** (Plant/Echo/Payoff → `schedule` vía el
>   parser loud; una diferición cross-book "Libro II" no aporta capítulo; el resto
>   de campos + touch-log verbatim en `notes`); los **truths migran solo
>   definiciones** — `reveal_caps` queda **vacío** porque el calendario de
>   revelación por-capítulo NO está en el archivo viejo (que solo tiene un nivel
>   de tope book-wide `sensed`/`suspected`): construirlo es la capa L5,
>   autor-en-el-loop, el migrador jamás lo fabrica. `verify_coverage` cruza
>   ids/schedule/status/touch-log/campos-raw (gate de cobertura: no escribe si
>   pierde algo) + `render_seeds_view` → `notes/_seeds-view.md`. ADITIVO: los `.md`
>   siguen en su sitio, no se escriben `world.json`/`entities.json`/eventos (capas
>   L1-L3), el store queda **dormido** (context.py gatea en `world.json`).
>   el-vitral migrado limpio (17 seeds, 10 truths). Refactor menor:
>   `seeds.parse_seeds(text)` extraído de `load_seeds` (espeja `shadows.parse_truths`).
>   +18 tests, **suite 251 OK**.
>   - **L1 ✅ (2026-07-20) — grafo del mundo (`plan-space`).** Subcomando read-only
>     `world_tool path` (¿existe ruta? + coste ordinal, exit 1 UNREACHABLE) para la
>     cobertura espacial + skill `plan-space` (gate interactivo, hilo principal:
>     propone lugares/aristas/POIs → STOP autor → aplica vía world_tool → verifica
>     que todo desplazamiento del outline tiene ruta). Corrido sobre el-vitral con
>     el autor: 10 lugares, 7 aristas, 7 entidades; replay OK; los 6 desplazamientos
>     con ruta. Commit del store `d0e9fb6`. Observación abierta: "Altaluz más lejos"
>     + clamp ordinal aplana casi todo a `días` (se revisa en L2).
>   - **L2 ⏳ infra (2026-07-20) — reloj del libro (`plan-time`).** Dual temporal de
>     L1: subcomando read-only `world_tool feasible` (coste de grafo vs.
>     `elapsed_bucket` entre dos relojes, exit 1 INFEASIBLE) + skill `plan-time`
>     (asigna reloj de apertura `(día, franja)` por capítulo vía `log-event --type
>     time`, verifica cada desplazamiento feasible). Decisión arquitectónica marcada
>     explícita para el autor: los relojes de plan-time viven como eventos `time` en
>     el log → L2 dueño de la apertura, el manifiesto de escritura la hereda y solo
>     emite `time` intra-capítulo. **✅ Corrido sobre el-vitral (d6557dc):** 24
>     relojes de apertura sellados, día 1→88 (~temporada); `replay OK`; los 2 viajes
>     reales del libro (Bruno vega→altaluz, Cándido solio→altaluz) FEASIBLE; la bajada
>     de cierre altaluz→camino INFEASIBLE en el día único del cap 24 — correcto,
>     completa off-page hacia el Libro II.
>   - **Extensión del motor: orden-de-historia ≠ orden-de-presentación (flashbacks).**
>     `Event` gana `story_pos` opcional (default `None` → `story_order == chapter`);
>     `sort_events`/`replay` ordenan y cortan por `story_order`, no por `chapter`. Un
>     capítulo-flashback narrado tarde pero ocurrido antes se coloca con `--story-pos`
>     en su sitio cronológico y la invariante "el reloj solo avanza" pasa a valer
>     sobre tiempo-de-historia. **ADITIVO**: un libro cronológico serializa
>     byte-idéntico (sin clave `story_pos`) y ordena igual que antes. El-vitral no
>     tiene flashbacks hoy; la extensión es para libros futuros. +3 tests.
>   - **L3 ⏳ infra (2026-07-20) — itinerarios del reparto (`plan-cast`).** Dual de
>     presencia de L1/L2: subcomando read-only `world_tool copresent --until-chapter N`
>     (mapa lugar→personajes + `meetings`; asserts `--expect-together` /
>     `--expect-apart`, exit 1; `--place` = overhear surface) + skill `plan-cast`
>     (coloca a cada personaje nombrado —on-page Y off-page— por capítulo vía
>     `log-event --type move|travel` en orden de historia, verifica que cada encuentro
>     que el outline asume esté copresente y cada secreto tenga los oídos equivocados
>     fuera). Sin movimientos, todos quedan congelados en su posición de apertura L1
>     — que es justo el hueco que L3 llena. +1 test. **✅ Corrido sobre el-vitral
>     (8bd3e73):** 11 desplazamientos logueados; `replay OK` día 88; 6 encuentros del
>     outline copresentes (Mauro↔Bruno ch1/2/5, convoy↔Olmo ch3/14, casi-test
>     Bruno↔Cándido ch16) + 3 privacidades (cazador en ruta ch10, clímax intrínseco
>     sin Cándido ch22, Olmo nunca cruza Bruno). Decisiones del autor: Cándido se va
>     tras ch16 (trampa intrínseca), convoy con ida y vuelta completa.
>   - **L4 ⏳ infra (2026-07-20) — layout de capítulo (`plan-layout`).** Lista de
>     escenas por capítulo derivada de L1-L3: cada escena con mitad **computada**
>     (stage/reloj/presentes/overhear vía `copresent`/`--place`/`render_place` —
>     no se teclea, no puede derivar) y mitad **autorada** (trabajo, quién habla/
>     calla, tempo+pausas). Verifica que cada escena tenga stage real y reparto
>     copresente y cada seed due tenga escena portadora; loguea los `move`/`travel`/
>     `time` **intra-capítulo** que el outline fija (los inter-capítulo son L3);
>     escribe `plan/layout.md`. Gruesa para todo el libro (critique-plan audita
>     exposición + cobertura de seeds), fina just-in-time en plan-chapter. **Sin
>     comando de motor nuevo** — se apoya entero en las queries que L1-L3 ya
>     dejaron; que no haga falta física nueva para la *lógica* de L4 es la señal de
>     que el stack paga. **✅ Corrido sobre el-vitral:** 24 capítulos → lista de
>     escenas en `plan/layout.md` (mitad computada del almacén, mitad autorada);
>     **0 eventos L4** (todo movimiento intra-capítulo es POI o ida-vuelta);
>     cobertura de portadoras verde (ningún seed due sin escena); 8 aserciones de
>     copresencia verdes. **1 hueco L1 que L4 cazó y corrigió:** `iglesia-altaluz`
>     era nodo huérfano sin arista (el grafo no podía poner a Bruno en la ascensión
>     del cap 9) → ahora **POI de `altaluz`**. Para aplicarlo hizo falta un comando
>     nuevo `remove-place` (validado por replay: rechaza si el lugar tiene aristas,
>     hijos, o una entidad/evento que lo referencia; +1 test) — no es física de L4,
>     es limpieza de L1 que la corrida de L4 destapó.
>   - **critique-plan (legacy) corrido sobre el plan denso: verdict PASS**
>     (0 MUST, 1 SHOULD). El SHOULD `[shadow-thin]`: `shadow.md` tiene 10 truths vs
>     suelo ≥12 — Cándido sin verdad propia, subtrama verde sin capa oculta de
>     Libro I; añadir 2-3. (El audit determinista emitió falsos positivos —deferrals
>     a Libro II/III, matcher de §14b y de entradas `[FIJO]`, per-acto sobre 7-ch por
>     defecto— que el crítico verificó contra fuente y NO contó.)
>   - **L5 ⏳ infra (2026-07-20) — conocimiento (`plan-knowledge`).** La última capa
>     ("el algo más"). Dos ejes sobre la lista de escenas de L4: la **escalera del
>     lector** (`reveal_caps` por truth: qué capítulos mueven al lector y hasta qué
>     dosis `hidden→sensed→suspected→confirmed`) y el **conocimiento de personaje**
>     (`learn`/`reveal` + `who_knows`). Dos comandos nuevos (duales del `copresent`
>     de L3): `set-reveal-cap` (autora un cap sobre un truth; valida dosis contra la
>     escalera; replay-valida) y `who-knows` (report + asserts `--expect-knows` /
>     `--expect-ignorant`, exit 1 — el muro que prueba que un secreto NO se filtró a
>     quien el plan mantiene a oscuras). El *join* con la overhear surface de L4:
>     un secreto dicho en una sala donde `who_knows` prueba que están los oídos
>     equivocados sale en el plan. Absorbe el SHOULD `shadow-thin` (paso 2: redactar
>     los 2-3 truths que faltan antes de tender sus caps). +1 test. Los 10 truths de
>     el-vitral llegaron migrados con `reveal_caps` vacíos — llenarlos es el corazón
>     de correr L5.
>   - **L5 ✅ corrido (2026-07-20) — sobre el-vitral, autor-in-the-loop.** El path
>     diferido `add-truth` construido y test-gated ANTES de correr: `mark_truth.py
>     --add` (append de un bloque SHADOW-TRUTH a la región Master-truths de
>     `shadow.md` vía `open()`, hook-safe) + `world_tool add-truth` (Truth al store
>     con `reveal_caps` vacíos) — evita re-migrar (que pisaría L1-L4). **shadow-thin
>     resuelto:** +2 writer-truths (10→12, el piso), en ambos carriles —
>     `el-cazador-sabe-que-existe` (cap suspected, la certeza interior del cazador) y
>     `el-verde-no-sabe-su-poder` (cap sensed, la capa oculta de la subtrama verde).
>     Decisiones del autor: naturaleza-de-bruno **hidden hasta el vuelco** (solo
>     13:suspected); `el-portaluz` en **escalera decoy** (1:misled→9:convinced, sin
>     invertir en el I); **Mauro sabe qué es Bruno desde el 1** (learn @1). 17 caps +
>     17 reveals + 3 learns. **Verificado:** replay OK; LA CAVERÍA (cap 16,
>     bruno+candido+mauro copresentes) — `who-knows naturaleza-de-bruno
>     --expect-ignorant candido` PASA (el cazador sale ignorante aunque comparta
>     sala), `--expect-knows mauro` PASA; un reveal fuera de cap se rechaza. Sin
>     disclosure imposible.
>   - **critique-plan profundo ✅ construido (2026-07-20).** `audit_plan_store.py` —
>     el audit store-backed (dual de `audit_plan.py`, store-gated: nota + exit 0 en
>     libro no migrado): **replay** (el plan es un estado válido), **escalera de
>     reveal honesta** (todo truth que aflora tiene cap; los caps solo suben; una
>     sola escalera reader/decoy; ninguno más alto que el `Reveal cap` de shadow.md
>     — el check que `set-reveal-cap` NO hace, con lógica decoy-aware: una decoy
>     revela la verdad solo al `inverted`), **seeds sin escena portadora** (cada
>     toque in-book cotejado contra `layout.md` — el "sin huérfanos" hecho
>     determinista) y **nodos aislados**. Cableado a `critique-plan` (paso 1b
>     store-gated + §3k cualitativo: correr `copresent`/`who-knows` sobre los
>     encuentros/secretos que outline/shadow/layout anotan — el testigo imposible /
>     secreto filtrado sale en el plan). **+13 tests (suite 275 OK).** Corrido sobre
>     el-vitral: 0 MUST, 2 SHOULD reales — `[decoy-ceiling]` el-portaluz (el store
>     corre a `convinced` pero shadow.md dice `sensed`: drift de la decisión decoy) y
>     `[seed-no-carrier]` el-telar-hilo-verde echo@2 (seeds.md lo programa, layout.md
>     lo dejó caer aunque shadow.md ch2 sí nombra el telar).
>   - **Suite 275 OK.** **El stack de plan L1-L5 + el critique-plan profundo están
>     completos.** **Pendiente de Fase 4:** correr el critique-plan profundo
>     entero (autor-in-the-loop, resolver los 2 SHOULD); luego replan+reescritura
>     cap 1 → primer commit de eventos de write-time real.

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

## Pendientes de Fase 2 — la costura `write → warm-fill → commit` (fixes R1/R2)

> **✅ Implementado 2026-07-21 (capa de skills, gated en `state/`).** Ambos fixes
> viven ya en `chapter-smith.md` + `write-novel/SKILL.md` + `chapter-grounder.md` +
> `update-canon/SKILL.md` (1b) + `canon-scribe.md`. Sin cambio de Python: R1 es
> disciplina de emisión, R2 reutiliza `copresent`/`who-knows` que L3/L5 ya
> construyeron. Se ejercitan de verdad al escribir el primer capítulo de el-vitral
> por la ruta v2 (store ya presente).

El smith de v2 vive **bien** salvo en una costura: entre que escribe y que
`update-canon` commitea, la prosa se toca dos veces más (warm-fill) y puede
proponer estados que el plan dio por imposibles. Ninguno de los dos es hipotético:
el-vitral ya tiene `state/world.json` + `events/`, así que la ruta MANIFEST está
**viva en la próxima escritura**. Dos fixes, ambos **reutilizan comandos que L3/L5
ya construyeron** (`copresent`, `who-knows`, replay) — no son física nueva ni una
batería de checks, son las aserciones de plan-time re-corridas en el único punto
donde la página (acto no derivado) puede romper la construcción.

### R1 — el MANIFEST/SUMMARY se emiten sobre el draft y quedan rancios tras el warm-fill

**Problema.** Hoy el smith emite MANIFEST + SUMMARY en el hand-off de fin-de-draft
([chapter-smith.md:149](.claude/agents/chapter-smith.md#L149)), PERO el warm-fill
(`write-novel` 2d, hasta 2 rondas) edita la prosa **después**, y el smith se
`RELEASE`a **antes** del commit (2e). Un inserto caliente puede escenificar un POI
nuevo o **mover la línea exacta donde aterrizó una semilla** → el replay/verify-cita
del commit cae sobre un manifiesto que ya no describe la prosa. El `WARM-FIX return`
solo devuelve `FIXED/FLAGS` y no tiene slot de manifiesto; el "unless the fix changed
them" de PLANTED/INVENTED no cubre eventos **aditivos** ni el SUMMARY.

**Fix (re-emisión, no un resume dedicado).** Invariante: *quien toca la prosa el
último emite el manifiesto que lee el commit.* La forma barata de garantizarlo NO
es diferir a un `EMIT-MANIFEST` al final (eso cuesta un resume con caché frío tras
la critique) — es **re-emitir en cada turno que ya toca prosa**: el warm-fill es el
único que edita después del draft, así que el manifiesto siempre viaja en un turno
que el smith hace de todos modos. Coste marginal cero.
- `chapter-smith.md` — el paso 7 (MANIFEST + DEVIATIONS + SUMMARY) sigue en el
  hand-off de fin-de-draft, pero marcado "describe el draft"; el `WARM-FIX return`
  gana un slot **MANIFEST + SUMMARY (refresh)**: si el fix añadió/movió/reescribió
  algo que el manifiesto rastrea, re-emite el manifiesto entero; si solo fue textura,
  `MANIFEST: unchanged`. El commit lee la última emisión.
- `write-novel/SKILL.md` 2e — regla explícita: el commit lee el manifiesto **más
  reciente** del smith (draft, o el refrescado del último `WARM-FIX`), nunca el del
  draft si hubo edición. Capítulo con PASS limpio (sin warm-fill) → el del draft ya
  es el final. Uniforme, sin turno extra.
- **Ruta fallback** (`chapter-grounder`, sin smith vivo): el grounder es quien toca
  la prosa el último, así que su retorno gana un **`MANIFEST-DELTA`** de lo que
  insertó; el commit lo aplica sobre el manifiesto base antes de verificar.
- **Por qué el residual real son los eventos ADITIVOS:** el quote-verify del commit
  (update-canon 1b.2) ya caza una cita **cambiada** (FLAG si la línea no está en la
  prosa). Lo que NO caza es un evento que el warm-fill escenificó y el manifiesto
  **nunca listó** (un POI, un `move` de una escena re-anclada) — la re-emisión existe
  para eso. Defensa en profundidad: prevención (refresh) + detección (quote-verify).
- *Guardrail R2b incluido:* al mover el manifiesto al final, la contabilidad tipada
  (`world_tool` vocab) queda **estrictamente como pasada final sellada**, nunca
  interleaved entre bloques de draft → la voz se sella antes del mode-switch a
  bookkeeping.

### R2 — las DEVIATIONS reconcilian en silencio y pueden filtrar la capa de conocimiento

**Problema.** v2 dice "la página gana, el commit reconcilia plan→página". Un choque
**duro** (move sin arista, reloj atrás) falla en el replay — bien. Pero una
desviación **blanda** —el smith mete a un personaje en una sala que el plan lo
mantenía fuera, o hace que alguien actúe sobre un secreto que la escalera `who-knows`
probó que no sabe— se absorbería sin ruido, destruyendo las garantías
`copresent()`/`who-knows()` que son la razón de ser del motor (y el contrato que el
autor puso por encima de la escritura misma).

**Fix (clasificar la desviación; re-asertar en el commit; FLAG, no reconcile).**
- `chapter-smith.md` — cada línea de `DEVIATIONS` se **etiqueta con la capa que toca**
  y nombra las entidades: `[spatial]` (posición, L1-L3) / `[knowledge]` (who-knows /
  reveal, L5) / `[tempo]` (ritmo/textura, libre). Ej.:
  `[knowledge] la página deja a Cándido oír el nombre → secreto=naturaleza-de-bruno`.
- `update-canon` / `canon-scribe` step 1b — tras el replay, iterar DEVIATIONS:
  - `[spatial]` → re-correr `world_tool copresent` (+ `feasible`) sobre el cap/escena
    afectada; si ahora junta a quien el plan mantenía aparte → **FLAG**.
  - `[knowledge]` → re-correr `world_tool who-knows <secreto> --expect-ignorant <char>`;
    si la página filtró el secreto → **FLAG**.
  - `[tempo]` → reconcilia libre (es el canal de auto-reorientación legítimo).
  - Un FLAG va al autor por el canal existente: o **acepta** la desviación como cambio
    de plan y **re-planifica la capa** (mover el itinerario L3 / ajustar el cap con
    `set-reveal-cap` L5), o el smith **revisa la prosa** para respetar el contrato.
    Nunca absorción silenciosa.
- *Tradeoff, honesto:* reintroduce una aserción en el punto donde el autor "odia los
  checks". Pero no es la batería v1: es re-correr **los mismos** comandos de plan-time
  en la única costura donde la construcción no basta. **La construcción garantiza el
  PLAN; el commit es lo único que mantiene la PÁGINA honesta al contrato** — porque la
  escritura es el único acto que el stack no deriva. Una desviación se rechaza (revisar
  prosa) o se promueve a cambio de plan (re-planificar capa); jamás se traga.
