# Plan critique — *El Apagado* (Libro I de *el Vitral*)

**Verdict:** REVISE (con asterisco — ver §0)

**Summary.** El edit estructural cerró todas las MUST de fondo que se
señalaron contra la v3: clímax como elección activa, coste del vacío
resuelto, reloj puesto, cara de la Orden (Vela), subtrama verde (Yedra),
declaración del sistema invertido. A nivel de **serie y de plan**, esto
ya es un libro que puede empezarse. Lo que queda es trabajo de
**transición de biblia a outline capítulo-a-capítulo** — y un par de
huecos finos que no se ven en el documento de serie.

## §0 — Por qué REVISE y no REJECT

El audit reporta MUST por outline TODO en los 25 capítulos. Eso es real
pero **esperado** en este momento: el documento de origen era una biblia
de serie, no un outline. La transición a beat-sheets por capítulo es la
siguiente tarea, no un bloqueo. Cuento outline-vacío como **una sola MUST
de transición**, no 25. Si se trataran como 25 individuales, esto sería
REJECT por bug del criterio, no por mérito.

Las otras MUST sí son hallazgos reales (gating decisions, plot fields
sin resolver).

## MUST fix

- **[gating] §13.2 — entrada de Bruno a la Academia.** Mentor reformista
  vs. Orden / Vela. El plan asume mentor reformista (ch 2-3 lo capta).
  Si la decisión cambia a "Vela lo detecta y lo mete dentro para
  vigilarlo", el primer acto entero se reescribe: la dramatic irony del
  Libro I cambia de "Vela busca a un Negro sin saber que está a tres
  pasos" a "Vela ya lo tiene cerca para confirmarlo". Imposible escribir
  el ch 1 antes de cerrar esto.
- **[gating] §13.3 — progenitor Negro.** Vivo o muerto al empezar; en
  escena o solo en backstory. Si vivo y en escena en Libro I, los ch 5-6
  son una vía de exposición íntima; si solo en backstory, lo es la
  Orden / Vela. Esto cambia **qué tipo de libro es** — íntimo o
  procedimental.
- **[plot] setup.md §Plot tiene TODOs en midpoint / all-is-lost / climax
  / resolution.** El plan los tiene **propuestos** dentro del párrafo,
  pero la sección está sin cerrar. El ch 13 (midpoint = primer uso
  honesto), ch 20-22 (all-is-lost = detección), ch 25 (cierre = Vela lo
  lee) son la columna del libro. Cerrar literalmente esas 4 líneas en
  setup.md.
- **[transición] outline.md está TODO en los 25 capítulos.** Esperado al
  pasar de biblia a plan, pero **el siguiente paso es expandir cada
  capítulo a plot beats / texture beats / subtext beats**. Sin esto,
  `write-chapter 1` no arranca (la skill se niega si el beat sheet está
  vacío). Empezar al menos por act 1 (ch 1-7) antes de iniciar prosa.

## SHOULD fix

- **[reparto] Bruno no tiene physical specifics cerrados.** El resto de
  principales sí (Vela: anillo girado / manos sin temblar / ojos pálidos
  · Yedra: aura saturada / cicatriz en frente / pulgar deformado). El
  protagonista debe estar al nivel de los antagonistas. Tres detalles
  concretos, no clichés.
- **[ritmo del clímax] Nueve seeds pagan en ch 25.** El cierre del Libro
  I es estructuralmente el "discovery chapter" donde casi todo se
  resuelve para el lector. Eso hace el ch 25 enorme y arriesgado: si no
  aguanta, el libro fracasa en la última página. Considerar:
  - Distribuir 1-2 payoffs a ch 24 (vela-prisma-anillo podría caer aquí
    como pre-eco visual del cierre).
  - Hacer del ch 25 un capítulo de mayor longitud (limit superior de
    palabras) declarado en setup.md.
- **[ritmo de Bruno en 2A] No hay un "first real failure" claro para
  Bruno entre ch 8 y ch 12.** Pasa del destello (ch 1) al primer uso
  honesto (ch 13). En el medio, Bruno aprende control en la Academia
  pero no hay un punto donde su contención falle visiblemente y el
  mundo casi lo vea. La beat de "first real failure" de
  `references/fantasy-beats.md` está sin tocar. Proponer: ch 11, un
  examen en la Academia donde Bruno casi se delata por exceso de
  control sospechosamente perfecto. Vela lo ve a distancia o le llega
  reporte.
- **[reparto sin rostro] Castas declaradas en canon sin personaje
  principal: rojo, azul, amarillo, ciano.** setup.md §13.6 dice
  "posponer", pero significa que las cuatro castas viven en el canon
  como cromatismo, no como gente. Para el Libro I (Sanderson-slow,
  inhabit) eso es perceptible. Como mínimo, dar **cara con voz** a un
  azul (juez / lectora menor / scribe en la Academia) y a un ciano
  (médico de palacio o profesor). Sin necesidad de arco; con presencia
  recurrente.
- **[POV económico] Yedra a 3 capítulos POV es el mínimo absoluto.** A
  ese nivel su arco se siente cuesta arriba al lector: aparece, decide,
  actúa. Si es deuteragonista de la subtrama A, considerar subir a 4-5
  POV chapters (ch 3, 10, 14, 19, 22). Si no, declararla francamente
  como personaje de presencia parcial y dejar a Vela como
  deuteragonista única.
- **[shadow leakage] Algunas master truths se revelan al lector demasiado
  pronto, no por Bruno.** Truth 4 (Blanco Falso) revealed in ch 15,
  Truth 7 (Portaluz coreografía) in ch 18. Bruno está en la Academia,
  ajeno. ¿Quién es el POV cuando estas verdades aterrizan? Si es Vela en
  esos capítulos, ok. Si es Bruno y la verdad llega vía exposición, eso
  es shadow leak — el escritor le pasa la verdad al lector por encima
  del POV. Revisar distribución de POV en ch 15 y ch 18 contra el plan.
- **[subtrama B] Portaluz tiene how_to_pay_off en ch 18 pero no tiene
  beat sheet de capítulo.** Su aparición pública es payoff del seed
  `portaluz-coreografia`. Sin beat sheet, no hay garantía de que la
  escena haga lo que el seed pide.

## CONSIDER

- **Nombres concretos (§13.5).** Cada cosa sin nombre — el reino entero,
  el monarca, la Iglesia, la Orden, la Academia, las aldeas — es un
  futuro stop al escribir. *Yedra*, *Vela* y *el Vitral* están bien;
  el resto necesitará sesión dedicada.
- **§13.1 — Bruno ↔ Portaluz infancia.** Si comparten infancia, ch 12
  (primera aparición pública del Portaluz desde POV Bruno) gana
  enorme peso. Si extraños, el Portaluz es figura política simétrica
  pero no íntima. La decisión cambia la cantidad de tensión emocional
  disponible en ch 12-18.
- **Portaluz physical / voice TODO.** Es una figura pública vista mucho.
  Necesita signo reconocible. Setup.md sugiere "hablar mirando al
  cielo, no a la cara" — converter eso en canon ya.
- **Calendar / lenguas todo TODO.** No bloqueante para escribir ch 1
  desde la aldea de Bruno, pero sí para escenas en la Cúpula con
  cerimonia litúrgica.

## What works

- **Sistema invertido declarado explícitamente** en `canon/magic.md`
  como decisión deliberada, no como omisión. Eso era MUST en la v3
  y se cerró con una declaración honesta — "este libro invierte la
  tercera ley". Eso permite que el critique no flaggee a Bruno como
  "magic sin escalada apex".
- **Coste del vacío resuelto en mecánica concreta** (borra recuerdos
  luminosos primero, deja los grises). Es una imagen visual + emocional
  + paralela al ordeño (los huecos quedan grises). El sistema mágico,
  el motor temático y la subtrama A comparten metáfora. Eso es trabajo
  poético serio.
- **El reloj convertido en motor causal**: "Bruno y la crisis son el
  mismo suceso." No es un cronómetro arbitrario; es el por qué Bruno
  pudo existir. Convierte una pregunta de plot ("¿por qué ahora?") en
  un nudo temático.
- **Vela cumple antagonist-with-true-thesis.** Su arco interno (lectora
  que canoniza nobles cocidos sabiendo lo que son) la convierte en una
  cómplice del sistema, no en una creyente ingenua. La Orden no es
  solo "los malos con razón"; Vela es alguien que ha pagado un precio
  moral por su tesis.
- **Subtrama A (Yedra / verde anula magenta) está estructurada
  honestamente:** tres toques con el principal, payoff en ch 22 (antes
  del clímax del Libro I), tema distinto del principal. Cumple las
  reglas de subplot weaving de `references/fantasy-beats.md`.
- **Diez seeds con distribución coherente:** 7 plants en act 1, payoffs
  agrupados en ch 22, 25, y Portaluz en ch 18. Ningún plant_in > payoff_in;
  ningún huérfano. Es la primera vez que estos checks pasan limpios.
- **Shadow timeline con overview denso + 7 master truths + slice
  capítulo-a-capítulo donde importa.** Eso es lo que la skill va a
  consultar en cada chapter — y aquí tiene de qué tirar.
- **Subtema temático integrado en la magia.** El motor moral ("¿vale
  una persona más allá de su uso?") no flota encima de la trama: la
  pregunta la fuerza la magia en cada uso (el ordeño la pregunta para
  los nobles; el coste de Bruno la pregunta para él).

---

## Anexo — Bugs / limitaciones de las skills expuestos por este caso

Al correr `audit_plan.py` contra este libro, salieron varios falsos
positivos / agujeros que merecen registro:

1. **Audit falla en "world premise has < 3 sentences"** — el premise está
   dentro de un blockquote para que se vea bonito en setup.md. El audit
   strip todas las líneas que empiezan por `>` como TODOs. Necesita
   distinguir "blockquote con TODO" de "blockquote con contenido".

2. **Audit falla en "magic source missing"** — el value tiene bold
   anidado (`un **aura interna** de color`). `setup_doc.fields()` se
   confunde con los `**` internos. Necesita parser más tolerante.

3. **Audit reporta cada arc como "missing decision point / lie / need /
   transformation"** — pero arcs.md sí los tiene. El regex de campo
   requiere `**Key:**` con dos puntos *fuera* del bold. Mis fields
   tienen la forma `**Decision point (which chapter):** ch 25` con el
   colon *dentro* del bold de cierre. Mismo bug que ya arreglamos en
   `find_str` pero no se replicó al regex de arcs.

4. **Audit reporta principales como "Portaluz (secundario, sin arc
   completo en Libro I)"** — porque el H2 lo capta literal. El parser
   de principales necesita reconocer y separar marcadores como
   "(secundario)" de los nombres.

5. **"Characters never mentioned in outline" reporta a TODOS los
   principales** — pero esto es porque la outline.md está TODO. El
   check debería detectar este caso (outline vacío) y degradar el
   warning, o consultar también shadow.md y arcs.md como evidencia de
   "mencionado en el plan".

6. **bootstrap_plan no detectó los principales del setup.md.** El
   regex espera `### Character N — Nombre` pero yo escribí
   `### Bruno`. El parser necesita aceptar ambos formatos o ser más
   tolerante.

7. **El skill `critique-plan` falta el paso de "convertir bible a
   layout"** — esta crítica acaba de hacerse a mano. Hace falta
   `ingest-bible` como skill / script con la conversión bible → setup +
   canon + plan skeletons.

8. **El skill no contempla seeds trans-libro.** Varios elementos de la
   biblia (la lectura, el complementario, el Blanco Falso) tienen
   payoff conceptual en Libro III pero seed en Libro I. Aquí los he
   declarado como seeds dentro del Libro I (payoff = ch 25, el
   descubrimiento), pero el coste narrativo real es en el Libro III.
   Necesitamos un tipo de seed `trans-book` con `payoff_in_book` además
   de `payoff_in_chapter`.

9. **El audit no comprueba "open decisions gating".** §13.2 y §13.3 son
   gating según setup.md. Sin un check específico de "open decisions
   marcadas gating sí", esa MUST hay que cogerla manualmente. Añadir
   parseo de `## Open decisions` con la convención `Gating: sí/no`.

10. **El audit no comprueba balance de payoffs por capítulo.** Nueve
    seeds pagan en ch 25 = un capítulo de cierre sobrecargado. Sería
    útil un check "máximo N payoffs por capítulo" con umbral
    configurable.

Estos son los huecos concretos que conviene cerrar en `audit_plan.py`
antes de la próxima auditoría. Los #1, #2, #3 son bugs de regex
rápidos. El #5, #9, #10 son features nuevos. El #7 (`ingest-bible`) y
el #8 (seeds trans-libro) son las dos cosas más grandes pendientes.
