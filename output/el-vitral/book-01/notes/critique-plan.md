# Plan critique — El Apagado (Libro I, *el Vitral*)

**Verdict:** REJECT

**Summary:** This is a strong, unusually disciplined plan — a tragic
slow-immersion descent with a complete hard-magic system, a genuine
midpoint inversion, an intrinsic (non-contrived) climax trigger, and a
real emotional spine (three resolution-image seeds). The shadow layer
tells a materially different story than the outline. But it ships with one
load-bearing structural break: the throughline that carries the
tutor-measures-not-loves arc and the *entire* midpoint reveal points to a
seed that **does not exist** in `seeds.md`. As written, the midpoint truth
`altaluz-es-escaparate` has no real reveal path, and ~15 outline/shadow/arc
references hang on a phantom id. That alone is a MUST-fix → REJECT. A
cluster of back-third thinness (Act-3 chapters running on "implícito"
seeds, a near-identical 19-22 siege run, a 2-touchpoint green subplot) sits
below it as SHOULD-level work.

> **Tooling caveat (not plan defects):** the deterministic audit produced
> two false positives the author should NOT chase. (1) The "Invalid
> entries / missing payoff_in" list (11 seeds) is the parser failing to
> read `Payoff in: Libro II/III` — every one of those seeds *does* declare a
> payoff, just into a later book (correct for a trilogy opener). (2) The
> "Truths tagging a non-existent mystery" list (8 truths) is an audit bug:
> the §14b table in `grimoire.md` parses to empty for the script (hence it
> also reports "§14b mysteries: all carried ✓" in the same run — a
> contradiction only possible if `myst_names` is empty). The §14b names in
> `shadow.md` (`La naturaleza de Bruno`, `El tutor agrisado`, …) match the
> grimoire prose by eye. Do not rename them.

## MUST fix

- **[consistency / seeds — phantom carrier `el-tutor-tiene-agenda`]** — The
  id `el-tutor-tiene-agenda` is referenced **15 times** (outline ch2/4/6/9/
  11/13/17, shadow Act-1 overview + ch4/6/11/13/17, arcs Mauro waypoint) and
  is the **only** `Revealed-by:` carrier of the midpoint truth
  `altaluz-es-escaparate` (`shadow.md:135`). But there is **no
  `## SEED: el-tutor-tiene-agenda`** in `seeds.md` (defined seeds: the 14
  listed at `seeds.md:15-261`). The spine of the book's central irony — the
  tutor's gaze *measures, not accompanies* — and the entire midpoint reveal
  therefore have no tracked plant/echo schedule and no real reveal path. →
  **Direction:** add a `## SEED: el-tutor-tiene-agenda` to `seeds.md` with
  `Plant in: 4`, `Echo in: 6, 9, 11, 17`, `Payoff in: 13 (vuelco) → Libro
  II`, a `Dose` capping it to oblique touches (it must never confess), and a
  reveal cap consistent with `altaluz-es-escaparate` (`suspected`). It is
  arguably a *resolution-type* carrier of the tutor arc — give it the
  treatment its load deserves. (Brings the seed count to 15, also clearing
  the trilogy-opener leanness note.)

- **[seeds / reveal path — `altaluz-es-escaparate` has no valid carrier]** —
  Because its sole `Revealed-by: el-tutor-tiene-agenda` (`shadow.md:135`) is
  the phantom above, this midpoint truth currently *cannot* reach the reader
  through any existing seed. It does carry `Confirm in: 13`, so it is not
  literally orphaned per the skill's "neither carrier nor Confirm-in" bar —
  but a midpoint inversion that lands on a *manual confirm only*, with its
  one named carrier missing, is exactly the reveal-path weakness the skill
  warns against. → **Direction:** once the seed exists, this resolves
  automatically; verify `el-tutor-tiene-agenda` appears in `seeds.md` and
  re-run `audit_plan.py` (the audit currently lists this truth under
  "Truths citing unknown carrier seeds").

## SHOULD fix

- **[pacing — Act-3 siege chapters run "more of the same" (19-22)]** —
  Chapters 19 ("El cerco"), 20 ("Sin salida"), 21 ("El pozo pide"), 22 ("El
  borde") are four consecutive Bruno-POV Altaluz chapters whose function is
  the same vector — *the snare tightens* — with Cándido echoing in
  19/20/21 and the pozo echoing in 21/22. The escalation is real but the
  beat shapes rhyme; over 8-12k words each this risks a flat 40k-word
  stretch before the climax. → Give each a distinct *kind* of pressure (e.g.
  19 = the father-trace opens a forward door; 20 = the intrinsic trap
  springs; 21 = the body's hunger becomes the threat; 22 = Mauro's choice),
  and consider folding 20 and 21 if they can't be differentiated.

- **[seeds — back-third runs on untracked "implícito" seeds]** — The audit
  flags ch 13, 17, 18, 20, 22 as having no tagged plant/echo/payoff. 17 and
  18 list only `el-tutor-tiene-agenda`(echo) / `naturaleza-de-bruno`
  (`outline.md:461-462, 485`) — the former phantom, the latter an
  un-defined-as-seed truth-id used as a seed tag throughout. The all-is-lost
  (18) and the two pre-climax chapters (20, 22) carry their weight on
  *implied* seeds, so nothing in the catalog tracks how they land. →
  Promote the recurring truth-tags actually used as seeds
  (`naturaleza-de-bruno`, `el-negro-y-el-drenaje`) to real `## SEED:`
  entries, or tag these chapters with the existing seeds they genuinely
  echo (`el-pozo-que-pide` in 18/20/22, `el-cazador-casi-test` in 18).

- **[subplots — green thread has only 2 in-book touchpoints]** — Subplot A
  (la revolución verde) touches the main plot at ch3 (plant) and ch14 (echo)
  only; ch14's POV is hedged "Olmo (o Bruno, si fluye)" (`outline.md:374`),
  so even the second touch is soft. The skill wants ≥3 touchpoints. It is
  deliberately a saga subplot (payoff in II-III, declared `[FIJO §8]`), but
  in *this* book it barely breathes. → Add a third concrete contact — e.g.
  let the convoy's harvest visibly feed Altaluz's un-fading vitral (the plan
  already gestures at this in ch7 texture and ch14 "lo que se cosecha abajo
  alimenta la luz de arriba") and *tag* it as an `el-convoy-jovenes` /
  `el-complementario-verde-magenta` echo on a Bruno chapter.

- **[seeds — `el-tutor-agrisado` reveal-path leans on the phantom indirectly]**
  — `el-tutor-agrisado` (`shadow.md:119`) is `Revealed-by: el-pozo-que-pide,
  ojos-que-no-suben` — both real, good. But the *meaning* of the
  agrisamiento (that the tutor who measured is the one Bruno drains) is built
  entirely on the `el-tutor-tiene-agenda` throughline. If the phantom seed is
  not added, the climax's gut-punch is under-planted even though its two
  resolution seeds fire. → Resolves with the MUST; flagged so it isn't
  treated as independently clean.

## CONSIDER

- **[POV economy — Olmo carries <3 chapters]** — Olmo is POV for ch3 and
  only *maybe* ch14 (`outline.md:92, 374`; arcs note "y posible eco en 14",
  `arcs.md:112-114`). A POV used once (or 1.5×) is thin per the skill's
  <3-chapter bar. It earns its place by showing the harvest from inside a
  green family — what Bruno can't see — so cutting it would cost the
  subplot. → Either commit ch14 firmly to Olmo (making it a clean 2-chapter
  POV with a purpose) or accept the single-use and note it as intentional.

- **[worldbuilding economy — Solio / Catedral del Prisma / Cúpula named, not
  entered]** — These FIJO places (`setup.md` Geography) appear only as
  distant referents in Book I (correct — their payoff is Book III). No fix
  needed; flagged only so the author confirms the *glimpse* is planned (ch1
  convoy "baja de Solio", a moneda-del-santo gesture) rather than fully
  absent.

- **[Cándido — zero decision by design]** — Cándido has "ninguna decisión de
  cambio" (`arcs.md:94`); his arc is the tightening clock. This is declared
  and thematically load-bearing (the flat, competent zealot as the cleanest
  face of the Vitral). Acceptable — noted only because a flat principal will
  read as under-arced to a critic who hasn't seen the design rationale.

## What works

- **Intrinsic climax trigger.** The snare closes via Cándido's
  *already-seeded* method (`el-cazador-casi-test`, plant ch10, near-miss
  ch16, trigger ch20) — "no caballo, ni tormenta" (`outline.md:536`). This
  is exactly the trigger soundness the skill demands; most plans fail here.
- **Real midpoint inversion.** Ch13 overturns something the reader
  *believed* (the refuge is the showcase; being seen = being exposed), not a
  plot turn dressed as a reveal. The shadow overview genuinely diverges from
  the outline.
- **Emotional spine present.** Three resolution-image seeds
  (`ojos-que-no-suben`, `el-pozo-que-pide`, `el-telar-hilo-verde`) give the
  book a felt arc that *transforms* rather than merely concludes — well
  above the ≥2 floor.
- **Complete, costed magic.** Source / mechanic / 3 costs / 4 hard limits /
  thematic question / three escalation tiers, with the apex (deliberate
  drenaje) reserved for the climax and the cost (memory erosion) deliberately
  imperceptible in Book I. The "coste nunca en cifras" constraint protects
  the tragedy from turning into a stat-sheet.
- **Distinct arc engines.** Bruno (lie: "valgo por lo que puedo hacer") and
  Mauro (lie: "puedo redimir lo que ayudé a destruir") argue different
  things and collide in one act; the subplot themes (la violencia hereda la
  violencia / el celo honrado sirve al despojo) are each distinct from the
  main theme.
- **Trilogy seeding is conscious.** Plants weighted to Act 1, payoffs
  deliberately deferred to II-III with explicit reveal caps (`sensed` /
  `suspected`) and a clean Book-II opener (`rastro-del-padre`, the father
  thread).
