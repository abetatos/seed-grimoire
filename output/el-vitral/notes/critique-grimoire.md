# Grimoire critique — el Vitral

**Verdict:** PASS

**Summary:** This is an unusually strong, late-stage grimoire. The magic
system is a genuine engine: a single unified operation ("tomar aura" at three
settings) generates the castes, the economy, the history, the antagonist's
mirror, and the protagonist's tragedy without a seam. The thematic question is
*forced* by the physics (a non-renewable color → "who keeps the last of it"),
not pasted on. The inverted-system declaration (§5) is honored everywhere: the
trilogy is a descent, the climax is cold and active, the world greys regardless.
Cast, decoys, loaded guns and master mysteries all clear or exceed the
series-scaled floors with fixed (not proposed) arcs. No MUST-fix exists: every
spine that downstream `book-setup`/`plan-book` must inherit is closed and
self-consistent. What remains is housekeeping (stale cross-refs, an
audit-parser blind spot on the second subplot, two un-named figures) — none of
it blocks Book I. The §14/§14b tables are complete (sow+payoff books, intro+
confirm books, Book-I presence), so `critique-plan` has a real contract to hold
each `shadow.md` against. Ship it to `book-setup`.

## MUST fix

- *(none)* — every gating decision in §16 is resolved (✅), the system is
  declared inverted (§5), each book block has a motor and an **active-decision**
  climax (Libro I "agrisa al tutor… su pecado original"; II "negarse a ser la
  función de nadie"; III "vacía el color… una última elección humana"), the
  clock is explicit and tied to the protagonist's existence (§13, "la sangría
  que mata al mundo cegó al verdugo que debía matarlo a él"), §14 is a full
  table with sow/payoff books and Book-I presence, and §14b enumerates 13
  mysteries with intro+confirm books. Nothing here breaks downstream.

## SHOULD fix

- **[cast — un-fixed identity details, not arcs]** The two back-half
  deuteragonists carry **`[FIJO]` arcs** (líder verde §8, cazador §9) — the
  thing the audit must check is committed. But both still lack **names**
  ("§9 El cazador… [FIJO · nombre por fijar]"; the líder verde is referred to
  only by function). The arcs survive a clean re-read; this is a draft-tag
  honesty issue, not a spine gap. Flagging per 3c so it isn't forgotten before
  prose: a deuteragonist who carries Libros II-III by function-only name is the
  thing most likely to drift in `plan-book`.

- **[subplots — audit parser undercounts; verify, don't trust the number]**
  `_audit-grimoire.md` reports "Subplots declared: **1** / with ≥3 contact
  points: **0**" and fires its thin-spine SHOULD. This is a **false negative**:
  §8 declares **two** structural subplots by design ("Dos hebras estructurales
  por diseño (FIJO)"), and **each** lists an explicit ≥3-contact-point ladder
  (§8 "≥3 puntos de contacto: 1. Libro I… 2. Libro II… 3. Libro III"; §8b
  "≥3 puntos de contacto con la principal: 1.… 2.… 3.…"). The parser misses
  §8b's separate `### 8b` header and the inline contact lists. Substantively the
  subplot floor (≥2 for a trilogy) is **met with distinct themes** ("la
  violencia hereda la violencia" vs "el celo honrado sirve al despojo", both
  distinct from Bruno's "persona vs función"). No content fix needed; consider a
  one-line parser/structure tweak so future audits don't keep flagging it.

## CONSIDER

- **[internal lint — stale cross-references]** Two pointers contradict their own
  now-closed sections: §3 line 75 "*(El clímax debe poner esto en manos de quien
  usa la magia — §12, **por cerrar**.)*" but §12 is `[FIJO en dirección]` with
  the climax closed; and §15 line 736 "Cerrado en estructura (tesis de cada uno
  **por afinar**)" while §9 declares both theses `[FIJO]` verbatim. Harmless, but
  they read as "still open" to a fresh planner. Reconcile the tags.

- **[premise — §1 still `[PROPUESTA]`]** The one-sentence idea (§1) is the only
  top-level section left tagged `[PROPUESTA]`, and its own note says the
  dependency "se levanta: lista para que el autor la fije en [FIJO]" and that the
  final sentence "debe capturar la **tensión del descenso** (gana mundo, pierde
  alma), no solo el concepto." The current sentence still sells the *concept*
  (the apex sink) rather than the *descent's cost*. Optional polish, but it's the
  logline `book-setup` will quote.

- **[Portaluz — declared, deliberately near-decoration; confirm the plant]** The
  Portaluz is honestly degraded to "mito, no hombre" (§9, §16.12-14) and §14
  gives it a Book-I sow (the coin) and a Book-III payoff (the lie confirmed), so
  it is *not* an un-planted decoration — it clears the rule. Just confirm in
  `plan-book` that the Book-I "moneda" plant actually lands on the page; a loaded
  gun whose only plant is a single prop is the easiest one to lose in drafting.

## What works

- **Magic as one engine.** Sumidero / drenaje / transformador unified as a single
  operation at three settings (§6) is the rare system where the economy
  (§7 vidrio-banca), the history (§10 three ages), the antagonist (§9 Corona as
  carne-vs-vidrio mirror) and the protagonist's tragedy all fall out of the
  *same* physics. No bolt-ons.

- **The thematic question is forced, not pasted.** "¿Puede conservarse un mundo
  sostenido por el despojo?" is a *consequence* of color being non-renewable
  (§10 corolario duro), so the theme and the worldbuilding are the same fact.

- **The inversion is honored to the climax.** §5 declares erosion-not-escalation,
  and §12 pays it: Bruno "gana mundo y pierde alma en el mismo gesto," the climax
  is "frío y trágico, NO mesiánico," the world greys regardless. The two-track
  erosion (visible moral / hidden mnemonic, §12) cleanly resolves what would
  otherwise be a clash between "imperceptible cost" (§9) and "arc of erosion."

- **The attrition ledger exists and balances (§12b).** "Hereda / muere / entra"
  per book, with an explicit "refill comprobado" — exactly the bookkeeping that
  proves the cast survives to Book III (Mauro→cazador as rastreador-mirror; the
  vínculo's "destruye a quien lo ve" pattern closes in II, not arrastrado).

- **Decoys named on purpose.** The Iglesia-as-public-decoy / Corona-as-real-
  parasite split (§2, §9), plus the "dos falsos salvadores" (loud Portaluz / quiet
  Bruno), are deliberate misdirection the trilogy will pay back — the audit counts
  8.

- **Antagonist theses are genuinely arguable.** Corona's "El orden es la vida"
  (concentrar = preservar) and the cazador's "matar a la causa salva al mundo"
  are worldviews that, in a different light, would be correct — not stock evil.

## Cross-references to plan

- A Book-I plan directory exists (`output/el-vitral/book-01/` with `plan/`,
  `canon/`, `notes/`). This critique did **not** audit it — that is
  `critique-plan`'s job, which per SKILL step 6 should be re-run now that the
  grimoire PASSes, holding `book-01/plan/shadow.md` to the §14b mysteries flagged
  `Introducido-en: Libro I` (#1, #2, #3, #5, #6, #7, #12, #13) and the §14 guns
  that must appear in Book I.
