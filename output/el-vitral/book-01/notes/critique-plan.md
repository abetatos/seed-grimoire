# Plan critique — El Apagado (el Vitral · Libro I)

**Verdict:** REJECT

**Summary:** This is, at the craft level, a strong and unusually disciplined
trilogy-opener plan: a genuinely hidden shadow layer (not the outline in code),
a tragic climax whose decision rests on capabilities planted from ch1 ("no
controla bien el caudal," the pozo, the blanco frío), an emotional spine built
on two resolution-image seeds (la-mirada-que-sube, recarga-vaciando), correct
plant-heavy / payoff-deferred distribution for a book 1, and texture beats in
every chapter. It does **not** PASS for one hard reason: the tutor is named
**Tobías** across the entire plan, but the series grimoire fixes his name as
**Mauro** `[FIJO · nombre: Mauro]` — a binding, deliberately-punned name the
plan silently discards. That is a contract break against the grimoire and must
be reconciled before any prose. A handful of seed-field inconsistencies and one
broken audit check round out the list. None of the other issues is fatal; fix
the name and the seed fields and this plan is ready.

## MUST fix

- **[consistency — tutor name vs grimoire]** — The grimoire fixes the mentor as
  **Mauro**: `### Mauro — el tutor [FIJO · nombre: Mauro]` and again `(Nombre:
  **Mauro** [FIJO]...)`, with an intentional pun (*mauro = oscuro/pardo*, rhyming
  in sordina with Bruno). The plan names him **Tobías** in `setup.md`, `arcs.md`
  ("## Maestro Tobías"), `canon/characters.md` ("## Maestro Tobías"),
  `shadow.md`, `outline.md` (every Act-1/2/3 beat) and `decisions.md`. Zero
  occurrences of "Mauro" anywhere in `book-01/`. `setup.md` even records the name
  as `> TODO: libre`, but the grimoire had already closed it. → Either rename the
  tutor to **Mauro** everywhere in the plan (recommended — it honors a [FIJO] and
  keeps the Bruno/Mauro sound-pun), or, if the author truly wants "Tobías," amend
  grimoire §9/§14b to release the [FIJO] first. Do not leave the plan and
  grimoire disagreeing on a principal's name.

## SHOULD fix

- **[seeds — payoff field inconsistency: el-polvo-gris]** — Its `**Payoff in:**`
  reads "Libro II (Bruno agrisa a quien ama, all-is-lost §12)", but the seed's
  own `Echo in:` lists **23 (Tobías agrisado — el mismo polvo, ahora por mano de
  Bruno)**, the `Dose` says "el clímax (23) lo pone en su propia mano sobre
  Tobías," outline ch23 lists "payoff ... el-polvo-gris (sobre Tobías)," and the
  seeds-file global note states "El único payoff dentro del Libro I es el clímax
  (23): la-mirada-que-sube y el-polvo-gris caen sobre Tobías." So this seed pays
  off **in this book at ch23** and also echoes forward — but the payoff field
  says Libro II only. → Set `Payoff in:` to "23 (Tobías agrisado) → eco Libro III
  (grises restaurados)" so the field matches the four other places that already
  treat ch23 as its payoff. (This is also why the mechanical audit can't see a
  Book-I payoff for it.)

- **[seeds — undefined seed: el-portaluz-reverso]** — `Echo in:` = "según trama
  (rol narrativo POR DECIDIR — no asumir señuelo)", `Payoff in:` = "por definir",
  `How to pay off:` = "por definir". A seed with no echo schedule and no payoff
  target is not yet a seed — it is a note-to-self. It will never get a `Realized`
  touch-log and the writer has no instruction for it past the ch3 iconography. →
  Either collapse it into `el-santo-prometido` (they already "comparten soporte
  físico (la moneda)") as a single half-line of texture, or commit a minimal
  Book-I plant + at least one defined later-book payoff. Leaving "POR DECIDIR" in
  a NEVER-compress file invites it to rot.

- **[seeds — trans-book seeds read as "invalid" to the mechanical audit]** — 16
  of 18 seeds have a prose `Payoff in:` of "Libro II/III", which `_parse_chapter`
  returns as `None`, so `audit_plan.py` lists them all as "missing payoff_in".
  For a trilogy opener that is *by design* (the seeds header says so), so this is
  not a real defect — but it means the deterministic audit cannot certify seed
  validity for this book, and a future reader of the audit will mistake the noise
  for 16 broken seeds. → Low-stakes, but worth a convention: give cross-book
  seeds a sentinel the parser accepts (e.g. a numeric in-book *anchor* echo plus a
  `Cross-book payoff:` free-text field), or teach `audit_plan.py` to treat a
  "Libro N" payoff as valid-deferred rather than missing. Until then, treat the
  16 "missing payoff_in" lines in `_audit-plan.md` as **expected noise**, not
  MUST-fixes.

- **[stale note — POV override marked PENDIENTE but already reconciled]** — Both
  `setup.md` (§POV note) and `decisions.md` say the multi-POV decision is an
  "OVERRIDE del grimorio §12" with action "PENDIENTE: actualizar grimorio §12...
  o critique lo marcará como contradicción." But grimoire §12 has *already* been
  updated: it now reads "La claustrofobia... pasa a ser el **default** del que el
  plan se separa con motivo. No es un olvido: es la decisión revisada (sesión
  2026-06-24)." There is no live contradiction. → Clear the "PENDIENTE" wording
  in `decisions.md`/`setup.md` so a later pass doesn't re-flag a closed item.

## CONSIDER

- **[audit tooling — §14b cross-reference is reading the wrong column]** — Not a
  plan defect, but it makes `_audit-plan.md` actively misleading. `audit_plan.py`
  uses `r[0]` for both the §14 and §14b tables, but the §14b table has a leading
  `#` column (`| 1 | **La naturaleza de Bruno** | ...`), so it keys mysteries on
  "1","2",... instead of their names. Result: the audit's "Truths tagging a
  non-existent mystery" list (8 entries) is **entirely false** — the shadow's
  `**Mystery:**` tags ("La naturaleza de Bruno," "El coste del don," etc.) do
  match §14b names; and "all carried ✓" / `_book_in_cell` is checked against the
  "Verdad real" column, not "Introducido-en", so that pass is also unreliable. →
  Fix the §14b parse to use the name column (index 1) and the "Introducido-en"
  column for the book check. The plan's shadow tags are correct as written.

- **[characters — physical specifics still TODO on principals]** — Bruno's 3rd
  physical detail, and Tobías/Mauro's and Vela's full physical triplets, are
  `> TODO:` in `canon/characters.md`. The grimoire deliberately left these "libre
  para escribir," so this is legitimately deferred — but lock at least one
  concrete non-cliché detail per principal before the chapter that introduces
  them, or chapter 1/4/10 will improvise generic faces.

- **[historical weight — Edad I/II declared, only lightly echoed in Book I]** —
  The three Ages are rich canon, but in Book I only the cribado (Edad II) gets an
  on-page echo (ch2, ch12 doctrine). Edad I (absorbedores vivos) is grimoire
  §14b #11, explicitly "Introducido-en Libro II," so its silence here is correct,
  not decoration. Noting only so it isn't mistaken for a dropped thread.

## What works

- **Shadow is genuinely hidden, not the outline in code.** The Overview reveals a
  different story (mirar=usar; the Church's "Mal" *is* the cure it exterminates;
  drenaje and the Negro are one operation) that the visible outline never states.
  This is the single hardest thing to get right and it is right.
- **The climax decision is fully pre-planted.** ch23 rests on "no controla bien
  el caudal" (canon/§6, ch22), the pozo that "pide" (ch5/11/17/20/22), and the
  blanco frío — no tool appears for the first time at the climax. And the climax
  pays off a major in-book seed (la-mirada-que-sube → "ojos que suben pero ya no
  ven"), so it does not float.
- **Emotional spine is built, not bolted on.** Two `Resolution image` seeds
  (la-mirada-que-sube, recarga-vaciando) give the book an inversion to land, so
  it resolves rather than merely concludes — exactly the spine the skill asks for.
- **Trigger soundness on the one in-book event payoff is intrinsic.** ch23's
  agrisamiento fires from Vela's cerco + Bruno's own uncontrolled caudal, named
  explicitly as "Trigger intrínseco... nunca un actor que llega solo a disparar."
  No contrivance reserved for writing time.
- **Pacing alternates load correctly.** POV relays (Saúl 3/14, Tobías 6, Vela
  10/16) sit between Bruno's interior chapters; no two action chapters stack
  without a quiet beat; texture-beat budget present in all 25 chapters; act 1 is
  a true slow-immersion inhabitation.
- **Distinct, non-redundant arcs.** Bruno (lie: "valgo por lo que puedo hacer"),
  Mauro (lie: "puedo redimir lo que ayudé a destruir"), Bras (lie: "cualquier
  arma está justificada") carry three different theses; the subplot's theme (la
  violencia hereda la violencia) differs from the main (persona vs función).
