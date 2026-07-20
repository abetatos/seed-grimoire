---
name: calibrate-style
description: Distill the author's own hand edits of a locked chapter into named, generalized style rules — the POSITIVE voice model, learned from a before/after delta instead of from exemplars the writer would photocopy. Runs scripts/calibrate_diff.py (git HEAD vs working tree, sentence-aligned), clusters the rewrites into recurring KINDS of edit, and — confirming each with the author via AskUserQuestion — routes each rule to its home: a cadence/craft rule to notes/style-rules.md, a countable tic to prose-lint.toml [[extra_patterns]], a recalibrated ceiling to [caps]. Never quotes more than 3 consecutive words of the prose (anti-photocopy). Use this after the author has hand-edited a chapter and wants the lesson captured, or says "learn from my edits to chapter N".
---

# calibrate-style

You are running the **calibrate-style** skill. The author has hand-edited a
chapter that was already drafted (and usually locked). Those edits are the
**voice target**, expressed as a *delta* — what the author reached for and what
they cut. Your job is to turn that delta into **named, generalized rules** the
pipeline can carry forward, WITHOUT ever pasting the author's prose back into a
rule (a rule that quotes the sentence teaches photocopying, not craft).

This is the **positive** counterpart to the deterministic tic auditor: `lint_prose`
counts what to avoid; this learns what to reach for, from the author's own hand.
There are no exemplars in this project by design (the author disabled them) — the
voice lives in rules + `notes/voice-spine.md`, and this skill is how a hand edit
becomes one of those rules.

**Stays in the main thread.** The input is a compact calibration file, not a
chapter's worth of prose, and every rule is author-confirmed — so unlike the
critique/scribe skills this does **not** dispatch to a subagent. Run it in the
conversation with the author.

## Steps

1. **Generate the delta.** Run the aligner (writes
   `notes/_calibration-chNN.md`):

   ```bash
   python scripts/calibrate_diff.py --series-slug <slug> --book-number <N> --chapter <M>
   ```

   It diffs the committed chapter (`git show HEAD:chapters/MM.md`) against the
   working tree. If the chapter was never committed before the edits (no HEAD
   version), the script errors — ask the author for the two versions and pass
   them with `--before <file> --after <file>` instead.

2. **Read `notes/_calibration-chNN.md`.** It carries: the word/tic-count deltas
   (chapter-wide), the **rewritten pairs** (before → after, with per-pair
   similarity and measurable delta), the pure cuts, and the pure additions. The
   rewrites are the gold; the cuts tell you what the author no longer tolerates;
   the additions tell you what they now want more of.

3. **Cluster the edits into recurring KINDS.** Do not treat each pair as its own
   rule. Look across the pairs for a repeated *move*: e.g. "explanatory similes
   collapsed into a plain verb" (watch the `similes N→0` deltas), "long sentence
   on an emotional peak cut to a short one" (word delta down on a charged beat),
   "filter verb removed to put the sensation directly on the page"
   (`filtro/1000` down), "abstract noun swapped for a concrete object", "a
   cadence change — clause order, rhythm". A cluster needs ≥2 pairs pointing the
   same way; a lone edit is a one-off, not a rule (say so and skip it).

4. **Name and generalize each cluster into a rule.** Write the rule as an
   instruction the writer can apply to prose it has not seen yet — a mechanism,
   not a citation. **Never quote more than 3 consecutive words of the author's
   prose** in the rule text; if you need an example, invent a fresh tiny one in
   the same register. Prefer the shape "*When X, do Y (not Z)*."

5. **Route each rule to its home, and confirm with the author** via
   `AskUserQuestion` (one question per cluster; options are the destination, with
   your recommended one first and labeled "(Recommended)"). The three homes:
   - **Cadence / craft rule** (a judgment the auditor can't count) →
     `notes/style-rules.md`, appended under a `## Cadencia` heading (create it if
     absent), in the file's format `- (YYYY-MM-DD, ch N) rule text`. `close-act`
     later folds it into `style.md`.
   - **A newly countable tic** (a phrase form, a word shape, an opener the author
     kept cutting that a regex CAN catch) → a `[[extra_patterns]]` entry in
     `notes/prose-lint.toml` (`name`, `pattern`, `scope = "chapter"`), so it is
     counted every future chapter instead of re-hunted by eye.
   - **A recalibrated ceiling** (the author's edits show an existing cap is too
     loose or too tight) → adjust the value under `[caps]` in
     `notes/prose-lint.toml`, and note in the confirmation why the corpus moved.

6. **Apply the confirmed rules** with Edit/Write to the routed file(s). Re-run
   `python scripts/lint_prose.py --series-slug <slug> --book-number <N> --chapter <M>`
   if you touched the toml, to confirm the new pattern/cap parses and counts.

7. **Report.** List each rule, its home, and one line on the cluster it came
   from (no prose quotes). Note any lone edits you skipped as one-offs.

## Hard rules

- **Anti-photocopy is absolute.** A rule never contains >3 consecutive words of
  the author's prose. The output is craft the writer generalizes, not a fragment
  it pattern-matches. This is why exemplars were disabled; do not smuggle them
  back in as "example" rules.
- **A rule needs ≥2 pairs.** One edit is taste on one sentence, not a pattern.
  Skip lone edits; say you skipped them.
- **Author confirms every rule and its home.** Propose via `AskUserQuestion`;
  never write a rule the author did not approve. The author may redirect a rule's
  home or reject it outright.
- **Regexable → toml; judgment → style-rules.** If a machine can count it, it
  belongs in `prose-lint.toml` where it is counted, not in a prose rule the critic
  must remember to check. Only genuinely uncountable craft goes to `style-rules.md`.
- **Never touch `plan/seeds.md` / `plan/shadow.md`** (protected) or the chapter
  prose itself — this skill reads the edits, it does not make them.
