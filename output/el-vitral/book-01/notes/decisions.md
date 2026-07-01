# Decisions — El Apagado (Libro I)

> Book-level binding choices. **Authoritative and committed.** `plan-book` and
> every regeneration MUST honor these; a re-plan/`--force` rebuild may NOT
> silently overwrite them. (Per-chapter gate decisions live in `decisions-chNN.md`.)

## 2026-06-24 — book-setup

- **Largo y forma.** 25 capítulos · 8000-12000 palabras/cap · ~250k. Actos:
  1 (1-7) · 2 (8-18, **midpoint ch 13**) · 3 (19-25).
- **Midpoint (ch 13) = "el refugio es escaparate".** Altaluz, que parecía
  salvación, se invierte: la luz que no deja nada en sombra; la mirada del tutor
  **mide, no acompaña**. Ser visto empieza a ser ser expuesto.
- **POV múltiple, abierto.** Default Bruno (tercera cercana, pasado), pero se
  permiten otros POVs **según fluya la historia** (puede aparecer un personaje
  importante aún no definido). **Regla dura:** un POV ajeno NUNCA confirma un
  `SHADOW-TRUTH` por encima de su `Reveal cap` (proteger la naturaleza de Bruno =
  cap `suspected`, y el linaje = no se confirma hasta Libro II).
  - **RECONCILIADO con el grimorio §12** (antes era un override). El grimorio se
    actualizó a **"POV — eje único, coro libre (FIJO)"**: Bruno ancla/dominante, otros
    POV permitidos cuando la historia lo pida (lo decide `plan-book`). El plan ya
    **coincide**; ya no hay contradicción que `critique-plan` pueda marcar.

## 2026-06-24 — actualización del grimorio (v5, sesión tarde) propagada al plan

- **Reparto con nombre [FIJO]:** el tutor = **Mauro**; el cazador = **Cándido**; el
  líder verde = **Tilo**. (Renombrados en todo el plan.)
- **Want de Mauro corregido:** **expiación, NO rescate** — busca la cura para deshacer
  su propio crimen (devolver el yo a los que agrisó), sabiendo que el apagado es imparable.
- **Cándido sube a deuteragonista-némesis** (arco [FIJO], §8b): el *verdugo competente*,
  espejo personal del despojo (*el celo honrado sirve al despojo*); nunca despierta.
- **DOS hebras estructurales** (no una): §8 revolución verde (espejo colectivo) + §8b la
  caza/cribado (espejo personal). Ambas sembradas en el Libro I.
- **Siembra §14 nueva:** *El cazador y el casi-test* → seed `el-cazador-casi-test`
  (Cándido ronda Altaluz; near-miss del complementario). Obligatoria, sembrada en Libro I.
- **`rastro-del-padre`:** seed que abre el hilo de búsqueda del Libro II (carrier de
  `el-padre-era-negro`). Planta en cap 19, eco 25.
- **§11 convoy de la cosecha:** ruta fija Solio/Cúpula → provincias, cadencia ritual,
  lleva el prisma (lee+cosecha), se lleva a los jóvenes. (Reflejado en canon/world.md.)

## 2026-06-29 — plan-chapter (cap 1)

- **Mauro llega a Vega Parda CON el convoy** (no como forastero suelto). Su
  presencia es ajena a Bruno y previa al destello (vino con el aparato del carro);
  el destello solo le **engancha la mirada**. Técnica **presencia≠mirada** para
  evitar deus ex machina. **Guarda dura:** su pasado de ex-Lector NO se telegrafía
  en el Libro I (reveal del II) — se escribe como un gris más de la logística, sin
  liturgia. (El cap 2 lo asume: se queda "con el pretexto de esperar el carro".)

## 2026-07-01 — plan-chapter (cap 3)

- **Olmo (POV verde, caps 3 y 14) — identidad [durable]:** hombre joven-adulto,
  **verde delgado/anodino** (el prisma no lo lleva: ya no "brilla" como los críos).
  El convoy del cap 3 se lleva a un **hermano/a menor** que estaba a su cargo → su
  agravio es **protector + culpa**. Queda vivo y móvil para el cap 14 (su rencor
  madura cuando el carro vuelve). Rima en sordina con el camuflaje-por-apagado de
  Bruno **sin** duplicarlo (verde no marrón; adulto no niño).
- **`el-complementario-verde-magenta` — plant en aldeano ANÓNIMO, no en Tilo.** La
  orden del magenta que "no prende" la sufre un verde cualquiera; **Tilo solo
  presencia**. Guarda: no telegrafiar a Tilo como "el líder" en el Libro I.

## 2026-07-01 — corrección de estilo (prosa cansina)

- **Diagnóstico.** El estilo se volvió repetitivo/plano por un vaivén del `style.md`:
  el commit `fcda0ce` cambió la filosofía gobernante de **"engine before the brakes /
  write rich"** (la buena, era v3 `8c1fc11`) a **"pane of glass / underplay / distrust
  the beautiful line"** (frenos primero → gris). El de-Sandersonize (`659f38c`) había
  quitado el norte concreto y lo dejó en etiquetas abstractas.
- **Lo largo se queda [FIJO].** El autor quiere la extensión/demora ("alargar me gusta,
  se toma el tiempo, está a posta"). El problema NO era el relleno ni el `expand-chapter`
  — es el **registro**. No tocar la longitud ni el pipeline por esto.
- **Norte de prosa sin nombrar a Sanderson [FIJO]:** mecanismo **"constelación de
  tradición"** — apuntar a *la escuela moderna del hard-magic* (no a la persona) +
  6 rasgos de oficio concretos. Implementado como sección `## The lodestar` en
  `style.md` y en `references/style.md`. Nunca nombrar un autor vivo/protegido en los
  ficheros.
- **Tics con cupo [FIJO]:** la antítesis "no X, sino Y" (1×/escena), la repetición-
  como-énfasis (1×/cap), el motivo/coinage repetido sin info nueva, y "con las dos
  manos". Codificado en `## Sentence & rhythm`.
- **Símbolo central = el TELAR, no el hojalatero [durable].** El telar con el hilo
  verde que se apaga en la trama es "el ejemplo perfecto para un libro de colores".
  Cuando se reescriba el cap 1 bajo la guía nueva, anclar en el telar (ya presente
  como símbolo materno en el cap actual) en vez del oficio de estaño de la v3.

## Heredado del grimorio (FIJO — no reabrir en el plan)

- Magia: física unificada (tomar aura a 3 ajustes), dos polos (Bruno/Portaluz),
  drenaje por vidrio, leyes §4, fondo común finito → apagado **imparable** (§3-§7, §10).
- Bruno: Blanco×Negro, sumidero apex; wound/want/need/lie; coste = erosión (oculta
  en Libro I); depreda hacia arriba (amar = peligro) (§9).
- Antagonistas: **Iglesia = decoy** (exterminar la cura + monopolio del vidrio +
  Portaluz como santo) · **Corona = parásito real**, espejo de Bruno (§9, §16).
- Estructura Libro I: motor *sobrevivir sin ser visto*; clímax *primer drenaje
  deliberado agrisa al tutor*; all-is-lost *ser visto = ser cazado* (§12).
- Subtrama: revolución verde, sembrada en Libro I (el convoy se lleva a los jóvenes) (§8).
- Portaluz = **mito/propaganda**, no personaje-eje (§9).
- Tono: slow-immersion, terrenal, tragedia sorda; coste **nunca en cifras**.
