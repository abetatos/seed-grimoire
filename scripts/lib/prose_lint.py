"""Deterministic prose-tic auditor — density of the model's richness-levers.

``style.md`` names the **explanatory / epic simile** ("A, como/igual que B
que…") as the model's number-one richness-lever and its clearest tell. But a
prose rule the model can rationalise past is weak; a counter is not. This turns
the simile tic into a **counted, per-scene finding** so ``critique-chapter`` can
gate on a script instead of a careful read — the same "invariants in code, not
prose" move as ``lint.py``, applied to prose texture instead of on-disk state.

Findings are WARN-level by design: the check flags a scene *for a look*, it does
not block the pipeline. The signal is fuzzy (Spanish ``como`` is overloaded), so
a hard gate would cost more in false positives than it saves. The value is
turning "the prose feels simile-heavy" into "scene 2: 6.0 similes / 1000 words,
here they are."
"""

from __future__ import annotations

import difflib
import re
import tomllib
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from . import seeds as seeds_mod
from .wordcount import count_words, prose_text

WARN = "WARN"

# The whole lexical layer of this auditor is per-language: the stopword set,
# the simile shapes ("como si", "igual que", "cual"), the -mente adverb rule,
# the gerund openings, the word/sentence regexes. Run against a book written
# in another language it would not error — it would count WRONG and report
# clean, which is worse. So the auditor refuses any book whose declared prose
# language has no lexical layer here. To support a new language, add its
# stopwords + tic regexes and register the code below.
SUPPORTED_LANGUAGES = {"es"}


class UnsupportedLanguageError(ValueError):
    """The book's declared prose language has no lexical layer in this module."""


def require_supported_language(paths) -> str:
    """Return the book's prose language code, or raise loudly when this
    module's per-language lexicon (stopwords, tic regexes) does not cover it.
    Called by ``load_config`` so every book-scoped entry point is gated."""
    from . import setup_doc  # local: keep module deps flat
    declared = setup_doc.language(setup_doc.load(paths.setup_md)).strip().lower()
    m = re.match(r"[a-z]{2,3}\b", declared)
    code = m.group(0) if m else declared
    if code not in SUPPORTED_LANGUAGES:
        raise UnsupportedLanguageError(
            f"prose_lint has no lexical layer for language '{declared}' "
            f"(setup.md 'Idioma de escritura'); supported: "
            f"{', '.join(sorted(SUPPORTED_LANGUAGES))}. Counting another "
            f"language with the es lexicon would report clean on garbage — "
            f"add the language's stopwords + tic regexes to lib/prose_lint.py "
            f"and register it in SUPPORTED_LANGUAGES."
        )
    return code

# A scene break in the prose: ``* * *`` / ``***`` / ``---`` / ``· · ·`` on its
# own line (the same markers build_epub.py turns into <hr>). A chapter with no
# break is one scene.
_SCENE_BREAK_RE = re.compile(
    r"^\s*(?:\*\s*\*\s*\*|\*{3,}|-{3,}|·(?:\s*·)+)\s*$",
    re.MULTILINE,
)

# The epic-simile vehicle. We do NOT try to match bare ``como`` (it is also
# "since"/"as"/"about" in Spanish and would be pure noise). We match the shapes
# that are almost always a comparison vehicle:
#   - ``igual que`` / ``al igual que``            → almost always a simile
#   - ``, como`` (comma then como)                → the classic "X, como Y"
#   - ``como`` + article ("como una moneda")      → simile
#   - ``como si``                                 → the hypothetical simile
#   - ``cual`` (literary "like"; not ``cuál``)    → simile
# finditer is non-overlapping, so ", como una" is counted once, not twice.
_SIMILE_RE = re.compile(
    r"(?:al\s+)?igual\s+que\b"
    r"|,\s*como\b"
    r"|\bcomo\s+si\b"
    r"|\bcomo\s+(?:un|una|unos|unas|el|la|los|las)\b"
    r"|\bcual\b",
    re.IGNORECASE,
)

# WARN a scene whose simile density clears BOTH gates: an absolute floor (so a
# 120-word micro-scene with one simile does not trip) and a rate ceiling. The
# style guide budgets ~1 explanatory simile per scene; at ~2500 words/scene that
# is 0.4/1000, so 4.0/1000 leaves an order of magnitude of headroom and fires
# only on genuine over-use.
DEFAULT_MIN_COUNT = 2
DEFAULT_RATE_PER_1000 = 4.0

_HEADER_RE = re.compile(r"^#{1,6}\s+.*$", re.MULTILINE)


@dataclass
class Scene:
    index: int  # 1-based, in reading order
    word_count: int
    similes: list[str] = field(default_factory=list)  # matched snippets w/ context

    @property
    def count(self) -> int:
        return len(self.similes)

    @property
    def rate_per_1000(self) -> float:
        if self.word_count <= 0:
            return 0.0
        return 1000.0 * self.count / self.word_count


@dataclass
class ProseFinding:
    level: str
    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.level} {self.where}: {self.message}"


def _snippet(text: str, start: int, end: int, pad: int = 28) -> str:
    """A one-line window around a match, for the writer to eyeball."""
    lo = max(0, start - pad)
    hi = min(len(text), end + pad)
    frag = text[lo:hi].replace("\n", " ").strip()
    frag = re.sub(r"\s+", " ", frag)
    prefix = "…" if lo > 0 else ""
    suffix = "…" if hi < len(text) else ""
    return f"{prefix}{frag}{suffix}"


def split_scenes(text: str) -> list[str]:
    """Split chapter prose into scenes on scene-break lines. Always ≥1 element."""
    parts = _SCENE_BREAK_RE.split(text)
    return parts if parts else [text]


def find_similes(scene_text: str) -> list[str]:
    """Return a context snippet for every explanatory-simile match in the scene."""
    out: list[str] = []
    for m in _SIMILE_RE.finditer(scene_text):
        out.append(_snippet(scene_text, m.start(), m.end()))
    return out


def audit_prose(
    text: str,
    *,
    min_count: int = DEFAULT_MIN_COUNT,
    rate_per_1000: float = DEFAULT_RATE_PER_1000,
) -> tuple[list[Scene], list[ProseFinding]]:
    """Split ``text`` into scenes, count similes per scene, and return
    (scenes, findings). A scene is flagged only if it clears both the absolute
    floor and the rate ceiling."""
    scenes: list[Scene] = []
    findings: list[ProseFinding] = []
    for i, raw in enumerate(split_scenes(text), start=1):
        # Strip headers before counting words (keep them out of the count) but
        # search similes in the header-stripped prose too.
        prose = _HEADER_RE.sub("", raw)
        scene = Scene(
            index=i,
            word_count=count_words(raw),
            similes=find_similes(prose),
        )
        scenes.append(scene)
        if scene.count >= min_count and scene.rate_per_1000 > rate_per_1000:
            findings.append(
                ProseFinding(
                    WARN,
                    f"scene {scene.index}",
                    f"explanatory-simile density {scene.rate_per_1000:.1f}/1000 "
                    f"words ({scene.count} in {scene.word_count}); "
                    f"style.md budgets ~1/scene. Cut to the truest one:\n    - "
                    + "\n    - ".join(scene.similes),
                )
            )
    return scenes, findings


# ---------------------------------------------------------------------------
# Config: countable tic caps + reserved lexicon (notes/prose-lint.toml).
# The regexes and thresholds live off style.md so they cost no bundle tokens
# and the model never mistakes machine config for prose rules. A missing file
# falls back to the six named tics from style.md.
# ---------------------------------------------------------------------------

DEFAULT_CAPS: dict[str, float] = {
    "no_x_sino_y_per_scene": 1,
    "como_si_per_paragraph": 1,
    "repetition_emphasis_per_chapter": 1,
    "anaphora_min_run": 3,
    "mente_per_1000w": 4.0,
    "gerund_openers_per_1000w": 3.0,
    "filter_verbs_per_1000w": 1.5,
}


@dataclass
class ReservedWord:
    word: str
    pattern: re.Pattern
    allowed_chapters: set[int]


@dataclass
class ExtraPattern:
    name: str
    pattern: re.Pattern
    scope: str  # "chapter" (informational; where the pattern is counted)


@dataclass
class ProseLintConfig:
    caps: dict[str, float]
    reserved: list[ReservedWord]
    extra_patterns: list[ExtraPattern]
    source: str  # "notes/prose-lint.toml" or "defaults"


def _seed_schedule(paths) -> dict[str, set[int]]:
    """Map each seed id → the chapters it is scheduled to touch (plant/echo/
    payoff), so a reserved word tied to that seed is 'scheduled' exactly there."""
    out: dict[str, set[int]] = {}
    try:
        seeds = seeds_mod.load_seeds(paths.seeds_md)
    except Exception:
        return out
    for s in seeds:
        chapters: set[int] = set(s.echo_in)
        if s.plant_in is not None:
            chapters.add(s.plant_in)
        if s.payoff_in is not None:
            chapters.add(s.payoff_in)
        out[s.id] = chapters
    return out


def parse_config(data: dict, seed_chapters: dict[str, set[int]]) -> ProseLintConfig:
    """Build a config from a parsed TOML dict + a seed→chapters schedule. Pure,
    so it is testable without a book on disk."""
    caps = dict(DEFAULT_CAPS)
    for k, v in (data.get("caps") or {}).items():
        caps[k] = v

    reserved: list[ReservedWord] = []
    for entry in data.get("reserved", []):
        pat = entry.get("pattern")
        if not pat:
            continue
        allowed: set[int] = set(entry.get("extra_chapters", []))
        for sid in entry.get("seeds", []):
            allowed |= seed_chapters.get(sid, set())
        reserved.append(ReservedWord(
            word=entry.get("word", pat),
            pattern=re.compile(pat, re.IGNORECASE),
            allowed_chapters=allowed,
        ))

    extra: list[ExtraPattern] = []
    for entry in data.get("extra_patterns", []):
        pat = entry.get("pattern")
        if not pat:
            continue
        extra.append(ExtraPattern(
            name=entry.get("name", pat),
            pattern=re.compile(pat, re.IGNORECASE),
            scope=entry.get("scope", "chapter"),
        ))
    return ProseLintConfig(caps=caps, reserved=reserved, extra_patterns=extra,
                           source="notes/prose-lint.toml")


def load_config(paths) -> ProseLintConfig:
    """Load notes/prose-lint.toml for a book, resolving reserved-word chapters
    from the seed schedule. Missing file → defaults (six named tics, no
    reserved lexicon). Raises UnsupportedLanguageError when the book's prose
    language has no lexical layer here (see SUPPORTED_LANGUAGES)."""
    require_supported_language(paths)
    toml_path: Path = paths.prose_lint_toml
    if not toml_path.exists():
        return ProseLintConfig(caps=dict(DEFAULT_CAPS), reserved=[],
                               extra_patterns=[], source="defaults")
    data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    return parse_config(data, _seed_schedule(paths))


# ---------------------------------------------------------------------------
# Sentence / paragraph segmentation (evidence-grade, not linguistically exact).
# ---------------------------------------------------------------------------

_SENT_SPLIT_RE = re.compile(r'(?<=[.!?…])\s+(?=[A-ZÁÉÍÓÚÑ¿¡«"“—])')
_LEAD_PUNCT_RE = re.compile(r'^[\s—«»"“”\-¿¡\'’(]+')


def split_sentences(text: str) -> list[str]:
    """Split prose into sentences on end-punctuation followed by an opener.
    Good enough to count tics; not a linguistic tokenizer."""
    text = text.strip()
    if not text:
        return []
    return [s.strip() for s in _SENT_SPLIT_RE.split(text) if s.strip()]


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def _first_word(sentence: str) -> str:
    s = _LEAD_PUNCT_RE.sub("", sentence)
    m = re.match(r"[\wáéíóúñÁÉÍÓÚÑ]+", s)
    return m.group(0).casefold() if m else ""


# ---------------------------------------------------------------------------
# Countable tic checks. Each returns (count, examples).
# ---------------------------------------------------------------------------

_NO_X_SINO_Y_RE = re.compile(
    r"\bno\s+(?:era|es|fue|son|eran|había sido)?\s*[^,.;:]{1,60},\s*(?:sino|era)\b",
    re.IGNORECASE,
)
_COMO_SI_RE = re.compile(r"\bcomo\s+si\b", re.IGNORECASE)
_MENTE_RE = re.compile(r"\b\w+mente\b", re.IGNORECASE)
_GERUND_OPENER_RE = re.compile(r"^[\s—«»\"“\-¿¡]*\w+(?:ando|iendo|ándo|iéndo)\b",
                               re.IGNORECASE)
# Filter-word frame (deep-POV breach): a perception/cognition verb interposed
# between the reader and the sensation — "notó que el frío subía" instead of
# "el frío subía". Evidence-grade: the verb must open a subordinate ("que /
# cómo / si", with optional "de"), or be "pudo + perception infinitive"; a bare
# "vio el carro" is NOT matched (staging a look can be legitimate).
_FILTER_VERB_RE = re.compile(
    r"\b(?:not(?:ó|aba)|ve(?:ía)|vio|sint(?:ió|ía)|oy(?:ó|ía)|escuch(?:ó|aba)"
    r"|percib(?:ió|ía)|advirt(?:ió|ía)|observ(?:ó|aba)|comprend(?:ió|ía)"
    r"|entend(?:ió|ía)|pens(?:ó|aba)|record(?:ó|aba)|se\s+dio\s+cuenta"
    r"|se\s+pregunt(?:ó|aba))\s+(?:de\s+)?(?:que|cómo|si)\b"
    r"|\bpud(?:o|ía)\s+(?:ver|oír|sentir|escuchar|notar|percibir)\b",
    re.IGNORECASE,
)


def _snippet_at(text: str, start: int, end: int, pad: int = 24) -> str:
    return _snippet(text, start, end, pad)


def count_no_x_sino_y(text: str) -> tuple[int, list[str]]:
    ms = list(_NO_X_SINO_Y_RE.finditer(text))
    return len(ms), [_snippet_at(text, m.start(), m.end()) for m in ms]


def count_como_si(text: str) -> tuple[int, list[str]]:
    ms = list(_COMO_SI_RE.finditer(text))
    return len(ms), [_snippet_at(text, m.start(), m.end()) for m in ms]


def max_como_si_per_paragraph(text: str) -> tuple[int, list[str]]:
    """Worst-paragraph 'como si' count (the tic is about clustering)."""
    worst = 0
    examples: list[str] = []
    for para in split_paragraphs(text):
        n, _ = count_como_si(para)
        if n > worst:
            worst = n
            examples = [para.strip()[:120]]
    return worst, examples


def count_repetition_emphasis(text: str) -> tuple[int, list[str]]:
    """Consecutive sentences that repeat for emphasis: identical, or two short
    sentences (<9 words) sharing their first two tokens."""
    sents = split_sentences(text)
    hits = 0
    examples: list[str] = []
    for a, b in zip(sents, sents[1:]):
        na, nb = _norm_words(a), _norm_words(b)
        identical = na and na == nb
        # Two short sentences opening on the same content word ("Volvían más
        # grises. Volvían menos.") — a parallelism tic. Floor the opener length
        # so "El…/La…/Se…" runs don't trip it.
        short_echo = (len(na) < 9 and len(nb) < 9 and na and nb
                      and na[0] == nb[0] and len(na[0]) >= 4)
        if identical or short_echo:
            hits += 1
            if len(examples) < 5:
                examples.append(f"{a} / {b}")
    return hits, examples


def _norm_words(sentence: str) -> list[str]:
    return re.findall(r"[\wáéíóúñÁÉÍÓÚÑ]+", sentence.casefold())


def max_anaphora_run(text: str) -> tuple[int, list[str]]:
    """Longest run of consecutive sentences sharing the same first word."""
    sents = split_sentences(text)
    best = 0
    best_word = ""
    run = 0
    prev = None
    for s in sents:
        fw = _first_word(s)
        if fw and fw == prev:
            run += 1
        else:
            run = 1
            prev = fw
        if run > best:
            best = run
            best_word = fw
    examples = [f'{best} frases seguidas empiezan por "{best_word}"'] if best >= 2 else []
    return best, examples


def density_per_1000(pattern: re.Pattern, text: str, words: int) -> tuple[float, int, list[str]]:
    ms = list(pattern.finditer(text))
    rate = 1000.0 * len(ms) / words if words else 0.0
    ex = [_snippet_at(text, m.start(), m.end()) for m in ms[:5]]
    return rate, len(ms), ex


def gerund_opener_count(text: str) -> tuple[int, list[str]]:
    hits = 0
    examples: list[str] = []
    for s in split_sentences(text):
        if _GERUND_OPENER_RE.match(s):
            hits += 1
            if len(examples) < 5:
                examples.append(s[:80])
    return hits, examples


# ---------------------------------------------------------------------------
# Per-chapter tic report.
# ---------------------------------------------------------------------------

@dataclass
class TicCount:
    name: str
    count: int
    detail: str          # e.g. "max 2/paragraph", "5.1/1000w"
    cap: float
    over: bool
    examples: list[str] = field(default_factory=list)


def audit_chapter_tics(text: str, config: ProseLintConfig) -> list[TicCount]:
    """Countable named-tic evidence for one chapter. Counts, does not judge —
    the critic decides which flagged instances are real faults."""
    prose = prose_text(text)
    words = len(re.findall(r"[\wáéíóúñÁÉÍÓÚÑ'’-]+", prose))
    scenes = split_scenes(prose)
    caps = config.caps
    out: list[TicCount] = []

    # no X, sino Y — total + worst per scene.
    total_nxs, ex_nxs = count_no_x_sino_y(prose)
    worst_scene = max((count_no_x_sino_y(s)[0] for s in scenes), default=0)
    cap_nxs = caps.get("no_x_sino_y_per_scene", 1)
    out.append(TicCount("no X, sino Y", total_nxs,
                        f"max {worst_scene}/escena (cap {cap_nxs})",
                        cap_nxs, worst_scene > cap_nxs, ex_nxs[:5]))

    # como si — worst paragraph.
    worst_cs, ex_cs = max_como_si_per_paragraph(prose)
    cap_cs = caps.get("como_si_per_paragraph", 1)
    out.append(TicCount("como si", worst_cs,
                        f"max {worst_cs}/párrafo (cap {cap_cs})",
                        cap_cs, worst_cs > cap_cs, ex_cs))

    # repetition-as-emphasis.
    rep, ex_rep = count_repetition_emphasis(prose)
    cap_rep = caps.get("repetition_emphasis_per_chapter", 1)
    out.append(TicCount("repetición-énfasis", rep, f"{rep} (cap {cap_rep})",
                        cap_rep, rep > cap_rep, ex_rep))

    # anaphora / triplet openers.
    run, ex_an = max_anaphora_run(prose)
    cap_an = caps.get("anaphora_min_run", 3)
    out.append(TicCount("anáfora/tripletes", run, f"racha máx {run} (cap {cap_an})",
                        cap_an, run >= cap_an, ex_an))

    # -mente adverb density.
    rate_m, n_m, ex_m = density_per_1000(_MENTE_RE, prose, words)
    cap_m = caps.get("mente_per_1000w", 4.0)
    out.append(TicCount("adverbios -mente", n_m, f"{rate_m:.1f}/1000w (cap {cap_m})",
                        cap_m, rate_m > cap_m, ex_m))

    # gerund openers.
    n_g, ex_g = gerund_opener_count(prose)
    rate_g = 1000.0 * n_g / words if words else 0.0
    cap_g = caps.get("gerund_openers_per_1000w", 3.0)
    out.append(TicCount("aperturas en gerundio", n_g, f"{rate_g:.1f}/1000w (cap {cap_g})",
                        cap_g, rate_g > cap_g, ex_g))

    # filter-word frames (deep-POV breach).
    rate_f, n_f, ex_f = density_per_1000(_FILTER_VERB_RE, prose, words)
    cap_f = caps.get("filter_verbs_per_1000w", 1.5)
    out.append(TicCount("verbos-filtro (notó/vio/sintió que)", n_f,
                        f"{rate_f:.1f}/1000w (cap {cap_f})",
                        cap_f, rate_f > cap_f, ex_f))

    # graduated extra patterns (from voice.md via P2-9).
    for xp in config.extra_patterns:
        ms = list(xp.pattern.finditer(prose))
        out.append(TicCount(xp.name, len(ms), f"{len(ms)} (patrón graduado)",
                            0, len(ms) > 0,
                            [_snippet_at(prose, m.start(), m.end()) for m in ms[:5]]))
    return out


# ---------------------------------------------------------------------------
# Reserved lexicon (per chapter, schedule-aware).
# ---------------------------------------------------------------------------

@dataclass
class ReservedHit:
    word: str
    chapter: int
    count: int
    scheduled: bool
    examples: list[str] = field(default_factory=list)


def audit_reserved(chapter: int, text: str, config: ProseLintConfig) -> list[ReservedHit]:
    prose = prose_text(text)
    hits: list[ReservedHit] = []
    for rw in config.reserved:
        ms = list(rw.pattern.finditer(prose))
        if not ms:
            continue
        hits.append(ReservedHit(
            word=rw.word, chapter=chapter, count=len(ms),
            scheduled=chapter in rw.allowed_chapters,
            examples=[_snippet_at(prose, m.start(), m.end()) for m in ms[:3]],
        ))
    return hits


# ---------------------------------------------------------------------------
# Cross-chapter checks: repetition the writer (fresh session) cannot see.
# ---------------------------------------------------------------------------

# Small Spanish stopword set — enough to keep the "signature word" signal from
# drowning in function words. Not exhaustive by design.
_STOPWORDS = {
    "que", "de", "la", "el", "los", "las", "un", "una", "unos", "unas", "y",
    "o", "pero", "sino", "como", "para", "por", "con", "sin", "su", "sus",
    "se", "le", "les", "lo", "me", "te", "nos", "del", "al", "en", "no", "sí",
    "más", "menos", "muy", "ya", "cuando", "donde", "porque", "aunque", "si",
    "era", "eran", "fue", "ser", "estar", "estaba", "había", "han", "hay",
    "eso", "esto", "aquello", "ese", "este", "aquel", "esa", "esta", "aquella",
    "todo", "toda", "todos", "todas", "nada", "algo", "alguien", "cada",
    "entonces", "entonces", "también", "tampoco", "así", "aquí", "allí", "ahí",
    "sobre", "entre", "hasta", "desde", "hacia", "tras", "mientras", "antes",
    "después", "luego", "sólo", "solo", "otra", "otro", "otros", "otras",
    # Generic verbs/fillers that would flood the ≥4-letter net without carrying
    # any image: flagging "dijo ×40" tells the writer nothing.
    "vez", "veces", "cosa", "cosas", "modo", "dijo", "decir", "hizo", "hacer",
    "hacía", "tenía", "tenían", "tener", "podía", "podían", "poder", "sabía",
    "saber", "quería", "querer", "mismo", "misma", "mismos", "mismas", "ahora",
    "nunca", "siempre", "alguno", "alguna", "ninguno", "ninguna", "cualquier",
    "quien", "quienes", "según", "bajo", "ante", "junto", "dentro", "fuera",
    "encima", "debajo", "detrás", "delante", "través", "atrás", "habían",
    "hubo", "esos", "esas", "estos", "estas", "aquellos", "aquellas", "ellos",
    "ellas", "poco", "poca", "pocos", "pocas", "tanto", "tanta", "tantos",
    "tantas", "estaban", "fueron", "sería", "serían", "haber", "sido",
}

_CONTENT_WORD_RE = re.compile(r"[a-záéíóúñ]{4,}")


@dataclass
class SignatureWord:
    word: str
    chapters: list[int]
    total: int


@dataclass
class OpeningEcho:
    chapter_a: int
    chapter_b: int
    ratio: float
    opener_a: str
    opener_b: str


@dataclass
class MotifEcho:
    """A verbatim (word-normalised) phrase that recurs across chapters — the
    'el telar de su madre' class of repetition the signature-word signal
    (single words, rare each) structurally cannot see."""
    phrase: str
    chapters: list[int]


@dataclass
class HeavyWord:
    """A content word leaned on hard (≥3 uses) in two or more chapters — a
    re-described image, not a rare recurring one."""
    word: str
    counts: dict[int, int]  # chapter -> count

    @property
    def total(self) -> int:
        return sum(self.counts.values())


@dataclass
class CrossReport:
    signature_words: list[SignatureWord]
    opening_echoes: list[OpeningEcho]
    reserved_out_of_schedule: list[ReservedHit]
    motif_echoes: list[MotifEcho] = field(default_factory=list)
    heavy_words: list[HeavyWord] = field(default_factory=list)


def _content_words(text: str) -> list[str]:
    """Lowercase content words ≥5 letters, not stopwords, not proper nouns.
    A capitalised token mid-sentence is a proper noun and is dropped; a
    capitalised sentence OPENER is kept only when the same word also appears
    lowercase somewhere in the text (so 'Bruno' stays out but a chapter that
    opens sentences with 'Telar' still counts it)."""
    prose = prose_text(text)
    lowercase_seen = {
        w.casefold() for w in re.findall(r"\b[a-záéíóúüñ][\wáéíóúñ]*", prose)
    }
    out: list[str] = []
    for sent in split_sentences(prose):
        for i, tok in enumerate(re.findall(r"[\wáéíóúñÁÉÍÓÚÑ-]+", sent)):
            w = tok.casefold()
            if tok[:1].isupper() and (i > 0 or w not in lowercase_seen):
                continue
            if _CONTENT_WORD_RE.fullmatch(w) and w not in _STOPWORDS:
                out.append(w)
    return out


def _token_seq(text: str) -> list[str]:
    """Every prose token, lowercased, in order — the raw sequence motif
    matching runs over (proper nouns kept: a repeated phrase may contain one)."""
    return re.findall(r"[\wáéíóúüñ'-]+", prose_text(text).casefold())


def _motif_echoes(
    chapters: dict[int, str],
    *,
    n: int = 5,
    min_content: int = 2,
    top_n: int = 12,
) -> list[MotifEcho]:
    """Word-level n-grams (≥min_content non-stopword tokens) that appear
    verbatim in ≥2 chapters, merged into maximal phrases."""
    seqs = {c: _token_seq(t) for c, t in sorted(chapters.items())}
    gram_chapters: dict[tuple[str, ...], set[int]] = {}
    for c, seq in seqs.items():
        for i in range(len(seq) - n + 1):
            gram_chapters.setdefault(tuple(seq[i:i + n]), set()).add(c)
    shared = {
        g for g, cs in gram_chapters.items()
        if len(cs) >= 2 and sum(1 for w in g if w not in _STOPWORDS) >= min_content
    }
    if not shared:
        return []
    echoes: list[MotifEcho] = []
    used: set[tuple[str, ...]] = set()
    for c, seq in seqs.items():
        i = 0
        while i <= len(seq) - n:
            g = tuple(seq[i:i + n])
            if g in shared and g not in used:
                j = i
                while j + 1 <= len(seq) - n and tuple(seq[j + 1:j + 1 + n]) in shared:
                    j += 1
                grams = {tuple(seq[k:k + n]) for k in range(i, j + 1)}
                used |= grams
                caps = sorted(set().union(*(gram_chapters[pg] for pg in grams)))
                echoes.append(MotifEcho(" ".join(seq[i:j + n]), caps))
                i = j + n
            else:
                i += 1
    echoes.sort(key=lambda e: (len(e.chapters), len(e.phrase)), reverse=True)
    return echoes[:top_n]


def spent_images(
    chapters: dict[int, str], *, min_total: int = 3, top_n: int = 12
) -> list[HeavyWord]:
    """Content words already leaned on (≥min_total uses across the given
    chapters) — works from a single chapter, unlike the cross signals."""
    per = {c: Counter(_content_words(t)) for c, t in chapters.items()}
    totals: Counter = Counter()
    for counts in per.values():
        totals.update(counts)
    out = [HeavyWord(w, {c: k[w] for c, k in per.items() if k[w]})
           for w, tot in totals.items() if tot >= min_total]
    out.sort(key=lambda h: h.total, reverse=True)
    return out[:top_n]


def _first_sentence_tokens(text: str, n: int = 12) -> list[str]:
    sents = split_sentences(prose_text(text))
    if not sents:
        return []
    toks = re.findall(r"[\wáéíóúñ]+", sents[0].casefold())
    return toks[:n]


def audit_cross_chapter(
    chapters: dict[int, str],
    config: ProseLintConfig,
    *,
    min_chapters: int = 2,
    max_uses_each: int = 2,
    heavy_min_each: int = 3,
    top_n: int = 20,
    opening_ratio: float = 0.55,
) -> CrossReport:
    """Repetition across chapters that no single-chapter view can catch:
    signature-word reuse, repeated motifs/phrases, re-described images,
    echoing openings, reserved lexicon off-schedule."""
    # Signature words: appear in ≥min_chapters chapters, ≤max_uses_each each.
    per_chapter_counts: dict[int, Counter] = {
        n: Counter(_content_words(t)) for n, t in chapters.items()
    }
    spread: dict[str, list[int]] = {}
    for n, counts in per_chapter_counts.items():
        for w, c in counts.items():
            if c <= max_uses_each:
                spread.setdefault(w, []).append(n)
    sig = [SignatureWord(w, sorted(ch), sum(per_chapter_counts[c][w] for c in ch))
           for w, ch in spread.items() if len(ch) >= min_chapters]
    sig.sort(key=lambda s: (len(s.chapters), s.total), reverse=True)
    sig = sig[:top_n]

    # Opening echoes: first-12-token similarity between any two chapters.
    openers = {n: _first_sentence_tokens(t) for n, t in chapters.items()}
    echoes: list[OpeningEcho] = []
    nums = sorted(chapters)
    for i, a in enumerate(nums):
        for b in nums[i + 1:]:
            ta, tb = openers[a], openers[b]
            if not ta or not tb:
                continue
            ratio = difflib.SequenceMatcher(None, ta, tb).ratio()
            shared = len(set(ta) & set(tb))
            if ratio >= opening_ratio or shared >= 5:
                echoes.append(OpeningEcho(a, b, ratio, " ".join(ta), " ".join(tb)))

    # Reserved lexicon used outside its scheduled chapters.
    reserved_out: list[ReservedHit] = []
    for n, t in chapters.items():
        for hit in audit_reserved(n, t, config):
            if not hit.scheduled:
                reserved_out.append(hit)

    # Repeated motifs (verbatim phrases in ≥2 chapters) and heavy words
    # (≥heavy_min_each uses in each of ≥2 chapters — a re-described image).
    motifs = _motif_echoes(chapters) if len(chapters) >= 2 else []
    heavy = [
        h for h in spent_images(chapters, min_total=2 * heavy_min_each, top_n=999)
        if len([c for c, k in h.counts.items() if k >= heavy_min_each]) >= 2
    ][:top_n]
    return CrossReport(sig, echoes, reserved_out, motifs, heavy)


def overuse_summary(paths, chapter: int) -> str:
    """≤15-line 'overused so far' note for the write bundle, built from chapters
    BEFORE ``chapter``. Empty string when there is no prior chapter.

    The spent-images line works from a SINGLE prior chapter (aggregate counts),
    so chapter 2 — the first chapter that can photocopy chapter 1 — already
    gets a warning; the cross signals join in as chapters accumulate."""
    from .paths import chapter_numbers  # local import to avoid a cycle at load
    prior = [n for n in chapter_numbers(paths) if n < chapter]
    if not prior:
        return ""
    chapters = {n: paths.chapter_file(n).read_text(encoding="utf-8") for n in prior}
    config = load_config(paths)
    rep = audit_cross_chapter(chapters, config)
    lines: list[str] = []
    spent = spent_images(chapters)
    if spent:
        top = ", ".join(
            f"{h.word} (" + ", ".join(f"×{k} cap {c}" for c, k in sorted(h.counts.items())) + ")"
            for h in spent[:10])
        lines.append(
            "- **Imágenes ya gastadas** (ya establecidas en la página — una "
            f"referencia de pasada basta; NO las re-describas ni vuelvas a "
            f"morar en ellas): {top}.")
    if rep.motif_echoes:
        phrases = "; ".join(f"«{m.phrase}» (caps {m.chapters})"
                            for m in rep.motif_echoes[:5])
        lines.append(
            "- **Frases/motivos ya escritos tal cual** (si el motivo debe "
            f"volver, formúlalo distinto): {phrases}.")
    if rep.signature_words:
        top = ", ".join(f"{s.word} (×{s.total} en {len(s.chapters)} caps)"
                        for s in rep.signature_words[:8])
        lines.append(f"- **Palabras firma ya repetidas** (busca sinónimo): {top}.")
    if rep.reserved_out_of_schedule:
        words = ", ".join(sorted({h.word for h in rep.reserved_out_of_schedule}))
        lines.append(f"- **Léxico reservado ya gastado fuera de plan**: {words}.")
    if rep.opening_echoes:
        pairs = "; ".join(f"caps {e.chapter_a}&{e.chapter_b}" for e in rep.opening_echoes[:4])
        lines.append(f"- **Aperturas que ya riman** (abre distinto): {pairs}.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Markdown report (written by scripts/lint_prose.py).
# ---------------------------------------------------------------------------

def render_chapter_report(chapter: int, text: str, config: ProseLintConfig) -> str:
    prose = prose_text(text)
    scene_count = len(split_scenes(prose))
    mode = ("escenas reales (hay marcas de corte)" if scene_count > 1
            else "sin marcas de corte → conteo por capítulo (proxy por párrafo)")
    tics = audit_chapter_tics(text, config)
    scenes, simile_findings = audit_prose(text)

    out = [f"# Prose report — chapter {chapter}",
           f"> Modo de escena: {mode}.",
           "> Los conteos son EVIDENCIA para el crítico, no un gate. "
           "Juzga cada instancia marcada.",
           "",
           "## Tic counts",
           "| tic | conteo | detalle | ¿sobre cap? |",
           "|-----|-------|---------|-------------|"]
    for t in tics:
        out.append(f"| {t.name} | {t.count} | {t.detail} | {'**SÍ**' if t.over else 'no'} |")
    for t in tics:
        if t.over and t.examples:
            out.append(f"\n**{t.name}** — ejemplos:")
            out += [f"- {e}" for e in t.examples]

    if simile_findings:
        out.append("\n## Símiles explicativos (densidad por escena)")
        out += [f"- {f.message}" for f in simile_findings]

    reserved = [h for h in audit_reserved(chapter, text, config) if not h.scheduled]
    if reserved:
        out.append("\n## Léxico reservado fuera de plan (este capítulo)")
        for h in reserved:
            out.append(f"- **{h.word}** ×{h.count} — no programado en el cap {chapter}: "
                       + "; ".join(h.examples))
    return "\n".join(out) + "\n"


def render_cross_report(chapters: dict[int, str], config: ProseLintConfig) -> str:
    out = ["## Cross-chapter (todos los capítulos hasta aquí)"]
    if len(chapters) < 2:
        out.append(f"\n({len(chapters)} capítulo(s) — las señales cross-capítulo "
                   "necesitan ≥2; sin base para juzgar todavía)")
        return "\n".join(out) + "\n"
    rep = audit_cross_chapter(chapters, config)
    if rep.motif_echoes:
        out.append("\n### Motivos/frases repetidos tal cual entre capítulos")
        for m in rep.motif_echoes:
            out.append(f"- «{m.phrase}» — caps {m.chapters}")
    else:
        out.append("\n### Motivos/frases repetidos entre capítulos — ninguno")
    if rep.heavy_words:
        out.append("\n### Imágenes re-descritas (≥3 usos en ≥2 caps)")
        for h in rep.heavy_words:
            detail = ", ".join(f"×{k} cap {c}" for c, k in sorted(h.counts.items()))
            out.append(f"- **{h.word}** — {detail} (total {h.total})")
    else:
        out.append("\n### Imágenes re-descritas — ninguna")
    if rep.signature_words:
        out.append("\n### Palabras firma repetidas (≥2 caps, ≤2 usos c/u)")
        for s in rep.signature_words:
            out.append(f"- **{s.word}** — caps {s.chapters} (total {s.total})")
    else:
        out.append("\n### Palabras firma repetidas — ninguna")
    if rep.opening_echoes:
        out.append("\n### Aperturas que riman")
        for e in rep.opening_echoes:
            out.append(f"- caps {e.chapter_a} & {e.chapter_b} (ratio {e.ratio:.2f}): "
                       f'"{e.opener_a}" / "{e.opener_b}"')
    else:
        out.append("\n### Aperturas que riman — ninguna")
    if rep.reserved_out_of_schedule:
        out.append("\n### Léxico reservado fuera de plan")
        for h in rep.reserved_out_of_schedule:
            out.append(f"- **{h.word}** en cap {h.chapter} ×{h.count} (no programado)")
    return "\n".join(out) + "\n"


def any_cap_exceeded(chapter: int, text: str, config: ProseLintConfig) -> bool:
    if any(t.over for t in audit_chapter_tics(text, config)):
        return True
    if any(not h.scheduled for h in audit_reserved(chapter, text, config)):
        return True
    _, sim = audit_prose(text)
    return bool(sim)
